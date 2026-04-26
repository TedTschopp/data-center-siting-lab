Dataset Sourcing
****************

This repository does not ship a full end-user data bundle for the data center siting
case study. The tracked ``tests/data`` files are small fixtures that demonstrate schema
shape and workflow expectations, not a production dataset catalog.

To make dataset sourcing reproducible, this repository now keeps a repo-local staging
surface under ``external-data`` with tracked manifest, provenance, and derived-output
artifacts:

* ``external-data/manifest/dataset-manifest.csv``: authoritative source inventory for
  cited datasets and repo-anchored fixtures.
* ``external-data/manifest/gap-register.csv``: unresolved, commercial, and uncited
  layers that block a full reproduction of the presentation workflow.
* ``external-data/manifest/open-substitutes.csv``: public-source substitutes for
  commercial or uncited layers.
* ``external-data/provenance/report-reproduction-gaps.md``: exact-vs-proxy inventory
  of the remaining report-layer blockers.
* ``external-data/provenance/eer-public-data.md``: provenance for the public EER ADP
  package already downloaded during research.
* ``external-data/provenance/eer-public-derived-loads.md``: notes on the public EER
  transform that generates reVeal-compatible projection CSVs.
* ``external-data/provenance/data-center-public-baseline.md``: notes on the first-pass
  public data center baseline built from exported OSM, Wikidata, and optional manual
  augmentation rows.
* ``external-data/provenance/power-infrastructure-public-baseline.md``: notes on the
  first-pass public transmission and substation baseline built from exported OSM
  power payloads.
* ``external-data/provenance/fiber-public-proxy.md``: notes on the first-pass public
  fiber proxy workflow built from exported OSM telecom linework, FCC availability
  polygons, and a template raster.
* ``external-data/provenance/gas-service-territory-public-baseline.md``: notes on the
  first-pass public gas service territory assembly workflow built from state-by-state
  extracts.
* ``external-data/provenance/land-value-public-proxy.md``: notes on the first-pass
  public land-value proxy workflow built from county proxy values, county polygons,
  and state-relative normalization.
* ``external-data/provenance/construction-cost-public-proxy.md``: notes on the
  first-pass public construction-cost proxy workflow built from county wage and
  regional price inputs, county polygons, and national-relative normalization.
* ``external-data/provenance/water-availability-public-proxy.md``: notes on the
  first-pass public water proxy workflow built from state freshwater withdrawal
  values and repo state-to-zone weights.
* ``external-data/provenance/nerc/nerc-ltra-2025.md``: provenance and transform notes
  for the public NERC reserve-margin workflow.
* ``external-data/provenance/ribits-manual-acquisition.md``: the current scripted
  webservice acquisition workflow for RIBITS.
* ``external-data/provenance/urdb-acquisition.md``: the direct staging decision for
  URDB.
* ``external-data/provenance/public-dataset-execution-ready.md``: the execution-ready
  command summary for the remaining public dataset families named in TODO item 18.
* ``external-data/provenance/public-geospatial-staging.md``: representative download
  workflow and staging notes for the public geospatial layers.
* ``external-data/derived/eer``: generated public EER national, regional, and grouped
  projection CSVs.
* ``external-data/derived/data-centers``: generated first-pass public data center
  baseline artifacts.
* ``external-data/derived/power``: generated first-pass public transmission and
  substation baseline artifacts.
* ``external-data/derived/fiber``: generated first-pass public fiber route-proxy and
  aligned raster artifacts.
* ``external-data/derived/gas``: generated first-pass public gas service territory
  assembly artifacts.
* ``external-data/derived/land``: generated first-pass public county and EMM-zone
  land-value proxy artifacts.
* ``external-data/derived/construction``: generated first-pass public county and
  EMM-zone construction-cost proxy artifacts.
* ``external-data/derived/water``: generated first-pass public water proxy artifacts.
* ``external-data/derived/nerc``: generated NERC assessment-area, EMM-zone, and grid
  reserve-margin artifacts.
* ``external-data/derived/report-bundle``: local regenerated report-bundle outputs;
  only the README policy is tracked, while the generated HTML, GeoPackage, JSON, CSV,
  Markdown, and cache payloads are recreated from the bundle command.

The ``external-data/raw``, ``external-data/unpacked``, and ``external-data/examples``
directories are intentionally ignored by git so that local downloads and runnable
example bundles can be staged without polluting version control.

Current status
==============

The first implementation pass covers three things:

