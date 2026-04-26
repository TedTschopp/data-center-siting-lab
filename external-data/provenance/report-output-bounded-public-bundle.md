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
- bounded feasible-land GeoPackage generation from the execution grid, filtered to `developable_capacity_mw > 0` cells while retaining cells whose staged NLCD water/wetland share across classes `11`, `90`, and `95` is at least `0.5` as flagged records
- bounded suitability-percentile GeoPackage generation from the execution grid, with flagged water/wetland cells clamped to `0` suitability percentile
- bounded nationwide ranked suitability CSV generation from the bounded suitability layer, including deterministic human-readable cell names and gateway-place duplicate-name disambiguation without raw cell ids in the display label
- derived state-boundary GeoPackage generation from the official Census generalized state layer for bounded map context
- bounded zoning proxy GeoPackage generation from staged NLCD developed-land context, transferred onto the execution-grid cells as a coarse land-use overlay
- bounded permitting and ordinance evidence proxy GeoPackage generation from a manually curated public evidence manifest, transferred onto the execution-grid cells as a coarse permitting-risk evidence overlay
- bounded social-friction evidence proxy GeoPackage generation from a manually curated public evidence manifest, transferred onto the execution-grid cells as a coarse community-friction evidence overlay
- bounded hosting-capacity proxy GeoPackage generation from the existing NERC reserve-margin surface, transferred onto the execution-grid cells as a coarse regional overlay
- single-page D3 suitability map generation from the bounded feasible-land, suitability, state-boundary, zoning-proxy, permitting-proxy, social-friction-proxy, and hosting-proxy layers, including a square/hex cell display switch, true Census state boundaries in square mode, snapped cell-edge state outlines in hex mode, light/dark/system theme switching, table-to-map hover highlighting for ranked cells, and optional zoning-proxy, permitting-proxy, social-friction-proxy, and hosting-proxy overlay toggles
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

## Version-Control Policy

The report bundle is a generated local deliverable, not a source dataset.

Track the durable inputs and recipes:

- `reVeal.public_data` source code and regression tests
- schema-only evidence manifests under `external-data/manifest/`
- provenance notes under `external-data/provenance/`
- usage and Sphinx documentation that describe how to regenerate the bundle
- `external-data/derived/report-bundle/README.md`, which records the local output policy

Do not track regenerated report-bundle payloads under
`external-data/derived/report-bundle/`, including the embedded HTML map, GeoPackages,
status JSON, output manifest JSON, deviation note, ranked CSV, cumulative-buildout
summary, and cached Census state-boundary ZIP. These files can be recreated with the
bundle command above.

The report-bundle command also refreshes NERC GeoPackage features under
`external-data/derived/nerc/`; those GeoPackages are regenerated artifacts as well.
The NERC README and small assessment-area CSV remain the durable tracked references
for that derived workflow.

## Tracked Commands, Configs, And Outputs

<!-- markdownlint-disable MD060 -->

