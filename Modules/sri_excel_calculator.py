"""
Drive the official SRI v4.5 Excel calculation sheet from Python.

Unlike openpyxl (which only writes values and never recalculates formulas), this
uses **xlwings**, which automates a real Excel instance over COM — so the
workbook's formulas recalculate exactly as if you opened and edited the file by
hand. Requires Microsoft Excel installed (Windows / macOS).

Cell map (SRI_calculation-sheet_v4.5.xlsx)
------------------------------------------
Inputs  — 'Calculation' tab, one row per smart-ready service (rows 6..104):
    col B  service code            (e.g. "H-1a")        [read-only key]
    col I  service applicable?     (1 / 0)              [input]
    col J  main functionality level                     [input]
    col K  share of that level     (default 1 = 100%)   [input]
Outputs — 'Results' tab:
    F8        total SRI score      (fraction 0..1)
    J8        SRI class label
    F13:F19   impact scores  (7)
    F25:F33   domain scores  (9)

NOTE ON SPEED: each evaluation is a full Excel recalculation (tens of ms each).
This is ideal for single assessments or validating a handful of upgrade plans,
but far too slow to use as the inner loop of the NSGA-II optimiser (which does
~10^5 evaluations). Keep the in-Python SRIScoringEngine for optimisation and use
this wrapper to verify the final recommended plans against the official sheet.
"""
from __future__ import annotations

import json
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

import xlwings as xw

DEFAULT_WORKBOOK = (
    Path(__file__).resolve().parent.parent / "Docs" / "SRI_calculation-sheet_v4.5.xlsx"
)

CALC_SHEET = "Calculation"
RESULTS_SHEET = "Results"
BUILDING_SHEET = "Building Information"
FIRST_SERVICE_ROW = 6
LAST_SERVICE_ROW = 104

# Building Information input cells (column G). Climate zone (G21) is auto-derived
# from the location, so it is NOT set directly.
BUILDING_CELLS = {
    "type": "G18",          # "residential" | "non-residential"
    "usage": "G19",         # e.g. "Offices", "residential - single-family house"
    "location": "G20",      # country name; drives the climate zone
    "floor_area_band": "G23",
    "year_band": "G24",
    "state": "G25",         # "Original" | "Renovated"
    "weightings": "G37",    # "Default" | "User-defined"
    "method": "G39",        # "A" | "B" | "Custom"
}
# Domains-present inputs (G48:G56) — value 0 (absent), 1 (present), 2 (absent-mandatory)
DOMAIN_PRESENT_CELLS = {
    "Heating": "G48",
    "Domestic hot water": "G49",
    "Cooling": "G50",
    "Ventilation": "G51",
    "Lighting": "G52",
    "Dynamic building envelope": "G53",
    "Electricity": "G54",
    "Electric vehicle charging": "G55",
    "Monitoring and control": "G56",
}

IMPACT_LABELS = [
    "energy_efficiency", "energy_flexibility_and_storage", "comfort", "convenience",
    "health,_wellbeing_and_accessibility", "maintenance_and_fault_prediction",
    "information_to_occupants",
]
DOMAIN_LABELS = [
    "Heating", "Domestic hot water", "Cooling", "Ventilation", "Lighting",
    "Dynamic building envelope", "Electricity", "Electric vehicle charging",
    "Monitoring and control",
]