#. A manifest of presentation-cited and repo-expected datasets.
#. A local staging layout for public-source downloads.
#. An open substitute matrix for the commercial or uncited layers in the case study.

The public EER ADP package is available and has already been validated at the archive
level. The package is useful context for the data center scenario work, but it is not
a direct drop-in replacement for the exact ``reVeal`` downscale CSV inputs used in
the presentation. The staged workbook must still be transformed into schema-compatible
projection CSVs using the repo workflow.

The remaining reproduction gaps are now also collapsed into a single execution note:
one commercial dependency for exact site inventory parity, one implemented first-pass
public power proxy workflow, one implemented first-pass public fiber proxy workflow,
one implemented public gas service-territory assembly workflow, one implemented public
land-value proxy workflow, one implemented public construction-cost proxy workflow,
one implemented public water proxy workflow, and one public source that now exposes a
scripted ORDS webservice acquisition path.

RIBITS is now handled through documented public webservices rather than a manual-only
portal workflow. The repo can still stage the local workflow note for that source
with:

.. code-block:: bash

  python -m reVeal.public_data stage-dataset ribits --repo-root .

And it can capture a repo-local JSON snapshot through the public ORDS list/detail
endpoints with:

.. code-block:: bash

  python -m reVeal.public_data download-ribits-bank-sites \
    --output-path external-data/raw/ribits/ribits_bank_sites_snapshot.json

If that snapshot is interrupted, rerun the same command with ``--resume``. A
checkpoint sidecar is written next to the output JSON by default, and you can
override that location with ``--checkpoint-path``.

URDB is now handled as a direct staged source rather than a deferred dataset. The repo
can stage the approved-rates bulk export with:

.. code-block:: bash

  python -m reVeal.public_data stage-dataset urdb --repo-root .

Execution-ready example bundles
===============================

The remaining generated public workflows now support repo-local runnable example
bundles. Stage one with:

.. code-block:: bash

  python -m reVeal.public_data stage-example-bundle public_data_center_baseline --repo-root .

Available bundle IDs are:

* ``public_data_center_baseline``
* ``public_power_infrastructure_baseline``
* ``public_fiber_proxy_baseline``
* ``public_gas_service_territory_baseline``
* ``public_land_value_proxy``
* ``public_construction_cost_proxy``
* ``public_water_availability_proxy``

Each staged bundle writes ``external-data/examples/<bundle_id>/README.md`` with the
validated generation command and expected outputs for that workflow. This is the
execution-ready path for the generated public proxy families referenced in TODO item
18.

Checkpointed public reproduction workflow
=========================================

The repo also exposes one bounded orchestration command for the validated public
reproduction path:

.. code-block:: bash

  python -m reVeal.public_data run-public-reproduction \
    --status-path external-data/derived/public_reproduction_status.json

This workflow currently runs five steps in order:

* assess the public EER workbook against the tracked anchors
* regenerate the public EER projection CSVs
* run the total smoke config
* run the grouped regional smoke config
* regenerate the public NERC reserve-margin features

The command emits step-level progress to stderr, writes a JSON status file with
completed steps and step outputs, and supports ``Ctrl+C`` interruption plus
``--resume`` continuation. Use ``--force`` to discard an existing status file and
restart from the beginning.

Bounded public report bundle
============================

For a coworker-facing explanation of what the bundle contains, where it came
from, what was added to upstream ``reVeal``, and what remains bounded, start with
:doc:`data_center_report_bundle`.

The repo now also exposes a report-facing bundle command that wraps the bounded
reproduction workflow and writes explicit deviation artifacts:

.. code-block:: bash

  python -m reVeal.public_data run-public-report-bundle \
    --output-dir external-data/derived/report-bundle

This command materializes a bundle directory with:

* ``external-data/derived/report-bundle/public_report_bundle_status.json``
* ``external-data/derived/report-bundle/public_reproduction_status.json``
* ``external-data/derived/report-bundle/public_report_feasible_land.gpkg``
* ``external-data/derived/report-bundle/public_report_suitability_percentiles.gpkg``
* ``external-data/derived/report-bundle/public_report_suitability_ranked_cells.csv``
* ``external-data/derived/report-bundle/public_report_state_boundaries.gpkg``
* ``external-data/derived/report-bundle/public_report_zoning_proxy.gpkg``
* ``external-data/derived/report-bundle/public_report_permitting_proxy.gpkg``
* ``external-data/derived/report-bundle/public_report_social_friction_proxy.gpkg``
* ``external-data/derived/report-bundle/public_report_hosting_capacity_proxy.gpkg``
* ``external-data/derived/report-bundle/public_report_suitability_map.html``
* ``external-data/derived/report-bundle/public_report_assumption_registry.json``
* ``external-data/derived/report-bundle/public_report_limitations.md``
* ``external-data/derived/report-bundle/public_report_reeds_integration_contract.json``
* ``external-data/derived/report-bundle/public_eer_total_downscaled_cumulative_buildout.gpkg``
* ``external-data/derived/report-bundle/public_eer_regional_downscaled_cumulative_buildout.gpkg``
* ``external-data/derived/report-bundle/public_report_bundle_cumulative_buildout_summary.csv``
* ``external-data/derived/report-bundle/public_report_bundle_manifest.json``
* ``external-data/derived/report-bundle/public_report_bundle_deviations.md``

Use this command when you want one local report-output surface for the current
bounded public approximation. The generated bundle outputs are intentionally ignored
by git; track the command, source code, tests, manifests, provenance, and
documentation that recreate them. The manifest records the generated output paths
plus the current baseline-year and grid-priority assumptions. The deviation note
makes the remaining report-parity gaps explicit, including the use of the fixture
grid, the 2022 baseline year, and the pre-existing ``suitability_score`` field.

The cumulative buildout GeoPackages are derived directly from the existing total
and grouped regional smoke outputs. They add baseline, cumulative-new, and
cumulative-total load columns by cell over time, and the summary CSV aggregates
those values by source output and year.

The feasible-land and suitability-percentile GeoPackages are derived directly from
the current execution grid. The bounded feasible-land layer keeps cells where
``developable_capacity_mw > 0``. Cells whose staged NLCD water/wetland share is at
least ``0.5`` remain in the layer as flagged records, and the bounded suitability
layer clamps those cells to ``0`` suitability percentile after ranking the
pre-existing ``suitability_score`` field across developable cells.

The ranked suitability CSV is derived from that same bounded suitability layer. It
assigns a nationwide rank and sorts developable cells by suitability percentile,
suitability score, and developable capacity, with water/wetland-flagged cells
retained at the bottom of the percentile surface. Cell labels follow a deterministic
bounded geographic identity stack. By default the report bundle enriches each cell
with the U.S. Census coordinate GeoLookup API and caches those generated responses
in the output directory; ``--no-census-geolookup`` keeps the fully offline bounded
catalog fallback. The outputs preserve a stable unique ``cell_name`` for row joins
and disambiguation, report-facing ``display_cell_name`` and
``display_context_name`` fields for the map and ranked table, plus
``local_cell_name``, ``general_american_cell_name``, ``identity_stack_json``, and
normalized ``census_*`` geography fields so the map can choose the useful layer for
its audience. Census-backed labels use official place, county subdivision, county,
metro area, state, Census division, and Census region names when available. Naming
basis fields remain in the data outputs and map tooltip rather than being appended
to the visible table label. The bundle also writes
``public_report_census_geolookup_misses.csv`` and
``public_report_census_geolookup_misses.md``. Those generated review artifacts
classify retained cells where Census did not return named geography by nearest
state fallback, boundary/coastal location class, water/wetland clamp status, and
map-impact class. Missing Census rows outside state boundaries receive dedicated
boundary/coastal display labels instead of presenting the bounded catalog fallback
as authoritative Census identity.

The D3 suitability map HTML page uses a single self-contained browser document to
render the bounded feasible-land and suitability surfaces directly from embedded
bundle data. The underlying grid remains the internal model, but the browser display
draws grid-backed cells as fitted hexagons for quicker visual scanning. Use it when
you want a quick visual review without opening the GeoPackages in desktop GIS
software. Optional state-boundary, zoning-proxy, permitting / ordinance evidence,
social-friction evidence, and hosting-capacity proxy layers provide bounded context
overlays without replacing the base suitability surface.