|                                         Output class | Current command or workflow                                                                                                                                                                                  | Config or input anchor                                                                                                                                                                                              | Current output                                                                                | Current validation                                                                  |
|-----------------------------------------------------:|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
|                       Public EER national projection | `python -m reVeal.public_data generate-eer-loads ...`                                                                                                                                                        | `external-data/unpacked/eer/ADP2024_detailed_output_data.xlsx`; `tests/data/downscale/inputs/regions/eer_adp_zones.gpkg`                                                                                            | `external-data/derived/eer/eer_public_central_high_data_center_national.csv`                  | Schema assessment plus `run-public-reproduction`                                    |
|               Public EER grouped regional projection | `python -m reVeal.public_data generate-eer-loads ...`                                                                                                                                                        | same as above                                                                                                                                                                                                       | `external-data/derived/eer/eer_public_central_high_data_center_region_groups.csv`             | Schema assessment plus `run-public-reproduction`                                    |
|                  Bounded feasible-land approximation | `python -m reVeal.public_data run-public-report-bundle --output-dir external-data/derived/report-bundle`                                                                                                     | `tests/data/downscale/inputs/grid_char_weighted_scores.gpkg`; `developable_capacity_mw > 0`; staged NLCD water/wetland share across classes `11`, `90`, and `95` flags cells at or above `0.5` without removing them | `external-data/derived/report-bundle/public_report_feasible_land.gpkg`                        | focused pytest coverage plus `run-public-report-bundle`                             |
|         Bounded suitability-percentile approximation | `python -m reVeal.public_data run-public-report-bundle --output-dir external-data/derived/report-bundle`                                                                                                     | `tests/data/downscale/inputs/grid_char_weighted_scores.gpkg`; percentile rank of `suitability_score` on developable cells; water/wetland-flagged cells are clamped to `0`; Census coordinate GeoLookup identity enrichment when enabled, with deterministic bounded catalog fallback | `external-data/derived/report-bundle/public_report_suitability_percentiles.gpkg`              | focused pytest coverage plus `run-public-report-bundle`                             |
|        Bounded nationwide ranked suitability summary | `python -m reVeal.public_data run-public-report-bundle --output-dir external-data/derived/report-bundle`                                                                                                     | derived from `public_report_suitability_percentiles.gpkg`, including numeric cell id, deterministic `cell_name`, `base_cell_name`, disambiguation flag, Census geography fields, anchor-place metadata, candidate names, and selection basis | `external-data/derived/report-bundle/public_report_suitability_ranked_cells.csv`              | focused pytest coverage plus `run-public-report-bundle`                             |
|                 Derived state-boundary context layer | `python -m reVeal.public_data run-public-report-bundle --output-dir external-data/derived/report-bundle`                                                                                                     | official Census generalized state boundaries from `https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_state_20m.zip`, reprojected into the suitability layer CRS                                             | `external-data/derived/report-bundle/public_report_state_boundaries.gpkg`                     | focused pytest coverage plus `run-public-report-bundle`                             |
|                     Bounded zoning proxy layer | `python -m reVeal.public_data run-public-report-bundle --output-dir external-data/derived/report-bundle`                                                                                                     | staged NLCD land-cover raster sampled onto the execution-grid cells; developed classes are carried forward as a coarse zoning-context proxy rather than parcel zoning                                                   | `external-data/derived/report-bundle/public_report_zoning_proxy.gpkg`                         | focused pytest coverage plus `run-public-report-bundle`                             |
|       Bounded permitting / ordinance proxy layer | `python -m reVeal.public_data run-public-report-bundle --output-dir external-data/derived/report-bundle`                                                                                                     | staged `external-data/manifest/permitting-ordinance-evidence.csv` rows with public evidence points assigned to execution-grid cells; classes are evidence signals, not permit-readiness determinations                  | `external-data/derived/report-bundle/public_report_permitting_proxy.gpkg`                      | focused pytest coverage plus `run-public-report-bundle`                             |
|               Bounded social-friction proxy layer | `python -m reVeal.public_data run-public-report-bundle --output-dir external-data/derived/report-bundle`                                                                                                     | staged `external-data/manifest/social-friction-evidence.csv` rows with public evidence points assigned to execution-grid cells; classes are evidence signals, not community-acceptance measurements                    | `external-data/derived/report-bundle/public_report_social_friction_proxy.gpkg`                 | focused pytest coverage plus `run-public-report-bundle`                             |
|             Bounded hosting-capacity proxy layer | `python -m reVeal.public_data run-public-report-bundle --output-dir external-data/derived/report-bundle`                                                                                                     | NERC reserve-margin assessment areas mapped into `tests/data/downscale/inputs/regions/eer_adp_zones.gpkg` and then transferred onto the execution-grid cells as a coarse regional headroom proxy                      | `external-data/derived/report-bundle/public_report_hosting_capacity_proxy.gpkg`               | focused pytest coverage plus `run-public-report-bundle`                             |
|                         Bounded suitability map page | `python -m reVeal.public_data run-public-report-bundle --output-dir external-data/derived/report-bundle`                                                                                                     | bounded feasible-land, suitability, state-boundary, zoning-proxy, permitting-proxy, social-friction-proxy, and hosting-proxy surfaces embedded in one HTML page with D3; grid-backed cells can render as original geographic squares or display-only honeycomb hexes while ranked rows bind back to the matching map cell by stable cell id | `external-data/derived/report-bundle/public_report_suitability_map.html`                      | focused pytest coverage plus `run-public-report-bundle`                             |
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

