# Public Construction Cost Proxy Workflow

- Generator command:
  `python -m reVeal.public_data generate-construction-cost-proxy-features`
- Expected raw workflow inputs:
  - `external-data/raw/construction/county_construction_cost_proxy.csv`
  - `external-data/raw/construction/county_construction_cost_counties.gpkg`
- Supporting transformation input:
  - the target EMM-zone geometry layer
- Expected derived outputs:
  - `external-data/derived/construction/public_construction_cost_county.gpkg`
  - `external-data/derived/construction/public_construction_cost_emm_zone.gpkg`

## Selected source

The first-pass proxy source is a county-level table assembled from public labor and
regional price inputs, such as BLS QCEW construction wages, Census LEHD labor
context, and BEA Regional Price Parities collapsed to one wage and one price signal
per county.

The repo expects a local CSV with at least:

- `county_id`
- `state`
- `construction_worker_mean_wage_usd`
- `regional_price_parity_index`

The county polygon layer must provide matching `county_id` values and polygon
geometry.

## Transformation method

The repo treats construction cost as a county wage-and-price proxy surface first and
then carries four signals forward:

1. the raw county wage proxy
2. the raw county price proxy
3. the derived `construction_cost_proxy_score`
4. the derived `construction_cost_relative_index`

That workflow is explicit:

1. Normalize county IDs and state labels.
2. Join the county proxy CSV to the county polygon layer.
3. Compute `construction_cost_proxy_score` as
   `construction_worker_mean_wage_usd * regional_price_parity_index / 100`.
4. Normalize that score to `construction_cost_relative_index` by dividing by the
   national mean proxy score.
5. Area-weight wage, price, proxy score, and relative index into the repo's EMM
   zones.
6. Write the county and EMM-zone GeoPackages.

## Current acquisition posture

The repo can stage the local input-schema note with:

- `python -m reVeal.public_data stage-dataset county_construction_cost_proxy_inputs --repo-root .`

This remains a payload-driven workflow rather than a live API or service call.

## Non-equivalence versus dollars-per-MW construction cost

This workflow should be treated as a public approximation.

Known limitations:

- No public national dataset reproduces data center dollars-per-MW construction cost
  directly.
- The proxy formula measures labor-cost pressure and regional price burden, not total
  project CAPEX.
- County inputs may rely on mixed-resolution public sources, including state or metro
  price parity assigned down to counties.
- The EMM-zone output smooths county variation through overlap-area weighting and is a
  screening proxy rather than an exact construction-cost estimate.