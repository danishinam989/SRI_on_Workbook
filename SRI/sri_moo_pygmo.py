"""
================================================================================
  SRI Multi-Objective Optimisation Engine  –  pygmo Implementation
  Smart Readiness Indicator | Technical Building System Upgrade Recommender
================================================================================

MATHEMATICAL FORMULATION
─────────────────────────
Decision Variables  x ∈ ℤⁿ
  Each element x_i represents the proposed functionality level for TBS service i.
  Bounds:  current_level_i  ≤  x_i  ≤  max_level_i   (integer-valued)
  Dimension n = total number of applicable services in the building
             (up to 54 for Method B across 9 domains)

Objective Functions  f : ℤⁿ → ℝ⁴    (pygmo MINIMISES everything)
  f₁(x) = −ΔSRI(x)                        → maximise overall SRI improvement
  f₂(x) = −ΔDomainOrImpact(x, target)     → maximise chosen domain / impact gain
  f₃(x) = −ΔCO₂(x)                        → maximise CO₂ reduction
  f₄(x) =  CapEx(x)                        → minimise capital expenditure

Inequality Constraint  g : ℤⁿ → ℝ¹    (pygmo form: g(x) ≤ 0)
  g₁(x) = CapEx(x) − BUDGET  ≤  0         → hard budget ceiling

SRI Score Computation Pipeline
  Layer 1 – Service Score:
    score_s(x_i) = impact_score[service_i][criterion_c][level=x_i]
                   normalised to [0, 1] by dividing by max possible score

  Layer 2 – Domain Score (vertical aggregation, equal weights within domain):
    DomainScore_d(c) = (1/|S_d|) Σ_{i∈S_d}  score_s_i(c)

  Layer 3 – Impact Score (horizontal aggregation with climate-aware weights):
    ImpactScore_c = Σ_d  w_dc · DomainScore_d(c)

  Layer 4 – Overall SRI:
    SRI = Σ_c  w_c · ImpactScore_c

ALGORITHM SELECTION RATIONALE
──────────────────────────────
  ► NSGA-II  (Non-dominated Sorting Genetic Algorithm II)
       pygmo.nsga2 with integer programming support via get_nix()

  Why NSGA-II for this problem?
  • Combinatorial, discrete search space (integer levels 0–4 per service)
    pygmo's NSGA-II natively supports mixed-integer / pure-integer problems
    via get_nix(); no continuous-relaxation or rounding hack is needed.
  • Multi-objective: Pareto-front recovery is the primary goal.
    NSGA-II's fast non-dominated sort + crowding distance selection is ideal
    for 2–4 objectives.
  • Constraint-handling: tournament selection naturally deprioritises
    infeasible solutions (budget violation) via constraint dominance.
  • Scalability: O(M·N²) complexity handles up to 54 services efficiently.
  • Interpretability: the resulting Pareto front is a concrete trade-off
    surface that a building owner / consultant can navigate visually.

  Runner-up: MOEA/D  (pygmo.moead)
  • Excels when objectives are strongly conflicting and a fine-grained
    decomposition of the weight vector space is desired. Recommended as a
    validation run alongside NSGA-II.

DISCRETE VARIABLE HANDLING (get_nix)
──────────────────────────────────────
  pygmo supports *integer programming* natively. By implementing get_nix()
  in the UDP to return the number of integer variables (= n_services), the
  optimiser enforces integrality exactly throughout evolution — no rounding
  post-processing, no constraint penalty for fractional levels.
  Bounds are set as float but must bracket integers (e.g. [2.0, 4.0]).

================================================================================
"""

from __future__ import annotations

import json
import math
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

# ── Optional imports (graceful degradation if pygmo not installed) ────────────
try:
    import pygmo as pg
    PYGMO_AVAILABLE = True
except ImportError:                                          # pragma: no cover
    warnings.warn("pygmo not installed.  Run:  pip install pygmo")
    PYGMO_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────────────────
#  DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

IMPACT_CRITERIA = [
    "energy_efficiency",
    "energy_flexibility_and_storage",
    "comfort",
    "convenience",
    "health,_wellbeing_and_accessibility",
    "maintenance_and_fault_prediction",
    "information_to_occupants",
]

DOMAINS = [
    "Heating", "Domestic hot water", "Cooling", "Ventilation",
    "Lighting", "Dynamic building envelope",
    "Electricity", "Electric vehicle charging",
    "Monitoring and control",
]

# Mapping from the official impact-criterion names used in the weighting-factor
# JSON files to the internal snake_case keys used throughout this module.
# REQUIRED: the JSON keys criteria as e.g. "Energy efficiency"; the scorer looks
# them up as "energy_efficiency". Without remapping, every weight lookup returns
# 0.0 and the SRI score collapses to 0.
OFFICIAL_TO_INTERNAL_IC: dict[str, str] = {
    "Energy efficiency":                    "energy_efficiency",
    "Energy flexibility and storage":       "energy_flexibility_and_storage",
    "Comfort":                              "comfort",
    "Convenience":                          "convenience",
    "Health, well-being and accessibility": "health,_wellbeing_and_accessibility",
    "Maintenance and fault prediction":     "maintenance_and_fault_prediction",
    "Information to occupants":             "information_to_occupants",
}

