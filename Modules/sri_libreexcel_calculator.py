"""
Drive the official SRI v4.5 Excel calculation sheet from Python — via
**LibreOffice headless + the UNO API** instead of Excel/COM. Runs natively on
Linux (the production Ubuntu box), no Windows or Microsoft Excel required.

Drop-in replacement for `sri_excel_calculator.py`: same cell map, same public
API (`evaluate`, `run_assessment`, `set_building_info`, `assess_from_json`,
`service_codes`, `max_levels`, `open_calculator`). Only the automation
backend changed, so a caller (e.g. a FastAPI `/sri/calculate` endpoint) can
swap the import with no other code changes.

Prerequisites (Ubuntu)
----------------------
    sudo apt install libreoffice-calc python3-uno
`python3-uno` installs the `uno` / `unohelper` modules for the *system*
python3 (unlike xlwings, no bundled-interpreter gymnastics needed). Verify
with `python3 -c "import uno"`.

Architecture
------------
Starting `soffice` itself takes several seconds, so spinning up a fresh
process per assessment (the way the xlwings version spins up a fresh Excel
per `with` block) would be too slow for an API. Instead a single headless
`soffice` listener is kept running, and each assessment just opens/edits/
closes a *document* inside that already-running process — cheap.

`SRILibreCalculator` will auto-start a listener on first use if none is
found on the configured host/port. In production, prefer running one
persistently (e.g. via systemd) so the autostart path is never hit:

    ExecStart=/usr/bin/soffice --headless --invisible --nocrashreport \\
        --nodefault --norestore --nologo --nofirststartwizard \\
        --accept="socket,host=localhost,port=2002;urp;"

Cell map (SRI_calculation-sheet_v4.5.xlsx) — identical to sri_excel_calculator.py
---------------------------------------------------------------------------
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
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

import uno
from com.sun.star.beans import PropertyValue
from com.sun.star.connection import NoConnectException

DEFAULT_WORKBOOK = (
    Path(__file__).resolve().parent.parent / "Docs" / "SRI_calculation-sheet_v4.5.xlsx"
)

CALC_SHEET = "Calculation"
RESULTS_SHEET = "Results"
BUILDING_SHEET = "Building Information"
FIRST_SERVICE_ROW = 6
LAST_SERVICE_ROW = 104

UNO_HOST = "localhost"
UNO_PORT = 2002
SOFFICE_START_TIMEOUT = 30.0  # seconds to wait for a freshly-launched soffice

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


def _prop(name: str, value):
    p = PropertyValue()
    p.Name = name
    p.Value = value
    return p


def _connect(host: str = UNO_HOST, port: int = UNO_PORT, autostart: bool = True,
             start_timeout: float = SOFFICE_START_TIMEOUT):
    """
    Connect to a headless soffice UNO listener at host:port, starting one if
    none is found (and autostart=True). Returns (desktop, started_proc) where
    started_proc is the subprocess.Popen we spawned, or None if we reused an
    already-running listener.
    """
    local_ctx = uno.getComponentContext()
    resolver = local_ctx.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local_ctx)
    uno_url = f"uno:socket,host={host},port={port};urp;StarOffice.ComponentContext"

    def _try_connect():
        ctx = resolver.resolve(uno_url)
        smgr = ctx.ServiceManager
        return smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)

    try:
        return _try_connect(), None
    except NoConnectException:
        if not autostart:
            raise

    proc = subprocess.Popen([
        "soffice", "--headless", "--invisible", "--nocrashreport",
        "--nodefault", "--norestore", "--nologo", "--nofirststartwizard",
        f"--accept=socket,host={host},port={port};urp;",
    ])
    deadline = time.monotonic() + start_timeout
    while time.monotonic() < deadline:
        try:
            return _try_connect(), proc
        except NoConnectException:
            time.sleep(0.5)
    proc.kill()
    raise RuntimeError(
        f"soffice did not accept UNO connections on {host}:{port} within "
        f"{start_timeout}s"
    )


class SRILibreCalculator:
    """
    Context manager that opens the SRI workbook in a headless LibreOffice
    listener and lets you run many assessments against the live formula
    engine — a drop-in swap for SRIExcelCalculator (Excel/xlwings) requiring
    no Windows/Excel.

    Example
    -------
        with SRILibreCalculator() as calc:
            result = calc.evaluate({"H-1a": 4, "H-1b": 3, "L-1a": 2})
            print(result["sri"], result["impacts"], result["domains"])
    """

    def __init__(self, workbook=DEFAULT_WORKBOOK, work_on_copy=True,
                 host: str = UNO_HOST, port: int = UNO_PORT, autostart: bool = True):
        self.src = Path(workbook)
        self.work_on_copy = work_on_copy
        self.host = host
        self.port = port
        self.autostart = autostart
        self._tmp = None
        self._desktop = None
        self._started_proc = None
        self._doc = None
        self._code_to_row: dict[str, int] = {}
        self._max_levels: dict[str, int] = {}

    # ---- lifecycle ----
    def __enter__(self):
        path = self.src
        if self.work_on_copy:
            self._tmp = Path(tempfile.mkdtemp()) / self.src.name
            shutil.copy2(self.src, self._tmp)
            path = self._tmp
        self._desktop, self._started_proc = _connect(
            self.host, self.port, autostart=self.autostart)
        url = uno.systemPathToFileUrl(str(path.resolve()))
        self._doc = self._desktop.loadComponentFromURL(
            url, "_blank", 0, (_prop("Hidden", True),))
        self._build_code_map()
        return self

    def __exit__(self, *exc):
        try:
            if self._doc is not None:
                self._doc.close(False)
        finally:
            if self._tmp is not None:
                shutil.rmtree(self._tmp.parent, ignore_errors=True)
            # Deliberately leave the soffice listener running (whether we
            # started it or reused one) — a long-lived listener is the whole
            # point of this backend; kill the process yourself (or stop the
            # systemd unit) if you need to recycle it.

    # ---- internals ----
    def _sheet(self, name: str):
        return self._doc.getSheets().getByName(name)

    def _build_code_map(self):
        ws = self._sheet(CALC_SHEET)
        for row in range(FIRST_SERVICE_ROW, LAST_SERVICE_ROW + 1):
            code = ws.getCellRangeByName(f"B{row}").getString().strip()
            if not code:
                continue
            self._code_to_row[code] = row
            raw_max = ws.getCellRangeByName(f"AC{row}").getString().strip()
            if raw_max:
                try:
                    self._max_levels[code] = int(float(raw_max))
                except ValueError:
                    pass

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
        calc = self._sheet(CALC_SHEET)
        for code, lvl in levels.items():
            row = self._code_to_row.get(code)
            if row is None:
                raise KeyError(f"Unknown service code: {code!r}")
            calc.getCellRangeByName(f"J{row}").setValue(int(lvl))
        if applicable:
            for code, a in applicable.items():
                calc.getCellRangeByName(f"I{self._code_to_row[code]}").setValue(int(a))
        if shares:
            for code, s in shares.items():
                calc.getCellRangeByName(f"K{self._code_to_row[code]}").setValue(float(s))

        self._doc.calculateAll()
        return self._read_results()

    def _read_results(self) -> dict:
        res = self._sheet(RESULTS_SHEET)
        sri = res.getCellRangeByName("F8").getValue()
        sri_class = res.getCellRangeByName("J8").getString()
        impacts = [res.getCellRangeByName(f"F{r}").getValue() for r in range(13, 20)]
        domains = [res.getCellRangeByName(f"F{r}").getValue() for r in range(25, 34)]

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
        bi = self._sheet(BUILDING_SHEET)
        for key, cell in BUILDING_CELLS.items():
            if key in building and building[key] is not None:
                bi.getCellRangeByName(cell).setString(str(building[key]))
        for dom, val in (building.get("domains_present") or {}).items():
            cell = DOMAIN_PRESENT_CELLS.get(dom)
            if cell is None:
                raise KeyError(f"Unknown domain in domains_present: {dom!r}")
            bi.getCellRangeByName(cell).setValue(int(val))

    def _reset_service_levels(self):
        """Zero every service's level and reset share to 100% for a clean slate."""
        calc = self._sheet(CALC_SHEET)
        for row in range(FIRST_SERVICE_ROW, LAST_SERVICE_ROW + 1):
            calc.getCellRangeByName(f"J{row}").setValue(0)
            calc.getCellRangeByName(f"K{row}").setValue(1)

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

        calc = self._sheet(CALC_SHEET)
        for code, (lvl, appl, share) in norm.items():
            row = self._code_to_row[code]
            calc.getCellRangeByName(f"J{row}").setValue(lvl)
            if appl is not None:
                calc.getCellRangeByName(f"I{row}").setValue(int(appl))
            if share is not None:
                calc.getCellRangeByName(f"K{row}").setValue(float(share))

        self._doc.calculateAll()
        return self._read_results()