class SRIExcelCalculator:
    """
    Context manager that opens the SRI workbook in Excel once and lets you run
    many assessments against the live formula engine.

    Example
    -------
        with SRIExcelCalculator() as calc:
            result = calc.evaluate({"H-1a": 4, "H-1b": 3, "L-1a": 2})
            print(result["sri"], result["impacts"], result["domains"])
    """

    def __init__(self, workbook=DEFAULT_WORKBOOK, work_on_copy=True, visible=False):
        self.src = Path(workbook)
        self.work_on_copy = work_on_copy
        self.visible = visible
        self._tmp = None
        self._app = None
        self._wb = None
        self._code_to_row: dict[str, int] = {}

    # ---- lifecycle ----
    def __enter__(self):
        path = self.src
        if self.work_on_copy:
            self._tmp = Path(tempfile.mkdtemp()) / self.src.name
            shutil.copy2(self.src, self._tmp)
            path = self._tmp
        self._app = xw.App(visible=self.visible, add_book=False)
        self._app.display_alerts = False
        self._app.screen_updating = False
        self._wb = self._app.books.open(str(path))
        self._build_code_map()
        return self

    def __exit__(self, *exc):
        try:
            if self._wb is not None:
                self._wb.close()
        finally:
            if self._app is not None:
                self._app.quit()
            if self._tmp is not None:
                shutil.rmtree(self._tmp.parent, ignore_errors=True)

    # ---- internals ----
    def _build_code_map(self):
        ws = self._wb.sheets[CALC_SHEET]
        codes = ws.range(f"B{FIRST_SERVICE_ROW}:B{LAST_SERVICE_ROW}").value
        maxes = ws.range(f"AC{FIRST_SERVICE_ROW}:AC{LAST_SERVICE_ROW}").value  # max level
        self._max_levels = {}
        for i, code in enumerate(codes):
            if code:
                code = str(code).strip()
                self._code_to_row[code] = FIRST_SERVICE_ROW + i
                if isinstance(maxes[i], (int, float)):
                    self._max_levels[code] = int(maxes[i])

    @property
    def service_codes(self) -> list[str]:
        return list(self._code_to_row)

    @property
    def max_levels(self) -> dict[str, int]:
        """{service_code: max valid functionality level} read from the sheet."""
        return dict(self._max_levels)

    # ---- main API ----
    def evaluate(
        self,
        levels: dict[str, int],
        applicable: dict[str, int] | None = None,
        shares: dict[str, float] | None = None,
    ) -> dict:
        """
        Set functionality levels for the given service codes, recalculate, and
        return the official SRI results.

        Parameters
        ----------
        levels      : {service_code: functionality_level_int}
        applicable  : optional {service_code: 1|0} overrides for col I
        shares      : optional {service_code: fraction} overrides for col K

        Returns
        -------
        {
          "sri": float (0..100, %),
          "sri_class": str,
          "impacts": {criterion: pct},
          "domains": {domain: pct},
        }
        """
        calc = self._wb.sheets[CALC_SHEET]
        for code, lvl in levels.items():
            row = self._code_to_row.get(code)
            if row is None:
                raise KeyError(f"Unknown service code: {code!r}")
            calc.range(f"J{row}").value = int(lvl)
        if applicable:
            for code, a in applicable.items():
                calc.range(f"I{self._code_to_row[code]}").value = int(a)
        if shares:
            for code, s in shares.items():
                calc.range(f"K{self._code_to_row[code]}").value = float(s)

        self._app.calculate()
        return self._read_results()

    def _read_results(self) -> dict:
        res = self._wb.sheets[RESULTS_SHEET]
        sri = res.range("F8").value
        sri_class = res.range("J8").value
        impacts = res.range("F13:F19").value
        domains = res.range("F25:F33").value

        def pct(x):
            return round(x * 100, 2) if isinstance(x, (int, float)) else x

        return {
            "sri": pct(sri),
            "sri_class": sri_class,
            "impacts": {k: pct(v) for k, v in zip(IMPACT_LABELS, impacts)},
            "domains": {k: pct(v) for k, v in zip(DOMAIN_LABELS, domains)},
        }

    # ---- real assessment from a structured spec ----
    def set_building_info(self, building: dict):
        """Set the Building Information dropdowns from a dict (see BUILDING_CELLS).
        `domains_present` is a {domain_name: 0|1|2} sub-dict."""
        bi = self._wb.sheets[BUILDING_SHEET]
        for key, cell in BUILDING_CELLS.items():
            if key in building and building[key] is not None:
                bi.range(cell).value = building[key]
        for dom, val in (building.get("domains_present") or {}).items():
            cell = DOMAIN_PRESENT_CELLS.get(dom)
            if cell is None:
                raise KeyError(f"Unknown domain in domains_present: {dom!r}")
            bi.range(cell).value = int(val)

    def _reset_service_levels(self):
        """Zero every service's level and reset share to 100% for a clean slate."""
        calc = self._wb.sheets[CALC_SHEET]
        n = LAST_SERVICE_ROW - FIRST_SERVICE_ROW + 1
        calc.range(f"J{FIRST_SERVICE_ROW}:J{LAST_SERVICE_ROW}").value = [[0]] * n
        calc.range(f"K{FIRST_SERVICE_ROW}:K{LAST_SERVICE_ROW}").value = [[1]] * n

    @staticmethod
    def _flatten_services(assessment: dict) -> dict:
        """Accept either {'services': {...}} (flat) or {'domains': {dom: {...}}}
        (grouped). Each entry is a level int OR {'level','applicable','share'}."""
        flat = {}
        if "services" in assessment:
            flat.update(assessment["services"])
        for _dom, svcs in (assessment.get("domains") or {}).items():
            flat.update(svcs)
        return flat

    def run_assessment(self, assessment: dict, reset: bool = True,
                       validate: bool = True) -> dict:
        """
        Run a full SRI assessment from a structured spec and return the results.

        assessment = {
          "building": { "type","usage","location","state","weightings","method",
                        "domains_present": {<domain>: 0|1|2} },
          # services as a flat map ...
          "services": { "H-1a": 2, "L-1a": {"level":3,"applicable":1,"share":1.0} },
          # ... or grouped by domain (purely for readability):
          "domains":  { "Heating": {"H-1a": 2, "H-1b": 1}, "Lighting": {"L-1a": 3} }
        }

        With reset=True (default) every service starts at level 0 so the result
        depends only on this spec, not on the workbook's previously-saved state.
        """
        if "building" in assessment:
            self.set_building_info(assessment["building"])
        if reset:
            self._reset_service_levels()

        services = self._flatten_services(assessment)

        # normalise entries to (level, applicable, share)
        norm = {}
        for code, spec in services.items():
            if code not in self._code_to_row:
                raise KeyError(f"Unknown service code: {code!r}")
            if isinstance(spec, dict):
                lvl = spec.get("level", 0)
                appl = spec.get("applicable")
                share = spec.get("share")
            else:
                lvl, appl, share = spec, None, None
            norm[code] = (int(lvl), appl, share)

        if validate:
            bad = [
                f"{c} (level {lvl} > max {self._max_levels.get(c)})"
                for c, (lvl, _, _) in norm.items()
                if c in self._max_levels and lvl > self._max_levels[c]
            ]
            if bad:
                raise ValueError("Invalid functionality levels: " + "; ".join(bad))

        calc = self._wb.sheets[CALC_SHEET]
        for code, (lvl, appl, share) in norm.items():
            row = self._code_to_row[code]
            calc.range(f"J{row}").value = lvl
            if appl is not None:
                calc.range(f"I{row}").value = int(appl)
            if share is not None:
                calc.range(f"K{row}").value = float(share)

        self._app.calculate()
        return self._read_results()


