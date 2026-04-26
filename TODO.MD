# TODO

Working checklist for reproducing the reports regarding the location of data center
opportunities.

## End Goal

Reproduce the reports seen regarding the location of data center opportunities using
repo-local, documented, repeatable workflows.

If exact reproduction is not possible because a source is commercial, uncited, or
portal-gated, the repo must explicitly distinguish exact reproduction from a
public-source approximation.

## Definition Of Done

- [ ] Every required dataset is either acquired and transformed or replaced with a
      documented public substitute.
- [ ] The transformation logic is implemented in code and backed by validation.
- [ ] The repo contains a documented, repeatable workflow for reproducing the report
      inputs and outputs.
- [ ] Remaining commercial or uncited dependencies are explicitly called out if exact
      parity is not feasible.
- [ ] Any generated report that claims data center siting coverage is traceable to
      the staged requirements in
      `external-data/provenance/data-center-siting-report-requirements.md` or to a
      documented deviation from those requirements.

## Completed Foundation

- [x] Dataset-sourcing scaffolding exists under `external-data/`.
- [x] A tracked reproduction-gap inventory exists under
      `external-data/provenance/report-reproduction-gaps.md`.
- [x] Public EER load generation exists in `reVeal/public_data.py`.
- [x] Public EER national, regional, and region-group CSVs are generated and tracked.
- [x] Public geospatial staging exists for NWI, NLCD, PAD-US, and FEMA NFHL.
- [x] Direct download or service URLs were verified for NWI, NLCD, PAD-US, and FEMA.
- [x] Representative public geospatial downloads can now be staged through
      `python -m reVeal.public_data stage-dataset ... --download-representative`.
- [x] FEMA NFHL helper exists for generating community-specific ZIP URLs.
- [x] RIBITS now has a scripted public webservice acquisition workflow.
- [x] URDB now has a direct staged acquisition workflow.
- [x] Total public-EER smoke test is validated.
- [x] Grouped regional public-EER smoke test is validated.
- [x] Smoke-test runner summary now handles long-form regional outputs correctly.
- [x] Checkpointed public reproduction workflow exists with stop/resume status.
- [x] Generated public example workflows now have a checkpointed runner.
- [x] Saved workflow status files can now be summarized from the CLI.
- [x] The FY26 data center siting report (`NLR/PR-6A20-99256`) is staged under
      `external-data/raw/reports/`.
- [x] Report-derived data center siting requirements are summarized under
      `external-data/provenance/data-center-siting-report-requirements.md`.
- [x] A row-level parity matrix now exists for the report-derived exclusion and
      favorability requirements under
      `external-data/provenance/data-center-siting-parity-matrix.md`.
- [x] The currently missing report favorability features are now explicitly deferred
      and traceable in the manifest and provenance notes.
- [x] The current site-suitability methodology boundary is now documented as a
      bounded public approximation.
- [x] The current bounded public report-output bundle and its deviations are now
      documented.

## Recommended Execution Order

Keep this section aligned with the open checklist below. When priorities or
dependencies change, update this order in the same change.

Current recommended next action: pursue true report-parity blockers now that the
bounded report map and ranked table have cleaner stakeholder-facing labels.

Immediate follow-up order:

1. Pursue true report-parity blockers, including baseline-year assumptions,
      utilization handling, grid resolution, exact downscaling rules, and Baxtel
      suitability-surface parity.

## Priority 1: Core Blockers

- [x] 1. Validate whether the public EER workbook can serve as a drop-in replacement.
      Evidence: `external-data/provenance/eer-public-data.md` says this is not yet
      proven.
      Compare against these schema anchors:
      `tests/data/downscale/config_total.json`
      `tests/data/downscale/config_regional.json`
      `tests/data/downscale/inputs/load_growth_projections/eer_us-adp-2024-central_national.csv`
      `tests/data/downscale/inputs/load_growth_projections/eer_us-adp-2024-central_region_groups.csv`
      Outcome: completed. `python -m reVeal.public_data assess-eer-drop-in`
      shows the workbook is not a direct drop-in replacement. It remains a
      transformable public-source alternative whose generated national and grouped
      regional CSV outputs match the required projection schemas.

- [x] 2. Implement the NERC reserve-margin feature pipeline.
      Evidence: `external-data/provenance/nerc/nerc-ltra-2025.md` now records the
      implemented transform and derived outputs.
      Outcome: completed. The usable reserve-margin values were taken from Table 2 in
      the staged 2025 LTRA PDF, mapped from NERC assessment areas into the repo's
      `emm_zone` geometry, and exposed through
      `python -m reVeal.public_data generate-nerc-reserve-margin-features`. The
      workflow now writes an assessment-area margin CSV, an EMM-zone feature GPKG,
      and an optional overlapping-cell grid GPKG under `external-data/derived/nerc/`.

- [x] 3. Move public geospatial layers from staging-prepared to actually acquired and
      usable.
      Evidence: `external-data/manifest/dataset-manifest.csv` lists the four public
      geospatial datasets as `staging-prepared`.
      Required datasets:
      `nwi_wetlands`
      `nlcd`
      `pad_us_gap`
      `fema_nfhl`
      Outcome: completed. `python -m reVeal.public_data stage-dataset ...
      --download-representative` now stages the note file and can fetch one
      representative payload for all four public geospatial datasets, including the
      helper-generated FEMA community ZIP workflow. The manifest statuses were moved
      from `staging-prepared` to `representative-download-ready` and the commands are
      documented in `external-data/provenance/public-geospatial-staging.md`.

