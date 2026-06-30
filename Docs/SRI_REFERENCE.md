# Smart Readiness Indicator (SRI) — Reference for Claude

> Condensed reference distilled from **"Practical Guide — SRI calculation framework v4.5"**
> (EU technical support team, 2023) plus how this concept maps onto the code in this repo.
> Read this before working on SRI scoring, weighting, or the optimisers in [SRI/](../SRI/).

---

## 1. What the SRI is

The **Smart Readiness Indicator (SRI)** is an optional, common EU scheme for rating the
*smart readiness* of buildings — i.e. the building's capability to sense, interpret,
communicate and actively respond in order to operate more efficiently, interact with the
grid, and adapt to occupant needs.

The score is expressed as a **percentage**: the ratio of the building's achieved smart
readiness to the **maximum smart readiness it could reach** (all applicable services at
their highest functionality level). It is a measure of *potential / capability*, **not a
direct measurement of energy savings** — an important caveat the cost/CO₂ estimators in
this repo deliberately flag.

**Legal basis:** Commission Delegated Regulation **(EU) 2020/2155** (14 Oct 2020),
supplementing the EPBD Directive (EU) 2010/31/EU. Methodology details come from the
technical support studies (Verbeke et al., 2020, DOI 10.2833/41100).

---

## 2. Core structure: 9 domains × 7 impact criteria

Smart-ready **services** are technology-neutral. Each service belongs to one **technical
domain** and is scored against the **impact criteria** it affects.

### The 9 Technical Domains
| # | Official name | Code in repo | JSON file |
|---|---|---|---|
| 1 | Heating | `Heating` | `Heating_Domain_Weights.json` |
| 2 | Domestic hot water | `DHW` | `DHW_Domain_Weights.json` |
| 3 | Cooling | `Cooling` | `Cooling_Domain_Weights.json` |
| 4 | Ventilation | `Ventilation` | `Ventilation_Domain_Weights.json` |
| 5 | Lighting | `Lighting` | `Lighting_Domain_Weights.json` |
| 6 | Dynamic building envelope | `DE` | `DE_Domain_Weights.json` |
| 7 | Electricity | `Electricity` | `Electricity_Domain_Weights.json` |
| 8 | Electric vehicle charging | `EV_Charging` | `EV_Charging_Domain_Weights.json` |
| 9 | Monitoring and control | `MC` | `MC_Domain_Weights.json` |

### The 7 Impact Criteria
1. Energy efficiency (a.k.a. "energy savings")
2. Energy flexibility and storage
3. Comfort
4. Convenience
5. Health, well-being and accessibility
6. Maintenance and fault prediction
7. Information to occupants

These 7 criteria roll up into **3 EPBD "key functionalities"** (the "aggregated scores"):
- **Energy performance & operation** → energy efficiency + maintenance & fault prediction
- **Response to occupant needs** → comfort + convenience + health & well-being + information to occupants
- **Energy flexibility** → energy flexibility and storage

---

## 3. Services and functionality levels

- Every service has several **functionality levels**, **0-indexed** (`level_0`, `level_1`, …).
  Level 0 = least smart / not present; higher = "smarter" implementation with more benefit.
- Each (service, impact criterion) pair has an **ordinal impact score** per level.
- **Negative scores are allowed** and exist by default:
  - `EV-16` (EV grid balancing), criterion *Energy flexibility*: level 0 = **−2**
    (uncontrolled charging is worse than no charging).
  - `MC-29` (Override of DSM control), criteria *Comfort / Maintenance / Information*:
    level 1 = **−2 / −1 / −2** (no override possibility is worse than no DSM control).
- **Service codes** follow domain prefixes: `H-*`, `DHW-*`, `C-*`, `V-*`, `L-*`, `DE-*`,
  `E-*`, `EV-*`, `MC-*`. (Note: code numbering differs between the two optimiser files —
  see §8.)

---

## 4. Assessment methods: A vs B

