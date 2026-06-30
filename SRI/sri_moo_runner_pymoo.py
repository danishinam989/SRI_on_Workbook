"""
===============================================================================
SRI Multi-Objective Optimization — Executable Runner (pymoo backend)
===============================================================================

This module provides a fully executable NSGA-II optimization using pymoo,
sharing the same SRI Scoring Engine, Cost Estimator, and CO₂ Estimator
from the core module (sri_moo_optimizer.py).

pymoo is pip-installable and provides identical NSGA-II semantics to pygmo,
making this a drop-in alternative for environments without conda.

The pygmo version (sri_moo_optimizer.py) remains the primary reference
implementation; this runner demonstrates the full pipeline with real results.
===============================================================================
"""

import sys
import os
import json
import types
import warnings
from dataclasses import dataclass

import numpy as np

# Provide a mock pygmo so our core module imports cleanly
if "pygmo" not in sys.modules:
    sys.modules["pygmo"] = types.ModuleType("pygmo")

from sri_moo_optimizer import (
    load_service_catalogue,
    load_weighting_factors,
    SRIScoringEngine,
    UpgradeCostEstimator,
    CO2ReductionEstimator,
    BuildingProfile,
    ServiceDefinition,
    ParetoSolution,
    DOMAIN_NAMES,
    IMPACT_CRITERIA,
    create_example_building,
)

from pymoo.core.problem import ElementwiseProblem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import IntegerRandomSampling
from pymoo.operators.repair.rounding import RoundingRepair
from pymoo.optimize import minimize
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting
from pymoo.termination import get_termination


# =============================================================================
# 1. PYMOO PROBLEM DEFINITION
# =============================================================================

class SRIUpgradePymoo(ElementwiseProblem):
    """
    pymoo-compatible problem definition for SRI upgrade optimisation.

    Mirrors the pygmo UDP from sri_moo_optimizer.py exactly:
      - N integer decision variables (one per applicable service)
      - 4 objectives (all minimised): [-ΔSRI, -ΔIC_target, -ΔCO₂, Cost]
      - 1 inequality constraint: Cost ≤ Budget

    pymoo natively supports integer variables via IntegerRandomSampling +
    RoundingRepair, which is cleaner than pygmo's get_nix() approach.
    """

    def __init__(
        self,
        scoring_engine: SRIScoringEngine,
        cost_estimator: UpgradeCostEstimator,
        co2_estimator: CO2ReductionEstimator,
        building: BuildingProfile,
        service_order: list,
    ):
        self.scoring_engine = scoring_engine
        self.cost_estimator = cost_estimator
        self.co2_estimator = co2_estimator
        self.building = building
        self.service_order = service_order
        self.n_services = len(service_order)

        # Pre-compute baseline
        self.baseline_levels = {
            code: building.current_levels.get(code, 0)
            for code in service_order
        }
        (
            self.baseline_sri,
            self.baseline_domain_scores,
            self.baseline_impact_scores,
        ) = scoring_engine.compute_scores(self.baseline_levels)

        # Bounds
        catalogue_lookup = {s.code: s for s in scoring_engine.catalogue}
        xl = np.array([building.current_levels.get(code, 0) for code in service_order])
        xu = np.array([catalogue_lookup[code].max_level for code in service_order])

        super().__init__(
            n_var=self.n_services,
            n_obj=4,
            n_ieq_constr=1,     # Budget constraint: g(x) = Cost - Budget ≤ 0
            xl=xl,
            xu=xu,
            vtype=int,
        )

    def _evaluate(self, x, out, *args, **kwargs):
        """Evaluate a single solution."""
        proposed_levels = {
            code: int(round(x[i]))
            for i, code in enumerate(self.service_order)
        }

        # Cost
        cost = self.cost_estimator.total_cost(self.baseline_levels, proposed_levels)

        # SRI scores
        new_sri, new_domain, new_impact = self.scoring_engine.compute_scores(proposed_levels)

        # f1: Maximise SRI improvement → minimise negative
        delta_sri = new_sri - self.baseline_sri
        f1 = -delta_sri

        # f2: Maximise targeted impact category improvement
        target_imp = 0.0
        targets = self.building.target_impact_criteria
        for ic in targets:
            baseline_ic = self.baseline_impact_scores.get(ic, 0.0)
            new_ic = new_impact.get(ic, 0.0)
            target_imp += (new_ic - baseline_ic)
        if targets:
            target_imp /= len(targets)
        f2 = -target_imp

        # f3: Maximise CO₂ reduction
        co2_red = self.co2_estimator.estimate_co2_reduction(
            self.baseline_domain_scores, new_domain
        )
        f3 = -co2_red

        # f4: Minimise cost
        f4 = cost

        out["F"] = [f1, f2, f3, f4]

        # Inequality constraint: Cost - Budget ≤ 0
        out["G"] = [cost - self.building.budget_eur]