- [x] 4. Inventory the remaining exact-vs-proxy reproduction gaps.
      Evidence: `external-data/manifest/gap-register.csv` and
      `external-data/manifest/open-substitutes.csv`.
      Outcome: completed in
      `external-data/provenance/report-reproduction-gaps.md`, which turns the
      remaining blockers into one commercial dependency, one implemented power
      proxy workflow, one implemented fiber proxy workflow, one implemented gas
      territory assembly workflow, one implemented land-value proxy workflow, one
      implemented construction-cost proxy workflow, one implemented water proxy
      workflow, and one portal-friction acquisition workflow.

## Priority 2: Gap Closure Backlog

- [x] 5. Build a first-pass public baseline for data center locations (`gap_001`).
      Exact blocker: Baxtel is commercial and was the cited presentation source.
      Public path: OpenStreetMap + Wikidata + operator announcements + permitting
      records.
      Required outcome: a reproducible baseline layer plus explicit non-equivalence
      notes versus Baxtel.
      Outcome: completed. The repo now includes
      `python -m reVeal.public_data generate-data-center-baseline`, repo-local
      staging notes for the exported OSM, Wikidata, and manual augmentation inputs,
      derived-output documentation under `external-data/derived/data-centers/`, and
      explicit non-equivalence notes versus Baxtel in
      `external-data/provenance/data-center-public-baseline.md`.

- [x] 6. Choose and implement the transmission and substation proxy stack
      (`gap_002`).
      Exact blocker: the presentation does not cite a definitive national source for
      substations or for transmission lines greater than 135 kV.
      Public path: OpenStreetMap power features plus public utility or federal GIS
      where available.
      Required outcome: a documented national baseline, filtering rules, and stated
      fidelity limits.
      Outcome: completed. The repo now includes
      `python -m reVeal.public_data generate-power-infrastructure-baseline`, repo-local
      staging notes for exported OSM transmission-line and substation payloads,
      derived-output documentation under `external-data/derived/power/`, and explicit
      filtering and fidelity-limit notes in
      `external-data/provenance/power-infrastructure-public-baseline.md`.

- [x] 7. Choose and implement the onshore fiber proxy stack (`gap_003`).
      Exact blocker: the presentation does not cite route geometry, and FCC
      availability data is not route geometry.
      Public path: FCC Broadband Data Collection plus OSM telecom layers.
      Required outcome: a proxy geometry method and an explicit statement of how it
      differs from exact fiber-route proximity.
      Outcome: completed. The repo now includes
      `python -m reVeal.public_data generate-fiber-proxy-rasters`, repo-local staging
      notes for exported OSM telecom linework and FCC fiber-availability polygons,
      derived-output documentation under `external-data/derived/fiber/`, and explicit
      non-equivalence notes in `external-data/provenance/fiber-public-proxy.md` that
      distinguish availability coverage from route-proximity geometry.

- [x] 8. Choose and implement the natural-gas territory proxy stack (`gap_004`).
      Exact blocker: no national open gas service-territory layer is cited.
      Public path: state public service commission service-territory layers where
      available.
      Required outcome: a state-by-state assembly workflow or an explicit national
      deferral decision.
      Outcome: completed. The repo now includes
      `python -m reVeal.public_data generate-gas-service-territory-baseline`, a local
      manifest-schema staging note for state extracts, derived-output documentation
      under `external-data/derived/gas/`, and explicit notes in
      `external-data/provenance/gas-service-territory-public-baseline.md` that this is
      a state-by-state assembly workflow rather than a claim of complete national
      coverage.

- [x] 9. Choose and implement the land-value proxy stack (`gap_005`).
      Exact blocker: no national open land fair market value source or preprocessing
      method is cited.
      Public path: county assessor parcel values or public land-value proxies.
      Required outcome: a first-pass normalization approach and explicit notes on
      cross-jurisdiction comparability limits.
      Outcome: completed. The repo now includes
      `python -m reVeal.public_data generate-land-value-proxy-features`, a staged
      input-schema note for county proxy and polygon inputs, derived-output
      documentation under `external-data/derived/land/`, and explicit notes in
      `external-data/provenance/land-value-public-proxy.md` that the
      `state_land_value_index` is a within-state normalization rather than a claim of
      cross-state land-price comparability.

- [x] 10. Choose and implement the construction-cost proxy stack (`gap_006`).
      Exact blocker: no public national dollars-per-MW construction-cost source is
      cited.
      Public path: regional wage and price proxies from public labor data.
      Required outcome: a documented proxy formula and explicit non-equivalence to
      presentation construction-cost values.
      Outcome: completed. The repo now includes
      `python -m reVeal.public_data generate-construction-cost-proxy-features`, a
      staged input-schema note for county wage-and-price proxy and polygon inputs,
      derived-output documentation under `external-data/derived/construction/`, and
      explicit notes in
      `external-data/provenance/construction-cost-public-proxy.md` that the proxy
      formula `construction_cost_proxy_score = construction_worker_mean_wage_usd *
      regional_price_parity_index / 100` is a relative affordability screen rather
      than an exact dollars-per-MW construction-cost estimate.