The assumption registry JSON is derived from the tracked total and regional smoke
configs plus the bounded bundle rules. It records scenario inputs,
report-reference assumptions, current bounded assumptions, output labels, and
explicit assumption gaps. It now includes a temporal-assumption contract that
separates the report reference from current bounded behavior: the report reference
starts from 2025 operating data centers, carries modeled years 2025, 2030, 2035,
2040, 2045, and 2050, and treats the buildout horizon as 25 years through 2050.
The current bundle keeps the configured 2022 starting-stock field and records the
mismatch as a parity blocker rather than changing buildout behavior implicitly.
It also records the report-style capacity constraint explicitly: the public smoke
configs use an 0.88 utilization factor and a 1000 MW per-site time-step nameplate
capacity cap, which the downscale path converts to load-equivalent allocation
limits. When projected demand exceeds capped available capacity, the output remains
capacity-limited instead of forcing excess load into a grid cell. The cumulative
buildout artifacts expose both load and capacity-equivalent fields.
The bundle also writes a grid-resolution contract. It measures the current
execution grid, compares it with the report-reference 5.76 km grid and the
LinkedIn 5 km aggregation language, and records the current grid as a spatial
parity blocker rather than subdividing the existing cells into unvalidated 5.76 km
surfaces.
It also writes an allocation-assumption contract. That contract records the current
bounded method as weighted-bootstrap random allocation over the current
``suitability_score`` surface, validates that total, grouped regional, cumulative,
and summary artifacts are present, and keeps exact report allocation parity blocked
until the report algorithm and trained suitability surface are recovered.
The Baxtel schema contract records the vendor procurement path, compares any local
Baxtel sample or licensed CSV schema against the public data-center baseline, and
keeps trained-suitability parity blocked until the Baxtel schema, 2025 operating
baseline, and model-training workflow are recovered.
The generated D3 map also includes a buildout timeline mode. Reviewers can switch
from the static suitability surface to bounded cumulative buildout by source,
metric, and year, using the existing cumulative smoke-output artifacts without
asserting report-equivalent temporal parity.

The limitations note carries forward the named LinkedIn refinement gaps directly
into the generated bundle. It explicitly states that local transmission hosting
capacity, demand queue times, zoning, permitting and ordinance information,
capacity scaling by market trends, and social acceptance are not fully
implemented in the current bounded report surface. Zoning, permitting, social
friction, and hosting now have bounded proxy layers, but those layers do not imply
parcel entitlement, permit readiness, ordinance compatibility, social acceptance, or
local interconnection feasibility.

The ReEDS integration contract JSON defines the bounded handoff surface for
ReEDS-facing workflows. It records the current handoff products, required
columns, annual modeled years, spatial join keys, grid-resolution parity status,
allocation-assumption parity status, Baxtel schema parity status, and the validation checks that
must pass before the bounded bundle is treated as a load-forecasting handoff.

Like the other checkpointed workflows, the command emits step-level progress to
stderr and supports ``Ctrl+C`` interruption plus ``--resume`` continuation. Use
``--force`` to discard the existing bundle metadata and restart.

Checkpointed public example workflows
=======================================

The repo also exposes a checkpointed runner for the generated public proxy example
workflows:

.. code-block:: bash

  python -m reVeal.public_data run-public-example-workflows \
    --status-path external-data/derived/public_example_workflows_status.json

This command stages example bundles when needed and then runs the generated public
workflow for each of these bundle families:

* ``public_data_center_baseline``
* ``public_power_infrastructure_baseline``
* ``public_fiber_proxy_baseline``
* ``public_gas_service_territory_baseline``
* ``public_land_value_proxy``
* ``public_construction_cost_proxy``
* ``public_water_availability_proxy``

Like the bounded reproduction workflow, it emits step-level progress to stderr,
writes a JSON status file with completed steps and outputs, and supports
``Ctrl+C`` interruption plus ``--resume`` continuation. Use ``--force`` to discard
the existing status file and restart. Use ``--force-stage`` if you want the staged
example bundles rebuilt before rerunning.

Workflow status summaries
=========================

Use the status-summary command when you want a compact report from a saved workflow
status file without rerunning the workflow:

.. code-block:: bash

  python -m reVeal.public_data summarize-public-workflow-status \
    --status-path external-data/derived/public_reproduction_status.json

The command works with both the bounded reproduction status file and the public
example-workflow status file. It also works with the report-bundle status file.

Public data center baseline
===========================

The repo now includes a first-pass public baseline workflow for data center site
inventory. It merges exported OpenStreetMap Overpass JSON, exported Wikidata SPARQL
JSON, and an optional manual CSV of operator-announcement or permitting rows.

The repo can also stage note files for those three input surfaces with:

.. code-block:: bash

  python -m reVeal.public_data stage-dataset data_center_osm_export --repo-root .
  python -m reVeal.public_data stage-dataset data_center_wikidata_export --repo-root .
  python -m reVeal.public_data stage-dataset data_center_manual_augmentation --repo-root .