1. By default the report bundle calls the U.S. Census coordinate GeoLookup API for each retained cell and caches normalized generated responses in `public_report_census_geography_cache.json` under the output directory. Pass `--no-census-geolookup` to keep the fully offline bounded-catalog fallback.
2. The repo still uses curated public catalogs of major U.S. metropolitan names, major natural-feature or monument names, and gateway place anchors as fallback context and landmark support. Census geography is authoritative for place, county subdivision, county, metro area, state, Census division, and Census region when available.
3. For each cell, the workflow reprojects cell geometry to EPSG:4326 for point-in-polygon checks and replaces missing or projected coordinate columns with a geographic representative point before nearest-place matching or Census lookup.
4. The workflow builds a geographic identity stack for each cell: exact point, landmark/address, neighborhood, district, city, county, metro area, state region, state, national region, and country. Layers without current public data, such as neighborhood, remain null instead of guessed.
5. The local label chooses the most specific useful layer available, preferring Census incorporated/CDP place, Census county subdivision, county, nearby landmark, then coordinates.
6. The general American label chooses the smallest broadly recognizable official layer: Census place when present, Census metro area when present, otherwise Census division, state, or fallback catalog/state labels.
7. The legacy `cell_name` remains a stable unique row label for CSV joins and disambiguation. Census-backed names use the official intersecting geography as the base label; duplicate row labels are expanded with available county/state context and coordinates only when needed.
8. The D3 map table uses the general American label as the primary display label and shows the local label as secondary context when it adds information. Naming basis, match type, Census fields, and identity-stack metadata remain available as CSV/GeoPackage fields and in the cell tooltip rather than appearing as visible suffixes such as `metro name` or `natural name`.

That rule is reproducible and based on public Census geography when online lookup is enabled, but it is still a bounded public approximation rather than a report-sourced naming layer.

## Current Map Display Shape Rule

The bounded D3 map now lets browser reviewers switch the grid-backed feasible,
suitability, zoning-proxy, permitting-proxy, social-friction-proxy, and hosting-proxy
cells between geographic squares and display-only honeycomb hexagons.

1. The underlying GeoPackages and embedded GeoJSON remain the original grid-cell
  geometries with stable `sc_point_gid` / `cell_id` keys.
2. The square display mode draws each grid-backed layer with the original projected
  cell geometry. This is the geographically aligned view and is the correct mode for
  inspecting state-boundary overlay alignment.
3. The hex display mode projects each original grid feature, computes shared honeycomb tile
  metrics from the suitability surface, assigns cells to staggered display row/column
  slots, and draws all grid-backed map cells with one consistent display-only hex
  center and radius instead of fitting each hex independently inside its source-cell
  footprint.
4. Table rows, tooltips, active highlighting, and optional overlay joins continue to
  use the original stable cell keys rather than the display geometry.
5. State-boundary context remains stroke-only and pointer-event disabled. Square mode
  uses the true Census-derived projected state paths because both layers use source
  geography. Hex mode hides those true paths and draws snapped state outlines from
  the boundary edges of state-assigned hex cells, so the visible state context lines
  up with the honeycomb display lattice.

That display rule improves scanability and removes the old rectangular-center hex
layout that made the browser hexes read as aligned symbols rather than a honeycomb
display tile surface, while preserving a geographically faithful square view for
overlay checks. The hex-mode state outline is a display aid, not a replacement for
the derived state-boundary GeoPackage. It does not change the internal grid model or
the downstream bundle artifacts.

