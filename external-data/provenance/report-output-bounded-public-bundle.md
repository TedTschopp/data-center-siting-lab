# Report Output Bounded Public Bundle

This note records the current repo-local command surface for report-like outputs and
the deviations that still keep those outputs from being report-equivalent.

## Current Executable Bundle

The current repo can now materialize a bounded public approximation of the
report-output slice with:

```bash
python -m reVeal.public_data run-public-report-bundle \
  --output-dir external-data/derived/report-bundle
```

That report-facing bundle command nests the bounded reproduction workflow and
currently drives these validated steps:

- public EER projection generation
- bounded feasible-land GeoPackage generation from the execution grid, filtered to `developable_capacity_mw > 0` cells whose staged NLCD water/wetland share across classes `11`, `90`, and `95` remains below `0.5`
- bounded suitability-percentile GeoPackage generation from the execution grid
- bounded nationwide ranked suitability CSV generation from the bounded suitability layer, including deterministic human-readable cell names and gateway-place duplicate-name disambiguation without raw cell ids in the display label
- derived state-boundary GeoPackage generation from the official Census generalized state layer for bounded map context
- bounded zoning proxy GeoPackage generation from staged NLCD developed-land context, transferred onto the execution-grid cells as a coarse land-use overlay
- bounded hosting-capacity proxy GeoPackage generation from the existing NERC reserve-margin surface, transferred onto the execution-grid cells as a coarse regional overlay
- single-page D3 suitability map generation from the bounded feasible-land, suitability, state-boundary, zoning-proxy, and hosting-proxy layers, including hexagon display of grid-backed cells, table-to-map hover highlighting for ranked cells, and optional zoning-proxy and hosting-proxy overlay toggles
- machine-readable assumption registry generation for scenario-controlled outputs
- limitations carry-forward note generation for missing local constraints and future refinements
- machine-readable reVeal-to-ReEDS integration contract generation for bounded handoff validation
- total downscale smoke execution
- grouped regional downscale smoke execution
- NERC reserve-margin feature generation
- cumulative buildout GeoPackage generation for the total and grouped regional smoke outputs
- cumulative buildout summary CSV generation by source output and year
- report-bundle manifest emission
- report-bundle deviation-note emission

## Tracked Commands, Configs, And Outputs

<!-- markdownlint-disable MD060 -->

