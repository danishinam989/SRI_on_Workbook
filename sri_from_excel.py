"""
Example: run a real SRI assessment through the official Excel calculation sheet.

Drives Modules/sri_excel_calculator.py (xlwings -> live Excel formula engine).
Two ways are shown:
  1. From a JSON file  (Modules/example_assessment.json)
  2. From an inline Python dict

Run:  uv run python sri_from_excel.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "Modules"))

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
    json_path = ROOT / "Modules" / "example_assessment.json"
    out_path = ROOT / "Modules" / "example_results.json"
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


if __name__ == "__main__":
    run_from_json()
    run_inline()