The transform is exposed through:

.. code-block:: bash

  python -m reVeal.public_data generate-data-center-baseline \
    --osm-payload external-data/raw/data-centers/osm_data_centers.json \
    --wikidata-payload external-data/raw/data-centers/wikidata_data_centers.json \
    --manual-csv external-data/raw/data-centers/manual_data_centers.csv \
    --output-dir external-data/derived/data-centers

That command writes:

* ``external-data/derived/data-centers/public_data_center_baseline.csv``
* ``external-data/derived/data-centers/public_data_center_baseline.gpkg``

Method summary:

* OSM rows are normalized from exported element payloads, including node coordinates
  or feature centers.
* Wikidata rows are normalized from exported SPARQL JSON point bindings.
* Manual rows can add operator-announcement or permitting evidence for planned or
  under-construction sites.
* Deduplication prefers shared ``wikidata_id`` values and otherwise falls back to
  normalized names plus rounded coordinates.
* The merged baseline preserves provenance fields such as ``sources``,
  ``source_count``, ``source_ids``, ``source_url``, and ``source_note``.

This workflow is a public approximation, not an exact Baxtel replacement. Coverage is
expected to be weaker for planned and under-construction sites, and manual
augmentation remains part of the first-pass workflow.

Public transmission and substation baseline
===========================================

The repo now includes a first-pass public baseline workflow for transmission-line and
substation proximity inputs. It consumes exported OpenStreetMap Overpass JSON for
power linework and substations.

The repo can stage note files for those two input surfaces with:

.. code-block:: bash

  python -m reVeal.public_data stage-dataset transmission_lines_osm_export --repo-root .
  python -m reVeal.public_data stage-dataset substations_osm_export --repo-root .

The transform is exposed through:

.. code-block:: bash

  python -m reVeal.public_data generate-power-infrastructure-baseline \
    --line-payload external-data/raw/power/osm_transmission_lines.json \
    --substation-payload external-data/raw/power/osm_substations.json \
    --output-dir external-data/derived/power

That command writes:

* ``external-data/derived/power/public_transmission_lines_135kv.gpkg``
* ``external-data/derived/power/public_substations.gpkg``

Method summary:

* The transmission-line layer keeps OSM ``power=line``, ``power=minor_line``, and
  ``power=cable`` features whose parsed ``max_voltage_kv`` is at least ``135``.
* Voltage tags are normalized to kilovolts, and when multiple values are present the
  repo keeps the maximum parsed voltage.
* The substation layer keeps OSM ``power=substation`` features and preserves the
  OSM ``substation`` tag plus any parsed maximum-voltage value.
* Features without a parsable voltage tag are excluded from the high-voltage
  transmission layer to avoid false positives.

This workflow is a public approximation, not an exact curated transmission model.
Coverage and voltage tagging vary across OSM regions, and the first pass does not
yet fold in utility or federal supplement layers.

Public fiber proxy workflow
===========================

The repo now includes a first-pass public workflow for fiber-related proxy surfaces.
It keeps two separate concepts explicit instead of pretending they are the same:

* route-like proximity derived from OSM telecom linework
* binary availability derived from FCC Broadband Data Collection polygons

The repo can stage note files for those two input surfaces with:

.. code-block:: bash

  python -m reVeal.public_data stage-dataset fiber_lines_osm_export --repo-root .
  python -m reVeal.public_data stage-dataset fcc_bdc_fiber_availability_export --repo-root .

The transform is exposed through:

.. code-block:: bash

  python -m reVeal.public_data generate-fiber-proxy-rasters \
    --osm-payload external-data/raw/fiber/osm_fiber_lines.json \
    --fcc-availability external-data/raw/fiber/fcc_bdc_fiber_availability.gpkg \
    --template-raster path/to/template.tif \
    --output-dir external-data/derived/fiber

That command writes:

* ``external-data/derived/fiber/public_fiber_route_proxy.gpkg``
* ``external-data/derived/fiber/fiber_lines_onshore_proximity.tif``
* ``external-data/derived/fiber/fiber_availability_binary.tif``

Method summary:

* The route proxy keeps line geometries whose OSM tags suggest route-like telecom or
  fiber infrastructure, including explicit fiber or fibre tags.
* The FCC vector is rasterized into a binary availability layer aligned to the chosen
  template raster.
* The OSM route layer is rasterized onto that same grid and converted into a
  proximity raster.
* Output units for the proximity raster follow the template raster CRS.

