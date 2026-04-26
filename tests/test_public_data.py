# -*- coding: utf-8 -*-
"""
public data utilities tests
"""
import io
import json
from pathlib import Path
import urllib.error
import zipfile

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
import rasterio
from rasterio.io import MemoryFile
from rasterio.transform import from_origin
from shapely.geometry import box

from reVeal.public_data import (
    MMBTU_PER_YEAR_TO_AVERAGE_MW,
    PUBLIC_DATASET_CATALOG,
    _annotate_public_report_cell_names,
    _build_public_report_feasible_land_frame,
    assess_public_eer_drop_in_compatibility,
    build_state_gas_service_territory_frame,
    build_state_water_availability_proxy_tables,
    build_county_construction_cost_proxy_frame,
    build_county_land_value_proxy_frame,
    build_osm_data_center_frame,
    build_osm_fiber_line_frame,
    build_osm_substation_frame,
    build_osm_transmission_line_frame,
    build_public_data_center_baseline,
    build_wikidata_data_center_frame,
    build_nerc_emm_zone_feature_frame,
    build_nerc_reserve_margin_table,
    build_fema_nfhl_download_url,
    build_eer_public_projection_frames,
    build_state_zone_weights,
    generate_public_data_center_baseline,
    generate_public_construction_cost_proxy_features,
    generate_public_fiber_proxy_rasters,
    generate_public_gas_service_territory_baseline,
    generate_public_land_value_proxy_features,
    generate_public_power_infrastructure_baseline,
    generate_public_water_availability_proxy_features,
    generate_nerc_reserve_margin_features,
    download_ribits_bank_site_snapshot,
    main,
    read_xlsx_sheet_records,
    run_public_example_workflows,
    run_public_report_bundle,
    run_public_reproduction_workflow,
    stage_public_example_bundle,
    stage_public_dataset,
)


EXAMPLE_BUNDLE_CASES = {
    "public_data_center_baseline": {
        "expected_inputs": [
            "osm_data_centers.json",
            "wikidata_data_centers.json",
            "manual_data_centers.csv",
            "README.md",
        ],
        "command_text": "generate-data-center-baseline",
        "build_args": lambda bundle_dir, output_dir: [
            "generate-data-center-baseline",
            "--osm-payload",
            (bundle_dir / "osm_data_centers.json").as_posix(),
            "--wikidata-payload",
            (bundle_dir / "wikidata_data_centers.json").as_posix(),
            "--manual-csv",
            (bundle_dir / "manual_data_centers.csv").as_posix(),
            "--output-dir",
            output_dir.as_posix(),
        ],
        "expected_outputs": [
            "public_data_center_baseline.csv",
            "public_data_center_baseline.gpkg",
        ],
    },
    "public_power_infrastructure_baseline": {
        "expected_inputs": [
            "osm_transmission_lines.json",
            "osm_substations.json",
            "README.md",
        ],
        "command_text": "generate-power-infrastructure-baseline",
        "build_args": lambda bundle_dir, output_dir: [
            "generate-power-infrastructure-baseline",
            "--line-payload",
            (bundle_dir / "osm_transmission_lines.json").as_posix(),
            "--substation-payload",
            (bundle_dir / "osm_substations.json").as_posix(),
            "--output-dir",
            output_dir.as_posix(),
        ],
        "expected_outputs": [
            "public_transmission_lines_135kv.gpkg",
            "public_substations.gpkg",
        ],
    },
    "public_fiber_proxy_baseline": {
        "expected_inputs": [
            "osm_fiber_lines.json",
            "fcc_bdc_fiber_availability.gpkg",
            "template.tif",
            "README.md",
        ],
        "command_text": "generate-fiber-proxy-rasters",
        "build_args": lambda bundle_dir, output_dir: [
            "generate-fiber-proxy-rasters",
            "--osm-payload",
            (bundle_dir / "osm_fiber_lines.json").as_posix(),
            "--fcc-availability",
            (bundle_dir / "fcc_bdc_fiber_availability.gpkg").as_posix(),
            "--template-raster",
            (bundle_dir / "template.tif").as_posix(),
            "--output-dir",
            output_dir.as_posix(),
        ],
        "expected_outputs": [
            "public_fiber_route_proxy.gpkg",
            "fiber_lines_onshore_proximity.tif",
            "fiber_availability_binary.tif",
        ],
    },
    "public_gas_service_territory_baseline": {
        "expected_inputs": [
            "state_gas_service_territories.csv",
            "texas_gas.gpkg",
            "README.md",
        ],
        "command_text": "generate-gas-service-territory-baseline",
        "build_args": lambda bundle_dir, output_dir: [
            "generate-gas-service-territory-baseline",
            "--manifest-csv",
            (bundle_dir / "state_gas_service_territories.csv").as_posix(),
            "--output-dir",
            output_dir.as_posix(),
        ],
        "expected_outputs": [
            "public_gas_service_territories.gpkg",
            "public_gas_service_territories_state_index.csv",
        ],
    },
    "public_land_value_proxy": {
        "expected_inputs": [
            "county_land_value_proxy.csv",
            "county_land_value_counties.gpkg",
            "zones.gpkg",
            "README.md",
        ],
        "command_text": "generate-land-value-proxy-features",
        "build_args": lambda bundle_dir, output_dir: [
            "generate-land-value-proxy-features",
            "--county-proxy-csv",
            (bundle_dir / "county_land_value_proxy.csv").as_posix(),
            "--county-polygons",
            (bundle_dir / "county_land_value_counties.gpkg").as_posix(),
            "--regions",
            (bundle_dir / "zones.gpkg").as_posix(),
            "--output-dir",
            output_dir.as_posix(),
        ],
        "expected_outputs": [
            "public_land_value_county.gpkg",
            "public_land_value_emm_zone.gpkg",
        ],
    },
    "public_construction_cost_proxy": {
        "expected_inputs": [
            "county_construction_cost_proxy.csv",
            "county_construction_cost_counties.gpkg",
            "zones.gpkg",
            "README.md",
        ],
        "command_text": "generate-construction-cost-proxy-features",
        "build_args": lambda bundle_dir, output_dir: [
            "generate-construction-cost-proxy-features",
            "--county-proxy-csv",
            (bundle_dir / "county_construction_cost_proxy.csv").as_posix(),
            "--county-polygons",
            (bundle_dir / "county_construction_cost_counties.gpkg").as_posix(),
            "--regions",
            (bundle_dir / "zones.gpkg").as_posix(),
            "--output-dir",
            output_dir.as_posix(),
        ],
        "expected_outputs": [
            "public_construction_cost_county.gpkg",
            "public_construction_cost_emm_zone.gpkg",
        ],
    },
    "public_water_availability_proxy": {
        "expected_inputs": [
            "usgs_state_water_use_proxy.csv",
            "state_zone_mapping.xlsx",
            "zones.gpkg",
            "README.md",
        ],
        "command_text": "generate-water-availability-proxy-features",
        "build_args": lambda bundle_dir, output_dir: [
            "generate-water-availability-proxy-features",
            "--state-proxy-csv",
            (bundle_dir / "usgs_state_water_use_proxy.csv").as_posix(),
            "--mapping-workbook",
            (bundle_dir / "state_zone_mapping.xlsx").as_posix(),
            "--regions",
            (bundle_dir / "zones.gpkg").as_posix(),
            "--output-dir",
            output_dir.as_posix(),
        ],
        "expected_outputs": [
            "public_water_availability_state_proxy.csv",
            "public_water_availability_emm_zone.gpkg",
        ],
    },
}


class FakeDownloadResponse(io.BytesIO):
    """Minimal HTTP response stub for streamed download tests."""

    def __init__(self, payload, headers=None, status=200):
        super().__init__(payload)
        self.headers = headers or {}
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


def _write_minimal_xlsx(xlsx_path):
    """Write a minimal XLSX file for parser tests."""

    shared_strings = [
        "county",
        "zone",
        "sqmi",
        "households 2010 (complete count)",
        "Cover",
        "alpha county, alpha",
        "north_emm",
        "75",
        "100",
    ]
    shared_xml = [
        (
            '<si><t xml:space="preserve">'
            f"{value}"
            "</t></si>"
        )
        for value in shared_strings
    ]

    workbook_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
              xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
      <sheets>
        <sheet name="Mapping zone to county" sheetId="1" r:id="rId1"/>
      </sheets>
    </workbook>
    """

    rels_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
      <Relationship Id="rId1"
        Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
        Target="worksheets/sheet1.xml"/>
    </Relationships>
    """

    sheet_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
      <sheetData>
        <row r="1">
          <c r="A1" t="s"><v>0</v></c>
          <c r="B1" t="s"><v>1</v></c>
          <c r="C1" t="s"><v>2</v></c>
          <c r="D1" t="s"><v>3</v></c>
          <c r="E1" t="s"><v>4</v></c>
        </row>
        <row r="2">
          <c r="A2" t="s"><v>5</v></c>
          <c r="B2" t="s"><v>6</v></c>
          <c r="C2" t="s"><v>7</v></c>
          <c r="D2" t="s"><v>8</v></c>
        </row>
      </sheetData>
    </worksheet>
    """

    with zipfile.ZipFile(xlsx_path, "w") as zf:
        zf.writestr("xl/workbook.xml", workbook_xml)
        zf.writestr("xl/_rels/workbook.xml.rels", rels_xml)
        zf.writestr(
            "xl/sharedStrings.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
            <sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
                 count="9" uniqueCount="9">
            """
            + "".join(shared_xml)
            + "</sst>",
        )
        zf.writestr("xl/worksheets/sheet1.xml", sheet_xml)


def test_read_xlsx_sheet_records_pads_missing_trailing_cells(tmp_path):
    """Parser should preserve rows even when trailing empty cells are omitted."""

    xlsx_path = tmp_path / "minimal.xlsx"
    _write_minimal_xlsx(xlsx_path)

    records = read_xlsx_sheet_records(
        xlsx_path, "Mapping zone to county", header_marker="county"
    )

    assert records == [
        {
            "county": "alpha county, alpha",
            "zone": "north_emm",
            "sqmi": "75",
            "households 2010 (complete count)": "100",
            "Cover": "",
        }
    ]


def test_build_eer_public_projection_frames_apportions_state_totals_to_groups():
    """Public EER rows should convert into internally consistent total and group CSVs."""

    mapping_rows = [
        {
            "county": "alpha county, alpha",
            "zone": "north_emm",
            "sqmi": "75",
            "households 2010 (complete count)": "100",
            "Cover": "",
        },
        {
            "county": "beta county, alpha",
            "zone": "south_emm",
            "sqmi": "25",
            "households 2010 (complete count)": "50",
            "Cover": "",
        },
        {
            "county": "gamma county, beta",
            "zone": "south_emm",
            "sqmi": "50",
            "households 2010 (complete count)": "80",
            "Cover": "",
        },
    ]
    zone_groups_df = pd.DataFrame(
        {
            "emm_zone": ["North", "South"],
            "zone_group": ["East", "West"],
        }
    )
    final_energy_rows = [
        {
            "Sector": "commercial",
            "Subsector": "data center cooling",
            "Final Energy": "electricity",
            "Unit": "mmBtu",
            "State": "alpha",
            "Year": "2024",
            "CENTRAL HIGH DATA CENTER": "100",
        },
        {
            "Sector": "commercial",
            "Subsector": "data center it",
            "Final Energy": "electricity",
            "Unit": "mmBtu",
            "State": "alpha",
            "Year": "2024",
            "CENTRAL HIGH DATA CENTER": "300",
        },
        {
            "Sector": "commercial",
            "Subsector": "data center cooling",
            "Final Energy": "electricity",
            "Unit": "mmBtu",
            "State": "beta",
            "Year": "2024",
            "CENTRAL HIGH DATA CENTER": "200",
        },
        {
            "Sector": "commercial",
            "Subsector": "data center it",
            "Final Energy": "electricity",
            "Unit": "mmBtu",
            "State": "beta",
            "Year": "2024",
            "CENTRAL HIGH DATA CENTER": "400",
        },
    ]

    state_zone_weights = build_state_zone_weights(mapping_rows, zone_groups_df)
    total_df, regional_df, grouped_df = build_eer_public_projection_frames(
        final_energy_rows,
        state_zone_weights,
        years=[2024],
    )

    expected_total = 1000 * MMBTU_PER_YEAR_TO_AVERAGE_MW
    expected_east = 300 * MMBTU_PER_YEAR_TO_AVERAGE_MW
    expected_west = 700 * MMBTU_PER_YEAR_TO_AVERAGE_MW

    assert total_df.to_dict("records") == [
        {"year": 2024, "dc_load_mw": pytest.approx(expected_total)}
    ]
    assert regional_df.to_dict("records") == [
        {"year": 2024, "zone": "north", "dc_load_mw": pytest.approx(expected_east)},
        {"year": 2024, "zone": "south", "dc_load_mw": pytest.approx(expected_west)},
    ]
    assert grouped_df.to_dict("records") == [
        {"year": 2024, "zone_group": "east", "dc_load_mw": pytest.approx(expected_east)},
        {"year": 2024, "zone_group": "west", "dc_load_mw": pytest.approx(expected_west)},
    ]


def test_build_eer_public_projection_frames_limits_total_to_mapped_states():
    """National totals should reconcile with grouped totals on the mapped footprint."""

    mapping_rows = [
        {
            "county": "alpha county, alpha",
            "zone": "north_emm",
            "sqmi": "100",
            "households 2010 (complete count)": "100",
            "Cover": "",
        }
    ]
    zone_groups_df = pd.DataFrame(
        {
            "emm_zone": ["North"],
            "zone_group": ["East"],
        }
    )
    final_energy_rows = [
        {
            "Sector": "commercial",
            "Subsector": "data center it",
            "Final Energy": "electricity",
            "Unit": "mmBtu",
            "State": "alpha",
            "Year": "2024",
            "CENTRAL HIGH DATA CENTER": "100",
        },
        {
            "Sector": "commercial",
            "Subsector": "data center it",
            "Final Energy": "electricity",
            "Unit": "mmBtu",
            "State": "gamma",
            "Year": "2024",
            "CENTRAL HIGH DATA CENTER": "50",
        },
    ]

    state_zone_weights = build_state_zone_weights(mapping_rows, zone_groups_df)
    total_df, regional_df, grouped_df = build_eer_public_projection_frames(
        final_energy_rows,
        state_zone_weights,
        years=[2024],
    )

    expected_total = 100 * MMBTU_PER_YEAR_TO_AVERAGE_MW

    assert total_df.to_dict("records") == [
        {"year": 2024, "dc_load_mw": pytest.approx(expected_total)}
    ]
    assert regional_df.to_dict("records") == [
        {"year": 2024, "zone": "north", "dc_load_mw": pytest.approx(expected_total)}
    ]
    assert grouped_df.to_dict("records") == [
        {"year": 2024, "zone_group": "east", "dc_load_mw": pytest.approx(expected_total)}
    ]