|                                         Output class | Current command or workflow                                                                                                                                                                                  | Config or input anchor                                                                                                                                                                                              | Current output                                                                                | Current validation                                                                  |
|-----------------------------------------------------:|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
|                       Public EER national projection | `python -m reVeal.public_data generate-eer-loads ...`                                                                                                                                                        | `external-data/unpacked/eer/ADP2024_detailed_output_data.xlsx`; `tests/data/downscale/inputs/regions/eer_adp_zones.gpkg`                                                                                            | `external-data/derived/eer/eer_public_central_high_data_center_national.csv`                  | Schema assessment plus `run-public-reproduction`                                    |
|               Public EER grouped regional projection | `python -m reVeal.public_data generate-eer-loads ...`                                                                                                                                                        | same as above                                                                                                                                                                                                       | `external-data/derived/eer/eer_public_central_high_data_center_region_groups.csv`             | Schema assessment plus `run-public-reproduction`                                    |
|                  Bounded feasible-land approximation | `python -m reVeal.public_data run-public-report-bundle --output-dir external-data/derived/report-bundle`                                                                                                     | `tests/data/downscale/inputs/grid_char_weighted_scores.gpkg`; `developable_capacity_mw > 0`; staged NLCD water/wetland share across classes `11`, `90`, and `95` must remain below `0.5`                         | `external-data/derived/report-bundle/public_report_feasible_land.gpkg`                        | focused pytest coverage plus `run-public-report-bundle`                             |
|         Bounded suitability-percentile approximation | `python -m reVeal.public_data run-public-report-bundle --output-dir external-data/derived/report-bundle`                                                                                                     | `tests/data/downscale/inputs/grid_char_weighted_scores.gpkg`; percentile rank of `suitability_score` on feasible cells; deterministic bounded place-name catalog lookup                                             | `external-data/derived/report-bundle/public_report_suitability_percentiles.gpkg`              | focused pytest coverage plus `run-public-report-bundle`                             |
|        Bounded nationwide ranked suitability summary | `python -m reVeal.public_data run-public-report-bundle --output-dir external-data/derived/report-bundle`                                                                                                     | derived from `public_report_suitability_percentiles.gpkg`, including numeric cell id, deterministic `cell_name`, `base_cell_name`, disambiguation flag, anchor-place metadata, candidate names, and selection basis | `external-data/derived/report-bundle/public_report_suitability_ranked_cells.csv`              | focused pytest coverage plus `run-public-report-bundle`                             |
|                 Derived state-boundary context layer | `python -m reVeal.public_data run-public-report-bundle --output-dir external-data/derived/report-bundle`                                                                                                     | official Census generalized state boundaries from `https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_state_20m.zip`, reprojected into the suitability layer CRS                                             | `external-data/derived/report-bundle/public_report_state_boundaries.gpkg`                     | focused pytest coverage plus `run-public-report-bundle`                             |
|                     Bounded zoning proxy layer | `python -m reVeal.public_data run-public-report-bundle --output-dir external-data/derived/report-bundle`                                                                                                     | staged NLCD land-cover raster sampled onto the execution-grid cells; developed classes are carried forward as a coarse zoning-context proxy rather than parcel zoning                                                   | `external-data/derived/report-bundle/public_report_zoning_proxy.gpkg`                         | focused pytest coverage plus `run-public-report-bundle`                             |
|             Bounded hosting-capacity proxy layer | `python -m reVeal.public_data run-public-report-bundle --output-dir external-data/derived/report-bundle`                                                                                                     | NERC reserve-margin assessment areas mapped into `tests/data/downscale/inputs/regions/eer_adp_zones.gpkg` and then transferred onto the execution-grid cells as a coarse regional headroom proxy                      | `external-data/derived/report-bundle/public_report_hosting_capacity_proxy.gpkg`               | focused pytest coverage plus `run-public-report-bundle`                             |
|                         Bounded suitability map page | `python -m reVeal.public_data run-public-report-bundle --output-dir external-data/derived/report-bundle`                                                                                                     | bounded feasible-land, suitability, state-boundary, zoning-proxy, and hosting-proxy surfaces embedded in one HTML page with D3; grid-backed cells display as hexagons while ranked rows bind back to the matching map cell by stable cell id                    | `external-data/derived/report-bundle/public_report_suitability_map.html`                      | focused pytest coverage plus `run-public-report-bundle`                             |
|                           Report assumption registry | `python -m reVeal.public_data run-public-report-bundle --output-dir external-data/derived/report-bundle`                                                                                                     | `external-data/derived/eer/config_public_total_smoke.json`; `external-data/derived/eer/config_public_regional_smoke.json`; bounded bundle rules                                                                     | `external-data/derived/report-bundle/public_report_assumption_registry.json`                  | focused pytest coverage plus `run-public-report-bundle`                             |
|                              Report limitations note | `python -m reVeal.public_data run-public-report-bundle --output-dir external-data/derived/report-bundle`                                                                                                     | LinkedIn limitation and refinement set carried forward through bounded bundle rules                                                                                                                                 | `external-data/derived/report-bundle/public_report_limitations.md`                            | focused pytest coverage plus `run-public-report-bundle`                             |
|                           ReEDS integration contract | `python -m reVeal.public_data run-public-report-bundle --output-dir external-data/derived/report-bundle`                                                                                                     | bounded bundle outputs, annual cumulative buildout artifacts, ranked suitability table, and current bundle assumptions                                                                                              | `external-data/derived/report-bundle/public_report_reeds_integration_contract.json`           | focused pytest coverage plus `run-public-report-bundle`                             |
|            Total downscaled deployment approximation | `python external-data/derived/eer/run_downscale_smoke.py external-data/derived/eer/config_public_total_smoke.json --output external-data/derived/eer/downscale-smoke/public_eer_total_downscaled.gpkg`       | `external-data/derived/eer/config_public_total_smoke.json`                                                                                                                                                          | `external-data/derived/eer/downscale-smoke/public_eer_total_downscaled.gpkg`                  | `external-data/provenance/eer-public-downscale-smoke.md`; `run-public-reproduction` |
| Grouped regional downscaled deployment approximation | `python external-data/derived/eer/run_downscale_smoke.py external-data/derived/eer/config_public_regional_smoke.json --output external-data/derived/eer/downscale-smoke/public_eer_regional_downscaled.gpkg` | `external-data/derived/eer/config_public_regional_smoke.json`                                                                                                                                                       | `external-data/derived/eer/downscale-smoke/public_eer_regional_downscaled.gpkg`               | `external-data/provenance/eer-public-downscale-smoke.md`; `run-public-reproduction` |
|              Total cumulative buildout approximation | `python -m reVeal.public_data run-public-report-bundle --output-dir external-data/derived/report-bundle`                                                                                                     | nested `external-data/derived/report-bundle/public_reproduction_status.json`; `external-data/derived/eer/downscale-smoke/public_eer_total_downscaled.gpkg`                                                          | `external-data/derived/report-bundle/public_eer_total_downscaled_cumulative_buildout.gpkg`    | focused pytest coverage plus `run-public-report-bundle`                             |
|   Grouped regional cumulative buildout approximation | `python -m reVeal.public_data run-public-report-bundle --output-dir external-data/derived/report-bundle`                                                                                                     | nested `external-data/derived/report-bundle/public_reproduction_status.json`; `external-data/derived/eer/downscale-smoke/public_eer_regional_downscaled.gpkg`                                                       | `external-data/derived/report-bundle/public_eer_regional_downscaled_cumulative_buildout.gpkg` | focused pytest coverage plus `run-public-report-bundle`                             |
|                     Cumulative buildout year summary | `python -m reVeal.public_data run-public-report-bundle --output-dir external-data/derived/report-bundle`                                                                                                     | derived from the cumulative buildout GeoPackages                                                                                                                                                                    | `external-data/derived/report-bundle/public_report_bundle_cumulative_buildout_summary.csv`    | focused pytest coverage plus `run-public-report-bundle`                             |
|                Report-bundle status and step outputs | `python -m reVeal.public_data run-public-report-bundle --output-dir external-data/derived/report-bundle`                                                                                                     | nested `external-data/derived/report-bundle/public_reproduction_status.json`                                                                                                                                        | `external-data/derived/report-bundle/public_report_bundle_status.json`                        | focused pytest coverage plus saved workflow status JSON                             |
|                               Report-bundle manifest | `python -m reVeal.public_data run-public-report-bundle --output-dir external-data/derived/report-bundle`                                                                                                     | `tests/data/downscale/inputs/grid_char_weighted_scores.gpkg`; nested reproduction status                                                                                                                            | `external-data/derived/report-bundle/public_report_bundle_manifest.json`                      | focused pytest coverage                                                             |
|                         Report-bundle deviation note | `python -m reVeal.public_data run-public-report-bundle --output-dir external-data/derived/report-bundle`                                                                                                     | current bounded-public policy and config assumptions                                                                                                                                                                | `external-data/derived/report-bundle/public_report_bundle_deviations.md`                      | focused pytest coverage                                                             |
|                        Human-readable status summary | `python -m reVeal.public_data summarize-public-workflow-status --status-path external-data/derived/report-bundle/public_report_bundle_status.json`                                                           | `external-data/derived/report-bundle/public_report_bundle_status.json`                                                                                                                                              | human-readable step summary                                                                   | CLI summary plus saved workflow status JSON                                         |

