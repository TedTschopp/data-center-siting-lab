# Public Data Center Baseline

- Generator command:
  `python -m reVeal.public_data generate-data-center-baseline`
- Expected raw payload paths:
  - `external-data/raw/data-centers/osm_data_centers.json`
  - `external-data/raw/data-centers/wikidata_data_centers.json`
  - `external-data/raw/data-centers/manual_data_centers.csv` (optional)
- Expected derived outputs:
  - `external-data/derived/data-centers/public_data_center_baseline.csv`
  - `external-data/derived/data-centers/public_data_center_baseline.gpkg`

## Intended scope

This workflow produces a first-pass public approximation of existing,
under-construction, and planned data center sites.

It is not an exact replacement for the Baxtel inventory cited in the presentation.

## Current acquisition posture

The transform is implemented in code, but acquisition is currently handled as manual
payload export rather than a live API fetch inside the repo workflow.

The repo can now stage local note files for those three input surfaces with:

- `python -m reVeal.public_data stage-dataset data_center_osm_export --repo-root .`
- `python -m reVeal.public_data stage-dataset data_center_wikidata_export --repo-root .`
- `python -m reVeal.public_data stage-dataset data_center_manual_augmentation --repo-root .`

That decision is deliberate:

- OpenStreetMap and Wikidata are public, but query-service behavior can vary and the
  repo should not depend on fragile live calls for repeatable tests.
- Operator announcements and permitting rows are inherently manual curation inputs in
  this first pass.

The repo therefore treats the baseline as a payload-driven merge workflow:

1. Export OSM data center features from an Overpass query into JSON.
2. Export a Wikidata SPARQL result into JSON.
3. Optionally add a manual CSV for rows that come from operator announcements or
   permitting records.
4. Run the generator command to normalize, dedupe, and write the baseline layer.

## Manual CSV schema

The optional manual augmentation CSV must contain:

- `name`
- `latitude`
- `longitude`
- `site_status`

It may also contain:

- `operator`
- `wikidata_id`
- `source_url`
- `source_note`

Accepted `site_status` values normalize to the repo vocabulary:

- `existing`
- `under_construction`
- `planned`

## Merge behavior

- OSM rows are normalized from exported element payloads, including node coordinates
  or feature centers.
- Wikidata rows are normalized from exported SPARQL JSON with point geometry.
- Manual rows are added as additional point records.
- Rows are deduped primarily by `wikidata_id` when present, otherwise by normalized
  site name plus rounded coordinates.
- The merged baseline keeps provenance fields such as `sources`, `source_count`,
  `source_ids`, `source_url`, and `source_note`.

## Non-equivalence versus Baxtel

This public baseline should be treated as a weaker approximation than Baxtel.

Known limitations:

- Coverage of planned and under-construction sites is incomplete.
- Operator names and lifecycle states may be sparse or inconsistent across sources.
- Public query exports can miss sites that are known commercially but not mapped or
  structured openly.
- Manual augmentation remains necessary for better planned-site coverage.