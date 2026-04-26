# Data Center Siting Parity Matrix

This matrix translates the staged report requirements into one row-level execution
view for the current repo.

Status labels:

- `implemented`: the repo has a report-aligned executable workflow or derived output.
- `proxy-implemented`: the repo has an executable public approximation, but it is
  explicitly weaker than the report concept or cited source.
- `commercial-blocked`: exact parity depends on a commercial input.
- `public-source-missing`: the repo does not yet define a public acquisition or
  staging path for the requirement.
- `not-yet-modeled`: the repo has a staged source or adjacent workflow, but the
  report-aligned transform or exclusion logic is not yet implemented.

## Feasibility Exclusion Requirements

| Requirement | Report cue | Current repo surface | Status | Current repo evidence / next step |
| --- | --- | --- | --- | --- |
| Airports and runways | Airspace / defense exclusions | No dedicated staged dataset or transform | `public-source-missing` | Add the public acquisition and exclusion workflow for airport and runway footprints. |
| DOD clear zones, accident potential zones, and military setbacks | Airspace / defense exclusions | No dedicated staged dataset or transform | `public-source-missing` | Add the public or restricted-source decision and the corresponding setback workflow. |
| NWI wetlands | Environmental exclusion | Dataset staging exists; exclusion transform does not | `not-yet-modeled` | `nwi_wetlands` is `execution-ready` in `external-data/manifest/dataset-manifest.csv`, but no report-layer exclusion workflow exists yet. |
| FEMA 100-year floodplains | Environmental exclusion | Dataset staging exists; exclusion transform does not | `not-yet-modeled` | `fema_nfhl` is `execution-ready`, but the repo does not yet produce the floodplain exclusion layer used by the report. |
| RIBITS mitigation banks and in-lieu fee lands | Environmental exclusion | Scripted snapshot exists; exclusion geometry transform does not | `not-yet-modeled` | `ribits` now stages a scripted snapshot, and `external-data/provenance/report-reproduction-gaps.md` still calls out the downstream transform gap. |
| NLCD water and wetlands exclusions | Environmental exclusion | NLCD staging plus bounded feasible-land exclusion slice | `proxy-implemented` | `nlcd` is `execution-ready`, and the bounded report bundle now excludes cells whose staged NLCD water/wetland share across classes `11`, `90`, and `95` is at least `0.5`; remaining work is full report-stack parity beyond this one slice. |
| PAD-US / GAP protected areas | Environmental exclusion | Dataset staging exists; exclusion transform does not | `not-yet-modeled` | `pad_us_gap` is `execution-ready`, but the report-aligned protected-land exclusion workflow is not yet implemented. |
| Roads | Infrastructure exclusion | No dedicated staged dataset or transform | `public-source-missing` | Define the public source and exclusion logic for road footprints or setbacks. |
| Railroads | Infrastructure exclusion | No dedicated staged dataset or transform | `public-source-missing` | Define the public source and exclusion logic for railroad footprints or setbacks. |
| Building structures | Infrastructure exclusion | Building tags are only used inside the public data center baseline workflow | `public-source-missing` | Add a dedicated building-structure exclusion source and transform instead of reusing data-center baseline logic indirectly. |
| Transmission corridors and right-of-way exclusions | Infrastructure exclusion | Public transmission line baseline exists, but no corridor or right-of-way workflow exists | `not-yet-modeled` | `external-data/provenance/power-infrastructure-public-baseline.md` covers lines and substations, not corridor-style exclusion geometry. |
| Oil and gas pipeline right-of-way exclusions | Infrastructure exclusion | No pipeline right-of-way dataset or transform exists | `public-source-missing` | Add the public acquisition and transform path for pipeline right-of-way exclusions. |
| Elevation constraint | Terrain exclusion | No dedicated terrain workflow exists | `public-source-missing` | Add a DEM source and terrain-threshold transform for report parity. |
| Slope constraint | Terrain exclusion | No dedicated terrain workflow exists | `public-source-missing` | Add a DEM source and slope-threshold transform for report parity. |