<!-- markdownlint-enable MD060 -->

## Current Human-Readable Cell Naming Rule

The bounded bundle now gives each ranked suitability cell a deterministic human-readable name.

The current rule is intentionally self-contained and offline so the bundle remains repeatable under test.

1. The repo uses a curated public catalog of major U.S. metropolitan names and major natural-feature or monument names with fixed `popularity_score` values to determine the core `base_cell_name`.
2. For each cell, the workflow selects the highest-popularity metro candidate and the highest-popularity natural-feature candidate that fall inside the cell polygon.
3. If a class has no in-cell candidate, the workflow falls back to the nearest catalog entry of that class using the cell representative point.
4. The final `base_cell_name` is the higher-popularity class winner; ties break by smaller centroid distance and then metro priority.
5. Separately, the workflow selects the nearest curated place anchor with official place, county, and state fields and computes the distance and bearing from that place to the cell representative point.
6. If two or more cells still share the same `base_cell_name`, the workflow rewrites the display names in a gateway-place style such as `5.6 miles South of Tusayan, Coconino County, AZ near Grand Canyon` while exposing `cell_name_is_disambiguated` and the anchor-place metadata in the outputs.
7. If two duplicate rows still collide after that first rewrite, the workflow increases distance precision and only falls back to coordinates as a last resort rather than exposing raw cell ids in the user-facing label.

