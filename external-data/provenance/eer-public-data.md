# EER Public Data Provenance

- Source landing page: https://www.evolved.energy/us-adp-2024
- Source artifact label on landing page: `Data` (`XLSX`)
- Local download used during research: `/Users/tedtschopp/Downloads/eer-public-data.zip`
- Repo-local staged raw file: `external-data/raw/eer/eer-public-data.zip`
- Repo-local unpacked files:
  - `external-data/unpacked/eer/ADP2024_detailed_output_data.xlsx`
  - `external-data/unpacked/eer/U.S._2024_ADP_RIO_data_input_catalog.xlsx`

## Archive contents verified

The archive was listed locally and contains:

- `ADP2024_detailed_output_data.xlsx`
- `U.S._2024_ADP_RIO_data_input_catalog.xlsx`

## Notes

- The public output workbook includes data-center strings such as `central high data center`,
  `data center cooling`, and `data center it`.
- This confirms the package is relevant to the data center case study.

## Validation outcome

The drop-in assessment has now been run with:

- `python -m reVeal.public_data assess-eer-drop-in`

Verdict:

- The public workbook is **not** a direct drop-in replacement for the exact load
  projection inputs expected by `reVeal` downscaling configs.
- The source is an XLSX workbook, while the configs reference CSV load-projection
  files.
- The `Final energy demand` sheet does not directly provide the required projection
  columns `year`, `dc_load_mw`, or `zone_group`.
- Grouped regional projections require the workbook's county-to-zone mapping plus the
  repo's regional geometry to derive `zone_group` results.
- The generated public EER national and region-group CSVs do match the required
  projection schemas and remain the supported public-source alternative.

## Schema anchors used in the assessment

The workbook was compared against these local schema anchors:

- `tests/data/downscale/config_total.json`
- `tests/data/downscale/config_regional.json`
- `tests/data/downscale/inputs/load_growth_projections/eer_us-adp-2024-central_national.csv`
- `tests/data/downscale/inputs/load_growth_projections/eer_us-adp-2024-central_region_groups.csv`
