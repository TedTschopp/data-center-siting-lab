# Public EER Derived Projections

These CSVs are generated from the unpacked public EER workbook with:

```bash
python -m reVeal.public_data generate-eer-loads \
  --workbook external-data/unpacked/eer/ADP2024_detailed_output_data.xlsx \
  --regions tests/data/downscale/inputs/regions/eer_adp_zones.gpkg \
  --output-dir external-data/derived/eer
```

The output files mirror the CSV shapes expected by `reVeal` downscale configs:

- `eer_public_central_high_data_center_national.csv`
- `eer_public_central_high_data_center_regional.csv`
- `eer_public_central_high_data_center_region_groups.csv`

They are public-source alternatives derived from EER `Final energy demand` rows for
`data center cooling` and `data center it`, converted from annual `mmBtu` to average
`MW` and apportioned from states into `emm_zone` and `zone_group` using area shares
from the EER `Mapping zone to county` sheet.

Smoke-test config copies are also provided:

- `config_public_total_smoke.json`
- `config_public_regional_smoke.json`

These configs point the standard downscale workflow at the generated public EER CSVs
while keeping the existing test grid and regional geometry as the execution surface.

To run the validated total smoke test:

```bash
python external-data/derived/eer/run_downscale_smoke.py \
  external-data/derived/eer/config_public_total_smoke.json \
  --output external-data/derived/eer/downscale-smoke/public_eer_total_downscaled.gpkg
```

The smoke-test GeoPackage is intentionally ignored by git because it is a generated
validation artifact rather than a source input.

The grouped regional smoke test has also been validated locally:

```bash
python external-data/derived/eer/run_downscale_smoke.py \
  external-data/derived/eer/config_public_regional_smoke.json \
  --output external-data/derived/eer/downscale-smoke/public_eer_regional_downscaled.gpkg
```

That run writes a long-form GeoPackage with `year`, `total_dc_load_mw`, and
`new_dc_load_mw` columns populated across the projected years.

Magnitude guidance:

- Treat these CSVs as schema-compatible public alternatives, not fixture-magnitude
  replacements.
- In the current repo state, the derived public national totals are only about
  `10.8%` to `18.7%` of the shipped fixture national totals at the shared years.
- Use schema compatibility, internal trend coherence, and successful smoke-test runs
  as the acceptance criteria for this public EER path.