That rule is reproducible, but it is still a bounded public approximation rather than a report-sourced naming layer.

## Current Hexagon Display Rule

The bounded D3 map now displays the grid-backed feasible, suitability, zoning-proxy,
and hosting-proxy cells as hexagons for browser review.

1. The underlying GeoPackages and embedded GeoJSON remain the original grid-cell
  geometries with stable `sc_point_gid` / `cell_id` keys.
2. The D3 page projects each original grid feature, computes the projected bounds and
  centroid, and draws a display-only hexagon fitted inside that cell footprint.
3. Table rows, tooltips, active highlighting, and optional overlay joins continue to
  use the original stable cell keys rather than the display geometry.
4. State-boundary context remains a stroke-only geographic overlay and is not
  converted to hexagons.

That display rule improves scanability without changing the internal grid model or
the downstream bundle artifacts.

## Current Feasible-Land Rule

The bounded bundle now carries one real exclusion-stack slice rather than relying only on `developable_capacity_mw > 0`.

1. The workflow starts from execution-grid cells where `developable_capacity_mw > 0`.
2. The workflow samples the staged NLCD land-cover raster onto those candidate cells.
3. The workflow computes `water_wetland_share` from NLCD classes `11` (open water), `90` (woody wetlands), and `95` (emergent herbaceous wetlands).
4. The bundle excludes cells whose `water_wetland_share` is at least `0.5` and keeps the surviving cells as `public_report_feasible_land.gpkg`.

That rule closes one report-aligned exclusion gap with staged public data, but it is still only one bounded slice of the broader exclusion stack described in the report.

It should not be described as a full reproduction of the report's feasibility exclusion workflow.

## Current State-Boundary Overlay Rule

The bounded D3 map now carries an explicit state-boundary context layer.

1. The workflow downloads the official Census generalized state-boundary ZIP from `cb_2024_us_state_20m.zip` when the cached copy is missing.
2. The derived state layer is normalized to `state_name`, `state_code`, and `geometry`, excludes Puerto Rico from the overlay, and is reprojected into the same CRS as the suitability surface before export.
3. The bundle writes that reprojected layer to `public_report_state_boundaries.gpkg` and embeds the same geometry into the D3 page as `stateBoundaryGeoJson`.
4. The map renders the state layer as a transparent stroke-only overlay above the suitability cells with pointer events disabled so hover behavior continues to target the suitability polygons.

That overlay improves orientation for quick review, but it remains contextual map framing rather than a claim of report-equivalent state-level methodology.

## Current Zoning Proxy Rule

The bounded D3 map now carries an optional zoning proxy overlay.

1. The workflow reads the staged NLCD land-cover raster from `external-data/raw/nlcd/` and samples the raster onto each feasible execution-grid cell in the current suitability surface.
2. The staged layer carries the dominant NLCD class, a readable `dominant_nlcd_label`, the share of developed pixels within each cell, and a derived `zoning_proxy_class`.
3. The bundle writes that derived layer to `public_report_zoning_proxy.gpkg` and embeds the same geometry into the D3 page as `zoningProxyGeoJson`.
4. The D3 page exposes a `Zoning Proxy` toggle and renders the overlay above the suitability cells with low-opacity class colors so it can be switched on without replacing the base suitability view.

