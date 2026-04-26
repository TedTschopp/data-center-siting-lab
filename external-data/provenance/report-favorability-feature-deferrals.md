# Report Favorability Feature Deferrals

This note records the features from the data center siting report that are still
missing from the report-aligned favorability stack and are therefore explicitly
deferred in the current repo scope.

The purpose of this note is traceability, not silent omission. Each deferred feature
remains a requirement. The repo is simply making the current decision explicit until
an executable workflow is implemented.

## Deferred Features

| Feature | Candidate public path | Current decision | Reason deferred now | Reopen trigger |
| --- | --- | --- | --- | --- |
| Operating generator proximity | EIA generator inventories (`https://www.eia.gov/electricity/data/eia860/`) | Explicitly deferred | The repo does not yet define the point extraction, status filter, and nearest-feature transform needed for the report feature. | Reopen when item 21 starts or when a generator-proximity workflow is selected for implementation. |
| Retired generator proximity | EIA generator inventories (`https://www.eia.gov/electricity/data/eia860/`) | Explicitly deferred | The repo does not yet define the retirement-status filter and nearest-feature transform needed for the report feature. | Reopen when item 21 starts or when a retired-generator workflow is selected for implementation. |
| Planned generator proximity | EIA generator inventories (`https://www.eia.gov/electricity/data/eia860/`) | Explicitly deferred | The repo does not yet define the planned-status filter and nearest-feature transform needed for the report feature. | Reopen when item 21 starts or when a planned-generator workflow is selected for implementation. |
| Gas pipeline proximity | Public pipeline mapping and geometry sources such as PHMSA NPMS Public Viewer (`https://pvnpms.phmsa.dot.gov/PublicViewer/`) | Explicitly deferred | The repo has a gas service territory proxy but no public pipeline geometry workflow, proximity transform, or right-of-way policy. | Reopen when a public pipeline geometry source is selected and the proximity method is agreed. |
| Natural hazard building loss rate | FEMA National Risk Index (`https://hazards.fema.gov/nri/`) | Explicitly deferred | The report-level hazard-loss concept is not yet mapped to one public source, one building-loss metric, or one zonal aggregation method in the repo. | Reopen when a specific hazard-loss source and aggregation contract are chosen. |
| Cooling degree days for 2035 | Public climate projection datasets such as NASA NEX-GDDP-CMIP6 (`https://www.nasa.gov/nccs/nex-gddp-cmip6/`) | Explicitly deferred | The repo has not yet fixed the public climate source, scenario, temporal slice, or spatial aggregation method needed for a report-traceable 2035 feature. | Reopen when the climate-source and scenario policy is selected. |
| Data center construction labor | Public labor datasets such as BLS OEWS (`https://www.bls.gov/oes/`) | Explicitly deferred | The repo does not yet define the occupations, industries, geography, or transformation needed to approximate the report's construction-worker feature. | Reopen when a labor-source and mapping policy are selected. |
| Residential electricity rate | Existing staged URDB bulk export (`https://apps.openei.org/USURDB/`) | Explicitly deferred | URDB staging exists, but the repo does not yet define the report-aligned extraction, normalization, and spatial assignment workflow for the residential-rate feature. | Reopen when the URDB-to-feature transform is selected for implementation. |
| Electricity service territory count | URDB plus an electric service-territory geometry source | Explicitly deferred | URDB alone does not produce the territory-count feature shown in the report, and the repo does not yet stage a service-territory polygon source or counting workflow. | Reopen when the electric service-territory source and count method are selected. |

## Current Rule

If one of these features is implemented later, replace the corresponding deferred
manifest row and note text with the executable workflow, derived outputs, and
validation guidance in the same change.