# Default impact-criteria weights (horizontal aggregation), per the consolidated
# methodology: equal 33.3% across the three EPBD key functionalities.
# Source: SRI Calculation Framework v4.5 / Commission Delegated Regulation (EU) 2020/2155.
# (These are also present per climate zone in the *_impact_weighting_factors.json
#  files — all zones share the same impact weights — and are loaded from there when
#  available; this dict is the fallback.)
DEFAULT_IMPACT_WEIGHTS: dict[str, float] = {
    "energy_efficiency":                    0.16667,  # energy performance & operation (½)
    "maintenance_and_fault_prediction":     0.16667,  # energy performance & operation (½)
    "energy_flexibility_and_storage":       0.33333,  # energy flexibility
    "comfort":                              0.08333,  # occupant needs (¼)
    "convenience":                          0.08333,  # occupant needs (¼)
    "health,_wellbeing_and_accessibility":  0.08333,  # occupant needs (¼)
    "information_to_occupants":             0.08333,  # occupant needs (¼)
}

# kgCO₂e / kWh grid emission factors by climate zone (approximation).
# Keys MUST match the climate-zone keys used in the weighting JSON files.
CO2_FACTORS: dict[str, float] = {
    "North Europe":       0.054,   # Nordic hydro / nuclear heavy mix
    "West Europe":        0.233,   # IE / FR / DE / BE / NL …
    "South Europe":       0.310,   # ES / IT / GR …
    "North-East Europe":  0.750,   # PL / CZ coal-heavy
    "South-East Europe":  0.480,   # RO / BG …
}

# Approximate upgrade cost curves per service (€, delta per level step).
# Structure: { service_code: [cost_L0→L1, cost_L1→L2, cost_L2→L3, cost_L3→L4] }
# PLACEHOLDER values (domain-representative) — replace with live/market data.
# IMPORTANT: keys MUST be real catalogue codes from the *_Domain_Weights.json
# files, otherwise load_domain_services() silently falls back to a flat default
# and these numbers never apply.
DEFAULT_UPGRADE_COSTS: dict[str, list[float]] = {
    # Heating
    "H-1a": [800,  1200, 2500, 4000], "H-1b": [800,  1200, 2500, 4000],
    "H-1c": [800,  1200, 2500, 4000], "H-1d": [800,  1200, 2500, 4000],
    "H-1f": [800,  1200, 2500, 4000], "H-2a": [1500, 2500, 5000, 0],
    "H-2b": [1500, 2500, 5000, 0],    "H-2d": [1500, 2500, 5000, 0],
    "H-3":  [2000, 3500, 6000, 8000], "H-4":  [2000, 3500, 6000, 8000],
    # DHW
    "DHW-1a": [400, 700, 1200, 2000], "DHW-1b": [400, 700, 1200, 2000],
    "DHW-1d": [400, 700, 1200, 2000], "DHW-2b": [600, 1000, 2000, 3500],
    "DHW-3":  [600, 1000, 2000, 3500],
    # Cooling
    "C-1a": [1000, 1800, 3000, 5000], "C-1b": [1000, 1800, 3000, 5000],
    "C-1c": [1000, 1800, 3000, 5000], "C-1d": [1000, 1800, 3000, 5000],
    "C-1f": [1000, 1800, 3000, 5000], "C-1g": [1000, 1800, 3000, 5000],
    "C-2a": [1000, 1800, 3000, 5000], "C-2b": [1000, 1800, 3000, 5000],
    "C-3":  [1000, 1800, 3000, 5000], "C-4":  [1000, 1800, 3000, 5000],
    # Ventilation
    "V-1a": [1500, 2500, 4000, 6000], "V-1c": [1500, 2500, 4000, 6000],
    "V-2c": [1500, 2500, 4000, 6000], "V-2d": [1500, 2500, 4000, 6000],
    "V-3":  [1500, 2500, 4000, 6000], "V-6":  [1500, 2500, 4000, 6000],
    # Lighting
    "L-1a": [500, 1000, 2000, 3500],  "L-2":  [500, 1000, 2000, 3500],
    # Dynamic building envelope
    "DE-1": [1200, 2000, 4000, 6000], "DE-2": [1200, 2000, 4000, 6000],
    "DE-4": [1200, 2000, 4000, 6000],
    # Electricity
    "E-2":  [2000, 3500, 6000, 9000], "E-3":  [2000, 3500, 6000, 9000],
    "E-4":  [2000, 3500, 6000, 9000], "E-5":  [2000, 3500, 6000, 9000],
    "E-8":  [2000, 3500, 6000, 9000], "E-11": [2000, 3500, 6000, 9000],
    "E-12": [2000, 3500, 6000, 9000],
    # EV charging
    "EV-15": [3000, 5000, 8000, 12000], "EV-16": [3000, 5000, 8000, 12000],
    "EV-17": [3000, 5000, 8000, 12000],
    # Monitoring & Control
    "MC-3":  [500, 1000, 2000, 4000], "MC-4":  [500, 1000, 2000, 4000],
    "MC-9":  [500, 1000, 2000, 4000], "MC-13": [500, 1000, 2000, 4000],
    "MC-25": [500, 1000, 2000, 4000], "MC-28": [500, 1000, 2000, 4000],
    "MC-29": [500, 1000, 2000, 4000], "MC-30": [500, 1000, 2000, 4000],
}


@dataclass
class TBSService:
    """A single Technical Building System service entry."""
    code: str
    name: str
    domain: str
    current_level: int
    max_level: int
    impact_scores: dict[str, dict[str, float]]   # criterion → level_key → score
    upgrade_costs: list[float]                    # cost[i] = cost to go from level i → i+1
    applicable: bool = True

    # ── helpers ──────────────────────────────────────────────────────────────
    def score_at(self, level: int, criterion: str) -> float:
        """Return raw impact score for a given level and criterion."""
        key = f"level_{level}"
        return self.impact_scores.get(criterion, {}).get(key, 0.0)

    def max_score(self, criterion: str) -> float:
        """Return the highest achievable impact score across all levels."""
        scores = [self.score_at(l, criterion) for l in range(self.max_level + 1)]
        return max(scores) if scores else 0.0

    def cost_to_upgrade(self, from_level: int, to_level: int) -> float:
        """Cumulative cost to move from from_level → to_level."""
        if to_level <= from_level:
            return 0.0
        total = 0.0
        for step in range(from_level, to_level):
            if step < len(self.upgrade_costs):
                total += self.upgrade_costs[step]
        return total