- [x] 11. Choose and implement the water-availability transformation (`gap_007`).
      Exact blocker: the presentation does not cite the source or spatial
      transformation for total water availability.
      Public path: USGS water-use or water-availability proxies.
      Required outcome: a selected source, transformation method, and documented
      mismatch versus the presentation concept.
      Outcome: completed. The repo now includes
      `python -m reVeal.public_data generate-water-availability-proxy-features`, a
      staged input-schema note for a state freshwater-withdrawal proxy CSV,
      derived-output documentation under `external-data/derived/water/`, and explicit
      mismatch notes in `external-data/provenance/water-availability-public-proxy.md`
      explaining that state withdrawal is only a coarse proxy for site-level water
      availability.

- [x] 12. Finalize the RIBITS acquisition approach (`gap_008`).
      Exact blocker: automated retrieval hit portal friction during research.
      Public path: manual acquisition through the public portal.
      Outcome: completed. The repo first recorded a staged acquisition note through
      `python -m reVeal.public_data stage-dataset ribits --repo-root .`, and item 17
      later promoted that source to a scripted public webservice workflow through
      `python -m reVeal.public_data download-ribits-bank-sites`. The current posture
      is recorded in `external-data/provenance/ribits-manual-acquisition.md`, and the
      dataset manifest now tracks RIBITS as `scripted-webservice-workflow-defined`.

## Priority 3: Dataset And Feature Follow-Through

- [x] 13. Add or explicitly defer URDB acquisition and staging.
      Evidence: `external-data/manifest/dataset-manifest.csv` marks `urdb` as
      `not-acquired`.
      Outcome: completed. The repo now stages URDB directly through
      `python -m reVeal.public_data stage-dataset urdb --repo-root .` using the
      OpenEI approved-rates bulk export as the default acquisition surface. The
      decision is recorded in `external-data/provenance/urdb-acquisition.md`, and the
      dataset manifest status was moved to `direct-download-ready`.

## Priority 4: Validation And Documentation Hardening

- [x] 14. Add magnitude-validation guidance for public EER outputs.
      Evidence: `external-data/provenance/eer-public-derived-loads.md` says the
      generated public EER files do not recreate the shipped fixture magnitudes
      exactly.
      Required outcome: define acceptable mismatch or explicitly document that exact
      parity is not expected.
      Outcome: completed. The repo now makes that guidance explicit in
      `external-data/provenance/eer-public-derived-loads.md`,
      `external-data/provenance/eer-public-downscale-smoke.md`,
      `external-data/derived/eer/README.md`, and `docs/source/misc/datasets.rst`.
      The current documented posture is that fixture-magnitude parity is not expected
      for the public EER path, and that validation should focus instead on schema
      compatibility, same-footprint reconciliation, coherent growth trend, and
      successful smoke-test execution.

- [x] 15. Update top-level usage documentation for the public-data workflow.
      Evidence: `usage.md` was still skeletal.
      Required commands to document:
      `python -m reVeal.public_data list-datasets`
      `python -m reVeal.public_data stage-dataset ...`
      `python -m reVeal.public_data build-fema-download-url ...`
      `python -m reVeal.public_data generate-eer-loads ...`
      `python external-data/derived/eer/run_downscale_smoke.py ...`
      Outcome: completed. `usage.md` now documents the public-data workflow end to
      end, including dataset inspection, staging, FEMA NFHL URL generation, public
      EER load generation, smoke-test execution, and the relationship between the
      public-data CLI and the core `reVeal` CLI surface.

## Priority 5: Commercial, Automation, And Workflow Readiness

- [x] 16. Evaluate the Baxtel commercial sample and schema-capture path.
      Evidence: `external-data/manifest/dataset-manifest.csv` now tracks
      `baxtel_us_data_center_sites` as `commercial-procurement-defined`, and
      `https://baxtel.com/services/datasets` advertises a sample CSV, schema
      documentation, snapshot delivery, and a quote workflow.
      Required outcome: determine whether a Baxtel sample or licensed snapshot can be
      obtained for schema review, stage a repo-local acquisition note for that path,
      and explicitly record whether Baxtel remains an out-of-scope commercial
      dependency or becomes a reproducible manual procurement dependency.
      Outcome: completed. The repo now stages a Baxtel procurement note through
      `python -m reVeal.public_data stage-dataset baxtel_us_data_center_sites
      --repo-root .`, records the sample and quote workflow in
      `external-data/provenance/baxtel-acquisition.md`, and updates
      `external-data/manifest/dataset-manifest.csv` so Baxtel is tracked as a
      defined commercial procurement dependency rather than an undefined missing
      source.

- [x] 17. Re-test RIBITS for durable automation instead of treating manual-only as
      final.
      Evidence: the live RIBITS site exposes a public webservices page at
      `https://ribits.ops.usace.army.mil/ords/f?p=107:353::::::` and documents
      `bank_site_list` plus `bank_site_data` ORDS endpoints with example requests.
      Required outcome: inspect the portal's export behavior for stable downloadable
      endpoints or service calls, then either implement a scripted staging path in
      `reVeal.public_data` or document the precise blocker that keeps RIBITS
      manual-only.
      Outcome: completed. The repo now includes
      `python -m reVeal.public_data download-ribits-bank-sites`, which stitches the
      documented public `bank_site_list` and `bank_site_data` webservices into a
      repo-local JSON snapshot. The acquisition note, manifest status, and gap
      register were updated accordingly, so RIBITS is no longer treated as a
      manual-only source.

