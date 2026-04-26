Data Center Report Bundle
*************************

Bottom Line
===========

This repository now contains a bounded public approximation of the data center
siting report workflow. It is designed to help reviewers inspect candidate
geography, modeled buildout pressure, and known evidence gaps without requiring
the original commercial or unrecovered report inputs.

Be explicit about the boundary: this is not an investment-grade or
report-equivalent reproduction. It is a transparent, repeatable public-data
bundle that keeps the remaining blockers visible.

Where This Came From
====================

The starting point was upstream ``reVeal`` from ``NatLabRockies/reVeal``. The
upstream package is a general geospatial modeling tool for large-load
site-suitability and downscaling workflows. It did not originally contain a
complete data center report reproduction package, executive map, public-source
substitute catalog, or report-parity contract surface.

The report-facing work in this repository is anchored to the staged data center
siting requirements and gap notes under ``external-data/provenance``. The key
source-facing documents are:

* ``external-data/provenance/data-center-siting-report-requirements.md``
* ``external-data/provenance/data-center-siting-parity-matrix.md``
* ``external-data/provenance/report-reproduction-gaps.md``
* ``external-data/provenance/site-suitability-bounded-public-approximation.md``
* ``external-data/provenance/report-output-bounded-public-bundle.md``
* ``external-data/provenance/data-center-bundle-deviations.md``

The report bundle uses tracked code, tests, manifests, provenance notes, and
small derived configuration artifacts to rebuild local outputs. Large source
downloads, runnable example bundles, and generated report payloads stay out of
git.

What Was Added To Upstream reVeal
=================================

This branch adds a report-oriented public-data layer on top of the original
package. The major additions are:

* Repo-local dataset inventory, gap register, and public substitute matrix under
   ``external-data/manifest``.
* Provenance notes for public EER loads, data center baseline inputs, power,
   fiber, gas, land, construction, water, NERC reserve-margin, RIBITS, URDB, and
   report reproduction gaps.
* Public EER transformation commands that generate schema-compatible load
   projection CSVs from the public EER workbook.
* Public proxy workflows for data center inventory, power infrastructure, fiber,
   gas service territories, land value, construction cost, water availability,
   and NERC reserve margin.
* Runnable example-bundle staging and checkpointed public example workflow
   execution.
* A checkpointed public reproduction workflow for the validated public-data
   smoke path.
* A report-bundle generator that writes suitability, feasible-land, proxy-layer,
   cumulative buildout, manifest, limitation, deviation, and contract artifacts.
* A self-contained Executive Siting and Buildout View HTML report with light and
   dark themes, square and hex display modes, risk overlays, priority candidates,
   Census-backed cell identity labels, and cumulative buildout timeline controls.
* Machine-readable contracts for temporal assumptions, capacity constraints,
   grid-resolution parity, allocation assumptions, Baxtel schema readiness, and
   ReEDS handoff expectations.
* Regression tests that assert the report-bundle contracts and HTML affordances
   are present.

What The Bundle Contains
========================

Run ``run-public-report-bundle`` to materialize a local bundle under
``external-data/derived/report-bundle``. The important outputs are:

* ``public_report_suitability_map.html``: Executive browser report for
  suitability, risk overlays, priority cells, and cumulative buildout review.
  Generated and ignored.
* ``public_report_feasible_land.gpkg``: feasible-land footprint from the current
  execution grid, including retained water/wetland-clamped cells. Generated and
  ignored.
* ``public_report_suitability_percentiles.gpkg``: grid-backed suitability
  surface derived from the current ``suitability_score`` field. Generated and
  ignored.
* ``public_report_suitability_ranked_cells.csv``: ranked candidate table with
  stable cell IDs, report-facing labels, and Census-backed identity fields.
  Generated and ignored.
* ``public_report_state_boundaries.gpkg``: context boundary layer used by the
  HTML report. Generated and ignored.
* ``public_report_zoning_proxy.gpkg``: bounded zoning-context proxy, not parcel
  entitlement evidence. Generated and ignored.
* ``public_report_permitting_proxy.gpkg``: bounded permitting / ordinance
  context proxy, not permit readiness. Generated and ignored.
* ``public_report_social_friction_proxy.gpkg``: bounded social-friction context
  proxy, not community acceptance. Generated and ignored.
* ``public_report_hosting_capacity_proxy.gpkg``: bounded hosting-capacity proxy,
  not local interconnection feasibility. Generated and ignored.
* ``public_eer_total_downscaled_cumulative_buildout.gpkg``: cumulative buildout
  geometry for the total smoke output. Generated and ignored.
* ``public_eer_regional_downscaled_cumulative_buildout.gpkg``: cumulative
  buildout geometry for grouped regional smoke output. Generated and ignored.
* ``public_report_bundle_cumulative_buildout_summary.csv``: source/year summary
  of cumulative load and capacity-equivalent values. Generated and ignored.
* ``public_report_assumption_registry.json``: machine-readable scenario,
  temporal, capacity, grid, allocation, Baxtel, and output-label assumptions.
  Generated and ignored.
* ``public_report_grid_resolution_contract.json``: current grid measurement and
  blocked status against the report-reference grid. Generated and ignored.
* ``public_report_allocation_assumption_contract.json``: current
  allocation-method assumptions and report-parity blockers. Generated and
  ignored.
