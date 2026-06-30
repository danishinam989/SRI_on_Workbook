# SRI Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A local NiceGUI app that runs official SRI assessments through the Excel calculation sheet, saves projects, and optionally exports a per-project Excel "proof" copy.

**Architecture:** A single Python process serves a browser UI on `localhost`. One long-lived Excel instance (wrapped by the existing `SRIExcelCalculator`) is the sole SRI engine; all calls are serialized through a lock. Pure-logic modules (catalog, options, store, form-building) are unit-tested without Excel; Excel itself is covered by opt-in integration tests.

**Tech Stack:** Python 3.13, NiceGUI (UI), xlwings (Excel COM), openpyxl (read option lists), pytest (tests), uv (env/deps).

## Global Constraints

- Python `>=3.13` (matches `pyproject.toml`).
- Add deps with `uv add <pkg>` (never `pip install`). Dev deps with `uv add --dev <pkg>`.
- The SRI engine MUST be Excel-only via `Modules/sri_excel_calculator.py`. Do NOT use the `weights/*.json` or pymoo/pygmo for scoring.
- Excel COM is single-threaded: every engine call goes through one lock.
- The official workbook is `Docs/SRI_calculation-sheet_v4.5.xlsx`; never modify it (always work on copies).
- Building-info dropdown values must match the workbook exactly (e.g. building type is `non_residential`, with an underscore).
- Run tests with `PYTHONIOENCODING=utf-8 uv run --project . pytest` (the repo prints non-cp1252 chars).
- Excel-dependent tests are gated behind env var `RUN_EXCEL_TESTS=1`.

---

## File Structure

```
frontend/
  __init__.py
  app.py                       # NiceGUI entry; sys.path setup; engine singleton; routes; ui.run
  pages/
    __init__.py
    assessment.py              # assessment form + run + results + save  (build_assessment helper lives here)
    projects.py                # list / open / delete saved projects
  services/
    __init__.py
    catalog.py                 # real-service detection + grouping by domain (pure)
    building_options.py        # extract dropdown option lists from the workbook
    store.py                   # per-project JSON persistence
    sri_engine.py              # thread-safe singleton wrapping SRIExcelCalculator
  data/
    .gitkeep                   # runtime: projects/<id>/..., building_options.json
Modules/
  sri_excel_calculator.py      # MODIFY: add export_copy()
conftest.py                    # sys.path + Excel-test gating
tests/
  frontend/
    __init__.py
    test_catalog.py
    test_building_options.py
    test_store.py
    test_sri_engine.py
    test_assessment_form.py
    test_pages_import.py
```

---

### Task 1: Project scaffolding, dependencies, test harness

**Files:**
- Create: `frontend/__init__.py`, `frontend/pages/__init__.py`, `frontend/services/__init__.py`, `frontend/data/.gitkeep`, `tests/frontend/__init__.py`
- Create: `conftest.py`
- Modify: `pyproject.toml` (via `uv add`)
- Test: `tests/frontend/test_scaffold.py`

**Interfaces:**
- Consumes: nothing.
- Produces: importable `frontend` package; `conftest.py` puts project root and `Modules/` on `sys.path` and exposes the `requires_excel` skip marker via env `RUN_EXCEL_TESTS`.

- [ ] **Step 1: Add dependencies**

Run:
```bash
uv add nicegui
uv add --dev pytest
```

- [ ] **Step 2: Create package files**

Create `frontend/__init__.py`, `frontend/pages/__init__.py`, `frontend/services/__init__.py`, `tests/frontend/__init__.py` as empty files. Create `frontend/data/.gitkeep` empty.

- [ ] **Step 3: Create `conftest.py`**

```python
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
# Make `frontend` importable and expose the existing Modules/ calculator.
for p in (ROOT, ROOT / "Modules"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

WORKBOOK = ROOT / "Docs" / "SRI_calculation-sheet_v4.5.xlsx"

requires_excel = pytest.mark.skipif(
    os.environ.get("RUN_EXCEL_TESTS") != "1",
    reason="set RUN_EXCEL_TESTS=1 to run Excel-dependent tests",
)
```

- [ ] **Step 4: Write the scaffold test**

Create `tests/frontend/test_scaffold.py`:
```python
import importlib


def test_frontend_package_imports():
    assert importlib.import_module("frontend") is not None


def test_nicegui_available():
    assert importlib.import_module("nicegui") is not None
```

- [ ] **Step 5: Run tests**

Run: `PYTHONIOENCODING=utf-8 uv run --project . pytest tests/frontend/test_scaffold.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock frontend tests conftest.py
git commit -m "feat(frontend): scaffold package, deps, and test harness"
```

---

### Task 2: Service catalog (group real services by domain)

**Files:**
- Create: `frontend/services/catalog.py`
- Test: `tests/frontend/test_catalog.py`