- [x] 18. Promote the remaining public dataset workflows from spec-ready to
      execution-ready.
      Evidence: multiple datasets still stop at `representative-download-ready`,
      `direct-download-ready`, or `generated-on-demand` in
      `external-data/manifest/dataset-manifest.csv` rather than having a complete
      staged input bundle or a validated example run.
      Target datasets:
      `nwi_wetlands`, `nlcd`, `pad_us_gap`, `fema_nfhl`, `urdb`,
      `public_data_center_baseline`, `public_power_infrastructure_baseline`,
      `public_fiber_proxy_baseline`, `public_gas_service_territory_baseline`,
      `public_land_value_proxy`, `public_construction_cost_proxy`, and
      `public_water_availability_proxy`.
      Required outcome: for each remaining dataset family, provide either a
      representative staged input bundle plus a validated example command, or an
      explicit note explaining why only schema-level staging is currently feasible.
      Outcome: completed. The manifest statuses for the remaining public dataset
      families were moved to `execution-ready`, the repo now supports
      `python -m reVeal.public_data stage-example-bundle <bundle_id> --repo-root .`
      for the generated proxy workflows, and each bundle writes a README with the
      validated end-to-end command and expected outputs. The external acquisition
      surfaces (`nwi_wetlands`, `nlcd`, `pad_us_gap`, `fema_nfhl`, and `urdb`) are
      now documented as validated example acquisition commands in
      `external-data/provenance/public-dataset-execution-ready.md`, alongside the
      execution-ready bundle workflow for the generated dataset families.

## Priority 6: Report-Derived Data Center Siting Requirements

- [x] 19. Build the report-derived parity matrix for exclusion and favorability
      requirements.
      Evidence:
      `external-data/provenance/data-center-siting-report-requirements.md` and the
      staged report `external-data/raw/reports/nlr-pr-6a20-99256-leveraging-reveal-for-data-center-siting.pdf`
      identify explicit feasibility exclusions, favorability features, and output
      expectations that are not yet represented as one repo coverage matrix.
      Required outcome: enumerate every report requirement as one of `implemented`,
      `proxy-implemented`, `commercial-blocked`, `public-source-missing`, or
      `not-yet-modeled`, and use that matrix as the requirement source for all future
      report-generation work.
      Outcome: completed. The repo now tracks this row-level view in
      `external-data/provenance/data-center-siting-parity-matrix.md`, covering the
      named exclusion and favorability requirements from the staged report and the
      LinkedIn follow-up notes.

- [x] 20. Implement or explicitly defer the missing report-table favorability
      features.
      Evidence: the report's feature table requires operating-generator proximity,
      retired-generator proximity, planned-generator proximity, gas pipeline
      proximity, natural hazard building loss rate, projected cooling degree days
      for 2035, residential electricity rate, electricity service-territory count,
      and data center construction labor in addition to the public proxy workflows
      already completed.
      Required outcome: add executable workflows or explicit deferrals for each
      missing feature so the suitability input stack used for generated reports is
      report-traceable end to end.
      Outcome: completed through explicit deferral. The repo now records the full
      missing set in `external-data/provenance/report-favorability-feature-deferrals.md`
      and traces each deferred feature in `external-data/manifest/dataset-manifest.csv`
      with status `explicitly-deferred`, rather than leaving them implicit.

- [x] 21. Reproduce the report's site suitability methodology or document the
      bounded public approximation.
      Evidence: the report uses random-forest-derived feature importance, a
      positive-unlabeled framing, and Baxtel locations for training and initialization.
      LinkedIn Part I adds that the trained model should learn location
      characteristics from existing data centers, weight feasible land with machine
      learning, and score and rank a nationwide suitability surface, while the
      current backlog mainly covers data acquisition and intermediate feature
      generation.
      Required outcome: either implement the report-aligned site suitability
      weighting workflow, including commercial dependency notes where needed, or
      define one documented public approximation that all generated reports must use
      consistently.
      Outcome: completed through explicit approximation policy. The repo now records
      that boundary in
      `external-data/provenance/site-suitability-bounded-public-approximation.md`,
      including what the current public workflows can validate, what they cannot
      claim, and what conditions must be met before report-equivalent methodology can
      be asserted.