@contextmanager
def open_calculator(**kwargs):
    with SRIExcelCalculator(**kwargs) as c:
        yield c


def assess_from_json(json_path, out_path=None, workbook=DEFAULT_WORKBOOK,
                     visible=False, reset=True) -> dict:
    """
    Run a real SRI assessment described by a JSON file and return the results
    (optionally writing them to `out_path` as JSON).

    The input JSON has the shape documented in SRIExcelCalculator.run_assessment.
    """
    assessment = json.loads(Path(json_path).read_text(encoding="utf-8"))
    with SRIExcelCalculator(workbook=workbook, visible=visible) as calc:
        result = calc.run_assessment(assessment, reset=reset)
    if out_path:
        Path(out_path).write_text(json.dumps(result, indent=2, ensure_ascii=False),
                                  encoding="utf-8")
    return result


if __name__ == "__main__":
    # Smoke test: read the current sheet state, then push a simple scenario.
    with SRIExcelCalculator() as calc:
        print(f"Workbook services found: {len(calc.service_codes)}")
        print(f"First 8 codes: {calc.service_codes[:8]}")

        # Baseline read (don't change anything that isn't already set)
        base = calc.evaluate({})
        print(f"\nAs-loaded SRI       : {base['sri']}%   class={base['sri_class']!r}")

        # Push all Heating services to their (valid) max level and re-read
        heat = {c: calc.max_levels[c] for c in calc.service_codes if c.startswith("H-")}
        scen = calc.evaluate(heat)
        print(f"Heating->max SRI    : {scen['sri']}%")
        print("Impact scores       :")
        for k, v in scen["impacts"].items():
            print(f"   {k:38s} {v}")
        print("Domain scores       :")
        for k, v in scen["domains"].items():
            print(f"   {k:30s} {v}")
