# Public Power Infrastructure Baseline

Before running the generator, the repo can stage the expected input-note files with:

```bash
python -m reVeal.public_data stage-dataset transmission_lines_osm_export --repo-root .
python -m reVeal.public_data stage-dataset substations_osm_export --repo-root .
```

Generate the first-pass public power baseline with:

```bash
python -m reVeal.public_data generate-power-infrastructure-baseline \
  --line-payload external-data/raw/power/osm_transmission_lines.json \
  --substation-payload external-data/raw/power/osm_substations.json \
  --output-dir external-data/derived/power
```

The command writes:

- `public_transmission_lines_135kv.gpkg`
- `public_substations.gpkg`

Input expectations:

- The line payload is an exported Overpass JSON file containing OSM power linework.
- The substation payload is an exported Overpass JSON file containing OSM substation
  features.

Filtering summary:

- Only OSM `power=line`, `power=minor_line`, and `power=cable` features with parsed
  `max_voltage_kv >= 135` are kept in the transmission-line layer.
- The substation layer preserves the OSM `substation` tag where available and any
  parsed maximum voltage value.

This is a public approximation and is explicitly non-equivalent to a curated
transmission planning model.