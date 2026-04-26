# Bounded Public Report Bundle Outputs

This directory is the local output target for:

```bash
python -m reVeal.public_data run-public-report-bundle \
  --output-dir external-data/derived/report-bundle
```

The generated bundle artifacts in this directory are intentionally not tracked in Git.
They are report deliverables, but they are regenerated deliverables.

Track the durable inputs and recipes instead:

- source code and regression tests
- schema-only public evidence manifests under `external-data/manifest/`
- provenance notes under `external-data/provenance/`
- user-facing usage and dataset documentation

Regenerate the local bundle whenever you need the HTML map, GeoPackages, manifest,
status JSON, deviation note, ranked CSV, cumulative buildout surfaces, or cached
state-boundary source ZIP.
