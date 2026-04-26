# Public Power Infrastructure Baseline

- Generator command:
  `python -m reVeal.public_data generate-power-infrastructure-baseline`
- Expected raw payload paths:
  - `external-data/raw/power/osm_transmission_lines.json`
  - `external-data/raw/power/osm_substations.json`
- Expected derived outputs:
  - `external-data/derived/power/public_transmission_lines_135kv.gpkg`
  - `external-data/derived/power/public_substations.gpkg`

## Intended scope

This workflow produces a first-pass public approximation of the power-infrastructure
inputs used for substation proximity and transmission-line proximity.

It is not an exact replacement for a curated transmission model.

## Current acquisition posture

The transform is implemented in code, but acquisition is currently handled as manual
payload export rather than a live Overpass fetch inside the repo workflow.

The repo can now stage local note files for the two OSM input surfaces with:

- `python -m reVeal.public_data stage-dataset transmission_lines_osm_export --repo-root .`
- `python -m reVeal.public_data stage-dataset substations_osm_export --repo-root .`

That decision is deliberate:

- Query-service behavior can vary, and the repo should not depend on fragile live
  calls for repeatable tests.
- The first pass should establish a reproducible national baseline before layering in
  optional utility or federal supplements.

The repo therefore treats this as a payload-driven workflow:

1. Export OSM power-line features from Overpass into JSON.
2. Export OSM substation features from Overpass into JSON.
3. Run the generator command to normalize, filter, and write the derived layers.

## Filtering rules

- Transmission-line candidates are limited to OSM features tagged as
  `power=line`, `power=minor_line`, or `power=cable`.
- Voltage tags are normalized to kilovolts.
- When multiple voltage values are present, the repo keeps the maximum parsed value.
- The high-voltage transmission layer only keeps features whose parsed
  `max_voltage_kv` is at least `135`.
- Features without a parsable voltage tag are excluded from the high-voltage line
  layer to avoid false positives.
- The substation layer keeps OSM `power=substation` features and preserves both the
  normalized `substation_type` tag and any parsed `max_voltage_kv` value.

## Non-equivalence versus a curated transmission model

This public baseline should be treated as a weaker approximation than a utility-grade
transmission dataset.

Known limitations:

- OSM voltage tagging is incomplete, so some real high-voltage lines will be absent.
- Substation attributes such as voltage class, capacity, and planned status are often
  sparse or missing.
- The first pass uses exported OSM payloads only; utility GIS and federal line
  inventories are not yet folded into the derived layer.
- Underground cable classification and power tagging can vary by editor and region.