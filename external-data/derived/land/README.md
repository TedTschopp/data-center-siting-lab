# Public Land Value Proxy Workflow

Before running the generator, the repo can stage the input-schema note with:

```bash
python -m reVeal.public_data stage-dataset county_land_value_proxy_inputs --repo-root .
```

Generate the first-pass land-value proxy outputs with:

```bash
python -m reVeal.public_data generate-land-value-proxy-features \
  --county-proxy-csv external-data/raw/land/county_land_value_proxy.csv \
  --county-polygons external-data/raw/land/county_land_value_counties.gpkg \
  --regions tests/data/downscale/inputs/regions/eer_adp_zones.gpkg \
  --output-dir external-data/derived/land
```

The command writes:

- `public_land_value_county.gpkg`
- `public_land_value_emm_zone.gpkg`

Input expectations:

- The county proxy CSV contains at least `county_id`, `state`, and
  `land_value_proxy_usd_per_acre`.
- The county polygon layer provides matching `county_id` values and geometry.
- The regions layer provides the target EMM-zone geometry.

This workflow is a public approximation and is explicitly non-equivalent to a
harmonized national land fair-market-value dataset. The normalized
`state_land_value_index` is only intended for within-state comparison.