This workflow is a public approximation, not exact fiber-route geometry. FCC
availability polygons indicate service coverage rather than literal route centerlines,
and OSM telecom linework is incomplete and inconsistent across regions.

Public gas service territory workflow
=====================================

The repo now includes a first-pass public workflow for assembling gas service
territory polygons from state-by-state public extracts.

The repo can stage the manifest-schema note with:

.. code-block:: bash

  python -m reVeal.public_data stage-dataset state_gas_service_territory_manifest --repo-root .

The transform is exposed through:

.. code-block:: bash

  python -m reVeal.public_data generate-gas-service-territory-baseline \
    --manifest-csv external-data/raw/gas/state_gas_service_territories.csv \
    --output-dir external-data/derived/gas

That command writes:

* ``external-data/derived/gas/public_gas_service_territories.gpkg``
* ``external-data/derived/gas/public_gas_service_territories_state_index.csv``

Method summary:

* The workflow treats national gas coverage as a state-assembly problem, not as a
  single authoritative national dataset.
* The manifest lists one row per state extract with a local path and an optional
  utility-name field.
* The generator merges the current set of state extracts into one polygon layer and a
  small state-index summary.

This workflow is a public approximation, not a claim of complete national parity.
Its completeness depends on which state sources have actually been collected and
normalized into the manifest.

Public land-value proxy workflow
================================

The repo now includes a first-pass public workflow for county-level land-value proxy
surfaces and an area-weighted transfer into the repo's EMM-zone geometry.

The repo can stage the local input-schema note with:

.. code-block:: bash

  python -m reVeal.public_data stage-dataset county_land_value_proxy_inputs --repo-root .

The transform is exposed through:

.. code-block:: bash

  python -m reVeal.public_data generate-land-value-proxy-features \
    --county-proxy-csv external-data/raw/land/county_land_value_proxy.csv \
    --county-polygons external-data/raw/land/county_land_value_counties.gpkg \
    --regions tests/data/downscale/inputs/regions/eer_adp_zones.gpkg \
    --output-dir external-data/derived/land

That command writes:

* ``external-data/derived/land/public_land_value_county.gpkg``
* ``external-data/derived/land/public_land_value_emm_zone.gpkg``

Method summary:

* The raw proxy CSV contains at least ``county_id``, ``state``, and
  ``land_value_proxy_usd_per_acre``.
* The county polygon layer provides matching ``county_id`` values and geometry.
* The repo computes ``state_land_value_index`` as a within-state percentile-style
  ranking to avoid pretending that raw county value signals are harmonized
  nationally.
* County raw values and the normalized index are then area-weighted into the repo's
  EMM-zone geometry.

This workflow is a public approximation, not a nationally harmonized land-market
dataset. County assessor methods differ across jurisdictions, so the normalized index
should only be compared within a state and the zone layer should be treated as a
screening proxy rather than an exact market valuation surface.

Public construction-cost proxy workflow
=======================================

The repo now includes a first-pass public workflow for county-level construction-cost
proxy surfaces and an area-weighted transfer into the repo's EMM-zone geometry.

The repo can stage the local input-schema note with:

.. code-block:: bash

  python -m reVeal.public_data stage-dataset county_construction_cost_proxy_inputs --repo-root .

The transform is exposed through:

.. code-block:: bash

  python -m reVeal.public_data generate-construction-cost-proxy-features \
    --county-proxy-csv external-data/raw/construction/county_construction_cost_proxy.csv \
    --county-polygons external-data/raw/construction/county_construction_cost_counties.gpkg \
    --regions tests/data/downscale/inputs/regions/eer_adp_zones.gpkg \
    --output-dir external-data/derived/construction

That command writes:

* ``external-data/derived/construction/public_construction_cost_county.gpkg``
* ``external-data/derived/construction/public_construction_cost_emm_zone.gpkg``

Method summary:

* The raw proxy CSV contains at least ``county_id``, ``state``,
  ``construction_worker_mean_wage_usd``, and ``regional_price_parity_index``.
* The county polygon layer provides matching ``county_id`` values and geometry.
* The repo derives ``construction_cost_proxy_score`` as
  ``construction_worker_mean_wage_usd * regional_price_parity_index / 100``.
* The repo normalizes that score to ``construction_cost_relative_index`` against the
  national mean proxy score.
* County wage, price, proxy score, and relative-index fields are then area-weighted
  into the repo's EMM-zone geometry.

