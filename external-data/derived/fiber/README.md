# Public Fiber Proxy Workflow

Before running the generator, the repo can stage the expected input-note files with:

```bash
python -m reVeal.public_data stage-dataset fiber_lines_osm_export --repo-root .
python -m reVeal.public_data stage-dataset fcc_bdc_fiber_availability_export --repo-root .
```

Generate the first-pass public fiber proxy outputs with:

```bash
python -m reVeal.public_data generate-fiber-proxy-rasters \
  --osm-payload external-data/raw/fiber/osm_fiber_lines.json \
  --fcc-availability external-data/raw/fiber/fcc_bdc_fiber_availability.gpkg \
  --template-raster path/to/template.tif \
  --output-dir external-data/derived/fiber
```

The command writes:

- `public_fiber_route_proxy.gpkg`
- `fiber_lines_onshore_proximity.tif`
- `fiber_availability_binary.tif`

Input expectations:

- The OSM payload is an exported Overpass JSON file containing route-like telecom or
  fiber linework.
- The FCC vector is a locally filtered availability polygon export.
- The template raster defines the output grid alignment and distance units.

This workflow is a public approximation and is explicitly non-equivalent to exact
national fiber-route geometry.