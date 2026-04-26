# NERC 2025 LTRA Provenance

- Source page: https://www.nerc.com/pa/RAPA/ra/Pages/default.aspx
- Direct report URL verified during implementation: https://www.nerc.com/globalassets/our-work/assessments/nerc_ltra_2025.pdf
- Repo-local staged file: `external-data/raw/nerc/nerc_ltra_2025.pdf`

## Intended use

This report is the public reference for the reserve-margin feature cited in the
presentation workflow.

## Implemented source decision

The implemented workflow uses Table 2 in the staged 2025 LTRA PDF as the numeric
source surface for anticipated reserve margin (`ARM`) and reference margin level
(`RML`) values across the 2026-2030 horizon. A supplemental workbook was not required
for the current transform.

## Implemented transform

- Source table transcription lives in `reVeal.public_data.build_nerc_reserve_margin_table`.
- Annual headroom is defined as `ARM - RML` for each year from 2026 through 2030.
- The conservative derived feature used for downstream scoring is
  `min_margin_headroom_2026_2030`.
- NERC assessment areas are mapped into the repo's `emm_zone` geometry through a
  repo-local crosswalk in `reVeal.public_data`.
- The optional grid feature is produced by area-weighted transfer from the EMM-zone
  feature layer and only includes cells that overlap the mapped study area.

The assessment-area table keeps the full transcribed NERC rows. The EMM-zone and grid
artifacts only use the assessment areas that map into the repo's U.S. EMM-zone
geometry.

## Generated artifacts

- `external-data/derived/nerc/nerc_ltra_2025_assessment_area_margins.csv`
- `external-data/derived/nerc/nerc_ltra_2025_emm_zone_margins.gpkg`
- `external-data/derived/nerc/nerc_ltra_2025_grid_margins.gpkg`

## Generation command

```bash
python -m reVeal.public_data generate-nerc-reserve-margin-features \
  --regions tests/data/downscale/inputs/regions/eer_adp_zones.gpkg \
  --grid tests/data/downscale/inputs/grid_char_weighted_scores.gpkg \
  --output-dir external-data/derived/nerc
```