| | **Method A (simplified)** | **Method B (detailed)** |
|---|---|---|
| Service set | Reduced | Full (up to **54** services) |
| Target | Small / low-complexity buildings (single-family, small MFH, small non-res) | Complex buildings (large non-residential, large MFH) |
| Effort | Lower | Higher |

A **Custom** method is also possible (assessor selects applicable services). In the
spreadsheet, methods are toggled per service via columns J (A), K (B), L (custom).

---

## 5. The calculation pipeline (how a score is computed)

Aggregation is **bottom-up** in 4 conceptual layers. **Normalisation** maps results to
[0, 100]%.

```
Service impact scores (per level, per criterion)
        │   Layer 1: pick the score at the assessed level
        ▼
Domain score per criterion   ──  EQUAL weighting of services within a domain
        │   Layer 2
        ▼
Impact score per criterion   ──  DOMAIN weights (vertical aggregation, climate/building aware)
        │   Layer 3
        ▼
Overall SRI (single %)       ──  IMPACT-criteria weights (horizontal aggregation)
        │   Layer 4
        ▼
SRI %  =  achieved / maximum-achievable
```

**Normalisation bounds** (per domain, per criterion):
- **Minimum** = all applicable services at level 0.
- **Maximum** = all applicable services at their max level.
- `normalised = (achieved − min) / (max − min) × 100`.

**Triage — "Domains present"** flag controls what counts toward the maximum:
- `0` = absent **and not** mandatory → domain skipped entirely.
- `1` = present → assessed normally.
- `2` = absent **but mandatory** → its services still count toward the *maximum obtainable
  score* (penalising the building for not having a mandatory domain).

---

## 6. Weighting factors

Two distinct weight sets, both alterable (default vs user-defined):

### 6.1 Domain weightings (vertical aggregation → impact scores)
- Aggregate domain scores into one impact score per criterion.
- **Each column must sum to 100%.**
- Derived via a **mixed approach**:
  - *Fixed weights* for `Monitoring and control` (all criteria), and for `EV charging` +
    `Dynamic building envelope` (energy savings, maintenance, flexibility).
  - *Equal weights* for comfort / convenience / health / information.
  - *Energy-balance weights* (from the EU **Building Stock Observatory**) for energy
    savings, maintenance, and flexibility on the remaining domains — these vary by
    **climate zone** and **building type**.
  - If no service in a domain affects a criterion → weight forced to **0**.
- Ventilation/heating split uses a transmission-vs-ventilation loss-coefficient ratio
  (Hᴛ / Hᴠ). Cooling weights account for the share of buildings with mechanical cooling.

### 6.2 Impact-criteria weightings (horizontal aggregation → single SRI)
- Aggregate the 7 impact scores into the final SRI. **Must sum to 100%.**
- **Official default** (equal weight across the 3 EPBD key functionalities, 33.3% each):

| Impact criterion | Official default |
|---|---|
| Energy efficiency (savings) | 16.7% |
| Maintenance and fault prediction | 16.7% |
| Comfort | 8.3% |
| Convenience | 8.3% |
| Health & well-being | 8.3% |
| Information to occupants | 8.3% |
| Energy flexibility and storage | 33.3% |

> ⚠️ **Discrepancy to be aware of:** the hardcoded `DEFAULT_IMPACT_WEIGHTS` fallback in
> [sri_moo_pygmo.py](../SRI/sri_moo_pygmo.py) (EE 0.20, flexibility 0.20, comfort 0.15, …)
> does **not** match these official values. The real weights are normally loaded from the
> `*_impact_weighting_factors.json` files per climate zone; treat the in-code dict only as
> a degraded fallback.

---

## 7. Building context inputs

### Climate zones (auto-derived from country)
| Zone | Countries |
|---|---|
| Northern Europe | DK, FI, SE, NO, IS |
| Western Europe | AT, BE, FR, DE, IE, LU, NL, UK, LI, CH |
| Southern Europe | GR, IT, MT, PT, ES, CY |
| North-Eastern Europe | CZ, EE, LV, LT, PL, SK |
| South-Eastern Europe | BG, HR, HU, RO, SI |