That overlay reduces the old "no zoning context at all" gap, but it is still only a coarse developed-land context proxy.

It should not be described as parcel zoning, industrial zoning, or an allowed-use determination for a data-center site.

## Current Hosting Capacity Proxy Rule

The bounded D3 map now carries an optional hosting-capacity proxy overlay.

1. The workflow reads the repo's `tests/data/downscale/inputs/regions/eer_adp_zones.gpkg` layer and maps the existing NERC reserve-margin assessment-area values into that EMM-zone geometry.
2. The workflow transfers those zone-level values onto the current execution-grid cells with overlap weighting and writes the result to `public_report_hosting_capacity_proxy.gpkg`.
3. The staged layer carries `assessment_area`, `emm_zone`, `zone_group`, `min_margin_headroom_2026_2030`, `mean_margin_headroom_2026_2030`, and a derived `hosting_capacity_proxy_class` for map rendering.
4. The D3 page embeds the same layer as `hostingProxyGeoJson`, exposes a `Hosting Capacity Proxy` toggle, and renders the overlay above the suitability cells with low-opacity class colors so it can be switched on without replacing the base suitability view.

That overlay reduces the old "no hosting context at all" gap, but it is still only a coarse regional proxy.

It should not be described as local transmission hosting-capacity headroom or interconnection-ready capacity.

## Explicit Deviations From The Published Report

The current bounded public bundle is not report-equivalent for these reasons:

- The current downscale configs use `tests/data/downscale/inputs/grid_char_weighted_scores.gpkg`
  as the execution grid rather than a reproduced nationwide report surface.
- The current configs use a `baseline_year` of `2022`, while the report narrative
  and LinkedIn Part II description frame the scenario around operating data centers
  in `2025`.
- The current grid priority field is a pre-existing `suitability_score`, not a
  reproduced Baxtel-trained random-forest output from the report methodology.
- The current feasible-land output is a bounded approximation that keeps cells where
  `developable_capacity_mw > 0` and excludes cells whose staged NLCD water/wetland
  share across classes `11`, `90`, and `95` is at least `0.5`, rather than a fully
  reproduced exclusion stack from the report workflow.
- The current suitability-percentile output ranks the pre-existing
  `suitability_score` field on those bounded feasible cells, not a trained
  nationwide model surface.
- The current ranked suitability summary is therefore a bounded table derived from
  that same pre-existing score surface, not a report-equivalent learned ranking.
- The current zoning overlay is an NLCD developed-land context proxy, not a
  reproduced parcel-zoning or land-use-entitlement surface.
- The current hosting-capacity overlay is a regional NERC reserve-margin headroom
  proxy, not a reproduced local transmission hosting-capacity surface.
- The current assumption registry makes those bounded choices explicit, but it does
  not turn them into report-equivalent methodology.
- The current limitations note carries forward named refinement gaps, but those
  limitations remain active constraints on how the bundle should be interpreted.
- The current ReEDS integration contract validates bounded handoff structure and
  schema expectations, not report-equivalent or production-ready ReEDS parity.
- The current workflow validates downscaling mechanics and schema compatibility,
  not parity of learned weights or parity of nationwide siting predictions.

## Output Classes Still Not Reproduced

These report-layer outputs remain out of scope for the current bounded public
bundle:

- report-equivalent feasible-land map derived from a reproduced exclusion stack
- report-equivalent suitability percentile map derived from the trained nationwide model
- report-equivalent scored and ranked nationwide siting surface from the report methodology
- report-equivalent cumulative buildout animation starting from a reproduced 2025
  operating baseline and a report-equivalent suitability surface

## Bottom Line

The repo now has a runnable bounded public report bundle.

It does not yet have a report-equivalent output bundle.

Use the current commands to validate mechanics, input compatibility, and bounded
public approximations. Do not describe the current outputs as exact reproductions of
the published report until the missing exclusion, suitability, baseline-year, and
training-label gaps are closed.
