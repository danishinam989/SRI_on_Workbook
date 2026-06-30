# Project: SRI with DEEP

Tooling around the EU **Smart Readiness Indicator (SRI)** plus integration with the
**DEEP** (De-risking Energy Efficiency Platform) database.

## Key references
- **[Docs/SRI_REFERENCE.md](Docs/SRI_REFERENCE.md)** — read this before working on SRI
  scoring, domains, impact criteria, functionality levels, weighting factors, or the
  optimisers in `SRI/`. Distilled from the official SRI calculation framework v4.5.

## Layout
- `SRI/` — multi-objective optimisers (NSGA-II via pygmo and pymoo) that recommend TBS
  functionality-level upgrades to improve the SRI under a budget constraint.
- `main.py` — client for the DEEP API (savings / payback / avoidance / KPI endpoints).
- `Docs/` — source PDFs and reference notes.

## Notes
- Cost and CO₂ models in the optimisers are **placeholders**, not part of the official SRI
  methodology. DEEP is being evaluated as a *calibration* source, not a per-service price
  lookup (granularity mismatch — see prior analysis).
- The DEEP API key lives in `.env` (git-ignored).
