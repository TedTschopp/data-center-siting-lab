# Public Water Availability Proxy Workflow

Before running the generator, the repo can stage the input-schema note with:

```bash
python -m reVeal.public_data stage-dataset usgs_state_water_use_proxy_csv --repo-root .
```

Generate the first-pass water proxy outputs with:

```bash
python -m reVeal.public_data generate-water-availability-proxy-features \
  --state-proxy-csv external-data/raw/water/usgs_state_water_use_proxy.csv \
  --mapping-workbook path/to/workbook.xlsx \
  --regions tests/data/downscale/inputs/regions/eer_adp_zones.gpkg \
  --output-dir external-data/derived/water
```

The command writes:

- `public_water_availability_state_proxy.csv`
- `public_water_availability_emm_zone.gpkg`

Input expectations:

- The state proxy CSV contains at least `state` and `freshwater_withdrawal_mgd`.
- The workbook provides the `Mapping zone to county` sheet used for state-to-zone
  weights.
- The regions layer provides the target EMM-zone geometry.

This workflow is a public approximation and is explicitly non-equivalent to literal
site-level water availability.