- [x] 22. Complete the bounded public report-layer outputs and downscaling bundle.
      Evidence: the report explicitly presents a feasible-land map, a suitability
      percentile map, and downscaled deployment results through 2050 using a 5.76 km
      grid, an 88% utilization factor, and a maximum 1 GW per site per time-step.
      LinkedIn Part I adds a high-resolution national-scale output showing where
      data centers are likely to be built and a scored and ranked nationwide
      surface, while LinkedIn Part II adds a cumulative 25-year buildout view,
      methodical distribution of EER regional projections to the suitability
      surface, and presentation of existing plus modeled data centers on a 5 km
      grid.
      Current bounded progress is documented in
      `external-data/provenance/report-output-bounded-public-bundle.md`, which
      captures the existing commands, configs, validations, and the remaining
      deviations from report parity. Bounded execution now also includes
      `python -m reVeal.public_data run-public-report-bundle --output-dir external-data/derived/report-bundle`,
      which materializes a report-facing bundle directory with nested reproduction
      status, a machine-readable manifest, an explicit deviation note, bounded
      feasible-land and suitability-percentile GeoPackages derived from the current
      execution grid, a bounded nationwide ranked suitability CSV derived from that
      suitability layer, cumulative buildout GeoPackages for the total and grouped
      regional smoke outputs, and a year-summary CSV derived from those time-stepped
      outputs.
      Required outcome: add tracked commands, configs, and validation checks that
      generate bounded public report outputs from repo-local inputs while making any
      deviations from the report assumptions explicit. This includes time-stepped
      outputs that can support cumulative buildout maps or animations.
      Outcome: completed for the bounded public bundle. The repo now generates the
      report-facing bundle through
      `python -m reVeal.public_data run-public-report-bundle --output-dir external-data/derived/report-bundle`,
      writes machine-readable status, manifest, assumption-registry, limitations,
      ranked-suitability, feasible-land, suitability-percentile, cumulative-buildout,
      year-summary, and ReEDS handoff artifacts, and documents the remaining
      deviations from report parity in
      `external-data/provenance/report-output-bounded-public-bundle.md`. True
      report-parity work is split into separate open follow-up items rather than
      hidden inside this bounded-bundle item.

- [x] 23. Integrate the additional requirements from the LinkedIn Part I and Part II
      descriptions.
      Evidence: the LinkedIn texts now explicitly describe trained nationwide
      suitability scoring, regional EER projections being distributed across the
      suitability surface, cumulative 25-year buildout, 5 km grid aggregation for
      existing and modeled data centers, user-controlled scenario assumptions,
      ReEDS integration intent, and known refinement gaps.
      Outcome: completed. Those additions are now incorporated in
      `external-data/provenance/data-center-siting-report-requirements.md`, and the
      remaining backlog items were sharpened accordingly.

- [x] 24. Add a report-assumption registry for scenario-controlled outputs.
      Evidence: the LinkedIn Part II description says reVeal allows complete control
      over assumptions and can model multiple scenarios, while the current repo does
      not yet expose one report-focused registry of those assumptions.
      Required outcome: define tracked scenario inputs, assumptions, and output
      labels for report generation so future report runs are comparable and
      reproducible.
      Outcome: completed. `python -m reVeal.public_data run-public-report-bundle`
      now writes `external-data/derived/report-bundle/public_report_assumption_registry.json`,
      which records the tracked total and regional smoke-config inputs,
      report-reference assumptions, current bounded bundle assumptions, output
      labels, and explicit assumption gaps for the current report surface.

- [x] 25. Carry forward the LinkedIn limitation and refinement set into report
      outputs.
      Evidence: the LinkedIn Part II description explicitly names local transmission
      hosting capacity, demand queue times, zoning, permitting and ordinance
      information, more representative capacity scaling, and social acceptance as
      missing or future refinements. LinkedIn Part I reinforces this with
      realistically scaled capacity by market trends.
      Required outcome: ensure generated reports and provenance notes explicitly
      surface those limitations whenever they are not implemented, rather than
      implying full siting fidelity.
      Outcome: completed. `python -m reVeal.public_data run-public-report-bundle`
      now writes `external-data/derived/report-bundle/public_report_limitations.md`,
      and the same limitation set is carried into
      `external-data/derived/report-bundle/public_report_assumption_registry.json`.
      The bundle and provenance note now explicitly surface local transmission
      hosting capacity, demand queue times, zoning, permitting and ordinance
      information, capacity scaling by market trends, and social acceptance as
      active fidelity limits when they are not implemented.

- [x] 26. Define the reVeal-to-ReEDS integration contract for report outputs.
      Evidence: LinkedIn Part I states that reVeal is being integrated with ReEDS to
      enable high-resolution load forecasting for advanced power systems modeling,
      but the current backlog does not yet define the required handoff surface.
      Required outcome: document or implement the data products, schema contract,
      temporal assumptions, and validation checks needed for report-oriented reVeal
      outputs to interoperate with ReEDS-facing workflows.
      Outcome: completed. `python -m reVeal.public_data run-public-report-bundle`
      now writes
      `external-data/derived/report-bundle/public_report_reeds_integration_contract.json`,
      which defines the bounded handoff products, required columns, annual modeled
      years, spatial join keys, supporting artifacts, and validation checks for the
      current reVeal-to-ReEDS report-output surface.

- [x] 27. Add table-to-map hover highlighting for the bounded D3 suitability map.
      Evidence: `external-data/derived/report-bundle/public_report_suitability_map.html`
      now renders the top-ranked table and the mapped cells, but hovering a ranked
      row does not yet outline the corresponding grid cell on the map.
      Required outcome: when an operator hovers a row in the `Top Ranked Cells`
      table, the matching mapped cell is highlighted with a visible outline and the
      interaction is documented and regression-tested with the bounded report-bundle
      workflow.
      Outcome: completed. `python -m reVeal.public_data run-public-report-bundle`
      now writes a D3 map page whose ranked rows and mapped suitability cells share
      a stable cell-id binding, so hovering a table row outlines the matching map
      cell. The interaction is regression-tested in `tests/test_public_data.py` and
      documented in
      `external-data/provenance/report-output-bounded-public-bundle.md`.