# =============================================================================
# 2. OPTIMISATION RUNNER
# =============================================================================

def run_optimisation_pymoo(
    building: BuildingProfile,
    data_dir: str,
    pop_size: int = 200,
    generations: int = 300,
    seed: int = 42,
    verbose: bool = True,
) -> list:
    """
    Execute the full SRI multi-objective optimisation using pymoo's NSGA-II.
    """
    # ── Load data ──
    if verbose:
        print("=" * 72)
        print("  SRI MULTI-OBJECTIVE UPGRADE OPTIMISATION (pymoo/NSGA-II)")
        print("=" * 72)
        print(f"\n[1/6] Loading service catalogue from {data_dir}...")

    catalogue = load_service_catalogue(data_dir)
    domain_weights, impact_weights = load_weighting_factors(
        data_dir, building.usage_type, building.climate_zone
    )

    if verbose:
        print(f"       Loaded {len(catalogue)} services across {len(DOMAIN_NAMES)} domains")

    # ── Filter to applicable services ──
    applicable = [svc for svc in catalogue if svc.code in building.applicable_services]
    service_order = [svc.code for svc in applicable]

    if verbose:
        print(f"[2/6] Applicable services: {len(service_order)}")
        print(f"       Search space: ~{np.prod([catalogue_lookup_max(catalogue, c, building) for c in service_order]):.1e} combinations")

    # ── Initialise engines ──
    scoring_engine = SRIScoringEngine(
        catalogue, domain_weights, impact_weights,
        building.applicable_services, building.domains_present,
    )
    cost_estimator = UpgradeCostEstimator(catalogue, building.floor_area_m2)
    co2_estimator = CO2ReductionEstimator(
        building.annual_energy_kwh, building.co2_emission_factor,
    )

    # ── Create pymoo problem ──
    if verbose:
        print("[3/6] Constructing pymoo problem...")

    problem = SRIUpgradePymoo(
        scoring_engine, cost_estimator, co2_estimator, building, service_order,
    )

    if verbose:
        baseline = problem.baseline_sri
        print(f"       Baseline SRI: {baseline:.1f}%")
        print(f"       Budget: €{building.budget_eur:,.0f}")
        print(f"       Decision vars: {problem.n_var} (all integer)")
        print(f"       Objectives: 4 | Constraints: 1")

    # ── Configure NSGA-II ──
    if verbose:
        print(f"[4/6] Configuring NSGA-II (pop={pop_size}, gen={generations})...")

    algorithm = NSGA2(
        pop_size=pop_size,
        sampling=IntegerRandomSampling(),
        crossover=SBX(
            prob=0.9,       # Crossover probability
            eta=15,         # Distribution index (higher → more exploitative)
            vtype=float,
            repair=RoundingRepair(),
        ),
        mutation=PM(
            eta=20,         # Distribution index
            vtype=float,
            repair=RoundingRepair(),
        ),
        eliminate_duplicates=True,
    )

    termination = get_termination("n_gen", generations)

    # ── Run optimisation ──
    if verbose:
        print("[5/6] Evolving population...")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = minimize(
            problem,
            algorithm,
            termination,
            seed=seed,
            verbose=verbose,
            save_history=False,
        )

    # ── Extract Pareto front ──
    if verbose:
        print(f"\n[6/6] Extracting Pareto-optimal solutions...")

    X = result.X  # Decision vectors
    F = result.F  # Fitness vectors
    G = result.G  # Constraint values

    if X is None or len(X) == 0:
        print("  ⚠ No feasible solutions found!")
        return []

    # Filter feasible solutions (constraint satisfied)
    feasible_mask = (G <= 0).all(axis=1) if G is not None else np.ones(len(X), dtype=bool)
    X_feas = X[feasible_mask]
    F_feas = F[feasible_mask]

    if len(X_feas) == 0:
        print("  ⚠ No feasible solutions within budget!")
        return []

    # Non-dominated sorting on feasible solutions
    nds = NonDominatedSorting()
    fronts = nds.do(F_feas)
    pareto_indices = fronts[0]

    if verbose:
        print(f"       Total feasible: {len(X_feas)}")
        print(f"       Pareto-optimal: {len(pareto_indices)}")

    # ── Build solution objects ──
    solutions = []
    for idx in pareto_indices:
        x = X_feas[idx]
        f = F_feas[idx]

        proposed_levels = {
            code: int(round(x[i]))
            for i, code in enumerate(service_order)
        }

        new_sri, new_domain, new_impact = scoring_engine.compute_scores(proposed_levels)
        cost = cost_estimator.total_cost(
            {c: building.current_levels.get(c, 0) for c in service_order},
            proposed_levels,
        )

        upgrades = {}
        for code in service_order:
            old = building.current_levels.get(code, 0)
            new = proposed_levels[code]
            if new > old:
                upgrades[code] = (old, new)

        solutions.append(ParetoSolution(
            service_levels=proposed_levels,
            sri_improvement=-f[0],
            impact_improvement=-f[1],
            co2_reduction_kg=-f[2],
            cost_eur=f[3],
            new_sri_score=new_sri,
            new_domain_scores=new_domain,
            new_impact_scores=new_impact,
            upgrades_from_baseline=upgrades,
        ))

    solutions.sort(key=lambda s: s.sri_improvement, reverse=True)
    return solutions