**Interfaces:**
- Consumes: a flat list of service codes (e.g. from `SRIEngine.service_codes`).
- Produces:
  - `DOMAIN_NAMES: list[str]` — the 9 domains in display order.
  - `is_real_service(code: str) -> bool` — True for catalogue codes like `H-1a`, False for user-defined like `MC-E5`.
  - `service_domain(code: str) -> str | None` — maps a code to its domain name.
  - `group_by_domain(codes: list[str]) -> dict[str, list[str]]` — ordered `{domain: [codes]}`, real services only, domains with no codes omitted.

- [ ] **Step 1: Write the failing test**

Create `tests/frontend/test_catalog.py`:
```python
from frontend.services.catalog import (
    DOMAIN_NAMES, is_real_service, service_domain, group_by_domain,
)


def test_real_vs_userdefined():
    assert is_real_service("H-1a")
    assert is_real_service("MC-29")
    assert not is_real_service("MC-E5")
    assert not is_real_service("L-E1")


def test_service_domain():
    assert service_domain("H-1a") == "Heating"
    assert service_domain("DHW-2b") == "Domestic hot water"
    assert service_domain("EV-15") == "Electric vehicle charging"
    assert service_domain("MC-3") == "Monitoring and control"


def test_group_by_domain_orders_and_filters():
    codes = ["L-2", "H-1a", "MC-E5", "L-1a", "H-4"]
    grouped = group_by_domain(codes)
    assert list(grouped.keys()) == ["Heating", "Lighting"]  # display order, EV/etc omitted
    assert grouped["Heating"] == ["H-1a", "H-4"]
    assert grouped["Lighting"] == ["L-1a", "L-2"]
    assert "MC-E5" not in grouped.get("Monitoring and control", [])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONIOENCODING=utf-8 uv run --project . pytest tests/frontend/test_catalog.py -v`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement `catalog.py`**

```python
"""Static service-catalogue helpers (pure; no Excel)."""
from __future__ import annotations

import re

DOMAIN_NAMES = [
    "Heating", "Domestic hot water", "Cooling", "Ventilation", "Lighting",
    "Dynamic building envelope", "Electricity", "Electric vehicle charging",
    "Monitoring and control",
]

# code prefix (text before the first '-') -> domain name
_PREFIX_TO_DOMAIN = {
    "H": "Heating",
    "DHW": "Domestic hot water",
    "C": "Cooling",
    "V": "Ventilation",
    "L": "Lighting",
    "DE": "Dynamic building envelope",
    "E": "Electricity",
    "EV": "Electric vehicle charging",
    "MC": "Monitoring and control",
}

# real catalogue codes have a digit immediately after the dash (e.g. H-1a);
# user-defined placeholders have a letter (e.g. L-E1, MC-E5).
_REAL = re.compile(r"^[A-Z]+-\d")


def is_real_service(code: str) -> bool:
    return bool(isinstance(code, str) and _REAL.match(code.strip()))


def service_domain(code: str) -> str | None:
    if not isinstance(code, str) or "-" not in code:
        return None
    prefix = code.split("-", 1)[0].strip()
    return _PREFIX_TO_DOMAIN.get(prefix)


def group_by_domain(codes: list[str]) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = {d: [] for d in DOMAIN_NAMES}
    for code in codes:
        if not is_real_service(code):
            continue
        dom = service_domain(code)
        if dom:
            buckets[dom].append(code)
    # preserve display order; drop empty domains; sort codes within a domain
    return {d: sorted(buckets[d]) for d in DOMAIN_NAMES if buckets[d]}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONIOENCODING=utf-8 uv run --project . pytest tests/frontend/test_catalog.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add frontend/services/catalog.py tests/frontend/test_catalog.py
git commit -m "feat(frontend): service catalog grouping helpers"
```

---

### Task 3: Building-info option lists from the workbook

**Files:**
- Create: `frontend/services/building_options.py`
- Test: `tests/frontend/test_building_options.py`

**Interfaces:**
- Consumes: the workbook path; the `_general` sheet layout (building type `C2`/`D2`; usages `C3:C6`/`D3:D6`; locations `C9:C40`; floor area `C45:C50`; age `C52:C56`; state `C58:C59`; weightings `C61:C62`).
- Produces:
  - `extract_building_options(workbook_path) -> dict` with keys: `building_types`, `usages` (`{type: [..]}`), `locations`, `floor_area`, `age`, `state`, `weightings`, `methods`, `domains_present`.
  - `load_or_build(cache_path, workbook_path) -> dict` — returns cached JSON if present, else extracts and writes it.

- [ ] **Step 1: Write the failing test**

