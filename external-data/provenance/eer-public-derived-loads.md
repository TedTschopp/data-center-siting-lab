# EER Public Derived Load Projections

- Generator module: `python -m reVeal.public_data generate-eer-loads`
- Source workbook: `external-data/unpacked/eer/ADP2024_detailed_output_data.xlsx`
- Region geometry: `tests/data/downscale/inputs/regions/eer_adp_zones.gpkg`
- Output directory: `external-data/derived/eer`

## Method

The current transform uses the public EER `Final energy demand` sheet and sums the
`CENTRAL HIGH DATA CENTER` scenario values for:

- `data center cooling`
- `data center it`

Only `Final Energy == electricity` rows are used.

The transform then:

1. Converts annual `mmBtu` to average `MW` using `0.29307107 / 8760`.
2. Builds state-to-`emm_zone` weights from county area shares in the EER `Mapping zone
   to county` sheet.
3. Aggregates those zonal results to the repo's `zone_group` values.
4. Limits the generated national totals to states represented by the repo's
   `emm_zone` geometry so that the national, zonal, and grouped outputs reconcile on
   the same footprint.

## Caveat

This produces CSVs that fit the `reVeal` projection schemas, but it does not recreate
the shipped fixture magnitudes exactly. The generated files should be treated as
reproducible public-source alternatives, not exact reproductions of the original case
study inputs.

## Magnitude-validation guidance

Exact magnitude parity with the shipped fixture CSVs is **not** an expected outcome
for this workflow.

At the shared national years in the current repo state, the derived public totals are
roughly `10.8%` to `18.7%` of the shipped fixture totals. That gap is large enough to
disqualify fixture-magnitude matching as a pass/fail criterion for the public EER
path.

The public EER workflow should therefore be validated against these criteria instead:

1. Schema compatibility: the generated CSVs must match the field shapes expected by
   the `reVeal` downscale configs.
2. Footprint consistency: the national, zonal, and grouped outputs must reconcile on
   the same EMM-zone footprint.
3. Directional reasonableness: the scenario should preserve a coherent growth trend
   across the projected years rather than oscillating unpredictably.
4. Executable compatibility: the generated outputs must run successfully through the
   documented smoke-test downscale workflows.

In other words: validate that the public-source alternative is internally coherent and
operationally usable, not that it numerically reproduces the original proprietary or
uncited case-study magnitudes.