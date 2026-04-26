# Data Center Bundle Deviations

## Bottom Line

The current report bundle is a bounded public approximation of the data center
siting report workflow. It is useful for executive screening, coworker review,
workflow validation, and gap discussion. It is not a report-equivalent
reproduction and should not be used as investment-grade site evidence without the
missing source data and methodology recovery steps below.

## Exact Vs Current Bundle

| Area | Exact report expectation | Current bundle behavior | Status |
| --- | --- | --- | --- |
| Source report requirements | Reproduce the report concepts and outputs from the original source workflow. | Requirements are summarized in tracked provenance, then mapped to public-source approximation outputs. | Bounded |
| Grid | Use the report-reference 5.76 km national grid, with related 5 km aggregation language called out separately. | Keeps the current execution grid as the internal model and documents the measured resolution mismatch. | Parity blocked |
| Baseline year | Start from 2025 operating data centers and build through the report horizon. | Records the configured 2022 starting-stock field and exposes the mismatch in the assumption registry. | Parity blocked |
| Baxtel and trained suitability | Use licensed Baxtel data and the report's trained suitability surface. | Uses a public data center baseline plus a Baxtel schema contract. The current suitability surface comes from the existing `suitability_score` field. | Parity blocked |
| Allocation | Apply the exact report allocation method over the trained suitability surface. | Uses the current weighted-bootstrap downscale behavior and records allocation assumptions explicitly. | Bounded |
| Feasible-land exclusions | Apply the exact report exclusion stack and preprocessing rules. | Keeps developable cells, flags high water/wetland share cells, and clamps excluded cells to 0 percent suitability rather than dropping them. | Bounded |
| Cell naming | Use report-quality place/site names suitable for executive review. | Uses Census coordinate GeoLookup where available, stable cell IDs for joins, and bounded fallback labels for misses. | Improved but bounded |
| Buildout timeline | Show modeled buildout across the report's temporal assumptions. | Builds cumulative load and capacity-equivalent outputs from the total and grouped regional smoke outputs. | Bounded |
| Risk proxies | Represent zoning, permitting, social acceptance, and hosting capacity with report-grade evidence. | Adds proxy overlays for zoning, permitting, social friction, and hosting capacity, with limitations preserved. | Context only |
| ReEDS handoff | Provide validated downstream integration products. | Writes a ReEDS integration contract with required products, columns, status fields, and validation checks. | Contract defined |

## Additions Made In This Repository

- Added `external-data/manifest` inventories for dataset sources, unresolved gaps,
  and public substitutes.
- Added provenance notes for each public substitute and report-facing workflow.
- Added public EER transformation and smoke-test workflows.
- Added public proxy workflows for data centers, power, fiber, gas, land,
  construction, water, and NERC reserve margin.
- Added runnable example-bundle staging and checkpointed public workflow execution.
- Added the bounded public report-bundle command.
- Added generated contract artifacts for temporal assumptions, capacity constraints,
  grid resolution, allocation, Baxtel schema readiness, and ReEDS handoff.
- Added Census-backed cell identity enrichment with cached responses and miss-review
  outputs.
- Added the Executive Siting and Buildout View HTML report with theme controls,
  square/hex display modes, risk overlays, priority candidates, and buildout
  timeline controls.
- Added regression coverage that checks report-bundle outputs, contracts, and HTML
  affordances.

## Appropriate Uses

- Executive screening and discussion of candidate geography.
- Coworker onboarding to the current public-data workflow.
- Testing report-bundle generation and documentation completeness.
- Comparing bounded public assumptions with future recovered source inputs.
- Scoping data acquisition, Baxtel procurement, and method-recovery work.

## Inappropriate Uses

- Claiming exact reproduction of the source report.
- Ranking individual parcels for acquisition or interconnection decisions.
- Treating proxy overlays as entitlement, permitting, community-acceptance, or
  hosting-capacity proof.
- Treating Census-backed cell labels as authoritative site names.
- Feeding downstream planning models without reviewing the ReEDS integration
  contract status fields.

## Next Parity Steps

1. Recover or procure the licensed Baxtel source data, schema, and 2025 operating
   baseline.
2. Recover the trained suitability surface and the exact model-training workflow.
3. Reconstruct or obtain the report-reference 5.76 km national grid.
4. Recover the exact allocation algorithm and compare it against the current
   weighted-bootstrap downscale behavior.
5. Replace proxy overlays with report-grade zoning, permitting, social acceptance,
   and hosting-capacity evidence where available.
6. Re-run the report-bundle contracts and update this deviation note before any
   claim of report-equivalent parity.