- [x] 28. Assign human-readable place names to ranked suitability cells.
      Evidence: the bounded report bundle currently exposes ranked cells only by
      numeric `cell_id`, which is difficult to interpret without GIS context.
      Required outcome: use each cell's longitude and latitude to look up the
      dominant city or metropolitan feature in that cell and the dominant natural
      feature or monument in that cell, select the more recognizable of the two
      using a documented reproducible popularity rule, and surface that derived cell
      name in the bounded report-bundle outputs alongside the numeric cell id.
      Outcome: completed. The bounded suitability GeoPackage, ranked suitability
      CSV, and D3 map page now carry deterministic `cell_name` values plus the
      selected basis and candidate feature metadata. The current naming rule uses a
      curated public metro and natural-feature catalog with fixed popularity scores,
      prefers in-cell matches, falls back to the nearest class-specific catalog
      feature when needed, and chooses the higher-popularity class winner as the
      final cell name. That rule is documented in
      `external-data/provenance/report-output-bounded-public-bundle.md` and
      regression-tested in `tests/test_public_data.py`.

- [x] 29. Make each bounded suitability cell name unique.
      Evidence: the current bounded naming workflow can assign the same
      human-readable `cell_name` to multiple nearby cells when they share the same
      dominant metro or natural-feature anchor, which makes table rows harder to
      distinguish operationally.
      Required outcome: extend the bounded naming workflow so every mapped cell has
      a unique display name while preserving the current human-readable place logic,
      document the disambiguation rule, and regression-test the updated output
      contract for the ranked suitability CSV and D3 map.
      Outcome: completed. The bounded naming workflow now preserves the original
      human-readable anchor as `base_cell_name`, rewrites duplicate display names
      into a gateway-place format such as `5.6 miles South of Tusayan, Coconino
      County, AZ near Grand Canyon`, and surfaces a
      `cell_name_is_disambiguated` flag in the suitability and ranked outputs.
      The updated contract is documented in
      `external-data/provenance/report-output-bounded-public-bundle.md` and
      regression-tested in `tests/test_public_data.py`.

- [x] 30. Overlay state boundaries as a transparent map layer above the bounded D3 map.
      Evidence: the current D3 page renders feasible land and suitability cells but
      does not provide state-boundary context for quick orientation.
      Required outcome: add a reproducible state-boundary overlay to
      `external-data/derived/report-bundle/public_report_suitability_map.html` as a
      transparent contextual layer that sits above the suitability cells without
      obscuring them, and document and regression-test that map enhancement.
      Outcome: completed. The bounded report bundle now stages an official Census
      state-boundary source into a derived
      `public_report_state_boundaries.gpkg`, reprojects it into the suitability
      layer CRS, and embeds it into the D3 page as a transparent stroke-only layer
      above the suitability cells. The new artifact and overlay behavior are
      documented in `external-data/provenance/report-output-bounded-public-bundle.md`
      and regression-tested in `tests/test_public_data.py`.

- [x] 31. Add a zoning layer or bounded zoning proxy to the report-bundle map surface.
      Evidence: the current quick-read note and limitations explicitly say the
      bounded map does not add the missing zoning layer.
      Required outcome: define the source or bounded proxy decision for zoning,
      stage the resulting geospatial layer, and wire it into the report-bundle map
      and provenance so the limitation is either reduced or made explicit at the
      layer level.
      Outcome: completed. The bounded report bundle now stages an NLCD-derived
      `public_report_zoning_proxy.gpkg` that transfers developed-land context onto
      the execution-grid cells as a coarse zoning proxy, exposes a `Zoning Proxy`
      toggle in the D3 page, updates the carried limitation posture to `bounded
      proxy`, and regression-tests the new artifact and map contract in
      `tests/test_public_data.py`.

- [x] 32. Add a permitting layer or bounded permitting proxy to the report-bundle map surface.
      Evidence: the current quick-read note and limitations explicitly say the
      bounded map does not add permitting information.
      Required outcome: define the source or bounded proxy decision for permitting,
      stage the resulting geospatial layer, and wire it into the report-bundle map
      and provenance so the limitation is either reduced or made explicit at the
      layer level.
      Practical path: define a bounded permitting / ordinance evidence proxy with a
      staged CSV or GeoPackage manifest, generate
      `public_report_permitting_proxy.gpkg`, add a D3 map toggle, update the
      assumption registry, limitations note, provenance, and tests.
      Outcome: completed. The bounded report bundle now reads staged
      `external-data/manifest/permitting-ordinance-evidence.csv` rows, assigns
      public evidence points to execution-grid cells, writes
      `public_report_permitting_proxy.gpkg`, exposes a `Permitting / Ordinance
      Proxy` toggle in the D3 page, updates the carried limitation posture to
      `bounded proxy`, and regression-tests the artifact, map contract, and proxy
      classes in `tests/test_public_data.py`.