@pytest.mark.parametrize(
    ("dataset_id", "expected_download_url", "expected_urls"),
    [
        (
            "nwi_wetlands",
            "https://documentst.ecosphere.fws.gov/wetlands/data/State-Downloads/AL_geodatabase_wetlands.zip",
            (
                "https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/rest",
                "https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/services/Wetlands/MapServer/WMSServer?request=GetCapabilities&service=WMS",
            ),
        ),
        (
            "nlcd",
            "https://www.sciencebase.gov/catalog/file/get/664e0d2bd34e702fe8744536?name=Annual_NLCD_LndCov_2023_CU_C1V0.zip",
            (
                "https://dmsdata.cr.usgs.gov/geoserver/mrlc_Land-Cover-Native_conus_year_data/wms?service=WMS&request=GetCapabilities",
                "https://dmsdata.cr.usgs.gov/geoserver/mrlc_Land-Cover-Native_conus_year_data/wcs?service=WCS&request=GetCapabilities",
            ),
        ),
        (
            "pad_us_gap",
            "https://www.sciencebase.gov/catalog/file/get/652d4fc5d34e44db0e2ee45e?name=PADUS4_1Geodatabase.zip",
            (
                "https://services.arcgis.com/v01gqwM5QqNysAAi/arcgis/rest/services/PADUS_Protection_Status_by_GAP_Status_Code/FeatureServer",
                "https://services.arcgis.com/v01gqwM5QqNysAAi/arcgis/rest/services/PADUS_Public_Access/FeatureServer",
            ),
        ),
        (
            "fema_nfhl",
            None,
            (
                "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer",
                "https://hazards.fema.gov/arcgis/services/public/NFHLWMS/MapServer/WMSServer?request=GetCapabilities&service=WMS",
                "https://hazards.fema.gov/arcgis/services/public/NFHL/MapServer/WFSServer?service=WFS&request=GetCapabilities",
            ),
        ),
    ],
)
def test_stage_public_dataset_manual_includes_confirmed_urls(
    tmp_path, dataset_id, expected_download_url, expected_urls
):
    """Manual staging notes should preserve confirmed download and access URLs."""

    output_path = stage_public_dataset(dataset_id, repo_root=tmp_path)
    text = output_path.read_text()

    if expected_download_url is not None:
        assert "download_url:" in text
        assert expected_download_url in text

    assert "access_urls:" in text
    for expected_url in expected_urls:
        assert expected_url in text


def test_build_fema_nfhl_download_url_encodes_expected_query():
    """The FEMA helper should build a direct ZIP URL from inventory fields."""

    url = build_fema_nfhl_download_url(
        "01001C",
        "Alabama",
        "Autauga County",
        "01001C_20231225.zip",
    )

    assert url == (
        "https://hazards.fema.gov/femaportal/NFHL/Download/ProductsDownLoadServlet"
        "?DFIRMID=01001C&state=ALABAMA&county=AUTAUGA%20COUNTY"
        "&fileName=01001C_20231225.zip"
    )


def test_stage_public_dataset_fema_override_includes_generated_download_url(tmp_path):
    """FEMA staging should include a generated community ZIP URL when provided."""

    url = build_fema_nfhl_download_url(
        "01001C",
        "Alabama",
        "Autauga County",
        "01001C_20231225.zip",
    )

    output_path = stage_public_dataset(
        "fema_nfhl",
        repo_root=tmp_path,
        download_url_override=url,
    )
    text = output_path.read_text()

    assert "download_url:" in text
    assert url in text


def test_stage_public_dataset_ribits_creates_webservice_workflow_note(tmp_path):
    """RIBITS staging should point users to the scripted webservice workflow."""

    output_path = stage_public_dataset("ribits", repo_root=tmp_path)
    text = output_path.read_text()

    assert output_path == tmp_path / "external-data/raw/ribits/MANUAL_DOWNLOAD.txt"
    assert "dataset_id: ribits" in text
    assert "landing_page: https://ribits.ops.usace.army.mil/" in text
    assert "download-ribits-bank-sites" in text
    assert "bank_site_list" in text
    assert "bank_site_data" in text