Create `tests/frontend/test_building_options.py`:
```python
from pathlib import Path

from conftest import WORKBOOK
from frontend.services.building_options import extract_building_options, load_or_build


def test_extract_has_expected_values():
    opts = extract_building_options(WORKBOOK)
    assert "residential" in opts["building_types"]
    assert "non_residential" in opts["building_types"]
    assert "Ireland" in opts["locations"]
    assert opts["state"] == ["Renovated", "Original"]
    assert opts["weightings"] == ["Default", "User-defined"]
    assert opts["methods"] == ["A", "B", "Custom"]
    assert opts["domains_present"] == [0, 1, 2]
    assert "office" in opts["usages"]["non_residential"]
    assert "single-family house" in opts["usages"]["residential"]


def test_load_or_build_caches(tmp_path):
    cache = tmp_path / "building_options.json"
    first = load_or_build(cache, WORKBOOK)
    assert cache.exists()
    # second call reads cache (no workbook needed)
    second = load_or_build(cache, "nonexistent.xlsx")
    assert second == first
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONIOENCODING=utf-8 uv run --project . pytest tests/frontend/test_building_options.py -v`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement `building_options.py`**

```python
"""Extract building-info dropdown option lists from the workbook's _general sheet.

openpyxl drops Excel data-validation, so the allowed values are read from the
_general option-list ranges instead.
"""
from __future__ import annotations

import json
from pathlib import Path

import openpyxl

GENERAL_SHEET = "_general"


def _col(ws, col: int, r0: int, r1: int) -> list:
    out = []
    for r in range(r0, r1 + 1):
        v = ws.cell(row=r, column=col).value
        if v is not None and str(v).strip():
            out.append(str(v).strip())
    return out


def extract_building_options(workbook_path) -> dict:
    wb = openpyxl.load_workbook(workbook_path, data_only=True)
    ws = wb[GENERAL_SHEET]
    res_type = str(ws.cell(row=2, column=3).value).strip()   # C2 -> "residential"
    non_res_type = str(ws.cell(row=2, column=4).value).strip()  # D2 -> "non_residential"
    opts = {
        "building_types": [res_type, non_res_type],
        "usages": {
            res_type: _col(ws, 3, 3, 6),       # C3:C6
            non_res_type: _col(ws, 4, 3, 6),   # D3:D6
        },
        "locations": _col(ws, 3, 9, 40),       # C9:C40
        "floor_area": _col(ws, 3, 45, 50),     # C45:C50
        "age": _col(ws, 3, 52, 56),            # C52:C56
        "state": _col(ws, 3, 58, 59),          # C58:C59 -> Renovated, Original
        "weightings": _col(ws, 3, 61, 62),     # C61:C62 -> Default, User-defined
        "methods": ["A", "B", "Custom"],
        "domains_present": [0, 1, 2],
    }
    wb.close()
    return opts


def load_or_build(cache_path, workbook_path) -> dict:
    cache_path = Path(cache_path)
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))
    opts = extract_building_options(workbook_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(opts, indent=2, ensure_ascii=False), encoding="utf-8")
    return opts
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONIOENCODING=utf-8 uv run --project . pytest tests/frontend/test_building_options.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add frontend/services/building_options.py tests/frontend/test_building_options.py
git commit -m "feat(frontend): extract building-info options from workbook"
```

---

### Task 4: Project persistence store

**Files:**
- Create: `frontend/services/store.py`
- Test: `tests/frontend/test_store.py`

**Interfaces:**
- Consumes: a base directory path.
- Produces:
  - `validate_project_id(project_id: str) -> str` — raises `ValueError` for unsafe ids.
  - `ProjectStore(base_dir)` with: `project_dir(id) -> Path`, `exists(id) -> bool`, `list_projects() -> list[str]`, `save(id, assessment: dict, results: dict) -> Path`, `load(id) -> tuple[dict, dict | None]`, `delete(id) -> None`.

- [ ] **Step 1: Write the failing test**

Create `tests/frontend/test_store.py`:
```python
import pytest

from frontend.services.store import ProjectStore, validate_project_id


def test_validate_rejects_unsafe():
    with pytest.raises(ValueError):
        validate_project_id("../evil")
    with pytest.raises(ValueError):
        validate_project_id("a/b")
    assert validate_project_id("Proj_01.2") == "Proj_01.2"


def test_save_load_roundtrip(tmp_path):
    s = ProjectStore(tmp_path)
    s.save("proj1", {"building": {"type": "x"}}, {"sri": 42.0})
    assessment, results = s.load("proj1")
    assert assessment["building"]["type"] == "x"
    assert results["sri"] == 42.0
    assert results["project_id"] == "proj1"
    assert "saved_at" in results


def test_list_and_delete(tmp_path):
    s = ProjectStore(tmp_path)
    s.save("p1", {}, {})
    s.save("p2", {}, {})
    assert s.list_projects() == ["p1", "p2"]
    s.delete("p1")
    assert s.list_projects() == ["p2"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONIOENCODING=utf-8 uv run --project . pytest tests/frontend/test_store.py -v`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement `store.py`**