@dataclass
class BuildingProfile:
    """Container for all building-level inputs to the optimiser."""
    building_id: str
    building_type: str                          # "Residential" | "Non-residential"
    climate_zone: str                           # e.g. "West Europe"
    floor_area_m2: float
    year_built: int
    annual_energy_kwh: float
    annual_energy_cost_eur: float
    solar_potential: float = 0.0               # 0–1 normalised
    geothermal_potential: float = 0.0          # 0–1 normalised
    current_sri_score: float = 0.0
    budget_eur: float = 50_000.0

    # Domain-level weights keyed by (domain, criterion) loaded from JSON
    domain_weights: dict[str, dict[str, float]] = field(default_factory=dict)
    impact_weights: dict[str, float] = field(
        default_factory=lambda: dict(DEFAULT_IMPACT_WEIGHTS))

    services: list[TBSService] = field(default_factory=list)

    # ── convenience ──────────────────────────────────────────────────────────
    @property
    def co2_factor(self) -> float:
        return CO2_FACTORS.get(self.climate_zone, 0.300)

    @property
    def n_services(self) -> int:
        return sum(1 for s in self.services if s.applicable)

    @property
    def applicable_services(self) -> list[TBSService]:
        return [s for s in self.services if s.applicable]


# ─────────────────────────────────────────────────────────────────────────────
#  SRI SCORING ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class SRIScorer:
    """
    Replicates the EU SRI calculation pipeline from Commission Delegated
    Regulation (EU) 2020/2155 and the v4.5 Calculation Framework.

    Two-pass architecture:
      Pass 1  (baseline)  – score current functionality levels.
      Pass 2  (candidate) – score proposed x vector, compute deltas.
    """

    def __init__(self, profile: BuildingProfile) -> None:
        self.profile = profile
        self._baseline_cache: dict[str, float] | None = None

    # ── private helpers ───────────────────────────────────────────────────────
    def _norm_score(self, service: TBSService, level: int, criterion: str) -> float:
        """Normalise a service's raw score to [0, 1]."""
        raw = service.score_at(level, criterion)
        max_s = service.max_score(criterion)
        return raw / max_s if max_s > 0 else 0.0

    def _domain_score(
        self,
        domain: str,
        criterion: str,
        levels: dict[str, int],
    ) -> float:
        """
        Layer 2 – equal-weight aggregation of normalised service scores
        within a domain for a given impact criterion.
        """
        domain_services = [
            s for s in self.profile.applicable_services if s.domain == domain
        ]
        if not domain_services:
            return 0.0
        scores = [
            self._norm_score(s, levels.get(s.code, s.current_level), criterion)
            for s in domain_services
        ]
        return float(np.mean(scores))

    def _impact_score(self, criterion: str, levels: dict[str, int]) -> float:
        """
        Layer 3 – climate-aware weighted sum of domain scores for a criterion.
        """
        total_weight = 0.0
        weighted_sum = 0.0
        for domain in DOMAINS:
            w = self.profile.domain_weights.get(domain, {}).get(criterion, 0.0)
            if w == 0.0:
                continue
            # Per SRI v4.5: a domain with no applicable services does not
            # contribute — force its weight to zero so it doesn't dilute the
            # weighted average via the denominator.
            if not any(s.domain == domain for s in self.profile.applicable_services):
                continue
            ds = self._domain_score(domain, criterion, levels)
            weighted_sum += w * ds
            total_weight += w
        if total_weight == 0.0:
            return 0.0
        return weighted_sum / total_weight  # normalise so that max possible = 1

    def compute_sri(self, levels: dict[str, int]) -> tuple[float, dict, dict]:
        """
        Full SRI computation.

        Parameters
        ----------
        levels : dict mapping service.code → proposed integer level

        Returns
        -------
        sri_score : float  (0–100 %)
        impact_scores : dict[criterion → float]
        domain_scores : dict[domain → float]  (averaged across criteria)
        """
        impact_scores: dict[str, float] = {}
        for criterion in IMPACT_CRITERIA:
            impact_scores[criterion] = self._impact_score(criterion, levels)

        # Layer 4 – weighted sum of impact scores
        sri = 0.0
        for criterion, score in impact_scores.items():
            w = self.profile.impact_weights.get(criterion, 0.0)
            sri += w * score
        sri_pct = sri * 100.0

        # Domain scores (average across all criteria, weighted by impact weight)
        domain_scores: dict[str, float] = {}
        for domain in DOMAINS:
            d_scores = []
            for criterion in IMPACT_CRITERIA:
                w_d = self.profile.domain_weights.get(domain, {}).get(criterion, 0.0)
                if w_d > 0:
                    d_scores.append(self._domain_score(domain, criterion, levels))
            domain_scores[domain] = float(np.mean(d_scores)) * 100.0 if d_scores else 0.0

        return sri_pct, impact_scores, domain_scores

    def baseline(self) -> tuple[float, dict, dict]:
        """Compute and cache the current (as-assessed) SRI score."""
        if self._baseline_cache is None:
            levels = {s.code: s.current_level for s in self.profile.applicable_services}
            self._baseline_cache = self.compute_sri(levels)
        return self._baseline_cache