## Favorability Feature Requirements

| Requirement | Report cue | Current repo surface | Status | Current repo evidence / next step |
| --- | --- | --- | --- | --- |
| Natural gas service coverage | Speed to power | Public gas service territory workflow | `proxy-implemented` | `external-data/provenance/gas-service-territory-public-baseline.md` documents a state-dependent public approximation rather than a complete national open standard layer. |
| Substation proximity | Speed to power | Public power baseline | `proxy-implemented` | `external-data/provenance/power-infrastructure-public-baseline.md` documents an OSM-based approximation with sparse voltage-tag limitations. |
| Operating generator proximity | Speed to power | No staged generator dataset or transform | `public-source-missing` | Define the public generator source and nearest-operating-generator workflow. |
| Onshore fiber proximity | Connectivity | Public fiber proxy workflow | `proxy-implemented` | `external-data/provenance/fiber-public-proxy.md` documents a route proxy rather than exact fiber centerline parity. |
| Retired generator proximity | Speed to power | No staged generator dataset or transform | `public-source-missing` | Define the public generator source and nearest-retired-generator workflow. |
| Land fair market value | Affordability | Public land-value proxy workflow | `proxy-implemented` | `external-data/provenance/land-value-public-proxy.md` documents a within-state normalization rather than harmonized national market values. |
| Data center construction labor | X factor | No dedicated labor-count workflow | `public-source-missing` | Add a public labor dataset and feature-generation workflow for the report's construction-worker signal. |
| Transmission line proximity above 135 kV | Speed to power | Public power baseline | `proxy-implemented` | The repo can generate `public_transmission_lines_135kv.gpkg`, but it remains a public approximation weaker than a curated grid model. |
| Planned generator proximity | Speed to power | No staged generator dataset or transform | `public-source-missing` | Define the public source and nearest-planned-generator workflow. |
| Natural hazard building loss rate | Environment | No staged hazard workflow | `public-source-missing` | Add the public hazard-loss input and zonal aggregation method. |
| Gas pipeline proximity | Speed to power | No pipeline geometry workflow | `public-source-missing` | Gas service territories exist, but pipeline geometry proximity does not. |
| Cooling degree days for 2035 | Environment | No staged climate workflow | `public-source-missing` | Add the public climate source, scenario choice, and 2035 aggregation method. |
| NERC reserve margin | Speed to power | NERC reserve-margin feature pipeline | `implemented` | `external-data/provenance/nerc/nerc-ltra-2025.md` and the derived `external-data/derived/nerc/` outputs provide the implemented workflow. |
| Construction cost ($/MW) | Affordability | Public construction-cost proxy workflow | `proxy-implemented` | `external-data/provenance/construction-cost-public-proxy.md` documents a relative affordability proxy, not exact dollars-per-MW parity. |
| Residential electricity rate ($/kWh) | Speed to power | URDB acquisition exists, but no report-feature transform exists | `not-yet-modeled` | `urdb` is `execution-ready`, but the repo does not yet derive the residential-rate feature used by the report. |
| Electricity service territories count | Speed to power | URDB acquisition exists, but no service-territory-count transform exists | `not-yet-modeled` | `urdb` is `execution-ready`, but the repo does not yet produce the utility-count feature used by the report. |
| Water availability | Water | Public water proxy workflow | `proxy-implemented` | `external-data/provenance/water-availability-public-proxy.md` documents a state-withdrawal proxy rather than literal site-level water availability. |

## Cross-Cutting Follow-Through

This matrix closes the row-level classification gap for exclusion and favorability
requirements. The remaining open work is tracked separately because it is about
workflow behavior rather than row inventory:

- report-aligned site suitability methodology or a documented bounded public
  approximation
- report-layer outputs and downscaling assumptions
- report-assumption registry
- limitation carry-forward in generated reports
- ReEDS-facing interoperability for report outputs