def catalogue_lookup_max(catalogue, code, building):
    """Helper: number of possible levels for a service (for search space calc)."""
    for svc in catalogue:
        if svc.code == code:
            current = building.current_levels.get(code, 0)
            return max(1, svc.max_level - current + 1)
    return 1


# =============================================================================
# 3. RESULTS PRESENTATION
# =============================================================================

def print_pareto_summary(solutions, baseline_sri, top_n=15):
    """Print a comprehensive summary of Pareto-optimal solutions."""
    print("\n" + "=" * 95)
    print("  PARETO-OPTIMAL UPGRADE RECOMMENDATIONS")
    print("=" * 95)
    print(
        f"{'#':>3}  {'ΔSRI':>7}  {'New SRI':>8}  {'ΔIC(EE+C)':>10}  "
        f"{'CO₂ Saved':>10}  {'Cost (€)':>10}  {'Upgrades':>8}  {'€/SRI pt':>8}"
    )
    print("-" * 95)

    for i, sol in enumerate(solutions[:top_n]):
        cost_per_pt = sol.cost_eur / max(sol.sri_improvement, 0.1)
        print(
            f"{i+1:>3}  {sol.sri_improvement:>6.1f}%  {sol.new_sri_score:>7.1f}%  "
            f"{sol.impact_improvement:>9.1f}%  {sol.co2_reduction_kg:>8.0f}kg  "
            f"€{sol.cost_eur:>9,.0f}  {len(sol.upgrades_from_baseline):>8}  "
            f"€{cost_per_pt:>7,.0f}"
        )

    print("-" * 95)

    if not solutions:
        return

    # ── Detailed breakdown of top 3 ──
    for rank, sol in enumerate(solutions[:3], 1):
        print(f"\n{'─' * 70}")
        print(f"  SOLUTION #{rank} — Detailed Breakdown")
        print(f"{'─' * 70}")
        print(f"  Overall SRI: {baseline_sri:.1f}% → {sol.new_sri_score:.1f}% (+{sol.sri_improvement:.1f}%)")
        print(f"  Capital Cost: €{sol.cost_eur:,.0f}")
        print(f"  Annual CO₂ Saved: {sol.co2_reduction_kg:,.0f} kg ({sol.co2_reduction_kg/1000:.1f} tonnes)")

        print(f"\n  Domain Scores (new):")
        for d, score in sol.new_domain_scores.items():
            if score > 0:
                print(f"    {d:25s} {score:5.1f}%")

        print(f"\n  Impact Criteria (new):")
        for ic, score in sol.new_impact_scores.items():
            label = ic.replace("_", " ").replace(",", "").title()
            print(f"    {label:40s} {score:5.1f}%")

        print(f"\n  Upgrades ({len(sol.upgrades_from_baseline)} services):")
        for code, (old, new) in sorted(sol.upgrades_from_baseline.items()):
            print(f"    {code:10s}  Level {old} → Level {new}")


