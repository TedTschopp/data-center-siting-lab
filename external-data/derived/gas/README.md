# Public Gas Service Territory Workflow

Before running the generator, the repo can stage the manifest-schema note with:

```bash
python -m reVeal.public_data stage-dataset state_gas_service_territory_manifest --repo-root .
```

Generate the first-pass assembled gas territory layer with:

```bash
python -m reVeal.public_data generate-gas-service-territory-baseline \
  --manifest-csv external-data/raw/gas/state_gas_service_territories.csv \
  --output-dir external-data/derived/gas
```

The command writes:

- `public_gas_service_territories.gpkg`
- `public_gas_service_territories_state_index.csv`

Input expectations:

- The manifest CSV contains one row per state extract.
- Each row must include `state` and `path`.
- `utility_field` is optional and can point to the source attribute that holds the
  utility or provider name.

This workflow is a public approximation and is explicitly state-source dependent.