> Outside Europe → no default weightings; must use user-defined. The repo's JSON keys use
> labels like `"West Europe"` — confirm exact spelling against the JSON when loading.

### Building type / usage (selects weighting factors)
- **Residential:** single-family house · small multi-family (≤10 units) · large
  multi-family (>10) · other (student housing, care homes…).
- **Non-residential:** offices · educational · healthcare · other.
- **Current limitation:** default weights differ by *type* (res vs non-res) only — **not**
  by usage. All non-residential buildings currently share one weight set.
- **Building state:** Renovated vs Original (no res/new-build differentiation at present).

### Partial compliance (optional)
A service may hold **up to two functionality levels** split by **share of net floor area**
(e.g. 60% at level 3, 40% at level 0). Default share = 100% at the main level.

---

## 8. How this maps to the code in this repo

| Concept | Where |
|---|---|
| Service catalogue loading (9 domain JSONs) | `load_service_catalogue()` in [sri_moo_optimizer.py](../SRI/sri_moo_optimizer.py) |
| Weighting-factor loading (climate-zone aware) | `load_weighting_factors()` / `load_domain_weights_from_residential_json()` |
| 4-layer scoring + normalisation + triage | `SRIScoringEngine.compute_scores()` (optimizer) and `SRIScorer.compute_sri()` (pygmo) |
| Functionality levels as decision variables | `SRIUpgradeProblem` (pygmo UDP) / `SRIUpgradePymoo` (pymoo) |
| Multi-objective optimisation (max ΔSRI, max target impact, max ΔCO₂, min cost) | NSGA-II runners |

**Corrections applied (2026-06-30)** — both optimiser files were reconciled to the
catalogue and the official methodology:
- `sri_moo_pygmo.py` `DEFAULT_IMPACT_WEIGHTS` now uses the official §6.2 values.
- `sri_moo_pygmo.py` domain/impact weights are remapped from the JSON's official
  criterion names to internal snake_case keys (previously the mismatch made the
  pygmo SRI score collapse to 0).
- `sri_moo_pygmo.py` `DEFAULT_UPGRADE_COSTS` now keys all 54 real catalogue codes.
- `sri_moo_pygmo.py` `CO2_FACTORS` zone keys now match the JSON climate zones.
- `sri_moo_pygmo.py` example loads the non-residential weighting file (matching the
  example building) with real service codes, and loads impact weights from JSON.
- Both engines now force a domain's weight to zero when it has no contributing
  services (per v4.5), instead of diluting the impact score.

**⚠️ Remaining divergence (by design, not yet changed):** the two scoring engines
normalise differently. `sri_moo_optimizer.py` uses the spec definition — max-achievable
= all services at their **max level**, so all-max → 100%. `sri_moo_pygmo.py`'s
`SRIScorer` normalises each service by its own per-criterion peak and averages equally,
so all-max ≈ 44% for the example and it is not spec-compliant for non-monotonic scores.
Reconciling pygmo's `SRIScorer` to the optimizer's normalisation is a deliberate design
decision (it changes all pygmo outputs) and was left for explicit sign-off.

- **Cost & CO₂ models remain placeholders** in all three files (see the separate DEEP
  calibration discussion) — not part of the official SRI methodology.

> Per the regulation, this tooling is for **testing/research only** and cannot produce an
> official SRI score or certificate.

---

## 9. Authoritative sources
- **Regulation (EU) 2020/2155:** https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32020R2155
- **Technical support final report (2020):** https://op.europa.eu/en/publication-detail/-/publication/f9e6d89d-fbb1-11ea-b44f-01aa75ed71a1
- **EC SRI topic page:** https://energy.ec.europa.eu/topics/energy-efficiency/energy-efficient-buildings/smart-readiness-indicator_en
- **EU Building Stock Observatory** (energy-balance weight derivation): https://ec.europa.eu/energy/en/eu-buildings-database
- Source PDF: [Docs/Practical Guide SRI calculation framework v4.5.pdf](Practical%20Guide%20SRI%20calculation%20framework%20v4.5.pdf)