This workflow is a public approximation, not a public dollars-per-MW construction
model. The derived score should be treated as a relative affordability screen rather
than an exact construction-cost estimate.

Public water availability proxy
===============================

The repo now includes a first-pass public workflow for transforming a state-level
water proxy into the repo's EMM-zone geometry.

The repo can stage the input-schema note with:

.. code-block:: bash

  python -m reVeal.public_data stage-dataset usgs_state_water_use_proxy_csv --repo-root .

The transform is exposed through:

.. code-block:: bash

  python -m reVeal.public_data generate-water-availability-proxy-features \
    --state-proxy-csv external-data/raw/water/usgs_state_water_use_proxy.csv \
    --mapping-workbook path/to/workbook.xlsx \
    --regions tests/data/downscale/inputs/regions/eer_adp_zones.gpkg \
    --output-dir external-data/derived/water

That command writes:

* ``external-data/derived/water/public_water_availability_state_proxy.csv``
* ``external-data/derived/water/public_water_availability_emm_zone.gpkg``

Method summary:

* The selected first-pass source is a state-level freshwater withdrawal proxy table.
* The repo reuses its existing state-to-zone weighting logic from the EER mapping
  workbook.
* State proxy values are apportioned into EMM zones and written as a zonal GeoPackage.

This workflow is a public approximation, not literal site-level water availability.
State withdrawal values are only a coarse proxy for the presentation's uncited water
feature.

NERC reserve-margin transform
=============================

The repo now includes a public-source NERC reserve-margin workflow built from Table 2
in the staged 2025 Long-Term Reliability Assessment PDF.

The transform is exposed through:

.. code-block:: bash

  python -m reVeal.public_data generate-nerc-reserve-margin-features \
    --regions tests/data/downscale/inputs/regions/eer_adp_zones.gpkg \
    --grid tests/data/downscale/inputs/grid_char_weighted_scores.gpkg \
    --output-dir external-data/derived/nerc

That command writes:

* ``external-data/derived/nerc/nerc_ltra_2025_assessment_area_margins.csv``
* ``external-data/derived/nerc/nerc_ltra_2025_emm_zone_margins.gpkg``
* ``external-data/derived/nerc/nerc_ltra_2025_grid_margins.gpkg``

Method summary:

* The numeric source is the PDF's Table 2 reserve-margin table, not a supplemental
  workbook.
* Annual headroom is computed as ``ARM - RML`` for each year from 2026 through 2030.
* The conservative feature carried downstream is
  ``min_margin_headroom_2026_2030``.
* NERC assessment areas are mapped into the repo's ``emm_zone`` polygons through a
  repo-local crosswalk.
* The optional grid artifact is generated by area-weighted transfer from the EMM-zone
  layer and only retains overlapping cells.

This gives the repo a documented public-source reserve-margin feature pipeline that
fits the same regional geometry contract already used by the EER-derived workflows.

Public EER transform
====================

This repository now includes a small public-data utility module that can generate
reVeal-compatible projection CSVs from the unpacked public EER workbook:

The repo also includes a small assessment command that makes the workbook verdict
explicit:

.. code-block:: bash

  python -m reVeal.public_data assess-eer-drop-in

That assessment reports that the workbook is not a direct drop-in replacement for the
fixture projection CSVs, but that the generated public EER national and grouped
regional outputs do match the expected projection schemas.

.. code-block:: bash

  python -m reVeal.public_data generate-eer-loads \
    --workbook external-data/unpacked/eer/ADP2024_detailed_output_data.xlsx \
    --regions tests/data/downscale/inputs/regions/eer_adp_zones.gpkg \
    --output-dir external-data/derived/eer

The current generated files are:

* ``external-data/derived/eer/eer_public_central_high_data_center_national.csv``
* ``external-data/derived/eer/eer_public_central_high_data_center_regional.csv``
* ``external-data/derived/eer/eer_public_central_high_data_center_region_groups.csv``

These files match the projection CSV schemas expected by reVeal, but they represent a
public-source alternative derived from the EER ``Final energy demand`` sheet. They do
not reproduce the shipped fixture magnitudes exactly.

Magnitude-validation guidance for this path is explicit: exact parity with the shipped
fixture magnitudes is not expected. In the current repo state, the derived public
national totals are only about ``10.8%`` to ``18.7%`` of the shipped fixture totals
at the shared years. That means the public EER workflow should be accepted or rejected
based on schema compatibility, footprint reconciliation, coherent growth trend, and
successful downscale smoke-test execution rather than direct magnitude matching.

