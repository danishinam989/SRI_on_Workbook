# Irish Supplier RFQ — SRI Smart-Ready Service Upgrade Pricing

Reference building for all pricing below: **non-residential building, ~1,500 m² gross floor area, built ~1990s, located in Ireland** (matches the profile already used in this project's optimiser examples). For each service, please provide the **total supply + install cost (€, ex. VAT) to bring this reference building from its current non-smart baseline (Level 0) up to each listed functionality level**, plus a **marginal €/m² rate** you'd add or subtract for a building larger or smaller than 1,500 m² (e.g. "+€X per m² above/below 1,500 m²"). Costs should be cumulative (i.e., the Level 3 figure is the total cost to reach Level 3 from scratch, not the incremental cost from Level 2). Where a service has no scope for a functionality level (blank cell), leave it blank. All descriptions below are condensed from the EU SRI Calculation Framework v4.5 / EN 15232 — full regulatory wording available on request.

This is a **non-binding budgetary estimate request** for research/planning purposes (SRI upgrade cost modelling), not a tender — happy to discuss scope or send the relevant domain sections only to the specialists who cover them.

## Domain: Heating (10 services — HVAC controls specialist)

| Code | Service | Level 1 | Level 2 | Level 3 | Level 4 | Cost→L1 | Cost→L2 | Cost→L3 | Cost→L4 | €/m² |
|---|---|---|---|---|---|---|---|---|---|---|
| H-1a | Heat emission control | Central automatic control | Individual room control (e.g. TRVs) | + communication to BACS | + occupancy detection | | | | | |
| H-1b | Emission control for TABS (heating) | Central automatic control | Advanced central control | + intermittent operation/room feedback | — | | | — | | |
| H-1c | Distribution fluid temp. control | Outside-temp compensated | Demand-based control | — | — | | — | — | |
| H-1d | Distribution pump control | On/off control | Multi-stage control | Variable speed (internal est.) | Variable speed (external signal) | | | | | |
| H-1f | Thermal energy storage (heating) | Time-scheduled operation | Load-prediction based | + flexible grid-signal control | — | | | — | |
| H-2a | Heat generator control (non-HP) | Variable temp (outdoor-compensated) | Variable temp (load-dependent) | — | — | | — | — | |
| H-2b | Heat generator control (heat pumps) | Multi-stage capacity control | Variable capacity control | + external grid signals | — | | | — | |
| H-2d | Sequencing of multiple heat generators | Fixed priority list | Dynamic priority (efficiency/CO2) | + predictive load | + grid signals | | | | | |
| H-3 | Heating system performance reporting | Central reporting (current KPIs) | + historical data | + forecasting/benchmarking | + predictive/fault detection | | | | | |
| H-4 | Heating flexibility/grid interaction | Scheduled operation | Self-learning optimal control | Flexible grid-signal control | Model-predictive + grid signals | | | | | |

## Domain: Domestic Hot Water (5 services — plumbing/heating specialist)

| Code | Service | Level 1 | Level 2 | Level 3 | Level 4 | Cost→L1 | Cost→L2 | Cost→L3 | Cost→L4 | €/m² |
|---|---|---|---|---|---|---|---|---|---|---|
| DHW-1a | DHW storage charging (electric) | Auto on/off + scheduled charging | + multi-sensor storage mgmt | + renewables/grid-based charging | — | | | — | |
| DHW-1b | DHW storage charging (hot water gen.) | Auto on/off + scheduled charging | + demand-based supply temp | + external signal (e.g. district heating) | — | | | — | |
| DHW-1d | DHW charging (solar + supplementary) | Auto solar + supplementary charge | + demand-oriented supply | + multi-sensor mgmt | — | | | — | |
| DHW-2b | Sequencing of DHW generators | Fixed priority list | Dynamic priority (efficiency/CO2) | + predictive load | + grid signals | | | | | |
| DHW-3 | DHW performance reporting | Indication of actual values | + historical data | + forecasting/benchmarking | + predictive/fault detection | | | | | |

## Domain: Cooling (10 services — HVAC controls specialist)

| Code | Service | Level 1 | Level 2 | Level 3 | Level 4 | Cost→L1 | Cost→L2 | Cost→L3 | Cost→L4 | €/m² |
|---|---|---|---|---|---|---|---|---|---|---|
| C-1a | Cooling emission control | Central automatic control | Individual room control | + BACS communication | + occupancy detection | | | | | |
| C-1b | Emission control for TABS (cooling) | Central automatic control | Advanced central control | + intermittent/feedback | — | | | — | |
| C-1c | Chilled water distribution temp. | Outside-temp compensated | Demand-based control | — | — | | — | — | |
| C-1d | Cooling distribution pump control | On/off control | Multi-stage control | Variable speed (internal) | Variable speed (external) | | | | | |
| C-1f | Heating/cooling interlock | Partial interlock | Total interlock | — | — | | — | — | |
| C-1g | Thermal energy storage (cooling) | Time-scheduled operation | Load-prediction based | + flexible grid control | — | | | — | |
| C-2a | Cooling generator control | Multi-stage capacity control | Variable capacity control | + external grid signals | — | | | — | |
| C-2b | Sequencing of cooling generators | Fixed sequencing (loads) | Dynamic priority (efficiency) | + predictive sequencing | + grid signals | | | | | |
| C-3 | Cooling performance reporting | Central reporting (current KPIs) | + historical data | + forecasting/benchmarking | + predictive/fault detection | | | | | |
| C-4 | Cooling flexibility/grid interaction | Scheduled operation | Self-learning optimal control | Flexible grid-signal control | Model-predictive + grid signals | | | | | |

## Domain: Ventilation (6 services — HVAC/mechanical specialist)

| Code | Service | Level 1 | Level 2 | Level 3 | Level 4 | Cost→L1 | Cost→L2 | Cost→L3 | Cost→L4 | €/m² |
|---|---|---|---|---|---|---|---|---|---|---|
| V-1a | Room-level supply air flow control | Clock control | Occupancy detection | Central CO2/VOC demand control | Local demand control (zone dampers) | | | | | |
| V-1c | Air handler flow/pressure control | On/off time control | Multi-stage control | Auto flow/pressure (no reset) | Auto flow/pressure (with reset) | | | | | |
| V-2c | Heat recovery overheating control | Modulate/bypass (exhaust sensor) | Modulate/bypass (multi-sensor/predictive) | — | — | | — | — | |
| V-2d | Supply air temp. control | Constant setpoint | Outdoor-temp compensated | Load-dependent compensation | — | | | — | |
| V-3 | Free cooling (mechanical vent.) | Night cooling | Free cooling (air flow modulated) | — | — | | — | — | |
| V-6 | IAQ reporting | Air quality sensors + monitoring | + historical info to occupants | + maintenance/action warnings | — | | | — | |

## Domain: Lighting (2 services — electrical specialist)

| Code | Service | Level 1 | Level 2 | Level 3 | Level 4 | Cost→L1 | Cost→L2 | Cost→L3 | Cost→L4 | €/m² |
|---|---|---|---|---|---|---|---|---|---|---|
| L-1a | Occupancy control for indoor lighting | Manual + sweep extinction | Automatic detection (auto on/dim) | Automatic (manual on/auto off) | — | | | — | |
| L-2 | Daylight-based lighting control | Manual (per room/zone) | Automatic switching | Automatic dimming | + scene-based control | | | | | |

## Domain: Dynamic Building Envelope (3 services — window/shading specialist)

| Code | Service | Level 1 | Level 2 | Level 3 | Level 4 | Cost→L1 | Cost→L2 | Cost→L3 | Cost→L4 | €/m² |
|---|---|---|---|---|---|---|---|---|---|---|
| DE-1 | Window solar shading control | Motorized, manual control | + automatic (sensor-based) | + combined light/blind/HVAC | + predictive (weather forecast) | | | | | |
| DE-2 | Window open/close + HVAC | Open/close detection → shutdown | + automated mechanical opening | + centralized coordination | — | | | — | |
| DE-4 | Envelope systems reporting | Position + fault detection | + predictive maintenance | + real-time sensor data | + historical sensor data | | | | | |

## Domain: Electricity / DER (7 services — electrical/BMS specialist)

| Code | Service | Level 1 | Level 2 | Level 3 | Level 4 | Cost→L1 | Cost→L2 | Cost→L3 | Cost→L4 | €/m² |
|---|---|---|---|---|---|---|---|---|---|---|
| E-2 | Local generation reporting | Current generation data | + historical data | + forecasting/benchmarking | + predictive/fault detection | | | | | |
| E-3 | Local electricity storage | On-site storage (battery) | + grid-signal controller | + optimising self-consumption | + grid feedback capability | | | | | |
| E-4 | Self-consumption optimisation | Scheduling consumption | Automated (current renewables) | + predicted needs/availability | — | | | — | |
| E-5 | CHP control | Runtime, RES-availability influenced | + grid signals, dynamic charging | — | — | | — | — | |
| E-8 | Microgrid operation support | Grid-signal-based mgmt | + supply to neighbours/microgrid | + island-mode capability | — | | | — | |
| E-11 | Energy storage reporting | Current SOC data | + historical data | + forecasting/benchmarking | + predictive/fault detection | | | | | |
| E-12 | Electricity consumption reporting | Building-level reporting | Real-time feedback/benchmarking | + appliance-level | + personalized recommendations | | | | | |

## Domain: EV Charging (3 services — electrical/EV infrastructure specialist)

| Code | Service | Level 1 | Level 2 | Level 3 | Level 4 | Cost→L1 | Cost→L2 | Cost→L3 | Cost→L4 | €/m² |
|---|---|---|---|---|---|---|---|---|---|---|
| EV-15 | EV charging capacity | Ducting/simple plug available | 0–9% of parking spaces | 10–50% of parking spaces | >50% of parking spaces | | | | | |
| EV-16 | EV charging grid balancing | 1-way controlled charging | 2-way controlled charging | — | — | | — | — | |
| EV-17 | EV charging info/connectivity | Status reporting to occupant | + auto ID/authorisation (ISO 15118) | — | — | | — | — | |

## Domain: Monitoring & Control (8 services — BMS/controls integrator)

| Code | Service | Level 1 | Level 2 | Level 3 | Level 4 | Cost→L1 | Cost→L2 | Cost→L3 | Cost→L4 | €/m² |
|---|---|---|---|---|---|---|---|---|---|---|
| MC-3 | HVAC runtime management | Scheduled runtime | On/off based on building loads | + predictive/grid signals | — | | | — | |
| MC-4 | Fault detection (TBS) | Central alarms (≥2 TBS) | Central alarms (all TBS) | + diagnosing functions | — | | | — | |
| MC-9 | Occupancy detection (connected) | Per-function detection | Centralised (feeds multiple TBS) | — | — | | — | — | |
| MC-13 | Central TBS/energy reporting | Real-time per energy carrier | + combining ≥2 domains | + combining all domains | — | | | — | |
| MC-25 | Smart grid integration | DSM per individual TBS | Coordinated DSM across TBS | — | — | | — | — | |
| MC-28 | DSM performance reporting | Current status + energy flows | + historical/predicted status | — | — | | — | — | |
| MC-29 | Override of DSM control | Manual override/reactivation | Scheduled override | + optimised control | — | | | — | |
| MC-30 | Unified TBS platform | Manual multi-TBS control | Automated coordination | + energy-flow optimisation | — | | | — | |

**Submission format requested:** a single spreadsheet (the table structure above, one row per code) is easiest to fold back into the pricing model — happy to provide this as an actual Excel/CSV template rather than the markdown tables above if that's more convenient for you or the supplier.
