# Energy Savings Potential by SRI Technical Domain and Building Subtype: A Literature Cross-Check for Optimiser Calibration

**Prepared for:** `SRI/sri_moo_optimizer.py` (multi-objective SRI upgrade optimiser)
**Date:** 2026-07-16
**Pipeline stage:** Finalized (Phase 6 of a deep-research run) — compiled from Phase 2's master evidence table (10 parallel domain/prior-art research agents) and Phase 3's synthesis (thematic synthesis, contradiction resolution, gap analysis, circularity assessment; revised at Devil's Advocate Checkpoint 2), then reviewed at Phase 5 (editorial, ethics/AI-disclosure, and Devil's Advocate Checkpoint 3) and revised at Phase 6 to address all findings. Corrections are marked inline as "[DA Checkpoint 2, ...]" (Phase 3) and "[Phase 6 revision, ...]" (Phase 5→6).
**AI disclosure:** see §7 for the full statement and sourcing caveats. In short: this report was produced with AI-assisted literature search and synthesis; source verification was not independently re-run by a human for every citation; treat incomplete or "citation unverified" entries accordingly.

---

## 0. JRC/EC Prior-Art & Foundational Findings

*[Phase 6 revision note: this section was dropped during Phase 4 report compilation despite being cross-referenced twice elsewhere in the document (§3.9, §8) — flagged by the Phase 5 editorial review. Restored here from the Phase 2 master evidence table's §0.]*

Before the 9 domain-specific literature streams (§3.1–3.9) ran, a dedicated Phase 2 research stream examined the JRC/EC's own SRI technical support studies and related EU policy literature — the foundational documents that define the SRI methodology this report cross-checks.

- **Verbeke, S., et al. (2020)** — the JRC/EC's final SRI technical support study — quantifies Heating/Cooling/DHW/Ventilation/Lighting savings **entirely via EN15232 factors**. This is circular, not independent corroboration (see §4.3).
- **Critical structural finding, stated by the JRC itself:** Monitoring & Control and Dynamic Envelope have **no energy-balance basis at all** in the SRI's own founding methodology. The JRC assigns them **fixed placeholder weights (20% MC, 5% DE)** of the total SRI score, explicitly because their energy impact "cannot be derived from an energy balance." This is not a literature gap that more searching fixes — it is a structural feature of how these two domains were defined from the outset, and it is the foundational fact behind §4.2.3's MC non-additivity finding and §6D's double-counting warning.
- **The SRI's ordinal 0–4 scores are a direct linear transform of EN15232 factors**: score 4 = 33.3% saving, score 3 (B) = 26.7%, score 2 (C) = 16.7%, per the JRC's 2018 preparatory methodology study. Any literature that "validates" SRI scores against EN15232 is circular by construction — this is the basis for the circularity screening applied throughout §3 and §4.3.
- **Electricity/self-consumption is the one genuine exception.** The JRC's own literature review (19 independent studies, not EN15232-derived, since EN15232 has no self-consumption coverage at all) found storage/DSM/smart-EV-charging raises self-consumption by **3–52 percentage points**. This is the one JRC-sourced figure treated as independent corroborating evidence rather than circular restatement (§4.3).
- **BPIE (2017)**, "Is Europe Ready for the Smart Buildings Revolution?" — a composite country-level readiness index, not a source of per-domain quantitative savings data; it explicitly excluded BACS data as "not available" at the time. Retained in §8 for completeness but not cited quantitatively anywhere in §3.
- **Leads identified but not fully chased in this pass** (named explicitly in §5.3 as literature-thin gaps, not hard gaps): IEA EBC Annex 81 (Data-Driven Smart Buildings — promising for Monitoring & Control), Annex 67 (Energy Flexible Buildings — relevant to EV Charging/flexibility), Annex 44 (Integrating Environmentally Responsive Elements in Buildings — relevant to Dynamic Envelope), COST Action TU1403 (Adaptive Facades Network), and O'Grady et al. (2021, *Building and Environment*, a BAS meta-analysis, paywalled and not independently verified).

---

## 1. What This Is, and What It Isn't

This report is an independent literature cross-check of the energy-savings magnitudes the SRI optimiser needs, broken out by SRI technical domain (Heating, DHW, Cooling, Ventilation, Lighting, Dynamic Envelope, Electricity, EV Charging, Monitoring & Control) and by eight non-residential/public building subtypes (Offices, Educational, Healthcare, Retail & wholesale, Hospitality, Sports & leisure, Industrial/warehouses/storage, Other public buildings). It exists to support calibration of `SRI/sri_moo_optimizer.py`, which currently derives its energy-savings estimates from the ISO 52120-1:2021 BAC-factor tables (see `Docs/ISO_52120_BAC_FACTORS.md`) via the EN 15232-aligned Method 2 factor approach.

It is **not** a replacement for those ISO 52120/EN 15232 factors, and it does not attempt to re-derive them. The ISO factors remain the optimiser's primary calculation mechanism. What this report adds is: (a) an independent check on whether the standard's per-class savings numbers are broadly consistent with what non-standard-derived literature actually measures or simulates; (b) coverage for the domains the standard does not quantify at all (Dynamic Envelope, Electricity, EV Charging, Monitoring & Control — all zero-weighted or placeholder-weighted in the SRI's own founding methodology, not merely under-researched); and (c) an explicit, honest map of where the literature — independent of the standard — simply does not exist yet, so that gaps are documented rather than silently patched with invented numbers.

A structural point carried over from the Phase 1 scoping revision (triggered by a Devil's Advocate finding, verified against the optimiser's actual code): the optimiser tracks upgrades as discrete `(from_level, to_level)` transitions — i.e., it needs **stepwise**, per-class-transition data (D→C, C→B, B→A), not just endpoint (D→A) comparisons. Almost none of the literature surveyed here reports data at that granularity. Every table row below is explicitly flagged **SW** (stepwise) or **EP** (endpoint-only) for exactly this reason, and §6 below states plainly what that means for how endpoint figures may and may not be used.

---

## 2. Methodology Summary

This section is condensed from what is evident in the Phase 2 master evidence table and Phase 3 synthesis; the full Phase 1 methodological blueprint is not reproduced here verbatim because it was not provided as an input to this compilation step.

- **Design:** rapid evidence assessment (not a full systematic review) across 10 parallel research streams — one per SRI technical domain (9) plus one prior-art/foundational stream covering the JRC's own SRI technical support studies and related EU policy literature.
- **Sourcing priority:** EU-based field and simulation studies were prioritized where available (Belgium, Norway, Spain, Italy, Netherlands, Denmark, Portugal, Germany recur throughout), with international literature (predominantly US national-laboratory sources — LBNL, PNNL, NREL, DOE — plus some non-EU sources from Hong Kong, Japan, South Africa, Saudi Arabia, Australia) used to fill gaps where EU-specific evidence did not exist. Geographic origin is recorded per row precisely because transferability to an EU SRI context is not guaranteed (see §6F).
- **Confidence rubric:** each row carries an explicit **H/M/L** (High/Medium/Low) confidence rating, assigned per-source by the originating Phase 2 research agent based on study type, sample size/duration, independence from vendor or industry-association funding, and (where applicable) geographic match to the EU. Vendor-authored sources are explicitly flagged and excluded from central estimates (retained only as plausibility ceilings) rather than blended in.
- **Granularity and isolation tagging:** every row is tagged **SW/EP** (stepwise vs. endpoint-only, per the Phase 1 revision above) and **ISO/BUN** (domain-isolated vs. bundled with other measures/domains) — both material to whether a figure can be used directly or needs adjustment before use.
- **Search strategy:** each domain agent ran multiple query variations (3+ minimum) per subtype before reporting an evidence gap as confirmed rather than merely unsearched; the master table and this report distinguish "hard gap" (exhausted search, confirmed absent) from "literature-thin gap" (plausible leads exist but were not fully chased) — see §5.3.
- **Circularity screening:** sources that derive their savings figures entirely from EN 15232's own tables (i.e., restate the standard rather than independently test or measure it) were flagged and excluded from being counted as corroborating evidence — see §4.3.
- **No fabrication rule:** where a citation in the Phase 2 compilation was incomplete (missing full author names, title, venue, or year), that incompleteness is carried forward explicitly into §8 rather than silently completed from outside knowledge. Where a figure was described as "unverified," "search-snippet only," or "paywalled," that caveat is preserved in the table cell.

---

## 3. Sourced Comparison Tables by SRI Domain

### 3.0 How to read these tables

- **Savings Range**: as reported by the source; where a source reports multiple figures (e.g., by system type, by control strategy), all are listed. "No credible standalone estimate found" is used verbatim (per the original task brief) where a domain×subtype cell has no credible independent data — never estimated or interpolated.
- **Granularity**: **SW** = stepwise/per-class-transition data available; **EP** = endpoint-only (typically "before controls" vs. "best-practice controls," roughly D-vs-A). See §6A for why this distinction is load-bearing for the optimiser.
- **Isolation**: **ISO** = domain-isolated (the figure reflects only this SRI domain's contribution); **BUN** = bundled (the figure mixes this domain with other measures or domains, e.g., HVAC-bundled heating+cooling).
- **Confidence**: **H/M/L** as assigned by the Phase 2 research agents (see §2). Where a rating combines two considerations (e.g., "H (measured)/M (geo)"), both are preserved rather than collapsed to one letter.
- **Source**: short Author-Year form; full bibliographic detail (where available) is in §8. Sources flagged "citation unverified," "search-snippet only," or "vendor-sponsored" in the Phase 2 compilation retain that flag here.
- Cross-cutting findings that apply to an entire domain (not one subtype) are given as a short intro paragraph before each domain's table, drawn directly from the master evidence table's own domain-level framing.

---

### 3.1 Heating

Cross-cutting: **Khabbazi et al. (2025)** — systematic review, 80 papers / 154 field tests, commercial HVAC. Filtered field-measured median = **15% energy / 13% cost**. This source also documents the strongest performance-gap mechanism found anywhere in the corpus: zone-level and short-duration and simulation-benchmarked studies systematically overestimate savings relative to whole-building, long-duration, measured studies (27% vs. 13% zone-vs-whole; 57% vs. 22% short-vs-long). This pattern recurs across nearly every other domain in this report (see §4.1, Theme A) and should be treated as a general caution, not a heating-specific quirk. **Vandenbogaerde et al. (2023/2025)** independently simulation-tested EN ISO 52120-1 against building-specific numerical simulation for heating emission control: 19–71% (vs. the standard's single fixed factor per class) — direct evidence that the standard's classes compress a much wider real range (see §4.1, Theme D).

**Circularity flag:** the Waide/eu.bac (2019) report (14% EU-wide primary energy by 2038, all-TBS) is entirely EN15232-derived and industry-association-funded — it is **not** independent corroboration despite its superficial EU-wide-dataset appearance (see §4.3).

| Building Subtype | Savings Range | Baseline / Denominator | Gran. | Isol. | Typical Intervention Studied | Study Type / Tier | Geographic Scope | Conf. | Source |
|---|---|---|---|---|---|---|---|---|---|
| Offices | 9–51% | Heating energy | SW | ISO | Stepwise BAC/TBM heating-control upgrade (specific measures not itemized in Phase 2 source) | Field / Academic | Germany | H | Goldschmidt (2026) |
| Offices | 19.2% (14–25%) | Heating energy | EP | ISO | EMCS/BAC control retrofit, 6 US federal office buildings (measures not itemized) | Field (6 bldgs) / Nat'l agency (DOE/PNL) | US | H | Szydlowski (1993) |
| Offices | 22–56% HVAC (heating component: DCV drives most; **multi-speed fan control INCREASES heating use**) | HVAC energy | SW | BUN | Demand-controlled ventilation (DCV) + multi-speed fan control — note: multi-speed fan control increased simulated heating energy use (an offsetting finding, not a clean saving) | Simulated / Nat'l agency (PNNL) | US | M | Wang et al. (2011), PNNL-20955 |
| Retail/wholesale | 16–47% HVAC | HVAC energy | SW | BUN | Same DCV + multi-speed fan-control bundle, retail application | Simulated / Nat'l agency | US | M | Wang et al. (2011), PNNL-20955 |
| Hospitality | 24–58% HVAC (occupancy-centric) | HVAC energy | EP | BUN | Occupancy-centric HVAC setback/scheduling tied to real-time occupancy | Simulated, 19 climates / Academic | US | M | Pang et al. (2021) |
| Sports/leisure (pools, closest match) | ~8% cost (control-only); 20%/40% (predictive+solar); ~20% (heat recovery, bundled) | Facility energy | EP | Mixed | BEMS control-only vs. predictive+solar-integrated control vs. heat-recovery retrofit — three separate intervention tiers within one review | Systematic review (524 papers screened) / Academic (NTNU) | Norway/EU | H (review) / M (sub-studies) | Smedegård et al. (2021) |
| Educational | **No credible standalone estimate found** | — | — | — | Adjacent data only: a Danish MPC school case exists (IEA Annex 81) but attribution is ambiguous and not citable as a clean figure | — | DK (lead only) | — | Gap |
| Healthcare | **No credible standalone estimate found** | — | — | — | A Cochrane systematic-review *protocol* (2024) itself confirms evidence scarcity — stronger than "not found," it is "a review body has looked and found nothing yet" | — | — | — | Hard gap |
| Industrial/warehouse | **No credible standalone estimate found** | — | — | — | Cold-storage refrigeration literature exists but is a different end-use and was deliberately excluded, not unsearched | — | — | — | Hard gap |
| Other public | Qualitative only, no % figure | — | — | — | No intervention studied — qualitative finding that heating-control underperformance correlates with facilities-management staff turnover (library case study) | Field (qualitative) / Academic (UK) | UK | L–M | Gupta et al. (2017) |

---

### 3.2 Domestic Hot Water (DHW)

Standard baseline (ISO 52120 A.7/A.8): `f_BAC,DHW` is **identical across all building types**, residential and non-residential — C→A ≈ 20%, D→A ≈ 28%; the only end-use in the standard with no per-type variation at all. **Key independent finding contradicting the standard's type-invariance**: Vandenbogaerde et al. state plainly that DHW's "share in office energy consumption is rather negligible, unlike residential buildings" — direct evidence that savings-relevance varies by building type in a way the flat factor does not encode. See §4.2.1 for the full contradiction resolution (the measured *rate* itself, not just materiality, diverges from the standard's implied value in both directions across subtypes).

| Building Subtype | Savings Range | Baseline / Denominator | Gran. | Isol. | Typical Intervention Studied | Study Type / Tier | Geographic Scope | Conf. | Source |
|---|---|---|---|---|---|---|---|---|---|
| Offices | Thermal 20.3%, pump elec. 88.0% (DHW described as "negligible" for offices generally) | % DHW thermal + pump elec. | EP | ISO | DHW recirculation-pump control + thermal setpoint/schedule optimization, 1-site field measurement | Field (1 site) / State agency (MN) | US | M–H | CARD/CEE (2018) |
| Educational | Thermal 11.4%, pump elec. 96.2% | % DHW thermal + pump elec. | EP | ISO | Same recirculation-pump control + setpoint optimization, educational site | Field (1 site) / State agency (MN) | US | M | CARD/CEE (2018) |
| Healthcare | Thermal 48.6%, elec. 68.6% | % DHW circuit energy | EP | ISO | Demand-based recirculation control + setpoint reduction — **zero Legionella detected** under the tested regime, directly addressing the safety-override concern | Field / Academic (Italy) | EU | H | Vincenti et al. (2025) |
| Healthcare (context) | DHW ≈ 15% of hospital thermal load | — | — | — | N/A — contextual materiality figure, not an intervention study | Modelled / Academic (Spain) | EU | M | Sánchez-Barroso et al. (2020) |
| Retail/wholesale | **No credible standalone estimate found** | — | — | — | — | — | — | — | Gap |
| Hospitality | Thermal 9.9–15.9%, pump elec. 70–93% (multi-site); tank relocation 3.69% (not a control measure); generator sequencing optimization 75% (auxiliary heater use) | % DHW thermal/elec. | EP | ISO (recirc sites) / N/A (relocation) | DHW recirculation control (multi-site); storage-tank relocation (not itself a control measure); auxiliary-generator sequencing optimization | Field (multi-site US) + sim (EU) / State agency + academic | US + EU (Spain) | M–H | CARD/CEE (2018); hotel-industry journal sources (citation incomplete) |
| Sports/leisure | **No credible standalone estimate found** | — | — | — | Conflated with pool-water heating in the available literature — no clean DHW/shower-isolated figure exists, so this is a conflation gap, not an absence of related literature | — | — | — | Gap (conflation) |
| Industrial/warehouse | **No credible standalone estimate found** | — | — | — | Self-consistent with ISO 52120's own gap — the standard provides no DHW factor for "Other types" either | — | — | — | Gap (self-consistent) |
| Other public | **No credible standalone estimate found** | — | — | — | No distinct evidence; closest-match recommendation is to use the Offices/Educational figures as a proxy, flagged as such | — | — | — | Gap |

**Validation point — corrected [Phase 6 revision, DA Checkpoint 3, M1]:** Bonomolo et al. (2021) — one of only two real-world validations of the DHW BAC factor found in the entire corpus (office + residential, Italy) — measured 27.93%. The original draft of this report compared that figure to "the standard's implied ~20% C→A" and concluded the standard "may be conservative." That comparison is wrong on two counts: (1) 27.93% is not close to the standard's C→A figure (~10%, computed as 1 − 1.00/1.11 from ISO 52120 Table A.7) — it is instead almost exactly equal to the standard's own **D→A** figure (1 − 0.80/1.11 = 27.93%, to four significant figures); (2) that exact numerical match is itself a reason for caution, not confidence — it raises the possibility that Bonomolo's reported figure is derived from (or contaminated by) the standard's own D→A calculation rather than being an independently measured field result, which is precisely the circularity risk §4.3's screen is meant to catch and did not catch for this source. Until the primary source is verified (it is marked [INCOMPLETE] in §8), this data point should be treated as **an open circularity question, not a validation of the standard**, and should not be used to support a "the standard reads conservative" claim in either direction.

---
### 3.3 Cooling

The standard has **no cooling factor at all** for Education, Hospital, or Residential building types — this gap is flagged by `ISO_52120_BAC_FACTORS.md` itself (Table A.1/A.5). Independent literature search prioritized filling exactly this gap.

| Building Subtype | Savings Range | Baseline / Denominator | Gran. | Isol. | Typical Intervention Studied | Study Type / Tier | Geographic Scope | Conf. | Source |
|---|---|---|---|---|---|---|---|---|---|
| Offices | 1–58% (emission control, EN 52120-testing simulation) | Cooling energy | SW | ISO | Simulated stepwise emission-control upgrade tested directly against EN ISO 52120-1 classes | Simulated / Academic | EU (Belgium) | M | Vandenbogaerde (2026) |
| Offices | Adaptive setpoint 12–38% of cooling energy; combined measures 23–39% of HVAC energy | Cooling / HVAC energy | SW | ISO (setpoint) / BUN (combined) | Adaptive cooling-setpoint control; combined-measures bundle, across all US climate zones | Simulated, all US zones / Nat'l agency (LBNL) | US | H | Chen & Yin (2022) |
| Offices | >30% chiller electricity | Chiller/cooling-plant elec. | EP | ISO | Chiller-plant control optimization, 4-year real operational data, 3 office towers | **Field** (4yr real data, 3 towers) / Academic | Hong Kong (non-EU) | H (measured) / M (geo) | HKUST (2018) |
| **Educational** | **14% / 18% / 24%** for Class C / B / A — explicitly fills the standard's own documented gap; paper directly quotes the ISO 52120 clause confirming no cooling factor exists for education | Sensible cooling energy | **SW (class-based)** | ISO | ISO 52120 BAC-class-by-class cooling-control upgrade — genuine stepwise C→B→A data, single case study; explicitly fills the standard's Education cooling-factor gap | Simulated (single case study) / Academic (thesis, not peer-reviewed) | **EU (Italy)** | H (for gap-filling purpose) | Albesiano (2023), Politecnico di Torino |
| **Healthcare** | OR-level 75% gas / 69% elec. (setback); hospital-wide extrapolation only 1.12%/0.64% of total; regulation-by-occupancy 37.5%, by-schedule 40%; chiller-plant ANN optimization 7–10% | Mixed (OR-level & hospital-total both reported) | EP | BUN (fan+chiller combined in summer) | Operating-room HVAC setback scheduling; occupancy-based and schedule-based regulation; chiller-plant ANN-based optimization (3 related Spanish hospital studies) | **Field** (real hospital) + sim / Academic | **EU (Spain, 3 studies)** | H | Tejero-González et al. (2022); Castellanos-Antolín et al. (2022); Dulce-Chamorro et al. (2021) |
| Retail/wholesale | 17.6% (chiller plant, measured); 9% (AI load forecasting, trade-press) | Chiller/cooling energy | EP | ISO | Chiller-plant control retrofit (measured); AI-based cooling-load forecasting (trade-press, unverified tier) | Field / Academic + trade-press | Hong Kong (non-EU) | M / L | "2025 Smart Cities" (citation incomplete); CIBSE Journal (citation incomplete) |
| Hospitality | Qualitative only — exact % unconfirmed (paywalled) | — | SW (steps named, % unconfirmed) | BUN | Named stepwise cooling-control measures (specific % savings paywalled/unconfirmed), 5 Mediterranean-climate simulated cities | Simulated, 5 Mediterranean cities / Academic | **EU** | L–M | Becchio et al. (2017) |
| Sports/leisure | ~8% (BEMS dew-point/wet-bulb control) | Facility energy cost | EP | BUN | BEMS dew-point/wet-bulb setpoint control | Modelled / Academic | Unconfirmed (likely Portugal) | L–M | Ribeiro et al. (2016) |
| Industrial/warehouse | 30–40% (8–72% range) — bundled with door-protection/retrofit, refrigerated cold-storage only, **not** ambient warehouses | Refrigeration energy | EP | BUN | Refrigeration control + door-protection retrofit bundle, cold-storage only — NOT representative of ambient/non-refrigerated warehouses (scope mismatch flagged) | Field survey, 329 facilities / **EU-funded (IEE)** | Pan-EU | M | ICE-E project (citation incomplete) |
| Other public (museums/archives, closest match) | ~15% (museum, temp+RH); 40% (archive, intermittent conditioning vs. strict single-setpoint) | HVAC/climate-control energy | EP | BUN (temp+RH combined) | Intermittent/setback climate-control scheduling vs. strict single-setpoint baseline, museum and archive climate control | Field + sim / Academic (TU Eindhoven) | **EU (Netherlands)** | M | Kompatscher et al. (2017, 2019) — same author group, not independent replication (see §4.3) |

---

### 3.4 Ventilation

**Key structural finding:** EN15232/ISO 52120's own electrical factor (`f_BAC,el`) bundles ventilation auxiliary electricity together with **lighting** electricity — the standard itself never isolates `W_V,aux` as a standalone figure. Most independent literature also blends fan-electricity savings with indirect thermal-load savings rather than reporting them separately, so most rows below are bundled (BUN) even where labelled otherwise for the *dominant* effect measured.

| Building Subtype | Savings Range | Baseline / Denominator | Gran. | Isol. | Typical Intervention Studied | Study Type / Tier | Geographic Scope | Conf. | Source |
|---|---|---|---|---|---|---|---|---|---|
| Offices | 12% (Montreal, 1yr field); 7.8% (heating+cooling, low-occupancy caveat); 9–28%/43–46% coil energy by system type; 7–17% (energy+cost+peak, 4 scenarios); **NOT cost-effective** under a lower baseline-ventilation-rate assumption in most CA climate zones | Mixed (whole-floor / coil / HVAC energy) | Mixed SW/EP | Mostly ISO | Demand-controlled ventilation (DCV), multiple independent studies/system types — Fisk (2010) shows baseline-assumption sensitivity alone can flip DCV from cost-effective to not, in most California climate zones | Field + sim / Academic + Nat'l lab (LBNL/CEC) | Canada, US | M–H | Donnini (1991–92); Gabel (1986); Knoespel/Emmerich (year not specified); Haghighat (year not specified); **Fisk (2010)**, LBNL |
| Offices | 50% fan / 34% heat-loss (field, Belgium) | Fan elec. + heat-loss, separately | EP | ISO | Demand-controlled ventilation, field-measured, fan-electricity and heat-loss reported separately | Field / Academic (KU Leuven) | **EU (Belgium)** | H | Merema et al. (2018) |
| **Educational** | 38% (Norway field); 21% heating/87% fan (Norway); 50–55% fan/36–47% heat-loss (Belgium, kindergarten+lecture hall) | Ventilation energy, fan/heat split available | EP | ISO | DCV, field-measured across independent Norwegian and Belgian school studies | **Field**, multiple independent EU countries / Academic | **EU (Norway, Belgium)** | H | Mysen et al. (2005); Wachenfeldt (2007); Merema et al. (2018) |
| **Healthcare** | 37.5%/40% (OR-specific, setback vs. continuous) — safety/code-constrained, savings from unoccupied-hours only, not representative hospital-wide | OR-specific energy | EP | ISO | Operating-room ventilation setback during unoccupied hours (code/safety-constrained ceiling) | Hybrid field-calibrated sim / Academic | **EU (Spain)** | M | Castellanos-Antolín et al. (2022) |
| Retail/wholesale | 19% elec./up to 100% heating (Sacramento); 40%/30% cooling/heating season (Tokyo) | Whole-building | SW (seasonal) | BUN (economizer) | DCV combined with economizer/free-cooling control, simulated, US and Japan | Simulated / Academic | US, Japan (non-EU) | L–M | Brandemuehl (1999); Ogasawara (1979) |
| Hospitality | 17% elec. (restaurant, ~half attributable to DCV alone); kitchen ventilation often **cannot** reduce airflow at low occupancy (code-constrained, parallel to healthcare) | Whole-building | EP | BUN | DCV in restaurant/kitchen spaces — code-constrained minimum-airflow requirements limit achievable savings, parallel to the healthcare OR finding | Simulated / Academic + DOE guidance | US | L–M | Brandemuehl (1999); DOE kitchen guidance (citation incomplete) |
| Sports/leisure | 40–70% (highest range in NIST table, high-density spaces); 26–53% (London auditorium sim); pool literature skews to heat-recovery not DCV | Whole-building/heating | SW | BUN | DCV in high-occupancy-density spaces (auditoria); pool-ventilation literature favors heat-recovery over DCV | Field + sim / Mixed | Mixed (incl. UK, Switzerland, Norway) | L–M | NIST Table 2 (year not specified); Warren & Harper (1991) |
| Industrial/warehouse | **No credible standalone estimate found** | — | — | — | Plausible genuine gap (low, non-CO2-driven occupancy density) but this is inference, not a sourced fact | — | — | — | Hard gap |
| Other public | 13–20% (Finland, old/thin source); 20–60% (entrance halls, vendor-estimate tier) | Daily energy | EP | BUN | DCV / entrance-hall ventilation control (dated, thin evidentiary base) | Field (thin) / Academic (old) | Finland | L | Kulmala (1984) |

---
### 3.5 Lighting

Best-evidenced domain in the entire corpus — includes a genuine meta-analysis (LBNL, 240 estimates / 88 sources) and a direct EN 15193-1/LENI-methodology paper (the standard EN 15232 Annex A.9 itself defers lighting evaluation to EN 15193-1).

| Building Subtype | Savings Range | Baseline / Denominator | Gran. | Isol. | Typical Intervention Studied | Study Type / Tier | Geographic Scope | Conf. | Source |
|---|---|---|---|---|---|---|---|---|---|
| Offices | Occupancy 24–38% avg; daylighting 16–32%; combined 38–79%; occupant-centered adaptive 38–73% | % lighting energy | **SW** (control-type breakdown) | ISO | Occupancy sensing / daylight-linked dimming / combined systems / occupant-centered adaptive control — control-type-by-control-type breakdown from a 240-estimate, 88-source meta-analysis | **Meta-analysis** (240 estimates) + multiple field studies / Nat'l lab (LBNL) + academic | US, Switzerland | **H** | Williams et al. (2011/2012); Galasiu (2007); Nagy et al. (2015); Dikel (2018) |
| Offices | EN15193-1/LENI method: daylight-linked ≥20% in 39% of configs; combined ≥20% in 100%, ≥30% in 74% | LENI (lighting energy/m²/yr) | SW | ISO | EN 15193-1 LENI-methodology daylight-linked and combined lighting-control evaluation, 4 EU climate zones | Standards-derived, applied across 4 EU climates / Academic | **EU** (Lisbon/Ankara/Berlin/Minsk) | H | Lo Verso & Pellegrino (2019) |
| **Educational** | 18–46% (3 daylight-control topologies compared, Belgium field); >60%/+46% (classroom auto-off + tuning, IEA program) | % lighting energy | SW | ISO | Three compared daylight-control topologies (Belgium field); classroom automatic-off plus lighting-level tuning (IEA SHC Task 50, 10-country program) | Field / Academic (KU Leuven) + IEA multi-country program | **EU (Belgium)** + 10-country IEA | H | Delvaeye (2016); IEA SHC Task 50 (year not specified) |
| Healthcare | 13% (**manual outperformed automated** in this NICU study — counter-intuitive) | % lighting energy | EP | BUN (spectral tuning combined) | Automated spectral-tuning + occupancy lighting control, NICU — manual control outperformed the automated system in this small field study | Field (small, n=5 rooms) / Nat'l lab (PNNL) | US | M | Safranek et al. (2021) |
| Retail/wholesale | 24–66¢/ft²/yr (utility-funded, not peer-reviewed); generic 20–60% claims largely unverified | Mixed | EP | ISO | Daylighting/lighting-control retrofit, utility-program white paper (cost-savings units, not %, carried forward as given) | Field (utility white paper) / Utility-funded | US | M | Heschong Mahone Group (1999/2003) |
| Hospitality | **No credible standalone estimate found** | — | — | — | Vendor-only claims (50–70%) exist but are unverified and excluded | — | — | — | Gap |
| Sports/leisure | **No credible standalone estimate found** | — | — | — | Vendor-only claims exist but are unverified and excluded | — | — | — | Gap |
| Industrial/warehouse | **No credible standalone estimate found** | — | — | — | Despite expectation of strong coverage, no independent source was retrieved; one lead (PNNL/DLC field report PDF) was identified but not retrieved | — | — | — | Gap (unresolved lead) |
| Other public | **No credible standalone estimate found** | — | — | — | No usable evidence — one search hit was outdoor street lighting, off-target for this domain's scope | — | — | — | Gap |

**Performance-gap literature (applies across subtypes):** Pigg (1996) — occupants with occupancy sensors were "half as likely" to manually switch off lights (a rebound effect); Bordass (1994) — high occupant dissatisfaction with photocontrol miscalibration/false-offs. See §4.1 Theme A and §6's occupant-behavior caveat.

---

### 3.6 Dynamic Envelope (DE)

**Zero ISO 52120 coverage — fully open literature.** Confirmed as the domain with the **most severe real coverage gaps** outside Offices. IEA ECBCS Annex 44 and COST Action TU1403 exist as named EU-institutional research programs, but no single aggregate savings figure was extractable from them without deeper mining not performed in this pass (flagged as a literature-thin lead, §5.3).

| Building Subtype | Savings Range | Baseline / Denominator | Gran. | Isol. | Typical Intervention Studied | Study Type / Tier | Geographic Scope | Conf. | Source |
|---|---|---|---|---|---|---|---|---|---|
| Offices | **Field-measured anchor: ~10–20%** HVAC/lighting from automated shading (Chicago, 44wk field; Berkeley, 20mo field w/ uncertainty bounds, ~0% cooling in one config); simulated range far wider (14–53%, up to 60–76% lighting in lab conditions) — the field band is the defensible anchor, the simulated/vendor range is an upper bound only | Mixed (HVAC/lighting/cooling separately in best sources) | Mostly SW | Mixed ISO/BUN | Automated dynamic shading/electrochromic-glazing control — field-measured anchor is the recommended basis; simulated range is an upper bound only | **Field** (2 strong US studies) + sim (EU: Denmark, Portugal, Greece/Sweden) / Academic + Nat'l lab (LBNL) | US + EU (DK, PT, GR, SE) | H (field) / M (sim) | Lee et al. (2025, Chicago); Lee et al. (2005, LBNL/Berkeley); Nielsen (2011, DK); Teixeira et al. (2024, PT) |
| Offices | **VENDOR — excluded from central estimate**: 48–53% | — | EP | ISO | Electrochromic glazing, vendor-authored simulation — excluded from central estimate, retained as plausibility ceiling only | Simulated / **Vendor-sponsored** (SAGE Electrochromics) | US | **L — flagged** | Sbar et al. (2012) |
| Educational | One bundled/closest-match source only (LBNL higher-ed demo, 12–30% perimeter lighting) | Lighting energy | EP | BUN | Automated shading, perimeter-zone lighting only (demo/lab test-bed, not a full-building field study) | Field (lab + demo) / Nat'l lab | US | M | LBNL FlexLab (citation incomplete) |
| Healthcare | One EU simulated source (Belgium, cooling load 40–80% via louvers, dynamic-EC case not cleanly isolated) | Cooling load | SW | Partial BUN | Automated louver shading (the dynamic-electrochromic case is not cleanly isolated from the static-louver case in this source) | Simulated / Academic | **EU (Belgium)** | M | Unnamed Belgium hospital-room study (citation incomplete) |
| Retail/wholesale | **No credible standalone estimate found** | — | — | — | Confirmed zero after repeated query variations | — | — | — | Hard gap (confirmed) |
| Hospitality | One marginal, automation-status-uncertain source (20.5%) | Total energy | EP | BUN | Shading — automation status uncertain, may be static rather than dynamically controlled (flagged accordingly) | Simulated / Academic | Saudi Arabia (non-EU) | L | Unnamed Saudi hotel study (citation incomplete) |
| Sports/leisure | **No credible standalone estimate found** | — | — | — | Confirmed near-zero — available literature is static shading-ratio design optimization, explicitly excluded as out-of-scope (not automated control) | — | — | — | Hard gap (confirmed, scope-excluded) |
| Industrial/warehouse | **No credible standalone estimate found** | — | — | — | Confirmed near-zero, exactly as anticipated — only component-level lab test found, not a building-type study | — | — | — | Hard gap (confirmed) |
| Other public | **No credible standalone estimate found** | — | — | — | No evidence, no closest-match candidate identified | — | — | — | Hard gap |

**Performance-gap (qualitative only):** occupant override for glare/view is well documented (Germany field test-cell study; Dutch office field study) but not quantified into a clean % penalty in any source located.

---
### 3.7 Electricity (Self-Consumption / Storage / Load Management)

**Zero ISO 52120 coverage.** A pervasive **sizing-vs-management conflation risk** runs across this domain's literature — many "on-topic" sources actually report jointly-optimized PV/battery *sizing* outcomes, not the effect of smart *management* on a *fixed* asset (the domain's actual scope for the optimiser, which is deciding control/management upgrades, not asset sizing). No JRC/IEA-PVPS report was found that quantifies smart-management savings at the non-residential building level specifically — the evidence base is almost entirely academic case studies.

| Building Subtype | Savings Range | Baseline / Denominator | Gran. | Isol. | Typical Intervention Studied | Study Type / Tier | Geographic Scope | Conf. | Source |
|---|---|---|---|---|---|---|---|---|---|
| Offices | Battery +13–24pp self-consumption, DSM +2–15pp (review, residential-dominated base, used as proxy); self-consumption 24%→37% w/ battery (bundled w/ thermal storage, DE case); peak reduction 5–15% avg / up to 56% short-duration (US ADR field data) | Self-consumption rate / peak demand | SW | Mixed ISO/BUN | Battery storage dispatch + demand-side management (DSM); automated demand response (ADR) event participation | Review + sim + **field** (LBNL ADR) / Academic + Nat'l lab | EU review (residential-heavy) + Germany + US | M | Luthander et al. (2015); "Energies" journal (2017, citation incomplete); LBNL ADR reports (citation incomplete) |
| Educational | Weak — one non-EU, non-isolated case within a multi-building-type simulation | — | — | Not isolated | Not cleanly extractable from source — multi-building-type simulation, figure not isolable to Educational alone | Simulated / Academic | US (Los Angeles) | L | Frontiers in Energy Research (2025, citation incomplete) |
| Healthcare | 8.1% annualized cost reduction (load-shifting, co-optimized w/ sizing — not isolated) | Cost | EP | Not isolated | Battery load-shifting, co-optimized jointly with battery sizing (management effect not isolated from sizing effect) | Simulated / Academic | US (Los Angeles) | M | Same source as above, hospital case |
| Retail/wholesale | **No credible standalone estimate found** | — | — | — | Leads only, not independently verified — a Greek net-billing study is promising but unconfirmed | — | — | — | Unresolved |
| Hospitality | 99% self-sufficiency (likely conflates sizing+dispatch, modest journal tier) + heavy unsourced vendor claims (85–95%) | — | EP | Not isolated | PV+battery sizing and dispatch jointly optimized (management effect not isolated); additional unsourced vendor claims not independently verifiable | Simulated / Academic (lower-tier) | Greece (EU) | L | WSEAS (2024, citation incomplete) |
| **Sports/leisure** | **Best evidence in the entire domain**: 5 control strategies on IDENTICAL fixed 1.1MWh/800kW hardware — self-consumption 68.6–84.7% depending purely on dispatch strategy (16pp swing from control choice alone); explicit tariff-context transparency | Self-consumption ratio | **SW (5 strategies, cleanest isolation found)** | **Fully ISO** | Five battery-dispatch control strategies tested on identical, fixed 1.1 MWh/800 kW battery+PV hardware — the cleanest management-only isolation in the entire Electricity domain | **Field-input + sim** (hybrid) / Independent research institute (SINTEF), industry-funded | **EU (Norway)** | **H** | Weniger et al. (2020), Skagerak Arena |
| Industrial/warehouse | **No credible standalone estimate found** | — | — | — | An EU lead (Italy logistics warehouse) was identified, but figures could not be independently verified from the primary text | — | — | — | Unresolved |
| Other public | **No credible standalone estimate found** | — | — | — | 3–13% operating cost reduction across pilot sites appears field-measured/real, multi-country, but is paywalled/unverified — a high-value follow-up target | — | — | — | Unresolved |

**Tariff-dependency finding** (Norway study, Weniger et al. 2020): spot-price volatility alone is "not big enough to make arbitrage profitable" — value requires stacking arbitrage + peak-shaving + self-consumption together. This suggests EU flat-tariff markets may show smaller smart-management value than demand-charge-heavy markets (US) — see §6F.

---

### 3.8 EV Charging

**Zero ISO 52120 coverage.** Critical framing finding, carried directly from §4.2.4: **"% energy saved" is largely a category error for this domain.** EV charging is an *additive* load whose *shape*, not magnitude, is what management optimizes — the dominant, meaningful metrics are peak-demand-reduction %, demand-charge-reduction %, and cost-shift %. Several "headline" figures in the corpus are **burden** figures (uncontrolled EV charging *increasing* peak demand), not savings — the table below uses an explicit **Direction** column (Mitigation / Burden / Mixed) so a burden figure is never misread as a negative saving with an ambiguous sign.

| Building Subtype | Value Metric & Range (Peak-Demand / Cost-Shift) | Direction | Baseline / Denominator | Gran. | Isol. | Typical Intervention Studied | Study Type / Tier | Geographic Scope | Conf. | Source |
|---|---|---|---|---|---|---|---|---|---|---|
| Offices/Workplace | Peak reduction 28.5% (peak-minimizing strategy) vs. uncontrolled; cost-min strategy: 19% cost savings but **+4.9% peak** (tradeoff); demand-charge −15–17%, cost −4.5% (MPC vs. smart benchmark); demand-charge cut to 59–98% of status quo depending on constraint | **MITIGATION** | Peak demand / cost | **SW** (multiple strategies compared) | ISO | Managed/smart EV charging — peak-minimizing (PM) vs. cost-minimizing control strategies compared directly; documents an explicit tradeoff (the cost-min strategy increases peak by +4.9% even while cutting cost 19%) | **Field-data-calibrated** modelling / Academic | UK, US (California) | **H** | Seger (2025, UK); Tucker (2022, SLAC/Google) |
| Industrial/warehouse (fleet depots) | 17% peak-demand-charge reduction (bus depot); 23–32% cost (peak-shaving vs. on-arrival, unverified) | **MITIGATION** | Peak demand / cost | EP | ISO | Fleet (bus depot) charge scheduling — peak-shaving vs. uncontrolled on-arrival charging | Field-calibrated MILP / Academic | South Africa (non-EU) | H | Golden Arrow (2025) |
| Educational | 3–13% (multiple paraphrase-inconsistent figures, unverified primary); EV chargers themselves **increase** campus peak load >17% (burden finding) | **MIXED** | Peak / cost | SW (uncertain) | Partial BUN | Campus EV-charging management (mitigation-side figures unverified/inconsistent); uncontrolled EV charging's burden effect on campus peak load is the more solid finding here | Sim (calibrated on real campus data) / Academic | **EU (Germany, Greece)** | M | Meiers & Frey (2024); Kanellos (2022) |
| Retail/wholesale | EV fast-charging can increase site peak demand **+250%** — no mitigation % found | **BURDEN ONLY** | Peak demand | EP | ISO | Uncontrolled EV fast-charging deployment (burden figure — no mitigating control strategy modelled in this source) | Modelled / **Nat'l lab (NREL)** | US | H (for the burden figure) | Gilleran et al. (2021) |
| Healthcare | **No credible standalone estimate found** | — | — | — | — | Vendor-only claims exist but are unverified and excluded | — | — | — | Gap |
| Hospitality | Burden only (peak demand rising to 250–320kW by 2030) — no mitigation % | **BURDEN ONLY** | Peak demand | EP | ISO | Uncontrolled/projected EV-charging demand growth to 2030 (burden projection, no control strategy modelled) | Modelled / State agency (Australia) | Non-EU | M | South Australian Government (citation incomplete) |
| Sports/leisure | **No credible standalone estimate found** | — | — | — | — | One paper identified but inaccessible | — | — | — | Gap |
| Other public | **No credible standalone estimate found** | — | — | — | — | No evidence located | — | — | — | Gap |

**Negative/tradeoff findings (explicitly requested; corroborate the SRI's own negative EV impact-scores):** Gschwendtner (2023, Zurich) — no strategy achieves both peak-reduction AND solar-alignment simultaneously; V2G shows the **largest tradeoffs** of any strategy category, introducing new peaks. An Applied Energy (2025, citation incomplete) source found V2G cycling increases battery degradation 9–14%/10yr, requiring €70–132/MWh compensation to offset. Seger (2025) additionally notes that cost/emission-optimizing strategies increase peak demand even while achieving their primary objective.

**System-level context (not building-isolated; IEA/IRENA, citation incomplete):** V1G/V2G reduce national 2040 peak loads 6–9% and save ~25% grid-reinforcement cost (France, projection); Germany/Belgium national peak reduction 10–13% (IRENA 2030 projection). Informative context for EU market direction, but **not attributable to any building subtype** — not usable as a per-building calibration input.

---
### 3.9 Monitoring & Control (MC)

**Zero ISO 52120 coverage — and this is confirmed structural, not merely a literature gap** (see §0/JRC prior-art below and §4.2.3). **Central finding, empirically confirmed across every field study located:** MC/FDD/commissioning savings are **not separable** from the HVAC (overwhelmingly) and secondary end-use faults the monitoring process catches and that get fixed in the same intervention. Im et al. (2021) decomposes 100% of hospital "Continuous Commissioning" savings into specific HVAC control-point fixes (AHU status 51%, SAT reset 31%, economizer 8%, damper 5%, pressure 4%) — **zero residual "monitoring-only" component**. Henze, Kircher & Braun (2024) state this as an open, unresolved methodological problem for the whole field, warning explicitly of **double-counting** risk. **Direct implication for the optimiser:** applying MC's headline 8–21% figures as an *additional* stackable saving on top of separately-modeled HVAC savings risks double-counting unless the HVAC baseline already assumes fault-free/well-commissioned operation — see §6D.

Geographic skew: 9 of 12 sources in this domain are US (LBNL/PNNL/DOE/ACEEE) — **no EU institutional quantitative MC savings evidence was found at all** despite targeted search; this absence is itself treated as a finding, not just a gap.

| Building Subtype | Savings Range | Baseline / Denominator | Gran. | Isol. | Typical Intervention Studied | Study Type / Tier | Geographic Scope | Conf. | Source |
|---|---|---|---|---|---|---|---|---|---|
| Offices | 8% median (whole-building, FDD, 26 orgs/550 bldgs); 16% median existing-building commissioning (10–30% range) | Whole-building | EP | **NOT separable** (confirmed empirically) | Fault detection & diagnostics (FDD) + existing-building commissioning — savings not separable from underlying HVAC/lighting fault fixes | Field (large portfolio) / Nat'l lab (LBNL) | US | H | Lin, Kramer & Granderson (2019); LBNL Cx database |
| **Educational** | 10% source energy (2–25% range), 9% elec., 24 UC/CSU buildings, **65% of savings from HVAC-fault fixes** (explicit decomposition); 14–15% (Clark University case) | Whole-building | EP | **NOT separable** (explicit) | Retro-/continuous commissioning — explicitly decomposed: 65% of measured savings attributable to HVAC-equipment-fault fixes, not a standalone MC effect | Field / Nat'l lab (LBNL) | US | H | Mills & Mathew (2009); Clark University case (year not specified) |
| **Healthcare** | **16%, 21%, 19%** across 3 hospitals — **100% of savings explicitly decomposed into HVAC control-point fixes** (strongest single MC finding in the entire project) | Whole-building EUI | EP | **NOT separable** (100% attributed to HVAC) | Continuous commissioning — 100% of savings decomposed into specific HVAC control-point fixes: AHU status (51%), SAT reset (31%), economizer (8%), damper (5%), pressure (4%) | Field (3 hospitals) / Academic | US | **H** | Im et al. (2021) |
| Retail/wholesale | Weak — only via a 14-type simulated PNNL study | Whole-building | EP (sim) | Partial (sim only) | Simulated fault-correction measure, modelled as a discrete line item — NOT empirically validated in real buildings | **Simulated** / Nat'l lab (PNNL) | US | M | PNNL-25985 |
| Industrial/warehouse | 18.3% (cold-store refrigeration end-use, closest-match) | Refrigeration energy (not whole-bldg) | EP | NOT separable (100% = defrost fault fix) | FDD applied to cold-storage refrigeration — 100% of the measured savings attributable to a defrost-fault fix | Field (applied) / Academic | Unconfirmed | M | Unnamed cold-store FDD paper (citation incomplete) |
| Hospitality | Weakest quantified: "lodging = 3%" (lowest of all commissioning segments in the LBNL database) | Whole-building | EP | Not separable | Building commissioning, lodging-segment database figure (lowest of all segments) | Field (database segment) / Nat'l lab | US | M | LBNL Cx database segment |
| Sports/leisure | One vendor-adjacent UK source only (10–30%, bundled with non-MC measures) | Whole-facility | EP | Not isolated at all | Bundled MC + non-MC measures, vendor-adjacent trade-advisory source — low confidence | Trade/advisory / **Vendor-adjacent** | UK | **L — flagged** | SEFE Energy (citation incomplete) |
| Other public | "Public order & safety" segment = 16% (closest-match) | Whole-building | EP (sim) | Partial | Simulated fault-correction, "public order & safety" building segment | Simulated / Nat'l lab | US | M | PNNL-25985 |

**PNNL-25985 partial counter-example:** models "fault correction" as a discrete measure line-item separable from scheduling/setpoints — but only *in simulation*, not empirically validated in real buildings. National potential (aggregate, all 34 measures modelled): ~29%.

---
## 4. Synthesis Findings

This section is pulled directly from the Phase 3 synthesis report, condensed for an engineering readership. Where the synthesis itself was corrected at the Devil's Advocate Checkpoint 2, the correction is preserved and marked inline exactly as it appears in the source.

### 4.1 Six Cross-Domain Themes

**Theme A — The field/simulated/vendor inflation gradient is universal, directional, and has an identified mechanism.** It is not domain-specific noise. Khabbazi et al. (2025) gives the clearest mechanistic account for Heating — zone-level vs. whole-building (27% vs. 13%), short-duration vs. long-duration (57% vs. 22%), and simulation-benchmarked vs. measured studies all inflate independently and tend to co-occur in the same "high" study. The same directional gradient recurs with domain-specific fingerprints: Lighting's LBNL meta-analysis explicitly notes simulations overestimate even *within* its own 240-estimate pool; Ventilation's Fisk (2010) shows baseline-assumption sensitivity alone can flip a measure from beneficial to "not cost-effective"; Dynamic Envelope shows the starkest spread of any domain — field ~10–20% vs. standard-methodology simulation 14–53% vs. the sole vendor-authored source's 48–53% [Phase 6 revision: corrected from "48–60%" — the 60–76% figure blended into that range in the Phase 4 draft actually belongs to the non-vendor, academic/national-lab lab-conditions upper bound in §3.6, not to the vendor source, which reports 48–53% only]; Cooling shows it inside a single paper (Vandenbogaerde's simulated 1–58% range against the standard's one fixed factor). This recurs in enough independently-authored domains to treat as a general property of building-energy-savings literature, not an artifact of one research group.

**Theme B — Structural attribution entanglement is a distinct problem from evidence scarcity, and the two get conflated.** Monitoring & Control is the sharpest case: it has *good* evidence (Offices, Educational, Healthcare all reach 2+ credible field sources) but that evidence is 100% decomposable into HVAC/lighting fault-fixes with zero residual. Weaker versions of the same entanglement recur elsewhere: the standard's own `f_BAC,el` bundles ventilation auxiliary electricity with lighting electricity so a "pure" ventilation-only factor is definitionally unavailable even in principle; Dynamic Envelope studies routinely report HVAC+lighting savings jointly rather than isolating shading's HVAC contribution; the Electricity domain has a parallel but distinct entanglement — many "smart management" sources actually report jointly-optimized *sizing* outcomes, conflating asset-sizing gains with dispatch/management gains. MC is the most severe instance, but it is a point on a spectrum, not a unique anomaly.

**Theme C — Evidence concentrates overwhelmingly in three subtypes (Offices, Educational, Healthcare) and is thin-to-absent in the other five.** This holds *within every domain* (see §5.2), not just as a vague overall impression. The mechanism is plausible and consistent: offices and schools have the most retrofit/ESCO market activity, public funding, and easy building access for researchers; healthcare gets attention because of high energy intensity and safety-critical control logic. Retail, hospitality, sports/leisure, industrial/warehouse, and "other public" buildings are simply under-instrumented and under-published across the board — every domain report exhausted 3+ query variations before reporting absence in these subtypes, treated as a genuine structural feature of the literature, not a search-execution failure.

**Theme D — Where independent literature tests the standard's fixed multi-class factors, it confirms the *central tendency* roughly but rejects the *precision*.** Vandenbogaerde et al. (heating emission control: 19–71% simulated range vs. the standard's single number per class) and Albesiano (2023) (cooling, Education) both take ISO 52120's classification scheme as their organizing structure and then independently simulate/measure outcomes — this is validation methodology, not restatement. The consistent finding: the standard's 4-class step function compresses a much wider real/simulated range into one point estimate per class. This argues for treating factors as point estimates within an uncertain band, not as precise predictions (§6A).

**Theme E — The four ISO-uncovered domains (DE, Electricity, EV, MC) do not share a uniform evidentiary signature.** MC is evidentially rich but structurally non-additive, while DE/Electricity/EV are evidentially thin but structurally straightforward. DE, Electricity, and EV are each genuinely thin domains anchored by a single high-quality source (DE: Lee et al. 2025/2005; Electricity: Weniger et al. 2020; EV: Seger 2025/Tucker 2022). MC does not fit this description: it has *three* independent high-confidence field sources across three subtypes (LBNL portfolio study, Mills & Mathew, Im et al.). MC's problem is not "not enough data," it is "the data unambiguously shows the effect isn't separable." Conflating these two failure modes would lead to the wrong fix — MC doesn't need more studies, it needs a different modeling architecture (§4.2.3, §6D); DE/Electricity/EV need more studies.

**Theme F — Market/context transferability is a live variable for demand-side domains but largely absent from the thermal domains' framing.** The Electricity domain's Norway study explicitly notes that spot-price volatility alone is "not big enough to make arbitrage profitable" in a flat-tariff EU market — value requires stacking multiple revenue streams. EV Charging shows the same market-structure dependency: US demand-charge evidence (Tucker/SLAC, Golden Arrow bus depot) measures value against a billing structure that doesn't exist in most EU markets. This caveat barely appears in Heating/Cooling/DHW/Ventilation/Lighting, where EU field data (Belgium, Norway, Spain, Italy) is comparatively well represented — but it compounds the geographic-skew problem for MC (9/12 US sources, zero EU institutional quantitative evidence) and for large parts of DE and Electricity. This transferability risk sits on top of, and is separate from, ordinary evidence-quality concerns.

### 4.2 Contradiction Resolutions

**4.2.1 — DHW's building-type-invariant factor vs. literature showing type-dependent relevance.** ISO 52120 Tables A.7/A.8 give one `f_BAC,DHW` table identical across *every* building type — the only end-use in the standard with no per-type variation at all. **[DA Checkpoint 2, M3 correction preserved]:** the measured rates actually **straddle the standard's implied rate on both sides, by comparable margins** — Educational (CARD/CEE 11.4%) sits at roughly *half* the standard's ~20–28% implied C→A/D→A range, while Healthcare (Vincenti 48.6% thermal) sits at roughly *double* it. These are rate discrepancies, on the same %-of-DHW-end-use basis the standard itself uses, and they cut in opposite directions — not materiality points. Bonomolo's 27.93% (Italy) is **not** usable as a third data point here at all — see the corrected note in §3.2, where it turns out to numerically match the standard's own D→A calculation almost exactly, raising a circularity concern rather than providing independent confirmation. **Verdict:** the standard's rate is not safely type-invariant even setting materiality aside. Combined with the separate, better-supported materiality issue (DHW's *share* of total building energy varies by roughly an order of magnitude across subtypes — negligible in offices, ~15% of hospital thermal load), the recommendation is that a type-specific weighting layer is needed, but as an open question requiring more evidence (one credible source per subtype in most cases), not a confirmed correction. Positive finding unaffected by this correction: Vincenti's healthcare study detected zero Legionella incidents under demand-based DHW control, removing a plausible safety-override objection specifically for healthcare/hospitality DHW.

**4.2.2 — Field-measured vs. simulated/vendor divergence: how to state a "central estimate."** Given Theme A, a naive pooled mean across study types is not a legitimate central estimate — it silently encodes the inflation. The defensible approach used throughout §3 above: (1) anchor on field-measured, whole-building, long-duration studies wherever ≥1 exists for a cell; (2) treat simulated/short-duration/zone-level figures as an explicit upper bound, never averaged into the field number; (3) exclude vendor-authored sources from central-estimate calculation entirely, using them only as a plausibility ceiling; (4) where no field study exists at all, report the simulated figure explicitly labeled "unvalidated upper bound, no field corroboration" rather than presenting it as a point estimate. Khabbazi's own multipliers (27%→13% zone-vs-whole; 57%→22% short-vs-long) imply roughly a 2–2.6× gap between worst-case-aggregation estimates and defensible whole-building/long-duration ones — this ratio is directly measured only for Heating and should be used as a plausibility check on other domains, not applied as a cross-domain rescaling formula.

**4.2.3 — Monitoring & Control: same underlying problem, or two different ones?** **[DA Checkpoint 2, M4 correction preserved]:** an earlier draft of this synthesis framed JRC's 2018–2020 methodological judgment and the field decomposition literature as independent discoveries "roughly 2–7 years apart" — that timeline was wrong (Mills & Mathew's decomposition study is dated 2009, nearly a decade *before* JRC's methodology was developed) and the "temporally-separated independent convergence" framing has been dropped. The corrected verdict: the JRC's founding methodology (top-down, ~2018–2020) could not construct an energy balance for MC when the SRI scoring system was designed — a definitional/theoretical judgment, which is why MC got a fixed 20%-of-score weight instead of an energy-derived one. Separately, and on its own empirical merits, the field decomposition literature (Im et al. 2021; Mills & Mathew 2009, predating JRC) shows *why* no clean energy balance exists: MC is not an end-use with its own physics — it is a meta-control layer whose entire measurable effect is mediated through the end-uses it corrects. **Implication: MC should not be modeled as an independent, additive energy-savings domain.** Two architecturally sound alternatives: (a) model MC as a precondition/multiplier on the realizable fraction of the separately-modeled HVAC/lighting factor-based savings; or (b) keep MC as cost-only with energy-savings attribution suppressed to zero. Adding a third, independent MC savings channel on top of separately-computed HVAC/lighting savings reproduces the exact double-counting the evidence warns against.

**4.2.4 — EV Charging's structurally different metric.** Not a category error to include, but a category error to force into the same "% energy saved" column as the other 8 domains. EV charging is an additive load whose *shape*, not magnitude, is what management optimizes. Several headline figures (NREL's +250% site peak demand, Gilleran et al. 2021; Australian hospitality peak-demand burden) are **burden, not savings**, describing *uncontrolled* charging — they do not contradict the mitigation figures (Seger 2025, Golden Arrow 2025), which describe *controlled* charging on the same underlying load; conflating the two risks a sign error. The tradeoff evidence (Gschwendtner 2023; V2G's 9–14%/10yr degradation penalty) is consistent with — though it does not directly prove — the reasoning behind the SRI methodology's choice to give EV Charging a fixed rather than energy-balance-derived weight (§0). [Phase 6 revision: softened from the Phase 4 draft's "corroborates the SRI methodology's own qualitative skepticism about EV/V2G scoring," which overstated what the SRI methodology actually documents — a modelling-necessity choice (no computable energy balance), not a stated skepticism toward V2G specifically.]

**Cross-paper tension inventory (scoped, advisory — not exhaustive):** 8 candidate tension pairs were scanned across the corpus (CP-001 through CP-008 in the Phase 3 source), covering DHW type-invariance, Heating field-vs-simulated magnitude, Heating BAC-class circularity, MC's "no energy balance" vs. field decomposition, DHW rate validation, EV burden-vs-mitigation, DE field-vs-vendor magnitude, and MC's simulated-separable-vs-field-non-separable modeling question. All 8 are resolved or explicitly flagged unresolved in the discussion above (details in the Phase 3 source document); this was a recall-limited scan of the compiled evidence table, not exhaustive pairwise contradiction detection, and other cross-domain tensions may exist unflagged (e.g., possible tension between Ventilation's code-constrained-minimum findings in Healthcare/Hospitality and Cooling's OR-level findings in the same subtypes).

### 4.3 Circularity Assessment

- **Verbeke et al. (2020) [JRC] / Waide/eu.bac (2019) — confirmed circular.** [Phase 6 revision: disambiguated per the Phase 5 ethics review — "JRC (2020)" below refers to the same Verbeke, S., et al. (2020) final SRI technical support study cited in §0 and §8, not a separate document.] Both derive Heating/Cooling/DHW/Ventilation/Lighting savings entirely via EN15232 factors. Any downstream use of these as "corroboration" of the standard is circular by construction — they restate the standard's own numbers.
- **Vandenbogaerde et al. — confirmed independent, despite structural resemblance to the standard.** Uses the standard's classification scheme as an *organizing structure* but the energy values come from independent building-specific numerical simulation, not from restating EN15232's tables. Using a standard's taxonomy to structure a test of that standard is not circularity; deriving the numbers from the standard's own tables is.
- **Albesiano (2023) — confirmed independent, with a different caveat.** Not circular (fills a gap the standard admits it doesn't cover), but a single academic thesis (Politecnico di Torino), not peer-reviewed — a quality-tier risk, distinct from circularity, that matters because it is the *sole* source filling the Cooling-Education gap.
- **Verbeke et al. (2020) [JRC]'s own 19-study self-consumption review — confirmed independent.** Table 13 of the same 2020 JRC report (§0). EN15232 has no self-consumption/storage/DSM coverage at all, so this review cannot be circular by construction — it is JRC surveying genuinely external literature, distinct from the same report's EN15232-derived Heating/Cooling/DHW/Ventilation/Lighting figures.

**Additional circularity-adjacent risk (source concentration, not circularity):**
- DHW's Offices, Educational, and Hospitality rows lean substantially on the **same single program** (CARD/CEE 2018, Minnesota) — three "covered" subtypes are, in reality, one research program's three sub-results.
- MC's Retail, Industrial/warehouse, and Other public rows all derive from **one paper** (PNNL-25985), simulated not field-measured — compounding concentration risk with a study-type weakness.
- Cooling's Other public row rests on two papers from the **same TU Eindhoven author group** (Kompatscher 2017, 2019) — nominally "2 sources" but not fully independent replication.
- Healthcare MC's apparent strength (Im et al. 2021, three hospitals) is internally replicated within **one publication**, not three independent studies. This is a distinct concentration caveat from the non-additivity caveat the grid's asterisk (§5.2) actually marks — it is recorded here, not in the grid, so a reader following a pointer to "the asterisk" for this specific concern will not find it there; treat this bullet as the authoritative note.
- **[Added at Phase 6 revision, editorial finding]** The Cooling/Healthcare "three independent Spain field/sim studies" cited in §6A (Tejero-González 2022, Castellanos-Antolín 2022, Dulce-Chamorro 2021) are three separate publications, not one, and so are not a case of the same single-publication concentration risk as the bullets above — but §3.3's own table row describes them as "**3 related** Spanish hospital studies," and that "related" framing (plausibly overlapping author networks / institutional context, not independently confirmed as fully separate research groups) is a softer version of the same concentration concern. §6A's "confidence now" framing for this cell should be read as resting on three related-but-formally-separate Spanish studies, not three studies with no connection to one another.
- Similarly, the Dynamic Envelope/Offices "field-anchored" rating (§3.6, §6A) rests on Lee, E. S. et al. (2005) and Lee, E. S. et al. (2025) — the same lead researcher, twenty years apart, not two independent research groups. This is at least as strong a concentration signal as Kompatscher's museum/archive pairing above and should be weighed the same way when using the DE/Offices cell for calibration.

None of these are circularity in the EN15232-derivation sense, but a calibration engineer treating "3 subtype rows," "3 hospitals," "3 related studies," or "2 field studies" as fully independent confirmations would overstate corroboration breadth. Flag this explicitly wherever cell counts are used as a confidence signal downstream.

---
## 5. Coverage Gaps & Caveats

### 5.1 Taxonomy caveat

The 8 research subtypes used throughout this report (Offices, Educational, Healthcare, Retail/wholesale, Hospitality, Sports/leisure, Industrial/warehouse, Other public) do **not** map 1:1 onto ISO 52120 Annex A's 8 categories (Offices, Lecture hall, Education, Hospital, Hotels, Restaurants, Wholesale/retail, **Other types**). Critically, ISO 52120 collapses Sports/leisure, Industrial/warehouse, and (implicitly) most of "Other public" into a single **"Other types"** bucket with **no D/B/A factors at all** — the standard cannot quantify a BAC upgrade for any of them (`ISO_52120_BAC_FACTORS.md` §5.1), and this is directly relevant because the optimiser's example building is a sports centre in this exact bucket. So even where the grid below shows three "separate" thin cells for Sports/leisure, Industrial/warehouse, and Other public, from the standard's perspective they are one bucket — and pooling all three subtypes' literature together for that single ISO category *still* leaves it the worst-covered building type in the corpus.

### 5.2 The 9×8 Gap-Analysis Grid

**Legend:** Strong (2+ independent, credible sources) / Moderate (2+ sources but lower confidence or geo mismatch, or single-but-exceptional) / Thin (1 source, or low confidence) / Gap-literature-thin (plausibly fillable by future search) / Gap-structural (structural/definitional, or confirmed-absent after exhausted search).

| Domain | Offices | Educational | Healthcare | Retail | Hospitality | Sports/leisure | Industrial | Other public |
|---|---|---|---|---|---|---|---|---|
| Heating | Strong | Gap-thin | Gap-structural (Cochrane-confirmed) | Thin | Thin | Moderate (review-tier) | Gap-structural (excluded end-use) | Thin |
| DHW | Strong | Thin | Strong | Gap-thin | Moderate | Gap-structural (conflated w/ pool heating) | Gap-structural (self-consistent w/ ISO gap) | Gap-thin |
| Cooling | Strong | Thin (single, high-value — fills ISO's own gap) | Strong | Moderate | Thin | Thin | Thin (scope mismatch: refrigeration ≠ ambient) | Thin |
| Ventilation | Strong | Strong | Thin | Moderate | Moderate | Moderate | Gap-structural (plausible but unsourced inference) | Thin |
| Lighting | Strong | Strong | Thin | Thin | Gap-structural (vendor-only) | Gap-structural (vendor-only) | Gap-thin (unretrieved PDF) | Gap-thin (off-target hit) |
| Dynamic Envelope | Strong (field-anchored) | Thin | Thin | Gap-structural (confirmed zero) | Gap-structural (unreliable single source) | Gap-structural (confirmed, scope-excluded) | Gap-structural (confirmed zero) | Gap-structural (confirmed zero) |
| Electricity | Moderate | Thin | Thin | Gap-thin (leads only) | Thin | Moderate (single but best-in-corpus: Weniger 2020) | Thin (unverified) | Thin (unverified) |
| EV Charging | Strong | Thin | Gap-structural (vendor-only) | Thin (burden only) | Thin (burden only) | Gap-structural (inaccessible) | Thin | Gap-structural |
| MC | Strong* | Strong* | Strong* | Thin | Thin | Gap-structural (vendor-adjacent only) | Thin | Thin |

\* MC "Strong" cells carry the non-additivity caveat from §4.2.3 — evidentially strong, structurally non-independent.

**Reading the grid by subtype (count of Strong cells out of 9 domains):** Offices 8/9 (all domains Strong except Electricity, which is Moderate); Educational 3/9 (Ventilation, Lighting, MC); Healthcare 3/9 (DHW, Cooling, MC — **not** Heating, which is Gap-structural for Healthcare); Retail 0/9; Hospitality 0/9; Sports/leisure 0–1/9 (Electricity is single-source-strong at best via Weniger 2020); Industrial/warehouse 0/9; Other public 0/9. **Five of eight subtypes have zero domains with strong, independent corroboration** (Retail, Hospitality, Industrial/warehouse, Other public, plus Sports/leisure — which reaches at most one single-source-strong cell, via Weniger 2020 in Electricity, so it rounds to the same "effectively zero" conclusion as the other four even though it isn't a clean zero) — and the project's actual example building subtype (sports/"Other types") is among them.

### 5.3 Structural vs. Literature-Thin vs. Hard Gaps

**Structural/definitional gaps (will not be closed by more literature search):**
- MC's non-separability from HVAC/lighting, all subtypes (§4.2.3) — an attribution property of the intervention, not an evidence deficit.
- ISO 52120's "Other types" bucket (sport/storage/industrial) has no D/B/A factors by design — independent literature here isn't corroborating the standard, it is the *only* possible source of a factor at all.
- DHW's flat, type-invariant rate table (§4.2.1) — a standard design choice; the fix is a weighting layer, not a literature search.
- DE Sports/leisure "confirmed near-zero" — the available literature (static shading-ratio optimization) is explicitly scope-excluded as not-automated-control, a taxonomic mismatch rather than an absence of research.
- Ventilation/DHW's bundling of fan/pump electricity into `f_BAC,el` jointly with lighting — a pure "ventilation-only" or "DHW-pump-only" factor is definitionally blurred in the standard itself.
- Healthcare/Hospitality Ventilation and Cooling OR-specific findings — savings ceilings are code/safety-constrained (unoccupied-hours-only), not measurement-limited.
- EV Charging's "% energy saved" mismatch (§4.2.4) — a units problem, not a data problem.

**Literature-thin gaps (plausibly fillable by future/deeper search — specific named leads exist):**
- Heating Educational — a Danish MPC school case (IEA Annex 81) exists but attribution is ambiguous; deeper mining could resolve it.
- Dynamic Envelope — IEA ECBCS Annex 44 and COST Action TU1403 are named EU research programs, not yet mined for extractable figures.
- Electricity — a Greek net-billing study, Italy logistics-warehouse figures, and an EU-Mediterranean multi-country Applied Energy paper are all named, specific, paywalled/unverified leads.
- Lighting Industrial/warehouse — a PNNL/DLC field report was identified but not retrieved.
- MC — O'Grady et al. (2021, *Building and Environment*, BAS meta-analysis) and IEA EBC Annex 81 are named but not fully chased.

**Genuine hard gaps (real absence, confirmed by exhausted search or independent systematic review):**
- Heating Healthcare — a Cochrane systematic-review *protocol* (2024) itself confirms evidence scarcity; stronger than "we didn't find it," it is "a review body has looked and found nothing yet."
- Heating Industrial/warehouse — deliberately excluded (cold-storage refrigeration is a different end-use), not unsearched.
- DE Retail/wholesale, Industrial/warehouse, Other public — confirmed zero after repeated query variations.
- Lighting Hospitality, Sports/leisure — vendor-only, independent literature confirmed absent.

---
## 6. Implications for Optimiser Calibration

**A — Use ISO52120-derived factors with confidence now (corroborated, not merely asserted):**
- Heating, Cooling, Ventilation, Lighting for **Offices**: the best-evidenced cells in the corpus, broadly consistent in direction and rough magnitude with independent field literature.
- Cooling for **Healthcare** (three independent Spain field/sim studies) and Ventilation/Lighting for **Educational** (independent EU field base — Belgium, Norway).
- These should still be treated as **point estimates within an uncertain band, not exact predictions** — Vandenbogaerde's demonstrated 19–71% real range against the standard's single per-class number is the direct evidence basis for attaching an uncertainty band (a first-pass ±30–50% around the point estimate is a defensible, evidence-grounded starting point) if the optimiser's cost/CO2/energy model supports sensitivity analysis.
- **Critical caveat for the optimiser's per-step decision variables [DA Checkpoint 2, M1].** The optimiser tracks upgrades as discrete `(from_level, to_level)` transitions, but almost every savings figure in the evidence base is an endpoint comparison (roughly D-vs-A). **Albesiano (2023) (Cooling, Education) is the only source in the entire corpus with genuine per-class stepwise data.** The ISO 52120 class steps are demonstrably **non-linear and front-loaded**: for Offices thermal (Table A.1, D=1.51/C=1.00/B=0.80/A=0.70), the D→C step alone accounts for ~63% of the total D→A savings, C→B for ~25%, and B→A for only ~12%. A calibration engineer must **not** linearly interpolate an endpoint (D-vs-A) field figure evenly across the three intermediate class transitions — doing so would silently reintroduce the endpoint-only category error the Phase 1 Devil's Advocate checkpoint flagged as Critical. Any per-step value derived from an endpoint figure must be explicitly labeled as an unvalidated linear-interpolation assumption, and the standard's own (non-linear) per-class factor ratios should be used to apportion an endpoint saving across steps where a domain has no independent stepwise evidence, rather than splitting it evenly.

**B — Adjust, don't take at face value:**
- **DHW**: **[Phase 6 revision, editorial finding]** the original draft of this bullet only carried forward the materiality half of §4.2.1's finding. The full picture: do not apply flat whole-building materiality across offices vs. healthcare/hospitality, **and** treat the standard's rate itself as an open question, not a settled value — independent evidence diverges from the standard's implied ~20–28% rate by roughly 2× in both directions (Educational ~half, Healthcare ~double), on one credible source per subtype. Use the standard's rate as a starting point, but do not treat it as validated for Educational or Healthcare specifically until more evidence accumulates.
- **Cooling, Education**: Albesiano's factor is usable as a provisional value to fill the standard's own documented gap, but flag it single-source/thesis-tier pending corroboration, not full confidence.
- **Dynamic Envelope, Offices**: the standard doesn't cover this domain at all, and the code currently assigns it zero saving by default. Now that a genuine field anchor exists (Lee et al., ~10–20% HVAC/lighting from automated shading), this specific cell can be upgraded from "no data" to a modest, field-anchored, non-zero estimate — explicitly excluding both the vendor source's 48–53% figure and the separate, non-vendor lab-conditions upper bound of 60–76% (see §3.6; the two are distinct sources and neither belongs in a central estimate).

**C — Currently uncalibratable — be honest, don't paper over with a number:**
- **Dynamic Envelope** for Retail, Industrial/warehouse, Other public, Sports/leisure — confirmed hard/structural gaps. Do not extrapolate the Offices field figure into these subtypes; the building physics doesn't transfer, and doing so would manufacture false precision.
- **The sports-centre example building itself** — its ISO `iso_building_type` bucket ("Other types") is, across almost every domain, the single worst-covered subtype in the entire corpus (0/9 strong cells even pooling Sports/leisure + Industrial/warehouse + Other public research subtypes together). The optimiser's running example should be understood as a structural/architectural demonstration of the multi-objective mechanics, not an evidence-calibrated result, until the flagged-but-unchased leads (IEA Annex 81/44/67, COST TU1403, O'Grady et al. 2021) are pursued.
- **Electricity** for every subtype except Offices (moderate) and Sports/leisure (Weniger 2020, single-but-excellent) — remains thin; usable as a directional planning input, not a precise savings %, with the added caveat that most of the underlying evidence is either residential-proxy or US-tariff-context and may not transfer to EU flat-tariff markets.
- **MC** for all subtypes — not a "need more data" situation (see D).

**D — The MC double-counting risk (explicit flag).** The current design already does the right thing: `ISO_52120_BAC_FACTORS.md` §6 confirms MC is "folded into class determination, not a separate end-use" — i.e., the code does not currently give MC its own additive savings line. **This must be preserved, not "improved" by adding an independent MC savings channel**, however tempting that is given MC's genuinely good evidence base and typically low retrofit cost. The evidence (Im et al. 2021: 100% of hospital MC savings attributable to HVAC control-point fixes; Mills & Mathew: 65% of educational MC savings attributable to HVAC-fault fixes) shows that if a future version of the cost/CO2/energy-savings model computes MC savings *and* separately computes Heating/Cooling/Ventilation/Lighting factor-based savings for the same building, and sums them, the total will overstate real savings by roughly the HVAC/lighting-attributable share of the MC figure — which the evidence says is close to 100%. If MC cost-effectiveness needs to be surfaced (it has real license/hardware/labor costs worth modeling), the two architecturally sound options are: (i) a precondition/multiplier on the realizable fraction of HVAC/lighting factor-savings, or (ii) a cost-only line item with energy-savings attribution suppressed to zero, matching current behavior.

**E — EV Charging architecture recommendation.** Current behavior (no energy-saving contribution, per the ISO-gap list) is reasonable given the §4.2.4 category-error finding, but if EV Charging is to enter the optimiser's decision space at all, it should be represented as a **separate objective dimension (peak-demand or cost-shift), not folded into the kWh energy-savings objective** — a single-objective energy formulation would render Seger (2025)'s documented tradeoff (cost-minimizing strategy achieves −19% cost but +4.9% peak) invisible to the optimiser entirely.

**F — Geographic/tariff transferability caveat.** MC (9/12 sources US, zero EU institutional quantitative evidence) and large parts of DE/Electricity/EV rest on US market structure or non-EU geography. Where EU field studies exist (Belgium/Norway ventilation, Spain healthcare cooling, Italy/EU DHW and cooling), those numbers are directly usable for an EU SRI tool; where only US or non-EU evidence exists, treat the transferred figure as a plausibility check against the optimiser's output, not a validated EU calibration input.

**G — Occupant-behavior discount, separate from the uncertainty band [added at Phase 6 revision — flagged by the Phase 4 draft's own §7 limitation note (DA Checkpoint 2, m3) but never actually carried into this section, per the Phase 5 editorial review].** A nominal functionality-level upgrade's factor-based savings assume the control operates as designed. Independent evidence shows occupants actively undermine this in practice, not just that measurement methodology overstates it (a distinct risk from Theme A/§4.2.2's field-vs-simulated inflation gradient): occupancy-sensor rebound reduces realized lighting savings by making occupants roughly half as likely to manually switch off lights once a sensor is present (Pigg 1996); photocontrol miscalibration and false-offs drive occupant dissatisfaction and workarounds (Bordass 1994); and in one healthcare field study, manual control **outperformed** the automated system entirely (Safranek et al. 2021, NICU, small sample). Treat this as a standing, direction-consistent (downward) discount to consider applying separately from the ±30–50% uncertainty band in §6A — the band captures measurement/methodology uncertainty around a point estimate, not the risk that a correctly-measured nominal saving under-delivers once real occupants interact with it. This is most relevant for Lighting and any domain with an occupant-facing override interface (thermostats, blind controls); it is not evidenced (positively or negatively) for domains without direct occupant interaction, such as MC or centralized plant-level Cooling/Heating generation control.

---

## 7. Limitations

**Inherited from the Phase 3 synthesis:**
- Built from the Phase 2 compiled master table only; primary sources were not re-verified and searches were not re-run for this compilation step, so confidence ratings and source-count assessments inherit whatever the originating Phase 2 agents established.
- Low-confidence and vendor-flagged sources were retained in the gap-analysis grid (marked accordingly) for coverage-mapping completeness rather than excluded outright — exclusion happens at the point of use (§6), not at the point of mapping.
- The 8-subtype research taxonomy and ISO 52120's 8-category taxonomy are not isomorphic (§5.1); this report preserves, rather than silently resolves, that mismatch.
- "Count of strong cells per subtype" figures in §5.2 are a synthesis judgment call against a stated 2+-independent-source threshold, not a figure reported by any single Phase 2 source — label as such if reused.
- **[DA Checkpoint 2, m2]** The field-over-simulated discipline (§4.2.2) is derived almost entirely from one domain's mechanistic account (Khabbazi et al. 2025, Heating) and is not applied with full consistency where it would bite hardest: Cooling's two best EU sources (Vandenbogaerde, Albesiano) are simulated, not field, yet §6A/§6B still promote them to "use with confidence"/"usable as provisional value" rather than strict ceiling-only status. The hedging language partially mitigates this, but the inconsistency should be read as a real tension in applying the field-over-simulated rule uniformly, not a fully resolved rule.
- **[DA Checkpoint 2, m3]** Occupant-behavior counter-evidence (Lighting: Pigg 1996 occupancy-sensor rebound; Bordass 1994 photocontrol miscalibration; Healthcare: Safranek 2021 — manual control outperformed automated control in a NICU field study) is a distinct risk category from Theme A's measurement-methodology inflation gradient: it concerns occupants actively undermining a nominal automated-control saving in practice, not researchers over-measuring it. This bears directly on whether a functionality-level upgrade delivers its nominal factor once installed, and should be treated as a standing calibration caveat — a plausible downward adjustment separate from the uncertainty band in §6A — rather than left as background material with no calibration implication.

**Specific to this compilation step (Phase 4):**
- **Sourcing method**: Phase 2's 10 research agents worked from live web search and did not have independent human verification of every citation before this report was compiled. Several sources in §3 and §8 are explicitly flagged "citation unverified," "search-snippet only," or with incomplete bibliographic detail (missing full author names, exact title, journal/publisher, or year) — these flags are preserved rather than resolved, and should be treated as a prompt to re-verify before this report's figures are cited externally or relied on for a decision with material cost consequences.
- **No independent recalculation**: this report does not re-run any of the cited studies' underlying data or models; all figures are as reported by the Phase 2 agents from the original sources (or from search snippets/abstracts where the full text was not accessible — flagged per-row where known).
- **Coverage is not exhaustive**: the cross-paper tension inventory (§4.2) is explicitly scoped and advisory, not a complete pairwise contradiction analysis; the gap grid (§5.2) reflects what 3+ query variations per domain×subtype cell surfaced, not a guarantee that no literature exists.

**AI Disclosure:** This report was produced with AI-assisted research tools. The research pipeline included AI-powered literature search, source identification, evidence compilation (Phase 2), evidence synthesis and contradiction resolution (Phase 3, including an adversarial Devil's Advocate review checkpoint that produced material corrections — see the "[DA Checkpoint 2, ...]" tags throughout this report), and report drafting (Phase 4, this document). Findings were checked for internal consistency against the source compilation but were **not** independently re-verified against original primary sources by a human researcher for every citation. Readers relying on this report for calibration decisions with material cost or safety consequences should independently verify any specific figure before use, particularly those flagged "citation unverified," "L" confidence, "vendor-sponsored," or with incomplete bibliographic detail in §8.

---
## 8. References

Compiled from all citations used across §0 (JRC prior-art) and §§3.1–3.9 (the 9 domain sections) of the Phase 2 master evidence table. APA 7th-edition format is used where sufficient bibliographic detail was captured in the Phase 2 compilation to do so.

**Note on incomplete citations.** The Phase 2 research agents worked from live web search and frequently captured only a surname and year (sometimes only a year, or only a journal/organization name) rather than a full author list, article title, venue, and identifier. Per this report's no-fabrication instruction, such entries are **not** completed from outside knowledge — each is marked **[INCOMPLETE]** and reproduces exactly what the source material provided. Do not cite these externally without first re-verifying the full reference. Entries with a DOI, arXiv ID, or report number are reproduced with that identifier as the link.

Albesiano, N. (2023). *[Title not captured in Phase 2 compilation]* [Thesis, Politecnico di Torino]. **[INCOMPLETE]**

Becchio, C., et al. (2017). *[Title not captured in Phase 2 compilation]*. **[INCOMPLETE]**

Bonomolo, M., et al. (2021). *[Title not captured in Phase 2 compilation]*. Italy. **[INCOMPLETE]**

Bordass, B. (1994). *[Title not captured in Phase 2 compilation — photocontrol miscalibration/false-offs finding]*. **[INCOMPLETE]**

BPIE (Buildings Performance Institute Europe). (2017). *Is Europe ready for the smart buildings revolution? Mapping smart-readiness and innovative case studies*. **[INCOMPLETE — exact title/URL not verified in Phase 2 compilation]**

Brandemuehl, M. J. (1999). *[Title not captured in Phase 2 compilation — DCV/ventilation, retail and hospitality]*. **[INCOMPLETE]**

Castellanos-Antolín, A., et al. (2022). *[Title not captured in Phase 2 compilation — Spain hospital HVAC OR-specific study]*. **[INCOMPLETE]**

Center for Energy and Environment / Conservation Applied Research and Development (CARD/CEE). (2018). *[DHW multi-site field study, Minnesota — exact report title not captured in Phase 2 compilation]*. **[INCOMPLETE]**

Chen, Y., & Yin, S. (2022). *[Title not captured in Phase 2 compilation — LBNL adaptive cooling setpoint simulation, all US climate zones]*. **[INCOMPLETE]**

CIBSE Journal. (n.d.). *[AI load-forecasting cooling article — exact title, author, and year not captured in Phase 2 compilation]*. **[INCOMPLETE]**

Clark University commissioning case study. (n.d.). *[Cited in Mills & Mathew 2009 context — not independently verified as a separate source]*. **[INCOMPLETE]**

Cochrane Collaboration. (2024). *[Systematic review protocol confirming evidence scarcity for healthcare heating BAC savings — exact title/authors not captured in Phase 2 compilation]*. **[INCOMPLETE]**

Delvaeye, R., et al. (2016). *[Title not captured in Phase 2 compilation — Belgium daylight-control field study, KU Leuven]*. **[INCOMPLETE]**

Dikel, E. E., et al. (2018). *[Title not captured in Phase 2 compilation — cited within the LBNL lighting-controls meta-analysis cluster]*. **[INCOMPLETE]**

Donnini, G. (1991–1992). *[Title not captured in Phase 2 compilation — Montreal ventilation field study]*. **[INCOMPLETE]**

Dulce-Chamorro, C., et al. (2021). *[Title not captured in Phase 2 compilation — Spain hospital chiller-plant ANN optimization]*. **[INCOMPLETE]**

*Energies* [journal]. (2017). *[Article title and authors not captured in Phase 2 compilation — DE electricity self-consumption case bundled with thermal storage]*. **[INCOMPLETE]**

Fisk, W. J. (2010). *[Title not captured in Phase 2 compilation — LBNL ventilation baseline-sensitivity study]*. **[INCOMPLETE]**

Frontiers in Energy Research [journal]. (2025). *[Article title and authors not captured in Phase 2 compilation — multi-building-type electricity storage simulation, Los Angeles]*. **[INCOMPLETE]**

Gabel, S. (1986). *[Title not captured in Phase 2 compilation — ventilation]*. **[INCOMPLETE]**

Galasiu, A. D. (2007). *[Title not captured in Phase 2 compilation — daylighting savings]*. **[INCOMPLETE]**

Gilleran, M., et al. (2021). *[Title not captured in Phase 2 compilation — EV fast-charging peak-demand burden modelling]* [Report]. National Renewable Energy Laboratory (NREL). **[INCOMPLETE — report number not captured]**

Goldschmidt, R. (2026). *[Title not captured in Phase 2 compilation — Germany stepwise heating-control field study]*. **[INCOMPLETE — flagged at Phase 6 revision (DA Checkpoint 3, M2): this is a field study dated the same calendar year as this report; the Phase 4 draft applied a current-year caveat to the neighboring Vandenbogaerde (2026) simulated source but not to this one, despite a field study being the more surprising same-year case. Given this citation anchors the single "H"-confidence Offices/Heating cell that §6A calls out as usable "with confidence," verify this source before relying on the cell; note it is independently corroborated in direction by Szydlowski (1993), so §6A's conclusion for this cell does not depend on Goldschmidt alone.]**

Golden Arrow Bus Services electrification study. (2025). *[Title, authors not captured in Phase 2 compilation — bus depot EV charge scheduling, South Africa]*. **[INCOMPLETE]**

Gschwendtner, C. (2023). *[Title not captured in Phase 2 compilation — Zurich EV charging tradeoff study]*. **[INCOMPLETE]**

Gupta, R., et al. (2017). *[Title not captured in Phase 2 compilation — UK library heating/FM staff-turnover qualitative study]*. **[INCOMPLETE]**

Haghighat, F. (n.d.). *[Title and year not captured in Phase 2 compilation — ventilation]*. **[INCOMPLETE]**

Henze, G. P., Kircher, K. J., & Braun, J. E. (2024). *[Title not captured in Phase 2 compilation — methodological problem of MC/HVAC savings double-counting]*. arXiv. https://arxiv.org/abs/2411.06204

Heschong Mahone Group. (1999/2003). *[Title not captured in Phase 2 compilation — retail daylighting/lighting-control field white paper]*. Utility-funded. **[INCOMPLETE — two possible years given in Phase 2 source]**

Hong Kong University of Science and Technology (HKUST). (2018). *[Title, authors not captured in Phase 2 compilation — 4-year field chiller-electricity study, 3 office towers]*. **[INCOMPLETE]**

ICE-E project. (n.d.). *[EU IEE-funded industrial refrigeration field survey, 329 facilities — exact title/year not captured in Phase 2 compilation]*. **[INCOMPLETE]**

Im, P., et al. (2021). *[Title not captured in Phase 2 compilation — continuous commissioning decomposition, 3 US hospitals]*. **[INCOMPLETE]**

International Energy Agency (IEA), Energy in Buildings and Communities Programme. *Annex 81: Data-Driven Smart Buildings*. **[INCOMPLETE — lead identified but not fully chased in Phase 2/3; no report retrieved]**

International Energy Agency (IEA), Energy in Buildings and Communities Programme. *Annex 67: Energy Flexible Buildings*. **[INCOMPLETE — lead identified but not fully chased]**

International Energy Agency (IEA), Energy Conservation in Buildings and Community Systems Programme. *Annex 44: Integrating Environmentally Responsive Elements in Buildings*. **[INCOMPLETE — lead identified but not mined for extractable figures]**

International Energy Agency (IEA) & International Renewable Energy Agency (IRENA). (n.d.). *[System-level V1G/V2G national peak-load reduction projections, France/Germany/Belgium 2030–2040]*. **[INCOMPLETE — cited jointly in Phase 2 source; exact report(s), authors, and year not captured]**

International Energy Agency (IEA) Solar Heating and Cooling Programme, Task 50. *Advanced Lighting Solutions for Retrofitting Buildings*. 10-country program. **[INCOMPLETE — exact publication/year not captured in Phase 2 compilation]**

Kanellos, F. D. (2022). *[Title not captured in Phase 2 compilation — EV charging campus peak-load burden, Greece]*. **[INCOMPLETE]**

Khabbazi, A., et al. (2025). *[Title not captured in Phase 2 compilation — systematic review, 80 papers/154 commercial-building HVAC field tests, establishing the field/zone/duration/benchmark-type savings-inflation mechanism]*. **[INCOMPLETE — added at Phase 6 revision; this citation was entirely absent from the Phase 4 draft despite anchoring §3.1's cross-cutting Heating framing, Theme A (§4.1, the report's central cross-domain finding), the central-estimate methodology in §4.2.2 (including the quantitative 27%→13%/57%→22% multipliers), and the limitation note at §7. Given its outsized role, verify this source before relying on Theme A or the 2–2.6× discount-ratio guidance in §4.2.2.]**

Knoespel, [initials not captured], & Emmerich, [initials not captured]. (n.d.). *[Title and year not captured in Phase 2 compilation — ventilation]*. **[INCOMPLETE]**

Kompatscher, K., et al. (2017). *[Title not captured in Phase 2 compilation — museum/archive climate-control field+sim study]*. TU Eindhoven, Netherlands. **[INCOMPLETE]**

Kompatscher, K., et al. (2019). *[Title not captured in Phase 2 compilation — companion/follow-up study to the 2017 source above]*. TU Eindhoven, Netherlands. **[INCOMPLETE]**

Kulmala, I. (1984). *[Title not captured in Phase 2 compilation — Finland ventilation field study]*. **[INCOMPLETE]**

Lawrence Berkeley National Laboratory (LBNL). *Commissioning (Cx) database*. **[INCOMPLETE — database, not a single publication; segment-level figures cited per row in §3]**

Lawrence Berkeley National Laboratory (LBNL) FlexLab. (n.d.). *[Higher-education automated-shading demonstration, perimeter lighting]*. **[INCOMPLETE]**

Lee, E. S., et al. (2005). *[Title not captured in Phase 2 compilation — Berkeley 20-month field study, automated shading]*. Lawrence Berkeley National Laboratory. **[INCOMPLETE]**

Lee, E. S., et al. (2025). *[Title not captured in Phase 2 compilation — Chicago 44-week field study, automated shading]*. **[INCOMPLETE]**

Lin, G., Kramer, H., & Granderson, J. (2019). *[Title not captured in Phase 2 compilation — FDD portfolio study, 26 organizations/550 buildings]*. Lawrence Berkeley National Laboratory. **[INCOMPLETE]**

Lo Verso, V. R. M., & Pellegrino, A. (2019). *[Title not captured in Phase 2 compilation — EN 15193-1/LENI lighting-control evaluation, 4 EU climates]*. **[INCOMPLETE]**

Luthander, R., et al. (2015). *[Title not captured in Phase 2 compilation — PV self-consumption/storage review]*. **[INCOMPLETE]**

Meiers, J., & Frey, G. (2024). *[Title not captured in Phase 2 compilation — campus EV charging simulation, Germany]*. **[INCOMPLETE]**

Merema, B., et al. (2018). *[Title not captured in Phase 2 compilation — Belgium field DCV study, KU Leuven]*. **[INCOMPLETE]**

Mills, E., & Mathew, P. (2009). *[Title not captured in Phase 2 compilation — 24 UC/CSU building commissioning decomposition study]*. Lawrence Berkeley National Laboratory. **[INCOMPLETE]**

Mysen, M., et al. (2005). *[Title not captured in Phase 2 compilation — Norway educational ventilation field study]*. **[INCOMPLETE]**

Nagy, Z., et al. (2015). *[Title not captured in Phase 2 compilation — occupant-centered adaptive lighting control]*. **[INCOMPLETE]**

National Institute of Standards and Technology (NIST). (n.d.). *[Ventilation savings reference table ("Table 2"), high-occupancy-density spaces]*. **[INCOMPLETE — exact publication and year not captured in Phase 2 compilation]**

Nielsen, T. R. (2011). *[Title not captured in Phase 2 compilation — Denmark dynamic-envelope simulation]*. **[INCOMPLETE]**

O'Grady, M., et al. (2021). *[Title not captured in Phase 2 compilation]*. *Building and Environment*. **[INCOMPLETE — paywalled, not independently verified by Phase 2/3]**

Ogasawara, N. (1979). *[Title not captured in Phase 2 compilation — Tokyo ventilation study]*. **[INCOMPLETE]**

Pacific Northwest National Laboratory (PNNL). (n.d.). *PNNL-25985* [Report]. **[INCOMPLETE — full title, authors, and publication year not captured in Phase 2 compilation]**

Pang, Z., et al. (2021). *[Title not captured in Phase 2 compilation — hospitality occupancy-centric HVAC simulation, 19 US climates]*. **[INCOMPLETE]**

Pigg, S. (1996). *[Title not captured in Phase 2 compilation — occupancy-sensor rebound effect]*. **[INCOMPLETE]**

Ribeiro, A. M., et al. (2016). *[Title not captured in Phase 2 compilation — BEMS dew-point/wet-bulb cooling control; geographic origin unconfirmed, likely Portugal]*. **[INCOMPLETE]**

Safranek, S., et al. (2021). *[Title not captured in Phase 2 compilation — NICU lighting field study, n=5 rooms]*. Pacific Northwest National Laboratory. **[INCOMPLETE]**

Sánchez-Barroso, G., et al. (2020). *[Title not captured in Phase 2 compilation — Spain hospital DHW thermal-load modelling]*. **[INCOMPLETE]**

Sbar, N. L., et al. (2012). *[Title not captured in Phase 2 compilation — electrochromic glazing simulation]*. SAGE Electrochromics. **[INCOMPLETE — vendor-sponsored; excluded from central estimates per §4.2.2]**

SEFE Energy. (n.d.). *[Title not captured in Phase 2 compilation — UK sports/leisure MC trade-advisory source]*. **[INCOMPLETE — vendor-adjacent]**

Seger, M. (2025). *[Title not captured in Phase 2 compilation — UK workplace EV charging control-strategy comparison]*. **[INCOMPLETE]**

Smedegård, O., et al. (2021). *[Title not captured in Phase 2 compilation — systematic review, 524 papers screened, sports/leisure facility heating]*. Norwegian University of Science and Technology (NTNU). **[INCOMPLETE]**

South Australian Government. (n.d.). *[Title not captured in Phase 2 compilation — hospitality EV charging peak-demand projection to 2030]*. **[INCOMPLETE]**

Szydlowski, R. F. (1993). *[Title not captured in Phase 2 compilation — 6-building field EMCS study]*. US Department of Energy / Pacific Northwest Laboratory. **[INCOMPLETE]**

Teixeira, H., et al. (2024). *[Title not captured in Phase 2 compilation — Portugal dynamic-envelope simulation]*. **[INCOMPLETE]**

Tejero-González, A., et al. (2022). *[Title not captured in Phase 2 compilation — Spain hospital operating-room HVAC setback study]*. **[INCOMPLETE]**

Tucker. (2022). *[Title, initials not captured in Phase 2 compilation — MPC EV charging study]*. SLAC National Accelerator Laboratory / Google. **[INCOMPLETE]**

Unnamed source. (n.d.). *[Belgium hospital-room dynamic-envelope simulation, louver shading, cooling load 40–80%]*. **[INCOMPLETE — no author/title/year captured in Phase 2 compilation]**

Unnamed source. (n.d.). *[Cold-storage refrigeration FDD field study, defrost-fault decomposition, 18.3% savings]*. **[INCOMPLETE — no author/title/year captured; geography unconfirmed]**

Unnamed source. (n.d.). *[Saudi Arabia hotel dynamic-envelope/shading simulation, 20.5%, automation status uncertain]*. **[INCOMPLETE — no author/title/year captured]**

*Applied Energy* [journal]. (n.d.). *[Article title, authors, and exact year not captured in Phase 2 compilation — EU-Mediterranean multi-country operating-cost pilot-site study, Electricity domain, Other public buildings]*. **[INCOMPLETE — possibly field-measured, paywalled/unverified]**

*Applied Energy* [journal]. (2025). *[Article title and authors not captured in Phase 2 compilation — V2G battery-degradation compensation-cost study]*. **[INCOMPLETE]**

Vandenbogaerde, L., et al. (2023). *[Title not captured in Phase 2 compilation — EN ISO 52120-1 heating emission-control simulation]*. *Energy Efficiency* (Springer). **[INCOMPLETE — exact article title/DOI not captured; possibly the same author series as the 2025 and 2026 entries below]**

Vandenbogaerde, L., et al. (2025). *[Title not captured in Phase 2 compilation — companion/follow-up heating study to the 2023 entry above]*. *Energy Efficiency* (Springer). **[INCOMPLETE]**

Vandenbogaerde, L. (2026). *[Title not captured in Phase 2 compilation — cooling emission-control simulation testing EN ISO 52120-1, Belgium]*. **[INCOMPLETE — co-authorship, exact venue not captured; note this is a 2026 (current-year) source per the Phase 2 compilation, carried forward as given]**

Verbeke, S., et al. (2020). *Support for setting up a Smart Readiness Indicator for buildings and related impact assessment* [Final report]. European Commission, Joint Research Centre. https://doi.org/10.2833/41100 **[INCOMPLETE — full author list beyond "Verbeke et al." and exact report title not verified against the Phase 2 compilation; DOI is as given in the source material]**

Vincenti, G., et al. (2025). *[Title not captured in Phase 2 compilation — Italy healthcare DHW field study, demand-based recirculation control]*. **[INCOMPLETE]**

Wachenfeldt, B. J. (2007). *[Title not captured in Phase 2 compilation — Norway educational ventilation field study]*. **[INCOMPLETE]**

Waide, P., & eu.bac (European Building Automation and Controls Association). (2019). *[Title not captured in Phase 2 compilation — EU-wide BACS savings projection to 2038, industry-association-funded]*. **[INCOMPLETE — flagged circular/EN15232-derived, see §4.3]**

Wang, W., et al. (2011). *[Title not captured in Phase 2 compilation]* (Report No. PNNL-20955). Pacific Northwest National Laboratory.

Warren, P. R., & Harper, C. H. (1991). *[Title not captured in Phase 2 compilation — London auditorium ventilation simulation]*. **[INCOMPLETE]**

Weniger, J., et al. (2020). *[Title not captured in Phase 2 compilation — Skagerak Arena, Norway, 5-strategy battery-dispatch field/sim study]*. SINTEF. **[INCOMPLETE]**

Williams, A., et al. (2011/2012). *[Title not captured in Phase 2 compilation — 240-estimate, 88-source lighting-controls meta-analysis]*. Lawrence Berkeley National Laboratory. **[INCOMPLETE — two possible years given in Phase 2 source, likely a working-paper/published-version pair]**

WSEAS [publisher]. (2024). *[Article title and authors not captured in Phase 2 compilation — Greece hospitality PV/battery self-sufficiency simulation]*. **[INCOMPLETE — lower journal tier per Phase 2 assessment]**

---

*End of report. Full source material for this compilation: `master_evidence_table.md` (Phase 2, 10 domain/prior-art research agents) and `phase3_synthesis.md` (Phase 3 synthesis, revised at Devil's Advocate Checkpoint 2). This document has completed the full deep-research pipeline: Phase 1 (scoping, one Critical finding fixed), Phase 2 (10 parallel literature-search agents), Phase 3 (synthesis, one Devil's Advocate checkpoint with four Major findings fixed), Phase 4 (composition), and Phase 5 (editorial review — MINOR REVISION; ethics/AI-disclosure review — CONDITIONAL; Devil's Advocate Checkpoint 3 — REVISE, two Major + several Minor findings). All Phase 5 findings were applied in this Phase 6 revision pass, marked inline as "[Phase 6 revision, ...]" where the fix is substantive rather than cosmetic. Some low-priority stylistic suggestions from the Phase 5 reviews (denser table-cell reformatting, a third gap-grid symbol, a consolidated verify-first citation list) were left as optional future polish, consistent with the reviews' own characterization of them as non-blocking.*







