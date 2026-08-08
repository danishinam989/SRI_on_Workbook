# ISO 52120-1:2021 — BAC Efficiency Factors (extract)

> ⚠️ **Copyright / licensing.** These values are extracted from a copy of ISO 52120-1:2021
> licensed to *Danish Inam (Dublin City University)*. The PDF states: *"No further
> reproduction or distribution permitted."* This file is an internal working extract for
> our own engineering use. **Do not publish it or push it to a public repository** — that
> would be redistribution. Consider git-ignoring this file if this repo may ever go public.
>
> Source: ISO 52120-1:2021(E) — *Energy performance of buildings — Contribution of building
> automation, controls and building management — Part 1*. Clause 7 (Method 2) + Annex A.
> ISO 52120-1 supersedes/aligns with **EN 15232-1**.

## 1. What this method does

Method 2 (Clause 7), the **BAC factor method**, gives *"a rough estimation of the impact of
BAC and TBM functions on thermal and electric energy demand of the building according to the
efficiency classes A, B, C and D."*

**BAC efficiency classes:**

| Class | Meaning |
|-------|---------|
| **D** | Non energy efficient |
| **C** | **Standard — the reference** (factor = 1 by definition) |
| **B** | Advanced |
| **A** | High energy performance |

Class C is the reference; B and A always give factors < 1 (an improvement), D gives > 1.

## 2. Which factor applies to which energy use (Table 9)

| Energy use | Composition | BAC factor |
|---|---|---|
| Heating | `Q_H,nd + Q_H,ls` | `f_BAC,H` |
| Heating aux | `W_H,aux` | `f_BAC,el` |
| Cooling | `Q_C,nd + Q_C,ls` | `f_BAC,C` |
| Cooling aux | `W_C,aux` | `f_BAC,el` |
| Ventilation | `W_V,aux` | `f_BAC,el` |
| Lighting | `W_L` | `f_BAC,el` |
| DHW | `Q_DHW,nd + Q_DHW,ls` | `f_BAC,DHW` |

## 3. The equations (§7.3.3, Eq. 4–10)

```
Heating      Q_H,tot,BAC   = (Q_H,nd,B + Q_H,ls) × f_BAC,H   / f_BAC,H,ref      (4)
Heating aux  W_H,aux,BAC   =  W_H,aux            × f_BAC,el  / f_BAC,el,ref     (5)
Cooling      Q_C,tot,BAC   = (Q_C,nd,B + Q_C,ls) × f_BAC,C   / f_BAC,C,ref      (6)
Cooling aux  W_C,aux,BAC   =  W_C,aux            × f_BAC,el  / f_BAC,el,ref     (7)
Ventilation  W_V,aux,BAC   =  W_V,aux            × f_BAC,el  / f_BAC,el,ref     (8)
Lighting     W_L,BAC       =  W_L                × f_BAC,el  / f_BAC,el,ref     (9)
DHW          Q_DHW,BAC     =  Q_DHW              × f_BAC,DHW / f_BAC,DHW,ref    (10)
```

**Practical form used by our estimator.** If your *measured* annual consumption corresponds
to the building's **current** BAC class, rescale from current → proposed:

```
E_proposed = E_measured × f(proposed) / f(current)
savings    = E_measured × (1 − f(proposed) / f(current))
```

## 4. Annex A — the factor tables

### Table A.1 — Overall thermal `f_BAC,th` — Non-residential

| Building type | D | C (ref) | B | A |
|---|---|---|---|---|
| Offices | 1.51 | 1 | 0.80 | 0.70 |
| Lecture hall | 1.24 | 1 | 0.75 | 0.5 ᵃ |
| Education buildings (schools) | 1.20 | 1 | 0.88 | 0.80 |
| Hospital | 1.31 | 1 | 0.91 | 0.86 |
| Hotels | 1.31 | 1 | 0.85 | 0.68 |
| Restaurants | 1.23 | 1 | 0.77 | 0.68 |
| Wholesale and retail trade service buildings | 1.56 | 1 | 0.73 | 0.6 ᵃ |
| **Other types** (sport facilities, storage, industrial, etc.) | — | 1 | — | — |

ᵃ These values highly depend on heating/cooling demand for ventilation.

### Table A.2 — Overall thermal `f_BAC,th` — Residential

| Building type | D | C (ref) | B | A |
|---|---|---|---|---|
| Single family houses / Apartment block / Other residential | 1.10 | 1 | 0.88 | 0.81 |

### Table A.3 — Overall electric `f_BAC,el` — Non-residential

| Building type | D | C (ref) | B | A |
|---|---|---|---|---|
| Offices | 1.10 | 1 | 0.93 | 0.87 |
| Lecture hall | 1.06 | 1 | 0.94 | 0.89 |
| Education buildings (schools) | 1.07 | 1 | 0.93 | 0.86 |
| Hospital | 1.05 | 1 | 0.98 | 0.96 |
| Hotels | 1.07 | 1 | 0.95 | 0.90 |
| Restaurants | 1.04 | 1 | 0.96 | 0.92 |
| Wholesale and retail trade service buildings | 1.08 | 1 | 0.95 | 0.91 |
| **Other types** (sport facilities, storage, industrial, etc.) | — | 1 | — | — |

### Table A.4 — Overall electric `f_BAC,el` — Residential

| Building type | D | C (ref) | B | A |
|---|---|---|---|---|
| Single family / Multi family / Apartment block / Other residential | 1.08 | 1 | 0.93 | 0.92 |

### Table A.5 — Detailed `f_BAC,H` / `f_BAC,C` — Non-residential

