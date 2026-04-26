# Usage Instructions

This guide covers the repo-local public-data workflow used to reproduce the data
center opportunity case-study inputs with documented public sources and explicit
proxy layers where exact parity is not feasible.

The workflow assumes you are running from the repository root so that the tracked
relative paths below resolve correctly.

## Public-Data Workflow

### 1. Inspect the available dataset surfaces

List the dataset IDs that the public-data utility knows how to stage:

```bash
python -m reVeal.public_data list-datasets
```

This prints one row per dataset ID with its acquisition mode and its repo-local
staging path under `external-data/`.

### 2. Stage acquisition notes, representative payloads, and example bundles

The public-data workflow uses `external-data/raw/` for source files,
`external-data/unpacked/` for extracted working copies, and `external-data/examples/`
for runnable synthetic example bundles. All three directories are ignored by git.

Stage a dataset with:

```bash
python -m reVeal.public_data stage-dataset <dataset_id> --repo-root .
```

If a direct or representative download is interrupted, resume it with:

```bash
python -m reVeal.public_data stage-dataset <dataset_id> --repo-root . --resume
```

Examples:

```bash
python -m reVeal.public_data stage-dataset urdb --repo-root .
python -m reVeal.public_data stage-dataset urdb --repo-root . --resume
python -m reVeal.public_data stage-dataset ribits --repo-root .
python -m reVeal.public_data stage-dataset nwi_wetlands --repo-root . --download-representative
python -m reVeal.public_data stage-dataset nwi_wetlands --repo-root . --download-representative --resume
python -m reVeal.public_data stage-dataset county_land_value_proxy_inputs --repo-root .
python -m reVeal.public_data stage-dataset county_construction_cost_proxy_inputs --repo-root .
```

RIBITS also has a dedicated scripted webservice snapshot command:

```bash
python -m reVeal.public_data download-ribits-bank-sites \
  --output-path external-data/raw/ribits/ribits_bank_sites_snapshot.json
```

If that snapshot is interrupted, resume it with:

```bash
python -m reVeal.public_data download-ribits-bank-sites \
	--output-path external-data/raw/ribits/ribits_bank_sites_snapshot.json \
	--resume
```

Use `--checkpoint-path` if you want the resume state written somewhere other than
the default sidecar file next to the snapshot JSON.

Behavior:

- Direct datasets download to the configured raw path.
- Manual datasets create a repo-local note file that documents the expected payload
	or schema.
- Some manual datasets also support `--download-representative` for one concrete
	sample payload.
- RIBITS uses a dedicated snapshot command rather than `--download-representative`
	because the public source is exposed as list/detail webservices instead of a single
	package download.
- Direct and representative download commands now print byte progress to stderr while
	they run.
- The RIBITS snapshot command prints bank-site progress to stderr as each detail
	payload is processed.
- Stop a running download with `Ctrl+C`.
- Resume a partial direct or representative download by rerunning the same
	`stage-dataset` command with `--resume`.
- Resume a partial RIBITS snapshot by rerunning `download-ribits-bank-sites` with
	`--resume`.

For the generated public proxy workflows, stage a runnable example bundle with:

```bash
python -m reVeal.public_data stage-example-bundle public_data_center_baseline --repo-root .
python -m reVeal.public_data stage-example-bundle public_power_infrastructure_baseline --repo-root .
python -m reVeal.public_data stage-example-bundle public_fiber_proxy_baseline --repo-root .
python -m reVeal.public_data stage-example-bundle public_gas_service_territory_baseline --repo-root .
python -m reVeal.public_data stage-example-bundle public_land_value_proxy --repo-root .
python -m reVeal.public_data stage-example-bundle public_construction_cost_proxy --repo-root .
python -m reVeal.public_data stage-example-bundle public_water_availability_proxy --repo-root .
```

Each bundle writes `external-data/examples/<bundle_id>/README.md` with the exact
validated command and expected outputs for that workflow.