# ─────────────────────────────────────────────────────────────────────────────
#  COST ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class CostEngine:
    """Computes capital expenditure for a proposed upgrade vector x."""

    # CO₂ intensity of upgrade activities (kgCO₂e per € spent) – RICS estimate
    EMBODIED_CO2_FACTOR: float = 0.0025   # kg CO₂e / €

    def __init__(self, profile: BuildingProfile) -> None:
        self.profile = profile

    def capex(self, x: np.ndarray) -> float:
        """Sum of incremental upgrade costs for all services in vector x."""
        total = 0.0
        for i, service in enumerate(self.profile.applicable_services):
            proposed = int(round(x[i]))
            total += service.cost_to_upgrade(service.current_level, proposed)
        return total

    def co2_reduction_kgpa(
        self, x: np.ndarray, scorer: SRIScorer
    ) -> float:
        """
        Estimate annual operational CO₂ reduction (kg/year).

        Heuristic: each 1% SRI improvement yields ~0.5% reduction in annual
        energy consumption (conservative estimate from IEA building studies).
        Adjust ENERGY_SAVING_PER_SRI_PCT for your building stock.
        """
        ENERGY_SAVING_PER_SRI_PCT: float = 0.005   # 0.5% energy / 1% SRI

        baseline_sri, _, _ = scorer.baseline()
        levels_proposed = {
            s.code: int(round(x[i]))
            for i, s in enumerate(self.profile.applicable_services)
        }
        proposed_sri, _, _ = scorer.compute_sri(levels_proposed)
        delta_sri = proposed_sri - baseline_sri

        energy_saved_kwh = (
            self.profile.annual_energy_kwh * ENERGY_SAVING_PER_SRI_PCT * delta_sri
        )
        co2_saved_kg = energy_saved_kwh * self.profile.co2_factor
        return max(co2_saved_kg, 0.0)


# ─────────────────────────────────────────────────────────────────────────────
#  PYGMO USER-DEFINED PROBLEM (UDP)
# ─────────────────────────────────────────────────────────────────────────────

class SRI_MOO_UDP:
    """
    pygmo User-Defined Problem for SRI upgrade optimisation.

    ┌─────────────────────────────────────────────────────────────────────┐
    │  Decision variables : integer array x ∈ ℤⁿ                         │
    │  x[i] = proposed functionality level for applicable_services[i]     │
    │  Bounds: [current_level_i, max_level_i]  for each i                 │
    │                                                                     │
    │  Objectives (all MINIMISED by pygmo):                               │
    │    f0 = −ΔSRI                     (maximise SRI gain)               │
    │    f1 = −ΔDomainOrImpact          (maximise target domain/impact)   │
    │    f2 = −ΔCO₂_reduction           (maximise CO₂ savings)           │
    │    f3 =  CapEx                    (minimise capital cost)            │
    │                                                                     │
    │  Constraints (inequality, form: g(x) ≤ 0):                         │
    │    g0 = CapEx(x) − BUDGET  ≤  0  (hard budget ceiling)             │
    └─────────────────────────────────────────────────────────────────────┘

    pygmo API contract
    ──────────────────
    fitness(x)    → [f0, f1, f2, f3, g0]   length = nobj + nic
    get_bounds()  → ([lb...], [ub...])
    get_nobj()    → 4
    get_nic()     → 1   (number of inequality constraints)
    get_nix()     → n   (number of INTEGER variables — enforces discreteness)
    get_name()    → str
    """

    def __init__(
        self,
        profile: BuildingProfile,
        target_domain: str | None = None,
        target_impact: str | None = None,
        objective_weights: dict[str, float] | None = None,
    ) -> None:
        """
        Parameters
        ----------
        profile        : BuildingProfile with pre-populated services list
        target_domain  : Optional – name of a domain to boost (f1 objective)
        target_impact  : Optional – name of an impact criterion to boost (f1)
                         (target_domain takes priority over target_impact)
        objective_weights : Optional override of relative importance scaling.
                            Keys: "sri", "domain", "co2", "cost"
        """
        self.profile = profile
        self.scorer = SRIScorer(profile)
        self.cost_engine = CostEngine(profile)
        self.services = profile.applicable_services
        self.n = len(self.services)

        self.target_domain = target_domain
        self.target_impact = target_impact

        self.obj_weights = objective_weights or {
            "sri": 1.0, "domain": 1.0, "co2": 1.0, "cost": 1.0
        }

        # Cache baseline once
        self._baseline_sri, self._baseline_impact, self._baseline_domain = (
            self.scorer.baseline()
        )

    # ── pygmo API ─────────────────────────────────────────────────────────────

    def fitness(self, x: np.ndarray) -> list[float]:
        """
        Core evaluation function called by pygmo for every candidate solution.

        pygmo passes x as a float64 array.  Because get_nix() == n, the
        optimiser guarantees that all components are integer-valued, but we
        defensively cast with int(round(·)) for robustness.
        """
        xi = np.array([int(round(v)) for v in x], dtype=int)

        levels_proposed = {
            s.code: xi[i] for i, s in enumerate(self.services)
        }

        # ── Compute proposed SRI ─────────────────────────────────────────────
        proposed_sri, proposed_impact, proposed_domain = self.scorer.compute_sri(
            levels_proposed
        )

        # ── f0 – SRI improvement (negate → minimise) ─────────────────────────
        delta_sri = proposed_sri - self._baseline_sri
        f0 = -delta_sri * self.obj_weights["sri"]

        # ── f1 – Domain or Impact category target ────────────────────────────
        if self.target_domain and self.target_domain in proposed_domain:
            delta_target = (
                proposed_domain[self.target_domain]
                - self._baseline_domain.get(self.target_domain, 0.0)
            )
        elif self.target_impact and self.target_impact in proposed_impact:
            delta_target = (
                proposed_impact[self.target_impact]
                - self._baseline_impact.get(self.target_impact, 0.0)
            )
        else:
            # Fall back: maximise the sum of all domain improvements
            delta_target = sum(
                proposed_domain.get(d, 0) - self._baseline_domain.get(d, 0)
                for d in DOMAINS
            )
        f1 = -delta_target * self.obj_weights["domain"]

        # ── f2 – CO₂ reduction (negate → minimise) ───────────────────────────
        co2_saved = self.cost_engine.co2_reduction_kgpa(x, self.scorer)
        f2 = -co2_saved * self.obj_weights["co2"]

        # ── f3 – Capital expenditure (minimise directly) ─────────────────────
        capex = self.cost_engine.capex(x)
        f3 = capex * self.obj_weights["cost"]

        # ── g0 – Budget constraint  (CapEx − Budget ≤ 0) ─────────────────────
        g0 = capex - self.profile.budget_eur

        return [f0, f1, f2, f3, g0]

    def get_bounds(self) -> tuple[list[float], list[float]]:
        """
        Lower bounds = current level (no downgrade allowed).
        Upper bounds = maximum defined level for each service.
        Returns floats; get_nix() instructs pygmo to treat them as integers.
        """
        lb = [float(s.current_level) for s in self.services]
        ub = [float(s.max_level)     for s in self.services]
        return lb, ub

    def get_nobj(self) -> int:
        return 4

    def get_nic(self) -> int:
        """Number of inequality constraints."""
        return 1

    def get_nix(self) -> int:
        """
        ★ INTEGER PROGRAMMING DECLARATION ★
        Returning n instructs pygmo that ALL decision variables are integers.
        NSGA-II will then apply integer-aware crossover/mutation operators
        (specifically: uniform crossover respects integer boundaries,
        polynomial mutation rounds to nearest integer).
        This is the correct, zero-hack way to handle discrete SRI levels.
        """
        return self.n

    def get_name(self) -> str:
        return "SRI_TBS_Upgrade_MOO"

    def get_extra_info(self) -> str:
        lines = [
            f"  Building:      {self.profile.building_id}",
            f"  Services (n):  {self.n}",
            f"  Budget (€):    {self.profile.budget_eur:,.0f}",
            f"  Climate zone:  {self.profile.climate_zone}",
            f"  Baseline SRI:  {self._baseline_sri:.1f}%",
            f"  Target domain: {self.target_domain or '—'}",
            f"  Target impact: {self.target_impact or '—'}",
        ]
        return "\n".join(lines)

    # ── Gradient (not provided – ensures pygmo uses derivative-free methods) ──
    # (Intentionally omitted — pygmo detects absence and selects EA solvers)