@contextmanager
def open_calculator(**kwargs):
    with SRILibreCalculator(**kwargs) as c:
        yield c


def assess_from_json(json_path, out_path=None, workbook=DEFAULT_WORKBOOK,
                     reset=True) -> dict:
    """
    Run a real SRI assessment described by a JSON file and return the results
    (optionally writing them to `out_path` as JSON).

    The input JSON has the shape documented in SRILibreCalculator.run_assessment.
    """
    assessment = json.loads(Path(json_path).read_text(encoding="utf-8"))
    with SRILibreCalculator(workbook=workbook) as calc:
        result = calc.run_assessment(assessment, reset=reset)
    if out_path:
        Path(out_path).write_text(json.dumps(result, indent=2, ensure_ascii=False),
                                  encoding="utf-8")
    return result


if __name__ == "__main__":
    # Smoke test: reset every service, assign a random (but valid) functionality
    # level per service across all domains, and read the recalculated result.
    import random

    with SRILibreCalculator() as calc:
        print(f"Workbook services found: {len(calc.service_codes)}")
        print(f"First 8 codes: {calc.service_codes[:8]}")

        random.seed(42)  # fixed seed so the scenario is reproducible run-to-run
        levels = {c: random.randint(0, calc.max_levels[c]) for c in calc.service_codes}

        # run_assessment(reset=True) zeroes every service first, so the result
        # depends only on `levels`, not on whatever the workbook had saved.
        scen = calc.run_assessment({"services": levels})
        print(f"\nRandom scenario SRI : {scen['sri']}%   class={scen['sri_class']!r}")
        print("Impact scores       :")
        for k, v in scen["impacts"].items():
            print(f"   {k:38s} {v}")
        print("Domain scores       :")
        for k, v in scen["domains"].items():
            print(f"   {k:30s} {v}")

        print("\nLevels used (first 15 services):")
        for c in calc.service_codes[:15]:
            print(f"   {c:10s} level={levels[c]:<3d} (max={calc.max_levels[c]})")
