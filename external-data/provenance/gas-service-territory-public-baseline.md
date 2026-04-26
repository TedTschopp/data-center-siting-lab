# Public Gas Service Territory Workflow

- Generator command:
  `python -m reVeal.public_data generate-gas-service-territory-baseline`
- Expected raw workflow input:
  - `external-data/raw/gas/state_gas_service_territories.csv`
- Expected derived outputs:
  - `external-data/derived/gas/public_gas_service_territories.gpkg`
  - `external-data/derived/gas/public_gas_service_territories_state_index.csv`

## Intended scope

This workflow produces a first-pass public assembly of gas service territory polygons
from manually sourced state extracts.

It does not claim that a clean national open gas service-territory layer already
exists.

## Current acquisition posture

The repo now treats this as a state-by-state assembly problem rather than a single
national download.

The repo can stage the local manifest-schema note with:

- `python -m reVeal.public_data stage-dataset state_gas_service_territory_manifest --repo-root .`

That staged note defines the expected CSV manifest and makes the workflow explicit:

1. Collect a state service-territory extract from a public source.
2. Save the local geospatial file.
3. Add one row to the manifest with the state code, local path, and optional utility
   name field.
4. Run the generator command to merge the current set of state extracts into one
   assembled territory layer and a state-index summary.

## Manifest schema

Required columns in `state_gas_service_territories.csv`:

- `state`
- `path`

Optional columns:

- `utility_field`

The `path` value may be absolute or relative to the manifest file.

## Non-equivalence versus a national authoritative layer

This workflow should be treated as a state-assembly baseline, not a proof that public
national coverage is complete.

Known limitations:

- Completeness depends entirely on which state sources are collected and normalized.
- State public service commission data formats vary widely.
- Utility name fields are inconsistent and may be absent.
- The merged layer is suitable as a first-pass polygon coverage proxy, not as a claim
  of exact national service-territory parity.