"""
===============================================================================
SRI Multi-Objective Optimization Engine (pygmo-based)
===============================================================================

Technical Proposal: Optimal Functionality Level Upgrades for Technical Building
Systems (TBS) to Improve the Smart Readiness Indicator (SRI).

Framework: EU Commission Delegated Regulation (EU) 2020/2155
Reference: SRI Calculation Framework v4.5

Author:  SRI Optimization Research Project
Version: 1.0.0
===============================================================================

MATHEMATICAL FORMULATION
========================

Decision Variables:
    x = [x_1, x_2, ..., x_N]  where N = number of assessed services (up to 54)
    Each x_i ∈ {current_level_i, current_level_i + 1, ..., max_level_i}
    (We only upgrade; never downgrade from the current assessed level.)

Objectives (all minimised in pygmo convention):
    f_1(x) = -ΔSRI(x)              Maximise overall SRI improvement
    f_2(x) = -ΔIC_target(x)        Maximise targeted Impact Category improvement
    f_3(x) = -ΔCO2(x)              Maximise CO2 reduction estimate
    f_4(x) =  Cost(x)              Minimise total capital expenditure

Constraints:
    g_1(x) = Cost(x) - Budget ≤ 0  Strict budget ceiling

    Because NSGA-II in pygmo handles only box constraints, we absorb the
    budget constraint into the fitness vector via a death-penalty approach:
    if Cost(x) > Budget, all objective values are set to a large penalty.

Integer Handling:
    All N decision variables are integers.  pygmo's get_nix() declares the
    integer dimension.  NSGA-II's SBX crossover and polynomial mutation
    operate in continuous space; pygmo automatically rounds the last nix
    variables to the nearest integer before passing them to fitness().

ALGORITHM SELECTION
===================
Primary:   NSGA-II (pg.nsga2)
Rationale:
  • Native support for multi-objective problems (2-4 objectives typical here).
  • Well-understood crowding-distance selection preserves Pareto front diversity.
  • SBX crossover + polynomial mutation work well after integer rounding.
  • Population-based: naturally explores the combinatorial space of ~54 discrete
    variables, each with 2-5 levels → search space up to ~3^54 ≈ 10^25.
  • pygmo's NSGA-II supports get_nix() for integer rounding out of the box.

Alternative: MOEA/D (pg.moead) for problems with >3 objectives where
             uniform reference-vector decomposition may yield better spread.

ARCHITECTURE OVERVIEW
=====================
                          ┌─────────────────────────┐
                          │   Building Profile &     │
                          │   Current SRI State      │
                          └────────────┬─────────────┘
                                       │
                          ┌────────────▼─────────────┐
                          │  SRI Scoring Engine       │
                          │  (mirrors official v4.5   │
                          │   calculation sheet)      │
                          └────────────┬─────────────┘
                                       │
    ┌──────────────────────────────────▼──────────────────────────────────┐
    │                     pygmo UDP: SRIUpgradeProblem                    │
    │                                                                     │
    │  fitness(x):                                                        │
    │    1. Decode x → proposed functionality levels per service           │
    │    2. Call SRI Scoring Engine → new SRI, Domain, Impact scores       │
    │    3. Estimate upgrade cost from cost catalogue                      │
    │    4. Estimate CO₂ reduction from energy model                      │
    │    5. Apply budget death-penalty if Cost > Budget                    │
    │    6. Return [-ΔSRI, -ΔIC_target, -ΔCO₂, Cost]                     │
    │                                                                     │
    │  get_bounds():  [current_levels, max_levels]                        │
    │  get_nobj():    4                                                   │
    │  get_nix():     N (all variables are integer)                       │
    └─────────────────────────────────┬───────────────────────────────────┘
                                      │
                          ┌───────────▼────────────┐
                          │  pg.algorithm(pg.nsga2) │
                          │  gen=500, pop=200       │
                          └───────────┬────────────┘
                                      │
                          ┌───────────▼────────────┐
                          │  Pareto Front Analysis  │
                          │  & Recommendation       │
                          └────────────────────────┘
"""

import json
import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np

try:
    import pygmo as pg
except ImportError:
    raise ImportError(
        "pygmo is required. Install via: conda install -c conda-forge pygmo"
    )


# =============================================================================
# 1. DATA LAYER — Load the official SRI service catalogues & weighting factors
# =============================================================================

# The 9 SRI Technical Domains
DOMAIN_NAMES = [
    "Heating", "DHW", "Cooling", "Ventilation", "Lighting",
    "DE", "Electricity", "EV_Charging", "MC"
]

# The 7 SRI Impact Criteria
IMPACT_CRITERIA = [
    "energy_efficiency",
    "energy_flexibility_and_storage",
    "comfort",
    "convenience",
    "health,_wellbeing_and_accessibility",
    "maintenance_and_fault_prediction",
    "information_to_occupants",
]