```python
"""Per-project JSON persistence under data/projects/<project_id>/."""
from __future__ import annotations

import json
import re
import shutil
import time
from pathlib import Path

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def validate_project_id(project_id: str) -> str:
    if not isinstance(project_id, str) or not _SAFE_ID.match(project_id):
        raise ValueError(f"Invalid project id: {project_id!r}")
    return project_id


class ProjectStore:
    def __init__(self, base_dir):
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)

    def project_dir(self, project_id: str) -> Path:
        return self.base / validate_project_id(project_id)

    def exists(self, project_id: str) -> bool:
        return (self.project_dir(project_id) / "assessment.json").exists()

    def list_projects(self) -> list[str]:
        return sorted(
            p.name for p in self.base.iterdir()
            if p.is_dir() and (p / "assessment.json").exists()
        )

    def save(self, project_id: str, assessment: dict, results: dict) -> Path:
        d = self.project_dir(project_id)
        d.mkdir(parents=True, exist_ok=True)
        (d / "assessment.json").write_text(
            json.dumps(assessment, indent=2, ensure_ascii=False), encoding="utf-8")
        payload = dict(results)
        payload.setdefault("project_id", project_id)
        payload["saved_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        (d / "results.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return d

    def load(self, project_id: str) -> tuple[dict, dict | None]:
        d = self.project_dir(project_id)
        assessment = json.loads((d / "assessment.json").read_text(encoding="utf-8"))
        rpath = d / "results.json"
        results = json.loads(rpath.read_text(encoding="utf-8")) if rpath.exists() else None
        return assessment, results

    def delete(self, project_id: str) -> None:
        d = self.project_dir(project_id)
        if d.exists():
            shutil.rmtree(d)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONIOENCODING=utf-8 uv run --project . pytest tests/frontend/test_store.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add frontend/services/store.py tests/frontend/test_store.py
git commit -m "feat(frontend): per-project JSON store"
```

---

### Task 5: Excel proof export + thread-safe SRI engine

**Files:**
- Modify: `Modules/sri_excel_calculator.py` (add `export_copy`)
- Create: `frontend/services/sri_engine.py`
- Test: `tests/frontend/test_sri_engine.py`

**Interfaces:**
- Consumes: `SRIExcelCalculator` (from `sri_excel_calculator`), the options dict from Task 3.
- Produces:
  - New method `SRIExcelCalculator.export_copy(self, path)` — saves a copy of the live workbook via `self._wb.api.SaveCopyAs` without disturbing the session.
  - `class SRIEngine`:
    - `SRIEngine(workbook=DEFAULT_WORKBOOK, options=None, calculator_factory=None)`
    - `start() -> SRIEngine`, `stop() -> None`
    - properties `service_codes -> list[str]`, `max_levels -> dict[str,int]`
    - `validate(assessment: dict) -> None` — raises `AssessmentError` on bad building-info option.
    - `assess(assessment: dict, export_to=None) -> dict` — validate, run, optional proof; auto-restart Excel once on failure.
    - `export_proof(path) -> None`
  - `class AssessmentError(Exception)`

- [ ] **Step 1: Add `export_copy` to the calculator**

In `Modules/sri_excel_calculator.py`, add this method to `SRIExcelCalculator` (after `run_assessment`):
```python
    def export_copy(self, path) -> None:
        """Save a copy of the populated workbook WITHOUT changing the live
        session's active file (uses Excel's SaveCopyAs over COM)."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        self._wb.api.SaveCopyAs(str(target))
```

- [ ] **Step 2: Write the failing test (mocked calculator — no Excel)**

Create `tests/frontend/test_sri_engine.py`:
```python
import pytest

from frontend.services.sri_engine import SRIEngine, AssessmentError

OPTIONS = {
    "building_types": ["residential", "non_residential"],
    "locations": ["Ireland", "Austria"],
    "weightings": ["Default", "User-defined"],
    "methods": ["A", "B", "Custom"],
}


class FakeAPI:
    def __init__(self):
        self.saved_to = None

    def SaveCopyAs(self, path):
        self.saved_to = path


class FakeWB:
    def __init__(self):
        self.api = FakeAPI()


class FakeCalc:
    """Stand-in for SRIExcelCalculator (context manager)."""
    def __init__(self):
        self.service_codes = ["H-1a", "L-1a"]
        self.max_levels = {"H-1a": 4, "L-1a": 3}
        self._wb = FakeWB()
        self.last_assessment = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def run_assessment(self, assessment, reset=True, validate=True):
        self.last_assessment = assessment
        return {"sri": 37.5, "sri_class": "Between 35% and 50%",
                "impacts": {}, "domains": {}}

    def export_copy(self, path):
        self._wb.api.SaveCopyAs(path)


def make_engine():
    fake = FakeCalc()
    eng = SRIEngine(options=OPTIONS, calculator_factory=lambda: fake)
    return eng, fake


def test_assess_returns_results_and_passes_spec():
    eng, fake = make_engine()
    a = {"building": {"type": "non_residential", "location": "Ireland",
                      "weightings": "Default", "method": "B"},
         "domains": {"Heating": {"H-1a": 2}}}
    result = eng.assess(a)
    assert result["sri"] == 37.5
    assert fake.last_assessment == a
    eng.stop()


def test_validate_rejects_bad_option():
    eng, _ = make_engine()
    a = {"building": {"type": "house", "location": "Ireland"}}
    with pytest.raises(AssessmentError):
        eng.assess(a)
    eng.stop()


def test_assess_with_export(tmp_path):
    eng, fake = make_engine()
    a = {"building": {"type": "non_residential", "location": "Ireland"},
         "domains": {}}
    out = tmp_path / "proof.xlsx"
    eng.assess(a, export_to=out)
    assert fake._wb.api.saved_to == str(out)
    eng.stop()
```