* ``public_report_baxtel_schema_contract.json``: Baxtel procurement/schema
  comparison and trained-suitability blockers. Generated and ignored.
* ``public_report_reeds_integration_contract.json``: handoff contract for
  downstream ReEDS-facing workflows. Generated and ignored.
* ``public_report_bundle_manifest.json``: bundle inventory and assumption
  summary. Generated and ignored.
* ``public_report_bundle_deviations.md``: generated exact-vs-bounded deviation
  note for the local bundle. Generated and ignored.
* ``public_report_census_geography_cache.json``: local cache for U.S. Census
  coordinate GeoLookup responses. Generated cache and ignored.
* ``public_report_census_geolookup_misses.csv`` and
  ``public_report_census_geolookup_misses.md``: review artifacts for retained
  cells where Census did not return named geography. Generated and ignored.

What Is Generated Vs Tracked
============================

Tracked source-of-truth files include:

* Python source and tests under ``reVeal`` and ``tests``.
* Dataset inventory and gap registers under ``external-data/manifest``.
* Human-readable provenance and gap notes under ``external-data/provenance``.
* Small reproducible derived configuration files and README policy files under
   ``external-data/derived``.
* Documentation under ``README.rst``, ``usage.md``, ``PUBLISHING.md``, and
   ``docs/source``.

Ignored local/generated surfaces include:

* ``external-data/raw`` for downloaded source archives and files.
* ``external-data/unpacked`` for extracted working copies.
* ``external-data/examples`` for runnable local example bundles.
* Generated report-bundle HTML, GeoPackage, JSON, CSV, Markdown, and cache
   payloads under ``external-data/derived/report-bundle``. Only the bundle
   ``README.md`` policy file is tracked there.

This keeps the repo lightweight while preserving the code and evidence needed to
recreate the report outputs.

How To Regenerate
=================

From the repository root, regenerate the bounded public report bundle with:

.. code-block:: bash

    python -m reVeal.public_data run-public-report-bundle \
       --output-dir external-data/derived/report-bundle

Useful options:

* ``--resume`` continues from the existing bundle status file.
* ``--force`` discards existing bundle metadata and starts over.
* ``--status-path`` writes bundle status metadata to a custom path.
* ``--no-census-geolookup`` keeps the run fully offline and uses the bounded
   local identity fallback instead of the U.S. Census coordinate GeoLookup API.

After generation, open
``external-data/derived/report-bundle/public_report_suitability_map.html`` in a
browser for the Executive Siting and Buildout View.

What Is Missing Or Still Bounded
================================

* Source report parity: requirements are summarized and mapped to public
   approximations. Exact report inputs and implementation details are not fully
   recovered.
* Grid: the current execution grid is retained as the internal model. The
   report-reference 5.76 km national grid is not reconstructed.
* Baseline year: the bounded bundle records the configured 2022 starting-stock
   field. The report-reference 2025 operating baseline is not yet available.
* Baxtel / trained suitability: public data center baseline and schema contract
   are present. Licensed Baxtel data, exact schema, 2025 baseline, and training
   workflow are not recovered.
* Allocation: current allocation uses the existing weighted-bootstrap downscale
   path and cumulative smoke outputs. Exact report allocation algorithm and
   trained suitability surface are not recovered.
* Feasible-land exclusions: water/wetland cells are retained, flagged, and
   clamped to zero suitability rather than dropped. Full report exclusion stack
   and exact preprocessing rules remain bounded.
* Cell naming: Census GeoLookup-backed labels are generated and cached when
   online access is enabled. Labels are review aids, not authoritative parcel or
   site names.
* Buildout timeline: timeline mode uses cumulative total and regional smoke
   outputs. Temporal parity with the report remains blocked by baseline-year and
   allocation-method gaps.
* Risk overlays: zoning, permitting, social-friction, and hosting-capacity proxy
   layers are present for context. Proxy layers do not prove entitlement, permit
   readiness, acceptance, or interconnection feasibility.
* ReEDS handoff: a machine-readable integration contract names handoff products
   and checks. Downstream use should remain gated by the contract status fields.

Validation
==========

Use these checks before treating the repository as ready for coworker handoff:

.. code-block:: bash

    micromamba run -p /Users/tedtschopp/micromamba/envs/reVeal make -C /Users/tedtschopp/Developer/reVeal/docs html
    micromamba run -p /Users/tedtschopp/micromamba/envs/reVeal python -m pytest tests/test_public_data.py::test_run_public_report_bundle_writes_manifest_and_deviation_note -q
    uvx ruff check ./reVeal && git diff --check

For a full confidence pass, run:

.. code-block:: bash

    micromamba run -p /Users/tedtschopp/micromamba/envs/reVeal python -m pytest -q

Coworker Reading Order
======================

Use this order for a coworker who needs to understand the solution quickly:

#. ``README.rst`` for the project entry point.
#. ``usage.md`` section 7 for the report-bundle command and output inventory.
#. This guide for the operating model and handoff boundary.
#. ``external-data/provenance/data-center-bundle-deviations.md`` for the concise
    exact-vs-bounded gap summary.
#. ``external-data/provenance/report-reproduction-gaps.md`` for the broader data
    sourcing blockers.
#. ``external-data/provenance/data-center-siting-parity-matrix.md`` for row-level
    requirement mapping.
#. ``PUBLISHING.md`` before changing repository ownership, remotes, package
    metadata, or release artifacts.