| Building type | D&nbsp;H | D&nbsp;C | C&nbsp;H (ref) | C&nbsp;C (ref) | B&nbsp;H | B&nbsp;C | A&nbsp;H | A&nbsp;C |
|---|---|---|---|---|---|---|---|---|
| Offices | 1.44 | 1.57 | 1 | 1 | 0.79 | 0.80 | 0.70 | 0.57 |
| Lecture hall | 1.22 | 1.32 | 1 | 1 | 0.73 | 0.94 | 0.3 ᵃ | 0.64 |
| Education buildings (schools) | 1.20 | — | 1 | 1 | 0.88 | — | 0.80 | — |
| Hospital | 1.31 | — | 1 | 1 | 0.91 | — | 0.86 | — |
| Hotels | 1.17 | 1.76 | 1 | 1 | 0.85 | 0.79 | 0.61 | 0.76 |
| Restaurants | 1.21 | 1.39 | 1 | 1 | 0.76 | 0.94 | 0.69 | 0.6 |
| Wholesale and retail trade service buildings | 1.56 | 1.59 | 1 | 1 | 0.71 | 0.85 | 0.46 ᵃ | 0.55 |
| **Other types** (sport facilities, storage, industrial, etc.) | — | — | 1 | 1 | — | — | — | — |

ᵃ These values highly depend on heating/cooling demand for ventilation.

### Table A.6 — Detailed `f_BAC,H` / `f_BAC,C` — Residential

| Building type | D&nbsp;H | D&nbsp;C | C&nbsp;H (ref) | C&nbsp;C | B&nbsp;H | B&nbsp;C | A&nbsp;H | A&nbsp;C |
|---|---|---|---|---|---|---|---|---|
| Single family houses / Apartment block / Other residential | 1.09 | — | 1 | — | 0.88 | — | 0.81 | — |

### Tables A.7 / A.8 — Detailed `f_BAC,DHW` (identical for **all** building types, res & non-res)

| Building type | D | C (ref) | B | A |
|---|---|---|---|---|
| All non-residential types (A.7) | 1.11 | 1.00 | 0.90 | 0.80 |
| All residential types (A.8) | 1.11 | 1.00 | 0.90 | 0.80 |

### Table A.9 — Detailed `f_BAC,el,L` (lighting) / `f_BAC,el,aux` (auxiliary) — Non-residential only

| Building type | D&nbsp;L | D&nbsp;aux | C&nbsp;L (ref) | C&nbsp;aux (ref) | B&nbsp;L | B&nbsp;aux | A&nbsp;L | A&nbsp;aux |
|---|---|---|---|---|---|---|---|---|
| Offices | 1.1 | 1.15 | 1 | 1 | 0.85 | 0.86 | 0.72 | 0.72 |
| Lecture hall | 1.1 | 1.11 | 1 | 1 | 0.88 | 0.88 | 0.76 | 0.78 |
| Education buildings (schools) | 1.1 | 1.12 | 1 | 1 | 0.88 | 0.87 | 0.76 | 0.74 |
| Hospital | 1.2 | 1.1 | 1 | 1 | 1 | 0.98 | 1 | 0.96 |
| Hotels | 1.1 | 1.12 | 1 | 1 | 0.88 | 0.89 | 0.76 | 0.78 |
| Restaurants | 1.1 | 1.09 | 1 | 1 | 1 | 0.96 | 1 | 0.92 |
| Wholesale and retail trade service buildings | 1.1 | 1.13 | 1 | 1 | 1 | 0.95 | 1 | 0.91 |
| **Other types** (sport facilities, storage, industrial, etc.) | — | — | 1 | 1 | — | — | — | — |

> **Note:** Table A.9 has **no residential rows** — use the overall `f_BAC,el` (Table A.4) for
> residential lighting/aux.

## 5. Important gaps and caveats

1. **"Other types" have no factors.** Sport facilities, storage and industrial buildings are
   listed with only `C = 1` — the standard provides **no D/B/A factors** for them. ISO 52120
   therefore **cannot quantify** a BAC upgrade for such a building. (Note: the example
   building in `SRI/sri_moo_optimizer.py` is a *sports centre*, which falls in this bucket.)
2. **Cooling factors are missing** for Education, Hospital, and all Residential types.
3. **Lighting is meant to be evaluated separately** with EN 15193-1 (Table 9, note d).
4. **Climate is deliberately excluded.** The standard treats climate impact on the *factors*
   as negligible — climate belongs in the underlying energy calculation, not the factor.
5. **The SRI → BAC-class mapping is NOT in this standard.** ISO 52120 defines classes by BAC
   function sets (Clause 5.6, Annex B), not by SRI score. Any SRI-score→class bridge is an
   **approximation we invent** and must be labelled as such.
6. This is a **"rough estimation"** by the standard's own words — appropriate for early design
   / screening, not a substitute for simulation or measurement.

## 6. How our estimator uses this

`SRI/sri_moo_optimizer.py` → `ISO52120EnergyEstimator`:

- Holds Tables A.1–A.9 as data.
- Maps SRI domains → ISO end-uses: `Heating→H`, `Cooling→C`, `DHW→DHW`,
  `Lighting→el,L`, `Ventilation→el,aux`.
- SRI domains with **no ISO 52120 counterpart** (`DE`, `Electricity`, `EV_Charging`, `MC`)
  contribute **no** energy saving. `MC` is folded into class determination, not a separate end-use.
- Applies `savings = E_current × (1 − f(proposed)/f(current))` per end-use.
- Requires an **end-use energy breakdown**; if absent it falls back to a documented default
  split, which is an assumption, not a measurement.