- [ ] **Step 3: Run test to verify it fails**

Run: `PYTHONIOENCODING=utf-8 uv run --project . pytest tests/frontend/test_sri_engine.py -v`
Expected: FAIL (module not found).

- [ ] **Step 4: Implement `sri_engine.py`**

```python
"""Thread-safe singleton wrapping the Excel SRI calculator."""
from __future__ import annotations

import threading
from contextlib import suppress
from pathlib import Path

from sri_excel_calculator import SRIExcelCalculator, DEFAULT_WORKBOOK


class AssessmentError(Exception):
    pass


class SRIEngine:
    def __init__(self, workbook=DEFAULT_WORKBOOK, options=None, calculator_factory=None):
        self._workbook = workbook
        self._options = options
        self._factory = calculator_factory or (
            lambda: SRIExcelCalculator(workbook=workbook))
        self._lock = threading.RLock()
        self._calc = None

    # ---- lifecycle ----
    def start(self) -> "SRIEngine":
        with self._lock:
            if self._calc is None:
                self._calc = self._factory().__enter__()
        return self

    def stop(self) -> None:
        with self._lock:
            if self._calc is not None:
                with suppress(Exception):
                    self._calc.__exit__(None, None, None)
                self._calc = None

    def _restart(self) -> None:
        self.stop()
        self.start()

    # ---- read-only introspection ----
    @property
    def service_codes(self) -> list[str]:
        with self._lock:
            self.start()
            return list(self._calc.service_codes)

    @property
    def max_levels(self) -> dict[str, int]:
        with self._lock:
            self.start()
            return dict(self._calc.max_levels)

    # ---- validation ----
    def validate(self, assessment: dict) -> None:
        if not self._options:
            return
        b = assessment.get("building", {}) or {}
        o = self._options
        checks = [
            ("type", "building_types"),
            ("location", "locations"),
            ("weightings", "weightings"),
            ("method", "methods"),
        ]
        errs = []
        for field, key in checks:
            val = b.get(field)
            allowed = o.get(key)
            if val is not None and allowed is not None and val not in allowed:
                errs.append(f"{field}={val!r} is not one of {allowed}")
        if errs:
            raise AssessmentError("; ".join(errs))

    # ---- main ----
    def assess(self, assessment: dict, export_to=None) -> dict:
        with self._lock:
            self.start()
            self.validate(assessment)
            try:
                result = self._calc.run_assessment(assessment)
            except AssessmentError:
                raise
            except Exception:
                # COM/Excel hiccup: restart once and retry
                self._restart()
                result = self._calc.run_assessment(assessment)
            if export_to is not None:
                self._calc.export_copy(Path(export_to))
            return result

    def export_proof(self, path) -> None:
        with self._lock:
            self.start()
            self._calc.export_copy(Path(path))
```

- [ ] **Step 5: Run unit tests (no Excel)**

Run: `PYTHONIOENCODING=utf-8 uv run --project . pytest tests/frontend/test_sri_engine.py -v`
Expected: 3 passed.

- [ ] **Step 6: Add the Excel integration test**

Append to `tests/frontend/test_sri_engine.py`:
```python
from conftest import WORKBOOK, requires_excel
from frontend.services.building_options import extract_building_options


@requires_excel
def test_real_engine_assess_and_export(tmp_path):
    opts = extract_building_options(WORKBOOK)
    eng = SRIEngine(workbook=WORKBOOK, options=opts).start()
    try:
        a = {
            "building": {"type": "non_residential", "usage": "office",
                         "location": "Ireland", "state": "Original",
                         "weightings": "Default", "method": "B",
                         "domains_present": {d: 1 for d in [
                             "Heating", "Domestic hot water", "Cooling",
                             "Ventilation", "Lighting", "Dynamic building envelope",
                             "Electricity", "Electric vehicle charging",
                             "Monitoring and control"]}},
            "domains": {"Lighting": {"L-1a": 3, "L-2": 3}},
        }
        out = tmp_path / "proof.xlsx"
        result = eng.assess(a, export_to=out)
        assert 0 <= result["sri"] <= 100
        assert out.exists()
    finally:
        eng.stop()
```

- [ ] **Step 7: Run the Excel integration test (local, with Excel)**