# ─────────────────────────────────────────────────────────────────────────────
#  OPTIMISATION RUNNER
# ─────────────────────────────────────────────────────────────────────────────

class SRIOptimiser:
    """
    High-level runner that configures the pygmo island, evolves the population,
    and returns a ranked Pareto front with human-readable upgrade plans.
    """

    # NSGA-II hyper-parameters (tune per building complexity)
    POP_SIZE: int = 120       # ≥ 4 × n_services recommended for diversity
    N_GENERATIONS: int = 300  # Increase for larger service sets
    SEED: int = 42

    def __init__(
        self,
        profile: BuildingProfile,
        target_domain: str | None = None,
        target_impact: str | None = None,
        pop_size: int | None = None,
        n_generations: int | None = None,
        algorithm: str = "nsga2",   # "nsga2" | "moead"
    ) -> None:
        self.profile = profile
        self.target_domain = target_domain
        self.target_impact = target_impact
        self.pop_size = pop_size or self.POP_SIZE
        self.n_generations = n_generations or self.N_GENERATIONS
        self.algorithm_name = algorithm

        self.udp = SRI_MOO_UDP(profile, target_domain, target_impact)
        self._pareto_front: list[dict] | None = None

    def _build_algorithm(self) -> "pg.algorithm":
        if self.algorithm_name == "nsga2":
            algo = pg.algorithm(
                pg.nsga2(
                    gen=self.n_generations,
                    cr=0.9,          # crossover rate
                    eta_c=10.0,      # distribution index for crossover
                    m=1.0 / max(self.profile.n_services, 1),  # mutation rate
                    eta_m=50.0,      # distribution index for mutation (higher = finer steps)
                    seed=self.SEED,
                )
            )
        elif self.algorithm_name == "moead":
            algo = pg.algorithm(
                pg.moead(
                    gen=self.n_generations,
                    weight_generation="grid",
                    decomposition="tchebycheff",
                    neighbours=20,
                    CR=1.0,
                    F=0.5,
                    eta_m=20.0,
                    seed=self.SEED,
                )
            )
        else:
            raise ValueError(f"Unknown algorithm: {self.algorithm_name!r}")
        algo.set_verbosity(50)   # log every 50 generations
        return algo

    def run(self, verbose: bool = True) -> list[dict]:
        """
        Execute the evolutionary optimisation and return the Pareto front.

        Returns
        -------
        List of dicts, each representing one non-dominated upgrade plan:
          {
            "rank":           int,
            "delta_sri_pct":  float,
            "delta_target":   float,
            "co2_saved_kg":   float,
            "capex_eur":      float,
            "payback_years":  float,
            "upgrades":       list[dict]   ← service-level upgrade details
          }
        """
        if not PYGMO_AVAILABLE:
            raise RuntimeError("pygmo is not installed.  Run: pip install pygmo")

        problem = pg.problem(self.udp)

        # ── Seed population ───────────────────────────────────────────────────
        pop = pg.population(
            prob=problem,
            size=self.pop_size,
            seed=self.SEED,
            b=pg.default_bfe(),
        )

        # ── Evolve ────────────────────────────────────────────────────────────
        algo = self._build_algorithm()
        if verbose:
            print(f"\n{'─'*60}")
            print(f"  SRI MOO Optimiser  |  Algorithm: {self.algorithm_name.upper()}")
            print(f"  Building: {self.profile.building_id}")
            print(f"  Services: {self.profile.n_services}  |  "
                  f"Pop: {self.pop_size}  |  Gen: {self.n_generations}")
            print(f"  Budget: €{self.profile.budget_eur:,.0f}  |  "
                  f"Baseline SRI: {self.udp._baseline_sri:.1f}%")
            print(f"{'─'*60}\n")

        pop = algo.evolve(pop)

        # ── Extract Pareto front ──────────────────────────────────────────────
        pf_indices = pg.select_best_N_mo(
            points=pop.get_f()[:, :4],   # objectives only (exclude constraint)
            N=self.pop_size,
        )
        pareto_x = pop.get_x()[pf_indices]
        pareto_f = pop.get_f()[pf_indices]

        # Filter to feasible solutions (g0 ≤ 0)
        feasible_mask = pop.get_f()[pf_indices, 4] <= 0.0
        pareto_x = pareto_x[feasible_mask]
        pareto_f = pareto_f[feasible_mask]

        if verbose:
            print(f"\n  Pareto front size (feasible): {len(pareto_x)}")

        self._pareto_front = self._decode_solutions(pareto_x, pareto_f)
        return self._pareto_front

    def _decode_solutions(
        self, xs: np.ndarray, fs: np.ndarray
    ) -> list[dict]:
        """Convert raw pygmo arrays to human-readable upgrade plans."""
        scorer = SRIScorer(self.profile)
        cost_engine = CostEngine(self.profile)
        baseline_sri = self.udp._baseline_sri
        baseline_domain = self.udp._baseline_domain

        plans = []
        for rank, (x, f) in enumerate(zip(xs, fs)):
            xi = np.array([int(round(v)) for v in x], dtype=int)
            levels = {
                s.code: xi[i]
                for i, s in enumerate(self.profile.applicable_services)
            }
            prop_sri, prop_impact, prop_domain = scorer.compute_sri(levels)
            capex = cost_engine.capex(x)
            co2 = cost_engine.co2_reduction_kgpa(x, scorer)

            # Payback estimate: energy cost savings
            ENERGY_SAVING_PER_SRI_PCT = 0.005
            annual_saving_eur = (
                self.profile.annual_energy_cost_eur
                * ENERGY_SAVING_PER_SRI_PCT
                * (prop_sri - baseline_sri)
            )
            payback = capex / annual_saving_eur if annual_saving_eur > 1 else math.inf

            # Per-service upgrade details
            upgrades = []
            for i, service in enumerate(self.profile.applicable_services):
                proposed_lvl = xi[i]
                if proposed_lvl > service.current_level:
                    upgrades.append({
                        "service_code": service.code,
                        "service_name": service.name,
                        "domain":       service.domain,
                        "from_level":   service.current_level,
                        "to_level":     proposed_lvl,
                        "cost_eur":     service.cost_to_upgrade(
                                            service.current_level, proposed_lvl
                                        ),
                    })

            # Domain-level delta breakdown
            domain_deltas = {
                d: round(prop_domain.get(d, 0) - baseline_domain.get(d, 0), 2)
                for d in DOMAINS
            }

            plans.append({
                "rank":           rank + 1,
                "delta_sri_pct":  round(prop_sri - baseline_sri, 2),
                "proposed_sri":   round(prop_sri, 2),
                "delta_domain":   domain_deltas,
                "co2_saved_kg":   round(co2, 1),
                "capex_eur":      round(capex, 0),
                "payback_years":  round(payback, 1) if payback < 99 else "N/A",
                "n_upgrades":     len(upgrades),
                "upgrades":       sorted(upgrades, key=lambda u: -u["cost_eur"]),
                # Raw objectives (negated back to positive improvement values)
                "_obj_raw":       [-f[0], -f[1], -f[2], f[3]],
            })

        # Sort by SRI improvement descending
        return sorted(plans, key=lambda p: -p["delta_sri_pct"])