- [x] 33. Add a hosting-capacity layer or bounded hosting-capacity proxy to the report-bundle map surface.
      Evidence: the current quick-read note and limitations explicitly say the
      bounded map does not add local transmission hosting-capacity information.
      Required outcome: define the source or bounded proxy decision for
      hosting-capacity, stage the resulting geospatial layer, and wire it into the
      report-bundle map and provenance so the limitation is either reduced or made
      explicit at the layer level.
      Outcome: completed through a bounded proxy. The bundle now stages
      `public_report_hosting_capacity_proxy.gpkg`, which transfers the existing
      NERC reserve-margin headroom values onto the execution-grid cells as a coarse
      regional hosting-capacity proxy, exposes the result in the assumption
      registry, and wires an optional `Hosting Capacity Proxy` overlay into the D3
      map while keeping the limitation explicit that this is not local transmission
      hosting-capacity headroom.

- [x] 34. Add a social-friction layer or bounded social-friction proxy to the report-bundle map surface.
      Evidence: the current quick-read note and limitations explicitly say the
      bounded map does not add social-acceptance information.
      Required outcome: define the source or bounded proxy decision for social
      friction, stage the resulting geospatial layer, and wire it into the
      report-bundle map and provenance so the limitation is either reduced or made
      explicit at the layer level. Be explicit that this is a social-friction proxy,
      not a claim to measure actual social acceptance.
      Practical path: use manually curated public evidence such as local opposition
      records, public hearing outcomes, civic organization objections, appeal
      records, or news-documented siting conflicts. Wire it into the same bundle,
      map, test, and provenance pattern as zoning, permitting, and hosting capacity.
      Outcome: completed. The bounded report bundle now reads staged
      `external-data/manifest/social-friction-evidence.csv` rows, assigns public
      evidence points to execution-grid cells, writes
      `public_report_social_friction_proxy.gpkg`, exposes a `Social-Friction Proxy`
      toggle in the D3 page, updates the carried limitation posture to `bounded
      proxy`, and regression-tests the artifact, map contract, and proxy classes in
      `tests/test_public_data.py`. The provenance note is explicit that this is a
      social-friction evidence proxy, not a measurement of actual social acceptance.

- [x] 35. Resolve manifest drift for the RIBITS acquisition posture.
      Evidence: `external-data/manifest/gap-register.csv` previously described
      RIBITS as `manual-only-workflow-defined`, while this checklist and the
      provenance notes said it had a scripted ORDS workflow.
      Required outcome: update the gap register or make the distinction explicit so
      the manifest, TODO, and provenance records agree. This is small, but it matters
      because the repo is becoming a traceability system.
      Outcome: completed. The gap register now describes RIBITS as a scripted public
      webservice workflow through the ORDS `bank_site_list` and `bank_site_data`
      endpoints, and reframes the remaining blocker as the downstream transform from
      staged snapshot to report-aligned exclusion-layer geometry.

- [x] 36. Decide the version-control policy for generated report-bundle outputs.
      Evidence: the report-bundle status confirms generated outputs are complete in
      `external-data/derived/report-bundle/public_report_bundle_status.json`, but the
      HTML map is large and several derived GeoPackages and CSVs are generated
      artifacts.
      Required outcome: decide what should be committed versus regenerated from
      commands. Prefer tracked commands plus small manifests over large generated
      blobs unless the artifact itself is part of the deliverable.
      Outcome: completed. The repo now treats the report bundle as a regenerated
      local deliverable rather than tracked source. Commit source code, regression
      tests, schema-only evidence manifests, provenance notes, usage docs, Sphinx
      docs, and the report-bundle README policy. Regenerate the HTML report,
      GeoPackages, output JSON, generated Markdown, ranked CSV, cumulative summary,
      cache payloads, and regenerated NERC GeoPackages from tracked commands when
      needed.

- [x] 37. Visually QA the D3 suitability map surface.
      Evidence: `external-data/derived/report-bundle/public_report_suitability_map.html`
      now includes base suitability cells, state boundaries, optional zoning,
      permitting, social-friction, and hosting overlays, ranked-table hover behavior,
      and display-only hexagons.
      Required outcome: open the generated map and verify that base cells render,
      state boundaries render, the zoning toggle works, the permitting toggle works,
      the social-friction toggle works, the hosting toggle works, ranked-table hover
      highlights the correct cell, and text does not overlap.
      Outcome: completed. Browser inspection verified that the generated report page
      renders the base map, contextual layer controls, ranked-cell table, and tooltip
      content, and surfaced the known display issue that the per-cell fitted hexes did
      not tile coherently.

- [x] 38. Fix the report-map hexagon tiling geometry.
      Evidence: visual inspection of
      `external-data/derived/report-bundle/public_report_suitability_map.html` shows
      the display-only hexagons are not tiled correctly, even though the grid remains
      the internal model.
      Required outcome: correct the D3 display geometry so the hexagons tile
      coherently over the grid-backed suitability cells, preserve stable cell IDs and
      hover behavior, document the display-only nature of the hex layer, and add a
      regression check that would catch the observed tiling defect.
      Outcome: completed. The D3 generator now computes shared honeycomb tile
      metrics from the projected suitability surface, assigns cells to staggered
      display row/column slots, and reuses the same display center across the
      feasible, suitability, zoning, permitting, social-friction, and hosting layers.
      The original grid geometries and stable cell IDs remain the internal model, and
      the report-bundle regression now checks for the staggered honeycomb contract.
      The generated report also now exposes a Squares/Hexes display switch so state
      boundaries can be reviewed against geographically aligned source-cell geometry
      while still preserving the honeycomb scan view. Hex mode now uses snapped
      state-boundary outlines built from hex-cell edges, so the boundary context
      lines up with the honeycomb display instead of crossing repositioned cells.

