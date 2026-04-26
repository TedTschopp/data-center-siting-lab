# Public Data Center Baseline

Generate the first-pass public baseline with:

Before running the generator, the repo can stage the expected input-note files with:

```bash
python -m reVeal.public_data stage-dataset data_center_osm_export --repo-root .
python -m reVeal.public_data stage-dataset data_center_wikidata_export --repo-root .
python -m reVeal.public_data stage-dataset data_center_manual_augmentation --repo-root .
```

Generate the first-pass public baseline with:

```bash
python -m reVeal.public_data generate-data-center-baseline \
  --osm-payload external-data/raw/data-centers/osm_data_centers.json \
  --wikidata-payload external-data/raw/data-centers/wikidata_data_centers.json \
  --manual-csv external-data/raw/data-centers/manual_data_centers.csv \
  --output-dir external-data/derived/data-centers
```

The command writes:

- `public_data_center_baseline.csv`
- `public_data_center_baseline.gpkg`

Input expectations:

- The OSM payload is an exported Overpass JSON file containing data center features.
- The Wikidata payload is an exported SPARQL JSON result containing point geometry.
- The manual CSV is optional and can add operator-announcement or permitting rows.

The output is a deduped point-layer baseline with provenance fields such as:

- `baseline_id`
- `name`
- `operator`
- `site_status`
- `sources`
- `source_count`
- `source_ids`
- `wikidata_id`
- `source_url`
- `source_note`

This is a public approximation and is explicitly non-equivalent to Baxtel coverage.