# ─────────────────────────────────────────────────────────────────────────────
#  DATA LOADING HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def load_domain_services(
    domain_json_path: str | Path,
    domain_name: str,
    current_levels: dict[str, int],
    upgrade_costs: dict[str, list[float]] | None = None,
) -> list[TBSService]:
    """
    Parse a domain JSON file (e.g. Heating_Domain_Weights.json) into a list
    of TBSService objects.

    Parameters
    ----------
    domain_json_path  : path to e.g. "Heating_Domain_Weights.json"
    domain_name       : human label, e.g. "Heating"
    current_levels    : dict mapping service_code → current assessed level
    upgrade_costs     : optional override dict; falls back to DEFAULT_UPGRADE_COSTS
    """
    _costs = upgrade_costs or DEFAULT_UPGRADE_COSTS
    data = json.loads(Path(domain_json_path).read_text())

    services: list[TBSService] = []
    for _idx, entry in data.items():
        code = entry["code"]
        name = entry.get("service", code)
        fl = entry.get("functionality_levels", {})
        max_level = len(fl) - 1   # levels are 0-indexed

        # Normalise impact_scores keys to project's canonical form
        raw_scores = entry.get("impact_scores", {})
        services.append(
            TBSService(
                code=code,
                name=name,
                domain=domain_name,
                current_level=current_levels.get(code, 0),
                max_level=max_level,
                impact_scores=raw_scores,
                upgrade_costs=_costs.get(code, [1000.0] * max_level),
                applicable=True,
            )
        )
    return services