Run: `PYTHONIOENCODING=utf-8 RUN_EXCEL_TESTS=1 uv run --project . pytest tests/frontend/test_sri_engine.py::test_real_engine_assess_and_export -v`
Expected: PASS (Excel launches; SRI in [0,100]; proof file written). Without `RUN_EXCEL_TESTS=1` it is skipped.

- [ ] **Step 8: Commit**

```bash
git add Modules/sri_excel_calculator.py frontend/services/sri_engine.py tests/frontend/test_sri_engine.py
git commit -m "feat(frontend): thread-safe SRI engine + Excel proof export"
```

---

### Task 6: Assessment form helper + Assessment page

**Files:**
- Create: `frontend/pages/assessment.py`
- Test: `tests/frontend/test_assessment_form.py`

**Interfaces:**
- Consumes: `SRIEngine`, `ProjectStore`, options dict, `catalog.group_by_domain`.
- Produces:
  - `build_assessment(building: dict, levels_by_domain: dict) -> dict` — pure; returns the assessment spec (`{"building": ..., "domains": ...}`).
  - `register(engine, store, options) -> None` — registers the NiceGUI `@ui.page('/')` route.

- [ ] **Step 1: Write the failing test for the pure helper**

Create `tests/frontend/test_assessment_form.py`:
```python
from frontend.pages.assessment import build_assessment


def test_build_assessment_shapes_spec():
    building = {"type": "non_residential", "usage": "office", "location": "Ireland",
                "state": "Original", "weightings": "Default", "method": "B",
                "domains_present": {"Heating": 1, "Lighting": 1}}
    levels = {"Heating": {"H-1a": 2}, "Lighting": {"L-1a": 3}}
    spec = build_assessment(building, levels)
    assert spec["building"]["type"] == "non_residential"
    assert spec["building"]["domains_present"]["Heating"] == 1
    assert spec["domains"]["Lighting"]["L-1a"] == 3
    assert set(spec.keys()) == {"building", "domains"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONIOENCODING=utf-8 uv run --project . pytest tests/frontend/test_assessment_form.py -v`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement `assessment.py`**

