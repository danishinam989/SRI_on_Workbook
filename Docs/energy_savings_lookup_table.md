# Energy Savings Lookup Table — SRI Domain × Building Subtype

Condensed, single-table lookup derived from **[`energy_savings_by_domain_literature.md`](energy_savings_by_domain_literature.md)** (the full literature cross-check — sourcing, methodology, caveats, gap analysis, circularity assessment, and calibration guidance). **Use this table for quick reference only** — before using any figure for an actual calibration decision, check the corresponding row/section in the full report; several figures below carry caveats (bundling, endpoint-vs-stepwise, source concentration, vendor exclusion) that don't fit in a compact table but materially affect whether a number is usable as-is.

## Legend

| Tag | Meaning |
|---|---|
| **SW** | Stepwise — per-class-transition data available (rare; almost every figure below is EP) |
| **EP** | Endpoint-only — typically "before controls" vs. "best-practice controls" (roughly D→A) |
| **ISO** | Domain-isolated — figure reflects only this SRI domain |
| **BUN** | Bundled — figure mixes this domain with other measures/domains |
| **H / M / L** | Confidence: High / Medium / Low, as assigned in the source report |
| **Gap** | No credible standalone estimate found (literature-thin — may be fillable by future search) |
| **Hard gap** | No credible standalone estimate found (confirmed absent after exhausted search, or structurally unfillable) |

**Three caveats that don't fit in the table — read before using any figure:**
1. **Almost nothing is stepwise.** The optimiser needs D→C / C→B / B→A transition data; nearly every figure here is an endpoint (D-vs-A) comparison, and ISO 52120's class steps are non-linear (D→C alone is ~63% of total D→A savings for Offices heating). Do not linearly interpolate. See report §6A.
2. **Monitoring & Control is NOT additive.** Every MC row below is empirically shown to be 100%-or-near-100% decomposable into HVAC/lighting fault-fixes. Do not stack MC's figure on top of separately-modeled HVAC/Lighting savings — see report §4.2.3 and §6D.
3. **EV Charging's numbers are peak-demand / cost-shift, not % energy saved** — a different unit from the other 8 domains, and several figures are *burden* (uncontrolled charging increasing peak demand), not savings. Direction is noted inline below.

---

## Lookup Table

