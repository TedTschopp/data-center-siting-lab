# Public Construction Cost Proxy Workflow

Before running the generator, the repo can stage the input-schema note with:

```bash
python -m reVeal.public_data stage-dataset county_construction_cost_proxy_inputs --repo-root .
```

Generate the first-pass construction-cost proxy outputs with:

```bash
python -m reVeal.public_data generate-construction-cost-proxy-features \
  --county-proxy-csv external-data/raw/construction/county_construction_cost_proxy.csv \
  --county-polygons external-data/raw/construction/county_construction_cost_counties.gpkg \
  --regions tests/data/downscale/inputs/regions/eer_adp_zones.gpkg \
  --output-dir external-data/derived/construction
```

The command writes:

- `public_construction_cost_county.gpkg`
- `public_construction_cost_emm_zone.gpkg`

Input expectations:

- The county proxy CSV contains at least `county_id`, `state`,
  `construction_worker_mean_wage_usd`, and `regional_price_parity_index`.
- The county polygon layer provides matching `county_id` values and geometry.
- The regions layer provides the target EMM-zone geometry.

This workflow is a public approximation and is explicitly non-equivalent to a
dollars-per-MW construction-cost model. The derived `construction_cost_proxy_score`
is a wage-and-price proxy, and `construction_cost_relative_index` is normalized to the
national mean rather than to a presentation-equivalent CAPEX benchmark.