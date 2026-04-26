# EER Public Downscale Smoke Test

- Runner: `python external-data/derived/eer/run_downscale_smoke.py`
- Validated config: `external-data/derived/eer/config_public_total_smoke.json`
- Validated output path: `external-data/derived/eer/downscale-smoke/public_eer_total_downscaled.gpkg`
- Validated config: `external-data/derived/eer/config_public_regional_smoke.json`
- Validated output path: `external-data/derived/eer/downscale-smoke/public_eer_regional_downscaled.gpkg`

## What was tested

The total downscale workflow was run end to end on the existing test grid using the
generated public EER national projection CSV:

- `external-data/derived/eer/eer_public_central_high_data_center_national.csv`

The smoke test completed successfully and wrote a GeoPackage with 105,336 rows.

The grouped regional downscale workflow was also run end to end on the existing test
grid using the generated public EER region-group projection CSV:

- `external-data/derived/eer/eer_public_central_high_data_center_region_groups.csv`

That smoke test completed successfully and wrote a GeoPackage with 94,253 rows.
The output is long-form rather than wide-form, with `year`, `total_dc_load_mw`, and
`new_dc_load_mw` columns populated for years 2022, 2024, 2030, 2035, 2040, 2045,
and 2050.

These smoke tests validate execution compatibility of the public EER outputs through
the repo's downscale workflow. They do **not** validate magnitude parity with the
shipped fixture projections, which is explicitly out of scope for the public-source
alternative path.

## Why the runner exists

On macOS, the downscale implementation uses multiprocessing. Running the workflow from
an inline `python - <<'PY'` snippet causes worker respawn to fail because the spawned
process cannot reload `<stdin>` as `__main__`. The file-backed runner avoids that local
execution issue and gives a repeatable smoke-test command.