def load_weighting_factors_from_json(
    json_path: str | Path,
    climate_zone: str,
) -> tuple[dict[str, dict[str, float]], dict[str, float]]:
    """
    Load domain weightings and impact weightings for a given climate zone from a
    *_impact_weighting_factors.json file.

    The JSON keys impact criteria by their official names (e.g. "Energy
    efficiency"); these are remapped to the internal snake_case keys used
    throughout this module (e.g. "energy_efficiency"). Domain names are kept as-is
    since they already match the DOMAINS list.

    Returns
    -------
    (domain_weights, impact_weights)
        domain_weights : dict[domain_name → dict[internal_criterion → weight]]
        impact_weights : dict[internal_criterion → weight]
    """
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    zones = data.get("climate_zones", {})
    zone_data = zones.get(climate_zone, {})

    domain_weights: dict[str, dict[str, float]] = {}
    for domain, crits in zone_data.get("domain_weightings", {}).items():
        domain_weights[domain] = {
            OFFICIAL_TO_INTERNAL_IC[off]: w
            for off, w in crits.items()
            if off in OFFICIAL_TO_INTERNAL_IC
        }

    impact_weights: dict[str, float] = {
        OFFICIAL_TO_INTERNAL_IC[off]: w
        for off, w in zone_data.get("impact_weightings", {}).items()
        if off in OFFICIAL_TO_INTERNAL_IC
    }

    return domain_weights, impact_weights


# ─────────────────────────────────────────────────────────────────────────────
#  EXAMPLE USAGE  (replace paths with your actual project data directory)
# ─────────────────────────────────────────────────────────────────────────────

def build_example_profile(data_dir: str = ".") -> BuildingProfile:
    """
    Construct a BuildingProfile for an example non-residential building
    using the project JSON files.  Mirrors the Finglas Sports Centre
    scenario used in earlier analysis work.
    """
    data_dir = Path(data_dir)

    # ── 1.  Assessed current functionality levels ────────────────────────────
    #   (In production this comes from your SRI assessment database.)
    #   Codes must match the catalogue in the *_Domain_Weights.json files; any
    #   service not listed here defaults to level 0.
    current_levels: dict[str, int] = {
        # Heating
        "H-1a": 1, "H-1b": 0, "H-1c": 1, "H-1d": 0, "H-1f": 0,
        "H-2a": 1, "H-2b": 0, "H-2d": 0, "H-3": 1, "H-4": 1,
        # DHW
        "DHW-1a": 1, "DHW-1b": 0, "DHW-1d": 0, "DHW-2b": 0, "DHW-3": 0,
        # Cooling
        "C-1a": 0, "C-1b": 0, "C-1c": 0, "C-1d": 0, "C-1f": 0,
        "C-1g": 0, "C-2a": 0, "C-2b": 0, "C-3": 0, "C-4": 0,
        # Ventilation
        "V-1a": 1, "V-1c": 0, "V-2c": 0, "V-2d": 0, "V-3": 0, "V-6": 0,
        # Lighting
        "L-1a": 2, "L-2": 1,
        # Dynamic building envelope
        "DE-1": 0, "DE-2": 0, "DE-4": 0,
        # Electricity
        "E-2": 0, "E-3": 0, "E-4": 0, "E-5": 0, "E-8": 0, "E-11": 0, "E-12": 0,
        # EV charging
        "EV-15": 0, "EV-16": 0, "EV-17": 0,
        # Monitoring & Control
        "MC-3": 1, "MC-4": 0, "MC-9": 0, "MC-13": 0,
        "MC-25": 0, "MC-28": 0, "MC-29": 0, "MC-30": 0,
    }

    # ── 2.  Load services from domain JSON files ─────────────────────────────
    domain_files = {
        "Heating":                    "Heating_Domain_Weights.json",
        "Domestic hot water":         "DHW_Domain_Weights.json",
        "Cooling":                    "Cooling_Domain_Weights.json",
        "Ventilation":                "Ventilation_Domain_Weights.json",
        "Lighting":                   "Lighting_Domain_Weights.json",
        "Dynamic building envelope":  "DE_Domain_Weights.json",
        "Electricity":                "Electricity_Domain_Weights.json",
        "Electric vehicle charging":  "EV_Charging_Domain_Weights.json",
        "Monitoring and control":     "MC_Domain_Weights.json",
    }

    all_services: list[TBSService] = []
    for domain_name, fname in domain_files.items():
        fpath = data_dir / fname
        if fpath.exists():
            svcs = load_domain_services(fpath, domain_name, current_levels)
            all_services.extend(svcs)
        else:
            print(f"  [WARN] Domain file not found: {fpath}")

    # ── 3.  Load climate-aware domain & impact weights ───────────────────────
    #   Pick the weighting file that matches the building type. (The example is a
    #   non-residential building, so the non-residential factors apply.)
    climate_zone = "West Europe"
    wf_path = data_dir / "non_residential_impact_weighting_factors.json"
    domain_weights: dict[str, dict[str, float]] = {}
    impact_weights = dict(DEFAULT_IMPACT_WEIGHTS)
    if wf_path.exists():
        domain_weights, loaded_impact = load_weighting_factors_from_json(
            wf_path, climate_zone=climate_zone
        )
        if loaded_impact:
            impact_weights = loaded_impact
    else:
        print(f"  [WARN] Weighting file not found: {wf_path} — using fallback impact weights")

    # ── 4.  Assemble profile ─────────────────────────────────────────────────
    profile = BuildingProfile(
        building_id="Finglas_Sports_Centre",
        building_type="Non-residential",
        climate_zone=climate_zone,
        floor_area_m2=3_500,
        year_built=1992,
        annual_energy_kwh=485_000,
        annual_energy_cost_eur=72_000,
        solar_potential=0.65,
        geothermal_potential=0.30,
        current_sri_score=28.4,
        budget_eur=80_000.0,
        domain_weights=domain_weights,
        impact_weights=impact_weights,
        services=all_services,
    )
    return profile


