# Public Fiber Proxy Workflow

- Generator command:
  `python -m reVeal.public_data generate-fiber-proxy-rasters`
- Expected raw input paths:
  - `external-data/raw/fiber/osm_fiber_lines.json`
  - `external-data/raw/fiber/fcc_bdc_fiber_availability.gpkg`
- Required alignment input:
  - a template raster whose CRS, transform, width, and height define the proxy grid
- Expected derived outputs:
  - `external-data/derived/fiber/public_fiber_route_proxy.gpkg`
  - `external-data/derived/fiber/fiber_lines_onshore_proximity.tif`
  - `external-data/derived/fiber/fiber_availability_binary.tif`

## Intended scope

This workflow produces a first-pass public approximation of two distinct ideas that
the presentation treats more cleanly than public sources allow:

- route-like proximity to onshore fiber
- binary coverage for public fiber availability

It is not an exact replacement for a curated national fiber centerline dataset.

## Current acquisition posture

The transform is implemented in code, but acquisition is currently handled as manual
payload export rather than live downloads inside the repo workflow.

The repo can now stage local note files for the two input surfaces with:

- `python -m reVeal.public_data stage-dataset fiber_lines_osm_export --repo-root .`
- `python -m reVeal.public_data stage-dataset fcc_bdc_fiber_availability_export --repo-root .`

That decision is deliberate:

- OSM query-service behavior can vary, and the repo should not depend on brittle live
  calls for repeatable tests.
- FCC availability polygons are not the same thing as route geometry, so the workflow
  keeps those two proxy surfaces separate instead of pretending they are equivalent.

## Proxy method

1. Export route-like OSM telecom or fiber linework into JSON.
2. Export a locally filtered FCC Broadband Data Collection fiber-availability polygon
   layer into a vector file such as GeoPackage.
3. Supply a template raster that defines the target grid.
4. Run the generator command to normalize the linework, write the route-proxy vector,
   rasterize the FCC coverage polygons, and compute a line-proximity raster aligned to
   the same grid.

## OSM route filter

The OSM route-proxy layer keeps line geometries when their tags suggest route-like
telecom infrastructure, including cases such as:

- `man_made=communications_line`
- `telecom=line`
- `communication=line`
- `cable=fibre_optic`
- any key or value containing `fiber` or `fibre`

This filter is intentionally broad because the goal is a reproducible route proxy,
not a claim of exact fiber-centerline completeness.

## Non-equivalence versus exact route geometry

This workflow should be treated as a weaker public approximation.

Known limitations:

- OSM telecom linework is incomplete and inconsistent by region.
- FCC Broadband Data Collection polygons represent service availability, not literal
  fiber centerlines.
- The availability raster and the route-proximity raster answer different questions and
  should not be conflated.
- Output distance units follow the template raster CRS; projected templates are the
  correct choice when metric interpretation matters.