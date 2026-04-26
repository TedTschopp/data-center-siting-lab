# Public Dataset Execution-Ready Workflows

This note records the execution-ready commands that close TODO item 18.

## External Acquisition Surfaces

- `nwi_wetlands`: use `python -m reVeal.public_data stage-dataset nwi_wetlands --repo-root . --download-representative`
- `nlcd`: use `python -m reVeal.public_data stage-dataset nlcd --repo-root . --download-representative`; the command still tries the representative ScienceBase ZIP first, but if that upstream delivery fails it now falls back to tiled MRLC WMS requests and writes a bounded TIFF under `external-data/raw/nlcd/`
- `pad_us_gap`: use `python -m reVeal.public_data stage-dataset pad_us_gap --repo-root . --download-representative`
- `fema_nfhl`: use `python -m reVeal.public_data stage-dataset fema_nfhl --repo-root . --download-representative --dfirm-id 01001C --state Alabama --county "Autauga County" --file-name 01001C_20231225.zip`
- `urdb`: use `python -m reVeal.public_data stage-dataset urdb --repo-root .`

Those commands are the current acquisition examples for the remaining public-source download surfaces. For NLCD specifically, the ScienceBase ZIP is still the preferred representative package when it behaves, but the command no longer depends on that path alone for the bounded report-bundle workflow because it can fall back to a staged TIFF built from MRLC WMS tiles.

## Generated Workflow Example Bundles

The generated public workflows now support `python -m reVeal.public_data stage-example-bundle <bundle_id> --repo-root .`.

Each staged bundle writes `external-data/examples/<bundle_id>/README.md` with the exact validated generation command and the expected outputs.

- `public_data_center_baseline`
- `public_power_infrastructure_baseline`
- `public_fiber_proxy_baseline`
- `public_gas_service_territory_baseline`
- `public_land_value_proxy`
- `public_construction_cost_proxy`
- `public_water_availability_proxy`

Representative examples are intentionally synthetic and minimal. They exist to prove the command surface, input schema, and output contract end to end without claiming that the example bundle is a production-quality national dataset.
