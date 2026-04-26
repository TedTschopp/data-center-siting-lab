# Bounded Public Report Bundle Outputs

This directory is the local output target for:

```bash
python -m reVeal.public_data run-public-report-bundle \
  --output-dir external-data/derived/report-bundle
```

The generated bundle artifacts in this directory are intentionally not tracked in Git.
They are report deliverables, but they are regenerated deliverables.

Current decision: keep the generated HTML, GeoPackages, CSVs, JSON status files, and
Census cache out of source control. If a reviewed snapshot must be shared, publish or
package that snapshot as an explicit release artifact instead of relaxing the ignore
rules for this directory.

Track the durable inputs and recipes instead:

- source code and regression tests
- schema-only public evidence manifests under `external-data/manifest/`
- provenance notes under `external-data/provenance/`
- user-facing usage and dataset documentation

Regenerate the local bundle whenever you need the HTML map, GeoPackages, manifest,
status JSON, deviation note, ranked CSV, cumulative buildout surfaces, or cached
state-boundary source ZIP. The default run also writes a generated
`public_report_census_geography_cache.json` file for Census coordinate GeoLookup
identity enrichment; pass `--no-census-geolookup` to skip that online enrichment.