def print_trade_off_analysis(solutions):
    """Analyse key trade-offs across the Pareto front."""
    if len(solutions) < 2:
        return

    print(f"\n{'=' * 70}")
    print("  TRADE-OFF ANALYSIS")
    print(f"{'=' * 70}")

    sri_vals = [s.sri_improvement for s in solutions]
    cost_vals = [s.cost_eur for s in solutions]
    co2_vals = [s.co2_reduction_kg for s in solutions]

    print(f"\n  SRI Improvement Range:  {min(sri_vals):.1f}% — {max(sri_vals):.1f}%")
    print(f"  Cost Range:             €{min(cost_vals):,.0f} — €{max(cost_vals):,.0f}")
    print(f"  CO₂ Reduction Range:    {min(co2_vals):,.0f} — {max(co2_vals):,.0f} kg/year")

    # Best bang-for-buck
    efficiency = [(s.sri_improvement / max(s.cost_eur, 1), s) for s in solutions]
    efficiency.sort(reverse=True)
    best_eff = efficiency[0][1]
    print(f"\n  Best Value (SRI/€):     +{best_eff.sri_improvement:.1f}% for €{best_eff.cost_eur:,.0f}")
    print(f"                          ({best_eff.sri_improvement/max(best_eff.cost_eur,1)*10000:.1f} SRI points per €10k)")

    # Knee point approximation (closest to utopia)
    sri_norm = np.array(sri_vals) / max(max(sri_vals), 0.01)
    cost_norm = 1 - np.array(cost_vals) / max(max(cost_vals), 1)
    co2_norm = np.array(co2_vals) / max(max(co2_vals), 0.01)
    distances = np.sqrt((1 - sri_norm)**2 + (1 - cost_norm)**2 + (1 - co2_norm)**2)
    knee_idx = np.argmin(distances)
    knee = solutions[knee_idx]
    print(f"\n  Knee-Point Solution:    +{knee.sri_improvement:.1f}% SRI | €{knee.cost_eur:,.0f} | {knee.co2_reduction_kg:,.0f} kg CO₂")
    print(f"                          ({len(knee.upgrades_from_baseline)} service upgrades)")


# =============================================================================
# 4. MAIN
# =============================================================================

if __name__ == "__main__":
    DATA_DIR = "./weights"

    # Create building profile
    building = create_example_building()

    print(f"\n  Building:     {building.usage_type} | {building.location_country}")
    print(f"  Floor area:   {building.floor_area_m2:,.0f} m²")
    print(f"  Year built:   {building.year_built}")
    print(f"  Annual energy:{building.annual_energy_kwh:,.0f} kWh (€{building.annual_energy_cost_eur:,.0f})")
    print(f"  Budget:       €{building.budget_eur:,.0f}")
    print(f"  Targets:      {building.target_impact_criteria}")
    print()

    # Run
    solutions = run_optimisation_pymoo(
        building=building,
        data_dir=DATA_DIR,
        pop_size=200,
        generations=500,
        seed=42,
        verbose=True,
    )

    if solutions:
        # Get baseline for display
        catalogue = load_service_catalogue(DATA_DIR)
        dw, iw = load_weighting_factors(DATA_DIR, building.usage_type, building.climate_zone)
        engine = SRIScoringEngine(
            catalogue, dw, iw, building.applicable_services, building.domains_present,
        )
        baseline_sri, _, _ = engine.compute_scores(building.current_levels)

        print_pareto_summary(solutions, baseline_sri, top_n=15)
        print_trade_off_analysis(solutions)
    else:
        print("\n⚠ No feasible solutions found. Consider increasing the budget.")
