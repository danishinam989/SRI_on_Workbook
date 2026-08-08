"""
===============================================================================
SRI Multi-Objective Upgrade Optimisation — EXCEL-BACKED (exact)
===============================================================================

Same optimisation as `sri_moo_optimizer.py`, but every SRI score is computed by
the **official SRI v4.5 Excel workbook** (via Modules/sri_excel_calculator.py)
instead of the in-Python `SRIScoringEngine`.

WHY THIS EXISTS
---------------
`sri_moo_optimizer.SRIScoringEngine` re-implements the methodology and reads
`weights/*_Domain_Weights.json`, which we validated against the workbook and
found defective:
  * 7 services have EMPTY impact_scores  (C-2b, C-3, DE-2, DHW-1b, E-4, E-5, L-2)
  * 5 services are missing 4 of 7 criteria (H-4, C-4, DE-4, E-8, E-12)
  * domain weights are rounded to 2 dp, breaking the sum-to-1 rule
Driving Excel removes every one of those discrepancies: the score IS the
official sheet's score, by construction.

THE TRADE-OFF (accepted deliberately)
-------------------------------------
Each evaluation is a real Excel recalculation (tens of ms) instead of ~50 µs.
Mitigations used here — none of which change a single feasible result:
  1. Excel is opened ONCE; building info + non-optimised services are written
     once; each candidate only rewrites the decision-variable cells.
  2. Results are memoised on the exact level vector (NSGA-II re-evaluates
     duplicates constantly).
  3. Over-budget candidates are rejected on cost alone, BEFORE touching Excel.
     They are infeasible and get discarded by constraint dominance anyway, so
     their objective values are never used.
Budget your time: roughly `unique_evaluations × ~40 ms`. Start small
(pop_size=40, generations=20) and scale up.

ENGINE: pymoo NSGA-II (pygmo has no Python 3.13 wheels).

Cost, CO₂/energy (ISO 52120-1) and the Pareto container are imported from
`sri_moo_optimizer` — no logic is duplicated.
===============================================================================
"""
from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import ElementwiseProblem
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.repair.rounding import RoundingRepair
from pymoo.operators.sampling.rnd import IntegerRandomSampling
from pymoo.optimize import minimize
from pymoo.termination import get_termination
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "Modules"))
sys.path.insert(0, str(_ROOT / "SRI"))

from sri_excel_calculator import SRIExcelCalculator, DEFAULT_WORKBOOK  # noqa: E402
from sri_moo_optimizer import (  # noqa: E402
    EnergyBreakdown,
    ISO52120EnergyEstimator,
    ParetoSolution,
    ServiceDefinition,
    UpgradeCostEstimator,
    load_pricing_catalogue,
    load_service_catalogue,
)

# The workbook reports domains under their official names; the ISO 52120
# estimator and the rest of this codebase use the short internal names.
EXCEL_TO_INTERNAL_DOMAIN = {
    "Heating": "Heating",
    "Domestic hot water": "DHW",
    "Cooling": "Cooling",
    "Ventilation": "Ventilation",
    "Lighting": "Lighting",
    "Dynamic building envelope": "DE",
    "Electricity": "Electricity",
    "Electric vehicle charging": "EV_Charging",
    "Monitoring and control": "MC",
}


@dataclass
class ExcelBuildingContext:
    """
    The non-SRI inputs the optimiser needs. The SRI side (building info +
    service levels) comes from the assessment JSON that sri_from_excel.py uses.
    """
    floor_area_m2: float
    annual_energy_kwh: float
    budget_eur: float
    co2_emission_factor: float = 0.233          # kgCO2/kWh (IE grid, ~2024)
    # ISO 52120 Annex A building type — see Docs/ISO_52120_BAC_FACTORS.md.
    # NB "Other types" (sport/storage/industrial) has NO D/B/A factors.
    iso_building_type: str = "Offices"
    usage_type: str = "non_residential"         # "residential" | "non_residential"
    energy_breakdown: Optional[EnergyBreakdown] = None
    target_impact_criteria: list[str] = field(
        default_factory=lambda: ["energy_efficiency"]
    )


