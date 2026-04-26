# Baxtel Acquisition

- Source page: https://baxtel.com/services/datasets
- Quote page: https://baxtel.com/quotes/new
- Contact page: https://baxtel.com/contacts/new
- Presentation anchor: Baxtel for U.S. data center sites
- Repo-local staging command:
  `python -m reVeal.public_data stage-dataset baxtel_us_data_center_sites --repo-root .`
- Expected local note path: `external-data/raw/data-centers/baxtel_SAMPLE_REQUEST.txt`
- Expected licensed payload path: `external-data/raw/data-centers/baxtel_data_center_sites.csv`

## Current vendor workflow

The live vendor page currently advertises:

- a sample CSV with schema documentation,
- one-time snapshot delivery,
- annual subscription delivery, and
- a quote-based procurement workflow rather than a self-serve public download.

## Decision

Baxtel remains a commercial dependency and is still outside the public-source
reproduction path.

However, it is no longer an undefined blocker. The repo now treats Baxtel as a
defined manual procurement dependency for licensed users.

## Current repo workflow

1. Run the stage command to create the repo-local procurement note.
2. Request either a sample CSV with schema documentation or a licensed snapshot from
   Baxtel.
3. If a file is received, store it as
   `external-data/raw/data-centers/baxtel_data_center_sites.csv`.
4. Keep the delivered payload out of git and treat it as license-bound source data.
5. Use the sample schema or licensed export to compare field coverage against the
   public baseline and update repo-local documentation if the licensed path is used.

## Posture

- Exact parity remains blocked until access is actually obtained.
- The repo now captures a repeatable human workflow for commercial procurement.
- The public OSM/Wikidata/manual baseline remains the default open workflow.