## Current Map Theme Rule

The bounded D3 map now lets browser reviewers switch between system, light, and dark
visual themes.

1. The generated HTML sets `data-theme-mode` and `data-theme` on the root element so
  the page has a valid fallback before JavaScript finishes loading.
2. The `System` mode resolves through `prefers-color-scheme: dark` and updates when
  the operating-system preference changes while the page is open.
3. Explicit `Light` or `Dark` selections are stored in local storage when the browser
  permits it, so repeated local reviews keep the reviewer-selected mode.
4. Theme colors are driven by CSS variables for the page background, cards, controls,
  notes, table hover state, map background, state outlines, active cell highlight,
  and tooltip contrast.
5. The theme switch changes presentation only. It does not change embedded GeoJSON,
  grid geometry, ranked rows, optional overlays, or display-mode behavior.

## Current Feasible-Land Rule

The bounded bundle now carries one real exclusion-stack slice rather than relying only on `developable_capacity_mw > 0`.

1. The workflow starts from execution-grid cells where `developable_capacity_mw > 0`.
2. The workflow samples the staged NLCD land-cover raster onto those candidate cells.
3. The workflow computes `water_wetland_share` from NLCD classes `11` (open water), `90` (woody wetlands), and `95` (emergent herbaceous wetlands).
4. The bundle flags cells whose `water_wetland_share` is at least `0.5`, keeps those cells in `public_report_feasible_land.gpkg`, and clamps their generated `suitability_percentile` to `0` so the map preserves the full developable-cell footprint without treating water/wetland-dominated cells as viable high-scoring candidates.

That rule closes one report-aligned exclusion gap with staged public data, but it is still only one bounded slice of the broader exclusion stack described in the report.

It should not be described as a full reproduction of the report's feasibility exclusion workflow.

## Current State-Boundary Overlay Rule

The bounded D3 map now carries an explicit state-boundary context layer.

1. The workflow downloads the official Census generalized state-boundary ZIP from `cb_2024_us_state_20m.zip` when the cached copy is missing.
2. The derived state layer is normalized to `state_name`, `state_code`, and `geometry`, excludes Puerto Rico from the overlay, and is reprojected into the same CRS as the suitability surface before export.
3. The bundle writes that reprojected layer to `public_report_state_boundaries.gpkg` and embeds the same geometry into the D3 page as `stateBoundaryGeoJson`.
4. The map renders the state layer as a transparent stroke-only overlay above the suitability cells with pointer events disabled so hover behavior continues to target the suitability polygons.
5. The true Census-derived overlay is geographically aligned in square display mode.
  In hex display mode, the true boundary paths are hidden and replaced by snapped
  cell-edge outlines derived from state-assigned hex cells, so state context aligns
  with the honeycomb display while remaining a contextual display aid.

That overlay improves orientation for quick review, but it remains contextual map framing rather than a claim of report-equivalent state-level methodology.

## Current Zoning Proxy Rule

The bounded D3 map now carries an optional zoning proxy overlay.

1. The workflow reads the staged NLCD land-cover raster from `external-data/raw/nlcd/` and samples the raster onto each feasible execution-grid cell in the current suitability surface.
2. The staged layer carries the dominant NLCD class, a readable `dominant_nlcd_label`, the share of developed pixels within each cell, and a derived `zoning_proxy_class`.
3. The bundle writes that derived layer to `public_report_zoning_proxy.gpkg` and embeds the same geometry into the D3 page as `zoningProxyGeoJson`.
4. The D3 page exposes a `Zoning Proxy` toggle and renders the overlay above the suitability cells with low-opacity class colors so it can be switched on without replacing the base suitability view.

That overlay reduces the old "no zoning context at all" gap, but it is still only a coarse developed-land context proxy.

It should not be described as parcel zoning, industrial zoning, or an allowed-use determination for a data-center site.

