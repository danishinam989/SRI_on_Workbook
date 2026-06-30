# SRI Frontend — Design Spec

**Date:** 2026-06-30
**Status:** Approved (pending written-spec review)
**Scope:** SRI calculator only. Optimizer, greedy search, DEEP integration, and cost
modeling are explicitly deferred (see §11).

## 1. Overview & goals

A local, single-user desktop-style application (browser UI on `localhost`) that lets a user:

1. **Run an SRI assessment** — enter building info + functionality levels per service,
   compute the official SRI via the Excel calculation sheet, and view the score breakdown.
2. **Save & reopen projects** — persist each assessment + its results per project, and
   optionally keep an Excel "proof" copy per project.

The defining principle: **Excel is the single SRI engine.** Scores are computed through the
official `SRI_calculation-sheet_v4.5.xlsx` via xlwings, so all reported numbers are
authoritative and identical to opening the sheet by hand.

## 2. Key decisions & rationale

| Decision    | Choice                                                  | Why |
|-------------|--------------------------------------------------------|-----|
| Deployment  | Local app on the user's Windows PC                     | The Excel engine needs Excel installed and runs over COM. |
| UI stack    | **NiceGUI** (pure Python)                              | App-like UX, no JS build tooling. |
| SRI engine  | **Excel only** (via `Modules/sri_excel_calculator.py`) | Authoritative; avoids the partly-broken domain-weight JSONs. |
| Persistence | JSON files per project + optional Excel proof copy     | Simple, transparent, git-friendly; SQLite is overkill for single-user. |

## 3. Architecture & module layout

```
frontend/
  app.py                 # NiceGUI entry; page routing; creates the SRIEngine singleton
  pages/
    assessment.py        # build / run / save an assessment
    projects.py          # list / open / delete saved projects
  services/
    sri_engine.py        # long-lived Excel instance; thread-safe; assess / export
    store.py             # project folders; load/save assessments & results
    building_options.py  # extract valid dropdown option lists from the workbook
  data/
    projects/<project_id>/  assessment.json  results.json  <name>.xlsx
    building_options.json
```

**Reused, unchanged:** `Modules/sri_excel_calculator.py`,
`Docs/SRI_calculation-sheet_v4.5.xlsx`, `weights/` (for option lists only).

## 4. Concurrency & Excel lifecycle

- The app opens **one** Excel instance at startup via a `SRIEngine` singleton and reuses it
  for the whole session.
- Excel COM is single-threaded → **all engine calls are serialized through a lock** and run
  in a **background worker thread** so the NiceGUI event loop never blocks.
- If Excel crashes or the COM connection dies, the engine **auto-restarts once** and surfaces
  a clear error if it still fails.
- On app shutdown, the engine quits Excel and cleans up its temp working copy.

## 5. Data model & persistence

Each project is a folder `data/projects/<project_id>/`:

- `assessment.json` — the input spec (the schema already used by
  `sri_excel_calculator.run_assessment`): `building`
  (type/usage/location/state/weightings/method/domains_present) + `domains`/`services`
  (per-service levels).
- `results.json` — `{ sri, sri_class, impacts{...}, domains{...}, timestamp, project_id }`.
- `<name>.xlsx` — **optional** Excel proof copy (see §6).

`store.py` API: `list_projects()`, `load(project_id)`, `save(project_id, assessment, results)`,
`delete(project_id)`. Project IDs are validated as safe folder names.

## 6. Excel proof export (audit trail)

- Optional per project. After inputs are written and Excel recalculates, the engine saves a
  **copy** of the populated workbook into the project folder.
- Implementation: `wb.api.SaveCopyAs(path)` (COM) — saves a copy **without** changing the live
  instance's active file, so the reusable Excel session is undisturbed.
- The saved `.xlsx` contains the formulas **and** the last cached results, so reopening it
  shows the full assessment and its scores — usable as proof.
- Filename is **user-supplied** (default `"<project_id>_SRI_v4.5.xlsx"`); the toggle and
  filename field appear on the Assessment page.
- Engine API: `assess(..., export_to: Path | None = None)` and a standalone `export_proof(path)`.

## 7. SRIEngine interface

Wraps `SRIExcelCalculator`; thread-safe singleton.

- `service_codes -> list[str]`
- `max_levels -> dict[code, int]`
- `assess(assessment: dict, export_to=None) -> result` — set building info + levels (reset
  first), recalc, read results, optionally export proof.
- `building_options() -> dict` — valid dropdown values (from `building_options.py`).
- Internal: `_lock`, `_restart()`, background-thread executor.

## 8. Pages (UI)

- **Assessment:** Project ID + building-info dropdowns (validated) + domains-present toggles +
  per-domain service-level inputs (clamped to each service's max) + proof-export
  toggle/filename → **Run** → results panel (total-SRI gauge & class, impact-scores bar,
  domain-scores bar/radar) → **Save**.
- **Projects:** list saved projects; open one (loads its inputs back into the Assessment
  form) or delete it.

## 9. Error handling

- **Excel/COM:** serialize via lock; validate levels ≤ max before writing (raises a clear
  error, not Excel's silent `"error, please check functionality levels"`); auto-restart Excel
  once on COM failure.
- **Invalid building-info strings:** validate against `building_options.json` before running;
  show inline field errors.
- **Bad Project ID / filename:** validate as safe path components; confirm before overwriting
  an existing project.

## 10. Testing

- **Unit (no Excel, CI-friendly):** `store` load/save/list/delete, `building_options`
  extraction, Project-ID/filename validation, assessment-dict normalization.
- **Integration (local, needs Excel):** `SRIEngine.assess` on the example JSON returns
  expected ranges; proof `.xlsx` is written and re-openable.
- Logic modules take dependencies by injection so Excel can be mocked.

## 11. Out of scope (deferred)

- **Upgrade optimizer** (greedy / GA search) — deferred.
- **DEEP integration** and **cost modeling / calibration** — deferred.
- **Side-by-side project comparison** with overlaid charts — deferred (the Projects list is
  enough for now).
- Multi-user / hosting; auth; editing the Excel formulas; mobile layout; PDF export
  (results JSON + Excel proof suffice).

## 12. Risks / open items

- **Excel COM stability** over long sessions — mitigated by serialization + auto-restart.
- **Dropdown value drift** — building-info option lists are extracted from the workbook, so
  they stay in sync if the sheet changes.