# Mapping from JSON impact criteria keys to the official weighting-factor keys
IMPACT_KEY_MAP = {
    "energy_efficiency": "Energy efficiency",
    "energy_flexibility_and_storage": "Energy flexibility and storage",
    "comfort": "Comfort",
    "convenience": "Convenience",
    "health,_wellbeing_and_accessibility": "Health, well-being and accessibility",
    "maintenance_and_fault_prediction": "Maintenance and fault prediction",
    "information_to_occupants": "Information to occupants",
}


@dataclass
class ServiceDefinition:
    """One smart-ready service from the official SRI catalogue."""
    code: str
    domain: str
    name: str
    max_level: int                              # Highest functionality level (0-indexed)
    impact_scores: dict[str, dict[str, int]]    # {criterion: {level_0: score, ...}}


@dataclass
class BuildingProfile:
    """All inputs needed to configure and run the optimisation."""
    usage_type: str                 # "residential" or "non_residential"
    climate_zone: str               # "West Europe", "North Europe", etc.
    floor_area_m2: float
    year_built: int
    location_country: str
    operational_hours: int          # Annual operating hours

    # Current assessed functionality levels: {service_code: current_int_level}
    current_levels: dict[str, int]

    # Which services are applicable to this building (subset of full catalogue)
    applicable_services: list[str]

    # Energy & Environment
    annual_energy_kwh: float
    annual_energy_cost_eur: float
    co2_emission_factor: float = 0.233   # kgCO2/kWh (Ireland 2024 grid average)
    solar_potential_kwp: float = 0.0
    geothermal_potential: bool = False

    # Financial constraint
    budget_eur: float = 50_000.0

    # Optimisation targets (which impact criteria to prioritise)
    target_impact_criteria: list[str] = field(default_factory=lambda: [
        "energy_efficiency"
    ])

    # Domains present in the building (1=present, 0=absent, 2=absent-mandatory)
    domains_present: dict[str, int] = field(default_factory=dict)


def load_service_catalogue(data_dir: str) -> list[ServiceDefinition]:
    """
    Load all 54 Method-B services from the 9 domain JSON files.

    Each JSON file (e.g. Heating_Domain_Weights.json) has the structure:
    {
        "1": {
            "code": "H-1a",
            "service": "Heat emission control",
            "functionality_levels": {"level_0": "...", "level_1": "...", ...},
            "impact_scores": {
                "energy_efficiency": {"level_0": 0, "level_1": 1, ...},
                ...
            }
        },
        ...
    }
    """
    catalogue: list[ServiceDefinition] = []

    domain_file_map = {
        "Heating": "Heating_Domain_Weights.json",
        "DHW": "DHW_Domain_Weights.json",
        "Cooling": "Cooling_Domain_Weights.json",
        "Ventilation": "Ventilation_Domain_Weights.json",
        "Lighting": "Lighting_Domain_Weights.json",
        "DE": "DE_Domain_Weights.json",
        "Electricity": "Electricity_Domain_Weights.json",
        "EV_Charging": "EV_Charging_Domain_Weights.json",
        "MC": "MC_Domain_Weights.json",
    }

    for domain_name, filename in domain_file_map.items():
        filepath = os.path.join(data_dir, filename)
        if not os.path.exists(filepath):
            continue
        with open(filepath, "r") as f:
            data = json.load(f)

        for _key, svc in data.items():
            max_level = len(svc["functionality_levels"]) - 1
            catalogue.append(ServiceDefinition(
                code=svc["code"],
                domain=domain_name,
                name=svc["service"],
                max_level=max_level,
                impact_scores=svc["impact_scores"],
            ))

    return catalogue