### 3. Build FEMA NFHL direct download URLs when needed

FEMA community packages are generated from inventory fields rather than a single
national ZIP URL.

Build one directly with:

```bash
python -m reVeal.public_data build-fema-download-url \
	--dfirm-id 01001C \
	--state Alabama \
	--county "Autauga County" \
	--file-name 01001C_20231225.zip
```

You can pass the same arguments through `stage-dataset` to stage the FEMA note and
download one representative community package through the same CLI surface:

```bash
python -m reVeal.public_data stage-dataset fema_nfhl \
	--repo-root . \
	--download-representative \
	--dfirm-id 01001C \
	--state Alabama \
	--county "Autauga County" \
	--file-name 01001C_20231225.zip
```

### 4. Assess and generate the public EER alternative load projections

The public EER workbook is not a direct drop-in replacement for the shipped fixture
CSV inputs. The repo includes an assessment command that makes that verdict explicit:

```bash
python -m reVeal.public_data assess-eer-drop-in
```

Generate the schema-compatible public alternative CSVs with:

```bash
python -m reVeal.public_data generate-eer-loads \
	--workbook external-data/unpacked/eer/ADP2024_detailed_output_data.xlsx \
	--regions tests/data/downscale/inputs/regions/eer_adp_zones.gpkg \
	--output-dir external-data/derived/eer
```

That command writes:

- `external-data/derived/eer/eer_public_central_high_data_center_national.csv`
- `external-data/derived/eer/eer_public_central_high_data_center_regional.csv`
- `external-data/derived/eer/eer_public_central_high_data_center_region_groups.csv`

Magnitude guidance for this path is explicit: validate schema compatibility,
footprint reconciliation, coherent trend behavior, and smoke-test execution. Do not
use direct magnitude matching against the shipped fixture totals as the acceptance
criterion for the public EER path.

### 5. Run the public EER smoke tests

Run the validated total smoke test with:

```bash
python external-data/derived/eer/run_downscale_smoke.py \
	external-data/derived/eer/config_public_total_smoke.json \
	--output external-data/derived/eer/downscale-smoke/public_eer_total_downscaled.gpkg
```

Run the validated grouped regional smoke test with:

```bash
python external-data/derived/eer/run_downscale_smoke.py \
	external-data/derived/eer/config_public_regional_smoke.json \
	--output external-data/derived/eer/downscale-smoke/public_eer_regional_downscaled.gpkg
```

These smoke tests confirm that the generated public EER outputs are operationally
usable by the repo's downscale workflow.

### 6. Run the checkpointed public reproduction workflow

If you want one bounded command that replays the validated public-data reproduction
path, use:

```bash
python -m reVeal.public_data run-public-reproduction \
  --status-path external-data/derived/public_reproduction_status.json
```

That workflow currently runs five steps:

- assess the public EER workbook against the tracked anchors
- regenerate the public EER projection CSVs
- run the total smoke config
- run the grouped regional smoke config
- regenerate the public NERC reserve-margin features

Behavior:

- The command prints step-level progress to stderr.
- Stop it with `Ctrl+C`.
- Resume it with `--resume` and the same `--status-path`.
- Use `--force` to discard an existing status file and start over.
- The status JSON records completed steps and per-step outputs so you can inspect
	what already ran.

### 7. Materialize the bounded public report bundle

If you want a report-facing bundle that wraps the bounded reproduction path and
records the current deviations from report parity, use:

```bash
python -m reVeal.public_data run-public-report-bundle \
  --output-dir external-data/derived/report-bundle
```

That command reruns the bounded public reproduction workflow and writes a tracked
bundle directory with:

