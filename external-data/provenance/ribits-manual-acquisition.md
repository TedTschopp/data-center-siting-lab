# RIBITS Acquisition

- Source page: https://ribits.ops.usace.army.mil/
- Webservice docs: https://ribits.ops.usace.army.mil/ords/f?p=107:353::::::
- List endpoint: https://ribits.ops.usace.army.mil/ords/RI/public/bank_site_list/
- Detail endpoint base: https://ribits.ops.usace.army.mil/ords/RI/public/bank_site_data/
- EPA ESRI mirror: https://geopub.epa.gov/arcgis/rest/services/NEPAssist/RIBITS/MapServer
- Presentation anchor: RIBITS mitigation banks and in-lieu fee program lands in the
  exclusion-layer workflow.
- Repo-local staging command:
  `python -m reVeal.public_data stage-dataset ribits --repo-root .`
- Snapshot command:
  `python -m reVeal.public_data download-ribits-bank-sites --output-path external-data/raw/ribits/ribits_bank_sites_snapshot.json`
- Expected local workflow note path: `external-data/raw/ribits/MANUAL_DOWNLOAD.txt`
- Expected automated snapshot path: `external-data/raw/ribits/ribits_bank_sites_snapshot.json`

## Decision

RIBITS is no longer treated as a manual-only acquisition workflow.

The live site now documents stable ORDS public webservices for list and detail access,
and those endpoints return machine-readable JSON without requiring an authenticated
browser session.

## Current workflow

1. Run the stage command to create the repo-local workflow note.
2. Run the snapshot command to capture a repo-local JSON snapshot through the public
   `bank_site_list` and `bank_site_data` webservices.
3. Optionally pass `--filters-json` and `--limit` to create smaller representative
   pulls while validating filters or downstream transforms.
4. Use the resulting JSON snapshot as the staged raw source for later geometry or
   exclusion-layer transformation work.

Example representative pull:

`python -m reVeal.public_data download-ribits-bank-sites --output-path external-data/raw/ribits/ribits_bank_sites_sample.json --limit 1`

## Verified posture

- The public webservice documentation page explicitly advertises programmatic access.
- The documented `bank_site_list` and `bank_site_data` endpoints are reachable over
  HTTPS and return JSON payloads under the `ITEMS` key.
- The repo now captures a scripted snapshot workflow rather than a manual-only portal
  decision.