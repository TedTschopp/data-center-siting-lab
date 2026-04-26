# Public Land Value Proxy Workflow

- Generator command:
  `python -m reVeal.public_data generate-land-value-proxy-features`
- Expected raw workflow inputs:
  - `external-data/raw/land/county_land_value_proxy.csv`
  - `external-data/raw/land/county_land_value_counties.gpkg`
- Supporting transformation input:
  - the target EMM-zone geometry layer
- Expected derived outputs:
  - `external-data/derived/land/public_land_value_county.gpkg`
  - `external-data/derived/land/public_land_value_emm_zone.gpkg`

## Selected source

The first-pass proxy source is a county-level land-value table built from public
assessor parcel summaries or another county-scale public land-value proxy collapsed to
one numeric value per county.

The repo expects a local CSV with at least:

- `county_id`
- `state`
- `land_value_proxy_usd_per_acre`

The county polygon layer must provide matching `county_id` values and polygon
geometry.

## Transformation method

The repo treats land value as a county proxy surface first and then carries two
signals forward:

1. the raw county proxy value
2. a within-state `state_land_value_index`

That workflow is explicit:

1. Normalize county IDs and state labels.
2. Join the county proxy CSV to the county polygon layer.
3. Compute `state_land_value_index` as a within-state percentile-style rank.
4. Area-weight both the raw proxy and normalized index into the repo's EMM zones.
5. Write the county and EMM-zone GeoPackages.

## Current acquisition posture

The repo can stage the local input-schema note with:

- `python -m reVeal.public_data stage-dataset county_land_value_proxy_inputs --repo-root .`

This remains a payload-driven workflow rather than a live API or service call.

## Non-equivalence versus national land-market comparability

This workflow should be treated as a public approximation.

Known limitations:

- No harmonized national open land-value dataset exists for exact parity.
- County assessor and parcel valuation methods vary widely across jurisdictions.
- Raw proxy values should not be treated as directly comparable across states.
- `state_land_value_index` is only intended for within-state comparison.
- The EMM-zone output smooths county variation through overlap-area weighting and is a
  screening proxy rather than an exact land fair-market-value surface.