- [x] 39. Add a dark, light, and system mode switcher to the generated HTML report.
      Evidence: the generated D3 suitability map currently has one fixed visual theme,
      which limits readability across room lighting, projector settings, and user
      accessibility preferences.
      Required outcome: add a visible theme control with dark, light, and system
      options; persist the explicit user choice for the local report when practical;
      default to system preference when no explicit choice exists; and verify that
      map fills, overlays, legends, table rows, hover highlights, and tooltips remain
      readable in all three modes.
      Outcome: completed. The generated D3 report now exposes a System/Light/Dark
      theme control, stores the selected mode in local storage when available,
      defaults to system preference when no explicit mode is set, and resolves CSS
      variables for map background, panels, controls, table rows, state outlines,
      active highlights, and tooltips across light and dark themes.

- [ ] 40. Define the report-parity baseline year and buildout horizon assumptions.
      Evidence: the bounded public bundle can emit cumulative buildout products, but
      the report-parity baseline and time horizon are still recorded as deviations
      rather than implemented assumptions.
      Required outcome: identify the report-equivalent baseline year, modeled years,
      existing-data-center starting stock, and cumulative-buildout horizon; encode
      those assumptions in tracked config or metadata; and update the bounded bundle
      only when the assumptions can be validated against report requirements.

- [ ] 41. Implement report-parity utilization and per-site capacity constraints.
      Evidence: the report references an 88% utilization factor and a maximum 1 GW per
      site per time-step, while the bounded public bundle currently documents these as
      parity gaps.
      Required outcome: implement configurable utilization and per-site/time-step
      capacity constraints in the report-output workflow, add validation coverage, and
      keep the limitation explicit if exact report semantics cannot be recovered.

- [ ] 42. Evaluate and implement report-equivalent national grid resolution.
      Evidence: the report references a 5.76 km grid and LinkedIn text references a
      5 km aggregation surface, while the bounded public bundle currently uses the
      repo's existing execution grid.
      Required outcome: determine the correct report-equivalent grid contract,
      generate or document the national grid needed for parity, preserve stable cell
      IDs, and validate that downstream map, ranked-table, and downscaling outputs use
      the intended spatial footprint.

- [ ] 43. Implement exact report downscaling allocation assumptions where recoverable.
      Evidence: the bounded public bundle distributes public smoke-test EER outputs
      onto the current suitability surface, but the report's exact allocation rules are
      not yet proven equivalent.
      Required outcome: recover, encode, and test the report-aligned allocation rules
      for regional EER projections, cumulative buildout, and time-stepped outputs; if
      the exact assumptions remain unavailable, document the non-equivalence as an
      explicit parity blocker.

- [ ] 44. Obtain Baxtel schema evidence and decide the trained-suitability parity path.
      Evidence: the largest remaining strategic blocker is still Baxtel/schema
      parity. The repo has a procurement path, but exact reproduction remains blocked
      until a sample or licensed schema is obtained and compared against the public
      baseline.
      Required outcome: obtain a sample or licensed Baxtel schema, compare it against
      the public baseline, and use that comparison to decide whether the
      report-aligned Baxtel-trained suitability surface is feasible or must remain
      explicitly non-equivalent.

- [x] 45. Fix the generated name labels for report-bundle cells.
      Evidence: the bounded report-bundle map and ranked-cell table now expose
      human-readable cell labels, but some labels can be operationally confusing in
      places with complex geography, nearby gateway cities, or distant fallback
      anchors.
      Required outcome: review the current `cell_name`, `base_cell_name`, naming
      basis, anchor-place, and candidate-feature fields; tighten the naming and
      disambiguation rules so labels are clear, local, and stable; document the
      revised rule; and regression-test the ranked CSV and D3 map label contract.
      Outcome: reopened and completed with a geographic identity-stack model. The
      bounded naming workflow now emits stable unique row labels plus
      `local_cell_name`, `general_american_cell_name`, and `identity_stack_json`.
      The D3 ranked table uses the general American label as the primary display
      layer and shows local identity as secondary context when useful. Basis,
      match scope, and stack metadata remain in output fields and the cell tooltip
      rather than visible suffixes like `metro name` or `natural name`.

## Ongoing Rule

- [ ] When an item is completed, update the relevant manifest, provenance note, test,
      or documentation file in the same change so this checklist stays aligned with
      the repo.
- [ ] When priorities or dependencies change, update the `Recommended Execution
      Order` section in the same change so the top of this file remains the current
      execution plan.

## Human Notes Integrated

- Staged report:
      `external-data/raw/reports/nlr-pr-6a20-99256-leveraging-reveal-for-data-center-siting.pdf`
- Requirement note:
      `external-data/provenance/data-center-siting-report-requirements.md`
- LinkedIn Part I and Part II text have now been integrated into the requirement
      note and the report-derived backlog, including nationwide scoring and ranking,
      cumulative 25-year buildout, 5 km grid aggregation, scenario-controlled
      assumptions, ReEDS integration intent, and explicit limitation carry-forward
      requirements.