def load_weighting_factors(
    data_dir: str,
    usage_type: str,
    climate_zone: str,
) -> tuple[dict, dict]:
    """
    Load domain weightings and impact weightings for this building context.

    Returns:
        domain_weights: {domain_name: {impact_criterion: weight}}
        impact_weights: {impact_criterion: weight}
    """
    filename = (
        "residential_impact_weighting_factors.json"
        if usage_type == "residential"
        else "non_residential_impact_weighting_factors.json"
    )
    filepath = os.path.join(data_dir, filename)
    with open(filepath, "r") as f:
        all_weights = json.load(f)

    # Handle the nested structure: {title: ..., climate_zones: {zone: data}}
    if "climate_zones" in all_weights:
        all_weights = all_weights["climate_zones"]

    zone_data = all_weights.get(climate_zone, {})

    # Map the official domain names to our internal names
    official_to_internal = {
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

    domain_weights = {}
    for official_name, internal_name in official_to_internal.items():
        if official_name in zone_data.get("domain_weightings", {}):
            domain_weights[internal_name] = {}
            for off_ic, weight in zone_data["domain_weightings"][official_name].items():
                # Find the internal key
                for internal_ic, official_ic in IMPACT_KEY_MAP.items():
                    if official_ic == off_ic:
                        domain_weights[internal_name][internal_ic] = weight
                        break

    impact_weights = {}
    for off_ic, weight in zone_data.get("impact_weightings", {}).items():
        for internal_ic, official_ic in IMPACT_KEY_MAP.items():
            if official_ic == off_ic:
                impact_weights[internal_ic] = weight
                break

    return domain_weights, impact_weights


# =============================================================================
# 2. SRI SCORING ENGINE — Mirrors the official v4.5 calculation methodology
# =============================================================================

class SRIScoringEngine:
    """
    Replicates the SRI v4.5 multi-criteria scoring methodology.

    Aggregation pipeline:
        Service levels → (impact scores per criterion)
            → Domain scores (equal weighting within domain)
            → Impact scores (domain weights × domain scores, per criterion)
            → Single SRI score (impact weights × impact scores)

    Normalisation:
        score_normalised = (achieved - minimum) / (maximum - minimum) × 100%
    """

    def __init__(
        self,
        catalogue: list[ServiceDefinition],
        domain_weights: dict,
        impact_weights: dict,
        applicable_services: list[str],
        domains_present: dict[str, int],
    ):
        self.catalogue = catalogue
        self.domain_weights = domain_weights
        self.impact_weights = impact_weights
        self.applicable_services = set(applicable_services)
        self.domains_present = domains_present

        # Build lookup: code → ServiceDefinition
        self.service_lookup: dict[str, ServiceDefinition] = {
            svc.code: svc for svc in catalogue
        }

        # Pre-compute min/max scores for normalisation
        self._precompute_normalisation_bounds()

    def _precompute_normalisation_bounds(self):
        """
        Per the SRI v4.5 methodology:
        - Minimum score: all applicable services at functionality level 0
        - Maximum score: all applicable services at their maximum level
        - For 'absent but mandatory' domains, services contribute to max score
        """
        self.min_scores_by_domain: dict[str, dict[str, float]] = {}
        self.max_scores_by_domain: dict[str, dict[str, float]] = {}

        for domain in DOMAIN_NAMES:
            self.min_scores_by_domain[domain] = {ic: 0.0 for ic in IMPACT_CRITERIA}
            self.max_scores_by_domain[domain] = {ic: 0.0 for ic in IMPACT_CRITERIA}

            domain_services = [
                s for s in self.catalogue
                if s.domain == domain and s.code in self.applicable_services
            ]

            for svc in domain_services:
                for ic in IMPACT_CRITERIA:
                    if ic in svc.impact_scores:
                        scores = svc.impact_scores[ic]
                        min_score = scores.get("level_0", 0)
                        max_score = scores.get(f"level_{svc.max_level}", 0)
                        self.min_scores_by_domain[domain][ic] += min_score
                        self.max_scores_by_domain[domain][ic] += max_score

    def compute_scores(
        self,
        levels: dict[str, int],
    ) -> tuple[float, dict[str, float], dict[str, float]]:
        """
        Compute the full SRI score breakdown for a given set of functionality levels.

        Args:
            levels: {service_code: functionality_level_int}

        Returns:
            (overall_sri_score, domain_scores, impact_scores)
            All scores are percentages in [0, 100].
        """
        # --- Step 1: Raw scores per domain per impact criterion ---
        raw_by_domain: dict[str, dict[str, float]] = {
            d: {ic: 0.0 for ic in IMPACT_CRITERIA} for d in DOMAIN_NAMES
        }

        for code, level in levels.items():
            if code not in self.applicable_services:
                continue
            svc = self.service_lookup.get(code)
            if svc is None:
                continue
            for ic in IMPACT_CRITERIA:
                if ic in svc.impact_scores:
                    score = svc.impact_scores[ic].get(f"level_{level}", 0)
                    raw_by_domain[svc.domain][ic] += score

        # --- Step 2: Normalised domain scores per impact criterion ---
        normalised_domain: dict[str, dict[str, float]] = {}
        for domain in DOMAIN_NAMES:
            normalised_domain[domain] = {}
            for ic in IMPACT_CRITERIA:
                raw = raw_by_domain[domain][ic]
                mn = self.min_scores_by_domain[domain][ic]
                mx = self.max_scores_by_domain[domain][ic]
                if mx - mn > 0:
                    normalised_domain[domain][ic] = (raw - mn) / (mx - mn) * 100.0
                else:
                    normalised_domain[domain][ic] = 0.0

        # --- Step 3: Impact scores (weighted aggregation of domain scores) ---
        impact_scores: dict[str, float] = {}
        for ic in IMPACT_CRITERIA:
            weighted_sum = 0.0
            total_weight = 0.0
            for domain in DOMAIN_NAMES:
                present = self.domains_present.get(domain, 0)
                if present == 0:
                    continue  # Absent and not mandatory — skip entirely
                w = self.domain_weights.get(domain, {}).get(ic, 0.0)
                # Per SRI v4.5: if no applicable service in this domain contributes
                # to this criterion (zero normalisation range), its weight is forced
                # to zero. Without this the domain adds 0 to the numerator but its
                # weight to the denominator, artificially diluting the impact score.
                contributes = (
                    self.max_scores_by_domain[domain][ic]
                    - self.min_scores_by_domain[domain][ic]
                ) > 0
                if w > 0 and contributes:
                    weighted_sum += w * normalised_domain[domain][ic]
                    total_weight += w

            if total_weight > 0:
                impact_scores[ic] = weighted_sum / total_weight
            else:
                impact_scores[ic] = 0.0

        # --- Step 4: Overall SRI score (weighted aggregation of impact scores) ---
        sri_score = 0.0
        total_iw = 0.0
        for ic in IMPACT_CRITERIA:
            w = self.impact_weights.get(ic, 0.0)
            sri_score += w * impact_scores[ic]
            total_iw += w

        if total_iw > 0:
            sri_score /= total_iw

        # --- Step 5: Aggregate domain scores (average across impact criteria) ---
        domain_scores: dict[str, float] = {}
        for domain in DOMAIN_NAMES:
            vals = [
                normalised_domain[domain][ic]
                for ic in IMPACT_CRITERIA
                if self.max_scores_by_domain[domain][ic]
                - self.min_scores_by_domain[domain][ic] > 0
            ]
            domain_scores[domain] = np.mean(vals) if vals else 0.0

        return sri_score, domain_scores, impact_scores


# =============================================================================
# 3. COST & CO₂ ESTIMATION MODELS
# =============================================================================

class UpgradeCostEstimator:
    """
    Estimates the capital expenditure for upgrading services from one
    functionality level to another.

    In production, this would be backed by a detailed cost database
    (per-service, per-level, per-country pricing from market research).
    Here we provide a structured placeholder with realistic cost ranges
    that should be replaced with actual market data.
    """

    # Indicative cost ranges per domain (EUR per service per level increment)
    # These are placeholder values — replace with your EU market research data
    DOMAIN_COST_PER_LEVEL = {
        "Heating":      {"base": 2000, "per_level": 3500},
        "DHW":          {"base": 1500, "per_level": 2500},
        "Cooling":      {"base": 2500, "per_level": 4000},
        "Ventilation":  {"base": 1800, "per_level": 3000},
        "Lighting":     {"base":  800, "per_level": 1500},
        "DE":           {"base": 3000, "per_level": 5000},
        "Electricity":  {"base": 2000, "per_level": 3500},
        "EV_Charging":  {"base": 2500, "per_level": 4500},
        "MC":           {"base": 1000, "per_level": 2000},
    }

    def __init__(
        self,
        catalogue: list[ServiceDefinition],
        floor_area_m2: float,
        custom_costs: Optional[dict] = None,
    ):
        self.service_lookup = {svc.code: svc for svc in catalogue}
        self.floor_area_m2 = floor_area_m2
        self.custom_costs = custom_costs or {}

    def estimate_upgrade_cost(
        self,
        service_code: str,
        from_level: int,
        to_level: int,
    ) -> float:
        """
        Estimate the cost to upgrade a single service.

        The cost model applies a non-linear scaling: higher levels cost
        progressively more (reflecting real-world diminishing returns and
        increased technology sophistication).
        """
        if to_level <= from_level:
            return 0.0

        # Check for custom per-service cost overrides
        if service_code in self.custom_costs:
            custom = self.custom_costs[service_code]
            return sum(
                custom.get(f"level_{l}", 0.0)
                for l in range(from_level + 1, to_level + 1)
            )

        svc = self.service_lookup.get(service_code)
        if svc is None:
            return 0.0

        domain_costs = self.DOMAIN_COST_PER_LEVEL.get(svc.domain, {"base": 1000, "per_level": 2000})

        total = 0.0
        for level in range(from_level + 1, to_level + 1):
            # Non-linear cost scaling: cost increases with level
            # level_factor: 1.0 for level 1, 1.3 for level 2, 1.7 for level 3, 2.2 for level 4
            level_factor = 1.0 + 0.3 * (level - 1)
            # Area scaling: costs scale sub-linearly with floor area
            area_factor = (self.floor_area_m2 / 200.0) ** 0.4  # Normalised to 200m²
            total += domain_costs["per_level"] * level_factor * area_factor

        return total

    def total_cost(
        self,
        current_levels: dict[str, int],
        proposed_levels: dict[str, int],
    ) -> float:
        """Sum of all individual service upgrade costs."""
        total = 0.0
        for code, new_level in proposed_levels.items():
            old_level = current_levels.get(code, 0)
            total += self.estimate_upgrade_cost(code, old_level, new_level)
        return total


class CO2ReductionEstimator:
    """
    Estimates annual CO₂ reduction from SRI-driven upgrades.

    The model links SRI domain improvements to estimated energy savings
    percentages, then converts to CO₂ using the grid emission factor.

    NOTE: As established in our research, SRI scores represent smart-readiness
    potential rather than direct energy savings. This estimator provides
    indicative figures; actual savings depend on building operation, occupant
    behaviour, and system integration quality.
    """

    # Estimated max energy saving potential per domain (% of domain energy use)
    # These are conservative estimates based on building energy research
    DOMAIN_SAVINGS_POTENTIAL = {
        "Heating":      0.25,   # Up to 25% savings from smart heating controls
        "DHW":          0.15,   # Up to 15% from smart DHW management
        "Cooling":      0.20,   # Up to 20% from smart cooling optimisation
        "Ventilation":  0.15,   # Up to 15% from demand-controlled ventilation
        "Lighting":     0.30,   # Up to 30% from smart lighting controls
        "DE":           0.10,   # Up to 10% from dynamic envelope
        "Electricity":  0.12,   # Up to 12% from smart energy management
        "EV_Charging":  0.05,   # Up to 5% grid flexibility benefit
        "MC":           0.08,   # Up to 8% from monitoring & control
    }

    # Approximate energy share per domain (will be overridden by actual data)
    DEFAULT_ENERGY_SHARE = {
        "Heating":      0.40,
        "DHW":          0.15,
        "Cooling":      0.10,
        "Ventilation":  0.08,
        "Lighting":     0.10,
        "DE":           0.02,
        "Electricity":  0.10,
        "EV_Charging":  0.03,
        "MC":           0.02,
    }

    def __init__(
        self,
        annual_energy_kwh: float,
        co2_factor: float,
        energy_shares: Optional[dict[str, float]] = None,
    ):
        self.annual_energy_kwh = annual_energy_kwh
        self.co2_factor = co2_factor
        self.energy_shares = energy_shares or self.DEFAULT_ENERGY_SHARE

    def estimate_co2_reduction(
        self,
        domain_score_baseline: dict[str, float],
        domain_score_proposed: dict[str, float],
    ) -> float:
        """
        Estimate annual CO₂ reduction (kg) from domain score improvements.

        The reduction is proportional to the domain score improvement (0-100%)
        scaled by the domain's energy share and savings potential.
        """
        total_co2_saved = 0.0

        for domain in DOMAIN_NAMES:
            baseline = domain_score_baseline.get(domain, 0.0)
            proposed = domain_score_proposed.get(domain, 0.0)
            improvement_fraction = max(0.0, (proposed - baseline) / 100.0)

            energy_share = self.energy_shares.get(domain, 0.0)
            savings_potential = self.DOMAIN_SAVINGS_POTENTIAL.get(domain, 0.0)

            domain_energy_kwh = self.annual_energy_kwh * energy_share
            energy_saved_kwh = domain_energy_kwh * savings_potential * improvement_fraction
            total_co2_saved += energy_saved_kwh * self.co2_factor

        return total_co2_saved


# =============================================================================
# 4. PYGMO USER-DEFINED PROBLEM (UDP)
# =============================================================================

class SRIUpgradeProblem:
    """
    pygmo-compatible User Defined Problem for SRI upgrade optimisation.

    Decision vector x has N components (one per applicable service).
    x_i ∈ {current_level_i, ..., max_level_i}  (integer)

    Fitness vector (all minimised):
        [  -ΔSRI,  -ΔIC_target,  -ΔCO₂,  Cost  ]

    Budget constraint handled via death penalty (since NSGA-II supports
    only box constraints).
    """

    def __init__(
        self,
        scoring_engine: SRIScoringEngine,
        cost_estimator: UpgradeCostEstimator,
        co2_estimator: CO2ReductionEstimator,
        building: BuildingProfile,
        service_order: list[str],
    ):
        self.scoring_engine = scoring_engine
        self.cost_estimator = cost_estimator
        self.co2_estimator = co2_estimator
        self.building = building
        self.service_order = service_order  # Ordered list of service codes
        self.n_services = len(service_order)

        # Pre-compute baseline scores
        self.baseline_levels = {
            code: building.current_levels.get(code, 0)
            for code in service_order
        }
        (
            self.baseline_sri,
            self.baseline_domain_scores,
            self.baseline_impact_scores,
        ) = scoring_engine.compute_scores(self.baseline_levels)

        # Pre-compute bounds
        catalogue_lookup = {s.code: s for s in scoring_engine.catalogue}
        self._lower = [
            building.current_levels.get(code, 0)
            for code in service_order
        ]
        self._upper = [
            catalogue_lookup[code].max_level
            for code in service_order
        ]

        # Large penalty value for infeasible solutions
        self._penalty = 1e8

    # ---- Mandatory pygmo UDP methods ----

    def fitness(self, x: np.ndarray) -> list[float]:
        """
        Evaluate the fitness of a decision vector.

        Args:
            x: numpy array of length N (integer functionality levels)

        Returns:
            [f1, f2, f3, f4] — four objective values (all to be minimised)
        """
        # Decode decision vector into service levels
        proposed_levels = {
            code: int(round(x[i]))
            for i, code in enumerate(self.service_order)
        }

        # Compute upgrade cost
        cost = self.cost_estimator.total_cost(self.baseline_levels, proposed_levels)

        # ---- Death penalty for budget violation ----
        if cost > self.building.budget_eur:
            return [self._penalty, self._penalty, self._penalty, self._penalty]

        # Compute new SRI scores
        new_sri, new_domain_scores, new_impact_scores = (
            self.scoring_engine.compute_scores(proposed_levels)
        )

        # Objective 1: Maximise overall SRI improvement → minimise negative
        delta_sri = new_sri - self.baseline_sri
        f1 = -delta_sri

        # Objective 2: Maximise targeted impact category improvement
        target_improvement = 0.0
        for ic in self.building.target_impact_criteria:
            baseline_ic = self.baseline_impact_scores.get(ic, 0.0)
            new_ic = new_impact_scores.get(ic, 0.0)
            target_improvement += (new_ic - baseline_ic)
        if len(self.building.target_impact_criteria) > 0:
            target_improvement /= len(self.building.target_impact_criteria)
        f2 = -target_improvement

        # Objective 3: Maximise CO₂ reduction
        co2_reduction = self.co2_estimator.estimate_co2_reduction(
            self.baseline_domain_scores, new_domain_scores
        )
        f3 = -co2_reduction

        # Objective 4: Minimise capital cost
        f4 = cost

        return [f1, f2, f3, f4]

    def get_bounds(self) -> tuple[list[int], list[int]]:
        """Return box bounds. Integer bounds must be actual integers."""
        return (self._lower, self._upper)

    # ---- Optional pygmo UDP methods ----

    def get_nobj(self) -> int:
        """Number of objectives."""
        return 4

    def get_nix(self) -> int:
        """
        Number of integer decision variables.

        CRITICAL: This tells pygmo that ALL N variables are integers.
        pygmo convention: the last nix variables in the decision vector
        are treated as integers.  Since ALL our variables are integers,
        nix = N.  We arrange bounds accordingly.
        """
        return self.n_services

    def get_name(self) -> str:
        return "SRI Multi-Objective Upgrade Optimisation"

    def get_extra_info(self) -> str:
        return (
            f"Services: {self.n_services}\n"
            f"Baseline SRI: {self.baseline_sri:.1f}%\n"
            f"Budget: €{self.building.budget_eur:,.0f}\n"
            f"Objectives: [max ΔSRI, max ΔIC_target, max ΔCO₂, min Cost]"
        )


# =============================================================================
# 5. OPTIMISATION RUNNER & PARETO FRONT ANALYSIS
# =============================================================================

@dataclass
class ParetoSolution:
    """A single solution on the Pareto front."""
    service_levels: dict[str, int]
    sri_improvement: float
    impact_improvement: float
    co2_reduction_kg: float
    cost_eur: float
    new_sri_score: float
    new_domain_scores: dict[str, float]
    new_impact_scores: dict[str, float]
    upgrades_from_baseline: dict[str, tuple[int, int]]  # {code: (from, to)}


def run_optimisation(
    building: BuildingProfile,
    data_dir: str,
    pop_size: int = 200,
    generations: int = 500,
    seed: int = 42,
    verbose: bool = True,
) -> list[ParetoSolution]:
    """
    Execute the full SRI multi-objective optimisation pipeline.

    Args:
        building:    Complete building profile with current state
        data_dir:    Path to the directory containing the JSON data files
        pop_size:    NSGA-II population size (recommend ≥ 4× number of services)
        generations: Number of evolutionary generations
        seed:        Random seed for reproducibility
        verbose:     Print progress information

    Returns:
        List of ParetoSolution objects representing the non-dominated front.
    """
    # ---- Load data ----
    if verbose:
        print("=" * 70)
        print("SRI MULTI-OBJECTIVE UPGRADE OPTIMISATION")
        print("=" * 70)
        print(f"\n[1/6] Loading service catalogue from {data_dir}...")

    catalogue = load_service_catalogue(data_dir)
    domain_weights, impact_weights = load_weighting_factors(
        data_dir, building.usage_type, building.climate_zone
    )

    if verbose:
        print(f"       Loaded {len(catalogue)} services across {len(DOMAIN_NAMES)} domains")

    # ---- Filter to applicable services ----
    applicable = [
        svc for svc in catalogue
        if svc.code in building.applicable_services
    ]
    service_order = [svc.code for svc in applicable]

    if verbose:
        print(f"[2/6] Applicable services for this building: {len(service_order)}")

    # ---- Initialise engines ----
    scoring_engine = SRIScoringEngine(
        catalogue=catalogue,
        domain_weights=domain_weights,
        impact_weights=impact_weights,
        applicable_services=building.applicable_services,
        domains_present=building.domains_present,
    )

    cost_estimator = UpgradeCostEstimator(
        catalogue=catalogue,
        floor_area_m2=building.floor_area_m2,
    )

    co2_estimator = CO2ReductionEstimator(
        annual_energy_kwh=building.annual_energy_kwh,
        co2_factor=building.co2_emission_factor,
    )

    # ---- Create pygmo UDP ----
    if verbose:
        print("[3/6] Constructing pygmo problem...")

    udp = SRIUpgradeProblem(
        scoring_engine=scoring_engine,
        cost_estimator=cost_estimator,
        co2_estimator=co2_estimator,
        building=building,
        service_order=service_order,
    )

    prob = pg.problem(udp)

    if verbose:
        print(f"\n{prob}\n")

    # ---- Configure NSGA-II ----
    if verbose:
        print(f"[4/6] Configuring NSGA-II (pop={pop_size}, gen={generations})...")

    algo = pg.algorithm(
        pg.nsga2(
            gen=generations,
            cr=0.9,       # Crossover probability (SBX)
            eta_c=15.0,   # Crossover distribution index (higher = more exploitative)
            m=0.1,        # Mutation probability (polynomial)
            eta_m=20.0,   # Mutation distribution index
            seed=seed,
        )
    )

    if verbose:
        algo.set_verbosity(50)  # Log every 50 generations

    # ---- Initialise population ----
    if verbose:
        print("[5/6] Initialising population and evolving...")

    pop = pg.population(prob, size=pop_size, seed=seed)

    # ---- Evolve ----
    pop = algo.evolve(pop)

    # ---- Extract Pareto front ----
    if verbose:
        print("\n[6/6] Extracting Pareto-optimal solutions...")

    fits = pop.get_f()
    vectors = pop.get_x()

    # Non-dominated sorting
    ndf, dl, dc, ndr = pg.fast_non_dominated_sorting(fits)
    pareto_indices = ndf[0]  # First front = non-dominated solutions

    if verbose:
        print(f"       Found {len(pareto_indices)} Pareto-optimal solutions")

    # ---- Build ParetoSolution objects ----
    solutions: list[ParetoSolution] = []

    for idx in pareto_indices:
        x = vectors[idx]
        f = fits[idx]

        # Skip penalised (infeasible) solutions
        if f[0] >= 1e7:
            continue

        proposed_levels = {
            code: int(round(x[i]))
            for i, code in enumerate(service_order)
        }

        new_sri, new_domain, new_impact = scoring_engine.compute_scores(proposed_levels)
        cost = cost_estimator.total_cost(
            {code: building.current_levels.get(code, 0) for code in service_order},
            proposed_levels,
        )

        # Identify which services were actually upgraded
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

    # Sort by SRI improvement (descending)
    solutions.sort(key=lambda s: s.sri_improvement, reverse=True)

    return solutions


def print_pareto_summary(solutions: list[ParetoSolution], top_n: int = 10):
    """Print a formatted summary of the top Pareto solutions."""
    print("\n" + "=" * 90)
    print("PARETO-OPTIMAL UPGRADE RECOMMENDATIONS")
    print("=" * 90)
    print(
        f"{'#':>3}  {'ΔSRI':>8}  {'New SRI':>8}  {'ΔIC Target':>10}  "
        f"{'CO₂ Saved':>10}  {'Cost (€)':>10}  {'Upgrades':>8}"
    )
    print("-" * 90)

    for i, sol in enumerate(solutions[:top_n]):
        print(
            f"{i+1:>3}  {sol.sri_improvement:>7.1f}%  {sol.new_sri_score:>7.1f}%  "
            f"{sol.impact_improvement:>9.1f}%  {sol.co2_reduction_kg:>8.0f}kg  "
            f"€{sol.cost_eur:>9,.0f}  {len(sol.upgrades_from_baseline):>8}"
        )

    print("-" * 90)

    if solutions:
        best = solutions[0]
        print(f"\n--- BEST SRI IMPROVEMENT (Solution #1) ---")
        print(f"    New SRI Score: {best.new_sri_score:.1f}% (+{best.sri_improvement:.1f}%)")
        print(f"    Cost:          €{best.cost_eur:,.0f}")
        print(f"    CO₂ Saved:     {best.co2_reduction_kg:.0f} kg/year")
        print(f"    Upgrades Required:")
        svc_lookup = {}
        for sol in solutions:
            for code in sol.upgrades_from_baseline:
                svc_lookup[code] = code  # placeholder

        for code, (old, new) in best.upgrades_from_baseline.items():
            print(f"      • {code}: Level {old} → Level {new}")


# =============================================================================
# 6. EXAMPLE USAGE — Demonstrating the full pipeline
# =============================================================================

def create_example_building() -> BuildingProfile:
    """
    Create an example non-residential building (sports centre) in Ireland
    for demonstration purposes.
    """
    # Define applicable services (Method B subset for a sports facility)
    applicable = [
        # Heating
        "H-1a", "H-1b", "H-1c", "H-1d", "H-1f", "H-2a", "H-2b", "H-2d", "H-3", "H-4",
        
        # DHW
        # "DHW-1a", "DHW-2b", "DHW-3",
        
        # Cooling (limited in Irish climate)
        # "C-1a", "C-2a",
        
        # Ventilation
        # "V-1a", "V-1c", "V-2c", "V-2d", "V-3", "V-6",
        
        # Lighting
        "L-1a", "L-2",
        
        # Dynamic Envelope
        # "DE-1",
        
        # Electricity
        "E-2", "E-3", "E-4", "E-5", "E-8", "E-11", "E-12",
        
        # EV Charging
        # "EV-15", "EV-16",
        
        # Monitoring & Control
        "MC-3", "MC-4", "MC-9", "MC-13", "MC-25", "MC-28", "MC-29", "MC-30",
    ]

    # Current functionality levels (baseline assessment)
    current_levels = {
        "H-1a": 0, "H-1b": 0, "H-1c": 0, "H-1d": 0, "H-1f": 0, "H-2a": 0, "H-2b": 0, "H-2d": 0, "H-3": 0, "H-4": 1,
        
        # "DHW-1a": 1, "DHW-2b": 0, "DHW-3": 0,
        
        # "C-1a": 0, "C-2a": 0,
        
        # "V-1a": 1, "V-1c": 0, "V-2c": 0, "V-3": 0, "V-6": 0,
        
        "L-1a": 0, "L-2": 0,
        
        # "DE-1": 0,
        
        "E-2": 0, "E-3": 0, "E-4": 0, "E-5": 0, "E-8": 0, "E-11": 0, "E-12": 1,
        
        # "EV-15": 0, "EV-16": 0,
        
        # "MC-3": 0, "MC-4": 0, "MC-9": 0, "MC-13": 0, "MC-25": 0, "MC-28": 0, "MC-29": 0, "MC-30": 0,
    }

    domains_present = {
        "Heating": 1, "DHW": 1, "Cooling": 1, "Ventilation": 1,
        "Lighting": 1, "DE": 1, "Electricity": 1, "EV_Charging": 1, "MC": 1,
    }

    return BuildingProfile(
        usage_type="non_residential",
        climate_zone="West Europe",
        floor_area_m2=1500.0,
        year_built=1990,
        location_country="Ireland",
        operational_hours=3500,
        current_levels=current_levels,
        applicable_services=applicable,
        annual_energy_kwh=279_373,
        annual_energy_cost_eur=73_151,
        co2_emission_factor=0.233,
        solar_potential_kwp=100.0,
        geothermal_potential=False,
        budget_eur=20_000,
        target_impact_criteria=["energy_efficiency", "comfort"],
        domains_present=domains_present,
    )


# =============================================================================
# 7. MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # Path to your project data directory containing the JSON files
    DATA_DIR = "./weights"

    # Create building profile
    building = create_example_building()

    print(f"Building: {building.usage_type} | {building.location_country}")
    print(f"Floor area: {building.floor_area_m2:,.0f} m²")
    print(f"Annual energy: {building.annual_energy_kwh:,.0f} kWh")
    print(f"Budget: €{building.budget_eur:,.0f}")
    print(f"Target criteria: {building.target_impact_criteria}")

    # Run optimisation
    solutions = run_optimisation(
        building=building,
        data_dir=DATA_DIR,
        pop_size=200,       # Recommend ≥ 4× number of services
        generations=500,     # 300-500 typical for convergence
        seed=42,
        verbose=True,
    )

    # Print results
    if solutions:
        print_pareto_summary(solutions, top_n=10)
    else:
        print("\nNo feasible solutions found within the budget constraint.")
        print("Consider increasing the budget or relaxing the target criteria.")