class ExcelSRIEngine:
    """
    Context manager around SRIExcelCalculator that scores level vectors exactly,
    with memoisation.

    On entry it runs the baseline assessment once (which writes the Building
    Information dropdowns, resets every service, then applies the JSON's levels).
    Afterwards `score()` rewrites ONLY the decision-variable cells, so services
    outside the decision vector deterministically retain their baseline level.
    """

    def __init__(self, assessment: dict, workbook=DEFAULT_WORKBOOK, visible: bool = False):
        self.assessment = assessment
        self._calc = SRIExcelCalculator(workbook=workbook, visible=visible)
        self._cache: dict[tuple[int, ...] | None, tuple] = {}
        self.evaluations = 0        # real Excel recalcs
        self.cache_hits = 0
        self._order: list[str] = []

    def __enter__(self) -> "ExcelSRIEngine":
        self._calc.__enter__()
        # Establishes building info + baseline levels in the live sheet.
        self.baseline_result = self._calc.run_assessment(self.assessment)
        self.baseline_sri, self.baseline_domains, self.baseline_impacts = (
            self._unpack(self.baseline_result)
        )
        return self

    def __exit__(self, *exc):
        return self._calc.__exit__(*exc)

    # ---- introspection ----
    @property
    def max_levels(self) -> dict[str, int]:
        return self._calc.max_levels

    @property
    def service_codes(self) -> list[str]:
        return self._calc.service_codes

    @staticmethod
    def _unpack(result: dict) -> tuple[float, dict[str, float], dict[str, float]]:
        sri = result["sri"]
        if not isinstance(sri, (int, float)):
            raise ValueError(
                f"Excel returned a non-numeric SRI ({sri!r}). This usually means a "
                "functionality level exceeded a service's max level."
            )
        domains = {
            EXCEL_TO_INTERNAL_DOMAIN[k]: v
            for k, v in result["domains"].items()
            if k in EXCEL_TO_INTERNAL_DOMAIN and isinstance(v, (int, float))
        }
        impacts = {k: v for k, v in result["impacts"].items()
                   if isinstance(v, (int, float))}
        return float(sri), domains, impacts

    # ---- scoring ----
    def set_order(self, service_order: list[str]) -> None:
        """Fix the service order used to build cache keys."""
        self._order = list(service_order)

    def score(self, levels: dict[str, int]) -> tuple[float, dict[str, float], dict[str, float]]:
        """(sri, domain_scores_internal, impact_scores) — memoised."""
        key = tuple(levels[c] for c in self._order) if self._order else None
        if key is not None and key in self._cache:
            self.cache_hits += 1
            return self._cache[key]

        result = self._calc.evaluate(levels)
        self.evaluations += 1
        unpacked = self._unpack(result)
        if key is not None:
            self._cache[key] = unpacked
        return unpacked