- `external-data/derived/report-bundle/public_report_bundle_status.json`
- `external-data/derived/report-bundle/public_reproduction_status.json`
- `external-data/derived/report-bundle/public_report_feasible_land.gpkg`
- `external-data/derived/report-bundle/public_report_suitability_percentiles.gpkg`
- `external-data/derived/report-bundle/public_report_suitability_ranked_cells.csv`
- `external-data/derived/report-bundle/public_report_state_boundaries.gpkg`
- `external-data/derived/report-bundle/public_report_zoning_proxy.gpkg`
- `external-data/derived/report-bundle/public_report_permitting_proxy.gpkg`
- `external-data/derived/report-bundle/public_report_social_friction_proxy.gpkg`
- `external-data/derived/report-bundle/public_report_hosting_capacity_proxy.gpkg`
- `external-data/derived/report-bundle/public_report_suitability_map.html`
- `external-data/derived/report-bundle/public_report_assumption_registry.json`
- `external-data/derived/report-bundle/public_report_limitations.md`
- `external-data/derived/report-bundle/public_report_reeds_integration_contract.json`
- `external-data/derived/report-bundle/public_eer_total_downscaled_cumulative_buildout.gpkg`
- `external-data/derived/report-bundle/public_eer_regional_downscaled_cumulative_buildout.gpkg`
- `external-data/derived/report-bundle/public_report_bundle_cumulative_buildout_summary.csv`
- `external-data/derived/report-bundle/public_report_bundle_manifest.json`
- `external-data/derived/report-bundle/public_report_bundle_deviations.md`

Behavior:

- The command prints step-level progress to stderr.
- Stop it with `Ctrl+C`.
- Resume it with `--resume` and the same `--output-dir` or `--status-path`.
- Use `--force` to discard the existing bundle metadata and restart.
- The manifest records the current repo-root outputs, baseline-year boundary, and
  the grid-priority assumption used by the bounded public bundle.
- The feasible-land GeoPackage is a bounded approximation built from execution-grid
  cells where `developable_capacity_mw > 0`; cells whose staged NLCD water/wetland
  share is at least `0.5` are retained and flagged rather than removed.
- The suitability-percentile GeoPackage ranks the pre-existing
  `suitability_score` field across developable cells, then clamps flagged
  water/wetland cells to `0` suitability percentile.
- The ranked suitability CSV orders those feasible cells nationwide by percentile,
  score, and developable capacity so the bundle has a report-facing scored table as
  well as map layers. Cell labels now carry a bounded geographic identity stack:
  stable unique `cell_name` values for joins, `local_cell_name` for the most
  specific available place identity, `general_american_cell_name` for report-facing
  recognition, and `identity_stack_json` for the ordered identity layers.
- The D3 map HTML page embeds the bounded feasible-land and suitability surfaces in a single browser-rendered file so you can inspect the map without opening GIS software. The underlying grid remains the internal model, but the browser display draws grid-backed cells as fitted hexagons for quicker visual scanning. Water/wetland-flagged cells remain in the map footprint at `0` suitability percentile. Optional state-boundary, zoning-proxy, permitting / ordinance evidence, social-friction evidence, and hosting-capacity proxy layers provide bounded context overlays without replacing the base suitability surface.
- The assumption registry JSON records the current scenario inputs, report-reference
  assumptions, bounded bundle rules, output labels, and explicit assumption gaps so
  future report runs can be compared consistently.
- The limitations note carries forward the named LinkedIn refinement gaps such as local transmission hosting capacity, demand queue times, zoning, permitting, capacity scaling, and social acceptance so the bundle does not imply full siting fidelity. Zoning, permitting, social friction, and hosting now have bounded proxy layers, but the note keeps the limits explicit so proxy evidence is not misread as entitlement, permit readiness, social acceptance, or local interconnection feasibility.
- The ReEDS integration contract JSON defines the current handoff products,
  required columns, annual time assumptions, spatial keys, and validation checks
  for using the bounded bundle in ReEDS-facing workflows.
- The cumulative buildout GeoPackages add `baseline_total_dc_load_mw`,
  `cumulative_new_dc_load_mw`, and `cumulative_total_dc_load_mw` so the bundle can
  support cumulative buildout maps or downstream animation prep from the existing
  time-stepped smoke outputs.
