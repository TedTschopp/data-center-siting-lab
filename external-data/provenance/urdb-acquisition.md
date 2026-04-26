# URDB Acquisition

- Source page: https://apps.openei.org/USURDB/
- Bulk approved-rates export: https://apps.openei.org/USURDB/download/usurdb.csv.gz
- API documentation: https://openei.org/services/doc/rest/util_rates/
- API endpoint: https://api.openei.org/utility_rates
- Repo-local staging command:
  `python -m reVeal.public_data stage-dataset urdb --repo-root .`
- Expected local stage path: `external-data/raw/urdb/usurdb.csv.gz`

## Decision

URDB is now part of the direct repo staging workflow.

The repo defaults to the bulk approved-rates CSV export as the acquisition surface.
The documented API remains available for later, more selective extraction work, but it
requires a free API key and is not the primary staging path for now.

## Current workflow

Use the staging command above to download the approved-rates export into the ignored
`external-data/raw/urdb/` directory.

This closes the old open question about whether URDB should be added to the workflow
or deferred. It is now a supported direct public source in the repo.