class ExcelSRIUpgradeProblem(ElementwiseProblem):
    """
    pymoo problem. Objectives (all minimised):
        f0 = -ΔSRI              f1 = -ΔIC_target
        f2 = -ΔCO₂              f3 =  CapEx
    Inequality constraint: g0 = CapEx - budget ≤ 0
    """

    def __init__(
        self,
        engine: ExcelSRIEngine,
        cost_estimator: UpgradeCostEstimator,
        energy_estimator: ISO52120EnergyEstimator,
        ctx: ExcelBuildingContext,
        service_order: list[str],
        baseline_levels: dict[str, int],
    ):
        self.engine = engine
        self.cost_estimator = cost_estimator
        self.energy_estimator = energy_estimator
        self.ctx = ctx
        self.service_order = service_order
        self.baseline_levels = baseline_levels
        self._penalty = 1e8

        xl = np.array([baseline_levels[c] for c in service_order])
        xu = np.array([engine.max_levels[c] for c in service_order])
        super().__init__(n_var=len(service_order), n_obj=4, n_ieq_constr=1,
                         xl=xl, xu=xu, vtype=int)

    def _evaluate(self, x, out, *args, **kwargs):
        levels = {
            code: int(np.clip(round(float(x[i])),
                              self.baseline_levels[code],
                              self.engine.max_levels[code]))
            for i, code in enumerate(self.service_order)
        }

        cost = self.cost_estimator.total_cost(self.baseline_levels, levels)

        # Reject on cost BEFORE touching Excel. Infeasible candidates are
        # discarded by constraint dominance, so their objective values are
        # never used — this costs nothing in accuracy and saves an Excel recalc.
        if cost > self.ctx.budget_eur:
            out["F"] = [self._penalty] * 4
            out["G"] = [cost - self.ctx.budget_eur]
            return

        sri, domains, impacts = self.engine.score(levels)

        f0 = -(sri - self.engine.baseline_sri)

        targets = self.ctx.target_impact_criteria
        delta_ic = sum(impacts.get(ic, 0.0) - self.engine.baseline_impacts.get(ic, 0.0)
                       for ic in targets)
        if targets:
            delta_ic /= len(targets)
        f1 = -delta_ic

        f2 = -self.energy_estimator.estimate_co2_reduction(
            self.engine.baseline_domains, domains
        )
        f3 = cost

        out["F"] = [f0, f1, f2, f3]
        out["G"] = [cost - self.ctx.budget_eur]