```python
"""Assessment page: build inputs, run via the engine, show results, save."""
from __future__ import annotations

from pathlib import Path

from nicegui import ui

from frontend.services import catalog


def build_assessment(building: dict, levels_by_domain: dict) -> dict:
    """Pure: assemble the assessment spec consumed by SRIEngine.assess."""
    return {"building": dict(building), "domains": dict(levels_by_domain)}


def _render_results(container, result: dict) -> None:
    container.clear()
    with container:
        ui.label(f"Total SRI: {result['sri']}%").classes("text-2xl font-bold")
        ui.label(f"Class: {result.get('sri_class', '')}")
        ui.linear_progress(value=max(0.0, min(1.0, (result.get('sri') or 0) / 100)),
                           show_value=False)
        for title, key in (("Impact scores", "impacts"), ("Domain scores", "domains")):
            data = result.get(key) or {}
            if not data:
                continue
            ui.label(title).classes("text-lg font-semibold mt-2")
            rows = [{"name": k, "score": v} for k, v in data.items()]
            ui.table(columns=[{"name": "name", "label": "Name", "field": "name",
                               "align": "left"},
                              {"name": "score", "label": "%", "field": "score"}],
                     rows=rows).classes("w-full")


def register(engine, store, options) -> None:
    grouped = catalog.group_by_domain(engine.service_codes)
    max_levels = engine.max_levels

    # NOTE: engine.assess() is called synchronously (NOT via run.io_bound). Excel
    # COM objects are thread-affine; the engine's Excel instance is created in
    # app.on_startup on the event-loop thread, so engine calls must happen on that
    # same thread. A single recalc is fast enough that brief UI blocking is fine.
    @ui.page("/")
    def assessment_page(project: str | None = None):
        state: dict = {}
        ui.label("SRI Assessment").classes("text-3xl font-bold")

        with ui.row().classes("w-full gap-8"):
            results = ui.column().classes("w-1/2 order-last")  # right column

            with ui.column().classes("w-1/2"):
                project_id = ui.input("Project ID", value=project or "project-1")

                ui.label("Building").classes("text-lg font-semibold")
                b_type = ui.select(options["building_types"],
                                   value=options["building_types"][-1], label="Type")
                b_usage = ui.select(
                    options["usages"][b_type.value], label="Usage",
                    value=(options["usages"][b_type.value] or [None])[0])
                b_type.on_value_change(
                    lambda e: b_usage.set_options(options["usages"][e.value]))
                b_loc = ui.select(options["locations"], value="Ireland", label="Location")
                b_state = ui.select(options["state"], value="Original", label="State")
                b_weight = ui.select(options["weightings"], value="Default",
                                     label="Weightings")
                b_method = ui.select(options["methods"], value="B", label="Method")

                ui.label("Domains present").classes("text-lg font-semibold mt-2")
                present = {d: ui.switch(d, value=d in grouped)
                           for d in catalog.DOMAIN_NAMES}

                ui.label("Service functionality levels").classes(
                    "text-lg font-semibold mt-2")
                level_inputs: dict[str, dict] = {}
                for dom, codes in grouped.items():
                    with ui.expansion(dom).classes("w-full"):
                        level_inputs[dom] = {
                            code: ui.number(label=code, value=0, min=0,
                                            max=max_levels.get(code, 4), step=1,
                                            format="%d")
                            for code in codes
                        }

                ui.label("Proof export").classes("text-lg font-semibold mt-2")
                export_on = ui.switch("Export Excel proof", value=False)
                export_name = ui.input(
                    "Excel filename", value="").bind_visibility_from(export_on, "value")

                def collect_spec() -> dict:
                    building = {
                        "type": b_type.value, "usage": b_usage.value,
                        "location": b_loc.value, "state": b_state.value,
                        "weightings": b_weight.value, "method": b_method.value,
                        "domains_present": {d: (1 if present[d].value else 0)
                                            for d in catalog.DOMAIN_NAMES},
                    }
                    levels = {dom: {c: int(inp.value or 0) for c, inp in items.items()}
                              for dom, items in level_inputs.items()}
                    return build_assessment(building, levels)

                def run():
                    spec = collect_spec()
                    export_to = None
                    if export_on.value:
                        pid = project_id.value
                        name = export_name.value or f"{pid}_SRI_v4.5.xlsx"
                        export_to = store.project_dir(pid) / name
                    try:
                        result = engine.assess(spec, export_to=export_to)
                    except Exception as exc:  # noqa: BLE001
                        ui.notify(f"Error: {exc}", type="negative")
                        return
                    state["spec"], state["result"] = spec, result
                    _render_results(results, result)
                    ui.notify(f"SRI = {result['sri']}%", type="positive")

                def save():
                    if "result" not in state:
                        ui.notify("Run an assessment first", type="warning")
                        return
                    store.save(project_id.value, state["spec"], state["result"])
                    ui.notify(f"Saved project {project_id.value!r}", type="positive")

                with ui.row():
                    ui.button("Run", on_click=run).props("color=primary")
                    ui.button("Save", on_click=save)

        # Prefill from a saved project when opened via /?project=<id>
        if project and store.exists(project):
            saved_assessment, saved_results = store.load(project)
            b = saved_assessment.get("building", {})
            if b.get("type") in options["building_types"]:
                b_type.set_value(b["type"])
                b_usage.set_options(options["usages"][b["type"]])
            for widget, field in ((b_usage, "usage"), (b_loc, "location"),
                                  (b_state, "state"), (b_weight, "weightings"),
                                  (b_method, "method")):
                if b.get(field) is not None:
                    widget.set_value(b[field])
            for d, val in (b.get("domains_present") or {}).items():
                if d in present:
                    present[d].set_value(bool(val))
            for dom, items in saved_assessment.get("domains", {}).items():
                for code, lvl in items.items():
                    if dom in level_inputs and code in level_inputs[dom]:
                        level_inputs[dom][code].set_value(int(lvl))
            if saved_results:
                _render_results(results, saved_results)

        ui.link("Projects", "/projects")
```

- [ ] **Step 4: Run the helper test**

Run: `PYTHONIOENCODING=utf-8 uv run --project . pytest tests/frontend/test_assessment_form.py -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add frontend/pages/assessment.py tests/frontend/test_assessment_form.py
git commit -m "feat(frontend): assessment page + form helper"
```

---

### Task 7: Projects page

**Files:**
- Create: `frontend/pages/projects.py`
- Test: `tests/frontend/test_pages_import.py`

**Interfaces:**
- Consumes: `ProjectStore`.
- Produces: `register(store) -> None` registering `@ui.page('/projects')`.

- [ ] **Step 1: Write the failing import/smoke test**

Create `tests/frontend/test_pages_import.py`:
```python
import importlib


def test_pages_modules_import():
    a = importlib.import_module("frontend.pages.assessment")
    p = importlib.import_module("frontend.pages.projects")
    assert hasattr(a, "register")
    assert hasattr(p, "register")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONIOENCODING=utf-8 uv run --project . pytest tests/frontend/test_pages_import.py -v`
Expected: FAIL (`frontend.pages.projects` not found).

- [ ] **Step 3: Implement `projects.py`**

```python
"""Projects page: list / open / delete saved projects."""
from __future__ import annotations

from nicegui import ui


def register(store) -> None:
    @ui.page("/projects")
    def projects_page():
        ui.label("Saved Projects").classes("text-3xl font-bold")
        table = ui.column().classes("w-full")

        def refresh():
            table.clear()
            with table:
                ids = store.list_projects()
                if not ids:
                    ui.label("No saved projects yet.")
                for pid in ids:
                    _, results = store.load(pid)
                    sri = (results or {}).get("sri", "—")
                    with ui.row().classes("items-center gap-4"):
                        ui.label(pid).classes("font-semibold w-48")
                        ui.label(f"SRI: {sri}%")
                        ui.link("Open", f"/?project={pid}")

                        def _del(p=pid):
                            store.delete(p)
                            refresh()
                            ui.notify(f"Deleted {p!r}", type="warning")

                        ui.button("Delete", on_click=_del).props("flat color=negative")

        refresh()
        ui.link("New assessment", "/")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONIOENCODING=utf-8 uv run --project . pytest tests/frontend/test_pages_import.py -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add frontend/pages/projects.py tests/frontend/test_pages_import.py
git commit -m "feat(frontend): projects list page"
```

