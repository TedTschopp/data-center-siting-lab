# Public Geospatial Staging

The following public geospatial layers now have a reproducible repo-local acquisition
workflow through `python -m reVeal.public_data stage-dataset ...`:

- `nwi_wetlands`
- `nlcd`
- `pad_us_gap`
- `fema_nfhl`

## Local staging paths

- `external-data/raw/nwi/MANUAL_DOWNLOAD.txt`
- `external-data/raw/nlcd/MANUAL_DOWNLOAD.txt`
- `external-data/raw/pad-us/MANUAL_DOWNLOAD.txt`
- `external-data/raw/fema/MANUAL_DOWNLOAD.txt`

Representative downloads are written alongside those note files in the same dataset
subdirectories.

Current NLCD caveat:

- The staged NLCD representative URL remains useful as a documented source pointer, but
  live representative download behavior has been unstable in practice.
- The ScienceBase file route has returned a truncated ZIP during live staging, and a
  direct manager-style fallback returned HTML rather than a raster package.
- The repo now handles that instability by falling back to tiled MRLC WMS requests and
  writing a bounded TIFF for the current report-grid footprint at
  `external-data/raw/nlcd/Annual_NLCD_LndCov_2023_CU_C1V0.tif` when the ZIP request fails.
- That fallback closes the old manual-only raster staging step for the bounded report
  bundle, but it does not turn the bounded TIFF into a full national replacement for
  the official packaged NLCD distribution.

## Representative download workflow

The repo now supports a `--download-representative` flag that keeps the staged note
file and also downloads one reproducible representative payload into `external-data/raw`.

Representative commands:

- `nwi_wetlands`
  - `python -m reVeal.public_data stage-dataset nwi_wetlands --repo-root . --download-representative`
  - Expected representative path: `external-data/raw/nwi/AL_geodatabase_wetlands.zip`
- `nlcd`
  - `python -m reVeal.public_data stage-dataset nlcd --repo-root . --download-representative`
  - Preferred representative path when ScienceBase behaves: `external-data/raw/nlcd/Annual_NLCD_LndCov_2023_CU_C1V0.zip`
  - Automatic fallback path when ScienceBase fails: `external-data/raw/nlcd/Annual_NLCD_LndCov_2023_CU_C1V0.tif`
  - Current status: the command first tries the representative ZIP and now falls back to
    a bounded MRLC WMS-derived TIFF automatically for the report-grid footprint
- `pad_us_gap`
  - `python -m reVeal.public_data stage-dataset pad_us_gap --repo-root . --download-representative`
  - Expected representative path: `external-data/raw/pad-us/PADUS4_1Geodatabase.zip`
- `fema_nfhl`
  - `python -m reVeal.public_data stage-dataset fema_nfhl --repo-root . --download-representative --dfirm-id 01001C --state Alabama --county "Autauga County" --file-name 01001C_20231225.zip`
  - Expected representative path: `external-data/raw/fema/01001C_20231225.zip`

This closes the old "staging-prepared only" state for NWI, PAD-US, FEMA NFHL, and the
NLCD note-staging workflow. The repo can now stage the explanatory note for all four
datasets and fetch representative packages through the same command surface where the
upstream source currently behaves reliably, with NLCD additionally able to fall back to
an automatically staged bounded TIFF when the representative ZIP path is unstable.

## Why manual for now

These sources are public, but their authoritative acquisition flows still depend on
landing pages, map tools, or portal-driven selection for bulk national or selectively
scoped extracts.

The representative-download workflow does not change that bulk-download reality.
What it does provide is a repeatable repo-local way to fetch one concrete payload for
inspection, testing, and workflow validation while preserving the note that explains
the broader acquisition context.

## Confirmed direct binary download paths

The following direct package paths have been confirmed and promoted into staged local
notes where the URL resolves directly to a ZIP payload:

- `nwi_wetlands`
  - Example direct state geodatabase ZIP from the official FWS state-download pattern: `https://documentst.ecosphere.fws.gov/wetlands/data/State-Downloads/AL_geodatabase_wetlands.zip`
- `nlcd`
  - ScienceBase 2023 CONUS land-cover ZIP pointer: `https://www.sciencebase.gov/catalog/file/get/664e0d2bd34e702fe8744536?name=Annual_NLCD_LndCov_2023_CU_C1V0.zip`
  - Current status: the pointer is still the documented package path, but live delivery has
    not been reliable enough to treat the representative ZIP as operationally validated
- `pad_us_gap`
  - ScienceBase PAD-US 4.1 national geodatabase ZIP: `https://www.sciencebase.gov/catalog/file/get/652d4fc5d34e44db0e2ee45e?name=PADUS4_1Geodatabase.zip`
- `fema_nfhl`
  - Community ZIP URL pattern generated from NFHL inventory fields with `python -m reVeal.public_data build-fema-download-url --dfirm-id ... --state ... --county ... --file-name ...`

For FEMA, the direct binary path is not a single national file. The status table
exposes many community-specific ZIP URLs through the same download servlet pattern.
The repo now includes a helper that builds the correct URL from those inventory
fields instead of carrying one hard-coded example county URL.

For NWI, the mapper code confirms both state geodatabase and state geopackage ZIP
patterns under the official FWS state-download directory. The promoted URL above is a
verified example using the mapper's postal-code state key format.

## Confirmed direct endpoints

The following direct endpoints have been confirmed and promoted into the staged local
notes written by `python -m reVeal.public_data stage-dataset ...`:

- `nwi_wetlands`
  - REST: `https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/rest`
  - WMS capabilities: `https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/services/Wetlands/MapServer/WMSServer?request=GetCapabilities&service=WMS`
- `nlcd`
  - WMS capabilities: `https://dmsdata.cr.usgs.gov/geoserver/mrlc_Land-Cover-Native_conus_year_data/wms?service=WMS&request=GetCapabilities`
  - WCS capabilities: `https://dmsdata.cr.usgs.gov/geoserver/mrlc_Land-Cover-Native_conus_year_data/wcs?service=WCS&request=GetCapabilities`
- `pad_us_gap`
  - Protection Status by GAP Status Code FeatureServer: `https://services.arcgis.com/v01gqwM5QqNysAAi/arcgis/rest/services/PADUS_Protection_Status_by_GAP_Status_Code/FeatureServer`
  - Public Access FeatureServer: `https://services.arcgis.com/v01gqwM5QqNysAAi/arcgis/rest/services/PADUS_Public_Access/FeatureServer`
- `fema_nfhl`
  - ArcGIS REST: `https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer`
  - WMS capabilities: `https://hazards.fema.gov/arcgis/services/public/NFHLWMS/MapServer/WMSServer?request=GetCapabilities&service=WMS`
  - WFS capabilities: `https://hazards.fema.gov/arcgis/services/public/NFHL/MapServer/WFSServer?service=WFS&request=GetCapabilities`

These service URLs support live access and integration workflows. They do not change
the recommendation that bulk downloads may still need selective manual handling when
local raster, vector, or packaged extract files are needed at larger scope.

## Source pages

- NWI: <https://www.fws.gov/program/national-wetlands-inventory/wetlands-mapper>
- NLCD: <https://www.usgs.gov/annualnlcd>
- PAD-US: <https://www.usgs.gov/programs/gap-analysis-project/science/pad-us-data-download>
- FEMA NFHL: <https://msc.fema.gov/portal/advanceSearch>