- The deviation note is intentionally explicit: this is a bounded public
  approximation, not a report-equivalent reproduction.
- Version-control policy: treat these report-bundle outputs as regenerated local deliverables. Commit the source code, tests, small input manifests, provenance, and documentation that recreate them; do not commit the generated HTML, GeoPackage, JSON, CSV, Markdown, or cache payloads under the bundle output directory.

### 8. Run the checkpointed public example workflows

If you want the same stop/resume behavior for the generated public proxy commands,
use the example-workflow runner:

```bash
python -m reVeal.public_data run-public-example-workflows \
	--status-path external-data/derived/public_example_workflows_status.json
```

That command stages the tracked example bundles when needed and then runs the seven
generated public workflows behind them:

- data center baseline
- power infrastructure baseline
- fiber proxy rasters
- gas service territory baseline
- land-value proxy features
- construction-cost proxy features
- water-availability proxy features

Behavior:

- The command prints step-level progress to stderr.
- Stop it with `Ctrl+C`.
- Resume it with `--resume` and the same `--status-path`.
- Use `--force` to discard an existing status file and start over.
- Use `--force-stage` if you want to rebuild the staged example bundles before rerunning.

### 9. Summarize a saved workflow status

Use the summary command when you want a compact report from a workflow status file
without rerunning the analysis:

```bash
python -m reVeal.public_data summarize-public-workflow-status \
	--status-path external-data/derived/public_reproduction_status.json
```

That command works with both:

- `external-data/derived/public_reproduction_status.json`
- `external-data/derived/public_example_workflows_status.json`
- `external-data/derived/report-bundle/public_report_bundle_status.json`

### 10. Generate the other public proxy layers

Once the relevant raw payloads or input tables are staged locally, the repo can build
the first-pass public proxy artifacts with commands such as:

```bash
python -m reVeal.public_data generate-data-center-baseline ...
python -m reVeal.public_data generate-power-infrastructure-baseline ...
python -m reVeal.public_data generate-fiber-proxy-rasters ...
python -m reVeal.public_data generate-gas-service-territory-baseline ...
python -m reVeal.public_data generate-land-value-proxy-features ...
python -m reVeal.public_data generate-construction-cost-proxy-features ...
python -m reVeal.public_data generate-water-availability-proxy-features ...
python -m reVeal.public_data generate-nerc-reserve-margin-features ...
```

If you want a ready-to-run minimal example instead of sourcing your own inputs first,
use `stage-example-bundle` and then run the command from the generated README for the
chosen workflow.

These longer-running analysis and generation commands now emit coarse-grained
progress messages to stderr when they start and complete. Stop one with `Ctrl+C` if
you want to interrupt it. If you need checkpointed resume for the validated bounded
analysis path, use `run-public-reproduction` or `run-public-example-workflows`
rather than invoking each step manually.

The dataset-specific expectations, limitations, and output paths for those workflows
are documented under `external-data/provenance/`, `external-data/derived/`, and
`docs/source/misc/datasets.rst`. The item-18 readiness summary is tracked in
`external-data/provenance/public-dataset-execution-ready.md`.

## Core CLI

For the package CLI itself, start with:

```bash
reVeal --help
reVeal template-configs
reVeal status
```

Those commands expose the main model-facing CLI surface separately from the
public-data acquisition and transformation utilities.

## API

If you want to automate the public-data workflow from Python instead of the CLI, use
the functions in `reVeal.public_data`. The CLI commands above map directly to module
functions such as:

```python
from reVeal.public_data import (
		download_ribits_bank_site_snapshot,
		generate_eer_public_projection_csvs,
		list_public_datasets,
		run_public_example_workflows,
		run_public_reproduction_workflow,
		summarize_public_workflow_status,
		stage_public_example_bundle,
		stage_public_dataset,
)
```

Use the CLI when you want the tracked repo paths and documented command surfaces.
Use the module functions when you want to orchestrate the same workflow inside a
larger Python process.
