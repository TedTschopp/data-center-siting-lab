# Public Water Availability Proxy Workflow

- Generator command:
  `python -m reVeal.public_data generate-water-availability-proxy-features`
- Expected raw workflow input:
  - `external-data/raw/water/usgs_state_water_use_proxy.csv`
- Supporting transformation inputs:
  - a workbook containing the `Mapping zone to county` sheet used for state-to-zone
    weighting
  - the target EMM-zone geometry layer
- Expected derived outputs:
  - `external-data/derived/water/public_water_availability_state_proxy.csv`
  - `external-data/derived/water/public_water_availability_emm_zone.gpkg`

## Selected source

The first-pass proxy source is a state-level USGS-style freshwater withdrawal table.

The repo expects a local CSV with at least:

- `state`
- `freshwater_withdrawal_mgd`

Optional columns such as `source_year` and `source_note` can be preserved in the raw
input CSV, but the core transform only requires the state label and numeric proxy
value.

## Transformation method

The repo treats state freshwater withdrawal as a coarse public proxy for water-system
capacity and then apportions it into the repo's EMM zones using the existing
state-to-zone area-share weights already derived from the EER mapping workbook.

That workflow is explicit:

1. Normalize the state proxy CSV.
2. Read the `Mapping zone to county` workbook sheet.
3. Reuse the repo's state-to-zone weighting logic.
4. Apportion state proxy values into EMM zones.
5. Write the cleaned state proxy CSV and an EMM-zone GeoPackage.

## Current acquisition posture

The repo can stage the local input-schema note with:

- `python -m reVeal.public_data stage-dataset usgs_state_water_use_proxy_csv --repo-root .`

This remains a payload-driven workflow rather than a live API or service call.

## Non-equivalence versus site-level water availability

This workflow should be treated as a public approximation.

Known limitations:

- State withdrawal totals are not the same thing as site-level water availability.
- The transformation uses state-to-zone area shares, which smooths local variation.
- The proxy measures observed withdrawal capacity or intensity, not a literal total
  water-availability surface.
- The chosen source is useful for a first pass, but it does not replicate the
  presentation's uncited water-availability feature exactly.