def _seeded_population(
    baseline_levels: dict[str, int],
    max_levels: dict[str, int],
    service_order: list[str],
    pop_size: int,
    seed: int,
) -> np.ndarray:
    """
    Build the initial population biased toward the FEASIBLE region.

    Plain IntegerRandomSampling draws every service uniformly in
    [baseline, max], so with N services each individual upgrades ~N/2 of them at
    once and blows any realistic budget — the GA then has no feasible foothold
    and returns nothing. Instead: row 0 is the untouched baseline (cost €0,
    always feasible) and the rest upgrade only a sparse random subset.

    This only changes where the search STARTS, not how candidates are scored.
    """
    rng = np.random.default_rng(seed)
    n = len(service_order)
    base = np.array([baseline_levels[c] for c in service_order], dtype=int)
    upper = np.array([max_levels[c] for c in service_order], dtype=int)

    X = np.tile(base, (pop_size, 1))
    upgradable = np.flatnonzero(upper > base)
    if len(upgradable) == 0:
        return X

    for i in range(1, pop_size):
        k = int(rng.integers(1, max(2, len(upgradable) // 3 + 1)))
        for j in rng.choice(upgradable, size=min(k, len(upgradable)), replace=False):
            X[i, j] = int(rng.integers(base[j], upper[j] + 1))
    return X


def _optimisable_services(assessment: dict, engine: ExcelSRIEngine) -> tuple[list[str], dict[str, int]]:
    """
    Services the optimiser may raise: those present in the assessment, flagged
    applicable, known to the workbook, and not already at their max level.
    Returns (service_order, baseline_levels_for_those_services).
    """
    flat: dict[str, dict] = {}
    if "services" in assessment:
        flat.update(assessment["services"])
    for _dom, svcs in (assessment.get("domains") or {}).items():
        flat.update(svcs)

    order: list[str] = []
    baseline: dict[str, int] = {}
    for code, spec in flat.items():
        if isinstance(spec, dict):
            level, applicable = int(spec.get("level", 0)), spec.get("applicable", 1)
        else:
            level, applicable = int(spec), 1
        if not applicable:
            continue
        if code not in engine.max_levels:
            continue
        if level >= engine.max_levels[code]:
            continue                      # already maxed — nothing to optimise
        order.append(code)
        baseline[code] = level
    return order, baseline


def run_optimisation_excel(
    assessment_path,
    ctx: ExcelBuildingContext,
    data_dir=None,
    workbook=DEFAULT_WORKBOOK,
    pop_size: int = 40,
    generations: int = 20,
    seed: int = 42,
    verbose: bool = True,
) -> list[ParetoSolution]:
    """
    Run the Excel-backed NSGA-II optimisation.

    Args:
        assessment_path: the same assessment JSON sri_from_excel.py consumes.
        ctx:             floor area / energy / budget / ISO building type.
        pop_size, generations: keep SMALL — every candidate is an Excel recalc.
    """
    data_dir = Path(data_dir) if data_dir else _ROOT / "weights"
    assessment = json.loads(Path(assessment_path).read_text(encoding="utf-8"))

    if verbose:
        print("=" * 72)
        print("  SRI UPGRADE OPTIMISATION — EXCEL-BACKED (exact)")
        print("=" * 72)
        print(f"[1/5] Opening workbook: {Path(workbook).name}")

    with ExcelSRIEngine(assessment, workbook=workbook) as engine:
        service_order, baseline_levels = _optimisable_services(assessment, engine)
        engine.set_order(service_order)

        if not service_order:
            if verbose:
                print("       Nothing to optimise (all applicable services already at max).")
            return []

        if verbose:
            print(f"       Baseline SRI (from Excel): {engine.baseline_sri:.2f}%")
            print(f"[2/5] Optimisable services: {len(service_order)}")
            space = int(np.prod([engine.max_levels[c] - baseline_levels[c] + 1
                                 for c in service_order]))
            print(f"       Search space ≈ {space:.3e} combinations")

        # ---- cost + energy models (shared with the pygmo module) ----
        catalogue: list[ServiceDefinition] = load_service_catalogue(str(data_dir))
        pricing, ref_area = load_pricing_catalogue(str(data_dir / "pricing_catalogue.json"))
        cost_estimator = UpgradeCostEstimator(
            catalogue=catalogue,
            floor_area_m2=ctx.floor_area_m2,
            pricing_catalogue=pricing,
            reference_floor_area_m2=ref_area,
        )
        breakdown = ctx.energy_breakdown or EnergyBreakdown.from_total(ctx.annual_energy_kwh)
        energy_estimator = ISO52120EnergyEstimator(
            breakdown=breakdown,
            co2_factor=ctx.co2_emission_factor,
            usage_type=ctx.usage_type,
            iso_building_type=ctx.iso_building_type,
        )
        if verbose:
            if ctx.energy_breakdown is None:
                print("       [!] No measured energy breakdown — using DEFAULT_END_USE_SHARE "
                      "(an assumption).")
            for w in energy_estimator.warnings:
                print(f"       [!] {w}")

        problem = ExcelSRIUpgradeProblem(
            engine, cost_estimator, energy_estimator, ctx, service_order, baseline_levels
        )

        if verbose:
            print(f"[3/5] NSGA-II (pop={pop_size}, gen={generations}) — "
                  f"up to ~{pop_size * generations:,} candidate evaluations")
            print("       Each unique candidate is a real Excel recalculation. Please wait...")

        algorithm = NSGA2(
            pop_size=pop_size,
            # Seeded from the baseline — see _seeded_population() for why plain
            # IntegerRandomSampling yields no feasible solutions under a budget.
            sampling=_seeded_population(
                baseline_levels, engine.max_levels, service_order, pop_size, seed
            ),
            crossover=SBX(prob=0.9, eta=15, vtype=float, repair=RoundingRepair()),
            mutation=PM(eta=20, vtype=float, repair=RoundingRepair()),
            eliminate_duplicates=True,
        )

        t0 = time.perf_counter()
        result = minimize(problem, algorithm, get_termination("n_gen", generations),
                          seed=seed, verbose=False, save_history=False)
        elapsed = time.perf_counter() - t0

        if verbose:
            print(f"[4/5] Done in {elapsed:,.1f}s — {engine.evaluations:,} Excel recalcs, "
                  f"{engine.cache_hits:,} cache hits "
                  f"({engine.evaluations and elapsed / engine.evaluations * 1000:.0f} ms/recalc)")

        if result.X is None or len(np.atleast_2d(result.X)) == 0:
            if verbose:
                print("       No feasible solutions within budget.")
            return []

        X = np.atleast_2d(result.X)
        F = np.atleast_2d(result.F)
        G = np.atleast_2d(result.G) if result.G is not None else None

        if G is not None:
            feasible = (G <= 0).all(axis=1)
            X, F = X[feasible], F[feasible]
        if len(X) == 0:
            if verbose:
                print("       No feasible solutions within budget.")
            return []

        fronts = NonDominatedSorting().do(F)
        if verbose:
            print(f"[5/5] Pareto-optimal (feasible): {len(fronts[0])}")

        solutions: list[ParetoSolution] = []
        for idx in fronts[0]:
            levels = {code: int(X[idx][i]) for i, code in enumerate(service_order)}
            sri, domains, impacts = engine.score(levels)
            cost = cost_estimator.total_cost(baseline_levels, levels)
            upgrades = {c: (baseline_levels[c], levels[c])
                        for c in service_order if levels[c] > baseline_levels[c]}
            solutions.append(ParetoSolution(
                service_levels=levels,
                sri_improvement=sri - engine.baseline_sri,
                impact_improvement=-F[idx][1],
                co2_reduction_kg=-F[idx][2],
                cost_eur=cost,
                new_sri_score=sri,
                new_domain_scores=domains,
                new_impact_scores=impacts,
                upgrades_from_baseline=upgrades,
            ))

        solutions.sort(key=lambda s: s.sri_improvement, reverse=True)
        return solutions


def print_summary(solutions: list[ParetoSolution], baseline_sri: float, top_n: int = 10) -> None:
    print("\n" + "=" * 92)
    print("  PARETO-OPTIMAL UPGRADE PLANS  (SRI from the official Excel workbook)")
    print("=" * 92)
    print(f"{'#':>3}  {'ΔSRI':>7}  {'New SRI':>8}  {'ΔIC':>7}  {'CO₂ saved':>11}  "
          f"{'Cost':>11}  {'Upgrades':>8}")
    print("-" * 92)
    for i, s in enumerate(solutions[:top_n], 1):
        print(f"{i:>3}  {s.sri_improvement:>6.2f}%  {s.new_sri_score:>7.2f}%  "
              f"{s.impact_improvement:>6.2f}%  {s.co2_reduction_kg:>8,.0f} kg  "
              f"€{s.cost_eur:>10,.0f}  {len(s.upgrades_from_baseline):>8}")
    print("-" * 92)
    if solutions:
        best = solutions[0]
        print(f"\n--- Best ΔSRI: {baseline_sri:.2f}% → {best.new_sri_score:.2f}% "
              f"(+{best.sri_improvement:.2f}) for €{best.cost_eur:,.0f} ---")
        for code, (old, new) in sorted(best.upgrades_from_baseline.items()):
            print(f"      • {code}: level {old} → {new}")


if __name__ == "__main__":
    # Ballymun Library — the same assessment sri_from_excel.py runs.
    assessment_file = _ROOT / "Modules" / "Ballymun_Library_assessment.json"

    ctx = ExcelBuildingContext(
        floor_area_m2=846.0,                       # from the SRI export
        # NOTE: placeholders — replace with metered data for defensible energy/CO₂.
        annual_energy_kwh=150_000,
        budget_eur=25_000,
        co2_emission_factor=0.233,
        iso_building_type="Education buildings (schools)",  # a library, not "Other types"
        usage_type="non_residential",
        target_impact_criteria=["energy_efficiency"],
    )

    sols = run_optimisation_excel(
        assessment_file, ctx,
        pop_size=24, generations=10,   # small by design — every eval hits Excel
        seed=42, verbose=True,
    )
    if sols:
        base = sols[0].new_sri_score - sols[0].sri_improvement
        print_summary(sols, base)
    else:
        print("\nNo feasible solutions — try raising the budget.")