## Current Permitting / Ordinance Proxy Rule

The bounded D3 map now carries an optional permitting and ordinance evidence proxy overlay.

1. The workflow reads staged rows from `external-data/manifest/permitting-ordinance-evidence.csv` using the schema `evidence_id`, `jurisdiction_name`, `state`, `evidence_type`, `friction_level`, `latitude`, `longitude`, `source_url`, `source_date`, and `summary`.
2. Each evidence row is interpreted as a public point signal and assigned to the current feasible execution-grid cell whose geometry covers the evidence point.
3. The staged layer carries evidence counts, restrictive-evidence counts, friction-evidence counts, source evidence ids, evidence types, jurisdictions, and a derived `permitting_proxy_class`.
4. The derived classes are `restrictive_ordinance_evidence`, `public_friction_signal`, `permit_activity_record`, and `no_public_evidence_recorded`.
5. The bundle writes that derived layer to `public_report_permitting_proxy.gpkg` and embeds the same geometry into the D3 page as `permittingProxyGeoJson`.
6. The D3 page exposes a `Permitting / Ordinance Proxy` toggle and renders the overlay above the suitability cells with low-opacity class colors so it can be switched on without replacing the base suitability view.

That overlay reduces the old "no permitting context at all" gap, but it is still only a manually curated public evidence proxy.

It should not be described as permit readiness, legal entitlement, ordinance compatibility, or a comprehensive local permitting pathway model. A cell with `no_public_evidence_recorded` only means no staged evidence row was assigned to that cell; it does not mean no permitting risk exists.

## Current Social-Friction Proxy Rule

The bounded D3 map now carries an optional social-friction evidence proxy overlay.

1. The workflow reads staged rows from `external-data/manifest/social-friction-evidence.csv` using the schema `evidence_id`, `community_name`, `state`, `evidence_type`, `friction_level`, `latitude`, `longitude`, `source_url`, `source_date`, and `summary`.
2. Each evidence row is interpreted as a public point signal and assigned to the current feasible execution-grid cell whose geometry covers the evidence point.
3. The staged layer carries evidence counts, opposition-evidence counts, concern-evidence counts, engagement-evidence counts, source evidence ids, evidence types, communities, and a derived `social_friction_proxy_class`.
4. The derived classes are `organized_opposition_evidence`, `public_concern_signal`, `community_engagement_record`, and `no_public_evidence_recorded`.
5. The bundle writes that derived layer to `public_report_social_friction_proxy.gpkg` and embeds the same geometry into the D3 page as `socialFrictionProxyGeoJson`.
6. The D3 page exposes a `Social-Friction Proxy` toggle and renders the overlay above the suitability cells with low-opacity class colors so it can be switched on without replacing the base suitability view.

That overlay reduces the old "no social-friction context at all" gap, but it is still only a manually curated public evidence proxy.

It should not be described as social acceptance, opposition intensity, sentiment, or social license to operate. A cell with `no_public_evidence_recorded` only means no staged evidence row was assigned to that cell; it does not mean no social-friction risk exists.

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
  `developable_capacity_mw > 0` and flags cells whose staged NLCD water/wetland
  share across classes `11`, `90`, and `95` is at least `0.5`, rather than a fully
  reproduced exclusion stack from the report workflow.
- The current suitability-percentile output ranks the pre-existing
  `suitability_score` field on developable cells and clamps water/wetland-flagged
  cells to `0` percentile, not a trained nationwide model surface.
- The current ranked suitability summary is therefore a bounded table derived from
  that same pre-existing score surface, not a report-equivalent learned ranking.
- The current zoning overlay is an NLCD developed-land context proxy, not a
  reproduced parcel-zoning or land-use-entitlement surface.
- The current permitting overlay is a manifest-driven public evidence proxy, not a
  reproduced permit-readiness or ordinance-compatibility surface.
- The current social-friction overlay is a manifest-driven public evidence proxy,
  not a reproduced community-acceptance or social-license surface.
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