The repository also includes copied smoke-test configs and a small runner:

.. code-block:: bash

  python external-data/derived/eer/run_downscale_smoke.py \
    external-data/derived/eer/config_public_total_smoke.json \
    --output external-data/derived/eer/downscale-smoke/public_eer_total_downscaled.gpkg

That command has been validated locally and produces a smoke-test GeoPackage on the
existing test grid using the public EER national alternative load projection.

The grouped regional smoke-test config has now also been validated locally with the
same runner pattern, producing a long-form GeoPackage with populated ``year``,
``total_dc_load_mw``, and ``new_dc_load_mw`` columns.

Geospatial staging
==================

The public-data utility can also prepare the next geospatial acquisition steps:

.. code-block:: bash

  python -m reVeal.public_data stage-dataset nwi_wetlands --repo-root .
  python -m reVeal.public_data stage-dataset nlcd --repo-root .
  python -m reVeal.public_data stage-dataset pad_us_gap --repo-root .
  python -m reVeal.public_data stage-dataset fema_nfhl --repo-root .

Those commands keep the explanatory note files under ``external-data/raw``. When a
representative direct package URL exists, the same command can also fetch a concrete
sample payload with ``--download-representative``:

.. code-block:: bash

  python -m reVeal.public_data stage-dataset nwi_wetlands --repo-root . --download-representative
  python -m reVeal.public_data stage-dataset nlcd --repo-root . --download-representative
  python -m reVeal.public_data stage-dataset pad_us_gap --repo-root . --download-representative

For FEMA, the public-data utility can also generate a community-specific direct ZIP
URL when the NFHL inventory table provides the needed fields:

.. code-block:: bash

  python -m reVeal.public_data build-fema-download-url \
    --dfirm-id 01001C \
    --state Alabama \
    --county "Autauga County" \
    --file-name 01001C_20231225.zip

To stage the FEMA note and fetch a representative community ZIP through the same
surface:

.. code-block:: bash

  python -m reVeal.public_data stage-dataset fema_nfhl \
    --repo-root . \
    --download-representative \
    --dfirm-id 01001C \
    --state Alabama \
    --county "Autauga County" \
    --file-name 01001C_20231225.zip

For those sources, the current implementation always creates local note files under
``external-data/raw`` and can now also download one representative payload when a
direct package URL exists or can be generated. That gives the repo a reproducible
inspection and validation workflow without pretending that every authoritative bulk
download is a single clean national package.

The current staging notes now also carry confirmed direct binary or live-service
endpoints where those paths could be verified:

* ``nwi_wetlands``: confirmed direct FWS state-download ZIP pattern, with the
  Alabama geodatabase package verified as a direct binary URL, plus REST and WMS
  endpoints.
* ``nlcd``: confirmed ScienceBase ZIP download URL for the 2023 CONUS land-cover
  package, plus official MRLC WMS and WCS capabilities endpoints.
* ``pad_us_gap``: confirmed ScienceBase ZIP download URL for the PAD-US 4.1 national
  geodatabase, plus stable USGS ArcGIS feature-service views.
* ``fema_nfhl``: confirmed per-community direct ZIP download pattern from the NFHL
  inventory table, with a repo-local helper that can generate the jurisdiction-
  specific URL from ``DFIRMID``, state, county, and filename fields, plus official
  FEMA ArcGIS REST, WMS, and WFS endpoints.

These confirmed URLs improve direct integration and inspection workflows. They also
mean the repo can now fetch representative sample payloads for all four staged public
geospatial datasets through the same CLI surface. They still do not eliminate the
need for selective manual handling when larger or differently scoped extracts are
required. FEMA remains the clearest example: a direct ZIP path exists, but it must be
generated from community-specific inventory fields rather than pulled from a single
national package URL.

Repo anchors
============

These files remain the concrete schema anchors for implementation:

* ``tests/data/downscale/config_total.json``
* ``tests/data/downscale/config_regional.json``
* ``tests/data/downscale/config_region_weights.json``
* ``tests/data/downscale/inputs/load_growth_projections/eer_us-adp-2024-central_national.csv``
* ``tests/data/downscale/inputs/load_growth_projections/eer_us-adp-2024-central_region_groups.csv``
* ``tests/data/downscale/inputs/regions/eer_adp_zones.gpkg``

Those local fixtures define the expected field names, resolution modes, and geometry
interfaces even when the authoritative public source lives elsewhere.