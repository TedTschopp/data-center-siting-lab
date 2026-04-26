# external-data

Repo-local staging area for sourced datasets and provenance.

## Tracked

- `manifest/` holds the dataset inventory, unresolved gap register, and open substitute matrix.
- `provenance/` holds human-readable notes on where a source artifact came from and what was verified.
- `provenance/report-reproduction-gaps.md` collapses the remaining exact-vs-proxy reproduction blockers into a single execution view.
- `provenance/ribits-manual-acquisition.md` records the current manual-only decision for RIBITS portal acquisition.
- `provenance/urdb-acquisition.md` records the direct staging decision for URDB.
- `provenance/public-geospatial-staging.md` now records the representative acquisition workflow for the staged public geospatial datasets.
- `derived/` holds reproducible small outputs generated from staged public-source artifacts.

## Ignored

- `raw/` is for downloaded source archives and files.
- `unpacked/` is for extracted working copies.

The ignored directories are intended to support local research and transformation work
without committing large binaries into git.