| Domain | Subtype | Savings Range | Basis | Conf. | Source |
|---|---|---|---|---|---|
| Heating | Offices | 9–51% | SW·ISO | H | Goldschmidt (2026) |
| Heating | Offices | 19.2% (14–25%) | EP·ISO | H | Szydlowski (1993) |
| Heating | Offices | 22–56% HVAC (bundled; fan control ↑ heating use — offsetting effect) | SW·BUN | M | Wang et al. (2011) |
| Heating | Retail/wholesale | 16–47% HVAC | SW·BUN | M | Wang et al. (2011) |
| Heating | Hospitality | 24–58% HVAC | EP·BUN | M | Pang et al. (2021) |
| Heating | Sports/leisure (pools) | ~8% cost; 20–40% (predictive+solar); ~20% (heat recovery) | EP·Mixed | H/M | Smedegård et al. (2021) |
| Heating | Educational | *No credible estimate found* | — | — | Gap |
| Heating | Healthcare | *No credible estimate found* (Cochrane review confirms scarcity) | — | — | Hard gap |
| Heating | Industrial/warehouse | *No credible estimate found* | — | — | Hard gap |
| Heating | Other public | Qualitative only, no % | — | L–M | Gupta et al. (2017) |
| DHW | Offices | Thermal 20.3%, pump elec. 88.0% (DHW "negligible" for offices generally) | EP·ISO | M–H | CARD/CEE (2018) |
| DHW | Educational | Thermal 11.4%, pump elec. 96.2% | EP·ISO | M | CARD/CEE (2018) |
| DHW | Healthcare | Thermal 48.6%, elec. 68.6% (zero Legionella detected under tested regime) | EP·ISO | H | Vincenti et al. (2025) |
| DHW | Retail/wholesale | *No credible estimate found* | — | — | Gap |
| DHW | Hospitality | Thermal 9.9–15.9%, pump elec. 70–93% | EP·ISO | M–H | CARD/CEE (2018) |
| DHW | Sports/leisure | *No credible estimate found* (conflated with pool-water heating) | — | — | Gap |
| DHW | Industrial/warehouse | *No credible estimate found* (self-consistent w/ ISO's own gap) | — | — | Gap |
| DHW | Other public | *No credible estimate found* (proxy: Offices/Educational) | — | — | Gap |
| Cooling | Offices | 1–58% (emission control, simulation) | SW·ISO | M | Vandenbogaerde (2026) |
| Cooling | Offices | Adaptive setpoint 12–38%; combined 23–39% HVAC | SW·ISO/BUN | H | Chen & Yin (2022) |
| Cooling | Offices | >30% chiller electricity | EP·ISO | H (measured)/M (geo) | HKUST (2018) |
| Cooling | Educational | **14% / 18% / 24%** for Class C/B/A — fills ISO's own documented gap | **SW (class-based)**·ISO | H | Albesiano (2023) |
| Cooling | Healthcare | OR 75% gas/69% elec.; hospital-wide only 1.12%/0.64%; occupancy 37.5%, schedule 40%; chiller ANN 7–10% | EP·BUN | H | Tejero-González et al.; Castellanos-Antolín et al.; Dulce-Chamorro et al. |
| Cooling | Retail/wholesale | 17.6% (measured); 9% (trade-press) | EP·ISO | M/L | "2025 Smart Cities"; CIBSE Journal |
| Cooling | Hospitality | Qualitative only, % unconfirmed (paywalled) | SW (unconfirmed)·BUN | L–M | Becchio et al. (2017) |
| Cooling | Sports/leisure | ~8% | EP·BUN | L–M | Ribeiro et al. (2016) |
| Cooling | Industrial/warehouse | 30–40% (8–72% range) — refrigeration only, not ambient warehouses | EP·BUN | M | ICE-E project |
| Cooling | Other public | ~15% (museum); 40% (archive) | EP·BUN | M | Kompatscher et al. (2017, 2019) |
| Ventilation | Offices | 12%; 7.8%; 9–28%/43–46% (coil); 7–17%; **not cost-effective** under some CA baseline assumptions | Mixed SW/EP·Mostly ISO | M–H | Donnini; Gabel; Knoespel/Emmerich; Haghighat; Fisk (2010) |
| Ventilation | Offices | 50% fan / 34% heat-loss (reported separately) | EP·ISO | H | Merema et al. (2018) |
| Ventilation | Educational | 38%; 21% heating/87% fan; 50–55% fan/36–47% heat-loss | EP·ISO | H | Mysen et al.; Wachenfeldt; Merema et al. |
| Ventilation | Healthcare | 37.5%/40% (OR-specific, unoccupied-hours setback only) | EP·ISO | M | Castellanos-Antolín et al. (2022) |
| Ventilation | Retail/wholesale | 19% elec./up to 100% heating (Sacramento); 40%/30% (Tokyo) | SW (seasonal)·BUN | L–M | Brandemuehl (1999); Ogasawara (1979) |
| Ventilation | Hospitality | 17% elec. (~half attributable to DCV alone); kitchen airflow often code-constrained | EP·BUN | L–M | Brandemuehl (1999) |
| Ventilation | Sports/leisure | 40–70% (auditoria); 26–53% (London sim); pools skew to heat-recovery not DCV | SW·BUN | L–M | NIST Table 2; Warren & Harper (1991) |
| Ventilation | Industrial/warehouse | *No credible estimate found* | — | — | Hard gap |
| Ventilation | Other public | 13–20%; 20–60% (entrance halls, thin/dated) | EP·BUN | L | Kulmala (1984) |
| Lighting | Offices | Occupancy 24–38%; daylight 16–32%; combined 38–79%; adaptive 38–73% | **SW**·ISO | **H** | Williams et al.; Galasiu; Nagy et al.; Dikel |
| Lighting | Offices | LENI method: daylight ≥20% in 39% of configs; combined ≥20% in 100% | SW·ISO | H | Lo Verso & Pellegrino (2019) |
| Lighting | Educational | 18–46% (3 topologies); >60%/+46% (auto-off + tuning) | SW·ISO | H | Delvaeye (2016); IEA SHC Task 50 |
| Lighting | Healthcare | 13% — **manual outperformed automated** in this study | EP·BUN | M | Safranek et al. (2021) |
| Lighting | Retail/wholesale | 24–66¢/ft²/yr (utility white paper); generic 20–60% claims unverified | EP·ISO | M | Heschong Mahone Group |
| Lighting | Hospitality | *No credible estimate found* (vendor-only) | — | — | Gap |
| Lighting | Sports/leisure | *No credible estimate found* (vendor-only) | — | — | Gap |
| Lighting | Industrial/warehouse | *No credible estimate found* (unresolved lead) | — | — | Gap |
| Lighting | Other public | *No credible estimate found* | — | — | Gap |
| Dynamic Envelope | Offices | **Field anchor ~10–20%** HVAC/lighting; sim range far wider (14–53%), lab up to 60–76% | Mostly SW·Mixed | H (field)/M (sim) | Lee et al. (2025, 2005); Nielsen (2011); Teixeira et al. (2024) |
| Dynamic Envelope | Offices | VENDOR 48–53% — excluded from central estimate, ceiling only | EP·ISO | L (flagged) | Sbar et al. (2012) |
| Dynamic Envelope | Educational | 12–30% perimeter lighting (bundled demo/lab) | EP·BUN | M | LBNL FlexLab |
| Dynamic Envelope | Healthcare | 40–80% cooling load (louvers; dynamic-EC case not cleanly isolated) | SW·Partial BUN | M | Unnamed Belgium study |
| Dynamic Envelope | Retail/wholesale | *No credible estimate found* (confirmed zero) | — | — | Hard gap |
| Dynamic Envelope | Hospitality | 20.5% (automation status uncertain — may be static) | EP·BUN | L | Unnamed Saudi study |
| Dynamic Envelope | Sports/leisure | *No credible estimate found* (confirmed, scope-excluded) | — | — | Hard gap |
| Dynamic Envelope | Industrial/warehouse | *No credible estimate found* (confirmed) | — | — | Hard gap |
| Dynamic Envelope | Other public | *No credible estimate found* | — | — | Hard gap |
| Electricity | Offices | Battery +13–24pp self-consumption; DSM +2–15pp; peak −5–15% avg (up to 56% short-duration) | SW·Mixed | M | Luthander et al.; *Energies* (2017); LBNL ADR |
| Electricity | Educational | Weak, non-isolated single case | — | L | Frontiers in Energy Research (2025) |
| Electricity | Healthcare | 8.1% cost reduction (co-optimized w/ sizing, not isolated) | EP·Not isolated | M | (same source, hospital case) |
| Electricity | Retail/wholesale | *No credible estimate found* (leads only) | — | — | Unresolved |
| Electricity | Hospitality | 99% self-sufficiency (conflates sizing+dispatch) | EP·Not isolated | L | WSEAS (2024) |
| Electricity | Sports/leisure | **68.6–84.7% self-consumption** — 5 strategies on identical fixed hardware, cleanest isolation in the domain | **SW·Fully ISO** | **H** | Weniger et al. (2020), Skagerak Arena |
| Electricity | Industrial/warehouse | *No credible estimate found* (EU lead unverified) | — | — | Unresolved |
| Electricity | Other public | *No credible estimate found* (3–13% cost, unverified) | — | — | Unresolved |
| EV Charging† | Offices/Workplace | Peak **−28.5%** (mitigation); cost-min: −19% cost but **+4.9% peak** (tradeoff) | SW·ISO | H | Seger (2025); Tucker (2022) |
| EV Charging† | Industrial/warehouse (fleet depots) | Peak-charge **−17%**; cost −23–32% | EP·ISO | H | Golden Arrow (2025) |
| EV Charging† | Educational | 3–13% (unverified); campus peak **+17%** (burden) | Mixed | M | Meiers & Frey (2024); Kanellos (2022) |
| EV Charging† | Retail/wholesale | Peak **+250%** (burden only — no mitigation found) | EP·ISO | H | Gilleran et al. (2021) |
| EV Charging† | Healthcare | *No credible estimate found* | — | — | Gap |
| EV Charging† | Hospitality | Peak rising to 250–320kW by 2030 (burden only) | EP·ISO | M | South Australian Government |
| EV Charging† | Sports/leisure | *No credible estimate found* | — | — | Gap |
| EV Charging† | Other public | *No credible estimate found* | — | — | Gap |
| Monitoring & Control‡ | Offices | 8% median (FDD); 16% median (commissioning, 10–30% range) | EP·**NOT SEPARABLE** | H | Lin, Kramer & Granderson (2019); LBNL Cx database |
| Monitoring & Control‡ | Educational | 10% (2–25%); 9% elec.; **65% explicitly attributed to HVAC-fault fixes** | EP·**NOT SEPARABLE** | H | Mills & Mathew (2009) |
| Monitoring & Control‡ | Healthcare | 16%, 21%, 19% — **100% decomposed into HVAC control-point fixes** | EP·**NOT SEPARABLE** | **H** | Im et al. (2021) |
| Monitoring & Control‡ | Retail/wholesale | Weak — simulated only, not field-validated | EP (sim)·Partial | M | PNNL-25985 |
| Monitoring & Control‡ | Industrial/warehouse | 18.3% — refrigeration end-use only, not whole-building | EP·NOT SEPARABLE | M | Unnamed cold-store FDD paper |
| Monitoring & Control‡ | Hospitality | ~3% — weakest segment in the LBNL database | EP·Not separable | M | LBNL Cx database segment |
| Monitoring & Control‡ | Sports/leisure | 10–30% (vendor-adjacent, bundled with non-MC measures) | EP·Not isolated | L (flagged) | SEFE Energy |
| Monitoring & Control‡ | Other public | 16% ("public order & safety" segment, simulated) | EP (sim)·Partial | M | PNNL-25985 |

† EV Charging figures are peak-demand-reduction % or cost-shift %, **not** % energy saved — see caveat 3 above.
‡ Monitoring & Control figures are the *headline decomposed savings*, not an independently-attributable MC effect — see caveat 2 above; do not add these on top of Heating/Cooling/Ventilation/Lighting savings for the same building.

---

*Source: [`energy_savings_by_domain_literature.md`](energy_savings_by_domain_literature.md) — see that document for full citations (§8), gap-analysis grid (§5.2), synthesis/contradiction resolution (§4), and calibration implications (§6). This lookup table is a compact derivative; where it and the full report ever disagree, the full report is authoritative.*
