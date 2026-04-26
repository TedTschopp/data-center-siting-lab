# Data Center Siting Report Requirements

This note captures the report-derived requirements that now govern report-oriented
reVeal reproduction work.

## Source Documents

- Local report copy: `external-data/raw/reports/nlr-pr-6a20-99256-leveraging-reveal-for-data-center-siting.pdf`
- Report title: `Leveraging reVeal for Data Center Siting` (`NLR/PR-6A20-99256`, March 2026)
- LinkedIn introductory post: `Data Center Site Modeling with reVeal: Part I`
- LinkedIn follow-up post: `Data Center Site Modeling with reVeal: Part II`

The staged FY26 report remains the primary requirement source. The LinkedIn Part I
and Part II descriptions add clarifying detail for the national-scale methodology,
downscaling outputs, scenario framing, integration target, and known model
limitations.

Detailed row-level coverage for the exclusion and favorability requirements is
tracked in `external-data/provenance/data-center-siting-parity-matrix.md`.

The current methodology boundary for site suitability is tracked in
`external-data/provenance/site-suitability-bounded-public-approximation.md`.

The current bounded public report-output bundle is tracked in
`external-data/provenance/report-output-bounded-public-bundle.md`.

## Report-Derived Requirements

### 1. Feasibility exclusions are a required report input

The report's data center siting feasibility step applies explicit geospatial
exclusion layers before favorability scoring. The cited exclusion families include:

- airspace and defense constraints
- environmental constraints
- infrastructure setbacks and occupied footprints
- terrain constraints

Named examples in the report include airports and runways, DOD clear zones, NWI,
FEMA floodplains, RIBITS mitigation lands, NLCD water and wetlands, PAD-US style
protected lands, roads, railroads, buildings, transmission corridors, oil and gas
pipeline rights-of-way, elevation, and slope.

### 2. Favorability features must be traceable to the report input table

The report's random-forest training and suitability aggregation reference these
feature families:

- natural gas service coverage
- substation proximity
- operating generator proximity
- onshore fiber proximity
- retired generator proximity
- land fair market value
- data center construction labor
- transmission proximity above 135 kV
- planned generator proximity
- natural hazard building loss rate
- gas pipeline proximity
- projected cooling degree days for 2035
- NERC reserve margin
- construction cost
- residential electricity rate
- electricity service territory count
- water availability

### 3. The site suitability method is part of the requirement, not just the data

The report describes:

- a unified 5.76 km by 5.76 km grid
- characterization then normalization to a 0-1 range
- site suitability via weighted aggregation
- random-forest-derived feature importance using existing data center locations
- a positive-unlabeled learning framing for the training problem

The LinkedIn Part I description sharpens the method requirements further:

- reVeal must be able to systematically disaggregate lower-resolution inputs such as
    county- or state-level data using other spatial datasets
- the model is trained on existing data center locations to learn the
    characteristics of where data centers are built
- feasible land is weighted with machine learning, then scored and ranked across a
    nationwide surface

### 4. The downscaling assumptions are part of the requirement

The report-level outputs use these explicit assumptions:

- EER high data center regional projections through 2050
- 88% utilization factor for load-to-capacity conversion
- 2025 initial locations from Baxtel
- a maximum 1 GW per site per time-step

The LinkedIn Part II description adds these downscaling details:

- regional EER data center load projections are methodically distributed to the
    suitability surface
- the scenario begins with operating data centers in 2025
- modeled buildout is cumulative over the next 25 years
- existing and modeled data centers are shown aggregated to a 5 km grid

### 5. Report-layer outputs are required deliverables

The report shows these output classes, not just intermediate datasets:

- map of land feasible for data centers
- suitability percentile map
- downscaled deployment results through 2050
- limitations and fidelity notes for missing local constraints

The LinkedIn Part I description sharpens the report-layer deliverables to include:

- a high-resolution national-scale output showing where data centers are likely to
    be built
- a scored and ranked nationwide suitability surface derived from the trained model

The LinkedIn Part II description sharpens the report-layer deliverables to include:

- a cumulative buildout view over time, not just one end-state map
- animation-ready or time-stepped 5 km grid outputs for existing and modeled data
    centers

### 6. Scenario control, integration targets, and limitations are part of the requirement

The LinkedIn Part II description makes two additional constraints explicit:

- report generation should be driven by named assumptions and scenario choices that
    a user can control
- generated reports must carry forward the known limitations and candidate future
    refinements rather than hiding them

The LinkedIn Part I description adds one downstream integration target:

- reVeal outputs are expected to support integration with ReEDS for high-resolution
    load forecasting in advanced power systems modeling

Named future refinements called out in the LinkedIn text include:

- local transmission hosting capacity
- demand queue times
- zoning information
- permitting and ordinance information
- more representative or realistically scaled capacity by market trends
- social acceptance

## Current High-Level Coverage

The repo already has public or proxy workflows for a subset of these needs,
including NWI, FEMA NFHL, PAD-US, NLCD, RIBITS, transmission and substations,
fiber, gas service territories, land-value proxy, construction-cost proxy, water
proxy, NERC reserve margins, URDB, and public EER load generation.

## Remaining High-Level Gaps

The report introduces or sharpens requirements that are not yet fully tracked in the
backlog:

- full exclusion-layer parity against the report's feasibility slide
- feature parity for generator proximity, hazard loss, cooling degree days,
  electricity territory count, and data center construction labor
- random-forest weight reproduction or a bounded public approximation policy
- report-oriented output generation and validation, not just intermediate layer prep
- national scored-and-ranked suitability outputs that reflect the trained model
- scenario-controlled, time-stepped 5 km buildout outputs suitable for map or
    animation generation
- ReEDS-facing interoperability for high-resolution load forecasting outputs
- explicit limitation carry-forward for missing local hosting, queue, zoning,
    permitting, capacity-scaling, and social-acceptance factors

The detailed row-level status behind those gaps is now tracked in
`external-data/provenance/data-center-siting-parity-matrix.md`.