def run_optimisation_example(data_dir: str = ".") -> None:
    """
    End-to-end demonstration of the optimisation pipeline.

    Scenario A: Maximise overall SRI within €80k budget.
    Scenario B: Prioritise Heating domain improvement within same budget.
    """
    profile = build_example_profile(data_dir)

    print(f"\n{'═'*60}")
    print("  SRI MOO OPTIMISATION  –  Example Run")
    print(f"  Building: {profile.building_id}")
    print(f"  Services loaded: {profile.n_services}")
    print(f"{'═'*60}")

    # ── Scenario A: Global SRI maximisation ──────────────────────────────────
    print("\n▶  Scenario A: Maximise Global SRI Improvement\n")
    opt_a = SRIOptimiser(
        profile=profile,
        algorithm="nsga2",
        pop_size=max(120, 4 * profile.n_services),
        n_generations=300,
    )
    pareto_a = opt_a.run(verbose=True)

    print(f"\n  Top 5 Pareto-optimal upgrade plans:")
    print(f"  {'Rank':<5} {'ΔSRI':>8} {'CapEx€':>10} {'CO₂kg':>9} {'Payback':>9} {'#Upgrades':>10}")
    print(f"  {'─'*5} {'─'*8} {'─'*10} {'─'*9} {'─'*9} {'─'*10}")
    for plan in pareto_a[:5]:
        print(
            f"  {plan['rank']:<5} "
            f"{plan['delta_sri_pct']:>+7.1f}% "
            f"€{plan['capex_eur']:>9,.0f} "
            f"{plan['co2_saved_kg']:>9,.0f} "
            f"{str(plan['payback_years']):>9} "
            f"{plan['n_upgrades']:>10}"
        )

    # ── Detailed top-1 plan ───────────────────────────────────────────────────
    if pareto_a:
        best = pareto_a[0]
        print(f"\n  ╔═══ Best Plan: Rank #{best['rank']} ═══════════════════════════════╗")
        print(f"  │  SRI: {profile.current_sri_score:.1f}% → {best['proposed_sri']:.1f}%  "
              f"(Δ {best['delta_sri_pct']:+.1f}%)")
        print(f"  │  CapEx: €{best['capex_eur']:,.0f}  |  "
              f"CO₂ saved: {best['co2_saved_kg']:,.0f} kg/yr  |  "
              f"Payback: {best['payback_years']} yrs")
        print(f"  │")
        print(f"  │  Recommended Upgrades:")
        for u in best["upgrades"][:8]:
            print(f"  │    [{u['domain'][:15]:<15}]  "
                  f"{u['service_code']:<8}  L{u['from_level']}→L{u['to_level']}  "
                  f"€{u['cost_eur']:,.0f}")
        print(f"  ╚{'═'*55}╝")

    # ── Scenario B: Target Heating domain ────────────────────────────────────
    print("\n▶  Scenario B: Prioritise Heating Domain Improvement\n")
    opt_b = SRIOptimiser(
        profile=profile,
        target_domain="Heating",
        algorithm="nsga2",
        pop_size=max(120, 4 * profile.n_services),
        n_generations=300,
    )
    pareto_b = opt_b.run(verbose=False)

    if pareto_b:
        best_b = pareto_b[0]
        heating_delta = best_b["delta_domain"].get("Heating", 0.0)
        print(f"  Best Heating-focused plan: ΔHeating={heating_delta:+.1f}%  "
              f"ΔSRI={best_b['delta_sri_pct']:+.1f}%  "
              f"CapEx=€{best_b['capex_eur']:,.0f}")


# ─────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    data_directory = sys.argv[1] if len(sys.argv) > 1 else "."
    run_optimisation_example(data_dir=data_directory)

# ─────────────────────────────────────────────────────────────────────────────
#  DEPENDENCY NOTES
# ─────────────────────────────────────────────────────────────────────────────
# pip install pygmo numpy
#
# pygmo wheels are available for Python 3.8–3.11 on Linux/macOS/Windows.
# For M-series Macs:  conda install -c conda-forge pygmo
#
# Usage:
#   python sri_moo_pygmo.py /path/to/project/json/directory
#
# Expected JSON files in data_dir:
#   Heating_Domain_Weights.json, DHW_Domain_Weights.json,
#   Cooling_Domain_Weights.json, Ventilation_Domain_Weights.json,
#   Lighting_Domain_Weights.json, DE_Domain_Weights.json,
#   Electricity_Domain_Weights.json, EV_Charging_Domain_Weights.json,
#   MC_Domain_Weights.json,
#   non_residential_impact_weighting_factors.json  (or the residential variant)
# ─────────────────────────────────────────────────────────────────────────────
