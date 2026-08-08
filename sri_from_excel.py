"""
Run real SRI work through the official Excel calculation sheet.

Everything here scores via Modules/sri_excel_calculator.py (xlwings -> live Excel
formula engine), so results are identical to the official workbook — the
weights/*.json defects never enter the picture.

Steps:
  1. assess   — score an assessment JSON        (Modules/Ballymun_Library_assessment.json)
  2. inline   — score an inline Python dict
  3. optimise — Excel-backed upgrade optimiser  (SRI/sri_moo_excel.py)  [SLOW]

Run:
    uv run python sri_from_excel.py            # default: assess
    uv run python sri_from_excel.py inline
    uv run python sri_from_excel.py optimise   # ~10-12 min (real Excel recalcs)
"""
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "Modules"))
sys.path.insert(0, str(ROOT / "SRI"))

from sri_excel_calculator import SRIExcelCalculator, assess_from_json  # noqa: E402


def print_report(title: str, result: dict) -> None:
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)
    print(f"  TOTAL SRI : {result['sri']}%   (class: {result['sri_class']})")
    print("\n  Impact scores")
    for k, v in result["impacts"].items():
        print(f"    {k:38s} {v:>6}%")
    print("\n  Domain scores")
    for k, v in result["domains"].items():
        print(f"    {k:30s} {v:>6}%")


# ---------------------------------------------------------------------------
# 1) From a JSON file
# ---------------------------------------------------------------------------
def run_from_json() -> dict:
    json_path = ROOT / "Modules" / "Ballymun_Library_assessment.json"
    out_path = ROOT / "Modules" / "Ballymun_Library_results.json"
    result = assess_from_json(json_path, out_path=out_path)
    print_report(f"Assessment from {json_path.name}", result)
    print(f"\n  Results written to: {out_path}")
    return result


# ---------------------------------------------------------------------------
# 2) From an inline dict (open Excel once, run one or more scenarios)
# ---------------------------------------------------------------------------
def run_inline() -> dict:
    assessment = {
        "building": {
            "type": "non-residential",
            "usage": "Offices",
            "location": "Ireland",
            "state": "Original",
            "weightings": "Default",
            "method": "B",
            "domains_present": {
                "Heating": 1, "Domestic hot water": 1, "Cooling": 1,
                "Ventilation": 1, "Lighting": 1, "Dynamic building envelope": 0,
                "Electricity": 1, "Electric vehicle charging": 0,
                "Monitoring and control": 1,
            },
        },
        # functionality levels per service, grouped by domain
        "domains": {
            "Heating": {"H-1a": 2, "H-1b": 1, "H-3": 2, "H-4": 1},
            "Lighting": {"L-1a": 2, "L-2": 3},
            "Monitoring and control": {"MC-3": 2, "MC-13": 2, "MC-29": 0},
        },
    }

    with SRIExcelCalculator(visible=False) as calc:
        # baseline: everything at level 0
        base = calc.run_assessment({"building": assessment["building"], "services": {}})
        # the actual assessment
        result = calc.run_assessment(assessment)

    print_report("Inline assessment (Offices, Ireland)", result)
    print(f"\n  Baseline (all level 0) SRI: {base['sri']}%"
          f"  ->  assessed SRI: {result['sri']}%")
    return result


# ---------------------------------------------------------------------------
# 3) Excel-backed upgrade optimiser  (SRI/sri_moo_excel.py)
# ---------------------------------------------------------------------------
# >>> PLUG REAL DATA IN HERE <<<
# Only `annual_energy_kwh` / `ENERGY_BREAKDOWN` are placeholders; the SRI side
# (levels, building info) already comes from the assessment JSON, and floor area
# is the real figure from the SRI export.
BUILDING_FLOOR_AREA_M2 = 846.0            # real: from the Ballymun SRI export
ANNUAL_ENERGY_KWH = 150_000               # PLACEHOLDER -> replace with metered kWh/yr
CO2_FACTOR_KG_PER_KWH = 0.233             # IE grid average, ~2024
ISO_BUILDING_TYPE = "Education buildings (schools)"   # ISO 52120 Annex A type
# Optional: the real end-use split. Until supplied, the optimiser falls back to
# DEFAULT_END_USE_SHARE (an assumption) and says so.
#   from sri_moo_optimizer import EnergyBreakdown
#   ENERGY_BREAKDOWN = EnergyBreakdown(heating_kwh=..., heating_aux_kwh=...,
#                                      cooling_kwh=..., cooling_aux_kwh=...,
#                                      dhw_kwh=..., ventilation_aux_kwh=...,
#                                      lighting_kwh=...)
ENERGY_BREAKDOWN = None


def run_optimiser(
    budget_eur: float = 25_000,
    pop_size: int = 40,
    generations: int = 25,
    assessment_path: Path | None = None,
    save: bool = True,
) -> list:
    """
    Find Pareto-optimal upgrade plans, scoring every candidate with the official
    Excel workbook (exact — no in-Python re-implementation).

    SLOW BY DESIGN: each unique candidate is a real Excel recalculation
    (~0.8 s). pop_size=40, generations=25 takes roughly 10-12 minutes. Raise
    both for a better front; the cost is linear in unique candidates.

    CO₂ caveat: while ANNUAL_ENERGY_KWH is a placeholder and ENERGY_BREAKDOWN is
    None, the ΔSRI and € figures are exact but the CO₂ column is indicative only.
    """
    from sri_moo_excel import (  # imported lazily: pulls in pymoo + Excel
        ExcelBuildingContext,
        print_summary,
        run_optimisation_excel,
    )

    assessment_path = assessment_path or ROOT / "Modules" / "Ballymun_Library_assessment.json"

    ctx = ExcelBuildingContext(
        floor_area_m2=BUILDING_FLOOR_AREA_M2,
        annual_energy_kwh=ANNUAL_ENERGY_KWH,
        budget_eur=budget_eur,
        co2_emission_factor=CO2_FACTOR_KG_PER_KWH,
        iso_building_type=ISO_BUILDING_TYPE,
        usage_type="non_residential",
        energy_breakdown=ENERGY_BREAKDOWN,
        target_impact_criteria=["energy_efficiency"],
    )

    solutions = run_optimisation_excel(
        assessment_path, ctx,
        pop_size=pop_size, generations=generations, seed=42, verbose=True,
    )

    if not solutions:
        print(f"\nNo feasible plans within €{budget_eur:,.0f} — try raising budget_eur.")
        return []

    baseline_sri = solutions[0].new_sri_score - solutions[0].sri_improvement
    print_summary(solutions, baseline_sri)

    if save:
        out_path = ROOT / "Modules" / "Ballymun_Library_upgrade_plans.json"
        out_path.write_text(json.dumps({
            "baseline_sri": round(baseline_sri, 2),
            "budget_eur": budget_eur,
            "energy_inputs_are_placeholders": ENERGY_BREAKDOWN is None,
            "plans": [asdict(s) for s in solutions],
        }, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n  {len(solutions)} plans written to: {out_path}")

    return solutions


STEPS = {"assess": run_from_json, "inline": run_inline, "optimise": run_optimiser}

if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "assess"
    if step not in STEPS:
        raise SystemExit(f"Unknown step {step!r}. Use one of: {', '.join(STEPS)}")
    STEPS[step]()