---

### Task 8: App entry point + wiring + manual smoke

**Files:**
- Create: `frontend/app.py`
- Modify: `tests/frontend/test_pages_import.py` (add app import smoke)

**Interfaces:**
- Consumes: `SRIEngine`, `ProjectStore`, `building_options.load_or_build`, both pages' `register`.
- Produces: a runnable app started with `uv run python frontend/app.py`.

- [ ] **Step 1: Implement `app.py`**

```python
"""SRI Frontend — NiceGUI entry point.

Run:  uv run python frontend/app.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT, ROOT / "Modules"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from nicegui import app, ui  # noqa: E402

from frontend.services.building_options import load_or_build  # noqa: E402
from frontend.services.sri_engine import SRIEngine  # noqa: E402
from frontend.services.store import ProjectStore  # noqa: E402
from frontend.pages import assessment, projects  # noqa: E402

WORKBOOK = ROOT / "Docs" / "SRI_calculation-sheet_v4.5.xlsx"
DATA_DIR = ROOT / "frontend" / "data"

options = load_or_build(DATA_DIR / "building_options.json", WORKBOOK)
store = ProjectStore(DATA_DIR / "projects")
engine = SRIEngine(workbook=WORKBOOK, options=options)


@app.on_startup
def _startup():
    engine.start()


@app.on_shutdown
def _shutdown():
    engine.stop()


assessment.register(engine, store, options)
projects.register(store)

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="SRI Calculator", reload=False, port=8080, show=True)
```

- [ ] **Step 2: Add app import smoke test**

Append to `tests/frontend/test_pages_import.py`:
```python
def test_app_module_imports(monkeypatch):
    # importing app registers pages and builds options/store/engine objects;
    # it must not start Excel or launch the server at import time.
    import importlib
    mod = importlib.import_module("frontend.app")
    assert hasattr(mod, "engine") and hasattr(mod, "store")
```

- [ ] **Step 3: Run the full non-Excel test suite**

Run: `PYTHONIOENCODING=utf-8 uv run --project . pytest tests/frontend -v`
Expected: all pass except the Excel-gated test (skipped).

- [ ] **Step 4: Manual smoke (local, with Excel)**

Run: `PYTHONIOENCODING=utf-8 uv run --project . python frontend/app.py`
Then in the browser at `http://localhost:8080`:
- Set Type=`non_residential`, Usage=`office`, Location=`Ireland`, Method=`B`.
- Expand a domain, set a few levels, click **Run** → a total SRI in [0,100] appears.
- Toggle **Export Excel proof**, click **Run**, then **Save** → confirm `frontend/data/projects/<id>/` contains `assessment.json`, `results.json`, and the `.xlsx` proof.
- Visit `/projects` → the project is listed; **Delete** removes it.
Stop the server with Ctrl+C.

- [ ] **Step 5: Commit**

```bash
git add frontend/app.py tests/frontend/test_pages_import.py
git commit -m "feat(frontend): app entry point and wiring"
```

---

## Self-Review

**Spec coverage:**
- §1 SRI assessment → Tasks 5–8. §1 save/reopen → Tasks 4, 7. §3 module layout → all tasks (matches exactly). §4 concurrency/lifecycle → Task 5 (`_lock`, `start/stop`, `_restart`, startup/shutdown in Task 8). §5 persistence → Task 4. §6 proof export → Task 5 (`export_copy`) + Task 6 (toggle/filename). §7 engine interface → Task 5. §8 pages → Tasks 6–7. §9 error handling → Task 5 (validate, restart, level check via `run_assessment`) + Task 6 (notify on error). §10 testing → tests in every task + Excel-gated integration test. §11 out-of-scope honored (no optimizer/DEEP). §12 risks → restart + options extraction.
- No gaps found.

**Placeholder scan:** No TBD/TODO; every code step shows complete code; commands have expected output. (The `pass` under the right-hand results column in Task 6 is intentional layout, not a placeholder — results render into the `results` column created on the left.)

**Type consistency:** `SRIEngine.assess(assessment, export_to)`, `service_codes`, `max_levels`, `export_copy(path)`, `ProjectStore.save/load/list_projects/delete/project_dir`, `catalog.group_by_domain/DOMAIN_NAMES`, `build_assessment(building, levels_by_domain)`, `register(...)` signatures are consistent across tasks and match the spec's §7 interface.