def test_download_ribits_bank_site_snapshot_writes_detail_records(tmp_path, monkeypatch):
    """The RIBITS snapshot helper should stitch list and detail webservice calls."""

    captured_urls = []

    class FakeResponse(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            self.close()

    def fake_urlopen(url, timeout=60):
        captured_urls.append(url)
        if "bank_site_list" in url:
            payload = {
                "ITEMS": [
                    {
                        "BANK_ID": 17,
                        "NAME": "Mud Slough",
                        "BANK_SITE_DATA_WS_URL": "https://ribits.ops.usace.army.mil/ords/RI/public/bank_site_data/?q={\"bank_id\":17}",
                    }
                ]
            }
        elif "bank_site_data" in url:
            payload = {
                "ITEMS": [
                    {
                        "BANK_ID": 17,
                        "BANK_NAME": "Mud Slough",
                        "SERVICE_AREAS": [{"SERVICE_AREA_NAME": "Primary Service Area"}],
                    }
                ]
            }
        else:
            raise AssertionError(f"Unexpected RIBITS URL: {url}")

        return FakeResponse(json.dumps(payload).encode("utf-8"))

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    output_path = download_ribits_bank_site_snapshot(
        tmp_path / "ribits_bank_sites_snapshot.json",
        filters={"district": "Portland"},
        limit=1,
    )

    snapshot = json.loads(output_path.read_text())

    assert output_path == tmp_path / "ribits_bank_sites_snapshot.json"
    assert snapshot["filters"] == {"district": "Portland"}
    assert snapshot["list_item_count"] == 1
    assert snapshot["item_count"] == 1
    assert snapshot["items"][0]["BANK_ID"] == 17
    assert snapshot["items"][0]["BANK_NAME"] == "Mud Slough"
    assert any("bank_site_list" in url for url in captured_urls)
    assert any("bank_site_data" in url for url in captured_urls)


def test_download_ribits_bank_site_snapshot_can_resume_from_checkpoint(
    tmp_path,
    monkeypatch,
    capsys,
):
    """The RIBITS snapshot workflow should save progress and continue on resume."""

    captured_urls = []
    first_attempt = {"interrupt": True}

    def fake_urlopen(url, timeout=60):
        text = url.full_url if hasattr(url, "full_url") else url
        captured_urls.append(text)
        if "bank_site_list" in text:
            payload = {"ITEMS": [{"BANK_ID": 17}, {"BANK_ID": 18}]}
            return FakeDownloadResponse(json.dumps(payload).encode("utf-8"))
        if '"bank_id":17' in text:
            payload = {"ITEMS": [{"BANK_ID": 17, "BANK_NAME": "Mud Slough"}]}
            return FakeDownloadResponse(json.dumps(payload).encode("utf-8"))
        if '"bank_id":18' in text:
            if first_attempt["interrupt"]:
                first_attempt["interrupt"] = False
                raise KeyboardInterrupt()
            payload = {"ITEMS": [{"BANK_ID": 18, "BANK_NAME": "Delta Marsh"}]}
            return FakeDownloadResponse(json.dumps(payload).encode("utf-8"))
        raise AssertionError(f"Unexpected RIBITS URL: {text}")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    output_path = tmp_path / "ribits_bank_sites_snapshot.json"
    checkpoint_path = tmp_path / "ribits_bank_sites_snapshot.checkpoint.json"

    with pytest.raises(KeyboardInterrupt):
        download_ribits_bank_site_snapshot(
            output_path,
            limit=2,
            checkpoint_path=checkpoint_path,
        )

    partial_snapshot = json.loads(output_path.read_text())
    assert partial_snapshot["item_count"] == 1
    assert checkpoint_path.exists()

    resumed_path = download_ribits_bank_site_snapshot(
        output_path,
        limit=2,
        checkpoint_path=checkpoint_path,
        resume=True,
    )

    resumed_snapshot = json.loads(resumed_path.read_text())
    assert resumed_snapshot["item_count"] == 2
    assert [item["BANK_ID"] for item in resumed_snapshot["items"]] == [17, 18]
    assert not checkpoint_path.exists()
    assert sum('"bank_id":17' in url for url in captured_urls) == 1
    assert sum("bank_site_list" in url for url in captured_urls) == 1

    progress_text = capsys.readouterr().err
    assert "Stopped RIBITS bank/site snapshot" in progress_text
    assert "Completed RIBITS bank/site snapshot" in progress_text


def test_stage_public_dataset_baxtel_creates_procurement_note(tmp_path):
    """Baxtel should stage as a manual commercial-procurement workflow."""

    output_path = stage_public_dataset("baxtel_us_data_center_sites", repo_root=tmp_path)
    text = output_path.read_text()

    assert output_path == tmp_path / "external-data/raw/data-centers/baxtel_SAMPLE_REQUEST.txt"
    assert "dataset_id: baxtel_us_data_center_sites" in text
    assert "landing_page: https://baxtel.com/services/datasets" in text
    assert "sample CSV" in text
    assert "schema documentation" in text
    assert "baxtel_data_center_sites.csv" in text


@pytest.mark.parametrize(
    ("dataset_id", "expected_path", "expected_text"),
    [
        (
            "data_center_osm_export",
            "external-data/raw/data-centers/osm_data_centers_QUERY.txt",
            "osm_data_centers.json",
        ),
        (
            "data_center_wikidata_export",
            "external-data/raw/data-centers/wikidata_data_centers_QUERY.txt",
            "wikidata_data_centers.json",
        ),
        (
            "data_center_manual_augmentation",
            "external-data/raw/data-centers/manual_data_centers_SCHEMA.txt",
            "manual_data_centers.csv",
        ),
    ],
)
def test_stage_public_dataset_data_center_workflow_creates_note_files(
    tmp_path, dataset_id, expected_path, expected_text
):
    """The public data center baseline inputs should have repo-local staging notes."""

    output_path = stage_public_dataset(dataset_id, repo_root=tmp_path)
    text = output_path.read_text()

    assert output_path == tmp_path / expected_path
    assert expected_text in text


@pytest.mark.parametrize(
    ("dataset_id", "expected_path", "expected_text"),
    [
        (
            "transmission_lines_osm_export",
            "external-data/raw/power/osm_transmission_lines_QUERY.txt",
            "osm_transmission_lines.json",
        ),
        (
            "substations_osm_export",
            "external-data/raw/power/osm_substations_QUERY.txt",
            "osm_substations.json",
        ),
    ],
)
def test_stage_public_dataset_power_workflow_creates_note_files(
    tmp_path, dataset_id, expected_path, expected_text
):
    """The public power baseline inputs should have repo-local staging notes."""

    output_path = stage_public_dataset(dataset_id, repo_root=tmp_path)
    text = output_path.read_text()

    assert output_path == tmp_path / expected_path
    assert expected_text in text


def test_stage_public_dataset_ribits_representative_download_is_unavailable(tmp_path):
    """RIBITS should stay manual-only until a stable scripted download path exists."""

    with pytest.raises(ValueError, match="Missing representative download URL for dataset: ribits"):
        stage_public_dataset(
            "ribits",
            repo_root=tmp_path,
            download_representative=True,
        )


def test_stage_public_dataset_urdb_downloads_direct_export(tmp_path, monkeypatch):
    """URDB should stage through the direct approved-rates export."""

    captured = {}

    def fake_urlopen(request, timeout=60):
        download_url = request.full_url if hasattr(request, "full_url") else request
        captured["download_url"] = download_url
        return FakeDownloadResponse(
            b"urdb export\n",
            headers={"Content-Length": str(len(b"urdb export\n"))},
            status=200,
        )

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    output_path = stage_public_dataset("urdb", repo_root=tmp_path)

    assert output_path == tmp_path / "external-data/raw/urdb/usurdb.csv.gz"
    assert output_path.read_text() == "urdb export\n"
    assert captured["download_url"] == "https://apps.openei.org/USURDB/download/usurdb.csv.gz"


@pytest.mark.parametrize(
    ("dataset_id", "expected_name"),
    [
        ("nwi_wetlands", "AL_geodatabase_wetlands.zip"),
        ("nlcd", "Annual_NLCD_LndCov_2023_CU_C1V0.zip"),
        ("pad_us_gap", "PADUS4_1Geodatabase.zip"),
    ],
)
def test_stage_public_dataset_downloads_representative_payload_for_manual_source(
    tmp_path, monkeypatch, dataset_id, expected_name
):
    """Manual sources with confirmed package URLs should support representative downloads."""

    captured = {}

    def fake_urlopen(request, timeout=60):
        url = request.full_url if hasattr(request, "full_url") else request
        captured["url"] = url
        return FakeDownloadResponse(
            f"downloaded from {url}\n".encode("utf-8"),
            headers={"Content-Length": str(len(f"downloaded from {url}\n".encode("utf-8")))},
            status=200,
        )

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    output_path = stage_public_dataset(
        dataset_id,
        repo_root=tmp_path,
        download_representative=True,
    )

    assert output_path == tmp_path / "external-data" / "raw" / output_path.parent.name / expected_name
    assert output_path.read_text().startswith("downloaded from ")
    assert captured["url"] == PUBLIC_DATASET_CATALOG[dataset_id].download_url

    note_path = tmp_path / PUBLIC_DATASET_CATALOG[dataset_id].output_relpath
    assert note_path.exists()
    assert "download_url:" in note_path.read_text()


def test_stage_public_dataset_nlcd_falls_back_to_wms_tiff_when_zip_download_fails(
    tmp_path, monkeypatch
):
    """NLCD staging should recover from ScienceBase failure by writing a usable TIFF."""

    grid_path = tmp_path / "tests/data/downscale/inputs/grid_char_weighted_scores.gpkg"
    grid_path.parent.mkdir(parents=True, exist_ok=True)
    gpd.GeoDataFrame(
        {"sc_point_gid": [1]},
        geometry=[box(0.0, 0.0, 4000.0, 4000.0)],
        crs="EPSG:5070",
    ).to_file(grid_path, driver="GPKG")

    with MemoryFile() as memfile:
        with memfile.open(
            driver="GTiff",
            height=2,
            width=2,
            count=1,
            dtype="uint8",
            crs="EPSG:5070",
            transform=from_origin(0.0, 2000.0, 1000.0, 1000.0),
            nodata=0,
        ) as dataset:
            dataset.write(np.array([[3, 6], [3, 6]], dtype=np.uint8), 1)
        tile_bytes = memfile.read()

    captured_urls = []

    def fake_urlopen(request, timeout=60):
        url = request.full_url if hasattr(request, "full_url") else request
        captured_urls.append(url)
        if url == PUBLIC_DATASET_CATALOG["nlcd"].download_url:
            raise urllib.error.URLError("ScienceBase unavailable")
        if "request=GetMap" in url or "REQUEST=GetMap" in url:
            return FakeDownloadResponse(
                tile_bytes,
                headers={"Content-Length": str(len(tile_bytes))},
                status=200,
            )
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    output_path = stage_public_dataset(
        "nlcd",
        repo_root=tmp_path,
        download_representative=True,
    )

    assert output_path == tmp_path / "external-data/raw/nlcd/Annual_NLCD_LndCov_2023_CU_C1V0.tif"
    assert output_path.exists()
    assert any(url == PUBLIC_DATASET_CATALOG["nlcd"].download_url for url in captured_urls)
    assert any("GetMap" in url for url in captured_urls)

    with rasterio.open(output_path) as dataset:
        values = np.unique(dataset.read(1))

    assert set(values.tolist()) == {21, 24}

    note_path = tmp_path / PUBLIC_DATASET_CATALOG["nlcd"].output_relpath
    assert note_path.exists()
    assert "download_url:" in note_path.read_text()


def test_stage_public_dataset_downloads_representative_fema_payload(tmp_path, monkeypatch):
    """FEMA representative downloads should use the generated community ZIP filename."""

    url = build_fema_nfhl_download_url(
        "01001C",
        "Alabama",
        "Autauga County",
        "01001C_20231225.zip",
    )
    captured = {}

    def fake_urlopen(request, timeout=60):
        download_url = request.full_url if hasattr(request, "full_url") else request
        captured["download_url"] = download_url
        return FakeDownloadResponse(
            b"fema zip payload\n",
            headers={"Content-Length": str(len(b"fema zip payload\n"))},
            status=200,
        )

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    output_path = stage_public_dataset(
        "fema_nfhl",
        repo_root=tmp_path,
        download_url_override=url,
        download_representative=True,
    )

    assert output_path == tmp_path / "external-data/raw/fema/01001C_20231225.zip"
    assert output_path.read_text() == "fema zip payload\n"
    assert captured["download_url"] == url

    note_path = tmp_path / PUBLIC_DATASET_CATALOG["fema_nfhl"].output_relpath
    assert note_path.exists()
    assert url in note_path.read_text()


def test_stage_public_dataset_reports_download_progress(tmp_path, monkeypatch, capsys):
    """Representative downloads should emit visible progress information."""

    def fake_urlopen(request, timeout=60):
        return FakeDownloadResponse(
            b"1234567890",
            headers={"Content-Length": "10"},
            status=200,
        )

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    stage_public_dataset(
        "nwi_wetlands",
        repo_root=tmp_path,
        download_representative=True,
    )

    assert "100.0%" in capsys.readouterr().err


def test_stage_public_dataset_can_resume_partial_download(tmp_path, monkeypatch):
    """Interrupted downloads should continue from the existing byte offset when resumed."""

    representative_path = tmp_path / "external-data/raw/nwi/AL_geodatabase_wetlands.zip"
    representative_path.parent.mkdir(parents=True, exist_ok=True)
    representative_path.write_bytes(b"hello ")
    captured = {}

    def fake_urlopen(request, timeout=60):
        captured["range"] = request.headers.get("Range")
        return FakeDownloadResponse(
            b"world",
            headers={"Content-Length": "5"},
            status=206,
        )

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    output_path = stage_public_dataset(
        "nwi_wetlands",
        repo_root=tmp_path,
        download_representative=True,
        resume=True,
    )

    assert output_path == representative_path
    assert output_path.read_bytes() == b"hello world"
    assert captured["range"] == "bytes=6-"


def test_build_public_report_feasible_land_frame_excludes_nlcd_water_and_wetlands(
    tmp_path,
):
    """Bounded feasible land should drop NLCD water and wetland dominated cells."""

    nlcd_target_path = tmp_path / "external-data/raw/nlcd/Annual_NLCD_LndCov_2023_CU_C1V0.tif"
    nlcd_target_path.parent.mkdir(parents=True, exist_ok=True)
    nlcd_data = np.full((10, 30), 81, dtype=np.uint8)
    nlcd_data[:, 0:10] = 11
    nlcd_data[:, 10:20] = 95
    with rasterio.open(
        nlcd_target_path,
        "w",
        driver="GTiff",
        height=nlcd_data.shape[0],
        width=nlcd_data.shape[1],
        count=1,
        dtype=nlcd_data.dtype,
        crs="EPSG:4326",
        transform=from_origin(0.0, 1.0, 0.1, 0.1),
        nodata=0,
    ) as dataset:
        dataset.write(nlcd_data, 1)

    frame = gpd.GeoDataFrame(
        {
            "sc_point_gid": [1, 2, 3],
            "developable_capacity_mw": [100.0, 100.0, 100.0],
            "suitability_score": [0.1, 0.2, 0.3],
        },
        geometry=[
            box(0.0, 0.0, 1.0, 1.0),
            box(1.0, 0.0, 2.0, 1.0),
            box(2.0, 0.0, 3.0, 1.0),
        ],
        crs="EPSG:4326",
    )

    feasible = _build_public_report_feasible_land_frame(tmp_path, frame)

    assert feasible["sc_point_gid"].tolist() == [3]
    assert feasible["is_feasible_land"].tolist() == [True]
    assert feasible["water_wetland_share"].tolist() == [pytest.approx(0.0)]


def test_assess_public_eer_drop_in_compatibility_marks_workbook_as_transform_only():
    """Workbook tables should be classified as transformable, not direct drop-ins."""

    assessment = assess_public_eer_drop_in_compatibility(
        final_energy_columns=[
            "Sector",
            "Subsector",
            "Final Energy",
            "Unit",
            "State",
            "Year",
            "CENTRAL HIGH DATA CENTER",
        ],
        mapping_columns=["county", "zone", "sqmi", "Cover"],
        total_anchor_columns=["year", "dc_load_mw"],
        regional_anchor_columns=["Unnamed: 0", "year", "zone_group", "dc_load_mw"],
        generated_total_columns=["year", "dc_load_mw"],
        generated_regional_columns=["year", "zone_group", "dc_load_mw"],
    )

    assert assessment["drop_in_replacement"] is False
    assert assessment["direct_total_drop_in"] is False
    assert assessment["direct_regional_drop_in"] is False
    assert assessment["missing_total_columns"] == ["year", "dc_load_mw"]
    assert assessment["missing_regional_columns"] == ["year", "zone_group", "dc_load_mw"]
    assert assessment["generated_total_schema_match"] is True
    assert assessment["generated_regional_schema_match"] is True
    assert any("CSV load-projection files" in reason for reason in assessment["reasons"])
    assert any("zone_group" in reason for reason in assessment["reasons"])


def test_build_nerc_reserve_margin_table_derives_headroom_metrics():
    """NERC reserve-margin rows should expose usable headroom metrics."""

    margin_df = build_nerc_reserve_margin_table()

    texas = margin_df.loc[
        margin_df["assessment_area"] == "Texas RE-ERCOT"
    ].iloc[0]
    miso = margin_df.loc[margin_df["assessment_area"] == "MISO"].iloc[0]

    assert texas["peak_season"] == "summer"
    assert texas["arm_2026"] == pytest.approx(28.2)
    assert texas["rml_2026"] == pytest.approx(13.75)
    assert texas["margin_headroom_2029"] == pytest.approx(17.05)
    assert texas["min_margin_headroom_2026_2030"] == pytest.approx(14.45)

    assert miso["margin_headroom_2030"] == pytest.approx(-4.2)
    assert miso["min_margin_headroom_2026_2030"] == pytest.approx(-4.2)


def test_build_nerc_emm_zone_feature_frame_maps_assessment_areas(data_dir):
    """The repo's EMM zones should map cleanly to NERC assessment areas."""

    zones_path = data_dir / "downscale" / "inputs" / "regions" / "eer_adp_zones.gpkg"
    zone_groups_df = gpd.read_file(zones_path)

    zone_feature_df = build_nerc_emm_zone_feature_frame(zone_groups_df)
    distinct_df = zone_feature_df[[
        "emm_zone",
        "zone_group",
        "assessment_area",
        "min_margin_headroom_2026_2030",
    ]].drop_duplicates()

    texas = distinct_df.loc[distinct_df["emm_zone"] == "Texas"].iloc[0]
    florida = distinct_df.loc[distinct_df["emm_zone"] == "Florida"].iloc[0]
    great_basin = distinct_df.loc[distinct_df["emm_zone"] == "Great Basin"].iloc[0]

    assert texas["zone_group"] == "Central"
    assert texas["assessment_area"] == "Texas RE-ERCOT"
    assert texas["min_margin_headroom_2026_2030"] == pytest.approx(14.45)

    assert florida["zone_group"] == "East"
    assert florida["assessment_area"] == "SERC-Florida Peninsula"
    assert florida["min_margin_headroom_2026_2030"] == pytest.approx(6.1)

    assert great_basin["zone_group"] == "West"
    assert great_basin["assessment_area"] == "WECC-Basin"
    assert great_basin["min_margin_headroom_2026_2030"] == pytest.approx(2.9)

    assert distinct_df["assessment_area"].notna().all()


def test_generate_nerc_reserve_margin_features_writes_zone_and_grid_artifacts(
    tmp_path, data_dir
):
    """The NERC pipeline should write derived assessment, zone, and grid artifacts."""

    zones_path = data_dir / "downscale" / "inputs" / "regions" / "eer_adp_zones.gpkg"
    grid_path = data_dir / "downscale" / "inputs" / "grid_char_weighted_scores.gpkg"

    assessment_path, zone_path, grid_output_path = generate_nerc_reserve_margin_features(
        zones_path,
        tmp_path,
        grid_path=grid_path,
    )

    assert assessment_path == tmp_path / "nerc_ltra_2025_assessment_area_margins.csv"
    assert zone_path == tmp_path / "nerc_ltra_2025_emm_zone_margins.gpkg"
    assert grid_output_path == tmp_path / "nerc_ltra_2025_grid_margins.gpkg"
    assert assessment_path.exists()
    assert zone_path.exists()
    assert grid_output_path.exists()

    assessment_df = pd.read_csv(assessment_path)
    zone_df = gpd.read_file(zone_path)
    grid_df = gpd.read_file(grid_output_path)

    assert "assessment_area" in assessment_df.columns
    assert "min_margin_headroom_2026_2030" in assessment_df.columns
    assert "assessment_area" in zone_df.columns
    assert "margin_headroom_2030" in zone_df.columns
    assert "assessment_area" in grid_df.columns
    assert "min_margin_headroom_2026_2030" in grid_df.columns
    assert grid_df["assessment_area"].notna().all()


def test_build_osm_data_center_frame_extracts_centers_and_status():
    """OSM payload rows should normalize into point features with status fields."""

    elements = [
        {
            "type": "node",
            "id": 101,
            "lat": 39.7392,
            "lon": -104.9903,
            "tags": {
                "name": "Alpha Data Center",
                "operator": "Example Compute",
                "building": "data_center",
                "wikidata": "Q1001",
            },
        },
        {
            "type": "way",
            "id": 202,
            "center": {"lat": 32.7767, "lon": -96.7970},
            "tags": {
                "name": "Beta Campus",
                "operator": "BuildCo",
                "building": "construction",
                "construction": "data_center",
            },
        },
    ]

    osm_df = build_osm_data_center_frame(elements)

    alpha = osm_df.loc[osm_df["source_id"] == "osm:node/101"].iloc[0]
    beta = osm_df.loc[osm_df["source_id"] == "osm:way/202"].iloc[0]

    assert alpha["name"] == "Alpha Data Center"
    assert alpha["operator"] == "Example Compute"
    assert alpha["site_status"] == "existing"
    assert alpha["wikidata_id"] == "Q1001"
    assert alpha.geometry.x == pytest.approx(-104.9903)
    assert alpha.geometry.y == pytest.approx(39.7392)

    assert beta["site_status"] == "under_construction"
    assert beta.geometry.x == pytest.approx(-96.7970)
    assert beta.geometry.y == pytest.approx(32.7767)


def test_build_public_data_center_baseline_merges_sources_and_manual_records():
    """The first-pass public baseline should dedupe linked OSM, Wikidata, and manual rows."""

    osm_df = build_osm_data_center_frame(
        [
            {
                "type": "node",
                "id": 101,
                "lat": 39.7392,
                "lon": -104.9903,
                "tags": {
                    "name": "Alpha Data Center",
                    "operator": "Example Compute",
                    "building": "data_center",
                    "wikidata": "Q1001",
                },
            },
            {
                "type": "way",
                "id": 202,
                "center": {"lat": 32.7767, "lon": -96.7970},
                "tags": {
                    "name": "Beta Campus",
                    "building": "data_center",
                },
            },
        ]
    )
    wikidata_df = build_wikidata_data_center_frame(
        [
            {
                "item": {"value": "http://www.wikidata.org/entity/Q1001"},
                "itemLabel": {"value": "Alpha Data Center"},
                "coord": {"value": "Point(-104.9903 39.7392)"},
                "operatorLabel": {"value": "Example Compute"},
            },
            {
                "item": {"value": "http://www.wikidata.org/entity/Q2002"},
                "itemLabel": {"value": "Gamma Digital Campus"},
                "coord": {"value": "Point(-118.2437 34.0522)"},
                "operatorLabel": {"value": "Gamma Cloud"},
            },
        ]
    )
    manual_df = pd.DataFrame(
        [
            {
                "name": "Delta Hyperscale",
                "operator": "Delta Compute",
                "latitude": 33.4484,
                "longitude": -112.0740,
                "site_status": "planned",
                "source_url": "https://example.com/delta",
                "source_note": "Operator announcement",
            }
        ]
    )

    baseline_df = build_public_data_center_baseline(
        osm_df,
        wikidata_df,
        manual_records=manual_df,
    )

    assert len(baseline_df) == 4

    alpha = baseline_df.loc[baseline_df["name"] == "Alpha Data Center"].iloc[0]
    gamma = baseline_df.loc[baseline_df["name"] == "Gamma Digital Campus"].iloc[0]
    delta = baseline_df.loc[baseline_df["name"] == "Delta Hyperscale"].iloc[0]

    assert alpha["source_count"] == 2
    assert alpha["sources"] == "osm;wikidata"
    assert alpha["wikidata_id"] == "Q1001"

    assert gamma["sources"] == "wikidata"
    assert gamma["site_status"] == "existing"

    assert delta["sources"] == "manual"
    assert delta["site_status"] == "planned"
    assert delta["source_url"] == "https://example.com/delta"


def test_generate_public_data_center_baseline_writes_csv_and_geopackage(tmp_path):
    """The baseline generator should write reproducible point-layer artifacts."""

    osm_payload_path = tmp_path / "osm_data_centers.json"
    wikidata_payload_path = tmp_path / "wikidata_data_centers.json"
    manual_csv_path = tmp_path / "manual_data_centers.csv"

    pd.DataFrame(
        [
            {
                "name": "Delta Hyperscale",
                "operator": "Delta Compute",
                "latitude": 33.4484,
                "longitude": -112.0740,
                "site_status": "planned",
                "source_url": "https://example.com/delta",
                "source_note": "Operator announcement",
            }
        ]
    ).to_csv(manual_csv_path, index=False)
    osm_payload_path.write_text(
        pd.Series(
            {
                "elements": [
                    {
                        "type": "node",
                        "id": 101,
                        "lat": 39.7392,
                        "lon": -104.9903,
                        "tags": {
                            "name": "Alpha Data Center",
                            "operator": "Example Compute",
                            "building": "data_center",
                            "wikidata": "Q1001",
                        },
                    }
                ]
            }
        ).to_json()
    )
    wikidata_payload_path.write_text(
        pd.Series(
            {
                "results": {
                    "bindings": [
                        {
                            "item": {"value": "http://www.wikidata.org/entity/Q1001"},
                            "itemLabel": {"value": "Alpha Data Center"},
                            "coord": {"value": "Point(-104.9903 39.7392)"},
                            "operatorLabel": {"value": "Example Compute"},
                        },
                        {
                            "item": {"value": "http://www.wikidata.org/entity/Q2002"},
                            "itemLabel": {"value": "Gamma Digital Campus"},
                            "coord": {"value": "Point(-118.2437 34.0522)"},
                            "operatorLabel": {"value": "Gamma Cloud"},
                        },
                    ]
                }
            }
        ).to_json()
    )

    csv_path, gpkg_path = generate_public_data_center_baseline(
        osm_payload_path,
        wikidata_payload_path,
        tmp_path,
        manual_csv_path=manual_csv_path,
    )

    assert csv_path == tmp_path / "public_data_center_baseline.csv"
    assert gpkg_path == tmp_path / "public_data_center_baseline.gpkg"
    assert csv_path.exists()
    assert gpkg_path.exists()

    baseline_csv = pd.read_csv(csv_path)
    baseline_gdf = gpd.read_file(gpkg_path)

    assert set(baseline_csv["name"]) == {
        "Alpha Data Center",
        "Gamma Digital Campus",
        "Delta Hyperscale",
    }
    assert set(baseline_gdf["sources"]) == {"osm;wikidata", "wikidata", "manual"}


def test_build_osm_transmission_line_frame_filters_high_voltage_features():
    """The line baseline should keep only OSM linework at or above the threshold."""

    elements = [
        {
            "type": "way",
            "id": 301,
            "geometry": [
                {"lat": 39.70, "lon": -104.99},
                {"lat": 39.71, "lon": -104.95},
            ],
            "tags": {
                "name": "Front Range 230 kV",
                "operator": "GridCo",
                "power": "line",
                "voltage": "230000",
            },
        },
        {
            "type": "way",
            "id": 302,
            "geometry": [
                {"lat": 35.20, "lon": -97.50},
                {"lat": 35.25, "lon": -97.45},
            ],
            "tags": {
                "name": "Metro 69 kV",
                "power": "minor_line",
                "voltage": "69 kV",
            },
        },
        {
            "type": "way",
            "id": 303,
            "geometry": [
                {"lat": 33.44, "lon": -112.07},
                {"lat": 33.45, "lon": -112.00},
            ],
            "tags": {
                "name": "Desert Cable",
                "power": "cable",
                "location": "underground",
                "voltage": "115000;138000",
            },
        },
    ]

    line_df = build_osm_transmission_line_frame(elements, min_voltage_kv=135)

    assert list(line_df["source_id"]) == ["osm:way/301", "osm:way/303"]
    assert list(line_df["max_voltage_kv"]) == [pytest.approx(230.0), pytest.approx(138.0)]
    assert bool(
        line_df.loc[line_df["source_id"] == "osm:way/303", "is_underground"].iloc[0]
    ) is True


def test_build_osm_substation_frame_extracts_centers_and_voltage():
    """The substation baseline should normalize node and area-centered OSM features."""

    elements = [
        {
            "type": "node",
            "id": 401,
            "lat": 32.7767,
            "lon": -96.7970,
            "tags": {
                "name": "Dallas Switchyard",
                "operator": "Example Utility",
                "power": "substation",
                "substation": "transmission",
                "voltage": "345000",
            },
        },
        {
            "type": "way",
            "id": 402,
            "center": {"lat": 29.7604, "lon": -95.3698},
            "tags": {
                "name": "Houston East",
                "power": "substation",
                "voltage": "138 kV",
            },
        },
    ]

    substation_df = build_osm_substation_frame(elements)

    assert list(substation_df["source_id"]) == ["osm:node/401", "osm:way/402"]
    assert substation_df.loc[substation_df["source_id"] == "osm:node/401", "substation_type"].iloc[0] == "transmission"
    assert substation_df.loc[substation_df["source_id"] == "osm:node/401", "max_voltage_kv"].iloc[0] == pytest.approx(345.0)
    assert substation_df.loc[substation_df["source_id"] == "osm:way/402", "max_voltage_kv"].iloc[0] == pytest.approx(138.0)


def test_generate_public_power_infrastructure_baseline_writes_line_and_substation_layers(
    tmp_path,
):
    """The OSM power baseline should write derived line and point GeoPackages."""

    line_payload_path = tmp_path / "osm_transmission_lines.json"
    substation_payload_path = tmp_path / "osm_substations.json"

    line_payload_path.write_text(
        json.dumps(
            {
                "elements": [
                    {
                        "type": "way",
                        "id": 301,
                        "geometry": [
                            {"lat": 39.70, "lon": -104.99},
                            {"lat": 39.71, "lon": -104.95},
                        ],
                        "tags": {
                            "name": "Front Range 230 kV",
                            "power": "line",
                            "voltage": "230000",
                        },
                    },
                    {
                        "type": "way",
                        "id": 302,
                        "geometry": [
                            {"lat": 35.20, "lon": -97.50},
                            {"lat": 35.25, "lon": -97.45},
                        ],
                        "tags": {
                            "name": "Metro 69 kV",
                            "power": "minor_line",
                            "voltage": "69000",
                        },
                    },
                ]
            }
        )
    )
    substation_payload_path.write_text(
        json.dumps(
            {
                "elements": [
                    {
                        "type": "node",
                        "id": 401,
                        "lat": 32.7767,
                        "lon": -96.7970,
                        "tags": {
                            "name": "Dallas Switchyard",
                            "power": "substation",
                            "substation": "transmission",
                            "voltage": "345000",
                        },
                    }
                ]
            }
        )
    )

    line_path, substation_path = generate_public_power_infrastructure_baseline(
        line_payload_path,
        substation_payload_path,
        tmp_path,
    )

    assert line_path == tmp_path / "public_transmission_lines_135kv.gpkg"
    assert substation_path == tmp_path / "public_substations.gpkg"
    assert line_path.exists()
    assert substation_path.exists()

    line_df = gpd.read_file(line_path)
    substation_df = gpd.read_file(substation_path)

    assert list(line_df["source_id"]) == ["osm:way/301"]
    assert line_df["max_voltage_kv"].iloc[0] == pytest.approx(230.0)
    assert list(substation_df["source_id"]) == ["osm:node/401"]
    assert substation_df["max_voltage_kv"].iloc[0] == pytest.approx(345.0)


@pytest.mark.parametrize(
    ("dataset_id", "expected_path", "expected_text"),
    [
        (
            "fiber_lines_osm_export",
            "external-data/raw/fiber/osm_fiber_lines_QUERY.txt",
            "osm_fiber_lines.json",
        ),
        (
            "fcc_bdc_fiber_availability_export",
            "external-data/raw/fiber/fcc_bdc_fiber_availability_EXPORT.txt",
            "fcc_bdc_fiber_availability.gpkg",
        ),
    ],
)
def test_stage_public_dataset_fiber_workflow_creates_note_files(
    tmp_path, dataset_id, expected_path, expected_text
):
    """The public fiber proxy inputs should have repo-local staging notes."""

    output_path = stage_public_dataset(dataset_id, repo_root=tmp_path)
    text = output_path.read_text()

    assert output_path == tmp_path / expected_path
    assert expected_text in text


@pytest.mark.parametrize(
    ("bundle_id", "case"),
    EXAMPLE_BUNDLE_CASES.items(),
)
def test_stage_public_example_bundle_writes_representative_inputs(tmp_path, bundle_id, case):
    """Example bundles should stage runnable sample inputs and a documented command."""

    bundle_dir = stage_public_example_bundle(bundle_id, repo_root=tmp_path)

    assert bundle_dir == tmp_path / "external-data" / "examples" / bundle_id
    for relative_path in case["expected_inputs"]:
        assert (bundle_dir / relative_path).exists()

    readme_text = (bundle_dir / "README.md").read_text()
    assert case["command_text"] in readme_text


@pytest.mark.parametrize(
    ("bundle_id", "case"),
    EXAMPLE_BUNDLE_CASES.items(),
)
def test_stage_public_example_bundle_supports_validated_cli_example_runs(
    tmp_path,
    bundle_id,
    case,
):
    """Each staged example bundle should be runnable through the real CLI."""

    bundle_dir = stage_public_example_bundle(bundle_id, repo_root=tmp_path)
    output_dir = bundle_dir / "output"

    exit_code = main(case["build_args"](bundle_dir, output_dir))

    assert exit_code == 0
    for relative_path in case["expected_outputs"]:
        assert (output_dir / relative_path).exists()


def test_main_emits_progress_for_long_running_public_data_commands(tmp_path, capsys):
    """CLI commands should emit coarse-grained progress updates for analysis workflows."""

    bundle_dir = stage_public_example_bundle("public_data_center_baseline", repo_root=tmp_path)
    output_dir = bundle_dir / "output"

    exit_code = main(
        [
            "generate-data-center-baseline",
            "--osm-payload",
            (bundle_dir / "osm_data_centers.json").as_posix(),
            "--wikidata-payload",
            (bundle_dir / "wikidata_data_centers.json").as_posix(),
            "--manual-csv",
            (bundle_dir / "manual_data_centers.csv").as_posix(),
            "--output-dir",
            output_dir.as_posix(),
        ]
    )

    assert exit_code == 0
    progress_text = capsys.readouterr().err
    assert "Starting generate-data-center-baseline" in progress_text
    assert "Completed generate-data-center-baseline" in progress_text


def test_run_public_reproduction_workflow_can_resume_after_interrupt(
    tmp_path,
    monkeypatch,
    capsys,
):
    """The multi-step public reproduction workflow should checkpoint completed steps."""

    status_path = tmp_path / "public_reproduction_status.json"
    call_counts = {
        "assess": 0,
        "generate": 0,
        "smoke": 0,
        "nerc": 0,
    }

    def fake_assess(*args, **kwargs):
        call_counts["assess"] += 1
        return {"drop_in_replacement": False, "reasons": ["transform only"]}

    def fake_generate(*args, **kwargs):
        call_counts["generate"] += 1
        if call_counts["generate"] == 1:
            raise KeyboardInterrupt()
        outputs = [tmp_path / "total.csv", tmp_path / "regional.csv", tmp_path / "groups.csv"]
        for path in outputs:
            path.write_text("ok\n")
        return tuple(outputs)

    def fake_smoke(config_path, output_path, repo_root=None):
        call_counts["smoke"] += 1
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("smoke\n")
        return {"output_path": output_path.as_posix(), "stdout": [output_path.as_posix()]}

    def fake_nerc(*args, **kwargs):
        call_counts["nerc"] += 1
        outputs = [tmp_path / "assessment.csv", tmp_path / "zones.gpkg", tmp_path / "grid.gpkg"]
        for path in outputs:
            path.write_text("ok\n")
        return tuple(outputs)

    monkeypatch.setattr("reVeal.public_data.assess_public_eer_drop_in_compatibility_from_paths", fake_assess)
    monkeypatch.setattr("reVeal.public_data.generate_eer_public_projection_csvs", fake_generate)
    monkeypatch.setattr("reVeal.public_data._run_public_reproduction_smoke", fake_smoke)
    monkeypatch.setattr("reVeal.public_data.generate_nerc_reserve_margin_features", fake_nerc)

    with pytest.raises(KeyboardInterrupt):
        run_public_reproduction_workflow(repo_root=tmp_path, status_path=status_path)

    partial_status = json.loads(status_path.read_text())
    assert partial_status["completed_steps"] == ["assess_eer_drop_in"]
    assert partial_status["stopped_at_step"] == "generate_eer_loads"

    final_status_path = run_public_reproduction_workflow(
        repo_root=tmp_path,
        status_path=status_path,
        resume=True,
    )

    final_status = json.loads(final_status_path.read_text())
    assert final_status["completed"] is True
    assert final_status["completed_steps"] == [
        "assess_eer_drop_in",
        "generate_eer_loads",
        "total_smoke",
        "regional_smoke",
        "generate_nerc_features",
    ]
    assert call_counts == {"assess": 1, "generate": 2, "smoke": 2, "nerc": 1}

    progress_text = capsys.readouterr().err
    assert "Stopped run-public-reproduction at step generate_eer_loads" in progress_text
    assert "Completed run-public-reproduction" in progress_text


def test_run_public_example_workflows_can_resume_after_interrupt(
    tmp_path,
    monkeypatch,
    capsys,
):
    """The generated public example-workflow runner should checkpoint completed steps."""

    status_path = tmp_path / "public_example_workflows_status.json"
    call_counts = {
        "public_data_center_baseline": 0,
        "public_fiber_proxy_baseline": 0,
    }

    def fake_build_steps(repo_root, bundle_ids=None, force_stage=False):
        def run_data_center():
            call_counts["public_data_center_baseline"] += 1
            output_path = tmp_path / "data_center.gpkg"
            output_path.write_text("ok\n")
            return {
                "bundle_id": "public_data_center_baseline",
                "outputs": [output_path.as_posix()],
            }

        def run_fiber():
            call_counts["public_fiber_proxy_baseline"] += 1
            if call_counts["public_fiber_proxy_baseline"] == 1:
                raise KeyboardInterrupt()
            output_path = tmp_path / "fiber.tif"
            output_path.write_text("ok\n")
            return {
                "bundle_id": "public_fiber_proxy_baseline",
                "outputs": [output_path.as_posix()],
            }

        return [
            {
                "step_id": "public_data_center_baseline",
                "runner": run_data_center,
            },
            {
                "step_id": "public_fiber_proxy_baseline",
                "runner": run_fiber,
            },
        ]

    monkeypatch.setattr("reVeal.public_data._build_public_example_workflow_steps", fake_build_steps)

    with pytest.raises(KeyboardInterrupt):
        run_public_example_workflows(repo_root=tmp_path, status_path=status_path)

    partial_status = json.loads(status_path.read_text())
    assert partial_status["completed_steps"] == ["public_data_center_baseline"]
    assert partial_status["stopped_at_step"] == "public_fiber_proxy_baseline"

    final_status_path = run_public_example_workflows(
        repo_root=tmp_path,
        status_path=status_path,
        resume=True,
    )

    final_status = json.loads(final_status_path.read_text())
    assert final_status["completed"] is True
    assert final_status["completed_steps"] == [
        "public_data_center_baseline",
        "public_fiber_proxy_baseline",
    ]
    assert call_counts == {
        "public_data_center_baseline": 1,
        "public_fiber_proxy_baseline": 2,
    }

    progress_text = capsys.readouterr().err
    assert "Stopped run-public-example-workflows at step public_fiber_proxy_baseline" in progress_text
    assert "Completed run-public-example-workflows" in progress_text


def test_main_summarize_public_workflow_status_reports_fit_and_gaps(tmp_path, capsys):
    """The status-summary command should surface compact workflow fit/gap output."""

    status_path = tmp_path / "public_reproduction_status.json"
    status_path.write_text(
        json.dumps(
            {
                "workflow": "run-public-reproduction",
                "repo_root": tmp_path.as_posix(),
                "completed": True,
                "completed_steps": ["assess_eer_drop_in", "generate_eer_loads"],
                "stopped_at_step": None,
                "step_results": {
                    "assess_eer_drop_in": {
                        "drop_in_replacement": False,
                        "generated_total_schema_match": True,
                        "generated_regional_schema_match": True,
                        "reasons": [
                            "The public source is an XLSX workbook while the downscale configs reference CSV load-projection files.",
                            "Grouped regional outputs require the repo mapping sheet.",
                        ],
                    },
                    "generate_eer_loads": [
                        (tmp_path / "national.csv").as_posix(),
                        (tmp_path / "regional.csv").as_posix(),
                    ],
                },
            }
        )
    )

    exit_code = main(
        [
            "summarize-public-workflow-status",
            "--status-path",
            status_path.as_posix(),
        ]
    )

    assert exit_code == 0
    stdout_text = capsys.readouterr().out
    assert "Workflow: run-public-reproduction" in stdout_text
    assert "Completed: yes (2 steps)" in stdout_text
    assert "Direct drop-in replacement: no" in stdout_text
    assert "Generated total schema match: yes" in stdout_text
    assert "Generated regional schema match: yes" in stdout_text
    assert "Gaps:" in stdout_text
    assert "XLSX workbook" in stdout_text


def test_annotate_public_report_cell_names_selects_more_popular_candidate():
    """Cell naming should keep both candidate lookups and choose the higher-score label."""

    frame = gpd.GeoDataFrame(
        {
            "sc_point_gid": [101, 202],
            "latitude": [0.5, 1.5],
            "longitude": [0.5, 1.5],
        },
        geometry=[
            box(0.0, 0.0, 1.0, 1.0),
            box(1.0, 1.0, 2.0, 2.0),
        ],
        crs="EPSG:4326",
    )

    named = _annotate_public_report_cell_names(
        frame,
        place_catalog=[
            {
                "name": "Metro Alpha",
                "kind": "metro",
                "latitude": 0.4,
                "longitude": 0.4,
                "popularity_score": 92.0,
            },
            {
                "name": "Lake Alpha",
                "kind": "natural",
                "latitude": 0.7,
                "longitude": 0.7,
                "popularity_score": 44.0,
            },
            {
                "name": "Metro Beta",
                "kind": "metro",
                "latitude": 1.4,
                "longitude": 1.4,
                "popularity_score": 61.0,
            },
            {
                "name": "Canyon Beta",
                "kind": "natural",
                "latitude": 1.6,
                "longitude": 1.6,
                "popularity_score": 88.0,
            },
        ],
    )

    assert named["cell_name"].tolist() == ["Metro Alpha", "Canyon Beta"]
    assert named["cell_name_basis"].tolist() == ["metro", "natural"]
    assert named["metro_feature_name"].tolist() == ["Metro Alpha", "Metro Beta"]
    assert named["natural_feature_name"].tolist() == ["Lake Alpha", "Canyon Beta"]
    assert named["cell_name_popularity_score"].tolist() == [pytest.approx(92.0), pytest.approx(88.0)]


def test_annotate_public_report_cell_names_handles_projected_geometry():
    """Projected suitability polygons should still use geographic cell lookup correctly."""

    frame = gpd.GeoDataFrame(
        {
            "sc_point_gid": [303],
            "latitude": [40.0],
            "longitude": [-105.0],
        },
        geometry=[box(-105.2, 39.8, -104.8, 40.2)],
        crs="EPSG:4326",
    ).to_crs("EPSG:3857")

    named = _annotate_public_report_cell_names(
        frame,
        place_catalog=[
            {
                "name": "Metro Gamma",
                "kind": "metro",
                "latitude": 40.01,
                "longitude": -105.01,
                "popularity_score": 91.0,
            },
            {
                "name": "Ridge Gamma",
                "kind": "natural",
                "latitude": 40.02,
                "longitude": -104.99,
                "popularity_score": 55.0,
            },
        ],
    )

    assert named["cell_name"].tolist() == ["Metro Gamma"]
    assert named["cell_name_match_scope"].tolist() == ["in_cell"]
    assert named["metro_feature_match_scope"].tolist() == ["in_cell"]


def test_annotate_public_report_cell_names_prefers_gateway_anchor_for_natural_base_name():
    """Natural-feature labels should anchor to the mapped gateway place instead of a nearer metro."""

    frame = gpd.GeoDataFrame(
        {
            "sc_point_gid": [404],
            "latitude": [33.80],
            "longitude": [-84.35],
        },
        geometry=[box(-84.40, 33.75, -84.30, 33.85)],
        crs="EPSG:4326",
    )

    named = _annotate_public_report_cell_names(
        frame,
        place_catalog=[
            {
                "name": "Atlanta",
                "kind": "metro",
                "latitude": 33.7490,
                "longitude": -84.3880,
                "popularity_score": 87.0,
            },
            {
                "name": "Great Smoky Mountains",
                "kind": "natural",
                "latitude": 35.6532,
                "longitude": -83.5070,
                "popularity_score": 94.0,
            },
        ],
        place_anchor_catalog=[
            {
                "name": "Atlanta",
                "latitude": 33.7490,
                "longitude": -84.3880,
                "county": "Fulton County",
                "state": "GA",
                "popularity_score": 87.0,
            },
            {
                "name": "Gatlinburg",
                "latitude": 35.7143,
                "longitude": -83.5102,
                "county": "Sevier County",
                "state": "TN",
                "popularity_score": 61.0,
            },
        ],
    )

    assert named["base_cell_name"].tolist() == ["Great Smoky Mountains"]
    assert named["anchor_place_name"].tolist() == ["Gatlinburg"]
    assert named["anchor_place_county"].tolist() == ["Sevier County"]
    assert named["anchor_place_state"].tolist() == ["TN"]


def test_annotate_public_report_cell_names_disambiguates_duplicate_names():
    """Duplicate base place names should be made unique with gateway-place phrasing."""

    frame = gpd.GeoDataFrame(
        {
            "sc_point_gid": [101, 202],
            "latitude": [35.93, 35.64],
            "longitude": [-112.13, -112.16],
        },
        geometry=[
            box(-112.16, 35.90, -112.10, 35.96),
            box(-112.20, 35.60, -112.12, 35.68),
        ],
        crs="EPSG:4326",
    )

    named = _annotate_public_report_cell_names(
        frame,
        place_catalog=[
            {
                "name": "Grand Canyon",
                "kind": "natural",
                "latitude": 35.95,
                "longitude": -112.13,
                "popularity_score": 92.0,
            },
            {
                "name": "Grand Canyon",
                "kind": "natural",
                "latitude": 35.64,
                "longitude": -112.16,
                "popularity_score": 92.0,
            },
            {
                "name": "Lake Elsewhere",
                "kind": "natural",
                "latitude": 39.0,
                "longitude": -104.0,
                "popularity_score": 10.0,
            },
        ],
        place_anchor_catalog=[
            {
                "name": "Tusayan",
                "latitude": 35.9736,
                "longitude": -112.1263,
                "county": "Coconino County",
                "state": "AZ",
                "popularity_score": 80.0,
            },
            {
                "name": "Valle",
                "latitude": 35.6500,
                "longitude": -112.1400,
                "county": "Coconino County",
                "state": "AZ",
                "popularity_score": 40.0,
            },
        ],
    )

    assert named["base_cell_name"].tolist() == ["Grand Canyon", "Grand Canyon"]
    assert named["cell_name"].is_unique
    assert named["cell_name_is_disambiguated"].tolist() == [True, True]
    assert named["anchor_place_name"].tolist() == ["Tusayan", "Tusayan"]
    assert named["anchor_place_county"].tolist() == ["Coconino County", "Coconino County"]
    assert named["anchor_place_state"].tolist() == ["AZ", "AZ"]
    assert all("(Cell " not in value for value in named["cell_name"])
    assert all("near Grand Canyon" in value for value in named["cell_name"])
    assert all("Coconino County, AZ" in value for value in named["cell_name"])


def test_run_public_report_bundle_writes_manifest_and_deviation_note(tmp_path, monkeypatch, capsys):
    """The report-bundle runner should materialize a bounded output bundle plus deviations."""

    bundle_dir = tmp_path / "report-bundle"
    reproduction_status_path = tmp_path / "public_reproduction_status.json"
    grid_path = tmp_path / "tests/data/downscale/inputs/grid_char_weighted_scores.gpkg"
    regions_path = tmp_path / "tests/data/downscale/inputs/regions/eer_adp_zones.gpkg"
    total_config_path = tmp_path / "external-data/derived/eer/config_public_total_smoke.json"
    regional_config_path = tmp_path / "external-data/derived/eer/config_public_regional_smoke.json"
    total_output_path = tmp_path / "public_eer_total_downscaled.gpkg"
    regional_output_path = tmp_path / "public_eer_regional_downscaled.gpkg"
    feasible_land_path = bundle_dir / "public_report_feasible_land.gpkg"
    suitability_path = bundle_dir / "public_report_suitability_percentiles.gpkg"
    ranked_suitability_path = bundle_dir / "public_report_suitability_ranked_cells.csv"
    state_boundary_path = bundle_dir / "public_report_state_boundaries.gpkg"
    hosting_capacity_proxy_path = bundle_dir / "public_report_hosting_capacity_proxy.gpkg"
    zoning_proxy_path = bundle_dir / "public_report_zoning_proxy.gpkg"
    suitability_map_path = bundle_dir / "public_report_suitability_map.html"
    assumption_registry_path = bundle_dir / "public_report_assumption_registry.json"
    limitations_path = bundle_dir / "public_report_limitations.md"
    reeds_contract_path = bundle_dir / "public_report_reeds_integration_contract.json"

    grid_path.parent.mkdir(parents=True, exist_ok=True)
    regions_path.parent.mkdir(parents=True, exist_ok=True)
    total_config_path.parent.mkdir(parents=True, exist_ok=True)
    total_config_path.write_text(
        json.dumps(
            {
                "grid": "tests/data/downscale/inputs/grid_char_weighted_scores.gpkg",
                "grid_priority": "suitability_score",
                "grid_baseline_load": "dc_capacity_mw_existing",
                "grid_capacity": "developable_capacity_mw",
                "baseline_year": 2022,
                "projection_resolution": "total",
                "load_projections": "external-data/derived/eer/eer_public_central_high_data_center_national.csv",
                "load_value": "dc_load_mw",
                "load_year": "year",
                "max_site_addition_per_year": 1000,
                "site_saturation_limit": 0.5,
                "priority_power": 100,
                "n_bootstraps": 500,
                "random_seed": 0,
            },
            indent=2,
        )
    )
    regional_config_path.write_text(
        json.dumps(
            {
                "grid": "tests/data/downscale/inputs/grid_char_weighted_scores.gpkg",
                "grid_priority": "suitability_score",
                "grid_baseline_load": "dc_capacity_mw_existing",
                "grid_capacity": "developable_capacity_mw",
                "baseline_year": 2022,
                "projection_resolution": "regional",
                "load_projections": "external-data/derived/eer/eer_public_central_high_data_center_region_groups.csv",
                "load_value": "dc_load_mw",
                "load_year": "year",
                "regions": "tests/data/downscale/inputs/regions/eer_adp_zones.gpkg",
                "region_names": "zone_group",
                "load_regions": "zone_group",
                "max_site_addition_per_year": 1000,
                "site_saturation_limit": 0.5,
                "priority_power": 100,
                "n_bootstraps": 100,
                "random_seed": 0,
            },
            indent=2,
        )
    )
    gpd.GeoDataFrame(
        {
            "gid": [1, 2, 3, 4],
            "sc_point_gid": [1, 2, 3, 4],
            "latitude": [39.0, 39.5, 40.0, 40.5],
            "longitude": [-106.0, -105.5, -105.0, -104.5],
            "developable_capacity_mw": [0.0, 100.0, 50.0, 10.0],
            "suitability_score": [0.0, 0.2, 0.8, 0.5],
        },
        geometry=[
            box(-106.1, 38.9, -105.9, 39.1),
            box(-105.6, 39.4, -105.4, 39.6),
            box(-105.1, 39.9, -104.9, 40.1),
            box(-104.6, 40.4, -104.4, 40.6),
        ],
        crs="EPSG:4326",
    ).to_file(grid_path, driver="GPKG")

    gpd.GeoDataFrame(
        {
            "emm_zone": ["Rockies"],
            "zone_group": ["West"],
        },
        geometry=[box(-106.5, 38.5, -103.5, 41.5)],
        crs="EPSG:4326",
    ).to_file(regions_path, driver="GPKG")

    gpd.GeoDataFrame(
        {
            "gid": [10, 10, 10, 11, 11, 11],
            "sc_point_gid": [10, 10, 10, 11, 11, 11],
            "latitude": [40.0, 40.0, 40.0, 41.0, 41.0, 41.0],
            "longitude": [-105.0, -105.0, -105.0, -104.0, -104.0, -104.0],
            "dc_capacity_mw_existing": [3.6, 3.6, 3.6, 0.0, 0.0, 0.0],
            "developable_capacity_mw": [100.0, 100.0, 100.0, 80.0, 80.0, 80.0],
            "suitability_score": [0.8, 0.8, 0.8, 0.5, 0.5, 0.5],
            "new_dc_load_mw": [0.0, 2.0, 3.0, 1.0, 0.0, 4.0],
            "total_dc_load_mw": [3.6, 5.6, 8.6, 1.0, 1.0, 5.0],
            "year": [2022, 2030, 2035, 2022, 2030, 2035],
        },
        geometry=[
            box(-105.1, 39.9, -104.9, 40.1),
            box(-105.1, 39.9, -104.9, 40.1),
            box(-105.1, 39.9, -104.9, 40.1),
            box(-104.1, 40.9, -103.9, 41.1),
            box(-104.1, 40.9, -103.9, 41.1),
            box(-104.1, 40.9, -103.9, 41.1),
        ],
        crs="EPSG:4326",
    ).to_file(total_output_path, driver="GPKG")

    nlcd_target_path = tmp_path / "external-data/raw/nlcd/Annual_NLCD_LndCov_2023_CU_C1V0.tif"
    nlcd_target_path.parent.mkdir(parents=True, exist_ok=True)
    nlcd_data = np.full((14, 14), 81, dtype=np.uint8)
    nlcd_data[6:8, 6:8] = 22
    nlcd_data[1:3, 11:13] = 24
    with rasterio.open(
        nlcd_target_path,
        "w",
        driver="GTiff",
        height=nlcd_data.shape[0],
        width=nlcd_data.shape[1],
        count=1,
        dtype=nlcd_data.dtype,
        crs="EPSG:4326",
        transform=from_origin(-105.7, 40.7, 0.1, 0.1),
        nodata=0,
    ) as dataset:
        dataset.write(nlcd_data, 1)

    gpd.GeoDataFrame(
        {
            "gid": [20, 20, 20],
            "sc_point_gid": [20, 20, 20],
            "latitude": [39.0, 39.0, 39.0],
            "longitude": [-106.0, -106.0, -106.0],
            "dc_capacity_mw_existing": [2.0, 2.0, 2.0],
            "developable_capacity_mw": [90.0, 90.0, 90.0],
            "suitability_score": [0.7, 0.7, 0.7],
            "zone_group": ["Central", "Central", "Central"],
            "new_dc_load_mw": [0.0, 1.5, 0.5],
            "total_dc_load_mw": [2.0, 3.5, 4.0],
            "year": [2022, 2030, 2035],
        },
        geometry=[
            box(-106.1, 38.9, -105.9, 39.1),
            box(-106.1, 38.9, -105.9, 39.1),
            box(-106.1, 38.9, -105.9, 39.1),
        ],
        crs="EPSG:4326",
    ).to_file(regional_output_path, driver="GPKG")

    reproduction_status_path.write_text(
        json.dumps(
            {
                "workflow": "run-public-reproduction",
                "repo_root": tmp_path.as_posix(),
                "completed": True,
                "completed_steps": ["generate_eer_loads", "total_smoke", "regional_smoke"],
                "stopped_at_step": None,
                "step_results": {
                    "generate_eer_loads": [
                        (tmp_path / "national.csv").as_posix(),
                        (tmp_path / "regional.csv").as_posix(),
                        (tmp_path / "groups.csv").as_posix(),
                    ],
                    "total_smoke": {
                        "output_path": total_output_path.as_posix(),
                        "stdout": ["rows 10"],
                    },
                    "regional_smoke": {
                        "output_path": regional_output_path.as_posix(),
                        "stdout": ["rows 8"],
                    },
                },
            }
        )
    )

    def fake_run_public_reproduction(repo_root=".", status_path=None, resume=False, force=False):
        return reproduction_status_path

    def fake_load_public_report_state_boundaries(target_crs, cache_dir=None):
        boundaries = gpd.GeoDataFrame(
            {
                "state_name": ["State A", "State B"],
                "state_code": ["AA", "BB"],
            },
            geometry=[
                box(-106.2, 38.8, -105.3, 40.2),
                box(-105.3, 39.8, -103.8, 41.2),
            ],
            crs="EPSG:4326",
        )
        return boundaries.to_crs(target_crs) if target_crs is not None else boundaries

    monkeypatch.setattr("reVeal.public_data.run_public_reproduction_workflow", fake_run_public_reproduction)
    monkeypatch.setattr(
        "reVeal.public_data._load_public_report_state_boundaries",
        fake_load_public_report_state_boundaries,
    )

    output_dir = run_public_report_bundle(
        repo_root=tmp_path,
        output_dir=bundle_dir,
        force=True,
    )

    assert output_dir == bundle_dir
    manifest_path = bundle_dir / "public_report_bundle_manifest.json"
    deviation_path = bundle_dir / "public_report_bundle_deviations.md"
    status_path = bundle_dir / "public_report_bundle_status.json"
    total_cumulative_path = bundle_dir / "public_eer_total_downscaled_cumulative_buildout.gpkg"
    regional_cumulative_path = bundle_dir / "public_eer_regional_downscaled_cumulative_buildout.gpkg"
    summary_path = bundle_dir / "public_report_bundle_cumulative_buildout_summary.csv"

    assert manifest_path.exists()
    assert deviation_path.exists()
    assert status_path.exists()
    assert feasible_land_path.exists()
    assert suitability_path.exists()
    assert ranked_suitability_path.exists()
    assert state_boundary_path.exists()
    assert hosting_capacity_proxy_path.exists()
    assert zoning_proxy_path.exists()
    assert suitability_map_path.exists()
    assert assumption_registry_path.exists()
    assert limitations_path.exists()
    assert reeds_contract_path.exists()
    assert total_cumulative_path.exists()
    assert regional_cumulative_path.exists()
    assert summary_path.exists()

    manifest = json.loads(manifest_path.read_text())
    assert manifest["bundle_type"] == "bounded-public-report-bundle"
    assert manifest["reproduction_status_path"] == reproduction_status_path.as_posix()
    assert manifest["baseline_year"] == 2022
    assert manifest["report_baseline_year"] == 2025
    assert manifest["grid_priority"] == "suitability_score"
    assert total_output_path.as_posix() in manifest["output_paths"]
    assert feasible_land_path.as_posix() in manifest["output_paths"]
    assert suitability_path.as_posix() in manifest["output_paths"]
    assert ranked_suitability_path.as_posix() in manifest["output_paths"]
    assert state_boundary_path.as_posix() in manifest["output_paths"]
    assert hosting_capacity_proxy_path.as_posix() in manifest["output_paths"]
    assert zoning_proxy_path.as_posix() in manifest["output_paths"]
    assert suitability_map_path.as_posix() in manifest["output_paths"]
    assert assumption_registry_path.as_posix() in manifest["output_paths"]
    assert limitations_path.as_posix() in manifest["output_paths"]
    assert reeds_contract_path.as_posix() in manifest["output_paths"]
    assert total_cumulative_path.as_posix() in manifest["output_paths"]
    assert regional_cumulative_path.as_posix() in manifest["output_paths"]
    assert summary_path.as_posix() in manifest["output_paths"]

    assumption_registry = json.loads(assumption_registry_path.read_text())
    assert assumption_registry["registry_type"] == "bounded-public-report-assumption-registry"
    assert assumption_registry["scenario_name"] == "CENTRAL HIGH DATA CENTER"
    assert assumption_registry["bundle_label"] == "bounded-public-report-bundle"
    assert assumption_registry["report_reference"]["baseline_year"] == 2025
    assert assumption_registry["report_reference"]["utilization_factor"] == 0.88
    assert assumption_registry["current_bundle"]["baseline_year"] == 2022
    assert assumption_registry["current_bundle"]["feasible_land_rule"] == (
        "developable_capacity_mw > 0 and NLCD water/wetland share across classes 11, 90, and 95 < 0.5"
    )
    assert assumption_registry["current_bundle"]["suitability_percentile_rule"] == "percentile rank of suitability_score across feasible cells"
    assert assumption_registry["current_bundle"]["ranked_summary_rule"] == "sort by suitability_percentile desc, suitability_score desc, developable_capacity_mw desc, sc_point_gid asc"
    assert [item["projection_resolution"] for item in assumption_registry["scenario_inputs"]] == ["total", "regional"]
    assert assumption_registry["scenario_inputs"][0]["max_site_addition_per_year_mw"] == 1000
    assert assumption_registry["scenario_inputs"][1]["region_names"] == "zone_group"
    output_labels = {item["label"] for item in assumption_registry["output_labels"]}
    assert "public_report_feasible_land" in output_labels
    assert "public_report_suitability_ranked_cells" in output_labels
    assert "public_report_state_boundaries" in output_labels
    assert "public_report_hosting_capacity_proxy" in output_labels
    assert "public_report_zoning_proxy" in output_labels
    assert "public_report_suitability_map" in output_labels

    suitability_map_html = suitability_map_path.read_text()
    assert "https://d3js.org/d3.v7.min.js" in suitability_map_html
    assert "Bounded Public Suitability Map" in suitability_map_html
    assert "suitabilityGeoJson" in suitability_map_html
    assert "stateBoundaryGeoJson" in suitability_map_html
    assert "hostingProxyGeoJson" in suitability_map_html
    assert "zoningProxyGeoJson" in suitability_map_html
    assert "rankedRows" in suitability_map_html
    assert "data-cell-key" in suitability_map_html
    assert "setActiveCellKey" in suitability_map_html
    assert "projectedHexPath" in suitability_map_html
    assert "hexDisplayPath" in suitability_map_html
    assert "suitability-hex" in suitability_map_html
    assert "is-active" in suitability_map_html
    assert "row.cell_name" in suitability_map_html
    assert "state-boundary" in suitability_map_html
    assert "hosting-layer-toggle" in suitability_map_html
    assert "Hosting Capacity Proxy" in suitability_map_html
    assert "zoning-layer-toggle" in suitability_map_html
    assert "Zoning Proxy" in suitability_map_html
    assert "Cell ${{cellKeyFromObject(row)}}${{row.cell_name_basis" not in suitability_map_html
    assert "if (activeCellKey === normalizedKey)" in suitability_map_html
    assert '.on("mouseenter", (event, feature) => {' in suitability_map_html
    assert '.on("mousemove", (event) => {' in suitability_map_html
    assert '.attr("d", (feature) => hexDisplayPath(feature))' in suitability_map_html
    assert "stroke-width: 1.8;" in suitability_map_html
    assert "drop-shadow(0 0 3px rgba(196, 92, 19, 0.45))" in suitability_map_html
    gap_names = {item["name"] for item in assumption_registry["assumption_gaps"]}
    assert "report_reference_utilization_factor" in gap_names
    assert "report_reference_initial_locations" in gap_names
    limitation_names = {item["name"] for item in assumption_registry["limitation_carry_forward"]}
    assert "local_transmission_hosting_capacity" in limitation_names
    assert "demand_queue_times" in limitation_names
    assert "zoning_information" in limitation_names
    assert "social_acceptance" in limitation_names
    hosting_limit = next(
        item
        for item in assumption_registry["limitation_carry_forward"]
        if item["name"] == "local_transmission_hosting_capacity"
    )
    assert hosting_limit["status"] == "bounded proxy"
    zoning_limit = next(
        item
        for item in assumption_registry["limitation_carry_forward"]
        if item["name"] == "zoning_information"
    )
    assert zoning_limit["status"] == "bounded proxy"

    reeds_contract = json.loads(reeds_contract_path.read_text())
    assert reeds_contract["contract_type"] == "bounded-public-report-reeds-integration-contract"
    assert reeds_contract["integration_target"] == "ReEDS high-resolution load forecasting"
    assert reeds_contract["bundle_label"] == "bounded-public-report-bundle"
    assert reeds_contract["temporal_contract"]["current_bundle_baseline_year"] == 2022
    assert reeds_contract["temporal_contract"]["report_reference_baseline_year"] == 2025
    assert reeds_contract["temporal_contract"]["modeled_years"] == [2022, 2030, 2035]
    assert reeds_contract["spatial_contract"]["grid_cell_key"] == "sc_point_gid"
    assert reeds_contract["spatial_contract"]["report_reference_grid_resolution_km"] == 5.76
    handoff_labels = {item["label"] for item in reeds_contract["handoff_products"]}
    assert "public_eer_total_downscaled_cumulative_buildout" in handoff_labels
    assert "public_eer_regional_downscaled_cumulative_buildout" in handoff_labels
    assert "public_report_suitability_ranked_cells" in handoff_labels
    validation_names = {item["name"] for item in reeds_contract["validation_checks"]}
    assert "required_handoff_products_exist" in validation_names
    assert "temporal_year_alignment" in validation_names
    assert all(item["status"] == "passed" for item in reeds_contract["validation_checks"])

    limitations_text = limitations_path.read_text()
    assert "local transmission hosting capacity" in limitations_text.lower()
    assert "demand queue times" in limitations_text.lower()
    assert "zoning" in limitations_text.lower()
    assert "permitting and ordinance" in limitations_text.lower()

    zoning_proxy = gpd.read_file(zoning_proxy_path).sort_values("sc_point_gid").reset_index(drop=True)
    assert list(zoning_proxy["sc_point_gid"]) == [2, 3, 4]
    assert {
        "dominant_nlcd_class",
        "dominant_nlcd_label",
        "developed_share",
        "zoning_proxy_class",
        "zoning_proxy_note",
    }.issubset(zoning_proxy.columns)
    assert zoning_proxy["zoning_proxy_class"].tolist() == [
        "non_developed_context",
        "developed_neighborhood_context",
        "urban_core_context",
    ]
    assert "capacity scaling" in limitations_text.lower()
    assert "social acceptance" in limitations_text.lower()
    assert "not implemented" in limitations_text.lower()

    feasible_land = gpd.read_file(feasible_land_path).sort_values("sc_point_gid")
    assert feasible_land["sc_point_gid"].tolist() == [2, 3, 4]
    assert feasible_land["is_feasible_land"].tolist() == [True, True, True]
    assert "water_wetland_share" in feasible_land.columns
    assert "water_wetland_excluded" in feasible_land.columns
    assert feasible_land["water_wetland_excluded"].notna().all()
    assert feasible_land["water_wetland_excluded"].fillna(False).tolist() == [False, False, False]

    suitability = gpd.read_file(suitability_path).sort_values("sc_point_gid")
    assert suitability["sc_point_gid"].tolist() == [2, 3, 4]
    assert suitability["suitability_score"].tolist() == [0.2, 0.8, 0.5]
    assert suitability["suitability_percentile"].tolist() == [16.666667, 83.333333, 50.0]
    assert "cell_name" in suitability.columns
    assert "base_cell_name" in suitability.columns
    assert "cell_name_basis" in suitability.columns
    assert "cell_name_is_disambiguated" in suitability.columns
    assert "anchor_place_name" in suitability.columns
    assert "anchor_place_county" in suitability.columns
    assert "anchor_place_state" in suitability.columns
    assert "anchor_place_distance_miles" in suitability.columns
    assert "anchor_place_direction" in suitability.columns
    assert suitability["cell_name"].notna().all()
    assert suitability["cell_name"].is_unique
    assert not suitability["cell_name"].str.contains(r"\(Cell ", regex=True).any()

    ranked_suitability = pd.read_csv(ranked_suitability_path)
    assert ranked_suitability["national_rank"].tolist() == [1, 2, 3]
    assert ranked_suitability["sc_point_gid"].tolist() == [3, 4, 2]
    assert ranked_suitability["suitability_percentile"].tolist() == [83.333333, 50.0, 16.666667]
    assert "cell_name" in ranked_suitability.columns
    assert "base_cell_name" in ranked_suitability.columns
    assert "cell_name_basis" in ranked_suitability.columns
    assert "cell_name_is_disambiguated" in ranked_suitability.columns
    assert "anchor_place_name" in ranked_suitability.columns
    assert "anchor_place_county" in ranked_suitability.columns
    assert "anchor_place_state" in ranked_suitability.columns
    assert "anchor_place_distance_miles" in ranked_suitability.columns
    assert "anchor_place_direction" in ranked_suitability.columns
    assert "metro_feature_name" in ranked_suitability.columns
    assert "natural_feature_name" in ranked_suitability.columns
    assert ranked_suitability["cell_name"].notna().all()
    assert ranked_suitability["cell_name"].is_unique
    assert not ranked_suitability["cell_name"].str.contains(r"\(Cell ", regex=True).any()

    state_boundaries = gpd.read_file(state_boundary_path)
    assert state_boundaries["state_name"].tolist() == ["State A", "State B"]
    assert state_boundaries["state_code"].tolist() == ["AA", "BB"]

    hosting_capacity_proxy = gpd.read_file(hosting_capacity_proxy_path).sort_values("sc_point_gid")
    assert hosting_capacity_proxy["sc_point_gid"].tolist() == [2, 3, 4]
    assert "assessment_area" in hosting_capacity_proxy.columns
    assert "min_margin_headroom_2026_2030" in hosting_capacity_proxy.columns
    assert "hosting_capacity_proxy_class" in hosting_capacity_proxy.columns
    assert "hosting_capacity_proxy_note" in hosting_capacity_proxy.columns
    assert hosting_capacity_proxy["assessment_area"].notna().all()
    assert hosting_capacity_proxy["hosting_capacity_proxy_class"].notna().all()

    total_cumulative = gpd.read_file(total_cumulative_path).sort_values(["sc_point_gid", "year"])
    total_rows = total_cumulative[total_cumulative["sc_point_gid"] == 10]
    assert total_rows["baseline_total_dc_load_mw"].tolist() == [3.6, 3.6, 3.6]
    assert total_rows["cumulative_new_dc_load_mw"].tolist() == [0.0, 2.0, 5.0]
    assert total_rows["cumulative_total_dc_load_mw"].tolist() == [3.6, 5.6, 8.6]

    summary = pd.read_csv(summary_path)
    summary = summary.sort_values(["source_output_name", "year"])
    total_summary = summary[summary["source_output_name"] == "public_eer_total_downscaled"]
    assert total_summary["year"].tolist() == [2022, 2030, 2035]
    assert total_summary["cumulative_total_dc_load_mw"].tolist() == [4.6, 6.6, 13.6]

    deviation_text = deviation_path.read_text()
    assert "baseline year" in deviation_text.lower()
    assert "2022" in deviation_text
    assert "2025" in deviation_text
    assert "Baxtel-trained" in deviation_text
    assert "developable_capacity_mw > 0" in deviation_text
    assert "11`, `90`, and `95`" in deviation_text
    assert "0.5" in deviation_text
    assert "suitability_score" in deviation_text

    progress_text = capsys.readouterr().err
    assert "Completed run-public-report-bundle" in progress_text


def test_main_runs_public_report_bundle_command(tmp_path, monkeypatch, capsys):
    """The CLI should expose the public report-bundle runner."""

    output_dir = tmp_path / "report-bundle"

    def fake_run_public_report_bundle(
        repo_root=".",
        output_dir=None,
        status_path=None,
        reproduction_status_path=None,
        resume=False,
        force=False,
    ):
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    monkeypatch.setattr("reVeal.public_data.run_public_report_bundle", fake_run_public_report_bundle)

    exit_code = main(
        [
            "run-public-report-bundle",
            "--repo-root",
            tmp_path.as_posix(),
            "--output-dir",
            output_dir.as_posix(),
            "--force",
        ]
    )

    assert exit_code == 0
    assert output_dir.as_posix() in capsys.readouterr().out


def test_build_osm_fiber_line_frame_filters_route_like_features():
    """The fiber proxy should only keep route-like telecom or fiber OSM linework."""

    elements = [
        {
            "type": "way",
            "id": 501,
            "geometry": [
                {"lat": 39.700, "lon": -104.990},
                {"lat": 39.705, "lon": -104.970},
            ],
            "tags": {
                "name": "Metro Fiber Route",
                "operator": "Example Fiber",
                "man_made": "communications_line",
                "communication:fibre": "yes",
            },
        },
        {
            "type": "way",
            "id": 502,
            "geometry": [
                {"lat": 32.770, "lon": -96.800},
                {"lat": 32.780, "lon": -96.780},
            ],
            "tags": {
                "name": "Backbone Segment",
                "telecom": "line",
                "cable": "fibre_optic",
            },
        },
        {
            "type": "way",
            "id": 503,
            "geometry": [
                {"lat": 35.200, "lon": -97.500},
                {"lat": 35.220, "lon": -97.470},
            ],
            "tags": {
                "name": "Power Corridor",
                "power": "line",
            },
        },
    ]

    fiber_df = build_osm_fiber_line_frame(elements)

    assert list(fiber_df["source_id"]) == ["osm:way/501", "osm:way/502"]
    assert set(fiber_df["operator"].fillna("")) == {"Example Fiber", ""}


def test_generate_public_fiber_proxy_rasters_writes_expected_proxy_outputs(tmp_path):
    """The fiber proxy workflow should emit the route proxy and aligned raster layers."""

    line_payload_path = tmp_path / "osm_fiber_lines.json"
    availability_path = tmp_path / "fcc_bdc_fiber_availability.gpkg"
    template_raster_path = tmp_path / "template.tif"

    line_payload_path.write_text(
        json.dumps(
            {
                "elements": [
                    {
                        "type": "way",
                        "id": 501,
                        "geometry": [
                            {"lat": 39.700, "lon": -104.990},
                            {"lat": 39.705, "lon": -104.970},
                        ],
                        "tags": {
                            "name": "Metro Fiber Route",
                            "man_made": "communications_line",
                            "communication:fibre": "yes",
                        },
                    }
                ]
            }
        )
    )

    availability_gdf = gpd.GeoDataFrame(
        {"technology": ["Fiber to the Premises"]},
        geometry=[box(-105.0, 39.69, -104.96, 39.71)],
        crs="EPSG:4326",
    )
    availability_gdf.to_file(availability_path, driver="GPKG")

    with rasterio.open(
        template_raster_path,
        "w",
        driver="GTiff",
        height=5,
        width=5,
        count=1,
        dtype="uint8",
        crs="EPSG:4326",
        transform=from_origin(-105.0, 39.71, 0.01, 0.01),
        nodata=0,
    ) as dst:
        dst.write(np.zeros((1, 5, 5), dtype=np.uint8))

    line_vector_path, proximity_raster_path, availability_raster_path = (
        generate_public_fiber_proxy_rasters(
            line_payload_path,
            availability_path,
            template_raster_path,
            tmp_path,
        )
    )

    assert line_vector_path == tmp_path / "public_fiber_route_proxy.gpkg"
    assert proximity_raster_path == tmp_path / "fiber_lines_onshore_proximity.tif"
    assert availability_raster_path == tmp_path / "fiber_availability_binary.tif"
    assert line_vector_path.exists()
    assert proximity_raster_path.exists()
    assert availability_raster_path.exists()

    line_df = gpd.read_file(line_vector_path)
    assert list(line_df["source_id"]) == ["osm:way/501"]

    with rasterio.open(proximity_raster_path) as src:
        proximity = src.read(1)
        assert proximity.shape == (5, 5)
        assert float(proximity.min()) == pytest.approx(0.0)
        assert float(proximity.max()) > 0.0

    with rasterio.open(availability_raster_path) as src:
        availability = src.read(1)
        assert availability.shape == (5, 5)
        assert set(np.unique(availability)).issubset({0, 1})
        assert int(availability.max()) == 1
        assert int(availability.sum()) > 0


def test_stage_public_dataset_gas_workflow_creates_note_file(tmp_path):
    """The gas service territory workflow should have a repo-local manifest note."""

    output_path = stage_public_dataset(
        "state_gas_service_territory_manifest",
        repo_root=tmp_path,
    )
    text = output_path.read_text()

    assert output_path == tmp_path / "external-data/raw/gas/state_gas_service_territories_MANIFEST_SCHEMA.txt"
    assert "state_gas_service_territories.csv" in text


def test_build_state_gas_service_territory_frame_merges_state_extracts(tmp_path):
    """The state-by-state gas workflow should normalize multiple utility extracts."""

    texas_path = tmp_path / "texas_gas.gpkg"
    oklahoma_path = tmp_path / "oklahoma_gas.gpkg"
    manifest_path = tmp_path / "state_gas_service_territories.csv"

    gpd.GeoDataFrame(
        {"utility_name": ["Lone Star Gas"]},
        geometry=[box(-97.0, 31.0, -96.5, 31.5)],
        crs="EPSG:4326",
    ).to_file(texas_path, driver="GPKG")
    gpd.GeoDataFrame(
        {"provider": ["Sooner Gas"]},
        geometry=[box(-97.5, 35.4, -97.0, 35.8)],
        crs="EPSG:4326",
    ).to_file(oklahoma_path, driver="GPKG")

    pd.DataFrame(
        [
            {
                "state": "TX",
                "path": texas_path.as_posix(),
                "utility_field": "utility_name",
            },
            {
                "state": "OK",
                "path": oklahoma_path.as_posix(),
                "utility_field": "provider",
            },
        ]
    ).to_csv(manifest_path, index=False)

    territory_df = build_state_gas_service_territory_frame(manifest_path)

    assert set(territory_df["state"]) == {"TX", "OK"}
    assert set(territory_df["utility_name"]) == {"Lone Star Gas", "Sooner Gas"}
    assert territory_df["territory_id"].str.startswith("gas_").all()


def test_generate_public_gas_service_territory_baseline_writes_assembled_layer(tmp_path):
    """The gas workflow should write the merged territory layer and a state index CSV."""

    texas_path = tmp_path / "texas_gas.gpkg"
    manifest_path = tmp_path / "state_gas_service_territories.csv"

    gpd.GeoDataFrame(
        {"utility_name": ["Lone Star Gas"]},
        geometry=[box(-97.0, 31.0, -96.5, 31.5)],
        crs="EPSG:4326",
    ).to_file(texas_path, driver="GPKG")
    pd.DataFrame(
        [
            {
                "state": "TX",
                "path": texas_path.as_posix(),
                "utility_field": "utility_name",
            }
        ]
    ).to_csv(manifest_path, index=False)

    gpkg_path, summary_csv_path = generate_public_gas_service_territory_baseline(
        manifest_path,
        tmp_path,
    )

    assert gpkg_path == tmp_path / "public_gas_service_territories.gpkg"
    assert summary_csv_path == tmp_path / "public_gas_service_territories_state_index.csv"
    assert gpkg_path.exists()
    assert summary_csv_path.exists()

    territory_df = gpd.read_file(gpkg_path)
    summary_df = pd.read_csv(summary_csv_path)

    assert list(territory_df["utility_name"]) == ["Lone Star Gas"]
    assert list(summary_df["state"]) == ["TX"]
    assert int(summary_df["territory_count"].iloc[0]) == 1


def test_stage_public_dataset_water_workflow_creates_note_file(tmp_path):
    """The water proxy workflow should have a repo-local input-schema note."""

    output_path = stage_public_dataset("usgs_state_water_use_proxy_csv", repo_root=tmp_path)
    text = output_path.read_text()

    assert output_path == tmp_path / "external-data/raw/water/usgs_state_water_use_proxy_SCHEMA.txt"
    assert "usgs_state_water_use_proxy.csv" in text


def test_build_state_water_availability_proxy_tables_apportions_state_values_to_zones():
    """State water proxy values should apportion cleanly into zones and zone groups."""

    state_zone_weights = pd.DataFrame(
        [
            {"state": "alpha", "zone": "north", "zone_group": "east", "weight": 0.75},
            {"state": "alpha", "zone": "south", "zone_group": "west", "weight": 0.25},
            {"state": "beta", "zone": "south", "zone_group": "west", "weight": 1.0},
        ]
    )
    state_proxy_df = pd.DataFrame(
        [
            {"state": "alpha", "freshwater_withdrawal_mgd": 100.0},
            {"state": "beta", "freshwater_withdrawal_mgd": 150.0},
        ]
    )

    zonal_df, grouped_df = build_state_water_availability_proxy_tables(
        state_proxy_df,
        state_zone_weights,
    )

    assert zonal_df.to_dict("records") == [
        {"zone": "north", "water_availability_proxy_mgd": pytest.approx(75.0)},
        {"zone": "south", "water_availability_proxy_mgd": pytest.approx(175.0)},
    ]
    assert grouped_df.to_dict("records") == [
        {"zone_group": "east", "water_availability_proxy_mgd": pytest.approx(75.0)},
        {"zone_group": "west", "water_availability_proxy_mgd": pytest.approx(175.0)},
    ]


def test_generate_public_water_availability_proxy_features_writes_state_and_zone_outputs(
    tmp_path, data_dir
):
    """The water proxy workflow should write a cleaned state CSV and a zonal GeoPackage."""

    workbook_path = tmp_path / "minimal.xlsx"
    _write_minimal_xlsx(workbook_path)

    state_proxy_csv_path = tmp_path / "usgs_state_water_use_proxy.csv"
    pd.DataFrame(
        [
            {"state": "alpha", "freshwater_withdrawal_mgd": 120.0},
        ]
    ).to_csv(state_proxy_csv_path, index=False)

    zone_gpkg_path = tmp_path / "zones.gpkg"
    gpd.GeoDataFrame(
        {"emm_zone": ["North"], "zone_group": ["East"]},
        geometry=[box(-100.0, 30.0, -99.0, 31.0)],
        crs="EPSG:4326",
    ).to_file(zone_gpkg_path, driver="GPKG")

    state_output_path, zone_output_path = generate_public_water_availability_proxy_features(
        state_proxy_csv_path,
        workbook_path,
        zone_gpkg_path,
        tmp_path,
    )

    assert state_output_path == tmp_path / "public_water_availability_state_proxy.csv"
    assert zone_output_path == tmp_path / "public_water_availability_emm_zone.gpkg"
    assert state_output_path.exists()
    assert zone_output_path.exists()

    state_df = pd.read_csv(state_output_path)
    zone_df = gpd.read_file(zone_output_path)

    assert list(state_df["state"]) == ["alpha"]
    assert state_df["freshwater_withdrawal_mgd"].iloc[0] == pytest.approx(120.0)
    assert list(zone_df["emm_zone"]) == ["North"]
    assert zone_df["water_availability_proxy_mgd"].iloc[0] == pytest.approx(120.0)


def test_stage_public_dataset_land_value_workflow_creates_note_file(tmp_path):
    """The land-value proxy workflow should have a repo-local input-schema note."""

    output_path = stage_public_dataset("county_land_value_proxy_inputs", repo_root=tmp_path)
    text = output_path.read_text()

    assert output_path == tmp_path / "external-data/raw/land/county_land_value_proxy_INPUTS.txt"
    assert "county_land_value_proxy.csv" in text
    assert "county_land_value_counties.gpkg" in text


def test_build_county_land_value_proxy_frame_computes_state_relative_index(tmp_path):
    """County land-value proxies should retain raw values and add state-relative ranking."""

    county_path = tmp_path / "counties.gpkg"
    county_gdf = gpd.GeoDataFrame(
        {
            "county_id": ["001", "003", "005"],
            "state": ["TX", "TX", "OK"],
        },
        geometry=[
            box(-100.0, 30.0, -99.5, 30.5),
            box(-99.5, 30.0, -99.0, 30.5),
            box(-98.0, 35.0, -97.5, 35.5),
        ],
        crs="EPSG:4326",
    )
    county_gdf.to_file(county_path, driver="GPKG")

    county_proxy_df = pd.DataFrame(
        [
            {"county_id": "001", "state": "TX", "land_value_proxy_usd_per_acre": 1000.0},
            {"county_id": "003", "state": "TX", "land_value_proxy_usd_per_acre": 3000.0},
            {"county_id": "005", "state": "OK", "land_value_proxy_usd_per_acre": 500.0},
        ]
    )

    county_feature_df = build_county_land_value_proxy_frame(county_proxy_df, county_path)

    texas_low = county_feature_df.loc[county_feature_df["county_id"] == "001"].iloc[0]
    texas_high = county_feature_df.loc[county_feature_df["county_id"] == "003"].iloc[0]
    oklahoma = county_feature_df.loc[county_feature_df["county_id"] == "005"].iloc[0]

    assert texas_low["land_value_proxy_usd_per_acre"] == pytest.approx(1000.0)
    assert texas_high["land_value_proxy_usd_per_acre"] == pytest.approx(3000.0)
    assert texas_low["state_land_value_index"] < texas_high["state_land_value_index"]
    assert oklahoma["state_land_value_index"] == pytest.approx(0.5)


def test_generate_public_land_value_proxy_features_writes_county_and_zone_outputs(tmp_path):
    """The land-value workflow should write county and zonal proxy outputs."""

    county_path = tmp_path / "counties.gpkg"
    zone_path = tmp_path / "zones.gpkg"
    proxy_csv_path = tmp_path / "county_land_value_proxy.csv"

    gpd.GeoDataFrame(
        {
            "county_id": ["001", "003"],
            "state": ["TX", "TX"],
        },
        geometry=[
            box(-100.0, 30.0, -99.5, 30.5),
            box(-99.5, 30.0, -99.0, 30.5),
        ],
        crs="EPSG:4326",
    ).to_file(county_path, driver="GPKG")
    gpd.GeoDataFrame(
        {"emm_zone": ["South"], "zone_group": ["West"]},
        geometry=[box(-100.0, 30.0, -99.0, 30.5)],
        crs="EPSG:4326",
    ).to_file(zone_path, driver="GPKG")
    pd.DataFrame(
        [
            {"county_id": "001", "state": "TX", "land_value_proxy_usd_per_acre": 1000.0},
            {"county_id": "003", "state": "TX", "land_value_proxy_usd_per_acre": 3000.0},
        ]
    ).to_csv(proxy_csv_path, index=False)

    county_output_path, zone_output_path = generate_public_land_value_proxy_features(
        proxy_csv_path,
        county_path,
        zone_path,
        tmp_path,
    )

    assert county_output_path == tmp_path / "public_land_value_county.gpkg"
    assert zone_output_path == tmp_path / "public_land_value_emm_zone.gpkg"
    assert county_output_path.exists()
    assert zone_output_path.exists()

    county_df = gpd.read_file(county_output_path)
    zone_df = gpd.read_file(zone_output_path)

    assert set(county_df["county_id"]) == {"001", "003"}
    assert "state_land_value_index" in county_df.columns
    assert list(zone_df["emm_zone"]) == ["South"]
    assert zone_df["land_value_proxy_usd_per_acre"].iloc[0] == pytest.approx(2000.0)


def test_stage_public_dataset_construction_cost_workflow_creates_note_file(tmp_path):
    """The construction-cost proxy workflow should have a repo-local input-schema note."""

    output_path = stage_public_dataset(
        "county_construction_cost_proxy_inputs",
        repo_root=tmp_path,
    )
    text = output_path.read_text()

    assert (
        output_path
        == tmp_path / "external-data/raw/construction/county_construction_cost_proxy_INPUTS.txt"
    )
    assert "county_construction_cost_proxy.csv" in text
    assert "county_construction_cost_counties.gpkg" in text


def test_build_county_construction_cost_proxy_frame_computes_proxy_and_relative_index(
    tmp_path,
):
    """County construction-cost proxies should derive a cost score and national-relative index."""

    county_path = tmp_path / "construction_counties.gpkg"
    gpd.GeoDataFrame(
        {
            "county_id": ["001", "003"],
            "state": ["TX", "OK"],
        },
        geometry=[
            box(-100.0, 30.0, -99.5, 30.5),
            box(-99.5, 30.0, -99.0, 30.5),
        ],
        crs="EPSG:4326",
    ).to_file(county_path, driver="GPKG")

    county_proxy_df = pd.DataFrame(
        [
            {
                "county_id": "001",
                "state": "TX",
                "construction_worker_mean_wage_usd": 30.0,
                "regional_price_parity_index": 110.0,
            },
            {
                "county_id": "003",
                "state": "OK",
                "construction_worker_mean_wage_usd": 20.0,
                "regional_price_parity_index": 90.0,
            },
        ]
    )

    county_feature_df = build_county_construction_cost_proxy_frame(
        county_proxy_df,
        county_path,
    )

    county_one = county_feature_df.loc[county_feature_df["county_id"] == "001"].iloc[0]
    county_two = county_feature_df.loc[county_feature_df["county_id"] == "003"].iloc[0]

    assert county_one["construction_cost_proxy_score"] == pytest.approx(33.0)
    assert county_two["construction_cost_proxy_score"] == pytest.approx(18.0)
    assert county_one["construction_cost_relative_index"] == pytest.approx(33.0 / 25.5)
    assert county_two["construction_cost_relative_index"] == pytest.approx(18.0 / 25.5)


def test_generate_public_construction_cost_proxy_features_writes_county_and_zone_outputs(
    tmp_path,
):
    """The construction-cost workflow should write county and zonal proxy outputs."""

    county_path = tmp_path / "construction_counties.gpkg"
    zone_path = tmp_path / "zones.gpkg"
    proxy_csv_path = tmp_path / "county_construction_cost_proxy.csv"

    gpd.GeoDataFrame(
        {
            "county_id": ["001", "003"],
            "state": ["TX", "OK"],
        },
        geometry=[
            box(-100.0, 30.0, -99.5, 30.5),
            box(-99.5, 30.0, -99.0, 30.5),
        ],
        crs="EPSG:4326",
    ).to_file(county_path, driver="GPKG")
    gpd.GeoDataFrame(
        {"emm_zone": ["South"], "zone_group": ["West"]},
        geometry=[box(-100.0, 30.0, -99.0, 30.5)],
        crs="EPSG:4326",
    ).to_file(zone_path, driver="GPKG")
    pd.DataFrame(
        [
            {
                "county_id": "001",
                "state": "TX",
                "construction_worker_mean_wage_usd": 30.0,
                "regional_price_parity_index": 110.0,
            },
            {
                "county_id": "003",
                "state": "OK",
                "construction_worker_mean_wage_usd": 20.0,
                "regional_price_parity_index": 90.0,
            },
        ]
    ).to_csv(proxy_csv_path, index=False)

    county_output_path, zone_output_path = generate_public_construction_cost_proxy_features(
        proxy_csv_path,
        county_path,
        zone_path,
        tmp_path,
    )

    assert county_output_path == tmp_path / "public_construction_cost_county.gpkg"
    assert zone_output_path == tmp_path / "public_construction_cost_emm_zone.gpkg"
    assert county_output_path.exists()
    assert zone_output_path.exists()

    county_df = gpd.read_file(county_output_path)
    zone_df = gpd.read_file(zone_output_path)

    assert set(county_df["county_id"]) == {"001", "003"}
    assert "construction_cost_proxy_score" in county_df.columns
    assert "construction_cost_relative_index" in county_df.columns
    assert list(zone_df["emm_zone"]) == ["South"]
    assert zone_df["construction_cost_proxy_score"].iloc[0] == pytest.approx(25.5)
    assert zone_df["construction_cost_relative_index"].iloc[0] == pytest.approx(1.0)