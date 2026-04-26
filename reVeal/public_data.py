# -*- coding: utf-8 -*-
"""
Utilities for sourcing and transforming public data artifacts used with reVeal.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
import argparse
import json
import math
import re
import shutil
import subprocess
import sys
from typing import Callable
from urllib.parse import parse_qs, quote, urlencode, urlparse
import urllib.error
import urllib.request
import zipfile
import xml.etree.ElementTree as ET

import geopandas as gpd
import numpy as np
import pandas as pd
from osgeo import gdal
import rasterio
from rasterio.io import MemoryFile
from rasterio.features import rasterize
from rasterio.mask import mask as raster_mask
from rasterio.transform import from_origin
from shapely.geometry import LineString, Point, box


EER_PUBLIC_SCENARIO = "CENTRAL HIGH DATA CENTER"
EER_PUBLIC_SUBSECTORS = ("data center cooling", "data center it")
EER_PUBLIC_YEARS = (2024, 2030, 2035, 2040, 2045, 2050)
PUBLIC_REPORT_BUNDLE_GRID_PATH = "tests/data/downscale/inputs/grid_char_weighted_scores.gpkg"
PUBLIC_REPORT_BUNDLE_GRID_PRIORITY = "suitability_score"
PUBLIC_REPORT_BUNDLE_BASELINE_YEAR = 2022
PUBLIC_REPORT_BUNDLE_REPORT_BASELINE_YEAR = 2025
PUBLIC_REPORT_REFERENCE_TERMINAL_YEAR = 2050
PUBLIC_REPORT_REFERENCE_MODELED_YEARS = (
    PUBLIC_REPORT_BUNDLE_REPORT_BASELINE_YEAR,
    2030,
    2035,
    2040,
    2045,
    PUBLIC_REPORT_REFERENCE_TERMINAL_YEAR,
)
PUBLIC_REPORT_REFERENCE_BUILDOUT_HORIZON_YEARS = (
    PUBLIC_REPORT_REFERENCE_TERMINAL_YEAR - PUBLIC_REPORT_BUNDLE_REPORT_BASELINE_YEAR
)
PUBLIC_REPORT_BUNDLE_TOTAL_CONFIG_PATH = "external-data/derived/eer/config_public_total_smoke.json"
PUBLIC_REPORT_BUNDLE_REGIONAL_CONFIG_PATH = "external-data/derived/eer/config_public_regional_smoke.json"
PUBLIC_REPORT_BAXTEL_SCHEMA_PATH = "external-data/raw/data-centers/baxtel_data_center_sites.csv"
PUBLIC_REPORT_PUBLIC_DATA_CENTER_BASELINE_PATH = "external-data/derived/data-centers/public_data_center_baseline.csv"
PUBLIC_REPORT_BAXTEL_REQUIRED_TRAINING_FIELDS = (
    "name",
    "latitude",
    "longitude",
    "site_status",
)
PUBLIC_REPORT_BAXTEL_DESIRED_CONTEXT_FIELDS = (
    "operator",
    "source_url",
    "source_note",
)
PUBLIC_REPORT_REFERENCE_GRID_RESOLUTION_KM = 5.76
PUBLIC_REPORT_LINKEDIN_AGGREGATION_GRID_RESOLUTION_KM = 5.0
PUBLIC_REPORT_GRID_MEASUREMENT_CRS = "EPSG:5070"
PUBLIC_REPORT_GRID_RESOLUTION_TOLERANCE_KM = 0.1
PUBLIC_REPORT_REFERENCE_UTILIZATION_FACTOR = 0.88
PUBLIC_REPORT_REFERENCE_MAX_SITE_ADDITION_PER_TIME_STEP_MW = 1000
PUBLIC_REPORT_REFERENCE_INITIAL_LOCATIONS = "Baxtel 2025 operating data centers"
PUBLIC_REPORT_STATE_BOUNDARY_SOURCE_URL = (
    "https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_state_20m.zip"
)
PUBLIC_REPORT_CENSUS_GEOLOOKUP_URL = (
    "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
)
PUBLIC_REPORT_CENSUS_GEOLOOKUP_BENCHMARK = "Public_AR_Current"
PUBLIC_REPORT_CENSUS_GEOLOOKUP_VINTAGE = "Current_Current"
PUBLIC_REPORT_CENSUS_GEOLOOKUP_LAYERS = (
    "States",
    "Counties",
    "County Subdivisions",
    "Census Designated Places",
    "Incorporated Places",
    "Metropolitan Statistical Areas",
    "Combined Statistical Areas",
    "Urban Areas",
    "Census Regions",
    "Census Divisions",
    "Census Tracts",
    "2020 Census Blocks",
)
PUBLIC_REPORT_CENSUS_MISS_NEAR_STATE_DISTANCE_MILES = 25.0
PUBLIC_REPORT_CENSUS_MISS_LOCAL_ANCHOR_DISTANCE_MILES = 75.0
PUBLIC_REPORT_CENSUS_MISS_HIGH_IMPACT_PERCENTILE = 90.0
PUBLIC_REPORT_CENSUS_MISS_MEDIUM_IMPACT_PERCENTILE = 50.0
PUBLIC_NLCD_REPRESENTATIVE_BASENAME = "Annual_NLCD_LndCov_2023_CU_C1V0"
PUBLIC_NLCD_REPRESENTATIVE_ZIP_NAME = f"{PUBLIC_NLCD_REPRESENTATIVE_BASENAME}.zip"
PUBLIC_NLCD_REPRESENTATIVE_TIF_NAME = f"{PUBLIC_NLCD_REPRESENTATIVE_BASENAME}.tif"
PUBLIC_NLCD_WMS_BASE_URL = (
    "https://dmsdata.cr.usgs.gov/geoserver/mrlc_Land-Cover-Native_conus_year_data/wms"
)
PUBLIC_NLCD_WMS_LAYER = "Land-Cover-Native_conus_year_data"
PUBLIC_NLCD_WMS_TIME = "2023-01-01T00:00:00.000Z"
PUBLIC_NLCD_WMS_CRS = "EPSG:5070"
PUBLIC_NLCD_WMS_FALLBACK_RESOLUTION_M = 1000.0
PUBLIC_NLCD_WMS_FALLBACK_TILE_COLUMNS = 2
PUBLIC_NLCD_WMS_FALLBACK_TILE_ROWS = 2
PUBLIC_NLCD_WMS_INDEX_TO_CLASS = {
    0: 0,
    1: 11,
    2: 12,
    3: 21,
    4: 22,
    5: 23,
    6: 24,
    7: 31,
    8: 41,
    9: 42,
    10: 43,
    11: 52,
    12: 71,
    13: 81,
    14: 82,
    15: 90,
    16: 95,
}
PUBLIC_REPORT_CELL_NAME_POPULARITY_RULE = (
    "Build a bounded offline geographic identity stack for each cell. Local labels use the most specific available "
    "culturally meaningful layer; general-audience labels use the smallest broadly recognizable layer, moving up to "
    "state or region when the nearest metro/city is too distant."
)
PUBLIC_REPORT_GENERAL_METRO_RADIUS_MILES = 125.0
PUBLIC_REPORT_LANDMARK_RADIUS_MILES = 50.0
PUBLIC_REPORT_STATE_NAME_BY_CODE = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
    "DC": "District of Columbia",
}
PUBLIC_REPORT_NATIONAL_REGION_BY_STATE = {
    "CA": "West Coast",
    "OR": "West Coast",
    "WA": "West Coast",
    "AZ": "Southwest",
    "NM": "Southwest",
    "NV": "Southwest",
    "UT": "Mountain West",
    "CO": "Mountain West",
    "ID": "Mountain West",
    "MT": "Mountain West",
    "WY": "Mountain West",
    "TX": "South Central United States",
    "OK": "South Central United States",
    "AR": "South Central United States",
    "LA": "Gulf Coast",
    "MS": "Gulf Coast",
    "AL": "Gulf Coast",
    "FL": "Southeast",
    "GA": "Southeast",
    "SC": "Southeast",
    "NC": "Southeast",
    "TN": "Southeast",
    "KY": "Southeast",
    "VA": "Mid-Atlantic",
    "WV": "Appalachia",
    "MD": "Mid-Atlantic",
    "DE": "Mid-Atlantic",
    "DC": "Mid-Atlantic",
    "PA": "Mid-Atlantic",
    "NJ": "Mid-Atlantic",
    "NY": "Northeast",
    "CT": "Northeast",
    "RI": "Northeast",
    "MA": "Northeast",
    "VT": "Northeast",
    "NH": "Northeast",
    "ME": "Northeast",
    "OH": "Midwest",
    "MI": "Midwest",
    "IN": "Midwest",
    "IL": "Midwest",
    "WI": "Midwest",
    "MN": "Midwest",
    "IA": "Midwest",
    "MO": "Midwest",
    "KS": "Great Plains",
    "NE": "Great Plains",
    "SD": "Great Plains",
    "ND": "Great Plains",
}
PUBLIC_REPORT_CELL_NAME_CATALOG = (
    {"name": "New York City", "kind": "metro", "latitude": 40.7128, "longitude": -74.0060, "popularity_score": 100.0},
    {"name": "Los Angeles", "kind": "metro", "latitude": 34.0522, "longitude": -118.2437, "popularity_score": 98.0},
    {"name": "Chicago", "kind": "metro", "latitude": 41.8781, "longitude": -87.6298, "popularity_score": 95.0},
    {"name": "Dallas-Fort Worth", "kind": "metro", "latitude": 32.7767, "longitude": -96.7970, "popularity_score": 91.0},
    {"name": "Houston", "kind": "metro", "latitude": 29.7604, "longitude": -95.3698, "popularity_score": 90.0},
    {"name": "Washington, DC", "kind": "metro", "latitude": 38.9072, "longitude": -77.0369, "popularity_score": 88.0},
    {"name": "Atlanta", "kind": "metro", "latitude": 33.7490, "longitude": -84.3880, "popularity_score": 87.0},
    {"name": "Miami", "kind": "metro", "latitude": 25.7617, "longitude": -80.1918, "popularity_score": 86.0},
    {"name": "Phoenix", "kind": "metro", "latitude": 33.4484, "longitude": -112.0740, "popularity_score": 85.0},
    {"name": "Boston", "kind": "metro", "latitude": 42.3601, "longitude": -71.0589, "popularity_score": 84.0},
    {"name": "San Francisco Bay Area", "kind": "metro", "latitude": 37.7749, "longitude": -122.4194, "popularity_score": 83.0},
    {"name": "Seattle", "kind": "metro", "latitude": 47.6062, "longitude": -122.3321, "popularity_score": 82.0},
    {"name": "Denver", "kind": "metro", "latitude": 39.7392, "longitude": -104.9903, "popularity_score": 81.0},
    {"name": "Minneapolis-Saint Paul", "kind": "metro", "latitude": 44.9778, "longitude": -93.2650, "popularity_score": 80.0},
    {"name": "Detroit", "kind": "metro", "latitude": 42.3314, "longitude": -83.0458, "popularity_score": 79.0},
    {"name": "San Diego", "kind": "metro", "latitude": 32.7157, "longitude": -117.1611, "popularity_score": 78.0},
    {"name": "Tampa Bay", "kind": "metro", "latitude": 27.9506, "longitude": -82.4572, "popularity_score": 77.0},
    {"name": "Orlando", "kind": "metro", "latitude": 28.5383, "longitude": -81.3792, "popularity_score": 76.0},
    {"name": "Charlotte", "kind": "metro", "latitude": 35.2271, "longitude": -80.8431, "popularity_score": 75.0},
    {"name": "Las Vegas", "kind": "metro", "latitude": 36.1699, "longitude": -115.1398, "popularity_score": 74.0},
    {"name": "Salt Lake City", "kind": "metro", "latitude": 40.7608, "longitude": -111.8910, "popularity_score": 73.0},
    {"name": "Portland", "kind": "metro", "latitude": 45.5152, "longitude": -122.6784, "popularity_score": 72.0},
    {"name": "Austin", "kind": "metro", "latitude": 30.2672, "longitude": -97.7431, "popularity_score": 71.0},
    {"name": "San Antonio", "kind": "metro", "latitude": 29.4241, "longitude": -98.4936, "popularity_score": 70.0},
    {"name": "Nashville", "kind": "metro", "latitude": 36.1627, "longitude": -86.7816, "popularity_score": 69.0},
    {"name": "St. Louis", "kind": "metro", "latitude": 38.6270, "longitude": -90.1994, "popularity_score": 68.0},
    {"name": "Kansas City", "kind": "metro", "latitude": 39.0997, "longitude": -94.5786, "popularity_score": 67.0},
    {"name": "Pittsburgh", "kind": "metro", "latitude": 40.4406, "longitude": -79.9959, "popularity_score": 66.0},
    {"name": "New Orleans", "kind": "metro", "latitude": 29.9511, "longitude": -90.0715, "popularity_score": 65.0},
    {"name": "Grand Canyon", "kind": "natural", "latitude": 36.0544, "longitude": -112.1401, "popularity_score": 97.0},
    {"name": "Yellowstone National Park", "kind": "natural", "latitude": 44.4280, "longitude": -110.5885, "popularity_score": 96.0},
    {"name": "Yosemite National Park", "kind": "natural", "latitude": 37.8651, "longitude": -119.5383, "popularity_score": 95.0},
    {"name": "Great Smoky Mountains", "kind": "natural", "latitude": 35.6532, "longitude": -83.5070, "popularity_score": 94.0},
    {"name": "Statue of Liberty", "kind": "natural", "latitude": 40.6892, "longitude": -74.0445, "popularity_score": 93.0},
    {"name": "Mount Rainier", "kind": "natural", "latitude": 46.8523, "longitude": -121.7603, "popularity_score": 92.0},
    {"name": "Niagara Falls", "kind": "natural", "latitude": 43.0962, "longitude": -79.0377, "popularity_score": 91.0},
    {"name": "Zion National Park", "kind": "natural", "latitude": 37.2982, "longitude": -113.0263, "popularity_score": 90.0},
    {"name": "Bryce Canyon", "kind": "natural", "latitude": 37.5930, "longitude": -112.1871, "popularity_score": 89.0},
    {"name": "Arches National Park", "kind": "natural", "latitude": 38.7331, "longitude": -109.5925, "popularity_score": 88.0},
    {"name": "Rocky Mountain National Park", "kind": "natural", "latitude": 40.3428, "longitude": -105.6836, "popularity_score": 87.0},
    {"name": "Lake Tahoe", "kind": "natural", "latitude": 39.0968, "longitude": -120.0324, "popularity_score": 86.0},
    {"name": "Monument Valley", "kind": "natural", "latitude": 36.9980, "longitude": -110.0985, "popularity_score": 85.0},
    {"name": "Everglades National Park", "kind": "natural", "latitude": 25.2866, "longitude": -80.8987, "popularity_score": 84.0},
    {"name": "Gateway Arch", "kind": "natural", "latitude": 38.6247, "longitude": -90.1848, "popularity_score": 83.0},
    {"name": "Glacier National Park", "kind": "natural", "latitude": 48.7596, "longitude": -113.7870, "popularity_score": 82.0},
    {"name": "Grand Teton", "kind": "natural", "latitude": 43.7904, "longitude": -110.6818, "popularity_score": 81.0},
    {"name": "Mount Rushmore", "kind": "natural", "latitude": 43.8791, "longitude": -103.4591, "popularity_score": 80.0},
    {"name": "Redwood National Park", "kind": "natural", "latitude": 41.2132, "longitude": -124.0046, "popularity_score": 79.0},
    {"name": "White Sands", "kind": "natural", "latitude": 32.7791, "longitude": -106.1717, "popularity_score": 78.0},
    {"name": "Great Sand Dunes", "kind": "natural", "latitude": 37.7916, "longitude": -105.5943, "popularity_score": 77.0},
    {"name": "Hoover Dam", "kind": "natural", "latitude": 36.0156, "longitude": -114.7378, "popularity_score": 76.0},
    {"name": "Pikes Peak", "kind": "natural", "latitude": 38.8409, "longitude": -105.0423, "popularity_score": 75.0},
    {"name": "Crater Lake", "kind": "natural", "latitude": 42.9446, "longitude": -122.1090, "popularity_score": 74.0},
    {"name": "Acadia National Park", "kind": "natural", "latitude": 44.3386, "longitude": -68.2733, "popularity_score": 73.0},
)
PUBLIC_REPORT_PLACE_ANCHOR_CATALOG = (
    {"name": "New York City", "latitude": 40.7128, "longitude": -74.0060, "county": "New York County", "state": "NY", "popularity_score": 100.0},
    {"name": "Los Angeles", "latitude": 34.0522, "longitude": -118.2437, "county": "Los Angeles County", "state": "CA", "popularity_score": 98.0},
    {"name": "Chicago", "latitude": 41.8781, "longitude": -87.6298, "county": "Cook County", "state": "IL", "popularity_score": 95.0},
    {"name": "Dallas", "latitude": 32.7767, "longitude": -96.7970, "county": "Dallas County", "state": "TX", "popularity_score": 91.0},
    {"name": "Houston", "latitude": 29.7604, "longitude": -95.3698, "county": "Harris County", "state": "TX", "popularity_score": 90.0},
    {"name": "Washington", "latitude": 38.9072, "longitude": -77.0369, "county": "District of Columbia", "state": "DC", "popularity_score": 88.0},
    {"name": "Atlanta", "latitude": 33.7490, "longitude": -84.3880, "county": "Fulton County", "state": "GA", "popularity_score": 87.0},
    {"name": "Miami", "latitude": 25.7617, "longitude": -80.1918, "county": "Miami-Dade County", "state": "FL", "popularity_score": 86.0},
    {"name": "Phoenix", "latitude": 33.4484, "longitude": -112.0740, "county": "Maricopa County", "state": "AZ", "popularity_score": 85.0},
    {"name": "Boston", "latitude": 42.3601, "longitude": -71.0589, "county": "Suffolk County", "state": "MA", "popularity_score": 84.0},
    {"name": "San Francisco", "latitude": 37.7749, "longitude": -122.4194, "county": "San Francisco County", "state": "CA", "popularity_score": 83.0},
    {"name": "Seattle", "latitude": 47.6062, "longitude": -122.3321, "county": "King County", "state": "WA", "popularity_score": 82.0},
    {"name": "Denver", "latitude": 39.7392, "longitude": -104.9903, "county": "Denver County", "state": "CO", "popularity_score": 81.0},
    {"name": "Minneapolis", "latitude": 44.9778, "longitude": -93.2650, "county": "Hennepin County", "state": "MN", "popularity_score": 80.0},
    {"name": "Detroit", "latitude": 42.3314, "longitude": -83.0458, "county": "Wayne County", "state": "MI", "popularity_score": 79.0},
    {"name": "San Diego", "latitude": 32.7157, "longitude": -117.1611, "county": "San Diego County", "state": "CA", "popularity_score": 78.0},
    {"name": "Tampa", "latitude": 27.9506, "longitude": -82.4572, "county": "Hillsborough County", "state": "FL", "popularity_score": 77.0},
    {"name": "Orlando", "latitude": 28.5383, "longitude": -81.3792, "county": "Orange County", "state": "FL", "popularity_score": 76.0},
    {"name": "Charlotte", "latitude": 35.2271, "longitude": -80.8431, "county": "Mecklenburg County", "state": "NC", "popularity_score": 75.0},
    {"name": "Las Vegas", "latitude": 36.1699, "longitude": -115.1398, "county": "Clark County", "state": "NV", "popularity_score": 74.0},
    {"name": "Salt Lake City", "latitude": 40.7608, "longitude": -111.8910, "county": "Salt Lake County", "state": "UT", "popularity_score": 73.0},
    {"name": "Portland", "latitude": 45.5152, "longitude": -122.6784, "county": "Multnomah County", "state": "OR", "popularity_score": 72.0},
    {"name": "Austin", "latitude": 30.2672, "longitude": -97.7431, "county": "Travis County", "state": "TX", "popularity_score": 71.0},
    {"name": "San Antonio", "latitude": 29.4241, "longitude": -98.4936, "county": "Bexar County", "state": "TX", "popularity_score": 70.0},
    {"name": "Nashville", "latitude": 36.1627, "longitude": -86.7816, "county": "Davidson County", "state": "TN", "popularity_score": 69.0},
    {"name": "St. Louis", "latitude": 38.6270, "longitude": -90.1994, "county": "St. Louis city", "state": "MO", "popularity_score": 68.0},
    {"name": "Kansas City", "latitude": 39.0997, "longitude": -94.5786, "county": "Jackson County", "state": "MO", "popularity_score": 67.0},
    {"name": "Pittsburgh", "latitude": 40.4406, "longitude": -79.9959, "county": "Allegheny County", "state": "PA", "popularity_score": 66.0},
    {"name": "New Orleans", "latitude": 29.9511, "longitude": -90.0715, "county": "Orleans Parish", "state": "LA", "popularity_score": 65.0},
    {"name": "Tusayan", "latitude": 35.9736, "longitude": -112.1263, "county": "Coconino County", "state": "AZ", "popularity_score": 64.0},
    {"name": "Springdale", "latitude": 37.1889, "longitude": -112.9986, "county": "Washington County", "state": "UT", "popularity_score": 63.0},
    {"name": "Bryce Canyon City", "latitude": 37.6720, "longitude": -112.1563, "county": "Garfield County", "state": "UT", "popularity_score": 62.0},
    {"name": "Gatlinburg", "latitude": 35.7143, "longitude": -83.5102, "county": "Sevier County", "state": "TN", "popularity_score": 61.0},
    {"name": "Ashford", "latitude": 46.7582, "longitude": -122.0293, "county": "Pierce County", "state": "WA", "popularity_score": 60.0},
    {"name": "Keystone", "latitude": 43.8950, "longitude": -103.4177, "county": "Pennington County", "state": "SD", "popularity_score": 59.0},
    {"name": "Boulder City", "latitude": 35.9780, "longitude": -114.8345, "county": "Clark County", "state": "NV", "popularity_score": 58.0},
    {"name": "Hulett", "latitude": 44.6833, "longitude": -104.6011, "county": "Crook County", "state": "WY", "popularity_score": 57.0},
    {"name": "Bar Harbor", "latitude": 44.3876, "longitude": -68.2039, "county": "Hancock County", "state": "ME", "popularity_score": 56.0},
    {"name": "Estes Park", "latitude": 40.3772, "longitude": -105.5217, "county": "Larimer County", "state": "CO", "popularity_score": 55.0},
    {"name": "Moab", "latitude": 38.5733, "longitude": -109.5498, "county": "Grand County", "state": "UT", "popularity_score": 54.0},
    {"name": "Jackson", "latitude": 43.4799, "longitude": -110.7624, "county": "Teton County", "state": "WY", "popularity_score": 53.0},
    {"name": "West Yellowstone", "latitude": 44.6621, "longitude": -111.1041, "county": "Gallatin County", "state": "MT", "popularity_score": 52.0},
    {"name": "Mariposa", "latitude": 37.4849, "longitude": -119.9663, "county": "Mariposa County", "state": "CA", "popularity_score": 51.0},
    {"name": "South Lake Tahoe", "latitude": 38.9399, "longitude": -119.9772, "county": "El Dorado County", "state": "CA", "popularity_score": 50.0},
    {"name": "Alamogordo", "latitude": 32.8995, "longitude": -105.9603, "county": "Otero County", "state": "NM", "popularity_score": 49.0},
    {"name": "Kalispell", "latitude": 48.1958, "longitude": -114.3129, "county": "Flathead County", "state": "MT", "popularity_score": 48.0},
    {"name": "Crescent City", "latitude": 41.7558, "longitude": -124.2026, "county": "Del Norte County", "state": "CA", "popularity_score": 47.0},
    {"name": "Government Camp", "latitude": 45.3043, "longitude": -121.7554, "county": "Clackamas County", "state": "OR", "popularity_score": 46.0},
    {"name": "Chiloquin", "latitude": 42.5771, "longitude": -121.8664, "county": "Klamath County", "state": "OR", "popularity_score": 45.0},
    {"name": "Oljato-Monument Valley", "latitude": 36.9897, "longitude": -110.1934, "county": "San Juan County", "state": "UT", "popularity_score": 44.0},
)
PUBLIC_REPORT_BASE_NAME_ANCHOR_MAP = {
    "New York City": "New York City",
    "Los Angeles": "Los Angeles",
    "Chicago": "Chicago",
    "Dallas-Fort Worth": "Dallas",
    "Houston": "Houston",
    "Washington, DC": "Washington",
    "Atlanta": "Atlanta",
    "Miami": "Miami",
    "Phoenix": "Phoenix",
    "Boston": "Boston",
    "San Francisco Bay Area": "San Francisco",
    "Seattle": "Seattle",
    "Denver": "Denver",
    "Minneapolis-Saint Paul": "Minneapolis",
    "Detroit": "Detroit",
    "San Diego": "San Diego",
    "Tampa Bay": "Tampa",
    "Orlando": "Orlando",
    "Charlotte": "Charlotte",
    "Las Vegas": "Las Vegas",
    "Salt Lake City": "Salt Lake City",
    "Portland": "Portland",
    "Austin": "Austin",
    "San Antonio": "San Antonio",
    "Nashville": "Nashville",
    "St. Louis": "St. Louis",
    "Kansas City": "Kansas City",
    "Pittsburgh": "Pittsburgh",
    "New Orleans": "New Orleans",
    "Grand Canyon": "Tusayan",
    "Yellowstone National Park": "West Yellowstone",
    "Yosemite National Park": "Mariposa",
    "Great Smoky Mountains": "Gatlinburg",
    "Statue of Liberty": "New York City",
    "Mount Rainier": "Ashford",
    "Niagara Falls": "New York City",
    "Zion National Park": "Springdale",
    "Bryce Canyon": "Bryce Canyon City",
    "Arches National Park": "Moab",
    "Rocky Mountain National Park": "Estes Park",
    "Lake Tahoe": "South Lake Tahoe",
    "Monument Valley": "Oljato-Monument Valley",
    "Everglades National Park": "Miami",
    "Gateway Arch": "St. Louis",
    "Glacier National Park": "Kalispell",
    "Grand Teton": "Jackson",
    "Mount Rushmore": "Keystone",
    "Redwood National Park": "Crescent City",
    "White Sands": "Alamogordo",
    "Great Sand Dunes": "Denver",
    "Hoover Dam": "Boulder City",
    "Pikes Peak": "Denver",
    "Crater Lake": "Chiloquin",
    "Acadia National Park": "Bar Harbor",
}
PUBLIC_REPORT_LIMITATION_ENTRIES = (
    {
        "name": "local_transmission_hosting_capacity",
        "title": "Local transmission hosting capacity",
        "status": "bounded proxy",
        "current_posture": "The current bundle stages a regional NERC reserve-margin headroom overlay as a coarse hosting-capacity proxy, but it still does not model local transmission hosting-capacity headroom.",
        "output_implication": "The hosting overlay supports coarse regional screening only; it does not confirm local deliverability or interconnection feasibility.",
    },
    {
        "name": "demand_queue_times",
        "title": "Demand queue times",
        "status": "not implemented",
        "current_posture": "The current bundle does not model interconnection queue wait times or developer queue backlog.",
        "output_implication": "Report outputs do not imply deployment-ready timing or queue-adjusted build schedules.",
    },
    {
        "name": "zoning_information",
        "title": "Zoning information",
        "status": "bounded proxy",
        "current_posture": "The current bundle stages an NLCD developed-land context overlay as a coarse zoning proxy, but it still does not model parcel-level zoning or allowed land uses.",
        "output_implication": "The zoning overlay supports coarse developed-context screening only; it does not confirm parcel-level zoning approval or data-center entitlement.",
    },
    {
        "name": "permitting_and_ordinance_information",
        "title": "Permitting and ordinance information",
        "status": "bounded proxy",
        "current_posture": "The current bundle stages a manifest-driven public permitting and ordinance evidence overlay, but it does not model permit approval likelihood or ordinance compatibility.",
        "output_implication": "The permitting overlay surfaces manually curated public evidence signals only; it does not confirm permit readiness or entitlement feasibility.",
    },
    {
        "name": "capacity_scaling_by_market_trends",
        "title": "More representative capacity scaling by market trends",
        "status": "bounded approximation",
        "current_posture": "The current bundle uses public EER scenario inputs and smoke-config site-addition limits rather than market-specific capacity scaling.",
        "output_implication": "Cumulative buildout outputs are screening artifacts, not market-calibrated deployment forecasts.",
    },
    {
        "name": "social_acceptance",
        "title": "Social acceptance",
        "status": "bounded proxy",
        "current_posture": "The current bundle stages a manifest-driven public social-friction evidence overlay, but it does not model community acceptance or social license to operate.",
        "output_implication": "The social-friction overlay surfaces manually curated public evidence signals only; it does not measure actual community acceptance or opposition intensity.",
    },
)
PUBLIC_REPORT_ZONING_PROXY_NLCD_LABELS = {
    21: "Developed, Open Space",
    22: "Developed, Low Intensity",
    23: "Developed, Medium Intensity",
    24: "Developed, High Intensity",
}
PUBLIC_REPORT_ZONING_PROXY_DEVELOPED_CLASSES = tuple(PUBLIC_REPORT_ZONING_PROXY_NLCD_LABELS)
PUBLIC_REPORT_PERMITTING_EVIDENCE_MANIFEST_PATH = (
    "external-data/manifest/permitting-ordinance-evidence.csv"
)
PUBLIC_REPORT_PERMITTING_EVIDENCE_COLUMNS = (
    "evidence_id",
    "jurisdiction_name",
    "state",
    "evidence_type",
    "friction_level",
    "latitude",
    "longitude",
    "source_url",
    "source_date",
    "summary",
)
PUBLIC_REPORT_PERMITTING_RESTRICTIVE_TYPES = {
    "moratorium",
    "ordinance_restriction",
}
PUBLIC_REPORT_PERMITTING_FRICTION_TYPES = {
    "local_opposition",
    "planning_board_signal",
    "public_hearing_outcome",
}
PUBLIC_REPORT_PERMITTING_RESTRICTIVE_LEVELS = {"high", "restrictive"}
PUBLIC_REPORT_PERMITTING_FRICTION_LEVELS = {"medium", "moderate"}
PUBLIC_REPORT_SOCIAL_FRICTION_EVIDENCE_MANIFEST_PATH = (
    "external-data/manifest/social-friction-evidence.csv"
)
PUBLIC_REPORT_SOCIAL_FRICTION_EVIDENCE_COLUMNS = (
    "evidence_id",
    "community_name",
    "state",
    "evidence_type",
    "friction_level",
    "latitude",
    "longitude",
    "source_url",
    "source_date",
    "summary",
)
PUBLIC_REPORT_SOCIAL_FRICTION_OPPOSITION_TYPES = {
    "appeal",
    "lawsuit",
    "news_documented_conflict",
    "organized_opposition",
    "petition",
}
PUBLIC_REPORT_SOCIAL_FRICTION_CONCERN_TYPES = {
    "civic_org_objection",
    "local_opposition_record",
    "public_hearing_concern",
    "public_meeting_concern",
}
PUBLIC_REPORT_SOCIAL_FRICTION_OPPOSITION_LEVELS = {"high", "organized", "opposition"}
PUBLIC_REPORT_SOCIAL_FRICTION_CONCERN_LEVELS = {"medium", "moderate", "concern"}
PUBLIC_REPORT_NLCD_WATER_WETLAND_CLASSES = (11, 90, 95)
PUBLIC_REPORT_NLCD_WATER_WETLAND_EXCLUSION_THRESHOLD = 0.5
MMBTU_PER_YEAR_TO_AVERAGE_MW = 0.29307107 / 8760
FEMA_NFHL_DOWNLOAD_BASE_URL = (
    "https://hazards.fema.gov/femaportal/NFHL/Download/ProductsDownLoadServlet"
)
RIBITS_WEBSERVICE_DOC_URL = "https://ribits.ops.usace.army.mil/ords/f?p=107:353::::::"
RIBITS_BANK_SITE_LIST_URL = "https://ribits.ops.usace.army.mil/ords/RI/public/bank_site_list/"
RIBITS_BANK_SITE_DATA_URL = "https://ribits.ops.usace.army.mil/ords/RI/public/bank_site_data/"
RIBITS_EPA_MAPSERVER_URL = "https://geopub.epa.gov/arcgis/rest/services/NEPAssist/RIBITS/MapServer"
DATA_CENTER_BASELINE_COLUMNS = [
    "baseline_id",
    "name",
    "operator",
    "site_status",
    "sources",
    "source_count",
    "source_ids",
    "wikidata_id",
    "source_url",
    "source_note",
    "latitude",
    "longitude",
    "geometry",
]
DATA_CENTER_STATUS_PRIORITY = {
    "unknown": 0,
    "planned": 1,
    "under_construction": 2,
    "existing": 3,
}
POWER_LINE_BASELINE_COLUMNS = [
    "source",
    "source_id",
    "name",
    "operator",
    "power_type",
    "voltage_text",
    "max_voltage_kv",
    "is_underground",
    "source_url",
    "geometry",
]
SUBSTATION_BASELINE_COLUMNS = [
    "source",
    "source_id",
    "name",
    "operator",
    "substation_type",
    "voltage_text",
    "max_voltage_kv",
    "latitude",
    "longitude",
    "source_url",
    "geometry",
]
FIBER_ROUTE_BASELINE_COLUMNS = [
    "source",
    "source_id",
    "name",
    "operator",
    "route_tag",
    "source_url",
    "geometry",
]
GAS_SERVICE_TERRITORY_COLUMNS = [
    "territory_id",
    "state",
    "utility_name",
    "source_path",
    "geometry",
]
LAND_VALUE_PROXY_COLUMNS = [
    "county_id",
    "state",
    "land_value_proxy_usd_per_acre",
    "state_land_value_index",
    "geometry",
]
CONSTRUCTION_COST_PROXY_COLUMNS = [
    "county_id",
    "state",
    "construction_worker_mean_wage_usd",
    "regional_price_parity_index",
    "construction_cost_proxy_score",
    "construction_cost_relative_index",
    "geometry",
]

_XML_NS = {
    "x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}


@dataclass(frozen=True)
class PublicDatasetSpec:
    """Definition of a public source dataset and how it is staged locally."""

    dataset_id: str
    acquisition_mode: str
    landing_page: str
    output_relpath: str
    download_url: str | None = None
    access_urls: tuple[str, ...] = ()
    notes: str = ""


@dataclass(frozen=True)
class PublicExampleBundleSpec:
    """Definition of a runnable example-input bundle for a generated public workflow."""

    bundle_id: str
    output_relpath: str
    writer: Callable[[Path], None]
    command: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    notes: str = ""


PUBLIC_DATASET_CATALOG = {
    "data_center_osm_export": PublicDatasetSpec(
        dataset_id="data_center_osm_export",
        acquisition_mode="manual",
        landing_page="https://overpass-turbo.eu/",
        output_relpath="external-data/raw/data-centers/osm_data_centers_QUERY.txt",
        access_urls=("https://overpass-api.de/api/interpreter",),
        notes=(
            "Export an Overpass JSON payload of public data center features and save it "
            "as external-data/raw/data-centers/osm_data_centers.json. The payload is "
            "consumed by python -m reVeal.public_data generate-data-center-baseline."
        ),
    ),
    "data_center_wikidata_export": PublicDatasetSpec(
        dataset_id="data_center_wikidata_export",
        acquisition_mode="manual",
        landing_page="https://query.wikidata.org/",
        output_relpath="external-data/raw/data-centers/wikidata_data_centers_QUERY.txt",
        access_urls=("https://query.wikidata.org/sparql",),
        notes=(
            "Export a Wikidata SPARQL JSON result of public data center features and save "
            "it as external-data/raw/data-centers/wikidata_data_centers.json. The payload "
            "is consumed by python -m reVeal.public_data generate-data-center-baseline."
        ),
    ),
    "data_center_manual_augmentation": PublicDatasetSpec(
        dataset_id="data_center_manual_augmentation",
        acquisition_mode="manual",
        landing_page="local",
        output_relpath="external-data/raw/data-centers/manual_data_centers_SCHEMA.txt",
        notes=(
            "Create an optional CSV named external-data/raw/data-centers/manual_data_centers.csv "
            "with columns name, latitude, longitude, and site_status. Optional columns are "
            "operator, wikidata_id, source_url, and source_note."
        ),
    ),
    "baxtel_us_data_center_sites": PublicDatasetSpec(
        dataset_id="baxtel_us_data_center_sites",
        acquisition_mode="manual",
        landing_page="https://baxtel.com/services/datasets",
        output_relpath="external-data/raw/data-centers/baxtel_SAMPLE_REQUEST.txt",
        access_urls=(
            "https://baxtel.com/quotes/new",
            "https://baxtel.com/contacts/new",
        ),
        notes=(
            "Request a sample CSV with schema documentation or a licensed snapshot from "
            "Baxtel's dataset workflow. If access is approved, save the delivered CSV as "
            "external-data/raw/data-centers/baxtel_data_center_sites.csv and keep it out "
            "of git because it is commercial, license-bound data. This remains a manual "
            "commercial-procurement workflow rather than a public download."
        ),
    ),
    "transmission_lines_osm_export": PublicDatasetSpec(
        dataset_id="transmission_lines_osm_export",
        acquisition_mode="manual",
        landing_page="https://overpass-turbo.eu/",
        output_relpath="external-data/raw/power/osm_transmission_lines_QUERY.txt",
        access_urls=("https://overpass-api.de/api/interpreter",),
        notes=(
            "Export an Overpass JSON payload of OSM power=line, power=minor_line, and "
            "power=cable features, then save it as external-data/raw/power/"
            "osm_transmission_lines.json. The payload is consumed by python -m "
            "reVeal.public_data generate-power-infrastructure-baseline."
        ),
    ),
    "substations_osm_export": PublicDatasetSpec(
        dataset_id="substations_osm_export",
        acquisition_mode="manual",
        landing_page="https://overpass-turbo.eu/",
        output_relpath="external-data/raw/power/osm_substations_QUERY.txt",
        access_urls=("https://overpass-api.de/api/interpreter",),
        notes=(
            "Export an Overpass JSON payload of OSM power=substation features and save it "
            "as external-data/raw/power/osm_substations.json. The payload is consumed by "
            "python -m reVeal.public_data generate-power-infrastructure-baseline."
        ),
    ),
    "fiber_lines_osm_export": PublicDatasetSpec(
        dataset_id="fiber_lines_osm_export",
        acquisition_mode="manual",
        landing_page="https://overpass-turbo.eu/",
        output_relpath="external-data/raw/fiber/osm_fiber_lines_QUERY.txt",
        access_urls=("https://overpass-api.de/api/interpreter",),
        notes=(
            "Export an Overpass JSON payload of route-like OSM telecom or fiber linework "
            "and save it as external-data/raw/fiber/osm_fiber_lines.json. The payload is "
            "consumed by python -m reVeal.public_data generate-fiber-proxy-rasters."
        ),
    ),
    "fcc_bdc_fiber_availability_export": PublicDatasetSpec(
        dataset_id="fcc_bdc_fiber_availability_export",
        acquisition_mode="manual",
        landing_page="https://broadbandmap.fcc.gov/home",
        output_relpath="external-data/raw/fiber/fcc_bdc_fiber_availability_EXPORT.txt",
        notes=(
            "Create a locally filtered FCC Broadband Data Collection fiber-availability "
            "polygon export and save it as external-data/raw/fiber/"
            "fcc_bdc_fiber_availability.gpkg. The repo treats this as an availability "
            "proxy surface rather than route geometry and consumes it with python -m "
            "reVeal.public_data generate-fiber-proxy-rasters."
        ),
    ),
    "state_gas_service_territory_manifest": PublicDatasetSpec(
        dataset_id="state_gas_service_territory_manifest",
        acquisition_mode="manual",
        landing_page="local",
        output_relpath="external-data/raw/gas/state_gas_service_territories_MANIFEST_SCHEMA.txt",
        notes=(
            "Create a CSV named external-data/raw/gas/state_gas_service_territories.csv "
            "with one row per state extract. Required columns are state and path. An "
            "optional utility_field column can name the source attribute that carries "
            "utility or provider names. The manifest is consumed by python -m "
            "reVeal.public_data generate-gas-service-territory-baseline."
        ),
    ),
    "usgs_state_water_use_proxy_csv": PublicDatasetSpec(
        dataset_id="usgs_state_water_use_proxy_csv",
        acquisition_mode="manual",
        landing_page="local",
        output_relpath="external-data/raw/water/usgs_state_water_use_proxy_SCHEMA.txt",
        notes=(
            "Create a CSV named external-data/raw/water/usgs_state_water_use_proxy.csv "
            "with columns state and freshwater_withdrawal_mgd. Optional columns are "
            "source_year and source_note. The CSV is consumed by python -m "
            "reVeal.public_data generate-water-availability-proxy-features."
        ),
    ),
    "county_land_value_proxy_inputs": PublicDatasetSpec(
        dataset_id="county_land_value_proxy_inputs",
        acquisition_mode="manual",
        landing_page="local",
        output_relpath="external-data/raw/land/county_land_value_proxy_INPUTS.txt",
        notes=(
            "Create a CSV named external-data/raw/land/county_land_value_proxy.csv with "
            "columns county_id, state, and land_value_proxy_usd_per_acre, and stage a "
            "county polygon layer such as external-data/raw/land/"
            "county_land_value_counties.gpkg with county_id and geometry. These inputs "
            "are consumed by python -m reVeal.public_data "
            "generate-land-value-proxy-features."
        ),
    ),
    "county_construction_cost_proxy_inputs": PublicDatasetSpec(
        dataset_id="county_construction_cost_proxy_inputs",
        acquisition_mode="manual",
        landing_page="local",
        output_relpath="external-data/raw/construction/county_construction_cost_proxy_INPUTS.txt",
        notes=(
            "Create a CSV named external-data/raw/construction/"
            "county_construction_cost_proxy.csv with columns county_id, state, "
            "construction_worker_mean_wage_usd, and regional_price_parity_index, "
            "and stage a county polygon layer such as external-data/raw/construction/"
            "county_construction_cost_counties.gpkg with county_id and geometry. The "
            "proxy CSV is intended to be assembled from public labor and regional "
            "price inputs such as BLS QCEW, LEHD, and BEA RPP. These inputs are "
            "consumed by python -m reVeal.public_data "
            "generate-construction-cost-proxy-features."
        ),
    ),
    "nerc_ltra": PublicDatasetSpec(
        dataset_id="nerc_ltra",
        acquisition_mode="direct",
        landing_page="https://www.nerc.com/pa/RAPA/ra/Pages/default.aspx",
        download_url="https://www.nerc.com/globalassets/our-work/assessments/nerc_ltra_2025.pdf",
        output_relpath="external-data/raw/nerc/nerc_ltra_2025.pdf",
        notes="Public direct download.",
    ),
    "urdb": PublicDatasetSpec(
        dataset_id="urdb",
        acquisition_mode="direct",
        landing_page="https://apps.openei.org/USURDB/",
        download_url="https://apps.openei.org/USURDB/download/usurdb.csv.gz",
        output_relpath="external-data/raw/urdb/usurdb.csv.gz",
        access_urls=(
            "https://api.openei.org/utility_rates",
            "https://openei.org/services/doc/rest/util_rates/",
        ),
        notes=(
            "OpenEI publishes a direct bulk export of approved utility rates and a "
            "public API. API use requires a free key; the bulk CSV export is the repo's "
            "default staging surface."
        ),
    ),
    "nwi_wetlands": PublicDatasetSpec(
        dataset_id="nwi_wetlands",
        acquisition_mode="manual",
        landing_page="https://www.fws.gov/program/national-wetlands-inventory/wetlands-mapper",
        output_relpath="external-data/raw/nwi/MANUAL_DOWNLOAD.txt",
        download_url=(
            "https://documentst.ecosphere.fws.gov/wetlands/data/State-Downloads/"
            "AL_geodatabase_wetlands.zip"
        ),
        access_urls=(
            "https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/rest",
            "https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/services/Wetlands/MapServer/WMSServer?request=GetCapabilities&service=WMS",
        ),
        notes=(
            "Use the Wetlands Mapper or Wetlands Data workflow to download the needed "
            "wetlands geospatial extracts. A confirmed direct FWS ZIP is available for "
            "state downloads using postal-code filenames, and stable REST and WMS "
            "service endpoints have also been confirmed for direct live access."
        ),
    ),
    "nlcd": PublicDatasetSpec(
        dataset_id="nlcd",
        acquisition_mode="manual",
        landing_page="https://www.usgs.gov/annualnlcd",
        output_relpath="external-data/raw/nlcd/MANUAL_DOWNLOAD.txt",
        download_url=(
            "https://www.sciencebase.gov/catalog/file/get/664e0d2bd34e702fe8744536"
            "?name=Annual_NLCD_LndCov_2023_CU_C1V0.zip"
        ),
        access_urls=(
            "https://dmsdata.cr.usgs.gov/geoserver/mrlc_Land-Cover-Native_conus_year_data/wms?service=WMS&request=GetCapabilities",
            "https://dmsdata.cr.usgs.gov/geoserver/mrlc_Land-Cover-Native_conus_year_data/wcs?service=WCS&request=GetCapabilities",
        ),
        notes=(
            "Use the Annual NLCD distribution workflow to select the needed land-cover "
            "raster products. A confirmed ScienceBase ZIP download is available for the "
            "2023 CONUS land-cover package, and official MRLC WMS and WCS endpoints are "
            "also available for direct live access to the Annual NLCD land-cover service. "
            "If the representative ZIP request fails during staging, the repo now falls "
            "back to tiled MRLC WMS requests and writes a bounded TIFF at "
            "external-data/raw/nlcd/Annual_NLCD_LndCov_2023_CU_C1V0.tif using the current "
            "report-grid footprint."
        ),
    ),
    "pad_us_gap": PublicDatasetSpec(
        dataset_id="pad_us_gap",
        acquisition_mode="manual",
        landing_page="https://www.usgs.gov/programs/gap-analysis-project/science/pad-us-data-download",
        output_relpath="external-data/raw/pad-us/MANUAL_DOWNLOAD.txt",
        download_url=(
            "https://www.sciencebase.gov/catalog/file/get/652d4fc5d34e44db0e2ee45e"
            "?name=PADUS4_1Geodatabase.zip"
        ),
        access_urls=(
            "https://services.arcgis.com/v01gqwM5QqNysAAi/arcgis/rest/services/PADUS_Protection_Status_by_GAP_Status_Code/FeatureServer",
            "https://services.arcgis.com/v01gqwM5QqNysAAi/arcgis/rest/services/PADUS_Public_Access/FeatureServer",
        ),
        notes=(
            "Use the PAD-US download workflow to pull the current protected-areas data "
            "package. A confirmed ScienceBase ZIP download is available for the PAD-US "
            "4.1 national geodatabase, and USGS also publishes stable ArcGIS feature-"
            "service views for PAD-US protection status and public-access layers."
        ),
    ),
    "fema_nfhl": PublicDatasetSpec(
        dataset_id="fema_nfhl",
        acquisition_mode="manual",
        landing_page="https://msc.fema.gov/portal/advanceSearch",
        output_relpath="external-data/raw/fema/MANUAL_DOWNLOAD.txt",
        access_urls=(
            "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer",
            "https://hazards.fema.gov/arcgis/services/public/NFHLWMS/MapServer/WMSServer?request=GetCapabilities&service=WMS",
            "https://hazards.fema.gov/arcgis/services/public/NFHL/MapServer/WFSServer?service=WFS&request=GetCapabilities",
        ),
        notes=(
            "Use the FEMA Map Service Center search workflow to download the needed NFHL "
            "products for the target jurisdictions. Generate a community-specific NFHL "
            "ZIP URL with `python -m reVeal.public_data build-fema-download-url --dfirm-id "
            "... --state ... --county ... --file-name ...` or pass those same arguments "
            "to `stage-dataset`. Official FEMA ArcGIS REST, WMS, and WFS endpoints are "
            "also available for direct live access."
        ),
    ),
    "ribits": PublicDatasetSpec(
        dataset_id="ribits",
        acquisition_mode="manual",
        landing_page="https://ribits.ops.usace.army.mil/",
        output_relpath="external-data/raw/ribits/MANUAL_DOWNLOAD.txt",
        access_urls=(
            RIBITS_WEBSERVICE_DOC_URL,
            RIBITS_BANK_SITE_LIST_URL,
            RIBITS_BANK_SITE_DATA_URL,
            RIBITS_EPA_MAPSERVER_URL,
        ),
        notes=(
            "Use `python -m reVeal.public_data download-ribits-bank-sites` to pull a "
            "repo-local JSON snapshot through the documented RIBITS ORDS public "
            "webservices. The staged note created here records that scripted workflow and "
            "the public webservice endpoints for bank_site_list, bank_site_data, and the "
            "EPA-hosted ESRI mirror."
        ),
    ),
}


NERC_LTRA_MARGIN_YEARS = (2026, 2027, 2028, 2029, 2030)

NERC_LTRA_2025_MARGIN_ROWS = (
    {
        "assessment_area": "MISO",
        "peak_season": "summer",
        "arm_2026": 11.0,
        "arm_2027": 11.2,
        "arm_2028": 9.5,
        "arm_2029": 8.6,
        "arm_2030": 4.3,
        "rml_2026": 8.1,
        "rml_2027": 8.3,
        "rml_2028": 8.5,
        "rml_2029": 8.5,
        "rml_2030": 8.5,
    },
    {
        "assessment_area": "MRO-Manitoba Hydro",
        "peak_season": "winter",
        "arm_2026": 13.9,
        "arm_2027": 36.2,
        "arm_2028": 15.4,
        "arm_2029": 13.6,
        "arm_2030": 1.2,
        "rml_2026": 12.0,
        "rml_2027": 12.0,
        "rml_2028": 12.0,
        "rml_2029": 12.0,
        "rml_2030": 12.0,
    },
    {
        "assessment_area": "MRO-SaskPower",
        "peak_season": "winter",
        "arm_2026": 25.9,
        "arm_2027": 23.4,
        "arm_2028": 33.4,
        "arm_2029": 32.3,
        "arm_2030": 31.2,
        "rml_2026": 15.0,
        "rml_2027": 15.0,
        "rml_2028": 15.0,
        "rml_2029": 15.0,
        "rml_2030": 15.0,
    },
    {
        "assessment_area": "MRO-SPP",
        "peak_season": "summer",
        "arm_2026": 32.4,
        "arm_2027": 30.3,
        "arm_2028": 28.4,
        "arm_2029": 25.1,
        "arm_2030": 22.6,
        "rml_2026": 19.0,
        "rml_2027": 19.0,
        "rml_2028": 19.0,
        "rml_2029": 19.0,
        "rml_2030": 19.0,
    },
    {
        "assessment_area": "NPCC-Maritimes",
        "peak_season": "winter",
        "arm_2026": 16.7,
        "arm_2027": 30.2,
        "arm_2028": 25.6,
        "arm_2029": 23.0,
        "arm_2030": 21.7,
        "rml_2026": 20.0,
        "rml_2027": 20.0,
        "rml_2028": 20.0,
        "rml_2029": 20.0,
        "rml_2030": 20.0,
    },
    {
        "assessment_area": "NPCC-New England",
        "peak_season": "summer",
        "arm_2026": 18.3,
        "arm_2027": 21.7,
        "arm_2028": 24.8,
        "arm_2029": 23.7,
        "arm_2030": 23.6,
        "rml_2026": 13.4,
        "rml_2027": 13.0,
        "rml_2028": 13.0,
        "rml_2029": 13.0,
        "rml_2030": 13.0,
    },
    {
        "assessment_area": "NPCC-New York",
        "peak_season": "summer",
        "arm_2026": 22.3,
        "arm_2027": 24.5,
        "arm_2028": 24.5,
        "arm_2029": 23.6,
        "arm_2030": 22.5,
        "rml_2026": 15.0,
        "rml_2027": 15.0,
        "rml_2028": 15.0,
        "rml_2029": 15.0,
        "rml_2030": 15.0,
    },
    {
        "assessment_area": "NPCC-Ontario",
        "peak_season": "summer",
        "arm_2026": 29.6,
        "arm_2027": 19.8,
        "arm_2028": 28.1,
        "arm_2029": 18.7,
        "arm_2030": 19.7,
        "rml_2026": 16.1,
        "rml_2027": 19.0,
        "rml_2028": 22.6,
        "rml_2029": 15.8,
        "rml_2030": 19.5,
    },
    {
        "assessment_area": "NPCC-Québec",
        "peak_season": "winter",
        "arm_2026": 35.0,
        "arm_2027": 16.7,
        "arm_2028": 14.7,
        "arm_2029": 13.0,
        "arm_2030": 11.5,
        "rml_2026": 11.9,
        "rml_2027": 12.2,
        "rml_2028": 12.2,
        "rml_2029": 12.2,
        "rml_2030": 12.2,
    },
    {
        "assessment_area": "PJM",
        "peak_season": "summer",
        "arm_2026": 29.7,
        "arm_2027": 28.3,
        "arm_2028": 24.3,
        "arm_2029": 18.9,
        "arm_2030": 16.5,
        "rml_2026": 18.6,
        "rml_2027": 20.1,
        "rml_2028": 21.9,
        "rml_2029": 23.9,
        "rml_2030": 26.3,
    },
    {
        "assessment_area": "SERC-Central",
        "peak_season": "summer",
        "arm_2026": 19.1,
        "arm_2027": 20.8,
        "arm_2028": 19.7,
        "arm_2029": 18.5,
        "arm_2030": 19.7,
        "rml_2026": 15.0,
        "rml_2027": 15.0,
        "rml_2028": 15.0,
        "rml_2029": 15.0,
        "rml_2030": 15.0,
    },
    {
        "assessment_area": "SERC-East",
        "peak_season": "summer",
        "arm_2026": 30.6,
        "arm_2027": 30.5,
        "arm_2028": 30.5,
        "arm_2029": 31.5,
        "arm_2030": 34.9,
        "rml_2026": 15.0,
        "rml_2027": 15.0,
        "rml_2028": 15.0,
        "rml_2029": 15.0,
        "rml_2030": 15.0,
    },
    {
        "assessment_area": "SERC-Florida Peninsula",
        "peak_season": "summer",
        "arm_2026": 27.4,
        "arm_2027": 25.2,
        "arm_2028": 24.3,
        "arm_2029": 22.6,
        "arm_2030": 21.1,
        "rml_2026": 15.0,
        "rml_2027": 15.0,
        "rml_2028": 15.0,
        "rml_2029": 15.0,
        "rml_2030": 15.0,
    },
    {
        "assessment_area": "SERC-Southeast",
        "peak_season": "summer",
        "arm_2026": 35.9,
        "arm_2027": 29.5,
        "arm_2028": 29.8,
        "arm_2029": 24.9,
        "arm_2030": 20.9,
        "rml_2026": 15.0,
        "rml_2027": 15.0,
        "rml_2028": 15.0,
        "rml_2029": 15.0,
        "rml_2030": 15.0,
    },
    {
        "assessment_area": "Texas RE-ERCOT",
        "peak_season": "summer",
        "arm_2026": 28.2,
        "arm_2027": 30.5,
        "arm_2028": 31.8,
        "arm_2029": 30.8,
        "arm_2030": 29.9,
        "rml_2026": 13.75,
        "rml_2027": 13.75,
        "rml_2028": 13.75,
        "rml_2029": 13.75,
        "rml_2030": 13.75,
    },
    {
        "assessment_area": "WECC-Alberta",
        "peak_season": "winter",
        "arm_2026": 17.2,
        "arm_2027": 45.3,
        "arm_2028": 40.7,
        "arm_2029": 38.0,
        "arm_2030": 33.0,
        "rml_2026": 11.8,
        "rml_2027": 17.6,
        "rml_2028": 14.3,
        "rml_2029": 15.6,
        "rml_2030": 11.6,
    },
    {
        "assessment_area": "WECC-Basin",
        "peak_season": "summer",
        "arm_2026": 36.3,
        "arm_2027": 37.9,
        "arm_2028": 27.4,
        "arm_2029": 19.7,
        "arm_2030": 15.2,
        "rml_2026": 13.5,
        "rml_2027": 14.0,
        "rml_2028": 13.6,
        "rml_2029": 12.4,
        "rml_2030": 12.3,
    },
    {
        "assessment_area": "WECC-British Columbia",
        "peak_season": "winter",
        "arm_2026": 18.5,
        "arm_2027": 19.1,
        "arm_2028": 19.5,
        "arm_2029": 24.1,
        "arm_2030": 24.2,
        "rml_2026": 11.7,
        "rml_2027": 12.1,
        "rml_2028": 12.1,
        "rml_2029": 11.6,
        "rml_2030": 11.6,
    },
    {
        "assessment_area": "WECC-California",
        "peak_season": "summer",
        "arm_2026": 53.2,
        "arm_2027": 47.0,
        "arm_2028": 46.1,
        "arm_2029": 45.6,
        "arm_2030": 42.7,
        "rml_2026": 20.3,
        "rml_2027": 19.2,
        "rml_2028": 19.3,
        "rml_2029": 19.7,
        "rml_2030": 19.3,
    },
    {
        "assessment_area": "WECC-Mexico",
        "peak_season": "summer",
        "arm_2026": 14.9,
        "arm_2027": 13.8,
        "arm_2028": 29.9,
        "arm_2029": 27.0,
        "arm_2030": 24.6,
        "rml_2026": 7.8,
        "rml_2027": 8.0,
        "rml_2028": 9.1,
        "rml_2029": 7.2,
        "rml_2030": 7.0,
    },
    {
        "assessment_area": "WECC-Northwest",
        "peak_season": "winter",
        "arm_2026": 15.6,
        "arm_2027": 29.3,
        "arm_2028": 23.3,
        "arm_2029": 19.1,
        "arm_2030": 15.7,
        "rml_2026": 17.8,
        "rml_2027": 17.4,
        "rml_2028": 16.1,
        "rml_2029": 15.8,
        "rml_2030": 15.5,
    },
    {
        "assessment_area": "WECC-Rocky Mountain",
        "peak_season": "summer",
        "arm_2026": 51.3,
        "arm_2027": 60.0,
        "arm_2028": 53.2,
        "arm_2029": 38.1,
        "arm_2030": 30.5,
        "rml_2026": 17.8,
        "rml_2027": 17.0,
        "rml_2028": 16.2,
        "rml_2029": 16.1,
        "rml_2030": 15.7,
    },
    {
        "assessment_area": "WECC-Southwest",
        "peak_season": "summer",
        "arm_2026": 41.1,
        "arm_2027": 39.6,
        "arm_2028": 38.6,
        "arm_2029": 38.4,
        "arm_2030": 36.1,
        "rml_2026": 13.3,
        "rml_2027": 13.7,
        "rml_2028": 13.6,
        "rml_2029": 12.6,
        "rml_2030": 12.2,
    },
)

NERC_LTRA_EMM_ZONE_CROSSWALK = {
    "Carolinas": "SERC-East",
    "Central Great Plains": "MRO-SPP",
    "Florida": "SERC-Florida Peninsula",
    "Great Basin": "WECC-Basin",
    "Metropolitan Chicago": "PJM",
    "Metropolitan New York": "NPCC-New York",
    "Mid-Atlantic": "PJM",
    "Middle Mississippi Valley": "MISO",
    "Michigan": "MISO",
    "Mississippi Delta": "SERC-Central",
    "New England": "NPCC-New England",
    "Northern California": "WECC-California",
    "Northern Great Plains": "MRO-SPP",
    "Northwest": "WECC-Northwest",
    "Ohio Valley": "PJM",
    "Rockies": "WECC-Rocky Mountain",
    "Southeast": "SERC-Southeast",
    "Southern California": "WECC-California",
    "Southern Great Plains": "MRO-SPP",
    "Southwest": "WECC-Southwest",
    "Tennessee Valley": "SERC-Central",
    "Texas": "Texas RE-ERCOT",
    "Upper Mississippi Valley": "MISO",
    "Upstate New York": "NPCC-New York",
    "Virginia": "PJM",
}


def _pad_row(values, width):
    """Pad a row of sheet values so it aligns with the header width."""
    if len(values) >= width:
        return values[:width]
    return values + [""] * (width - len(values))


def _read_shared_strings(workbook_zip):
    """Read XLSX shared strings into a list."""
    shared_strings = []
    if "xl/sharedStrings.xml" not in workbook_zip.namelist():
        return shared_strings

    root = ET.fromstring(workbook_zip.read("xl/sharedStrings.xml"))
    for cell in root.findall("x:si", _XML_NS):
        shared_strings.append(
            "".join(text.text or "" for text in cell.iterfind(".//x:t", _XML_NS))
        )

    return shared_strings


def _cell_value(cell, shared_strings):
    """Decode a raw XLSX cell into a string value."""
    value = cell.find("x:v", _XML_NS)
    if value is None:
        return ""
    text = value.text or ""
    if cell.attrib.get("t") == "s":
        return shared_strings[int(text)]
    return text


def read_xlsx_sheet_records(xlsx_path, sheet_name, header_marker):
    """
    Read records from an XLSX sheet using a row whose first cell matches a marker.

    Parameters
    ----------
    xlsx_path : str | pathlib.Path
        Path to XLSX workbook.
    sheet_name : str
        Sheet name to read.
    header_marker : str
        Value expected in the first header cell.

    Returns
    -------
    list[dict]
        List of row records keyed by header name.
    """
    xlsx_path = Path(xlsx_path)
    with zipfile.ZipFile(xlsx_path) as workbook_zip:
        shared_strings = _read_shared_strings(workbook_zip)
        workbook = ET.fromstring(workbook_zip.read("xl/workbook.xml"))
        rels = ET.fromstring(workbook_zip.read("xl/_rels/workbook.xml.rels"))
        relmap = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in rels.findall("rel:Relationship", _XML_NS)
        }

        target = None
        for sheet in workbook.find("x:sheets", _XML_NS):
            if sheet.attrib["name"] == sheet_name:
                rel_id = sheet.attrib[
                    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
                ]
                target = "xl/" + relmap[rel_id]
                break
        if target is None:
            raise ValueError(f"Sheet not found in workbook: {sheet_name}")

        sheet_root = ET.fromstring(workbook_zip.read(target))
        header = None
        records = []
        for row in sheet_root.findall(".//x:sheetData/x:row", _XML_NS):
            values = [_cell_value(cell, shared_strings) for cell in row.findall("x:c", _XML_NS)]
            if not values or not any(values):
                continue
            if values[0] == header_marker:
                header = values
                continue
            if header is None:
                continue
            padded = _pad_row(values, len(header))
            records.append(dict(zip(header, padded)))

    return records


def normalize_eer_zone_name(zone_name):
    """Normalize an EER workbook EMM zone string to title case."""
    normalized = str(zone_name).strip().replace("_emm", "").replace("_", " ")
    return normalized.title()


def build_state_zone_weights(mapping_rows, zone_groups_df):
    """
    Build state-to-zone and state-to-zone-group area-share weights.

    Parameters
    ----------
    mapping_rows : list[dict]
        Records from the EER workbook ``Mapping zone to county`` sheet.
    zone_groups_df : pandas.DataFrame | geopandas.GeoDataFrame
        DataFrame with ``emm_zone`` and ``zone_group`` columns.

    Returns
    -------
    pandas.DataFrame
        Columns: ``state``, ``zone``, ``zone_group``, ``weight``.
    """
    zone_lookup = {
        normalize_eer_zone_name(row.emm_zone): str(row.zone_group).strip().lower()
        for row in zone_groups_df[["emm_zone", "zone_group"]].drop_duplicates().itertuples(index=False)
    }
    state_zone_area = {}
    state_area = {}
    for row in mapping_rows:
        county_label = row.get("county", "")
        if "," not in county_label:
            continue
        zone_name = normalize_eer_zone_name(row.get("zone", ""))
        if zone_name not in zone_lookup:
            continue
        area = float(row.get("sqmi", 0) or 0)
        state = county_label.rsplit(",", 1)[-1].strip().lower()
        key = (state, zone_name)
        state_zone_area[key] = state_zone_area.get(key, 0.0) + area
        state_area[state] = state_area.get(state, 0.0) + area

    records = []
    for (state, zone_name), area in state_zone_area.items():
        if state_area[state] == 0:
            continue
        records.append(
            {
                "state": state,
                "zone": zone_name.lower(),
                "zone_group": zone_lookup[zone_name],
                "weight": area / state_area[state],
            }
        )

    return pd.DataFrame(records).sort_values(["state", "zone"]).reset_index(drop=True)


def _build_state_year_loads(final_energy_rows, years, scenario_column):
    """Aggregate public EER final-energy records to state-year average MW loads."""
    state_year_load = {}
    year_filter = {int(year) for year in years}
    for row in final_energy_rows:
        if row.get("Subsector") not in EER_PUBLIC_SUBSECTORS:
            continue
        if row.get("Final Energy") != "electricity":
            continue
        if scenario_column not in row:
            raise KeyError(f"Scenario column not found: {scenario_column}")
        state = row.get("State", "").strip().lower()
        if not state:
            continue
        year = int(row.get("Year"))
        if year not in year_filter:
            continue
        load = float(row.get(scenario_column, 0) or 0) * MMBTU_PER_YEAR_TO_AVERAGE_MW
        key = (state, year)
        state_year_load[key] = state_year_load.get(key, 0.0) + load

    return state_year_load


def build_eer_public_projection_frames(
    final_energy_rows,
    state_zone_weights,
    years=EER_PUBLIC_YEARS,
    scenario_column=EER_PUBLIC_SCENARIO,
):
    """
    Convert public EER final-energy rows into reVeal-compatible projection frames.

    Parameters
    ----------
    final_energy_rows : list[dict]
        Records from the public EER ``Final energy demand`` sheet.
    state_zone_weights : pandas.DataFrame
        Output of :func:`build_state_zone_weights`.
    years : iterable[int], optional
        Years to include in the output projections.
    scenario_column : str, optional
        Scenario column to read from the workbook.

    Returns
    -------
    tuple[pandas.DataFrame, pandas.DataFrame, pandas.DataFrame]
        Total, regional, and region-group projection dataframes.
    """
    state_year_load = _build_state_year_loads(final_energy_rows, years, scenario_column)

    mapped_states = set()
    if not state_zone_weights.empty:
        mapped_states = set(state_zone_weights["state"])

    total_records = []
    for year in sorted({year for _, year in state_year_load}):
        total_records.append(
            {
                "year": year,
                "dc_load_mw": sum(
                    load
                    for (state, year_key), load in state_year_load.items()
                    if year_key == year
                    and (not mapped_states or state in mapped_states)
                ),
            }
        )

    zone_records = []
    for row in state_zone_weights.itertuples(index=False):
        for (state, year), load in state_year_load.items():
            if state != row.state:
                continue
            zone_records.append(
                {
                    "year": year,
                    "zone": row.zone,
                    "zone_group": row.zone_group,
                    "dc_load_mw": load * row.weight,
                }
            )
    zone_df = pd.DataFrame(zone_records)
    if zone_df.empty:
        regional_df = pd.DataFrame(columns=["year", "zone", "dc_load_mw"])
        grouped_df = pd.DataFrame(columns=["year", "zone_group", "dc_load_mw"])
    else:
        regional_df = (
            zone_df.groupby(["year", "zone"], as_index=False)["dc_load_mw"]
            .sum()
            .sort_values(["year", "zone"])
            .reset_index(drop=True)
        )
        grouped_df = (
            zone_df.groupby(["year", "zone_group"], as_index=False)["dc_load_mw"]
            .sum()
            .sort_values(["year", "zone_group"])
            .reset_index(drop=True)
        )

    total_df = pd.DataFrame(total_records).sort_values("year").reset_index(drop=True)
    return total_df, regional_df, grouped_df


def generate_eer_public_projection_csvs(
    workbook_path,
    zone_gpkg_path,
    output_dir,
    years=EER_PUBLIC_YEARS,
    scenario_column=EER_PUBLIC_SCENARIO,
):
    """Generate reVeal-compatible CSVs from the public EER workbook."""
    workbook_path = Path(workbook_path)
    zone_gpkg_path = Path(zone_gpkg_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    final_energy_rows = read_xlsx_sheet_records(
        workbook_path, "Final energy demand", header_marker="Sector"
    )
    mapping_rows = read_xlsx_sheet_records(
        workbook_path, "Mapping zone to county", header_marker="county"
    )
    zone_groups_df = gpd.read_file(zone_gpkg_path)

    state_zone_weights = build_state_zone_weights(mapping_rows, zone_groups_df)
    total_df, regional_df, grouped_df = build_eer_public_projection_frames(
        final_energy_rows,
        state_zone_weights,
        years=years,
        scenario_column=scenario_column,
    )

    slug = scenario_column.lower().replace(" ", "_")
    total_path = output_dir / f"eer_public_{slug}_national.csv"
    regional_path = output_dir / f"eer_public_{slug}_regional.csv"
    grouped_path = output_dir / f"eer_public_{slug}_region_groups.csv"
    total_df.to_csv(total_path, index=False)
    regional_df.to_csv(regional_path, index=False)
    grouped_df.to_csv(grouped_path, index=False)

    return total_path, regional_path, grouped_path


def _normalized_projection_columns(columns):
    """Normalize projection CSV columns by dropping synthetic index columns."""
    return [str(column) for column in columns if not str(column).startswith("Unnamed:")]


def _read_csv_columns(csv_path):
    """Read only the header row from a CSV file."""
    csv_path = Path(csv_path)
    return _normalized_projection_columns(pd.read_csv(csv_path, nrows=0).columns)


def assess_public_eer_drop_in_compatibility(
    final_energy_columns,
    mapping_columns,
    total_anchor_columns,
    regional_anchor_columns,
    generated_total_columns=(),
    generated_regional_columns=(),
    source_format="xlsx",
):
    """Assess whether the public EER workbook is a direct replacement for fixture CSVs."""
    final_energy_columns = [str(column) for column in final_energy_columns]
    mapping_columns = [str(column) for column in mapping_columns]
    total_anchor_columns = _normalized_projection_columns(total_anchor_columns)
    regional_anchor_columns = _normalized_projection_columns(regional_anchor_columns)
    generated_total_columns = _normalized_projection_columns(generated_total_columns)
    generated_regional_columns = _normalized_projection_columns(generated_regional_columns)

    missing_total_columns = [
        column for column in total_anchor_columns if column not in final_energy_columns
    ]
    missing_regional_columns = [
        column for column in regional_anchor_columns if column not in final_energy_columns
    ]

    reasons = []
    if source_format.lower() != "csv":
        reasons.append(
            "The public source is an XLSX workbook while the downscale configs reference "
            "CSV load-projection files."
        )
    if missing_total_columns:
        reasons.append(
            "The `Final energy demand` sheet is missing required total projection columns: "
            f"{missing_total_columns}."
        )
    if missing_regional_columns:
        reasons.append(
            "The `Final energy demand` sheet is missing required grouped regional projection "
            f"columns: {missing_regional_columns}."
        )
    if "zone_group" in regional_anchor_columns and "zone_group" not in final_energy_columns:
        reasons.append(
            "`zone_group` is not present directly in the workbook; grouped regional outputs "
            "require the county-to-zone mapping sheet plus the repo's regional geometry."
        )

    direct_total_drop_in = not missing_total_columns and source_format.lower() == "csv"
    direct_regional_drop_in = not missing_regional_columns and source_format.lower() == "csv"

    return {
        "drop_in_replacement": direct_total_drop_in and direct_regional_drop_in,
        "direct_total_drop_in": direct_total_drop_in,
        "direct_regional_drop_in": direct_regional_drop_in,
        "final_energy_columns": final_energy_columns,
        "mapping_columns": mapping_columns,
        "total_anchor_columns": total_anchor_columns,
        "regional_anchor_columns": regional_anchor_columns,
        "missing_total_columns": missing_total_columns,
        "missing_regional_columns": missing_regional_columns,
        "generated_total_schema_match": (
            generated_total_columns == total_anchor_columns if generated_total_columns else None
        ),
        "generated_regional_schema_match": (
            generated_regional_columns == regional_anchor_columns
            if generated_regional_columns
            else None
        ),
        "reasons": reasons,
    }


def assess_public_eer_drop_in_compatibility_from_paths(
    workbook_path,
    total_anchor_path,
    regional_anchor_path,
    generated_total_path=None,
    generated_regional_path=None,
):
    """Assess drop-in compatibility using the staged workbook and anchor CSV paths."""
    workbook_path = Path(workbook_path)
    final_energy_rows = read_xlsx_sheet_records(
        workbook_path, "Final energy demand", header_marker="Sector"
    )
    mapping_rows = read_xlsx_sheet_records(
        workbook_path, "Mapping zone to county", header_marker="county"
    )
    if not final_energy_rows:
        raise ValueError("No rows found in `Final energy demand` sheet")
    if not mapping_rows:
        raise ValueError("No rows found in `Mapping zone to county` sheet")

    generated_total_columns = ()
    generated_regional_columns = ()
    if generated_total_path is not None:
        generated_total_columns = _read_csv_columns(generated_total_path)
    if generated_regional_path is not None:
        generated_regional_columns = _read_csv_columns(generated_regional_path)

    return assess_public_eer_drop_in_compatibility(
        final_energy_columns=final_energy_rows[0].keys(),
        mapping_columns=mapping_rows[0].keys(),
        total_anchor_columns=_read_csv_columns(total_anchor_path),
        regional_anchor_columns=_read_csv_columns(regional_anchor_path),
        generated_total_columns=generated_total_columns,
        generated_regional_columns=generated_regional_columns,
        source_format=workbook_path.suffix.lstrip("."),
    )


def _format_drop_in_assessment(assessment):
    """Render the EER drop-in assessment as human-readable lines."""
    lines = [
        f"drop_in_replacement {assessment['drop_in_replacement']}",
        f"direct_total_drop_in {assessment['direct_total_drop_in']}",
        f"direct_regional_drop_in {assessment['direct_regional_drop_in']}",
        f"missing_total_columns {assessment['missing_total_columns']}",
        f"missing_regional_columns {assessment['missing_regional_columns']}",
    ]
    if assessment["generated_total_schema_match"] is not None:
        lines.append(
            f"generated_total_schema_match {assessment['generated_total_schema_match']}"
        )
    if assessment["generated_regional_schema_match"] is not None:
        lines.append(
            "generated_regional_schema_match "
            f"{assessment['generated_regional_schema_match']}"
        )
    for reason in assessment["reasons"]:
        lines.append(f"reason {reason}")
    return lines


def build_fema_nfhl_download_url(dfirm_id, state, county, file_name):
    """Build a direct FEMA NFHL ZIP download URL from inventory table fields."""
    params = {
        "DFIRMID": str(dfirm_id).strip(),
        "state": str(state).strip().upper(),
        "county": str(county).strip().upper(),
        "fileName": str(file_name).strip(),
    }
    missing = [key for key, value in params.items() if not value]
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"Missing FEMA NFHL URL fields: {missing_list}")

    return f"{FEMA_NFHL_DOWNLOAD_BASE_URL}?{urlencode(params, quote_via=quote)}"


def _resolve_download_filename(download_url, dataset_id):
    """Resolve a stable local filename for a representative download URL."""
    parsed = urlparse(download_url)
    query_params = {
        key.lower(): values for key, values in parse_qs(parsed.query).items() if values
    }
    for key in ("filename", "name"):
        if key in query_params:
            return Path(query_params[key][0]).name

    path_name = Path(parsed.path).name
    if path_name:
        return path_name

    return f"{dataset_id}_download"


def _load_json_from_url(url):
    """Load a JSON payload from a public URL."""
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


def _default_ribits_checkpoint_path(output_path):
    """Return the default checkpoint path for a RIBITS snapshot file."""
    output_path = Path(output_path)
    return output_path.with_name(f"{output_path.name}.checkpoint.json")


def _write_ribits_snapshot(output_path, snapshot):
    """Persist the current RIBITS snapshot state to disk."""
    output_path = Path(output_path)
    output_path.write_text(json.dumps(snapshot, indent=2))
    return output_path


def _write_ribits_checkpoint(checkpoint_path, checkpoint):
    """Persist the resumable RIBITS checkpoint state to disk."""
    checkpoint_path = Path(checkpoint_path)
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text(json.dumps(checkpoint, indent=2))
    return checkpoint_path


def _normalize_ribits_snapshot_state(
    *,
    list_url,
    filters,
    include_service_area,
    include_footprint,
    include_contacts,
    include_ledger,
    consumer_email,
    bank_ids,
    detail_items,
):
    """Build the persisted snapshot payload used for both partial and final output."""
    return {
        "source": "RIBITS public webservices",
        "list_url": list_url,
        "filters": dict(filters or {}),
        "detail_options": {
            "include_service_area": bool(include_service_area),
            "include_footprint": bool(include_footprint),
            "include_contacts": bool(include_contacts),
            "include_ledger": bool(include_ledger),
            "consumer_email": consumer_email,
        },
        "list_item_count": len(bank_ids),
        "item_count": len(detail_items),
        "items": detail_items,
    }


def _load_ribits_checkpoint(checkpoint_path):
    """Load a persisted RIBITS checkpoint file if one exists."""
    checkpoint_path = Path(checkpoint_path)
    if not checkpoint_path.exists():
        return None
    return json.loads(checkpoint_path.read_text())


def build_ribits_bank_site_list_url(filters=None, consumer_email=None):
    """Build the documented public RIBITS bank-site list webservice URL."""
    query_obj = dict(filters or {})
    if consumer_email:
        query_obj["webconsumer_email"] = str(consumer_email).strip()

    if not query_obj:
        return RIBITS_BANK_SITE_LIST_URL

    query_text = json.dumps(query_obj, separators=(",", ":"))
    return f"{RIBITS_BANK_SITE_LIST_URL}?q={quote(query_text, safe='{}\":,')}"


def build_ribits_bank_site_data_url(
    bank_id,
    show_service_area=True,
    show_footprint=True,
    show_contacts=False,
    show_ledger=False,
    consumer_email=None,
):
    """Build the documented public RIBITS bank-site detail webservice URL."""
    query_obj = {"bank_id": int(bank_id)}
    if show_service_area:
        query_obj["show_service_area"] = "Yes"
    if show_footprint:
        query_obj["show_footprint"] = "Yes"
    if show_contacts:
        query_obj["show_contacts"] = "Yes"
    if show_ledger:
        query_obj["show_ledger"] = "Yes"
    if consumer_email:
        query_obj["webconsumer_email"] = str(consumer_email).strip()

    query_text = json.dumps(query_obj, separators=(",", ":"))
    return f"{RIBITS_BANK_SITE_DATA_URL}?q={quote(query_text, safe='{}\":,')}"


def download_ribits_bank_site_snapshot(
    output_path,
    filters=None,
    limit=None,
    include_service_area=True,
    include_footprint=True,
    include_contacts=False,
    include_ledger=False,
    consumer_email=None,
    checkpoint_path=None,
    resume=False,
):
    """Download a repo-local RIBITS bank/site snapshot through the public webservices."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path = (
        Path(checkpoint_path)
        if checkpoint_path is not None
        else _default_ribits_checkpoint_path(output_path)
    )

    if limit is not None:
        limit = int(limit)
        if limit < 1:
            raise ValueError("limit must be at least 1 when provided")

    filters = dict(filters or {})
    list_url = build_ribits_bank_site_list_url(filters=filters, consumer_email=consumer_email)
    detail_options = {
        "include_service_area": bool(include_service_area),
        "include_footprint": bool(include_footprint),
        "include_contacts": bool(include_contacts),
        "include_ledger": bool(include_ledger),
        "consumer_email": consumer_email,
    }
    label = "RIBITS bank/site snapshot"

    checkpoint = _load_ribits_checkpoint(checkpoint_path) if resume else None
    if checkpoint is not None:
        if checkpoint.get("list_url") != list_url:
            raise ValueError("Existing RIBITS checkpoint does not match the current filters")
        if checkpoint.get("detail_options") != detail_options:
            raise ValueError(
                "Existing RIBITS checkpoint does not match the current detail options"
            )
        bank_ids = [int(bank_id) for bank_id in checkpoint.get("bank_ids", [])]
        detail_items = list(checkpoint.get("items", []))
        next_index = int(checkpoint.get("next_index", 0))
        _emit_progress(f"Resuming {label} from item {next_index + 1} of {len(bank_ids)}")
    else:
        _emit_progress(f"Starting {label}")
        list_payload = _load_json_from_url(list_url)
        list_items = list_payload.get("ITEMS") or list_payload.get("items") or []
        if limit is not None:
            list_items = list_items[:limit]
        bank_ids = [int(item.get("BANK_ID")) for item in list_items if item.get("BANK_ID") is not None]
        detail_items = []
        next_index = 0

    total_items = len(bank_ids)
    if total_items == 0:
        snapshot = _normalize_ribits_snapshot_state(
            list_url=list_url,
            filters=filters,
            include_service_area=include_service_area,
            include_footprint=include_footprint,
            include_contacts=include_contacts,
            include_ledger=include_ledger,
            consumer_email=consumer_email,
            bank_ids=bank_ids,
            detail_items=detail_items,
        )
        _write_ribits_snapshot(output_path, snapshot)
        if checkpoint_path.exists():
            checkpoint_path.unlink()
        _emit_progress(f"Completed {label}")
        return output_path

    try:
        for index in range(next_index, total_items):
            bank_id = bank_ids[index]
            detail_url = build_ribits_bank_site_data_url(
                bank_id,
                show_service_area=include_service_area,
                show_footprint=include_footprint,
                show_contacts=include_contacts,
                show_ledger=include_ledger,
                consumer_email=consumer_email,
            )
            detail_payload = _load_json_from_url(detail_url)
            detail_records = detail_payload.get("ITEMS") or detail_payload.get("items") or []
            if detail_records:
                detail_items.append(detail_records[0])

            snapshot = _normalize_ribits_snapshot_state(
                list_url=list_url,
                filters=filters,
                include_service_area=include_service_area,
                include_footprint=include_footprint,
                include_contacts=include_contacts,
                include_ledger=include_ledger,
                consumer_email=consumer_email,
                bank_ids=bank_ids,
                detail_items=detail_items,
            )
            _write_ribits_snapshot(output_path, snapshot)
            _write_ribits_checkpoint(
                checkpoint_path,
                {
                    "list_url": list_url,
                    "filters": filters,
                    "detail_options": detail_options,
                    "bank_ids": bank_ids,
                    "next_index": index + 1,
                    "items": detail_items,
                },
            )
            _emit_progress(f"{label}: {index + 1}/{total_items} bank sites processed")
    except KeyboardInterrupt:
        _emit_progress(
            f"Stopped {label} at step {min(next_index + len(detail_items) + 1, total_items)}/{total_items}. Rerun with --resume to continue."
        )
        raise

    if checkpoint_path.exists():
        checkpoint_path.unlink()
    _emit_progress(f"Completed {label}")
    return output_path


def _write_manual_dataset_note(output_path, spec, download_url):
    """Write the local note that explains how a manual dataset is acquired."""
    manual_text = (
        f"dataset_id: {spec.dataset_id}\n"
        f"landing_page: {spec.landing_page}\n"
        f"notes: {spec.notes}\n"
    )
    if download_url is not None:
        manual_text += f"download_url: {download_url}\n"
    if spec.access_urls:
        manual_text += "access_urls:\n"
        for access_url in spec.access_urls:
            manual_text += f"- {access_url}\n"
    output_path.write_text(manual_text)


def list_public_datasets():
    """Return the available public dataset specifications."""
    return PUBLIC_DATASET_CATALOG


def _normalize_optional_text(value):
    """Normalize a possibly empty text value."""
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _normalize_data_center_status(value):
    """Normalize source-specific status values to a small common vocabulary."""
    text = _normalize_optional_text(value)
    if text is None:
        return "unknown"

    normalized = text.lower().replace("-", "_").replace(" ", "_")
    status_map = {
        "existing": "existing",
        "operating": "existing",
        "operational": "existing",
        "active": "existing",
        "in_service": "existing",
        "planned": "planned",
        "proposed": "planned",
        "announced": "planned",
        "permitted": "planned",
        "permit": "planned",
        "under_construction": "under_construction",
        "construction": "under_construction",
        "being_built": "under_construction",
    }
    return status_map.get(normalized, "unknown")


def _empty_data_center_gdf():
    """Return an empty baseline GeoDataFrame with the expected columns."""
    return gpd.GeoDataFrame(
        pd.DataFrame(columns=DATA_CENTER_BASELINE_COLUMNS),
        geometry="geometry",
        crs="EPSG:4326",
    )


def _osm_element_is_data_center(tags):
    """Check whether an OSM element looks like a data center feature."""
    normalized = {
        str(key).lower(): str(value).strip().lower()
        for key, value in (tags or {}).items()
    }
    candidate_keys = (
        "building",
        "construction",
        "proposed",
        "office",
        "landuse",
        "industrial",
        "man_made",
    )
    if any(normalized.get(key) == "data_center" for key in candidate_keys):
        return True
    return any(value == "data_center" for value in normalized.values())


def _extract_osm_lat_lon(element):
    """Extract latitude and longitude from an OSM element or its center."""
    if "lat" in element and "lon" in element:
        return float(element["lat"]), float(element["lon"])

    center = element.get("center") or {}
    if "lat" in center and "lon" in center:
        return float(center["lat"]), float(center["lon"])

    return None, None


def _infer_osm_site_status(tags):
    """Infer an OSM site's lifecycle state from common tag patterns."""
    normalized = {
        str(key).lower(): str(value).strip().lower()
        for key, value in (tags or {}).items()
    }
    if normalized.get("construction") == "data_center" or normalized.get("building") == "construction":
        return "under_construction"
    if normalized.get("proposed") == "data_center" or normalized.get("building") == "proposed":
        return "planned"
    return "existing"


def _normalize_name_key(value):
    """Build a stable comparison key for site names."""
    text = _normalize_optional_text(value)
    if text is None:
        return None
    return " ".join(text.lower().split())


def _parse_wikidata_entity_id(item_value):
    """Extract a QID from a Wikidata entity URL or bare value."""
    text = _normalize_optional_text(item_value)
    if text is None:
        return None
    return text.rstrip("/").split("/")[-1]


def _parse_wikidata_point(point_value):
    """Parse a Wikidata point literal of the form ``Point(lon lat)``."""
    text = _normalize_optional_text(point_value)
    if text is None or not text.startswith("Point(") or not text.endswith(")"):
        return None, None

    lon_text, lat_text = text[6:-1].split()
    return float(lat_text), float(lon_text)


def _coerce_json_sequence(value):
    """Coerce a nested JSON value into a list of records."""
    if value is None:
        return []
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict) and all(str(key).isdigit() for key in value):
        return [value[key] for key in sorted(value, key=lambda item: int(item))]
    return []


def _empty_power_line_gdf():
    """Return an empty GeoDataFrame with the expected power-line columns."""
    return gpd.GeoDataFrame(
        pd.DataFrame(columns=POWER_LINE_BASELINE_COLUMNS),
        geometry="geometry",
        crs="EPSG:4326",
    )


def _empty_substation_gdf():
    """Return an empty GeoDataFrame with the expected substation columns."""
    return gpd.GeoDataFrame(
        pd.DataFrame(columns=SUBSTATION_BASELINE_COLUMNS),
        geometry="geometry",
        crs="EPSG:4326",
    )


def _empty_fiber_route_gdf():
    """Return an empty GeoDataFrame with the expected fiber-route columns."""
    return gpd.GeoDataFrame(
        pd.DataFrame(columns=FIBER_ROUTE_BASELINE_COLUMNS),
        geometry="geometry",
        crs="EPSG:4326",
    )


def _empty_gas_service_territory_gdf():
    """Return an empty GeoDataFrame with the expected gas-territory columns."""
    return gpd.GeoDataFrame(
        pd.DataFrame(columns=GAS_SERVICE_TERRITORY_COLUMNS),
        geometry="geometry",
        crs="EPSG:4326",
    )


def _empty_land_value_gdf():
    """Return an empty GeoDataFrame with the expected land-value columns."""
    return gpd.GeoDataFrame(
        pd.DataFrame(columns=LAND_VALUE_PROXY_COLUMNS),
        geometry="geometry",
        crs="EPSG:4326",
    )


def _empty_construction_cost_gdf():
    """Return an empty GeoDataFrame with the expected construction-cost columns."""
    return gpd.GeoDataFrame(
        pd.DataFrame(columns=CONSTRUCTION_COST_PROXY_COLUMNS),
        geometry="geometry",
        crs="EPSG:4326",
    )


def _osm_element_is_power_line(tags):
    """Check whether an OSM element looks like transmission-style linework."""
    normalized = {
        str(key).lower(): str(value).strip().lower()
        for key, value in (tags or {}).items()
    }
    return normalized.get("power") in {"line", "minor_line", "cable"}


def _osm_element_is_substation(tags):
    """Check whether an OSM element looks like a substation feature."""
    normalized = {
        str(key).lower(): str(value).strip().lower()
        for key, value in (tags or {}).items()
    }
    return normalized.get("power") == "substation" or "substation" in normalized


def _osm_element_is_fiber_line(tags):
    """Check whether an OSM element looks like route-like telecom or fiber linework."""
    normalized = {
        str(key).lower(): str(value).strip().lower()
        for key, value in (tags or {}).items()
    }

    direct_pairs = (
        ("man_made", {"communications_line", "communication_line"}),
        ("telecom", {"line", "fiber", "fibre", "fiber_optic", "fibre_optic"}),
        ("communication", {"line"}),
        ("cable", {"fiber_optic", "fibre_optic", "optical_fiber", "optical_fibre"}),
    )
    if any(normalized.get(key) in values for key, values in direct_pairs):
        return True

    return any(
        any(token in text for token in ("fiber", "fibre"))
        for text in tuple(normalized.keys()) + tuple(normalized.values())
    )


def _pick_route_tag(tags):
    """Pick a short descriptive route tag from OSM telecom tags."""
    normalized = {
        str(key).lower(): str(value).strip().lower()
        for key, value in (tags or {}).items()
    }
    for key in (
        "man_made",
        "telecom",
        "communication",
        "cable",
        "communication:fibre",
        "communication:fiber",
    ):
        if key in normalized:
            return f"{key}={normalized[key]}"
    return None


def _extract_osm_linestring(element):
    """Extract a LineString from an OSM element geometry array."""
    vertices = []
    for vertex in element.get("geometry") or ():
        latitude = vertex.get("lat")
        longitude = vertex.get("lon")
        if latitude is None or longitude is None:
            continue
        vertices.append((float(longitude), float(latitude)))

    if len(vertices) < 2:
        return None

    return LineString(vertices)


def _parse_voltage_values_kv(value):
    """Parse one or more OSM voltage values into kilovolts."""
    text = _normalize_optional_text(value)
    if text is None:
        return []

    normalized = text.lower().replace(",", "")
    numbers = [float(match) for match in re.findall(r"\d+(?:\.\d+)?", normalized)]
    if not numbers:
        return []

    if any(number >= 1000 for number in numbers):
        numbers = [number for number in numbers if number >= 1000]

    has_kv = "kv" in normalized
    values = []
    for number in numbers:
        if number <= 0:
            continue
        if has_kv or number < 1000:
            values.append(number)
        else:
            values.append(number / 1000.0)

    return values


def build_osm_transmission_line_frame(elements, min_voltage_kv=135.0):
    """Normalize an OSM power-line payload into a high-voltage line GeoDataFrame."""
    records = []
    min_voltage_kv = float(min_voltage_kv)

    for element in elements:
        tags = element.get("tags") or {}
        if not _osm_element_is_power_line(tags):
            continue

        geometry = _extract_osm_linestring(element)
        if geometry is None:
            continue

        voltages_kv = _parse_voltage_values_kv(tags.get("voltage"))
        if not voltages_kv:
            continue

        max_voltage_kv = max(voltages_kv)
        if max_voltage_kv < min_voltage_kv:
            continue

        element_type = _normalize_optional_text(element.get("type")) or "element"
        element_id = element.get("id")
        location = (_normalize_optional_text(tags.get("location")) or "").lower()
        records.append(
            {
                "source": "osm",
                "source_id": f"osm:{element_type}/{element_id}",
                "name": _normalize_optional_text(tags.get("name"))
                or f"osm:{element_type}/{element_id}",
                "operator": _normalize_optional_text(tags.get("operator")),
                "power_type": _normalize_optional_text(tags.get("power")),
                "voltage_text": _normalize_optional_text(tags.get("voltage")),
                "max_voltage_kv": max_voltage_kv,
                "is_underground": location == "underground",
                "source_url": f"https://www.openstreetmap.org/{element_type}/{element_id}",
                "geometry": geometry,
            }
        )

    if not records:
        return _empty_power_line_gdf()

    return gpd.GeoDataFrame(pd.DataFrame(records), geometry="geometry", crs="EPSG:4326")


def build_osm_substation_frame(elements):
    """Normalize OSM substation elements into a point GeoDataFrame."""
    records = []
    for element in elements:
        tags = element.get("tags") or {}
        if not _osm_element_is_substation(tags):
            continue

        latitude, longitude = _extract_osm_lat_lon(element)
        if latitude is None or longitude is None:
            continue

        element_type = _normalize_optional_text(element.get("type")) or "element"
        element_id = element.get("id")
        voltages_kv = _parse_voltage_values_kv(tags.get("voltage"))
        records.append(
            {
                "source": "osm",
                "source_id": f"osm:{element_type}/{element_id}",
                "name": _normalize_optional_text(tags.get("name"))
                or f"osm:{element_type}/{element_id}",
                "operator": _normalize_optional_text(tags.get("operator")),
                "substation_type": _normalize_optional_text(tags.get("substation")),
                "voltage_text": _normalize_optional_text(tags.get("voltage")),
                "max_voltage_kv": max(voltages_kv) if voltages_kv else None,
                "latitude": latitude,
                "longitude": longitude,
                "source_url": f"https://www.openstreetmap.org/{element_type}/{element_id}",
            }
        )

    if not records:
        return _empty_substation_gdf()

    data_df = pd.DataFrame(records)
    return gpd.GeoDataFrame(
        data_df,
        geometry=gpd.points_from_xy(data_df["longitude"], data_df["latitude"]),
        crs="EPSG:4326",
    )


def build_osm_fiber_line_frame(elements):
    """Normalize route-like OSM telecom features into a fiber-route proxy layer."""
    records = []
    for element in elements:
        tags = element.get("tags") or {}
        if not _osm_element_is_fiber_line(tags):
            continue

        geometry = _extract_osm_linestring(element)
        if geometry is None:
            continue

        element_type = _normalize_optional_text(element.get("type")) or "element"
        element_id = element.get("id")
        source_id = f"osm:{element_type}/{element_id}"
        records.append(
            {
                "source": "osm",
                "source_id": source_id,
                "name": _normalize_optional_text(tags.get("name")) or source_id,
                "operator": _normalize_optional_text(tags.get("operator")),
                "route_tag": _pick_route_tag(tags),
                "source_url": f"https://www.openstreetmap.org/{element_type}/{element_id}",
                "geometry": geometry,
            }
        )

    if not records:
        return _empty_fiber_route_gdf()

    return gpd.GeoDataFrame(pd.DataFrame(records), geometry="geometry", crs="EPSG:4326")


def _aligned_raster_template(template_raster_path):
    """Read the alignment metadata from a template raster."""
    with rasterio.open(template_raster_path) as src:
        return {
            "height": src.height,
            "width": src.width,
            "transform": src.transform,
            "crs": src.crs,
            "profile": src.profile.copy(),
        }


def _rasterize_geometries(vector_df, template, dtype="uint8", all_touched=True):
    """Rasterize vector geometries onto the template raster grid."""
    if vector_df.crs != template["crs"]:
        vector_df = vector_df.to_crs(template["crs"])

    shapes = [
        (geometry, 1)
        for geometry in vector_df.geometry
        if geometry is not None and not geometry.is_empty
    ]
    if not shapes:
        return np.zeros((template["height"], template["width"]), dtype=dtype)

    return rasterize(
        shapes,
        out_shape=(template["height"], template["width"]),
        transform=template["transform"],
        fill=0,
        all_touched=all_touched,
        dtype=dtype,
    )


def _write_binary_raster(output_path, array, template, dtype="uint8"):
    """Write a binary raster aligned to the template grid."""
    output_path = Path(output_path)
    profile = template["profile"].copy()
    profile.update(count=1, dtype=dtype, nodata=0)
    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(array.astype(dtype), 1)
    return output_path


def _write_proximity_raster(output_path, mask_array, template):
    """Write a proximity raster derived from a binary mask array."""
    if int(mask_array.max()) == 0:
        raise ValueError("Fiber route proxy mask is empty; cannot compute proximity raster")

    geotransform = template["transform"].to_gdal()
    projection = template["crs"].to_wkt() if template["crs"] is not None else ""
    height = template["height"]
    width = template["width"]

    mem_driver = gdal.GetDriverByName("MEM")
    src_ds = mem_driver.Create("", width, height, 1, gdal.GDT_Byte)
    src_ds.SetGeoTransform(geotransform)
    src_ds.SetProjection(projection)
    src_band = src_ds.GetRasterBand(1)
    src_band.WriteArray(mask_array.astype("uint8"))

    dst_ds = mem_driver.Create("", width, height, 1, gdal.GDT_Float32)
    dst_ds.SetGeoTransform(geotransform)
    dst_ds.SetProjection(projection)
    dst_band = dst_ds.GetRasterBand(1)
    dst_band.SetNoDataValue(-9999.0)

    gdal.ComputeProximity(
        src_band,
        dst_band,
        ["VALUES=1", "DISTUNITS=GEO"],
    )

    output_path = Path(output_path)
    gtiff_driver = gdal.GetDriverByName("GTiff")
    output_ds = gtiff_driver.CreateCopy(str(output_path), dst_ds, strict=0)
    output_ds.FlushCache()
    output_ds = None
    dst_ds = None
    src_ds = None
    return output_path


def build_osm_data_center_frame(elements):
    """Normalize OSM data center elements into a point GeoDataFrame."""
    records = []
    for element in elements:
        tags = element.get("tags") or {}
        if not _osm_element_is_data_center(tags):
            continue

        latitude, longitude = _extract_osm_lat_lon(element)
        if latitude is None or longitude is None:
            continue

        element_type = _normalize_optional_text(element.get("type")) or "element"
        element_id = element.get("id")
        source_id = f"osm:{element_type}/{element_id}"
        records.append(
            {
                "source": "osm",
                "source_id": source_id,
                "name": _normalize_optional_text(tags.get("name")) or source_id,
                "operator": _normalize_optional_text(tags.get("operator")),
                "site_status": _infer_osm_site_status(tags),
                "wikidata_id": _parse_wikidata_entity_id(tags.get("wikidata")),
                "source_url": f"https://www.openstreetmap.org/{element_type}/{element_id}",
                "source_note": None,
                "latitude": latitude,
                "longitude": longitude,
            }
        )

    if not records:
        return _empty_data_center_gdf().drop(columns=["baseline_id", "sources", "source_count", "source_ids"])

    data_df = pd.DataFrame(records)
    return gpd.GeoDataFrame(
        data_df,
        geometry=gpd.points_from_xy(data_df["longitude"], data_df["latitude"]),
        crs="EPSG:4326",
    )


def build_wikidata_data_center_frame(bindings):
    """Normalize Wikidata SPARQL bindings into a point GeoDataFrame."""
    records = []
    for binding in bindings:
        wikidata_id = _parse_wikidata_entity_id(binding.get("item", {}).get("value"))
        latitude, longitude = _parse_wikidata_point(binding.get("coord", {}).get("value"))
        if wikidata_id is None or latitude is None or longitude is None:
            continue

        source_id = f"wikidata:{wikidata_id}"
        records.append(
            {
                "source": "wikidata",
                "source_id": source_id,
                "name": _normalize_optional_text(binding.get("itemLabel", {}).get("value")) or source_id,
                "operator": _normalize_optional_text(binding.get("operatorLabel", {}).get("value")),
                "site_status": _normalize_data_center_status(
                    binding.get("statusLabel", {}).get("value")
                )
                if binding.get("statusLabel")
                else "existing",
                "wikidata_id": wikidata_id,
                "source_url": binding.get("item", {}).get("value"),
                "source_note": None,
                "latitude": latitude,
                "longitude": longitude,
            }
        )

    if not records:
        return _empty_data_center_gdf().drop(columns=["baseline_id", "sources", "source_count", "source_ids"])

    data_df = pd.DataFrame(records)
    return gpd.GeoDataFrame(
        data_df,
        geometry=gpd.points_from_xy(data_df["longitude"], data_df["latitude"]),
        crs="EPSG:4326",
    )


def _coerce_manual_data_center_frame(manual_records):
    """Normalize optional manual augmentation records into a point GeoDataFrame."""
    if manual_records is None:
        return _empty_data_center_gdf().drop(columns=["baseline_id", "sources", "source_count", "source_ids"])

    data_df = pd.DataFrame(manual_records).copy()
    if data_df.empty:
        return _empty_data_center_gdf().drop(columns=["baseline_id", "sources", "source_count", "source_ids"])

    required = {"name", "latitude", "longitude", "site_status"}
    missing = required.difference(data_df.columns)
    if missing:
        raise KeyError(f"Manual data center records are missing required columns: {sorted(missing)}")

    data_df["source"] = "manual"
    data_df["source_id"] = [f"manual:{index + 1}" for index in range(len(data_df))]
    data_df["name"] = data_df["name"].map(_normalize_optional_text)
    data_df["operator"] = data_df.get("operator", pd.Series([None] * len(data_df))).map(
        _normalize_optional_text
    )
    data_df["wikidata_id"] = data_df.get(
        "wikidata_id", pd.Series([None] * len(data_df))
    ).map(_parse_wikidata_entity_id)
    data_df["source_url"] = data_df.get(
        "source_url", pd.Series([None] * len(data_df))
    ).map(_normalize_optional_text)
    data_df["source_note"] = data_df.get(
        "source_note", pd.Series([None] * len(data_df))
    ).map(_normalize_optional_text)
    data_df["site_status"] = data_df["site_status"].map(_normalize_data_center_status)
    data_df["latitude"] = data_df["latitude"].astype(float)
    data_df["longitude"] = data_df["longitude"].astype(float)

    return gpd.GeoDataFrame(
        data_df[
            [
                "source",
                "source_id",
                "name",
                "operator",
                "site_status",
                "wikidata_id",
                "source_url",
                "source_note",
                "latitude",
                "longitude",
            ]
        ],
        geometry=gpd.points_from_xy(data_df["longitude"], data_df["latitude"]),
        crs="EPSG:4326",
    )


def _baseline_merge_key(record):
    """Build the deduplication key for a normalized data center record."""
    wikidata_id = _normalize_optional_text(record.get("wikidata_id"))
    if wikidata_id is not None:
        return f"wikidata:{wikidata_id}"

    name_key = _normalize_name_key(record.get("name"))
    if name_key is None:
        return record.get("source_id")

    latitude = round(float(record.get("latitude")), 3)
    longitude = round(float(record.get("longitude")), 3)
    return f"{name_key}|{latitude:.3f}|{longitude:.3f}"


def _pick_preferred_value(group_df, column):
    """Select the first non-empty value using a stable source preference."""
    source_order = {"manual": 0, "wikidata": 1, "osm": 2}
    ordered_df = group_df.assign(_source_rank=group_df["source"].map(source_order).fillna(99))
    ordered_df = ordered_df.sort_values(["_source_rank", "source_id"])
    for value in ordered_df[column]:
        normalized = _normalize_optional_text(value)
        if normalized is not None:
            return normalized
    return None


def build_public_data_center_baseline(osm_df, wikidata_df, manual_records=None):
    """Merge normalized public-source records into a first-pass baseline layer."""
    manual_df = _coerce_manual_data_center_frame(manual_records)
    frames = [frame for frame in (osm_df, wikidata_df, manual_df) if not frame.empty]
    if not frames:
        return _empty_data_center_gdf()

    combined_df = pd.concat(
        [frame.drop(columns=["geometry"]).copy() for frame in frames],
        ignore_index=True,
    )
    combined_df["merge_key"] = combined_df.apply(_baseline_merge_key, axis=1)

    records = []
    for index, (_, group_df) in enumerate(combined_df.groupby("merge_key", sort=True), start=1):
        status = max(
            group_df["site_status"],
            key=lambda value: DATA_CENTER_STATUS_PRIORITY.get(value, -1),
        )
        latitude = group_df["latitude"].mean()
        longitude = group_df["longitude"].mean()
        sources = sorted(set(group_df["source"]))
        records.append(
            {
                "baseline_id": f"dc_{index:05d}",
                "name": _pick_preferred_value(group_df, "name"),
                "operator": _pick_preferred_value(group_df, "operator"),
                "site_status": status,
                "sources": ";".join(sources),
                "source_count": len(sources),
                "source_ids": ";".join(sorted(set(group_df["source_id"]))),
                "wikidata_id": _pick_preferred_value(group_df, "wikidata_id"),
                "source_url": _pick_preferred_value(group_df, "source_url"),
                "source_note": _pick_preferred_value(group_df, "source_note"),
                "latitude": latitude,
                "longitude": longitude,
            }
        )

    baseline_df = pd.DataFrame(records).sort_values(["name", "baseline_id"]).reset_index(drop=True)
    return gpd.GeoDataFrame(
        baseline_df,
        geometry=gpd.points_from_xy(baseline_df["longitude"], baseline_df["latitude"]),
        crs="EPSG:4326",
    )


def generate_public_data_center_baseline(
    osm_payload_path,
    wikidata_payload_path,
    output_dir,
    manual_csv_path=None,
):
    """Generate a first-pass public data center baseline from local source payloads."""
    osm_payload_path = Path(osm_payload_path)
    wikidata_payload_path = Path(wikidata_payload_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    osm_payload = json.loads(osm_payload_path.read_text())
    wikidata_payload = json.loads(wikidata_payload_path.read_text())
    manual_df = pd.read_csv(manual_csv_path) if manual_csv_path is not None else None

    osm_df = build_osm_data_center_frame(_coerce_json_sequence(osm_payload.get("elements")))
    wikidata_df = build_wikidata_data_center_frame(
        _coerce_json_sequence(wikidata_payload.get("results", {}).get("bindings"))
    )
    baseline_gdf = build_public_data_center_baseline(
        osm_df,
        wikidata_df,
        manual_records=manual_df,
    )

    csv_path = output_dir / "public_data_center_baseline.csv"
    gpkg_path = output_dir / "public_data_center_baseline.gpkg"
    baseline_gdf.drop(columns=["geometry"]).to_csv(csv_path, index=False)
    baseline_gdf.to_file(gpkg_path, driver="GPKG")

    return csv_path, gpkg_path


def generate_public_power_infrastructure_baseline(
    line_payload_path,
    substation_payload_path,
    output_dir,
    min_voltage_kv=135.0,
):
    """Generate first-pass public transmission-line and substation baseline layers."""
    line_payload_path = Path(line_payload_path)
    substation_payload_path = Path(substation_payload_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    line_payload = json.loads(line_payload_path.read_text())
    substation_payload = json.loads(substation_payload_path.read_text())

    line_gdf = build_osm_transmission_line_frame(
        _coerce_json_sequence(line_payload.get("elements")),
        min_voltage_kv=min_voltage_kv,
    )
    substation_gdf = build_osm_substation_frame(
        _coerce_json_sequence(substation_payload.get("elements"))
    )

    voltage_slug = int(min_voltage_kv) if float(min_voltage_kv).is_integer() else str(min_voltage_kv).replace(".", "p")
    line_path = output_dir / f"public_transmission_lines_{voltage_slug}kv.gpkg"
    substation_path = output_dir / "public_substations.gpkg"
    line_gdf.to_file(line_path, driver="GPKG")
    substation_gdf.to_file(substation_path, driver="GPKG")

    return line_path, substation_path


def generate_public_fiber_proxy_rasters(
    osm_payload_path,
    availability_vector_path,
    template_raster_path,
    output_dir,
):
    """Generate first-pass public fiber route and availability proxy artifacts."""
    osm_payload_path = Path(osm_payload_path)
    availability_vector_path = Path(availability_vector_path)
    template_raster_path = Path(template_raster_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    osm_payload = json.loads(osm_payload_path.read_text())
    fiber_line_gdf = build_osm_fiber_line_frame(
        _coerce_json_sequence(osm_payload.get("elements"))
    )
    if fiber_line_gdf.empty:
        raise ValueError("No route-like OSM fiber features were found in the input payload")

    availability_gdf = gpd.read_file(availability_vector_path)
    if availability_gdf.empty:
        raise ValueError("The FCC availability vector is empty")

    template = _aligned_raster_template(template_raster_path)
    line_mask = _rasterize_geometries(fiber_line_gdf, template, dtype="uint8")
    availability_mask = _rasterize_geometries(
        availability_gdf,
        template,
        dtype="uint8",
    )

    line_vector_path = output_dir / "public_fiber_route_proxy.gpkg"
    proximity_raster_path = output_dir / "fiber_lines_onshore_proximity.tif"
    availability_raster_path = output_dir / "fiber_availability_binary.tif"

    fiber_line_gdf.to_file(line_vector_path, driver="GPKG")
    _write_proximity_raster(proximity_raster_path, line_mask, template)
    _write_binary_raster(availability_raster_path, availability_mask, template)

    return line_vector_path, proximity_raster_path, availability_raster_path


def build_state_gas_service_territory_frame(manifest_csv_path):
    """Build a merged gas service territory layer from state-by-state extracts."""
    manifest_csv_path = Path(manifest_csv_path)
    manifest_df = pd.read_csv(manifest_csv_path)
    required_columns = {"state", "path"}
    missing_columns = required_columns.difference(manifest_df.columns)
    if missing_columns:
        raise KeyError(
            f"Gas service territory manifest is missing required columns: {sorted(missing_columns)}"
        )

    frames = []
    target_crs = None
    for row in manifest_df.itertuples(index=False):
        state = str(row.state).strip().upper()
        source_path = Path(row.path)
        if not source_path.is_absolute():
            source_path = manifest_csv_path.parent / source_path

        source_gdf = gpd.read_file(source_path)
        if source_gdf.empty:
            continue

        utility_field = _normalize_optional_text(getattr(row, "utility_field", None))
        if utility_field is not None and utility_field not in source_gdf.columns:
            raise KeyError(f"utility_field {utility_field} not found in {source_path}")

        work_gdf = source_gdf[["geometry"]].copy()
        if utility_field is not None:
            work_gdf["utility_name"] = source_gdf[utility_field].map(_normalize_optional_text)
        else:
            work_gdf["utility_name"] = None

        work_gdf["state"] = state
        work_gdf["source_path"] = source_path.as_posix()

        if target_crs is None:
            target_crs = work_gdf.crs or "EPSG:4326"
        if work_gdf.crs != target_crs:
            work_gdf = work_gdf.to_crs(target_crs)

        frames.append(work_gdf)

    if not frames:
        return _empty_gas_service_territory_gdf()

    combined_df = pd.concat(frames, ignore_index=True)
    combined_df["territory_id"] = [f"gas_{index:05d}" for index in range(1, len(combined_df) + 1)]
    combined_gdf = gpd.GeoDataFrame(combined_df, geometry="geometry", crs=target_crs)
    return combined_gdf[
        ["territory_id", "state", "utility_name", "source_path", "geometry"]
    ]


def generate_public_gas_service_territory_baseline(manifest_csv_path, output_dir):
    """Generate a merged public gas service territory layer from state extracts."""
    manifest_csv_path = Path(manifest_csv_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    territory_gdf = build_state_gas_service_territory_frame(manifest_csv_path)
    if territory_gdf.empty:
        raise ValueError("No gas service territory features were found in the manifest inputs")

    gpkg_path = output_dir / "public_gas_service_territories.gpkg"
    summary_csv_path = output_dir / "public_gas_service_territories_state_index.csv"

    territory_gdf.to_file(gpkg_path, driver="GPKG")
    summary_df = (
        territory_gdf.groupby("state", as_index=False)
        .agg(
            territory_count=("territory_id", "count"),
            utility_count=("utility_name", lambda values: values.dropna().nunique()),
        )
        .sort_values("state")
        .reset_index(drop=True)
    )
    summary_df.to_csv(summary_csv_path, index=False)

    return gpkg_path, summary_csv_path


def build_state_water_availability_proxy_tables(
    state_proxy_df,
    state_zone_weights,
    value_column="freshwater_withdrawal_mgd",
):
    """Apportion state water proxy values into EMM zones and zone groups."""
    state_proxy_df = pd.DataFrame(state_proxy_df).copy()
    required_columns = {"state", value_column}
    missing_columns = required_columns.difference(state_proxy_df.columns)
    if missing_columns:
        raise KeyError(
            f"State water proxy input is missing required columns: {sorted(missing_columns)}"
        )

    state_proxy_df["state"] = state_proxy_df["state"].map(
        lambda value: str(value).strip().lower()
    )
    state_proxy_df[value_column] = state_proxy_df[value_column].astype(float)

    merged_df = state_zone_weights.merge(
        state_proxy_df[["state", value_column]],
        on="state",
        how="inner",
        validate="many_to_one",
    )
    if merged_df.empty:
        return (
            pd.DataFrame(columns=["zone", "water_availability_proxy_mgd"]),
            pd.DataFrame(columns=["zone_group", "water_availability_proxy_mgd"]),
        )

    merged_df["water_availability_proxy_mgd"] = merged_df[value_column] * merged_df["weight"]
    zonal_df = (
        merged_df.groupby("zone", as_index=False)["water_availability_proxy_mgd"]
        .sum()
        .sort_values("zone")
        .reset_index(drop=True)
    )
    grouped_df = (
        merged_df.groupby("zone_group", as_index=False)["water_availability_proxy_mgd"]
        .sum()
        .sort_values("zone_group")
        .reset_index(drop=True)
    )

    return zonal_df, grouped_df


def generate_public_water_availability_proxy_features(
    state_proxy_csv_path,
    mapping_workbook_path,
    zone_gpkg_path,
    output_dir,
    value_column="freshwater_withdrawal_mgd",
):
    """Generate a first-pass zonal water-availability proxy from state inputs."""
    state_proxy_csv_path = Path(state_proxy_csv_path)
    mapping_workbook_path = Path(mapping_workbook_path)
    zone_gpkg_path = Path(zone_gpkg_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    state_proxy_df = pd.read_csv(state_proxy_csv_path)
    zone_groups_df = gpd.read_file(zone_gpkg_path)
    mapping_rows = read_xlsx_sheet_records(
        mapping_workbook_path,
        "Mapping zone to county",
        header_marker="county",
    )
    state_zone_weights = build_state_zone_weights(mapping_rows, zone_groups_df)
    zonal_df, _ = build_state_water_availability_proxy_tables(
        state_proxy_df,
        state_zone_weights,
        value_column=value_column,
    )
    if zonal_df.empty:
        raise ValueError("No zonal water proxy values could be derived from the state inputs")

    normalized_state_df = state_proxy_df.copy()
    normalized_state_df["state"] = normalized_state_df["state"].map(
        lambda value: str(value).strip().lower()
    )
    state_output_path = output_dir / "public_water_availability_state_proxy.csv"
    normalized_state_df.to_csv(state_output_path, index=False)

    zone_feature_df = zone_groups_df.copy()
    zone_feature_df["zone"] = zone_feature_df["emm_zone"].map(lambda value: str(value).strip().lower())
    zone_feature_df = zone_feature_df.merge(zonal_df, on="zone", how="inner", validate="one_to_one")
    zone_output_path = output_dir / "public_water_availability_emm_zone.gpkg"
    zone_feature_df.to_file(zone_output_path, driver="GPKG")

    return state_output_path, zone_output_path


def _calc_percentile_rank(values):
    """Compute a mean percentile rank from 0 to 1 for a numeric series."""
    values = pd.Series(values, dtype=float)
    total = len(values)
    if total == 0:
        return pd.Series(dtype=float)

    ranked = []
    for value in values:
        less = float((values < value).sum())
        less_equal = float((values <= value).sum())
        ranked.append((less + less_equal) / (2.0 * total))

    return pd.Series(ranked, index=values.index, dtype=float)


def _normalize_county_id(value, width=None):
    """Normalize a county identifier while preserving leading-zero semantics."""
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    if width is not None and text.isdigit():
        return text.zfill(width)
    return text


def build_county_construction_cost_proxy_frame(
    county_proxy_df,
    county_polygon_path,
    wage_column="construction_worker_mean_wage_usd",
    price_column="regional_price_parity_index",
):
    """Merge county wage and price proxies with county polygons and derive cost scores."""
    county_proxy_df = pd.DataFrame(county_proxy_df).copy()
    required_columns = {"county_id", "state", wage_column, price_column}
    missing_columns = required_columns.difference(county_proxy_df.columns)
    if missing_columns:
        raise KeyError(
            "County construction-cost proxy input is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    county_id_width = max(
        county_proxy_df["county_id"].map(lambda value: len(_normalize_county_id(value))).max(),
        1,
    )
    county_proxy_df["county_id"] = county_proxy_df["county_id"].map(
        lambda value: _normalize_county_id(value, width=county_id_width)
    )
    county_proxy_df["state"] = county_proxy_df["state"].map(
        lambda value: str(value).strip().upper()
    )
    county_proxy_df[wage_column] = county_proxy_df[wage_column].astype(float)
    county_proxy_df[price_column] = county_proxy_df[price_column].astype(float)

    county_gdf = gpd.read_file(county_polygon_path)
    if county_gdf.empty:
        return _empty_construction_cost_gdf()
    if "county_id" not in county_gdf.columns:
        raise KeyError(f"county_id not found in county polygon layer: {county_polygon_path}")

    county_id_width = max(
        county_id_width,
        county_gdf["county_id"].map(lambda value: len(_normalize_county_id(value))).max(),
    )
    county_proxy_df["county_id"] = county_proxy_df["county_id"].map(
        lambda value: _normalize_county_id(value, width=county_id_width)
    )

    county_gdf = county_gdf[["county_id", "geometry"]].copy()
    county_gdf["county_id"] = county_gdf["county_id"].map(
        lambda value: _normalize_county_id(value, width=county_id_width)
    )

    feature_df = county_gdf.merge(
        county_proxy_df[["county_id", "state", wage_column, price_column]],
        on="county_id",
        how="inner",
        validate="one_to_one",
    )
    if feature_df.empty:
        return _empty_construction_cost_gdf()

    feature_df["construction_cost_proxy_score"] = feature_df[wage_column] * (
        feature_df[price_column] / 100.0
    )
    national_mean = float(feature_df["construction_cost_proxy_score"].mean())
    if np.isclose(national_mean, 0.0):
        feature_df["construction_cost_relative_index"] = 0.0
    else:
        feature_df["construction_cost_relative_index"] = (
            feature_df["construction_cost_proxy_score"] / national_mean
        )

    return gpd.GeoDataFrame(feature_df, geometry="geometry", crs=county_gdf.crs)


def build_county_land_value_proxy_frame(
    county_proxy_df,
    county_polygon_path,
    value_column="land_value_proxy_usd_per_acre",
):
    """Merge county proxy values with county polygons and compute a state-relative index."""
    county_proxy_df = pd.DataFrame(county_proxy_df).copy()
    required_columns = {"county_id", "state", value_column}
    missing_columns = required_columns.difference(county_proxy_df.columns)
    if missing_columns:
        raise KeyError(
            f"County land-value proxy input is missing required columns: {sorted(missing_columns)}"
        )

    county_id_width = max(
        county_proxy_df["county_id"].map(lambda value: len(_normalize_county_id(value))).max(),
        1,
    )
    county_proxy_df["county_id"] = county_proxy_df["county_id"].map(
        lambda value: _normalize_county_id(value, width=county_id_width)
    )
    county_proxy_df["state"] = county_proxy_df["state"].map(lambda value: str(value).strip().upper())
    county_proxy_df[value_column] = county_proxy_df[value_column].astype(float)

    county_gdf = gpd.read_file(county_polygon_path)
    if county_gdf.empty:
        return _empty_land_value_gdf()
    if "county_id" not in county_gdf.columns:
        raise KeyError(f"county_id not found in county polygon layer: {county_polygon_path}")

    county_id_width = max(
        county_id_width,
        county_gdf["county_id"].map(lambda value: len(_normalize_county_id(value))).max(),
    )
    county_proxy_df["county_id"] = county_proxy_df["county_id"].map(
        lambda value: _normalize_county_id(value, width=county_id_width)
    )

    county_gdf = county_gdf[["county_id", "geometry"]].copy()
    county_gdf["county_id"] = county_gdf["county_id"].map(
        lambda value: _normalize_county_id(value, width=county_id_width)
    )

    feature_df = county_gdf.merge(
        county_proxy_df[["county_id", "state", value_column]],
        on="county_id",
        how="inner",
        validate="one_to_one",
    )
    if feature_df.empty:
        return _empty_land_value_gdf()

    feature_df["state_land_value_index"] = (
        feature_df.groupby("state", group_keys=False)[value_column]
        .apply(_calc_percentile_rank)
        .astype(float)
    )

    return gpd.GeoDataFrame(feature_df, geometry="geometry", crs=county_gdf.crs)


def _build_area_weighted_zone_feature_frame(source_gdf, zone_gdf, value_columns):
    """Transfer polygon values to zones using overlap-area weighting."""
    source = source_gdf.to_crs(zone_gdf.crs) if source_gdf.crs != zone_gdf.crs else source_gdf
    zone_columns = ["emm_zone", "zone_group", "geometry"]
    intersection_df = gpd.overlay(
        zone_gdf[zone_columns],
        source[[*value_columns, "geometry"]],
        how="intersection",
        keep_geom_type=True,
        make_valid=True,
    )
    if intersection_df.empty:
        raise ValueError("No overlap found between county land-value features and EMM zones")

    intersection_df["_overlap_area"] = intersection_df.geometry.area
    grouped = intersection_df.groupby(["emm_zone", "zone_group"], as_index=False)["_overlap_area"].sum()
    zone_feature_df = zone_gdf[["emm_zone", "zone_group", "geometry"]].copy()

    for column in value_columns:
        weighted = (
            intersection_df.assign(_weighted_value=intersection_df[column] * intersection_df["_overlap_area"])
            .groupby(["emm_zone", "zone_group"], as_index=False)["_weighted_value"]
            .sum()
            .merge(grouped, on=["emm_zone", "zone_group"], how="left")
        )
        weighted[column] = weighted["_weighted_value"] / weighted["_overlap_area"]
        zone_feature_df = zone_feature_df.merge(
            weighted[["emm_zone", "zone_group", column]],
            on=["emm_zone", "zone_group"],
            how="inner",
            validate="one_to_one",
        )

    return gpd.GeoDataFrame(zone_feature_df, geometry="geometry", crs=zone_gdf.crs)


def generate_public_land_value_proxy_features(
    county_proxy_csv_path,
    county_polygon_path,
    zone_gpkg_path,
    output_dir,
    value_column="land_value_proxy_usd_per_acre",
):
    """Generate first-pass county and zonal land-value proxy features."""
    county_proxy_csv_path = Path(county_proxy_csv_path)
    county_polygon_path = Path(county_polygon_path)
    zone_gpkg_path = Path(zone_gpkg_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    county_proxy_df = pd.read_csv(
        county_proxy_csv_path,
        dtype={"county_id": str, "state": str},
    )
    county_feature_df = build_county_land_value_proxy_frame(
        county_proxy_df,
        county_polygon_path,
        value_column=value_column,
    )
    if county_feature_df.empty:
        raise ValueError("No county land-value proxy features were generated from the inputs")

    zone_gdf = gpd.read_file(zone_gpkg_path)
    zone_feature_df = _build_area_weighted_zone_feature_frame(
        county_feature_df,
        zone_gdf,
        value_columns=[value_column, "state_land_value_index"],
    )

    county_output_path = output_dir / "public_land_value_county.gpkg"
    zone_output_path = output_dir / "public_land_value_emm_zone.gpkg"
    county_feature_df.to_file(county_output_path, driver="GPKG")
    zone_feature_df.to_file(zone_output_path, driver="GPKG")

    return county_output_path, zone_output_path


def generate_public_construction_cost_proxy_features(
    county_proxy_csv_path,
    county_polygon_path,
    zone_gpkg_path,
    output_dir,
    wage_column="construction_worker_mean_wage_usd",
    price_column="regional_price_parity_index",
):
    """Generate first-pass county and zonal construction-cost proxy features."""
    county_proxy_csv_path = Path(county_proxy_csv_path)
    county_polygon_path = Path(county_polygon_path)
    zone_gpkg_path = Path(zone_gpkg_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    county_proxy_df = pd.read_csv(
        county_proxy_csv_path,
        dtype={"county_id": str, "state": str},
    )
    county_feature_df = build_county_construction_cost_proxy_frame(
        county_proxy_df,
        county_polygon_path,
        wage_column=wage_column,
        price_column=price_column,
    )
    if county_feature_df.empty:
        raise ValueError(
            "No county construction-cost proxy features were generated from the inputs"
        )

    zone_gdf = gpd.read_file(zone_gpkg_path)
    zone_feature_df = _build_area_weighted_zone_feature_frame(
        county_feature_df,
        zone_gdf,
        value_columns=[
            wage_column,
            price_column,
            "construction_cost_proxy_score",
            "construction_cost_relative_index",
        ],
    )

    county_output_path = output_dir / "public_construction_cost_county.gpkg"
    zone_output_path = output_dir / "public_construction_cost_emm_zone.gpkg"
    county_feature_df.to_file(county_output_path, driver="GPKG")
    zone_feature_df.to_file(zone_output_path, driver="GPKG")

    return county_output_path, zone_output_path


def build_nerc_reserve_margin_table(
    rows=NERC_LTRA_2025_MARGIN_ROWS,
    years=NERC_LTRA_MARGIN_YEARS,
):
    """Build a structured NERC reserve-margin table for the 2025 LTRA horizon."""
    years = tuple(int(year) for year in years)
    margin_df = pd.DataFrame(rows).copy()

    for year in years:
        margin_df[f"margin_headroom_{year}"] = (
            margin_df[f"arm_{year}"] - margin_df[f"rml_{year}"]
        )

    year_suffix = f"{min(years)}_{max(years)}"
    headroom_cols = [f"margin_headroom_{year}" for year in years]
    arm_cols = [f"arm_{year}" for year in years]
    margin_df[f"min_margin_headroom_{year_suffix}"] = margin_df[headroom_cols].min(axis=1)
    margin_df[f"mean_margin_headroom_{year_suffix}"] = margin_df[headroom_cols].mean(axis=1)
    margin_df[f"min_arm_{year_suffix}"] = margin_df[arm_cols].min(axis=1)

    return margin_df.sort_values("assessment_area").reset_index(drop=True)


def build_nerc_emm_zone_feature_frame(
    zone_groups_df,
    margin_table=None,
    crosswalk=NERC_LTRA_EMM_ZONE_CROSSWALK,
):
    """Map NERC reserve-margin values onto the repo's EMM zone geometry."""
    if margin_table is None:
        margin_table = build_nerc_reserve_margin_table()

    required_columns = {"emm_zone", "zone_group", "geometry"}
    missing_columns = required_columns.difference(zone_groups_df.columns)
    if missing_columns:
        raise KeyError(f"Zone geometry is missing required columns: {sorted(missing_columns)}")

    zone_feature_df = zone_groups_df[["emm_zone", "zone_group", "geometry"]].copy()
    zone_feature_df["assessment_area"] = zone_feature_df["emm_zone"].map(crosswalk)

    missing_zones = sorted(zone_feature_df.loc[zone_feature_df["assessment_area"].isna(), "emm_zone"].unique())
    if missing_zones:
        raise ValueError(f"Missing NERC crosswalk entries for EMM zones: {missing_zones}")

    merged_df = zone_feature_df.merge(
        margin_table,
        on="assessment_area",
        how="left",
        validate="many_to_one",
    )
    if merged_df["peak_season"].isna().any():
        missing_areas = sorted(merged_df.loc[merged_df["peak_season"].isna(), "assessment_area"].unique())
        raise ValueError(f"Missing reserve-margin rows for assessment areas: {missing_areas}")

    return gpd.GeoDataFrame(merged_df, geometry="geometry", crs=zone_groups_df.crs)


def build_nerc_grid_margin_feature_frame(grid_df, zone_feature_df):
    """Transfer zone-level NERC reserve-margin values onto a grid by overlap."""
    grid_idx = grid_df.index.name or "_grid_index"
    reset_index_name = grid_df.index.name or "index"
    grid_work_df = grid_df.reset_index().rename(columns={reset_index_name: grid_idx})

    zones = zone_feature_df.to_crs(grid_df.crs) if zone_feature_df.crs != grid_df.crs else zone_feature_df
    zone_columns = [
        column
        for column in zones.columns
        if column not in {"geometry"}
    ]
    categorical_cols = ["emm_zone", "zone_group", "assessment_area", "peak_season"]
    numeric_cols = [column for column in zone_columns if column not in categorical_cols]

    intersection_df = gpd.overlay(
        grid_work_df[[grid_idx, "geometry"]],
        zones[zone_columns + ["geometry"]],
        how="intersection",
        keep_geom_type=True,
        make_valid=True,
    )
    if intersection_df.empty:
        raise ValueError("No overlap found between the input grid and EMM zone features")

    intersection_df["_overlap_area"] = intersection_df.geometry.area
    total_area_df = intersection_df.groupby(grid_idx, as_index=False)["_overlap_area"].sum()

    weighted_frames = [grid_work_df.drop(columns=["geometry"]).copy()]
    for column in numeric_cols:
        weighted = (
            intersection_df.assign(_weighted_value=intersection_df[column] * intersection_df["_overlap_area"])
            .groupby(grid_idx, as_index=False)["_weighted_value"]
            .sum()
            .merge(total_area_df, on=grid_idx, how="left")
        )
        weighted[column] = weighted["_weighted_value"] / weighted["_overlap_area"]
        weighted_frames.append(weighted[[grid_idx, column]])

    dominant_idx = intersection_df.groupby(grid_idx)["_overlap_area"].idxmax()
    dominant_df = intersection_df.loc[dominant_idx, [grid_idx] + categorical_cols].copy()
    weighted_frames.append(dominant_df)

    overlapping_ids = dominant_df[[grid_idx]].drop_duplicates()
    result_df = grid_work_df.merge(overlapping_ids, on=grid_idx, how="inner")
    for frame in weighted_frames[1:]:
        result_df = result_df.merge(frame, on=grid_idx, how="left")

    if result_df[numeric_cols + categorical_cols].isna().any().any():
        raise ValueError("Some grid cells could not be assigned NERC reserve-margin values")

    result_df.set_index(grid_idx, inplace=True)
    result_df.index.name = grid_df.index.name or grid_idx

    return gpd.GeoDataFrame(result_df, geometry="geometry", crs=grid_df.crs)


def generate_nerc_reserve_margin_features(zone_gpkg_path, output_dir, grid_path=None):
    """Generate derived NERC reserve-margin artifacts for reVeal regional geometry."""
    zone_gpkg_path = Path(zone_gpkg_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    margin_df = build_nerc_reserve_margin_table()
    assessment_path = output_dir / "nerc_ltra_2025_assessment_area_margins.csv"
    margin_df.to_csv(assessment_path, index=False)

    zone_groups_df = gpd.read_file(zone_gpkg_path)
    zone_feature_df = build_nerc_emm_zone_feature_frame(zone_groups_df, margin_table=margin_df)
    zone_path = output_dir / "nerc_ltra_2025_emm_zone_margins.gpkg"
    zone_feature_df.to_file(zone_path, driver="GPKG")

    grid_output_path = None
    if grid_path is not None:
        grid_df = gpd.read_file(grid_path)
        grid_feature_df = build_nerc_grid_margin_feature_frame(grid_df, zone_feature_df)
        grid_output_path = output_dir / "nerc_ltra_2025_grid_margins.gpkg"
        grid_feature_df.to_file(grid_output_path, driver="GPKG")

    return assessment_path, zone_path, grid_output_path


def _emit_progress(message):
    """Emit a progress message to stderr for long-running CLI operations."""
    sys.stderr.write(f"{message}\n")
    sys.stderr.flush()


def _read_content_length(headers):
    """Read a response content length when the server provides one."""
    value = headers.get("Content-Length") if headers is not None else None
    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _report_download_progress(label, bytes_downloaded, total_bytes, last_bucket=None):
    """Emit coarse download progress and return the latest reported bucket."""
    if total_bytes is None or total_bytes <= 0:
        _emit_progress(f"{label}: {bytes_downloaded} bytes downloaded")
        return last_bucket

    percent = min(100.0, (bytes_downloaded / total_bytes) * 100.0)
    bucket = int(percent)
    if last_bucket is None or bucket >= last_bucket + 5 or percent >= 100.0:
        _emit_progress(f"{label}: {percent:0.1f}% ({bytes_downloaded}/{total_bytes} bytes)")
        return bucket
    return last_bucket


def _download_with_progress(download_url, output_path, resume=False, chunk_size=1024 * 1024):
    """Download a URL to disk with visible progress and optional HTTP range resume."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    existing_size = output_path.stat().st_size if resume and output_path.exists() else 0
    request = urllib.request.Request(download_url)
    if existing_size > 0:
        request.add_header("Range", f"bytes={existing_size}-")

    label = f"Downloading {output_path.name}"
    _emit_progress(f"Starting {label}")
    if existing_size > 0:
        _emit_progress(f"Resuming {label} from {existing_size} bytes")

    bytes_downloaded = existing_size
    last_bucket = None

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            response_status = getattr(response, "status", None)
            response_length = _read_content_length(getattr(response, "headers", None))
            append_mode = existing_size > 0 and response_status == 206

            if append_mode:
                total_bytes = existing_size + response_length if response_length is not None else None
                file_mode = "ab"
            else:
                total_bytes = response_length
                file_mode = "wb"
                if existing_size > 0:
                    bytes_downloaded = 0

            with output_path.open(file_mode) as handle:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break

                    handle.write(chunk)
                    bytes_downloaded += len(chunk)
                    last_bucket = _report_download_progress(
                        label,
                        bytes_downloaded,
                        total_bytes,
                        last_bucket=last_bucket,
                    )
    except KeyboardInterrupt:
        _emit_progress(
            f"Stopped {label} at {bytes_downloaded} bytes. Rerun with --resume to continue."
        )
        raise

    if last_bucket is None:
        _report_download_progress(label, bytes_downloaded, bytes_downloaded or None)
    _emit_progress(f"Completed {label}")
    return output_path


def _resolve_public_nlcd_representative_paths(repo_root):
    """Return the staged NLCD directory plus the expected TIFF and ZIP payload paths."""
    repo_root = Path(repo_root).resolve()
    raster_dir = repo_root / "external-data/raw/nlcd"
    return (
        raster_dir,
        raster_dir / PUBLIC_NLCD_REPRESENTATIVE_TIF_NAME,
        raster_dir / PUBLIC_NLCD_REPRESENTATIVE_ZIP_NAME,
    )


def _read_public_nlcd_fallback_bounds(repo_root):
    """Read the bounded report-grid extent used for the NLCD WMS fallback."""
    grid_path = Path(repo_root).resolve() / PUBLIC_REPORT_BUNDLE_GRID_PATH
    if not grid_path.exists():
        raise FileNotFoundError(
            "NLCD WMS fallback requires the bounded report grid at "
            f"{grid_path.as_posix()}."
        )

    grid_df = gpd.read_file(grid_path)
    if grid_df.empty:
        raise ValueError("NLCD WMS fallback cannot use an empty bounded report grid")
    if grid_df.crs is None:
        raise ValueError("NLCD WMS fallback requires a CRS on the bounded report grid")

    return grid_df.to_crs(PUBLIC_NLCD_WMS_CRS).total_bounds


def _build_public_nlcd_wms_getmap_url(bounds, width, height):
    """Build one MRLC GetMap request for a bounded NLCD tile."""
    bbox = ",".join(f"{float(value):0.3f}" for value in bounds)
    query = urlencode(
        {
            "service": "WMS",
            "version": "1.1.1",
            "request": "GetMap",
            "layers": PUBLIC_NLCD_WMS_LAYER,
            "time": PUBLIC_NLCD_WMS_TIME,
            "styles": "",
            "format": "image/geotiff",
            "transparent": "false",
            "srs": PUBLIC_NLCD_WMS_CRS,
            "bbox": bbox,
            "width": int(width),
            "height": int(height),
        }
    )
    return f"{PUBLIC_NLCD_WMS_BASE_URL}?{query}"


def _download_public_nlcd_wms_tile(bounds, width, height):
    """Fetch one bounded NLCD WMS tile as a palette-index raster array."""
    request_url = _build_public_nlcd_wms_getmap_url(bounds, width, height)
    with urllib.request.urlopen(request_url, timeout=120) as response:
        payload = response.read()

    with MemoryFile(payload) as memfile:
        with memfile.open() as dataset:
            return dataset.read(1)


def _remap_public_nlcd_wms_indices(index_array):
    """Convert NLCD WMS palette indices into the standard NLCD class codes."""
    unique_values = {int(value) for value in np.unique(index_array).tolist()}
    unknown_values = sorted(unique_values.difference(PUBLIC_NLCD_WMS_INDEX_TO_CLASS))
    if unknown_values:
        raise ValueError(
            "Unexpected NLCD WMS palette indices: "
            f"{unknown_values}"
        )

    lookup = np.zeros(256, dtype=np.uint8)
    for index_value, class_value in PUBLIC_NLCD_WMS_INDEX_TO_CLASS.items():
        lookup[index_value] = class_value
    return lookup[index_array]


def _stage_public_nlcd_wms_fallback(repo_root, force=False):
    """Stage a bounded NLCD TIFF by mosaicking tiled MRLC WMS responses."""
    raster_dir, tif_path, _ = _resolve_public_nlcd_representative_paths(repo_root)
    raster_dir.mkdir(parents=True, exist_ok=True)
    if tif_path.exists() and not force:
        return tif_path

    minx, miny, maxx, maxy = _read_public_nlcd_fallback_bounds(repo_root)
    resolution = float(PUBLIC_NLCD_WMS_FALLBACK_RESOLUTION_M)
    width = max(1, int(math.ceil((maxx - minx) / resolution)))
    height = max(1, int(math.ceil((maxy - miny) / resolution)))
    palette_index_grid = np.zeros((height, width), dtype=np.uint8)
    x_edges = np.linspace(minx, maxx, PUBLIC_NLCD_WMS_FALLBACK_TILE_COLUMNS + 1)
    y_edges = np.linspace(maxy, miny, PUBLIC_NLCD_WMS_FALLBACK_TILE_ROWS + 1)
    tile_count = PUBLIC_NLCD_WMS_FALLBACK_TILE_COLUMNS * PUBLIC_NLCD_WMS_FALLBACK_TILE_ROWS
    tile_number = 0

    for row_index in range(PUBLIC_NLCD_WMS_FALLBACK_TILE_ROWS):
        tile_maxy = float(y_edges[row_index])
        tile_miny = float(y_edges[row_index + 1])
        row_offset = int(round((maxy - tile_maxy) / resolution))
        tile_height = max(1, int(round((tile_maxy - tile_miny) / resolution)))
        if row_index == PUBLIC_NLCD_WMS_FALLBACK_TILE_ROWS - 1:
            tile_height = height - row_offset

        for col_index in range(PUBLIC_NLCD_WMS_FALLBACK_TILE_COLUMNS):
            tile_minx = float(x_edges[col_index])
            tile_maxx = float(x_edges[col_index + 1])
            col_offset = int(round((tile_minx - minx) / resolution))
            tile_width = max(1, int(round((tile_maxx - tile_minx) / resolution)))
            if col_index == PUBLIC_NLCD_WMS_FALLBACK_TILE_COLUMNS - 1:
                tile_width = width - col_offset

            tile_number += 1
            _emit_progress(
                f"Starting NLCD WMS fallback tile {tile_number}/{tile_count}"
            )
            tile_array = _download_public_nlcd_wms_tile(
                (tile_minx, tile_miny, tile_maxx, tile_maxy),
                tile_width,
                tile_height,
            )
            if tile_array.shape != (tile_height, tile_width):
                raise ValueError(
                    "NLCD WMS fallback tile shape mismatch: "
                    f"expected {(tile_height, tile_width)} got {tile_array.shape}"
                )
            palette_index_grid[
                row_offset : row_offset + tile_height,
                col_offset : col_offset + tile_width,
            ] = tile_array
            _emit_progress(
                f"Completed NLCD WMS fallback tile {tile_number}/{tile_count}"
            )

    class_grid = _remap_public_nlcd_wms_indices(palette_index_grid)
    with rasterio.open(
        tif_path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype="uint8",
        crs=PUBLIC_NLCD_WMS_CRS,
        transform=from_origin(minx, maxy, resolution, resolution),
        nodata=0,
    ) as dataset:
        dataset.write(class_grid, 1)
    return tif_path


def _run_with_progress(command_name, operation):
    """Run a CLI operation with coarse start/stop/completed progress reporting."""
    _emit_progress(f"Starting {command_name}")
    try:
        result = operation()
    except KeyboardInterrupt:
        _emit_progress(f"Stopped {command_name}")
        raise
    _emit_progress(f"Completed {command_name}")
    return result


def _run_public_reproduction_smoke(config_path, output_path, repo_root=None):
    """Run the EER smoke-test helper script as one workflow step."""
    repo_root = Path(repo_root or ".").resolve()
    config_path = Path(config_path)
    output_path = Path(output_path)
    script_path = repo_root / "external-data/derived/eer/run_downscale_smoke.py"
    command = [
        sys.executable,
        str(script_path),
        str(config_path),
        "--output",
        str(output_path),
    ]
    completed = subprocess.run(
        command,
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return {
        "output_path": output_path.as_posix(),
        "stdout": [line for line in completed.stdout.strip().splitlines() if line],
    }


def _serialize_workflow_result(result):
    """Normalize workflow step results into JSON-serializable structures."""
    if isinstance(result, Path):
        return result.as_posix()
    if isinstance(result, tuple):
        return [_serialize_workflow_result(item) for item in result]
    if isinstance(result, list):
        return [_serialize_workflow_result(item) for item in result]
    if isinstance(result, dict):
        return {
            key: _serialize_workflow_result(value)
            for key, value in result.items()
        }
    return result


def _write_workflow_status(status_path, status):
    """Persist workflow status to disk."""
    status_path = Path(status_path)
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(json.dumps(status, indent=2))
    return status_path


def _initialize_workflow_status(workflow_name, repo_root, step_ids):
    """Create the initial checkpoint status structure for a workflow."""
    return {
        "workflow": workflow_name,
        "repo_root": Path(repo_root).resolve().as_posix(),
        "completed": False,
        "completed_steps": [],
        "stopped_at_step": None,
        "step_results": {},
        "step_order": list(step_ids),
        "total_steps": len(step_ids),
    }


def _run_checkpointed_workflow(
    workflow_name,
    steps,
    repo_root=".",
    status_path=None,
    default_status_relpath=None,
    resume=False,
    force=False,
):
    """Run a workflow that persists per-step completion state for resume support."""
    repo_root = Path(repo_root).resolve()
    steps = list(steps)
    step_ids = [step["step_id"] for step in steps]

    if status_path is not None:
        status_path = Path(status_path)
    elif default_status_relpath is not None:
        status_path = repo_root / default_status_relpath
    else:
        raise ValueError("Either status_path or default_status_relpath is required")

    if force and status_path.exists() and not resume:
        status_path.unlink()

    if resume and status_path.exists():
        status = json.loads(status_path.read_text())
        existing_workflow = status.get("workflow")
        if existing_workflow and existing_workflow != workflow_name:
            raise ValueError(
                f"Status file {status_path} belongs to workflow {existing_workflow}, not {workflow_name}"
            )
        status.setdefault("workflow", workflow_name)
        status.setdefault("repo_root", repo_root.as_posix())
        status.setdefault("completed", False)
        status.setdefault("completed_steps", [])
        status.setdefault("stopped_at_step", None)
        status.setdefault("step_results", {})
    else:
        status = _initialize_workflow_status(workflow_name, repo_root, step_ids)

    status["step_order"] = list(step_ids)
    status["total_steps"] = len(step_ids)

    _emit_progress(f"Starting {workflow_name}")
    try:
        for index, step in enumerate(steps, start=1):
            step_id = step["step_id"]
            if step_id in status.get("completed_steps", []):
                continue

            status["stopped_at_step"] = step_id
            _write_workflow_status(status_path, status)
            _emit_progress(f"{workflow_name}: step {index}/{len(steps)} {step_id}")
            result = step["runner"]()
            status.setdefault("step_results", {})[step_id] = _serialize_workflow_result(result)
            status.setdefault("completed_steps", []).append(step_id)
            status["stopped_at_step"] = None
            _write_workflow_status(status_path, status)
    except KeyboardInterrupt:
        _emit_progress(
            f"Stopped {workflow_name} at step {status.get('stopped_at_step')}. Rerun with --resume to continue."
        )
        raise

    status["completed"] = True
    status["stopped_at_step"] = None
    _write_workflow_status(status_path, status)
    _emit_progress(f"Completed {workflow_name}")
    return status_path


def _build_public_reproduction_steps(repo_root):
    """Build the bounded public reproduction workflow step list."""
    repo_root = Path(repo_root).resolve()
    return [
        {
            "step_id": "assess_eer_drop_in",
            "runner": lambda: assess_public_eer_drop_in_compatibility_from_paths(
                repo_root / "external-data/unpacked/eer/ADP2024_detailed_output_data.xlsx",
                repo_root / "tests/data/downscale/inputs/load_growth_projections/eer_us-adp-2024-central_national.csv",
                repo_root / "tests/data/downscale/inputs/load_growth_projections/eer_us-adp-2024-central_region_groups.csv",
                generated_total_path=repo_root / "external-data/derived/eer/eer_public_central_high_data_center_national.csv",
                generated_regional_path=repo_root / "external-data/derived/eer/eer_public_central_high_data_center_region_groups.csv",
            ),
        },
        {
            "step_id": "generate_eer_loads",
            "runner": lambda: generate_eer_public_projection_csvs(
                repo_root / "external-data/unpacked/eer/ADP2024_detailed_output_data.xlsx",
                repo_root / "tests/data/downscale/inputs/regions/eer_adp_zones.gpkg",
                repo_root / "external-data/derived/eer",
                scenario_column=EER_PUBLIC_SCENARIO,
            ),
        },
        {
            "step_id": "total_smoke",
            "runner": lambda: _run_public_reproduction_smoke(
                repo_root / "external-data/derived/eer/config_public_total_smoke.json",
                repo_root / "external-data/derived/eer/downscale-smoke/public_eer_total_downscaled.gpkg",
                repo_root=repo_root,
            ),
        },
        {
            "step_id": "regional_smoke",
            "runner": lambda: _run_public_reproduction_smoke(
                repo_root / "external-data/derived/eer/config_public_regional_smoke.json",
                repo_root / "external-data/derived/eer/downscale-smoke/public_eer_regional_downscaled.gpkg",
                repo_root=repo_root,
            ),
        },
        {
            "step_id": "generate_nerc_features",
            "runner": lambda: generate_nerc_reserve_margin_features(
                repo_root / "tests/data/downscale/inputs/regions/eer_adp_zones.gpkg",
                repo_root / "external-data/derived/nerc",
                grid_path=repo_root / "tests/data/downscale/inputs/grid_char_weighted_scores.gpkg",
            ),
        },
    ]


def _build_public_example_bundle_cli_args(bundle_id, repo_root="."):
    """Build absolute CLI args for a staged public example bundle command."""
    repo_root = Path(repo_root).resolve()
    spec = PUBLIC_EXAMPLE_BUNDLE_CATALOG[bundle_id]
    args = [spec.command[3]]
    for arg in spec.command[4:]:
        if isinstance(arg, str) and (arg.startswith("external-data/") or arg.startswith("tests/")):
            args.append((repo_root / arg).as_posix())
        else:
            args.append(arg)
    return args


def _run_public_example_bundle_workflow_step(bundle_id, repo_root=".", force_stage=False):
    """Stage and execute one example-bundle-backed generated public workflow."""
    repo_root = Path(repo_root).resolve()
    spec = PUBLIC_EXAMPLE_BUNDLE_CATALOG[bundle_id]
    bundle_dir = stage_public_example_bundle(bundle_id, repo_root=repo_root, force=force_stage)
    exit_code = main(_build_public_example_bundle_cli_args(bundle_id, repo_root=repo_root))
    if exit_code != 0:
        raise RuntimeError(f"Example workflow failed for bundle_id={bundle_id}")
    output_dir = bundle_dir / "output"
    return {
        "bundle_id": bundle_id,
        "bundle_dir": bundle_dir.as_posix(),
        "outputs": [
            (output_dir / output_name).as_posix() for output_name in spec.expected_outputs
        ],
    }


def _build_public_example_workflow_steps(repo_root, bundle_ids=None, force_stage=False):
    """Build the generated public example-workflow step list."""
    repo_root = Path(repo_root).resolve()
    bundle_ids = list(bundle_ids or PUBLIC_EXAMPLE_BUNDLE_CATALOG.keys())
    unknown_bundle_ids = [bundle_id for bundle_id in bundle_ids if bundle_id not in PUBLIC_EXAMPLE_BUNDLE_CATALOG]
    if unknown_bundle_ids:
        raise KeyError(f"Unknown bundle_id values: {unknown_bundle_ids}")

    steps = []
    for bundle_id in bundle_ids:
        steps.append(
            {
                "step_id": bundle_id,
                "runner": lambda bundle_id=bundle_id: _run_public_example_bundle_workflow_step(
                    bundle_id,
                    repo_root=repo_root,
                    force_stage=force_stage,
                ),
            }
        )
    return steps


def run_public_example_workflows(
    repo_root=".",
    status_path=None,
    resume=False,
    force=False,
    bundle_ids=None,
    force_stage=False,
):
    """Run the generated public example workflows with checkpointed resume support."""
    steps = _build_public_example_workflow_steps(
        repo_root,
        bundle_ids=bundle_ids,
        force_stage=force_stage,
    )
    return _run_checkpointed_workflow(
        "run-public-example-workflows",
        steps,
        repo_root=repo_root,
        status_path=status_path,
        default_status_relpath="external-data/derived/public_example_workflows_status.json",
        resume=resume,
        force=force,
    )


def _collect_workflow_output_paths(result):
    """Extract output paths from a serialized workflow step result when present."""
    if isinstance(result, dict):
        if isinstance(result.get("outputs"), list):
            return [str(value) for value in result["outputs"]]
        if isinstance(result.get("output_path"), str):
            return [result["output_path"]]
        return []
    if isinstance(result, list):
        return [str(value) for value in result if isinstance(value, str)]
    if isinstance(result, str):
        return [result]
    return []


def format_public_workflow_status(status):
    """Render a compact human-readable workflow status summary."""
    workflow_name = status.get("workflow", "unknown")
    completed_steps = status.get("completed_steps", [])
    total_steps = status.get("total_steps")
    if total_steps is None:
        step_order = status.get("step_order", [])
        total_steps = len(step_order) if step_order else len(completed_steps)

    if total_steps and total_steps != len(completed_steps):
        completed_text = f"{'yes' if status.get('completed') else 'no'} ({len(completed_steps)}/{total_steps} steps)"
    else:
        completed_text = f"{'yes' if status.get('completed') else 'no'} ({len(completed_steps)} steps)"

    lines = [
        f"Workflow: {workflow_name}",
        f"Completed: {completed_text}",
    ]

    stopped_at_step = status.get("stopped_at_step")
    if stopped_at_step:
        lines.append(f"Stopped at: {stopped_at_step}")

    step_results = status.get("step_results", {})
    if workflow_name == "run-public-reproduction":
        assessment = step_results.get("assess_eer_drop_in")
        if isinstance(assessment, dict):
            lines.append(
                f"Direct drop-in replacement: {'yes' if assessment.get('drop_in_replacement') else 'no'}"
            )
            if "generated_total_schema_match" in assessment:
                lines.append(
                    "Generated total schema match: "
                    f"{'yes' if assessment.get('generated_total_schema_match') else 'no'}"
                )
            if "generated_regional_schema_match" in assessment:
                lines.append(
                    "Generated regional schema match: "
                    f"{'yes' if assessment.get('generated_regional_schema_match') else 'no'}"
                )
            reasons = assessment.get("reasons") or []
            if reasons:
                lines.append("Gaps:")
                lines.extend(f"- {reason}" for reason in reasons)

    if completed_steps:
        lines.append("Completed steps:")
        for step_id in completed_steps:
            outputs = _collect_workflow_output_paths(step_results.get(step_id))
            if outputs:
                lines.append(f"- {step_id}: {len(outputs)} outputs")
            else:
                lines.append(f"- {step_id}")

    return lines


def summarize_public_workflow_status(status_path):
    """Load and format a public workflow status file."""
    status_path = Path(status_path)
    return format_public_workflow_status(json.loads(status_path.read_text()))


def _default_public_report_bundle_output_dir(repo_root):
    """Return the default output directory for the bounded public report bundle."""
    repo_root = Path(repo_root).resolve()
    return repo_root / "external-data/derived/report-bundle"


def _default_public_report_bundle_status_path(output_dir):
    """Return the default checkpoint status path for the report-bundle workflow."""
    return Path(output_dir) / "public_report_bundle_status.json"


def _default_public_report_bundle_reproduction_status_path(output_dir):
    """Return the nested reproduction status path used by the report-bundle workflow."""
    return Path(output_dir) / "public_reproduction_status.json"


def _write_public_report_bundle_readme(output_dir):
    """Write the local-output policy README for the generated report bundle."""
    output_dir = Path(output_dir)
    readme_path = output_dir / "README.md"
    readme_path.write_text(
        "\n".join(
            [
                "# Bounded Public Report Bundle Outputs",
                "",
                "This directory is the local output target for:",
                "",
                "```bash",
                "python -m reVeal.public_data run-public-report-bundle \\",
                "  --output-dir external-data/derived/report-bundle",
                "```",
                "",
                "The generated bundle artifacts in this directory are intentionally not tracked in Git.",
                "They are report deliverables, but they are regenerated deliverables.",
                "",
                "Current decision: keep the generated HTML, GeoPackages, CSVs, JSON status files, and",
                "Census cache out of source control. If a reviewed snapshot must be shared, publish or",
                "package that snapshot as an explicit release artifact instead of relaxing the ignore",
                "rules for this directory.",
                "",
                "Track the durable inputs and recipes instead:",
                "",
                "- source code and regression tests",
                "- schema-only public evidence manifests under `external-data/manifest/`",
                "- provenance notes under `external-data/provenance/`",
                "- user-facing usage and dataset documentation",
                "",
                "Regenerate the local bundle whenever you need the HTML map with buildout timeline",
                "controls, GeoPackages, manifest,",
                "status JSON, deviation note, ranked CSV, grid-resolution contract, allocation-assumption contract, Baxtel schema contract,",
                "cumulative buildout surfaces, or cached",
                "state-boundary source ZIP. The default run also writes Census GeoLookup miss review",
                "artifacts and a generated",
                "`public_report_census_geography_cache.json` file for Census coordinate GeoLookup",
                "identity enrichment; pass `--no-census-geolookup` to skip that online enrichment.",
                "",
            ]
        )
    )
    return readme_path


def _report_bundle_deviation_lines(repo_root):
    """Return the current bounded-public deviations from the published report."""
    repo_root = Path(repo_root).resolve()
    grid_path = (repo_root / PUBLIC_REPORT_BUNDLE_GRID_PATH).as_posix()
    return [
        "# Public Report Bundle Deviations",
        "",
        "This bundle is a bounded public approximation, not a report-equivalent reproduction.",
        "",
        f"- The execution grid is `{grid_path}` rather than a reproduced nationwide report surface.",
        (
            f"- The current bundle uses baseline year `{PUBLIC_REPORT_BUNDLE_BASELINE_YEAR}` while "
            f"the report narrative frames the scenario around operating data centers in `{PUBLIC_REPORT_BUNDLE_REPORT_BASELINE_YEAR}`."
        ),
        (
            f"- The report-parity temporal contract is now encoded as metadata: the report reference starts from "
            f"`{PUBLIC_REPORT_BUNDLE_REPORT_BASELINE_YEAR}` operating data centers, uses modeled years "
            f"`{list(PUBLIC_REPORT_REFERENCE_MODELED_YEARS)}`, and carries a "
            f"`{PUBLIC_REPORT_REFERENCE_BUILDOUT_HORIZON_YEARS}`-year cumulative buildout horizon through "
            f"`{PUBLIC_REPORT_REFERENCE_TERMINAL_YEAR}`. The current bounded bundle keeps its existing "
            "smoke-test buildout behavior until the 2025 starting-stock source and exact temporal semantics are validated."
        ),
        (
            f"- The current grid priority field is `{PUBLIC_REPORT_BUNDLE_GRID_PRIORITY}`, "
            "not a reproduced Baxtel-trained random-forest output from the published methodology."
        ),
        (
            "- The current feasible-land artifact is a bounded approximation that keeps cells where "
            "`developable_capacity_mw > 0` and flags cells whose staged NLCD water/wetland share across classes "
            "`11`, `90`, and `95` is at least `0.5`; flagged cells remain in the map but are clamped to "
            "0 suitability percentile rather than removed, and this remains a bounded approximation rather than a reproduced exclusion stack from the report."
        ),
        (
            "- The current suitability-percentile artifact ranks the pre-existing `suitability_score` field on "
            "developable cells, then clamps water/wetland-excluded cells to 0 percentile rather than using a trained nationwide model surface."
        ),
        (
            "- The HTML map's buildout timeline mode visualizes bounded cumulative smoke-output artifacts by "
            "source, metric, and year; it is not a report-equivalent 2025-to-2050 buildout animation."
        ),
        "- The current workflow validates downscaling mechanics and schema compatibility, not parity of learned weights or parity of nationwide siting predictions.",
    ]


def _load_public_report_bundle_grid(repo_root):
    """Load the bounded-public execution grid used for report-bundle artifacts."""
    repo_root = Path(repo_root).resolve()
    grid_path = repo_root / PUBLIC_REPORT_BUNDLE_GRID_PATH
    return gpd.read_file(grid_path), grid_path


def _public_report_float(value, digits=6):
    if value is None or pd.isna(value):
        return None
    rounded = round(float(value), digits)
    return int(rounded) if float(rounded).is_integer() else rounded


def _build_public_report_grid_resolution_contract(repo_root, grid_frame=None, grid_path=None):
    """Measure the current execution grid and compare it with the report grid contract."""
    repo_root = Path(repo_root).resolve()
    if grid_frame is None:
        grid_frame, grid_path = _load_public_report_bundle_grid(repo_root)
    elif grid_path is None:
        grid_path = repo_root / PUBLIC_REPORT_BUNDLE_GRID_PATH
    else:
        grid_path = Path(grid_path)

    if grid_frame.empty:
        raise ValueError("Grid-resolution contract requires at least one grid cell")

    source_crs = str(grid_frame.crs) if grid_frame.crs is not None else None
    measurement_frame = grid_frame
    measurement_crs = source_crs
    if grid_frame.crs is not None:
        measurement_frame = grid_frame.to_crs(PUBLIC_REPORT_GRID_MEASUREMENT_CRS)
        measurement_crs = PUBLIC_REPORT_GRID_MEASUREMENT_CRS

    bounds = measurement_frame.geometry.bounds
    widths_km = (bounds.maxx - bounds.minx) / 1000.0
    heights_km = (bounds.maxy - bounds.miny) / 1000.0
    areas_sq_km = measurement_frame.geometry.area / 1_000_000.0
    target_resolution = PUBLIC_REPORT_REFERENCE_GRID_RESOLUTION_KM
    median_width_km = float(widths_km.median())
    median_height_km = float(heights_km.median())
    median_area_sq_km = float(areas_sq_km.median())
    median_equivalent_square_resolution_km = float(np.sqrt(median_area_sq_km))
    width_factor = median_width_km / target_resolution
    height_factor = median_height_km / target_resolution
    resolution_matches = (
        abs(median_width_km - target_resolution) <= PUBLIC_REPORT_GRID_RESOLUTION_TOLERANCE_KM
        and abs(median_height_km - target_resolution)
        <= PUBLIC_REPORT_GRID_RESOLUTION_TOLERANCE_KM
    )
    shape_is_square = (
        abs(median_width_km - median_height_km)
        <= PUBLIC_REPORT_GRID_RESOLUTION_TOLERANCE_KM
    )
    parity_blockers = [
        "report_grid_source_not_recovered",
        "stable_report_cell_id_scheme_missing",
    ]
    if not resolution_matches:
        parity_blockers.insert(0, "current_grid_resolution_mismatch")
    if not shape_is_square:
        parity_blockers.append("current_grid_cell_shape_mismatch")

    cell_count = int(len(grid_frame))
    coarsening_factor = max(width_factor, height_factor)
    return {
        "contract_type": "report-parity-grid-resolution-contract",
        "report_reference": {
            "grid_resolution_km": PUBLIC_REPORT_REFERENCE_GRID_RESOLUTION_KM,
            "grid_cell_width_km": PUBLIC_REPORT_REFERENCE_GRID_RESOLUTION_KM,
            "grid_cell_height_km": PUBLIC_REPORT_REFERENCE_GRID_RESOLUTION_KM,
            "linkedin_aggregation_grid_resolution_km": PUBLIC_REPORT_LINKEDIN_AGGREGATION_GRID_RESOLUTION_KM,
        },
        "current_bundle": {
            "grid_path": Path(grid_path).as_posix(),
            "source_crs": source_crs,
            "measurement_crs": measurement_crs,
            "geometry_types": sorted(grid_frame.geometry.geom_type.dropna().unique().tolist()),
            "stable_cell_id_field": _public_report_cell_key_column(grid_frame),
            "cell_count": cell_count,
            "median_cell_width_km": _public_report_float(median_width_km),
            "median_cell_height_km": _public_report_float(median_height_km),
            "median_cell_area_sq_km": _public_report_float(median_area_sq_km),
            "median_equivalent_square_resolution_km": _public_report_float(
                median_equivalent_square_resolution_km
            ),
            "min_cell_width_km": _public_report_float(widths_km.min()),
            "max_cell_width_km": _public_report_float(widths_km.max()),
            "min_cell_height_km": _public_report_float(heights_km.min()),
            "max_cell_height_km": _public_report_float(heights_km.max()),
            "coarsening_factor_vs_report_width": _public_report_float(width_factor),
            "coarsening_factor_vs_report_height": _public_report_float(height_factor),
            "estimated_report_equivalent_cells_for_current_footprint": int(
                round(cell_count * coarsening_factor * coarsening_factor)
            ),
        },
        "target_grid_contract": {
            "required_resolution_km": PUBLIC_REPORT_REFERENCE_GRID_RESOLUTION_KM,
            "required_grid_description": "unified national 5.76 km by 5.76 km grid from the report methodology",
            "linked_output_aggregation_resolution_km": PUBLIC_REPORT_LINKEDIN_AGGREGATION_GRID_RESOLUTION_KM,
            "required_cell_id_rule": "stable deterministic cell IDs for the recovered report-equivalent national grid",
            "generation_status": "not-generated-current-bundle",
        },
        "parity_status": "value-aligned" if not parity_blockers else "blocked",
        "parity_blockers": parity_blockers,
        "implementation_decision": (
            "Do not subdivide the current execution grid to 5.76 km because that would invent "
            "unvalidated suitability, capacity, and exclusion data. Preserve current stable cell IDs "
            "and treat the report-equivalent national grid as a required parity input until the source "
            "grid or generation rule is recovered."
        ),
    }


def _write_public_report_grid_resolution_contract(repo_root, output_dir):
    """Write the machine-readable grid-resolution contract for the bounded bundle."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    contract_path = output_dir / "public_report_grid_resolution_contract.json"
    contract = _build_public_report_grid_resolution_contract(repo_root)
    contract_path.write_text(json.dumps(contract, indent=2))
    return contract_path


def _coerce_public_report_bool(value):
    """Coerce nullable report flags to plain booleans."""
    if pd.isna(value):
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def _build_public_report_feasible_land_frame(repo_root, frame):
    """Build the bounded feasible-land layer from the current execution grid."""
    if "developable_capacity_mw" not in frame.columns:
        raise KeyError("developable_capacity_mw not found in execution grid")

    feasible = frame[frame["developable_capacity_mw"].fillna(0.0) > 0.0].copy()
    feasible = _annotate_public_report_nlcd_context_frame(repo_root, feasible)
    feasible["water_wetland_excluded"] = feasible["water_wetland_excluded"].map(
        _coerce_public_report_bool
    )
    feasible["is_feasible_land"] = True
    return feasible


def _build_public_report_suitability_percentile_frame(feasible_land):
    """Build the bounded suitability-percentile layer from feasible execution-grid cells."""
    if "suitability_score" not in feasible_land.columns:
        raise KeyError("suitability_score not found in execution grid")

    suitability = feasible_land.copy()
    valid_mask = suitability["suitability_score"].notna()
    suitability["suitability_percentile"] = np.nan
    suitability.loc[valid_mask, "suitability_percentile"] = (
        _calc_percentile_rank(suitability.loc[valid_mask, "suitability_score"]) * 100.0
    ).round(6)
    if "water_wetland_excluded" in suitability.columns:
        exclusion_mask = suitability["water_wetland_excluded"].map(_coerce_public_report_bool)
        suitability.loc[exclusion_mask, "suitability_percentile"] = 0.0
    return suitability


def _build_public_report_place_catalog_frame(place_catalog=None):
    """Normalize the bounded public place catalog used for human-readable cell names."""
    catalog_df = pd.DataFrame(place_catalog or PUBLIC_REPORT_CELL_NAME_CATALOG).copy()
    required_columns = {"name", "kind", "latitude", "longitude", "popularity_score"}
    missing_columns = sorted(required_columns.difference(catalog_df.columns))
    if missing_columns:
        raise KeyError(
            "Public report place catalog is missing required columns: "
            + ", ".join(missing_columns)
        )

    catalog_df["name"] = catalog_df["name"].map(str)
    catalog_df["kind"] = catalog_df["kind"].map(str)
    invalid_kinds = sorted(set(catalog_df[~catalog_df["kind"].isin(["metro", "natural"])] ["kind"]))
    if invalid_kinds:
        raise ValueError(
            "Public report place catalog kinds must be `metro` or `natural`: "
            + ", ".join(invalid_kinds)
        )

    catalog_df["latitude"] = catalog_df["latitude"].astype(float)
    catalog_df["longitude"] = catalog_df["longitude"].astype(float)
    catalog_df["popularity_score"] = catalog_df["popularity_score"].astype(float)
    return catalog_df


def _build_public_report_place_anchor_catalog_frame(place_anchor_catalog=None):
    """Normalize the curated place-anchor catalog used for gateway-style labels."""
    catalog_df = pd.DataFrame(place_anchor_catalog or PUBLIC_REPORT_PLACE_ANCHOR_CATALOG).copy()
    required_columns = {"name", "latitude", "longitude", "county", "state", "popularity_score"}
    missing_columns = sorted(required_columns.difference(catalog_df.columns))
    if missing_columns:
        raise KeyError(
            "Public report place-anchor catalog is missing required columns: "
            + ", ".join(missing_columns)
        )

    for column in ("name", "county", "state"):
        catalog_df[column] = catalog_df[column].map(str)
    catalog_df["latitude"] = catalog_df["latitude"].astype(float)
    catalog_df["longitude"] = catalog_df["longitude"].astype(float)
    catalog_df["popularity_score"] = catalog_df["popularity_score"].astype(float)
    return catalog_df


def _calculate_haversine_distance_miles(latitude_a, longitude_a, latitude_b, longitude_b):
    """Return the great-circle distance between two points in miles."""
    earth_radius_miles = 3958.7613
    latitude_a = math.radians(float(latitude_a))
    latitude_b = math.radians(float(latitude_b))
    delta_latitude = math.radians(float(latitude_b) - float(latitude_a))
    delta_longitude = math.radians(float(longitude_b) - float(longitude_a))
    haversine = (
        math.sin(delta_latitude / 2.0) ** 2
        + math.cos(latitude_a)
        * math.cos(latitude_b)
        * math.sin(delta_longitude / 2.0) ** 2
    )
    haversine = min(1.0, max(0.0, haversine))
    return 2.0 * earth_radius_miles * math.asin(math.sqrt(haversine))


def _calculate_bearing_degrees(latitude_a, longitude_a, latitude_b, longitude_b):
    """Return the initial bearing from point A to point B in degrees."""
    latitude_a = math.radians(float(latitude_a))
    latitude_b = math.radians(float(latitude_b))
    delta_longitude = math.radians(float(longitude_b) - float(longitude_a))
    y_value = math.sin(delta_longitude) * math.cos(latitude_b)
    x_value = (
        math.cos(latitude_a) * math.sin(latitude_b)
        - math.sin(latitude_a) * math.cos(latitude_b) * math.cos(delta_longitude)
    )
    return (math.degrees(math.atan2(y_value, x_value)) + 360.0) % 360.0


def _clean_public_report_text(value):
    """Return a stripped scalar string, or None for missing bounded identity values."""
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _first_public_report_census_layer(geographies, layer_names):
    """Return the first Census geography row from the requested layer aliases."""
    for layer_name in layer_names:
        rows = geographies.get(layer_name)
        if rows:
            return layer_name, rows[0]
    return None, None


def _clean_public_report_census_name(row, field="NAME"):
    """Return a clean Census geography name from one response row."""
    if not row:
        return None
    return _clean_public_report_text(row.get(field)) or _clean_public_report_text(row.get("NAME"))


def _extract_public_report_census_geography_record(payload):
    """Normalize one Census coordinate GeoLookup JSON response into report identity fields."""
    geographies = payload.get("result", {}).get("geographies", {}) if payload else {}
    if not geographies:
        return {
            "census_geolookup_status": "missing",
            "census_place_name": None,
            "census_place_layer": None,
            "census_district_name": None,
            "census_county_name": None,
            "census_state_name": None,
            "census_state_code": None,
            "census_metro_area_name": None,
            "census_combined_statistical_area_name": None,
            "census_urban_area_name": None,
            "census_state_region_name": None,
            "census_national_region_name": None,
            "census_tract_geoid": None,
            "census_block_geoid": None,
        }

    place_layer, place_row = _first_public_report_census_layer(
        geographies,
        ("Incorporated Places", "Census Designated Places"),
    )
    _, county_subdivision_row = _first_public_report_census_layer(
        geographies,
        ("County Subdivisions",),
    )
    _, county_row = _first_public_report_census_layer(geographies, ("Counties",))
    _, state_row = _first_public_report_census_layer(geographies, ("States",))
    _, metro_row = _first_public_report_census_layer(
        geographies,
        ("Metropolitan Statistical Areas",),
    )
    _, combined_statistical_area_row = _first_public_report_census_layer(
        geographies,
        ("Combined Statistical Areas",),
    )
    _, urban_area_row = _first_public_report_census_layer(geographies, ("Urban Areas",))
    _, division_row = _first_public_report_census_layer(geographies, ("Census Divisions",))
    _, region_row = _first_public_report_census_layer(geographies, ("Census Regions",))
    _, tract_row = _first_public_report_census_layer(geographies, ("Census Tracts",))
    _, block_row = _first_public_report_census_layer(
        geographies,
        ("2020 Census Blocks", "Census Blocks"),
    )

    return {
        "census_geolookup_status": "matched",
        "census_place_name": _clean_public_report_census_name(place_row, "BASENAME"),
        "census_place_layer": place_layer,
        "census_district_name": _clean_public_report_census_name(county_subdivision_row),
        "census_county_name": _clean_public_report_census_name(county_row),
        "census_state_name": _clean_public_report_census_name(state_row),
        "census_state_code": _clean_public_report_census_name(state_row, "STUSAB"),
        "census_metro_area_name": _clean_public_report_census_name(metro_row),
        "census_combined_statistical_area_name": _clean_public_report_census_name(
            combined_statistical_area_row
        ),
        "census_urban_area_name": _clean_public_report_census_name(urban_area_row),
        "census_state_region_name": _clean_public_report_census_name(division_row),
        "census_national_region_name": _clean_public_report_census_name(region_row),
        "census_tract_geoid": _clean_public_report_census_name(tract_row, "GEOID"),
        "census_block_geoid": _clean_public_report_census_name(block_row, "GEOID"),
    }


def _build_public_report_census_geolookup_url(latitude, longitude):
    """Build a Census coordinate GeoLookup URL for one WGS84 point."""
    params = urlencode(
        {
            "x": f"{float(longitude):.8f}",
            "y": f"{float(latitude):.8f}",
            "benchmark": PUBLIC_REPORT_CENSUS_GEOLOOKUP_BENCHMARK,
            "vintage": PUBLIC_REPORT_CENSUS_GEOLOOKUP_VINTAGE,
            "layers": ",".join(PUBLIC_REPORT_CENSUS_GEOLOOKUP_LAYERS),
            "format": "json",
        }
    )
    return f"{PUBLIC_REPORT_CENSUS_GEOLOOKUP_URL}?{params}"


def _fetch_public_report_census_geography(latitude, longitude, timeout=30):
    """Fetch one normalized Census coordinate GeoLookup record."""
    request_url = _build_public_report_census_geolookup_url(latitude, longitude)
    with urllib.request.urlopen(request_url, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return _extract_public_report_census_geography_record(payload)


def _public_report_census_cache_key(latitude, longitude):
    """Return a stable coordinate cache key for Census identity enrichment."""
    return f"{float(longitude):.6f},{float(latitude):.6f}"


def _coerce_public_report_coordinate_value(value):
    """Return a numeric coordinate value or None when it is unavailable."""
    try:
        coordinate = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(coordinate):
        return None
    return coordinate


def _load_public_report_census_geography_cache(cache_path):
    """Load cached Census GeoLookup responses from a generated output directory."""
    cache_path = Path(cache_path)
    if not cache_path.exists():
        return {}
    try:
        payload = json.loads(cache_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_public_report_census_geography_cache(cache_path, cache):
    """Persist generated Census GeoLookup cache records."""
    cache_path = Path(cache_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache, indent=2, sort_keys=True))


def _fetch_public_report_census_geographies(
    frame,
    cache_path=None,
    timeout=30,
    max_workers=8,
    progress_label=None,
    progress_interval=100,
    cache_write_interval=25,
):
    """Fetch Census coordinate GeoLookup identity records for report cells with caching."""
    if (
        "latitude" not in frame.columns
        and "longitude" not in frame.columns
        and "geometry" not in frame.columns
    ):
        return None

    lookup_points = None
    if "geometry" in frame.columns:
        lookup_frame = frame
        if isinstance(frame, gpd.GeoDataFrame) and frame.crs is not None and str(frame.crs) != "EPSG:4326":
            lookup_frame = frame.to_crs("EPSG:4326")
        lookup_points = lookup_frame.geometry.representative_point()

    cache = _load_public_report_census_geography_cache(cache_path) if cache_path else {}
    records_by_index = {}
    lookup_requests = []
    for index, row in frame.iterrows():
        latitude = _coerce_public_report_coordinate_value(row.get("latitude"))
        longitude = _coerce_public_report_coordinate_value(row.get("longitude"))
        invalid_coordinate = (
            latitude is None
            or longitude is None
            or not -90.0 <= latitude <= 90.0
            or not -180.0 <= longitude <= 180.0
        )
        if invalid_coordinate and lookup_points is not None:
            latitude = float(lookup_points.loc[index].y)
            longitude = float(lookup_points.loc[index].x)
            invalid_coordinate = False

        if invalid_coordinate:
            records_by_index[index] = _extract_public_report_census_geography_record(None)
            continue

        cache_key = _public_report_census_cache_key(latitude, longitude)
        if cache_key in cache:
            records_by_index[index] = cache[cache_key]
        else:
            lookup_requests.append((index, cache_key, latitude, longitude))

    if progress_label:
        print(
            f"{progress_label}: {len(records_by_index)}/{len(frame)} records available before fetch; "
            f"{len(lookup_requests)} to fetch",
            flush=True,
        )

    def fetch_lookup(request):
        index, cache_key, latitude, longitude = request
        try:
            record = _fetch_public_report_census_geography(
                latitude,
                longitude,
                timeout=timeout,
            )
        except (json.JSONDecodeError, KeyError, OSError, TimeoutError, urllib.error.URLError) as error:
            record = {
                **_extract_public_report_census_geography_record(None),
                "census_geolookup_status": "error",
                "census_geolookup_error": str(error),
            }
        return index, cache_key, record

    completed_fetches = 0
    if lookup_requests:
        worker_count = max(1, min(int(max_workers), len(lookup_requests)))
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_map = {
                executor.submit(fetch_lookup, request): request
                for request in lookup_requests
            }
            for future in as_completed(future_map):
                index, cache_key, record = future.result()
                cache[cache_key] = record
                records_by_index[index] = record
                completed_fetches += 1
                if cache_path and (
                    completed_fetches % int(cache_write_interval) == 0
                    or completed_fetches == len(lookup_requests)
                ):
                    _write_public_report_census_geography_cache(cache_path, cache)
                if progress_label and (
                    completed_fetches % int(progress_interval) == 0
                    or completed_fetches == len(lookup_requests)
                ):
                    print(
                        f"{progress_label}: fetched {completed_fetches}/{len(lookup_requests)}; "
                        f"total ready {len(records_by_index)}/{len(frame)}",
                        flush=True,
                    )

    return pd.DataFrame([records_by_index[index] for index in frame.index], index=frame.index)


def _coerce_public_report_census_geography_frame(census_geographies, index):
    """Align caller-provided Census geography records to the report-cell index."""
    if census_geographies is None:
        return None
    if isinstance(census_geographies, pd.DataFrame):
        census_frame = census_geographies.copy()
    else:
        census_frame = pd.DataFrame(census_geographies)
    if census_frame.empty:
        return None
    if list(census_frame.index) != list(index):
        if len(census_frame) != len(index):
            raise ValueError("Census geography records must align one-to-one with report cells")
        census_frame.index = index
    return census_frame


def _format_public_report_coordinate_label(latitude, longitude):
    """Format a coordinate fallback for public report cell identity fields."""
    return f"{float(latitude):.3f}, {float(longitude):.3f}"


def _format_public_report_state_name(state_code):
    """Return a display state name from an abbreviation or existing state label."""
    state_text = _clean_public_report_text(state_code)
    if state_text is None:
        return None
    return PUBLIC_REPORT_STATE_NAME_BY_CODE.get(state_text.upper(), state_text)


def _select_public_report_state_region(latitude, longitude, state_code):
    """Return a coarse state-region identity layer when the bounded data supports one."""
    state_text = _clean_public_report_text(state_code)
    if state_text is None:
        return None
    state_text = state_text.upper()
    latitude = float(latitude)
    longitude = float(longitude)
    if state_text == "CA":
        return "Southern California" if latitude < 36.5 else "Northern California"
    if state_text == "TX" and latitude < 30.75 and longitude > -98.5:
        return "Texas Gulf Coast"
    if state_text in {"LA", "MS", "AL"} and latitude < 31.5:
        return "Gulf Coast"
    if state_text == "FL":
        return "Florida Peninsula"
    return None


def _select_public_report_national_region(state_code):
    """Return a broad national-region label from state-level identity."""
    state_text = _clean_public_report_text(state_code)
    if state_text is None:
        return None
    return PUBLIC_REPORT_NATIONAL_REGION_BY_STATE.get(state_text.upper())


def _format_bearing_direction(bearing_degrees):
    """Map a numeric bearing to an eight-point cardinal direction label."""
    directions = (
        "North",
        "Northeast",
        "East",
        "Southeast",
        "South",
        "Southwest",
        "West",
        "Northwest",
    )
    return directions[int((float(bearing_degrees) + 22.5) // 45.0) % len(directions)]


def _select_public_report_anchor_place(center_latitude, center_longitude, anchor_catalog_df, base_cell_name=None):
    """Select the nearest curated place anchor used in gateway-style labels."""
    if anchor_catalog_df.empty:
        return {
            "anchor_place_name": None,
            "anchor_place_county": None,
            "anchor_place_state": None,
            "anchor_place_distance_miles": None,
            "anchor_place_direction": None,
        }

    center_latitude = float(center_latitude)
    center_longitude = float(center_longitude)
    candidate_df = anchor_catalog_df.copy()
    candidate_df["distance_degrees"] = np.hypot(
        candidate_df["latitude"] - center_latitude,
        candidate_df["longitude"] - center_longitude,
    )
    selected = None
    mapped_anchor_name = PUBLIC_REPORT_BASE_NAME_ANCHOR_MAP.get(str(base_cell_name)) if pd.notna(base_cell_name) else None
    if mapped_anchor_name is not None:
        mapped_candidates = candidate_df[candidate_df["name"] == mapped_anchor_name]
        if not mapped_candidates.empty:
            selected = mapped_candidates.sort_values(
                ["popularity_score", "name"],
                ascending=[False, True],
            ).iloc[0]

    if selected is None:
        selected = candidate_df.sort_values(
            ["distance_degrees", "popularity_score", "name"],
            ascending=[True, False, True],
        ).iloc[0]

    distance_miles = _calculate_haversine_distance_miles(
        selected["latitude"],
        selected["longitude"],
        center_latitude,
        center_longitude,
    )
    bearing_degrees = _calculate_bearing_degrees(
        selected["latitude"],
        selected["longitude"],
        center_latitude,
        center_longitude,
    )
    return {
        "anchor_place_name": selected["name"],
        "anchor_place_county": selected["county"],
        "anchor_place_state": selected["state"],
        "anchor_place_distance_miles": float(distance_miles),
        "anchor_place_direction": _format_bearing_direction(bearing_degrees),
    }


def _format_public_report_cell_name_from_anchor(row, distance_precision=1, include_coordinates=False):
    """Render a stable human-readable label from place-anchor metadata."""
    anchor_place_name = row.get("anchor_place_name")
    anchor_place_county = row.get("anchor_place_county")
    anchor_place_state = row.get("anchor_place_state")
    anchor_place_distance_miles = row.get("anchor_place_distance_miles")
    anchor_place_direction = row.get("anchor_place_direction")
    base_cell_name = row.get("base_cell_name")

    if (
        pd.notna(anchor_place_name)
        and pd.notna(anchor_place_county)
        and pd.notna(anchor_place_state)
    ):
        if pd.notna(anchor_place_distance_miles) and pd.notna(anchor_place_direction):
            label = (
                f"{float(anchor_place_distance_miles):.{distance_precision}f} miles "
                f"{anchor_place_direction} of {anchor_place_name}, {anchor_place_county}, {anchor_place_state}"
            )
            if pd.notna(base_cell_name) and str(base_cell_name) != str(anchor_place_name):
                label = f"{label} near {base_cell_name}"
        else:
            label = str(anchor_place_name)
            if pd.notna(base_cell_name) and str(base_cell_name) != str(anchor_place_name):
                label = f"{base_cell_name} in {anchor_place_name}"
        if include_coordinates:
            label = f"{label} at {float(row['latitude']):.3f}, {float(row['longitude']):.3f}"
        return label

    if include_coordinates:
        fallback_base = base_cell_name if pd.notna(base_cell_name) else "Unnamed suitability cell"
        return f"{fallback_base} at {float(row['latitude']):.3f}, {float(row['longitude']):.3f}"

    return base_cell_name if pd.notna(base_cell_name) else "Unnamed suitability cell"


def _select_public_report_cell_name_candidate(
    cell_geometry,
    center_latitude,
    center_longitude,
    catalog_df,
    kind,
):
    """Select either the metro or natural candidate used to name one suitability cell."""
    candidate_df = catalog_df[catalog_df["kind"] == kind].copy()
    if candidate_df.empty:
        return {
            "feature_name": None,
            "popularity_score": None,
            "distance_degrees": None,
            "distance_miles": None,
            "match_scope": None,
            "kind": kind,
        }

    center_latitude = float(center_latitude)
    center_longitude = float(center_longitude)
    candidate_df["distance_degrees"] = np.hypot(
        candidate_df["latitude"] - center_latitude,
        candidate_df["longitude"] - center_longitude,
    )
    candidate_df["matched_in_cell"] = False

    if cell_geometry is not None and not cell_geometry.is_empty:
        candidate_df["matched_in_cell"] = candidate_df.apply(
            lambda row: cell_geometry.covers(Point(row["longitude"], row["latitude"])),
            axis=1,
        )

    if candidate_df["matched_in_cell"].any():
        selected = candidate_df[candidate_df["matched_in_cell"]].sort_values(
            ["popularity_score", "distance_degrees", "name"],
            ascending=[False, True, True],
        ).iloc[0]
        match_scope = "in_cell"
    else:
        selected = candidate_df.sort_values(
            ["distance_degrees", "popularity_score", "name"],
            ascending=[True, False, True],
        ).iloc[0]
        match_scope = "nearest_catalog_fallback"

    return {
        "feature_name": selected["name"],
        "popularity_score": float(selected["popularity_score"]),
        "distance_degrees": float(selected["distance_degrees"]),
        "distance_miles": _calculate_haversine_distance_miles(
            selected["latitude"],
            selected["longitude"],
            center_latitude,
            center_longitude,
        ),
        "match_scope": match_scope,
        "kind": kind,
    }


def _select_public_report_cell_name_choice(metro_candidate, natural_candidate):
    """Choose the final human-readable cell name from the bounded label hierarchy."""
    selected = None
    if metro_candidate["feature_name"] is not None and metro_candidate["match_scope"] == "in_cell":
        selected = metro_candidate
    elif metro_candidate["feature_name"] is not None:
        selected = metro_candidate
    elif natural_candidate["feature_name"] is not None:
        selected = natural_candidate

    if selected is None:
        return {
            "cell_name": None,
            "cell_name_basis": None,
            "cell_name_popularity_score": None,
            "cell_name_match_scope": None,
        }
    return {
        "cell_name": selected["feature_name"],
        "cell_name_basis": selected["kind"],
        "cell_name_popularity_score": float(selected["popularity_score"]),
        "cell_name_match_scope": selected["match_scope"],
    }


def _build_public_report_identity_fields(
    center_latitude,
    center_longitude,
    metro_candidate,
    natural_candidate,
    anchor_place,
    census_geography=None,
):
    """Build local and general-audience identity layers from bounded offline inputs."""
    exact_point = _format_public_report_coordinate_label(center_latitude, center_longitude)
    census_geography = census_geography or {}
    has_census_match = census_geography.get("census_geolookup_status") == "matched"
    census_place_name = _clean_public_report_text(census_geography.get("census_place_name"))
    census_district_name = _clean_public_report_text(census_geography.get("census_district_name"))
    census_county_name = _clean_public_report_text(census_geography.get("census_county_name"))
    census_state_name = _clean_public_report_text(census_geography.get("census_state_name"))
    census_state_code = _clean_public_report_text(census_geography.get("census_state_code"))
    census_metro_area_name = _clean_public_report_text(
        census_geography.get("census_metro_area_name")
    )
    census_combined_statistical_area_name = _clean_public_report_text(
        census_geography.get("census_combined_statistical_area_name")
    )
    census_urban_area_name = _clean_public_report_text(census_geography.get("census_urban_area_name"))
    census_state_region_name = _clean_public_report_text(
        census_geography.get("census_state_region_name")
    )
    census_national_region_name = _clean_public_report_text(
        census_geography.get("census_national_region_name")
    )

    anchor_name = _clean_public_report_text(anchor_place.get("anchor_place_name"))
    anchor_county = _clean_public_report_text(anchor_place.get("anchor_place_county"))
    anchor_state = _clean_public_report_text(anchor_place.get("anchor_place_state"))
    state_name = census_state_name or _format_public_report_state_name(anchor_state)
    state_code = census_state_code or anchor_state
    state_region = census_state_region_name or _select_public_report_state_region(
        center_latitude,
        center_longitude,
        state_code,
    )
    national_region = census_national_region_name or _select_public_report_national_region(
        state_code
    )

    metro_name = _clean_public_report_text(metro_candidate.get("feature_name"))
    metro_distance_miles = metro_candidate.get("distance_miles")
    natural_name = _clean_public_report_text(natural_candidate.get("feature_name"))
    natural_distance_miles = natural_candidate.get("distance_miles")
    landmark_name = None
    if natural_name is not None and (
        natural_candidate.get("match_scope") == "in_cell"
        or (
            natural_distance_miles is not None
            and float(natural_distance_miles) <= PUBLIC_REPORT_LANDMARK_RADIUS_MILES
        )
    ):
        landmark_name = natural_name

    census_metro_name = (
        census_metro_area_name or census_combined_statistical_area_name or census_urban_area_name
    )

    anchor_city_name = None if has_census_match else anchor_name

    if census_place_name is not None:
        local_name = census_place_name
        local_layer = "city"
    elif census_district_name is not None:
        local_name = census_district_name
        local_layer = "district"
    elif anchor_city_name is not None:
        local_name = anchor_name
        local_layer = "city"
    elif landmark_name is not None:
        local_name = f"near {landmark_name}"
        local_layer = "landmark_or_address"
    elif census_county_name is not None or anchor_county is not None:
        local_name = census_county_name or anchor_county
        local_layer = "county"
    else:
        local_name = exact_point
        local_layer = "exact_point"

    state_suffix = f", {state_name}" if state_name is not None else ""
    if census_place_name is not None:
        general_name = f"{census_place_name}{state_suffix}"
        general_layer = "city"
    elif census_metro_name is not None:
        general_name = census_metro_name
        general_layer = "metro_area"
    elif metro_name is not None and (
        metro_candidate.get("match_scope") == "in_cell"
        or (
            metro_distance_miles is not None
            and float(metro_distance_miles) <= PUBLIC_REPORT_GENERAL_METRO_RADIUS_MILES
        )
    ):
        if metro_candidate.get("match_scope") == "in_cell":
            general_name = f"{metro_name}{state_suffix}"
            general_layer = "city"
        else:
            general_name = f"near {metro_name}{state_suffix}"
            general_layer = "metro_area"
    elif state_region is not None:
        general_name = state_region
        general_layer = "state_region"
    elif state_name is not None:
        general_name = state_name
        general_layer = "state"
    elif landmark_name is not None:
        general_name = f"near {landmark_name}"
        general_layer = "landmark_or_address"
    else:
        general_name = exact_point
        general_layer = "exact_point"

    identity_stack = [
        {"layer": "exact_point", "name": exact_point},
        {"layer": "landmark_or_address", "name": landmark_name},
        {"layer": "neighborhood", "name": None},
        {"layer": "district", "name": census_district_name},
        {"layer": "city", "name": census_place_name or anchor_city_name},
        {"layer": "county", "name": census_county_name or anchor_county},
        {"layer": "metro_area", "name": census_metro_name or metro_name},
        {"layer": "state_region", "name": state_region},
        {"layer": "state", "name": state_name},
        {"layer": "national_region", "name": national_region},
        {"layer": "country", "name": "United States"},
    ]

    return {
        "local_cell_name": local_name,
        "local_cell_name_layer": local_layer,
        "general_american_cell_name": general_name,
        "general_american_cell_name_layer": general_layer,
        "identity_stack_json": json.dumps(identity_stack, ensure_ascii=True),
    }


def _normalize_public_report_display_text(value):
    text = _clean_public_report_text(value)
    if text is None:
        return None
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _public_report_text_contains_name(value, contained_value):
    value_text = _normalize_public_report_display_text(value)
    contained_text = _normalize_public_report_display_text(contained_value)
    if value_text is None or contained_text is None:
        return False
    return f" {contained_text} " in f" {value_text} "


def _join_public_report_display_location_parts(*parts):
    joined_parts = []
    for part in parts:
        text = _clean_public_report_text(part)
        if text is None:
            continue
        if any(_public_report_text_contains_name(existing, text) for existing in joined_parts):
            continue
        joined_parts.append(text)
    return ", ".join(joined_parts) if joined_parts else None


def _is_generic_public_report_district_name(value):
    text = _normalize_public_report_display_text(value)
    return bool(text and re.fullmatch(r"(district|precinct|ward) [a-z0-9]+", text))


def _format_public_report_display_context_name(value, layer):
    text = _clean_public_report_text(value)
    if text is None:
        return None
    if layer == "metro_area":
        return re.sub(r"\s+Metro Area$", " metro", text)
    if layer == "urban_area":
        return re.sub(r"\s+Urban Area$", " urban area", text)
    return text


def _build_public_report_display_label_fields(row):
    local_name = _clean_public_report_text(row.get("local_cell_name"))
    local_layer = _clean_public_report_text(row.get("local_cell_name_layer"))
    general_name = _clean_public_report_text(row.get("general_american_cell_name"))
    general_layer = _clean_public_report_text(row.get("general_american_cell_name_layer"))
    state_name = _clean_public_report_text(row.get("census_state_name"))
    county_name = _clean_public_report_text(row.get("census_county_name"))
    cell_name = _clean_public_report_text(row.get("cell_name"))

    if local_name is not None:
        include_county = local_layer == "district" and _is_generic_public_report_district_name(local_name)
        display_name = _join_public_report_display_location_parts(
            local_name,
            county_name if include_county else None,
            state_name,
        )
        display_layer = local_layer
    elif general_name is not None:
        display_name = general_name
        display_layer = general_layer
    else:
        display_name = cell_name or "Unnamed suitability cell"
        display_layer = "cell"

    context_candidates = []
    if local_layer != "city":
        context_candidates.extend(
            [
                (row.get("census_metro_area_name"), "metro_area"),
                (row.get("census_combined_statistical_area_name"), "combined_statistical_area"),
                (row.get("census_urban_area_name"), "urban_area"),
            ]
        )
    if general_name is not None and general_layer != display_layer:
        context_candidates.append((general_name, general_layer))

    context_name = None
    context_layer = None
    for candidate_name, candidate_layer in context_candidates:
        formatted_context_name = _format_public_report_display_context_name(
            candidate_name,
            candidate_layer,
        )
        if formatted_context_name is None:
            continue
        if _normalize_public_report_display_text(formatted_context_name) == _normalize_public_report_display_text(
            display_name
        ):
            continue
        context_name = formatted_context_name
        context_layer = candidate_layer
        break

    return {
        "display_cell_name": display_name,
        "display_cell_name_layer": display_layer,
        "display_context_name": context_name,
        "display_context_name_layer": context_layer,
    }


def _select_public_report_census_cell_name_choice(census_geography):
    """Return a Census-backed base label for stable cell naming when available."""
    if not census_geography or census_geography.get("census_geolookup_status") != "matched":
        return None
    for column in (
        "census_place_name",
        "census_district_name",
        "census_county_name",
        "census_state_name",
    ):
        value = _clean_public_report_text(census_geography.get(column))
        if value is not None:
            return {
                "cell_name": value,
                "cell_name_basis": "census_geolookup",
                "cell_name_popularity_score": None,
                "cell_name_match_scope": "intersecting_census_geography",
            }
    return None


def _select_public_report_census_anchor_place(census_geography):
    """Build anchor metadata from Census intersecting geography when available."""
    if not census_geography or census_geography.get("census_geolookup_status") != "matched":
        return None
    anchor_place_name = (
        _clean_public_report_text(census_geography.get("census_place_name"))
        or _clean_public_report_text(census_geography.get("census_district_name"))
        or _clean_public_report_text(census_geography.get("census_county_name"))
    )
    anchor_place_county = _clean_public_report_text(census_geography.get("census_county_name"))
    anchor_place_state = _clean_public_report_text(census_geography.get("census_state_code"))
    if anchor_place_name is None or anchor_place_county is None or anchor_place_state is None:
        return None
    return {
        "anchor_place_name": anchor_place_name,
        "anchor_place_county": anchor_place_county,
        "anchor_place_state": anchor_place_state,
        "anchor_place_distance_miles": None,
        "anchor_place_direction": None,
    }


def _make_public_report_cell_names_unique(frame):
    """Disambiguate duplicate cell names with gateway-place phrasing instead of cell ids."""
    named = frame.copy()
    if "cell_name" not in named.columns:
        raise KeyError("Public report cell naming requires a cell_name column")

    if "cell_id" not in named.columns:
        named["cell_id"] = np.arange(1, len(named) + 1, dtype=int)

    named["base_cell_name"] = named["cell_name"].copy()
    missing_name_mask = named["base_cell_name"].isna()
    if missing_name_mask.any():
        if "anchor_place_name" in named.columns:
            named.loc[missing_name_mask, "base_cell_name"] = named.loc[
                missing_name_mask, "anchor_place_name"
            ].map(lambda value: f"Area near {value}" if pd.notna(value) else "Unnamed suitability cell")
        else:
            named.loc[missing_name_mask, "base_cell_name"] = "Unnamed suitability cell"

    named["cell_name"] = named["base_cell_name"]
    named["cell_name_is_disambiguated"] = False

    duplicate_mask = named["base_cell_name"].duplicated(keep=False)
    if duplicate_mask.any():
        named.loc[duplicate_mask, "cell_name"] = named.loc[duplicate_mask].apply(
            _format_public_report_cell_name_from_anchor,
            axis=1,
        )
        remaining_duplicate_mask = duplicate_mask & named["cell_name"].duplicated(keep=False)
        if remaining_duplicate_mask.any():
            named.loc[remaining_duplicate_mask, "cell_name"] = named.loc[
                remaining_duplicate_mask
            ].apply(
                lambda row: _format_public_report_cell_name_from_anchor(
                    row,
                    distance_precision=2,
                ),
                axis=1,
            )
        remaining_duplicate_mask = duplicate_mask & named["cell_name"].duplicated(keep=False)
        if remaining_duplicate_mask.any():
            named.loc[remaining_duplicate_mask, "cell_name"] = named.loc[
                remaining_duplicate_mask
            ].apply(
                lambda row: _format_public_report_cell_name_from_anchor(
                    row,
                    distance_precision=2,
                    include_coordinates=True,
                ),
                axis=1,
            )
        named.loc[duplicate_mask, "cell_name_is_disambiguated"] = True

    display_fields = named.apply(_build_public_report_display_label_fields, axis=1).apply(pd.Series)
    for column in display_fields.columns:
        named[column] = display_fields[column]

    return named


def _annotate_public_report_cell_names(
    frame,
    place_catalog=None,
    place_anchor_catalog=None,
    census_geographies=None,
):
    """Add deterministic human-readable place names to bounded report suitability cells."""
    named = frame.copy()
    catalog_df = _build_public_report_place_catalog_frame(place_catalog=place_catalog)
    anchor_catalog_df = _build_public_report_place_anchor_catalog_frame(
        place_anchor_catalog=place_anchor_catalog
    )
    census_geography_frame = _coerce_public_report_census_geography_frame(
        census_geographies,
        named.index,
    )

    if "geometry" not in named.columns:
        raise KeyError("Public report cell naming requires a geometry column")

    lookup_frame = named
    if isinstance(named, gpd.GeoDataFrame) and named.crs is not None and str(named.crs) != "EPSG:4326":
        lookup_frame = named.to_crs("EPSG:4326")

    lookup_points = lookup_frame.geometry.representative_point()
    if "latitude" not in named.columns:
        named["latitude"] = np.nan
    if "longitude" not in named.columns:
        named["longitude"] = np.nan
    named["latitude"] = pd.to_numeric(named["latitude"], errors="coerce")
    named["longitude"] = pd.to_numeric(named["longitude"], errors="coerce")
    invalid_coordinate_mask = (
        named["latitude"].isna()
        | named["longitude"].isna()
        | ~named["latitude"].between(-90.0, 90.0)
        | ~named["longitude"].between(-180.0, 180.0)
    )
    named.loc[invalid_coordinate_mask, "latitude"] = lookup_points.y.loc[invalid_coordinate_mask]
    named.loc[invalid_coordinate_mask, "longitude"] = lookup_points.x.loc[invalid_coordinate_mask]

    try:
        cell_key = _select_public_buildout_cell_key(named)
    except ValueError:
        cell_key = None
    if cell_key is not None:
        named["cell_id"] = named[cell_key]

    annotation_rows = []
    for index, row in named.iterrows():
        geometry = lookup_frame.geometry.loc[index]
        center_latitude = float(row["latitude"])
        center_longitude = float(row["longitude"])

        metro_candidate = _select_public_report_cell_name_candidate(
            geometry,
            center_latitude,
            center_longitude,
            catalog_df,
            "metro",
        )
        natural_candidate = _select_public_report_cell_name_candidate(
            geometry,
            center_latitude,
            center_longitude,
            catalog_df,
            "natural",
        )
        census_geography = (
            census_geography_frame.loc[index].to_dict()
            if census_geography_frame is not None and index in census_geography_frame.index
            else None
        )
        chosen = _select_public_report_census_cell_name_choice(
            census_geography
        ) or _select_public_report_cell_name_choice(metro_candidate, natural_candidate)
        anchor_place = _select_public_report_census_anchor_place(
            census_geography
        ) or _select_public_report_anchor_place(
            center_latitude,
            center_longitude,
            anchor_catalog_df,
            base_cell_name=chosen["cell_name"],
        )
        identity_fields = _build_public_report_identity_fields(
            center_latitude,
            center_longitude,
            metro_candidate,
            natural_candidate,
            anchor_place,
            census_geography=census_geography,
        )
        census_fields = census_geography or {}
        annotation_rows.append(
            {
                "metro_feature_name": metro_candidate["feature_name"],
                "metro_feature_popularity_score": metro_candidate["popularity_score"],
                "metro_feature_distance_degrees": metro_candidate["distance_degrees"],
                "metro_feature_distance_miles": metro_candidate["distance_miles"],
                "metro_feature_match_scope": metro_candidate["match_scope"],
                "natural_feature_name": natural_candidate["feature_name"],
                "natural_feature_popularity_score": natural_candidate["popularity_score"],
                "natural_feature_distance_degrees": natural_candidate["distance_degrees"],
                "natural_feature_distance_miles": natural_candidate["distance_miles"],
                "natural_feature_match_scope": natural_candidate["match_scope"],
                **census_fields,
                **anchor_place,
                **identity_fields,
                **chosen,
            }
        )

    annotation_df = pd.DataFrame(annotation_rows, index=named.index)
    for column in annotation_df.columns:
        named[column] = annotation_df[column]
    return _make_public_report_cell_names_unique(named)


def _build_public_report_ranked_suitability_summary(frame):
    """Build a ranked nationwide suitability table from the bounded suitability layer."""
    cell_key = _select_public_buildout_cell_key(frame)
    ranked = pd.DataFrame(frame.drop(columns="geometry", errors="ignore")).copy()
    sort_columns = ["suitability_percentile", "suitability_score"]
    ascending = [False, False]

    if "developable_capacity_mw" in ranked.columns:
        sort_columns.append("developable_capacity_mw")
        ascending.append(False)

    sort_columns.append(cell_key)
    ascending.append(True)

    ranked = ranked.sort_values(sort_columns, ascending=ascending).reset_index(drop=True)
    ranked.insert(0, "national_rank", np.arange(1, len(ranked) + 1, dtype=int))

    preferred_columns = [
        "national_rank",
        "cell_id",
        "cell_name",
        "base_cell_name",
        "display_cell_name",
        "display_cell_name_layer",
        "display_context_name",
        "display_context_name_layer",
        "local_cell_name",
        "local_cell_name_layer",
        "general_american_cell_name",
        "general_american_cell_name_layer",
        "identity_stack_json",
        "census_geolookup_status",
        "census_place_name",
        "census_place_layer",
        "census_district_name",
        "census_county_name",
        "census_state_name",
        "census_state_code",
        "census_metro_area_name",
        "census_combined_statistical_area_name",
        "census_urban_area_name",
        "census_state_region_name",
        "census_national_region_name",
        "census_tract_geoid",
        "census_block_geoid",
        "census_geolookup_miss_class",
        "census_geolookup_nearest_state_name",
        "census_geolookup_nearest_state_code",
        "census_geolookup_nearest_state_distance_miles",
        "census_geolookup_nearest_state_region_name",
        "census_geolookup_nearest_national_region_name",
        "census_geolookup_map_impact_class",
        "census_geolookup_display_label_decision",
        "cell_name_basis",
        "cell_name_is_disambiguated",
        "anchor_place_name",
        "anchor_place_county",
        "anchor_place_state",
        "anchor_place_distance_miles",
        "anchor_place_direction",
        "gid",
        "sc_point_gid",
        "latitude",
        "longitude",
        "developable_capacity_mw",
        "suitability_score",
        "suitability_percentile",
        "is_feasible_land",
        "cell_name_popularity_score",
        "cell_name_match_scope",
        "metro_feature_name",
        "metro_feature_popularity_score",
        "metro_feature_distance_degrees",
        "metro_feature_distance_miles",
        "metro_feature_match_scope",
        "natural_feature_name",
        "natural_feature_popularity_score",
        "natural_feature_distance_degrees",
        "natural_feature_distance_miles",
        "natural_feature_match_scope",
    ]
    ordered_columns = [column for column in preferred_columns if column in ranked.columns]
    remaining_columns = [column for column in ranked.columns if column not in ordered_columns]
    return ranked[ordered_columns + remaining_columns]


def _empty_public_report_census_geolookup_miss_frame():
    columns = [
        "national_rank",
        "cell_id",
        "census_geolookup_status",
        "census_geolookup_miss_class",
        "nearest_state_name",
        "nearest_state_code",
        "nearest_state_distance_miles",
        "nearest_state_region_name",
        "nearest_national_region_name",
        "map_impact_class",
        "water_wetland_exclusion_status",
        "water_wetland_excluded",
        "water_wetland_share",
        "suitability_percentile",
        "longitude",
        "latitude",
        "original_display_cell_name",
        "original_display_context_name",
        "recommended_display_cell_name",
        "recommended_display_context_name",
        "display_label_decision",
        "fallback_review_note",
    ]
    return pd.DataFrame(columns=columns)


def _classify_public_report_census_miss_map_impact(row):
    percentile = pd.to_numeric(pd.Series([row.get("suitability_percentile")]), errors="coerce").iloc[0]
    water_wetland_excluded = bool(row.get("water_wetland_excluded")) if pd.notna(
        row.get("water_wetland_excluded")
    ) else False
    if water_wetland_excluded or (pd.notna(percentile) and float(percentile) == 0.0):
        return "clamped_zero"
    if pd.notna(percentile) and float(percentile) >= PUBLIC_REPORT_CENSUS_MISS_HIGH_IMPACT_PERCENTILE:
        return "high"
    if pd.notna(percentile) and float(percentile) >= PUBLIC_REPORT_CENSUS_MISS_MEDIUM_IMPACT_PERCENTILE:
        return "medium"
    return "low"


def _format_public_report_census_miss_display_label(row, nearest_state_name, nearest_state_code):
    existing_display = _clean_public_report_text(row.get("display_cell_name"))
    general_name = _clean_public_report_text(row.get("general_american_cell_name"))
    anchor_distance = pd.to_numeric(pd.Series([row.get("anchor_place_distance_miles")]), errors="coerce").iloc[0]
    anchor_is_local = pd.notna(anchor_distance) and float(anchor_distance) <= float(
        PUBLIC_REPORT_CENSUS_MISS_LOCAL_ANCHOR_DISTANCE_MILES
    )
    if existing_display is not None and anchor_is_local:
        place_label = existing_display
    elif general_name is not None and general_name.lower().startswith("near "):
        place_label = general_name[5:]
    else:
        place_label = _clean_public_report_text(nearest_state_name or nearest_state_code)
    if place_label is None:
        return "Boundary/coastal retained cell"
    return f"Boundary/coastal cell near {place_label}"


def _build_public_report_census_geolookup_miss_frame(ranked_suitability, state_boundaries):
    """Classify retained cells where Census GeoLookup did not return named geography."""
    ranked = pd.DataFrame(ranked_suitability).copy()
    if "census_geolookup_status" not in ranked.columns:
        return _empty_public_report_census_geolookup_miss_frame()

    missing_mask = ranked["census_geolookup_status"].fillna("missing") != "matched"
    misses = ranked.loc[missing_mask].copy()
    if misses.empty:
        return _empty_public_report_census_geolookup_miss_frame()

    states = gpd.GeoDataFrame(state_boundaries).copy()
    if states.empty or "geometry" not in states.columns:
        return _empty_public_report_census_geolookup_miss_frame()
    if states.crs is None:
        states = states.set_crs("EPSG:4326", allow_override=True)
    states = states[[column for column in ("state_name", "state_code", "geometry") if column in states.columns]]
    for column in ("state_name", "state_code"):
        if column not in states.columns:
            states[column] = None

    point_frame = gpd.GeoDataFrame(
        misses,
        geometry=gpd.points_from_xy(misses["longitude"], misses["latitude"]),
        crs="EPSG:4326",
    )
    contains_points = point_frame.to_crs(states.crs)
    distance_states = states.to_crs("EPSG:5070")
    distance_points = point_frame.to_crs("EPSG:5070")

    rows = []
    for index, row in misses.iterrows():
        point_geometry = contains_points.geometry.loc[index]
        distance_geometry = distance_points.geometry.loc[index]
        state_cover_mask = states.geometry.covers(point_geometry)
        within_state_boundary = bool(state_cover_mask.any())
        distances = distance_states.geometry.distance(distance_geometry)
        nearest_state_index = distances.idxmin()
        nearest_state = distance_states.loc[nearest_state_index]
        nearest_state_distance_miles = float(distances.loc[nearest_state_index]) / 1609.344
        nearest_state_name = _clean_public_report_text(nearest_state.get("state_name"))
        nearest_state_code = _clean_public_report_text(nearest_state.get("state_code"))

        if within_state_boundary:
            miss_class = "inside_state_boundary_unmatched"
            display_label_decision = "bounded_catalog_fallback_sufficient_with_review"
            recommended_display_cell_name = _clean_public_report_text(row.get("display_cell_name"))
            recommended_display_context_name = _clean_public_report_text(row.get("display_context_name"))
        elif nearest_state_distance_miles <= PUBLIC_REPORT_CENSUS_MISS_NEAR_STATE_DISTANCE_MILES:
            miss_class = "near_state_boundary_or_coast"
            display_label_decision = "dedicated_boundary_coastal_display_label"
            recommended_display_cell_name = _format_public_report_census_miss_display_label(
                row,
                nearest_state_name,
                nearest_state_code,
            )
            original_display = _clean_public_report_text(row.get("display_cell_name"))
            recommended_display_context_name = original_display if original_display else None
        else:
            miss_class = "outside_state_boundary"
            display_label_decision = "dedicated_outside_boundary_display_label"
            recommended_display_cell_name = _format_public_report_census_miss_display_label(
                row,
                nearest_state_name,
                nearest_state_code,
            )
            recommended_display_context_name = _clean_public_report_text(row.get("display_cell_name"))

        water_wetland_excluded = bool(row.get("water_wetland_excluded")) if pd.notna(
            row.get("water_wetland_excluded")
        ) else False
        rows.append(
            {
                "national_rank": row.get("national_rank"),
                "cell_id": row.get("cell_id"),
                "census_geolookup_status": row.get("census_geolookup_status"),
                "census_geolookup_miss_class": miss_class,
                "nearest_state_name": nearest_state_name,
                "nearest_state_code": nearest_state_code,
                "nearest_state_distance_miles": round(nearest_state_distance_miles, 3),
                "nearest_state_region_name": _select_public_report_state_region(
                    row.get("latitude"),
                    row.get("longitude"),
                    nearest_state_code,
                ),
                "nearest_national_region_name": _select_public_report_national_region(
                    nearest_state_code
                ),
                "map_impact_class": _classify_public_report_census_miss_map_impact(row),
                "water_wetland_exclusion_status": "water_wetland_clamped"
                if water_wetland_excluded
                else "not_water_wetland_clamped",
                "water_wetland_excluded": water_wetland_excluded,
                "water_wetland_share": row.get("water_wetland_share"),
                "suitability_percentile": row.get("suitability_percentile"),
                "longitude": row.get("longitude"),
                "latitude": row.get("latitude"),
                "original_display_cell_name": row.get("display_cell_name"),
                "original_display_context_name": row.get("display_context_name"),
                "recommended_display_cell_name": recommended_display_cell_name,
                "recommended_display_context_name": recommended_display_context_name,
                "display_label_decision": display_label_decision,
                "fallback_review_note": (
                    "Census did not return named geography for the representative point; "
                    "use nearest-state boundary/coastal classification and bounded catalog label as review context."
                ),
            }
        )
    return pd.DataFrame(rows)


def _apply_public_report_census_miss_classification(frame, miss_frame):
    """Attach Census miss review fields and display labels to a report cell frame."""
    classified = frame.copy()
    if miss_frame is None or miss_frame.empty or "cell_id" not in classified.columns:
        return classified
    miss_by_cell = pd.DataFrame(miss_frame).set_index("cell_id")
    cell_ids = classified["cell_id"]
    mapped_columns = {
        "census_geolookup_miss_class": "census_geolookup_miss_class",
        "nearest_state_name": "census_geolookup_nearest_state_name",
        "nearest_state_code": "census_geolookup_nearest_state_code",
        "nearest_state_distance_miles": "census_geolookup_nearest_state_distance_miles",
        "nearest_state_region_name": "census_geolookup_nearest_state_region_name",
        "nearest_national_region_name": "census_geolookup_nearest_national_region_name",
        "map_impact_class": "census_geolookup_map_impact_class",
        "display_label_decision": "census_geolookup_display_label_decision",
    }
    for source_column, target_column in mapped_columns.items():
        classified[target_column] = cell_ids.map(miss_by_cell[source_column])
    for source_column, target_column in (
        ("recommended_display_cell_name", "display_cell_name"),
        ("recommended_display_context_name", "display_context_name"),
    ):
        replacement_values = cell_ids.map(miss_by_cell[source_column])
        replacement_mask = replacement_values.notna()
        classified.loc[replacement_mask, target_column] = replacement_values.loc[replacement_mask]
    return classified


def _value_counts_dict(series):
    return {
        str(key): int(value)
        for key, value in series.value_counts(dropna=False).sort_index().items()
    }


def _write_public_report_census_geolookup_miss_artifacts(
    output_dir,
    ranked_suitability,
    miss_frame,
):
    """Write row-level and narrative Census GeoLookup miss review artifacts."""
    output_dir = Path(output_dir)
    miss_frame = pd.DataFrame(miss_frame).copy()
    ranked = pd.DataFrame(ranked_suitability)
    miss_csv_path = output_dir / "public_report_census_geolookup_misses.csv"
    miss_note_path = output_dir / "public_report_census_geolookup_misses.md"
    miss_frame.to_csv(miss_csv_path, index=False)

    total_cells = int(len(ranked))
    if "census_geolookup_status" in ranked.columns:
        matched_cells = int((ranked["census_geolookup_status"].fillna("missing") == "matched").sum())
        geolookup_enabled = True
    else:
        matched_cells = 0
        geolookup_enabled = False
    missing_cells = int(len(miss_frame))
    lines = [
        "# Census GeoLookup Miss Classification",
        "",
        "This generated review note classifies retained report cells where the Census coordinate GeoLookup response did not return named geography.",
        "",
        "## Summary",
        "",
        f"- Census GeoLookup enabled: {'yes' if geolookup_enabled else 'no'}",
        f"- Retained ranked cells: {total_cells}",
        f"- Census matched cells: {matched_cells}",
        f"- Census missing/error cells: {missing_cells}",
    ]
    if not miss_frame.empty:
        max_distance = miss_frame["nearest_state_distance_miles"].max()
        lines.extend(
            [
                f"- Maximum nearest-state distance for misses: {float(max_distance):.1f} miles",
                "",
                "## Classification Counts",
                "",
                "### Location Class",
                "",
            ]
        )
        lines.extend(
            f"- {key}: {value}"
            for key, value in _value_counts_dict(miss_frame["census_geolookup_miss_class"]).items()
        )
        lines.extend(["", "### Map Impact", ""])
        lines.extend(
            f"- {key}: {value}"
            for key, value in _value_counts_dict(miss_frame["map_impact_class"]).items()
        )
        lines.extend(["", "### Water/Wetland Status", ""])
        lines.extend(
            f"- {key}: {value}"
            for key, value in _value_counts_dict(miss_frame["water_wetland_exclusion_status"]).items()
        )
        lines.extend(["", "### Nearest State Fallback", ""])
        lines.extend(
            f"- {key}: {value}"
            for key, value in _value_counts_dict(miss_frame["nearest_state_code"]).items()
        )
        high_impact = miss_frame.loc[miss_frame["map_impact_class"] == "high"]
        if not high_impact.empty:
            lines.extend(["", "## High-Impact Misses", ""])
            for _, row in high_impact.sort_values("national_rank").iterrows():
                lines.append(
                    f"- Rank {int(row['national_rank'])}, cell {int(row['cell_id'])}: "
                    f"{row['recommended_display_cell_name']} "
                    f"({float(row['suitability_percentile']):.1f} percentile; "
                    f"{float(row['nearest_state_distance_miles']):.1f} miles from {row['nearest_state_code']})"
                )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The bounded catalog fallback alone is not treated as an authoritative place identity for Census misses.",
            "For retained cells whose representative point falls outside named Census geography, the bundle now records nearest-state boundary/coastal classification and applies a dedicated boundary/coastal display label in the ranked output. No Census place, county, metro, state, division, or region is inferred for those rows.",
            "",
            "The row-level CSV next to this note is the review surface for deciding whether a future coastal/offshore naming rule should become more specific.",
            "",
        ]
    )
    miss_note_path.write_text("\n".join(lines))
    return {"outputs": [miss_csv_path.as_posix(), miss_note_path.as_posix()]}


def _load_public_report_bundle_smoke_configs(repo_root):
    """Load the tracked smoke configs that define the current bundle's scenario controls."""
    repo_root = Path(repo_root).resolve()
    config_specs = [
        (
            "public_eer_total_downscaled",
            repo_root / PUBLIC_REPORT_BUNDLE_TOTAL_CONFIG_PATH,
        ),
        (
            "public_eer_regional_downscaled",
            repo_root / PUBLIC_REPORT_BUNDLE_REGIONAL_CONFIG_PATH,
        ),
    ]
    loaded = []
    for output_label, config_path in config_specs:
        loaded.append((output_label, config_path, json.loads(config_path.read_text())))
    return loaded


def _build_public_report_output_labels(output_dir):
    """Return the tracked output labels for the bounded public report bundle."""
    output_dir = Path(output_dir)
    return [
        {
            "label": "public_report_feasible_land",
            "path": (output_dir / "public_report_feasible_land.gpkg").as_posix(),
            "description": "bounded feasible-land approximation derived from execution-grid cells where developable_capacity_mw > 0; cells with NLCD water/wetland share across classes 11, 90, and 95 at or above 0.5 are retained and flagged for suitability-percentile clamping",
        },
        {
            "label": "public_report_suitability_percentiles",
            "path": (output_dir / "public_report_suitability_percentiles.gpkg").as_posix(),
            "description": "bounded suitability-percentile surface derived from the pre-existing suitability_score field on developable cells, with water/wetland-excluded cells clamped to 0 percentile",
        },
        {
            "label": "public_report_suitability_ranked_cells",
            "path": (output_dir / "public_report_suitability_ranked_cells.csv").as_posix(),
            "description": "bounded nationwide ranked suitability table sorted by percentile, score, developable capacity, and stable cell identifier",
        },
        {
            "label": "public_report_census_geolookup_misses_csv",
            "path": (output_dir / "public_report_census_geolookup_misses.csv").as_posix(),
            "description": "row-level review table for retained cells where Census coordinate GeoLookup did not return named geography",
        },
        {
            "label": "public_report_census_geolookup_misses_note",
            "path": (output_dir / "public_report_census_geolookup_misses.md").as_posix(),
            "description": "summary and display-label decision note for Census GeoLookup misses in retained report cells",
        },
        {
            "label": "public_report_state_boundaries",
            "path": (output_dir / "public_report_state_boundaries.gpkg").as_posix(),
            "description": "derived Census state-boundary layer reprojected into the bounded map CRS for transparent contextual overlay",
        },
        {
            "label": "public_report_hosting_capacity_proxy",
            "path": (output_dir / "public_report_hosting_capacity_proxy.gpkg").as_posix(),
            "description": "bounded regional hosting-capacity proxy derived from NERC reserve-margin headroom and transferred onto the execution-grid cells",
        },
        {
            "label": "public_report_zoning_proxy",
            "path": (output_dir / "public_report_zoning_proxy.gpkg").as_posix(),
            "description": "bounded zoning proxy derived from NLCD developed-land context sampled onto the execution-grid cells",
        },
        {
            "label": "public_report_permitting_proxy",
            "path": (output_dir / "public_report_permitting_proxy.gpkg").as_posix(),
            "description": "bounded permitting and ordinance evidence proxy derived from a manually curated public evidence manifest and transferred onto the execution-grid cells",
        },
        {
            "label": "public_report_social_friction_proxy",
            "path": (output_dir / "public_report_social_friction_proxy.gpkg").as_posix(),
            "description": "bounded social-friction evidence proxy derived from a manually curated public evidence manifest and transferred onto the execution-grid cells",
        },
        {
            "label": "public_report_suitability_map",
            "path": (output_dir / "public_report_suitability_map.html").as_posix(),
            "description": "single-page D3 map of the bounded suitability-percentile surface for quick visual review",
        },
        {
            "label": "public_report_limitations",
            "path": (output_dir / "public_report_limitations.md").as_posix(),
            "description": "limitations and refinement carry-forward note for the current bounded public report surface",
        },
        {
            "label": "public_report_reeds_integration_contract",
            "path": (output_dir / "public_report_reeds_integration_contract.json").as_posix(),
            "description": "machine-readable handoff contract for ReEDS-facing use of the bounded public report bundle",
        },
        {
            "label": "public_report_grid_resolution_contract",
            "path": (output_dir / "public_report_grid_resolution_contract.json").as_posix(),
            "description": "machine-readable comparison between the current execution grid and the report-reference national grid contract",
        },
        {
            "label": "public_report_allocation_assumption_contract",
            "path": (output_dir / "public_report_allocation_assumption_contract.json").as_posix(),
            "description": "machine-readable comparison between current bounded allocation mechanics and unrecovered report allocation assumptions",
        },
        {
            "label": "public_report_baxtel_schema_contract",
            "path": (output_dir / "public_report_baxtel_schema_contract.json").as_posix(),
            "description": "machine-readable comparison between Baxtel schema evidence, the public data-center baseline, and trained-suitability parity requirements",
        },
        {
            "label": "public_eer_total_downscaled_cumulative_buildout",
            "path": (output_dir / "public_eer_total_downscaled_cumulative_buildout.gpkg").as_posix(),
            "description": "bounded cumulative buildout approximation derived from the total smoke output",
        },
        {
            "label": "public_eer_regional_downscaled_cumulative_buildout",
            "path": (output_dir / "public_eer_regional_downscaled_cumulative_buildout.gpkg").as_posix(),
            "description": "bounded cumulative buildout approximation derived from the grouped regional smoke output",
        },
        {
            "label": "public_report_bundle_cumulative_buildout_summary",
            "path": (output_dir / "public_report_bundle_cumulative_buildout_summary.csv").as_posix(),
            "description": "year-by-year cumulative buildout summary for the bounded bundle outputs",
        },
    ]


def _build_public_report_scenario_input(output_label, config_path, config):
    """Normalize one smoke-config-driven scenario input entry for the assumption registry."""
    entry = {
        "output_label": output_label,
        "config_path": Path(config_path).as_posix(),
        "projection_resolution": config.get("projection_resolution"),
        "load_projection_path": config.get("load_projections"),
        "load_value": config.get("load_value"),
        "load_year": config.get("load_year"),
        "grid_path": config.get("grid"),
        "grid_priority": config.get("grid_priority"),
        "grid_baseline_load": config.get("grid_baseline_load"),
        "grid_capacity": config.get("grid_capacity"),
        "baseline_year": config.get("baseline_year"),
        "utilization_factor": config.get("utilization_factor"),
        "max_site_addition_per_year_mw": config.get("max_site_addition_per_year"),
        "max_site_addition_per_time_step_mw": config.get("max_site_addition_per_time_step"),
        "site_saturation_limit": config.get("site_saturation_limit"),
        "priority_power": config.get("priority_power"),
        "n_bootstraps": config.get("n_bootstraps"),
        "random_seed": config.get("random_seed"),
    }
    optional_fields = ("regions", "region_names", "load_regions")
    for field in optional_fields:
        if field in config:
            entry[field] = config[field]
    return entry


def _sorted_unique_public_report_ints(values):
    cleaned = []
    for value in values:
        if value is None or pd.isna(value):
            continue
        cleaned.append(int(value))
    return sorted(set(cleaned))


def _normalize_public_report_number(value):
    if value is None or pd.isna(value):
        return None
    number = float(value)
    return int(number) if number.is_integer() else number


def _sorted_unique_public_report_numbers(values):
    cleaned = []
    for value in values:
        normalized = _normalize_public_report_number(value)
        if normalized is not None:
            cleaned.append(normalized)
    return sorted(set(cleaned))


def _load_public_report_cumulative_buildout_years(output_dir):
    summary_path = Path(output_dir) / "public_report_bundle_cumulative_buildout_summary.csv"
    if not summary_path.exists():
        return []
    summary = pd.read_csv(summary_path, usecols=["year"])
    return _sorted_unique_public_report_ints(summary["year"])


def _first_public_report_projection_year(years, starting_stock_year):
    if starting_stock_year is None:
        return None
    future_years = [year for year in years if year > starting_stock_year]
    return future_years[0] if future_years else None


def _build_public_report_capacity_constraint_assumptions(smoke_configs):
    """Build the report-parity capacity and utilization constraint contract."""
    utilization_factors = _sorted_unique_public_report_numbers(
        config.get("utilization_factor", 1.0) for _, _, config in smoke_configs
    )
    max_site_addition_per_time_step = _sorted_unique_public_report_numbers(
        config.get("max_site_addition_per_time_step") for _, _, config in smoke_configs
    )
    max_site_addition_per_year = _sorted_unique_public_report_numbers(
        config.get("max_site_addition_per_year") for _, _, config in smoke_configs
    )
    report_reference = {
        "utilization_factor": PUBLIC_REPORT_REFERENCE_UTILIZATION_FACTOR,
        "max_site_addition_per_time_step_mw": PUBLIC_REPORT_REFERENCE_MAX_SITE_ADDITION_PER_TIME_STEP_MW,
        "load_to_capacity_rule": "capacity_mw = load_mw / utilization_factor",
    }
    current_bundle = {
        "utilization_factors": utilization_factors,
        "max_site_addition_per_time_step_mw": max_site_addition_per_time_step,
        "max_site_addition_per_year_mw": max_site_addition_per_year,
        "capacity_to_load_rule": "load_mw = capacity_mw * utilization_factor for grid-capacity and per-site limits",
        "capacity_equivalent_output_rule": "cumulative buildout outputs include capacity-equivalent columns derived as load_mw / utilization_factor",
        "capacity_limited_allocation_rule": "when projected demand exceeds available capped capacity, output remains capacity-limited instead of forcing excess load into a grid cell",
    }
    alignment_checks = {
        "utilization_factor_matches": utilization_factors
        == [PUBLIC_REPORT_REFERENCE_UTILIZATION_FACTOR],
        "per_time_step_limit_matches": max_site_addition_per_time_step
        == [PUBLIC_REPORT_REFERENCE_MAX_SITE_ADDITION_PER_TIME_STEP_MW],
        "per_year_limit_not_used": len(max_site_addition_per_year) == 0,
    }
    blockers = [name for name, passed in alignment_checks.items() if not passed]
    return {
        "contract_type": "report-parity-capacity-constraint-contract",
        "report_reference": report_reference,
        "current_bundle": current_bundle,
        "alignment_checks": alignment_checks,
        "parity_status": "value-aligned" if not blockers else "blocked",
        "parity_blockers": blockers,
        "implementation_decision": (
            "Apply the 88% utilization factor to convert capacity constraints into load-equivalent "
            "limits for downscaling, and emit capacity-equivalent cumulative buildout fields for review. "
            "Exact report semantics remain bounded until the report source data and allocation rules are recovered."
        ),
    }


def _read_public_report_csv_columns(path):
    path = Path(path)
    if not path.exists():
        return []
    try:
        return [str(column) for column in pd.read_csv(path, nrows=0).columns]
    except pd.errors.EmptyDataError:
        return []


def _public_report_schema_present_fields(columns, expected_fields):
    normalized_columns = {str(column).strip().lower() for column in columns}
    return [field for field in expected_fields if field.lower() in normalized_columns]


def _public_report_schema_missing_fields(columns, expected_fields):
    present_fields = set(_public_report_schema_present_fields(columns, expected_fields))
    return [field for field in expected_fields if field not in present_fields]


def _build_public_report_baxtel_schema_contract(
    repo_root,
    baxtel_schema_path=None,
    public_baseline_path=None,
):
    """Build the Baxtel schema and trained-suitability parity contract."""
    repo_root = Path(repo_root).resolve()
    baxtel_spec = PUBLIC_DATASET_CATALOG["baxtel_us_data_center_sites"]
    baxtel_schema_path = Path(
        baxtel_schema_path or repo_root / PUBLIC_REPORT_BAXTEL_SCHEMA_PATH
    )
    public_baseline_path = Path(
        public_baseline_path or repo_root / PUBLIC_REPORT_PUBLIC_DATA_CENTER_BASELINE_PATH
    )
    procurement_note_path = repo_root / baxtel_spec.output_relpath
    baxtel_columns = _read_public_report_csv_columns(baxtel_schema_path)
    public_baseline_columns = (
        _read_public_report_csv_columns(public_baseline_path)
        if public_baseline_path.exists()
        else list(DATA_CENTER_BASELINE_COLUMNS)
    )
    baxtel_schema_available = baxtel_schema_path.exists() and bool(baxtel_columns)
    public_baseline_available = public_baseline_path.exists()
    baxtel_missing_required_fields = _public_report_schema_missing_fields(
        baxtel_columns,
        PUBLIC_REPORT_BAXTEL_REQUIRED_TRAINING_FIELDS,
    )
    public_baseline_missing_required_fields = _public_report_schema_missing_fields(
        public_baseline_columns,
        PUBLIC_REPORT_BAXTEL_REQUIRED_TRAINING_FIELDS,
    )
    baxtel_required_fields_present = (
        baxtel_schema_available and not baxtel_missing_required_fields
    )
    public_baseline_required_fields_present = not public_baseline_missing_required_fields
    trained_suitability_surface_reproducible = False
    baxtel_2025_operating_baseline_recovered = False
    if not baxtel_schema_available:
        trained_suitability_parity_path = "blocked-commercial-schema-required"
    elif not baxtel_required_fields_present:
        trained_suitability_parity_path = "blocked-schema-incomplete"
    else:
        trained_suitability_parity_path = "schema-evidence-available-training-workflow-required"

    parity_blockers = []
    if not baxtel_schema_available:
        parity_blockers.append("baxtel_sample_or_licensed_schema_not_available")
    elif not baxtel_required_fields_present:
        parity_blockers.append("baxtel_required_training_fields_missing")
    if not baxtel_2025_operating_baseline_recovered:
        parity_blockers.append("baxtel_2025_operating_baseline_not_recovered")
    if not trained_suitability_surface_reproducible:
        parity_blockers.append(
            "trained_suitability_surface_not_reproducible_from_current_public_baseline"
        )

    return {
        "contract_type": "report-parity-baxtel-schema-contract",
        "report_reference": {
            "source": "Baxtel U.S. data center sites",
            "source_role": "2025 operating data center starting stock and positive labels for trained suitability",
            "starting_stock_year": PUBLIC_REPORT_BUNDLE_REPORT_BASELINE_YEAR,
            "trained_surface": "Baxtel-trained report-equivalent suitability surface",
            "minimum_training_fields": list(PUBLIC_REPORT_BAXTEL_REQUIRED_TRAINING_FIELDS),
            "desired_context_fields": list(PUBLIC_REPORT_BAXTEL_DESIRED_CONTEXT_FIELDS),
        },
        "vendor_procurement": {
            "dataset_id": baxtel_spec.dataset_id,
            "acquisition_mode": baxtel_spec.acquisition_mode,
            "landing_page": baxtel_spec.landing_page,
            "access_urls": list(baxtel_spec.access_urls),
            "sample_request_note_path": procurement_note_path.as_posix(),
            "expected_local_schema_path": baxtel_schema_path.as_posix(),
        },
        "current_evidence": {
            "baxtel_schema_path": baxtel_schema_path.as_posix(),
            "baxtel_schema_available": baxtel_schema_available,
            "baxtel_columns": baxtel_columns,
            "public_baseline_path": public_baseline_path.as_posix(),
            "public_baseline_available": public_baseline_available,
            "public_baseline_schema_source": "derived-csv"
            if public_baseline_available
            else "code-defined-columns",
            "public_baseline_columns": public_baseline_columns,
        },
        "schema_comparison": {
            "baxtel_required_fields_present": _public_report_schema_present_fields(
                baxtel_columns,
                PUBLIC_REPORT_BAXTEL_REQUIRED_TRAINING_FIELDS,
            ),
            "baxtel_missing_required_fields": baxtel_missing_required_fields,
            "public_baseline_required_fields_present": _public_report_schema_present_fields(
                public_baseline_columns,
                PUBLIC_REPORT_BAXTEL_REQUIRED_TRAINING_FIELDS,
            ),
            "public_baseline_missing_required_fields": public_baseline_missing_required_fields,
        },
        "alignment_checks": {
            "baxtel_schema_available": baxtel_schema_available,
            "baxtel_minimum_training_fields_present": baxtel_required_fields_present,
            "public_baseline_minimum_training_fields_present": public_baseline_required_fields_present,
            "baxtel_2025_operating_baseline_recovered": baxtel_2025_operating_baseline_recovered,
            "trained_suitability_surface_reproducible": trained_suitability_surface_reproducible,
        },
        "decision": {
            "trained_suitability_parity_path": trained_suitability_parity_path,
            "current_bundle_path": "bounded-public-baseline-only",
            "next_step": (
                "Place a Baxtel sample or licensed CSV at the expected local schema path, keep it out "
                "of git, rerun the report bundle, and use the schema comparison to decide whether a "
                "licensed report-aligned training workflow is feasible."
            ),
        },
        "parity_status": "value-aligned" if not parity_blockers else "blocked",
        "parity_blockers": parity_blockers,
        "implementation_decision": (
            "Do not treat the public OSM/Wikidata/manual baseline or the current suitability_score "
            "field as a Baxtel-trained report-equivalent suitability surface. Keep trained-suitability "
            "parity blocked until the Baxtel schema, 2025 operating baseline, and model-training workflow "
            "are recovered and validated."
        ),
    }


def _write_public_report_baxtel_schema_contract(repo_root, output_dir):
    """Write the machine-readable Baxtel schema contract for the bounded bundle."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    contract_path = output_dir / "public_report_baxtel_schema_contract.json"
    contract = _build_public_report_baxtel_schema_contract(repo_root)
    contract_path.write_text(json.dumps(contract, indent=2))
    return contract_path


def _build_public_report_allocation_validation_checks(output_dir, regional_projection_configured):
    checks = [
        {
            "name": "regional_projection_configured",
            "status": "passed" if regional_projection_configured else "failed",
            "detail": "The bounded bundle includes a grouped regional EER projection allocation path.",
        }
    ]
    if output_dir is None:
        return checks

    output_dir = Path(output_dir)
    required_outputs = {
        "total_cumulative_buildout_output_exists": output_dir
        / "public_eer_total_downscaled_cumulative_buildout.gpkg",
        "regional_cumulative_buildout_output_exists": output_dir
        / "public_eer_regional_downscaled_cumulative_buildout.gpkg",
        "cumulative_buildout_summary_exists": output_dir
        / "public_report_bundle_cumulative_buildout_summary.csv",
    }
    for name, path in required_outputs.items():
        checks.append(
            {
                "name": name,
                "status": "passed" if path.exists() else "failed",
                "path": path.as_posix(),
            }
        )
    return checks


def _build_public_report_allocation_assumption_contract(
    repo_root,
    output_dir=None,
    smoke_configs=None,
    temporal_assumptions=None,
    spatial_grid_contract=None,
    capacity_constraint_assumptions=None,
):
    """Build the report-parity allocation assumption contract for the bounded bundle."""
    repo_root = Path(repo_root).resolve()
    smoke_configs = smoke_configs or _load_public_report_bundle_smoke_configs(repo_root)
    temporal_assumptions = temporal_assumptions or _build_public_report_temporal_assumptions(
        repo_root,
        output_dir or repo_root,
        smoke_configs=smoke_configs,
    )
    spatial_grid_contract = spatial_grid_contract or _build_public_report_grid_resolution_contract(
        repo_root
    )
    capacity_constraint_assumptions = (
        capacity_constraint_assumptions
        or _build_public_report_capacity_constraint_assumptions(smoke_configs)
    )
    projection_resolutions = [
        str(config.get("projection_resolution"))
        for _, _, config in smoke_configs
        if config.get("projection_resolution")
    ]
    regional_projection_configured = "regional" in {
        resolution.lower() for resolution in projection_resolutions
    }
    regional_group_fields = sorted(
        {
            str(config.get(field))
            for _, _, config in smoke_configs
            for field in ("load_regions", "region_names")
            if config.get(field)
        }
    )
    priority_fields = sorted(
        {
            str(config.get("grid_priority"))
            for _, _, config in smoke_configs
            if config.get("grid_priority")
        }
    )
    current_bundle = {
        "allocation_algorithm": "weighted-bootstrap random shuffle over suitability-priority cells",
        "allocation_surface": "current execution-grid suitability_score field",
        "projection_resolutions": projection_resolutions,
        "regional_projection_configured": regional_projection_configured,
        "regional_group_fields": regional_group_fields,
        "priority_fields": priority_fields,
        "priority_powers": _sorted_unique_public_report_numbers(
            config.get("priority_power") for _, _, config in smoke_configs
        ),
        "n_bootstraps": _sorted_unique_public_report_numbers(
            config.get("n_bootstraps") for _, _, config in smoke_configs
        ),
        "random_seeds": _sorted_unique_public_report_numbers(
            config.get("random_seed") for _, _, config in smoke_configs
        ),
        "load_value_fields": sorted(
            {
                str(config.get("load_value"))
                for _, _, config in smoke_configs
                if config.get("load_value")
            }
        ),
        "load_year_fields": sorted(
            {
                str(config.get("load_year"))
                for _, _, config in smoke_configs
                if config.get("load_year")
            }
        ),
        "cumulative_output_rule": "sum new_dc_load_mw by stable cell over modeled years and reconcile cumulative_total_dc_load_mw to total_dc_load_mw",
    }
    alignment_checks = {
        "regional_projection_configured": regional_projection_configured,
        "capacity_constraint_value_aligned": capacity_constraint_assumptions.get(
            "parity_status"
        )
        == "value-aligned",
        "spatial_grid_value_aligned": spatial_grid_contract.get("parity_status")
        == "value-aligned",
        "temporal_assumptions_value_aligned": temporal_assumptions.get("parity_status")
        == "value-aligned",
        "exact_report_algorithm_recovered": False,
        "report_suitability_surface_recovered": False,
    }
    blockers = []
    if not alignment_checks["regional_projection_configured"]:
        blockers.append("regional_projection_not_configured")
    if not alignment_checks["capacity_constraint_value_aligned"]:
        blockers.append("capacity_constraint_contract_blocked")
    if not alignment_checks["spatial_grid_value_aligned"]:
        blockers.append("spatial_grid_contract_blocked")
    if not alignment_checks["temporal_assumptions_value_aligned"]:
        blockers.append("temporal_contract_blocked")
    if not alignment_checks["exact_report_algorithm_recovered"]:
        blockers.insert(0, "exact_report_allocation_algorithm_not_recovered")
    if not alignment_checks["report_suitability_surface_recovered"]:
        blockers.insert(1, "report_suitability_surface_not_recovered")

    return {
        "contract_type": "report-parity-allocation-assumption-contract",
        "report_reference": {
            "projection_source": "EER high data center regional projections through 2050",
            "allocation_surface": "report-equivalent suitability surface",
            "allocation_mode": "methodically distribute regional EER projections to the suitability surface",
            "starting_stock_year": PUBLIC_REPORT_BUNDLE_REPORT_BASELINE_YEAR,
            "buildout_horizon_years": PUBLIC_REPORT_REFERENCE_BUILDOUT_HORIZON_YEARS,
            "capacity_constraints": {
                "utilization_factor": PUBLIC_REPORT_REFERENCE_UTILIZATION_FACTOR,
                "max_site_addition_per_time_step_mw": PUBLIC_REPORT_REFERENCE_MAX_SITE_ADDITION_PER_TIME_STEP_MW,
            },
        },
        "current_bundle": current_bundle,
        "alignment_checks": alignment_checks,
        "validation_checks": _build_public_report_allocation_validation_checks(
            output_dir,
            regional_projection_configured,
        ),
        "parity_status": "value-aligned" if not blockers else "blocked",
        "parity_blockers": blockers,
        "implementation_decision": (
            "Encode the current weighted-bootstrap allocation as a bounded approximation. "
            "Do not claim report-equivalent allocation until the exact report algorithm, "
            "report suitability surface, temporal contract, and spatial grid contract are recovered."
        ),
    }


def _write_public_report_allocation_assumption_contract(repo_root, output_dir):
    """Write the machine-readable allocation-assumption contract for the bounded bundle."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    contract_path = output_dir / "public_report_allocation_assumption_contract.json"
    contract = _build_public_report_allocation_assumption_contract(repo_root, output_dir=output_dir)
    contract_path.write_text(json.dumps(contract, indent=2))
    return contract_path


def _build_public_report_temporal_assumptions(repo_root, output_dir, smoke_configs=None):
    """Build the report-parity temporal assumption contract for the bounded bundle."""
    repo_root = Path(repo_root).resolve()
    smoke_configs = smoke_configs or _load_public_report_bundle_smoke_configs(repo_root)
    baseline_years = _sorted_unique_public_report_ints(
        config.get("baseline_year") for _, _, config in smoke_configs
    )
    starting_stock_fields = sorted(
        {
            str(config.get("grid_baseline_load"))
            for _, _, config in smoke_configs
            if config.get("grid_baseline_load")
        }
    )
    current_starting_stock_year = baseline_years[0] if len(baseline_years) == 1 else None
    current_modeled_years = _load_public_report_cumulative_buildout_years(output_dir)
    current_first_projection_year = _first_public_report_projection_year(
        current_modeled_years,
        current_starting_stock_year,
    )
    current_terminal_year = current_modeled_years[-1] if current_modeled_years else None
    current_buildout_horizon_years = (
        current_terminal_year - current_starting_stock_year
        if current_terminal_year is not None and current_starting_stock_year is not None
        else None
    )
    if len(starting_stock_fields) == 1:
        current_starting_stock_source = f"execution-grid baseline field {starting_stock_fields[0]}"
    elif starting_stock_fields:
        current_starting_stock_source = "execution-grid baseline fields " + ", ".join(
            starting_stock_fields
        )
    else:
        current_starting_stock_source = None

    report_reference = {
        "starting_stock_year": PUBLIC_REPORT_BUNDLE_REPORT_BASELINE_YEAR,
        "starting_stock_source": PUBLIC_REPORT_REFERENCE_INITIAL_LOCATIONS,
        "modeled_years": list(PUBLIC_REPORT_REFERENCE_MODELED_YEARS),
        "first_projection_year": _first_public_report_projection_year(
            PUBLIC_REPORT_REFERENCE_MODELED_YEARS,
            PUBLIC_REPORT_BUNDLE_REPORT_BASELINE_YEAR,
        ),
        "terminal_year": PUBLIC_REPORT_REFERENCE_TERMINAL_YEAR,
        "buildout_horizon_years": PUBLIC_REPORT_REFERENCE_BUILDOUT_HORIZON_YEARS,
    }
    current_bundle = {
        "starting_stock_year": current_starting_stock_year,
        "starting_stock_fields": starting_stock_fields,
        "starting_stock_source": current_starting_stock_source,
        "baseline_years_from_configs": baseline_years,
        "modeled_years": current_modeled_years,
        "first_projection_year": current_first_projection_year,
        "terminal_year": current_terminal_year,
        "buildout_horizon_years": current_buildout_horizon_years,
    }
    alignment_checks = {
        "starting_stock_year_matches": current_starting_stock_year
        == report_reference["starting_stock_year"],
        "starting_stock_source_matches": current_starting_stock_source
        == report_reference["starting_stock_source"],
        "terminal_year_matches": current_terminal_year == report_reference["terminal_year"],
        "buildout_horizon_matches": current_buildout_horizon_years
        == report_reference["buildout_horizon_years"],
        "modeled_years_match": current_modeled_years == report_reference["modeled_years"],
    }
    blocker_names = {
        "starting_stock_year_matches": "starting_stock_year_mismatch",
        "starting_stock_source_matches": "starting_stock_source_mismatch",
        "terminal_year_matches": "terminal_year_mismatch",
        "buildout_horizon_matches": "buildout_horizon_mismatch",
        "modeled_years_match": "modeled_years_mismatch",
    }
    parity_blockers = [
        blocker_names[name]
        for name, passed in alignment_checks.items()
        if not passed
    ]
    return {
        "contract_type": "report-parity-temporal-assumption-contract",
        "report_reference": report_reference,
        "current_bundle": current_bundle,
        "alignment_checks": alignment_checks,
        "parity_status": "aligned" if not parity_blockers else "blocked",
        "parity_blockers": parity_blockers,
        "implementation_decision": (
            "Encode the report-parity temporal contract as metadata only; do not change current "
            "bounded buildout behavior until the 2025 starting-stock source and modeled-year "
            "contract can be validated."
        ),
    }


def _build_public_report_assumption_registry(repo_root, output_dir):
    """Build the machine-readable assumption registry for the bounded public report bundle."""
    repo_root = Path(repo_root).resolve()
    smoke_configs = _load_public_report_bundle_smoke_configs(repo_root)
    output_labels = _build_public_report_output_labels(output_dir)
    temporal_assumptions = _build_public_report_temporal_assumptions(
        repo_root,
        output_dir,
        smoke_configs=smoke_configs,
    )
    capacity_constraint_assumptions = _build_public_report_capacity_constraint_assumptions(
        smoke_configs
    )
    spatial_grid_contract = _build_public_report_grid_resolution_contract(repo_root)
    allocation_assumption_contract = _build_public_report_allocation_assumption_contract(
        repo_root,
        output_dir=output_dir,
        smoke_configs=smoke_configs,
        temporal_assumptions=temporal_assumptions,
        spatial_grid_contract=spatial_grid_contract,
        capacity_constraint_assumptions=capacity_constraint_assumptions,
    )
    baxtel_schema_contract = _build_public_report_baxtel_schema_contract(repo_root)
    return {
        "registry_type": "bounded-public-report-assumption-registry",
        "bundle_label": "bounded-public-report-bundle",
        "scenario_name": EER_PUBLIC_SCENARIO,
        "bundle_mode": "bounded-public-approximation",
        "report_reference": {
            "baseline_year": PUBLIC_REPORT_BUNDLE_REPORT_BASELINE_YEAR,
            "modeled_years": list(PUBLIC_REPORT_REFERENCE_MODELED_YEARS),
            "buildout_horizon_years": PUBLIC_REPORT_REFERENCE_BUILDOUT_HORIZON_YEARS,
            "terminal_year": PUBLIC_REPORT_REFERENCE_TERMINAL_YEAR,
            "grid_resolution_km": PUBLIC_REPORT_REFERENCE_GRID_RESOLUTION_KM,
            "utilization_factor": PUBLIC_REPORT_REFERENCE_UTILIZATION_FACTOR,
            "initial_locations": PUBLIC_REPORT_REFERENCE_INITIAL_LOCATIONS,
            "max_site_addition_per_time_step_mw": PUBLIC_REPORT_REFERENCE_MAX_SITE_ADDITION_PER_TIME_STEP_MW,
        },
        "current_bundle": {
            "baseline_year": PUBLIC_REPORT_BUNDLE_BASELINE_YEAR,
            "grid_path": (repo_root / PUBLIC_REPORT_BUNDLE_GRID_PATH).as_posix(),
            "grid_priority": PUBLIC_REPORT_BUNDLE_GRID_PRIORITY,
            "feasible_land_rule": "developable_capacity_mw > 0; cells with NLCD water/wetland share across classes 11, 90, and 95 >= 0.5 are retained and clamped to 0 suitability percentile",
            "suitability_percentile_rule": "percentile rank of suitability_score across developable cells, with water/wetland-excluded cells clamped to 0",
            "ranked_summary_rule": "sort by suitability_percentile desc, suitability_score desc, developable_capacity_mw desc, sc_point_gid asc",
            "permitting_proxy_rule": "manually curated public permitting and ordinance evidence points from external-data/manifest/permitting-ordinance-evidence.csv are assigned to execution-grid cells and classified as restrictive ordinance evidence, public friction signal, permit activity record, or no public evidence recorded",
            "social_friction_proxy_rule": "manually curated public social-friction evidence points from external-data/manifest/social-friction-evidence.csv are assigned to execution-grid cells and classified as organized opposition evidence, public concern signal, community engagement record, or no public evidence recorded",
            "output_dir": Path(output_dir).as_posix(),
        },
        "scenario_inputs": [
            _build_public_report_scenario_input(output_label, config_path, config)
            for output_label, config_path, config in smoke_configs
        ],
        "temporal_assumptions": temporal_assumptions,
        "capacity_constraint_assumptions": capacity_constraint_assumptions,
        "spatial_grid_contract": spatial_grid_contract,
        "allocation_assumption_contract": allocation_assumption_contract,
        "baxtel_schema_contract": baxtel_schema_contract,
        "output_labels": output_labels,
        "limitation_carry_forward": [dict(entry) for entry in PUBLIC_REPORT_LIMITATION_ENTRIES],
        "assumption_gaps": [
            {
                "name": "report_reference_utilization_factor",
                "report_reference_value": PUBLIC_REPORT_REFERENCE_UTILIZATION_FACTOR,
                "current_bundle_value": capacity_constraint_assumptions["current_bundle"][
                    "utilization_factors"
                ],
                "status": "configured-in-current-bundle"
                if capacity_constraint_assumptions["alignment_checks"]["utilization_factor_matches"]
                else "mismatch",
            },
            {
                "name": "report_reference_per_site_capacity_constraint",
                "report_reference_value": PUBLIC_REPORT_REFERENCE_MAX_SITE_ADDITION_PER_TIME_STEP_MW,
                "current_bundle_value": capacity_constraint_assumptions["current_bundle"][
                    "max_site_addition_per_time_step_mw"
                ],
                "status": "configured-in-current-bundle"
                if capacity_constraint_assumptions["alignment_checks"]["per_time_step_limit_matches"]
                else "mismatch",
            },
            {
                "name": "report_reference_initial_locations",
                "report_reference_value": PUBLIC_REPORT_REFERENCE_INITIAL_LOCATIONS,
                "current_bundle_value": "execution-grid baseline field dc_capacity_mw_existing with 2022 baseline year",
                "status": "bounded-approximation",
            },
            {
                "name": "report_reference_temporal_assumptions",
                "report_reference_value": temporal_assumptions["report_reference"],
                "current_bundle_value": temporal_assumptions["current_bundle"],
                "status": temporal_assumptions["parity_status"],
                "parity_blockers": temporal_assumptions["parity_blockers"],
            },
            {
                "name": "report_reference_grid_resolution_km",
                "report_reference_value": PUBLIC_REPORT_REFERENCE_GRID_RESOLUTION_KM,
                "current_bundle_value": spatial_grid_contract["current_bundle"],
                "status": spatial_grid_contract["parity_status"],
                "parity_blockers": spatial_grid_contract["parity_blockers"],
            },
            {
                "name": "report_reference_allocation_assumptions",
                "report_reference_value": allocation_assumption_contract["report_reference"],
                "current_bundle_value": allocation_assumption_contract["current_bundle"],
                "status": allocation_assumption_contract["parity_status"],
                "parity_blockers": allocation_assumption_contract["parity_blockers"],
            },
            {
                "name": "report_reference_baxtel_schema_and_trained_suitability",
                "report_reference_value": baxtel_schema_contract["report_reference"],
                "current_bundle_value": baxtel_schema_contract["current_evidence"],
                "status": baxtel_schema_contract["parity_status"],
                "parity_blockers": baxtel_schema_contract["parity_blockers"],
                "decision": baxtel_schema_contract["decision"],
            },
        ],
    }


def _write_public_report_assumption_registry(repo_root, output_dir):
    """Write the machine-readable assumption registry for scenario-controlled report outputs."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    registry_path = output_dir / "public_report_assumption_registry.json"
    registry = _build_public_report_assumption_registry(repo_root, output_dir)
    registry_path.write_text(json.dumps(registry, indent=2))
    return registry_path


def _build_public_report_limitations_lines():
    """Render the carried-forward LinkedIn limitation and refinement set for the bundle."""
    lines = [
        "# Public Report Limitations",
        "",
        "This bundle carries forward the known limitations and candidate refinements named in the LinkedIn Part I and Part II descriptions.",
        "These items are not fully implemented in the current bounded public report surface and should be read as active fidelity limits.",
        "",
        "| Limitation | Status | Current posture | Output implication |",
        "| --- | --- | --- | --- |",
    ]
    for entry in PUBLIC_REPORT_LIMITATION_ENTRIES:
        lines.append(
            f"| {entry['title']} | {entry['status']} | {entry['current_posture']} | {entry['output_implication']} |"
        )
    return lines


def _write_public_report_limitations(output_dir):
    """Write the carried-forward limitations note for the current report bundle."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    limitations_path = output_dir / "public_report_limitations.md"
    limitations_path.write_text("\n".join(_build_public_report_limitations_lines()) + "\n")
    return limitations_path


def _load_public_report_state_boundaries(target_crs, cache_dir=None):
    """Load and cache official Census state boundaries for the bounded report map."""
    cache_dir = Path(cache_dir or Path.cwd() / ".cache" / "public-report-state-boundaries")
    cache_dir.mkdir(parents=True, exist_ok=True)
    zip_name = Path(urlparse(PUBLIC_REPORT_STATE_BOUNDARY_SOURCE_URL).path).name
    zip_path = cache_dir / zip_name
    if not zip_path.exists():
        _download_with_progress(PUBLIC_REPORT_STATE_BOUNDARY_SOURCE_URL, zip_path)

    with zipfile.ZipFile(zip_path) as archive:
        shapefile_name = next(name for name in archive.namelist() if name.endswith(".shp"))

    boundaries = gpd.read_file(f"zip://{zip_path}!{shapefile_name}")
    boundaries = boundaries[["NAME", "STUSPS", "geometry"]].rename(
        columns={"NAME": "state_name", "STUSPS": "state_code"}
    )
    boundaries = boundaries[boundaries["state_code"] != "PR"].reset_index(drop=True)
    if target_crs is not None and boundaries.crs != target_crs:
        boundaries = boundaries.to_crs(target_crs)
    return boundaries


def _write_public_report_state_boundaries(output_dir, suitability):
    """Write the derived state-boundary layer used by the bounded D3 map overlay."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    state_boundaries = _load_public_report_state_boundaries(
        suitability.crs,
        cache_dir=output_dir / "_cache",
    )
    state_boundary_path = output_dir / "public_report_state_boundaries.gpkg"
    state_boundaries.to_file(state_boundary_path, driver="GPKG")
    return state_boundaries, state_boundary_path


def _classify_public_report_hosting_capacity_proxy(min_headroom):
    """Classify coarse hosting-capacity proxy levels from NERC headroom values."""
    if pd.isna(min_headroom):
        return "unknown"
    if float(min_headroom) < 0:
        return "deficit"
    if float(min_headroom) < 5:
        return "tight"
    if float(min_headroom) < 15:
        return "moderate"
    return "headroom"


def _build_public_report_hosting_capacity_proxy_frame(repo_root, suitability):
    """Build a coarse hosting-capacity proxy layer for the bounded report bundle."""
    repo_root = Path(repo_root).resolve()
    regions_path = repo_root / "tests/data/downscale/inputs/regions/eer_adp_zones.gpkg"
    zone_groups_df = gpd.read_file(regions_path)
    zone_feature_df = build_nerc_emm_zone_feature_frame(zone_groups_df)

    grid_columns = [
        column
        for column in (
            "gid",
            "sc_point_gid",
            "latitude",
            "longitude",
            "developable_capacity_mw",
            "suitability_score",
            "geometry",
        )
        if column in suitability.columns
    ]
    grid_proxy_input = suitability[grid_columns].copy()
    proxy_df = build_nerc_grid_margin_feature_frame(grid_proxy_input, zone_feature_df)
    proxy_df["hosting_capacity_proxy_class"] = proxy_df[
        "min_margin_headroom_2026_2030"
    ].apply(_classify_public_report_hosting_capacity_proxy)
    proxy_df["hosting_capacity_proxy_note"] = (
        "Regional NERC reserve-margin headroom proxy, not local transmission hosting-capacity headroom."
    )

    ordered_columns = [
        column
        for column in (
            "gid",
            "sc_point_gid",
            "latitude",
            "longitude",
            "developable_capacity_mw",
            "suitability_score",
            "assessment_area",
            "emm_zone",
            "zone_group",
            "peak_season",
            "min_margin_headroom_2026_2030",
            "mean_margin_headroom_2026_2030",
            "hosting_capacity_proxy_class",
            "hosting_capacity_proxy_note",
            "geometry",
        )
        if column in proxy_df.columns
    ]
    return proxy_df[ordered_columns].copy()


def _write_public_report_hosting_capacity_proxy(output_dir, repo_root, suitability):
    """Write the bounded hosting-capacity proxy layer used by the report-bundle map."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    proxy_df = _build_public_report_hosting_capacity_proxy_frame(repo_root, suitability)
    proxy_path = output_dir / "public_report_hosting_capacity_proxy.gpkg"
    proxy_df.to_file(proxy_path, driver="GPKG")
    return proxy_df, proxy_path


def _resolve_public_report_nlcd_raster_path(repo_root):
    """Resolve the staged NLCD land-cover raster used for the bounded zoning proxy."""
    repo_root = Path(repo_root).resolve()
    raster_dir = repo_root / "external-data/raw/nlcd"
    tif_path = raster_dir / "Annual_NLCD_LndCov_2023_CU_C1V0.tif"
    if tif_path.exists():
        return tif_path.as_posix()

    zip_path = raster_dir / "Annual_NLCD_LndCov_2023_CU_C1V0.zip"
    if zip_path.exists():
        if not zipfile.is_zipfile(zip_path):
            raise FileNotFoundError(
                "Staged NLCD representative is unreadable. Refresh it with "
                "`python -m reVeal.public_data stage-dataset nlcd --repo-root . --download-representative --force`."
            )
        return f"zip://{zip_path}!Annual_NLCD_LndCov_2023_CU_C1V0.tif"

    raise FileNotFoundError(
        "NLCD representative raster is not staged. Run "
        "`python -m reVeal.public_data stage-dataset nlcd --repo-root . --download-representative`."
    )


def _label_public_report_nlcd_class(class_code):
    """Return a readable label for one NLCD class code."""
    if pd.isna(class_code):
        return None
    class_code = int(class_code)
    return PUBLIC_REPORT_ZONING_PROXY_NLCD_LABELS.get(class_code, f"Class {class_code}")


def _classify_public_report_zoning_proxy(developed_share, urban_core_share, dominant_nlcd_class):
    """Classify coarse zoning context from NLCD developed-land fractions."""
    if pd.isna(developed_share):
        return "unknown"
    if float(developed_share) < 0.05:
        return "non_developed_context"
    if dominant_nlcd_class == 24 or float(urban_core_share) >= 0.25:
        return "urban_core_context"
    return "developed_neighborhood_context"


def _summarize_public_report_nlcd_cell(src, geometry):
    """Summarize NLCD land-cover context for one suitability cell."""
    try:
        data, _ = raster_mask(src, [geometry.__geo_interface__], crop=True, filled=False, indexes=1)
    except ValueError:
        data = np.ma.masked_array(np.empty((1, 0, 0), dtype=np.int16), mask=True)

    values = data[0].compressed()
    if src.nodata is not None:
        values = values[values != src.nodata]
    if values.size == 0:
        return {
            "dominant_nlcd_class": None,
            "dominant_nlcd_label": None,
            "developed_share": None,
            "water_wetland_share": None,
            "water_wetland_excluded": None,
            "zoning_proxy_class": "unknown",
        }

    values = values.astype(np.int32, copy=False)
    unique_classes, counts = np.unique(values, return_counts=True)
    dominant_nlcd_class = int(unique_classes[np.argmax(counts)])
    total_valid = int(counts.sum())
    developed_share = float(
        np.isin(values, PUBLIC_REPORT_ZONING_PROXY_DEVELOPED_CLASSES).sum() / total_valid
    )
    water_wetland_share = float(
        np.isin(values, PUBLIC_REPORT_NLCD_WATER_WETLAND_CLASSES).sum() / total_valid
    )
    urban_core_share = float((values == 24).sum() / total_valid)
    return {
        "dominant_nlcd_class": dominant_nlcd_class,
        "dominant_nlcd_label": _label_public_report_nlcd_class(dominant_nlcd_class),
        "developed_share": developed_share,
        "water_wetland_share": water_wetland_share,
        "water_wetland_excluded": water_wetland_share
        >= PUBLIC_REPORT_NLCD_WATER_WETLAND_EXCLUSION_THRESHOLD,
        "zoning_proxy_class": _classify_public_report_zoning_proxy(
            developed_share,
            urban_core_share,
            dominant_nlcd_class,
        ),
    }


def _annotate_public_report_nlcd_context_frame(repo_root, frame):
    """Annotate a frame with staged NLCD land-cover context sampled per cell."""
    summary_columns = {
        "dominant_nlcd_class",
        "dominant_nlcd_label",
        "developed_share",
        "water_wetland_share",
        "water_wetland_excluded",
        "zoning_proxy_class",
    }
    if summary_columns.issubset(frame.columns):
        return frame.copy()

    raster_path = _resolve_public_report_nlcd_raster_path(repo_root)
    input_crs = frame.crs
    with rasterio.open(raster_path) as src:
        annotated = frame.to_crs(src.crs).copy()
        summaries = [
            _summarize_public_report_nlcd_cell(src, geometry) for geometry in annotated.geometry
        ]
    annotated = annotated.join(pd.DataFrame.from_records(summaries, index=annotated.index))
    if input_crs is not None and annotated.crs != input_crs:
        annotated = annotated.to_crs(input_crs)
    return annotated


def _build_public_report_zoning_proxy_frame(repo_root, suitability):
    """Build a coarse zoning proxy from staged NLCD developed-land context."""
    proxy_df = _annotate_public_report_nlcd_context_frame(repo_root, suitability)
    proxy_df["zoning_proxy_note"] = (
        "NLCD developed-land context proxy, not parcel zoning or allowed-use entitlement."
    )

    ordered_columns = [
        column
        for column in (
            "gid",
            "sc_point_gid",
            "latitude",
            "longitude",
            "developable_capacity_mw",
            "suitability_score",
            "dominant_nlcd_class",
            "dominant_nlcd_label",
            "developed_share",
            "zoning_proxy_class",
            "zoning_proxy_note",
            "geometry",
        )
        if column in proxy_df.columns
    ]
    return proxy_df[ordered_columns].copy()


def _write_public_report_zoning_proxy(output_dir, repo_root, suitability):
    """Write the bounded zoning proxy layer used by the report-bundle map."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    proxy_df = _build_public_report_zoning_proxy_frame(repo_root, suitability)
    proxy_path = output_dir / "public_report_zoning_proxy.gpkg"
    proxy_df.to_file(proxy_path, driver="GPKG")
    return proxy_df, proxy_path


def _empty_public_report_evidence_frame(evidence_columns):
    """Return an empty evidence manifest frame with the expected schema."""
    return pd.DataFrame(columns=evidence_columns)


def _load_public_report_evidence_manifest(repo_root, manifest_path, evidence_columns, label):
    """Load a staged point-evidence manifest if present."""
    repo_root = Path(repo_root).resolve()
    manifest_path = repo_root / manifest_path
    if not manifest_path.exists():
        return _empty_public_report_evidence_frame(evidence_columns)

    evidence = pd.read_csv(manifest_path, dtype=str).fillna("")
    missing_columns = [column for column in evidence_columns if column not in evidence.columns]
    if missing_columns:
        raise ValueError(
            f"{label} evidence manifest is missing required columns: "
            + ", ".join(missing_columns)
        )

    evidence = evidence.loc[:, evidence_columns].copy()
    evidence["latitude"] = pd.to_numeric(evidence["latitude"], errors="coerce")
    evidence["longitude"] = pd.to_numeric(evidence["longitude"], errors="coerce")
    evidence = evidence.dropna(subset=["latitude", "longitude"]).reset_index(drop=True)
    evidence["evidence_type"] = evidence["evidence_type"].str.strip().str.lower()
    evidence["friction_level"] = evidence["friction_level"].str.strip().str.lower()
    evidence["evidence_id"] = evidence["evidence_id"].str.strip()
    return evidence


def _load_public_report_permitting_evidence(repo_root):
    """Load the staged public permitting and ordinance evidence manifest if present."""
    return _load_public_report_evidence_manifest(
        repo_root,
        PUBLIC_REPORT_PERMITTING_EVIDENCE_MANIFEST_PATH,
        PUBLIC_REPORT_PERMITTING_EVIDENCE_COLUMNS,
        "Permitting",
    )


def _load_public_report_social_friction_evidence(repo_root):
    """Load the staged public social-friction evidence manifest if present."""
    return _load_public_report_evidence_manifest(
        repo_root,
        PUBLIC_REPORT_SOCIAL_FRICTION_EVIDENCE_MANIFEST_PATH,
        PUBLIC_REPORT_SOCIAL_FRICTION_EVIDENCE_COLUMNS,
        "Social-friction",
    )


def _public_report_cell_key_column(frame):
    """Return the stable cell-key column used by report-bundle grid surfaces."""
    if "sc_point_gid" in frame.columns:
        return "sc_point_gid"
    if "gid" in frame.columns:
        return "gid"
    raise ValueError("Report-bundle surfaces require sc_point_gid or gid for cell joins")


def _classify_public_report_permitting_proxy(
    evidence_count,
    restrictive_evidence_count,
    friction_evidence_count,
):
    """Classify the manifest-driven permitting evidence signal for one cell."""
    if int(evidence_count) == 0:
        return "no_public_evidence_recorded"
    if int(restrictive_evidence_count) > 0:
        return "restrictive_ordinance_evidence"
    if int(friction_evidence_count) > 0:
        return "public_friction_signal"
    return "permit_activity_record"


def _assign_public_report_evidence_to_cells(evidence, suitability, evidence_columns):
    """Assign evidence points to suitability cells using the grid geometry."""
    if evidence.empty:
        return pd.DataFrame(columns=["cell_key", *evidence_columns])

    cell_key_column = _public_report_cell_key_column(suitability)
    points = gpd.GeoDataFrame(
        evidence.copy(),
        geometry=gpd.points_from_xy(evidence["longitude"], evidence["latitude"]),
        crs="EPSG:4326",
    )
    if suitability.crs is not None and points.crs != suitability.crs:
        points = points.to_crs(suitability.crs)

    cell_frame = suitability[[cell_key_column, "geometry"]].copy()
    assignments = []
    for evidence_row in points.itertuples(index=False):
        point = evidence_row.geometry
        matched_cell_key = None
        for cell_row in cell_frame.itertuples(index=False):
            if cell_row.geometry is not None and cell_row.geometry.covers(point):
                matched_cell_key = getattr(cell_row, cell_key_column)
                break
        if matched_cell_key is None:
            continue
        record = {column: getattr(evidence_row, column) for column in evidence_columns}
        record["cell_key"] = matched_cell_key
        assignments.append(record)

    return pd.DataFrame(assignments)


def _assign_public_report_permitting_evidence_to_cells(evidence, suitability):
    """Assign permitting evidence points to suitability cells using the grid geometry."""
    return _assign_public_report_evidence_to_cells(
        evidence,
        suitability,
        PUBLIC_REPORT_PERMITTING_EVIDENCE_COLUMNS,
    )


def _assign_public_report_social_friction_evidence_to_cells(evidence, suitability):
    """Assign social-friction evidence points to suitability cells using the grid geometry."""
    return _assign_public_report_evidence_to_cells(
        evidence,
        suitability,
        PUBLIC_REPORT_SOCIAL_FRICTION_EVIDENCE_COLUMNS,
    )


def _join_unique_public_report_values(values):
    """Join non-empty unique manifest values into a stable semicolon-delimited field."""
    clean_values = sorted({str(value).strip() for value in values if str(value).strip()})
    return ";".join(clean_values)


def _build_public_report_permitting_proxy_frame(repo_root, suitability):
    """Build a bounded permitting and ordinance evidence proxy layer."""
    proxy_df = suitability.copy()
    cell_key_column = _public_report_cell_key_column(proxy_df)
    cell_keys = proxy_df[cell_key_column].astype(str)

    proxy_df["evidence_count"] = 0
    proxy_df["restrictive_evidence_count"] = 0
    proxy_df["friction_evidence_count"] = 0
    proxy_df["permit_activity_evidence_count"] = 0
    proxy_df["source_evidence_ids"] = ""
    proxy_df["permitting_evidence_types"] = ""
    proxy_df["permitting_jurisdictions"] = ""

    evidence = _load_public_report_permitting_evidence(repo_root)
    assignments = _assign_public_report_permitting_evidence_to_cells(evidence, suitability)
    if not assignments.empty:
        assignments["is_restrictive_evidence"] = assignments["evidence_type"].isin(
            PUBLIC_REPORT_PERMITTING_RESTRICTIVE_TYPES
        ) | assignments["friction_level"].isin(PUBLIC_REPORT_PERMITTING_RESTRICTIVE_LEVELS)
        assignments["is_friction_evidence"] = assignments["evidence_type"].isin(
            PUBLIC_REPORT_PERMITTING_FRICTION_TYPES
        ) | assignments["friction_level"].isin(PUBLIC_REPORT_PERMITTING_FRICTION_LEVELS)
        assignments["is_permit_activity_evidence"] = ~(
            assignments["is_restrictive_evidence"] | assignments["is_friction_evidence"]
        )

        grouped = assignments.groupby(assignments["cell_key"].astype(str), sort=False)
        for cell_key, group in grouped:
            row_mask = cell_keys == cell_key
            proxy_df.loc[row_mask, "evidence_count"] = int(len(group))
            proxy_df.loc[row_mask, "restrictive_evidence_count"] = int(
                group["is_restrictive_evidence"].sum()
            )
            proxy_df.loc[row_mask, "friction_evidence_count"] = int(
                group["is_friction_evidence"].sum()
            )
            proxy_df.loc[row_mask, "permit_activity_evidence_count"] = int(
                group["is_permit_activity_evidence"].sum()
            )
            proxy_df.loc[row_mask, "source_evidence_ids"] = _join_unique_public_report_values(
                group["evidence_id"]
            )
            proxy_df.loc[row_mask, "permitting_evidence_types"] = _join_unique_public_report_values(
                group["evidence_type"]
            )
            proxy_df.loc[row_mask, "permitting_jurisdictions"] = _join_unique_public_report_values(
                group["jurisdiction_name"]
            )

    proxy_df["permitting_proxy_class"] = [
        _classify_public_report_permitting_proxy(evidence_count, restrictive_count, friction_count)
        for evidence_count, restrictive_count, friction_count in zip(
            proxy_df["evidence_count"],
            proxy_df["restrictive_evidence_count"],
            proxy_df["friction_evidence_count"],
            strict=False,
        )
    ]
    proxy_df["permitting_proxy_note"] = (
        "Manifest-driven public permitting and ordinance evidence proxy, not permit readiness, legal entitlement, or ordinance compatibility."
    )

    ordered_columns = [
        column
        for column in (
            "gid",
            "sc_point_gid",
            "latitude",
            "longitude",
            "developable_capacity_mw",
            "suitability_score",
            "evidence_count",
            "restrictive_evidence_count",
            "friction_evidence_count",
            "permit_activity_evidence_count",
            "source_evidence_ids",
            "permitting_evidence_types",
            "permitting_jurisdictions",
            "permitting_proxy_class",
            "permitting_proxy_note",
            "geometry",
        )
        if column in proxy_df.columns
    ]
    return proxy_df[ordered_columns].copy()


def _write_public_report_permitting_proxy(output_dir, repo_root, suitability):
    """Write the bounded permitting evidence proxy layer used by the report-bundle map."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    proxy_df = _build_public_report_permitting_proxy_frame(repo_root, suitability)
    proxy_path = output_dir / "public_report_permitting_proxy.gpkg"
    proxy_df.to_file(proxy_path, driver="GPKG")
    return proxy_df, proxy_path


def _classify_public_report_social_friction_proxy(
    evidence_count,
    opposition_evidence_count,
    concern_evidence_count,
):
    """Classify the manifest-driven social-friction evidence signal for one cell."""
    if int(evidence_count) == 0:
        return "no_public_evidence_recorded"
    if int(opposition_evidence_count) > 0:
        return "organized_opposition_evidence"
    if int(concern_evidence_count) > 0:
        return "public_concern_signal"
    return "community_engagement_record"


def _build_public_report_social_friction_proxy_frame(repo_root, suitability):
    """Build a bounded social-friction evidence proxy layer."""
    proxy_df = suitability.copy()
    cell_key_column = _public_report_cell_key_column(proxy_df)
    cell_keys = proxy_df[cell_key_column].astype(str)

    proxy_df["evidence_count"] = 0
    proxy_df["opposition_evidence_count"] = 0
    proxy_df["concern_evidence_count"] = 0
    proxy_df["engagement_evidence_count"] = 0
    proxy_df["source_evidence_ids"] = ""
    proxy_df["social_evidence_types"] = ""
    proxy_df["social_communities"] = ""

    evidence = _load_public_report_social_friction_evidence(repo_root)
    assignments = _assign_public_report_social_friction_evidence_to_cells(evidence, suitability)
    if not assignments.empty:
        assignments["is_opposition_evidence"] = assignments["evidence_type"].isin(
            PUBLIC_REPORT_SOCIAL_FRICTION_OPPOSITION_TYPES
        ) | assignments["friction_level"].isin(PUBLIC_REPORT_SOCIAL_FRICTION_OPPOSITION_LEVELS)
        assignments["is_concern_evidence"] = assignments["evidence_type"].isin(
            PUBLIC_REPORT_SOCIAL_FRICTION_CONCERN_TYPES
        ) | assignments["friction_level"].isin(PUBLIC_REPORT_SOCIAL_FRICTION_CONCERN_LEVELS)
        assignments["is_engagement_evidence"] = ~(
            assignments["is_opposition_evidence"] | assignments["is_concern_evidence"]
        )

        grouped = assignments.groupby(assignments["cell_key"].astype(str), sort=False)
        for cell_key, group in grouped:
            row_mask = cell_keys == cell_key
            proxy_df.loc[row_mask, "evidence_count"] = int(len(group))
            proxy_df.loc[row_mask, "opposition_evidence_count"] = int(
                group["is_opposition_evidence"].sum()
            )
            proxy_df.loc[row_mask, "concern_evidence_count"] = int(
                group["is_concern_evidence"].sum()
            )
            proxy_df.loc[row_mask, "engagement_evidence_count"] = int(
                group["is_engagement_evidence"].sum()
            )
            proxy_df.loc[row_mask, "source_evidence_ids"] = _join_unique_public_report_values(
                group["evidence_id"]
            )
            proxy_df.loc[row_mask, "social_evidence_types"] = _join_unique_public_report_values(
                group["evidence_type"]
            )
            proxy_df.loc[row_mask, "social_communities"] = _join_unique_public_report_values(
                group["community_name"]
            )

    proxy_df["social_friction_proxy_class"] = [
        _classify_public_report_social_friction_proxy(evidence_count, opposition_count, concern_count)
        for evidence_count, opposition_count, concern_count in zip(
            proxy_df["evidence_count"],
            proxy_df["opposition_evidence_count"],
            proxy_df["concern_evidence_count"],
            strict=False,
        )
    ]
    proxy_df["social_friction_proxy_note"] = (
        "Manifest-driven public social-friction evidence proxy, not a measure of actual community acceptance or social license."
    )

    ordered_columns = [
        column
        for column in (
            "gid",
            "sc_point_gid",
            "latitude",
            "longitude",
            "developable_capacity_mw",
            "suitability_score",
            "evidence_count",
            "opposition_evidence_count",
            "concern_evidence_count",
            "engagement_evidence_count",
            "source_evidence_ids",
            "social_evidence_types",
            "social_communities",
            "social_friction_proxy_class",
            "social_friction_proxy_note",
            "geometry",
        )
        if column in proxy_df.columns
    ]
    return proxy_df[ordered_columns].copy()


def _write_public_report_social_friction_proxy(output_dir, repo_root, suitability):
    """Write the bounded social-friction proxy layer used by the report-bundle map."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    proxy_df = _build_public_report_social_friction_proxy_frame(repo_root, suitability)
    proxy_path = output_dir / "public_report_social_friction_proxy.gpkg"
    proxy_df.to_file(proxy_path, driver="GPKG")
    return proxy_df, proxy_path


def _build_public_report_suitability_map_rows(frame, limit=12):
    """Prepare ranked suitability rows for embedding in the HTML map page."""
    safe = frame.head(limit).copy()
    safe = safe.replace({np.nan: None})
    return safe.to_dict(orient="records")


def _public_report_json_records(frame):
    """Return JSON-safe records from a pandas frame."""
    if frame.empty:
        return []
    return json.loads(frame.to_json(orient="records"))


def _build_public_report_buildout_timeline_payload(output_dir):
    """Build the embedded year-by-year cumulative buildout payload for the HTML map."""
    output_dir = Path(output_dir)
    source_specs = [
        {
            "id": "total",
            "label": "Total EER buildout",
            "output_name": "public_eer_total_downscaled",
            "path": output_dir / "public_eer_total_downscaled_cumulative_buildout.gpkg",
        },
        {
            "id": "regional",
            "label": "Grouped regional EER buildout",
            "output_name": "public_eer_regional_downscaled",
            "path": output_dir / "public_eer_regional_downscaled_cumulative_buildout.gpkg",
        },
    ]
    buildout_columns = [
        "sc_point_gid",
        "gid",
        "year",
        "zone_group",
        "baseline_total_dc_load_mw",
        "cumulative_new_dc_load_mw",
        "cumulative_total_dc_load_mw",
        "new_dc_capacity_mw",
        "baseline_total_dc_capacity_mw",
        "cumulative_new_dc_capacity_mw",
        "cumulative_total_dc_capacity_mw",
        "utilization_factor",
        "max_site_addition_per_time_step_mw",
        "per_site_time_step_capacity_limit_exceeded",
        "geometry",
    ]
    sources = []
    for spec in source_specs:
        if not spec["path"].exists():
            continue
        buildout_frame = gpd.read_file(spec["path"])
        if "year" not in buildout_frame.columns:
            continue
        selected_columns = [
            column for column in buildout_columns if column in buildout_frame.columns
        ]
        buildout_frame = buildout_frame[selected_columns].copy()
        years = sorted(int(year) for year in buildout_frame["year"].dropna().unique())
        sources.append(
            {
                "id": spec["id"],
                "label": spec["label"],
                "outputName": spec["output_name"],
                "path": spec["path"].as_posix(),
                "years": years,
                "geoJson": json.loads(buildout_frame.to_json()),
            }
        )

    summary_path = output_dir / "public_report_bundle_cumulative_buildout_summary.csv"
    summary_rows = []
    if summary_path.exists():
        summary = pd.read_csv(summary_path)
        source_id_by_output_name = {
            spec["output_name"]: spec["id"] for spec in source_specs
        }
        if "source_output_name" in summary.columns:
            summary["source_id"] = summary["source_output_name"].map(
                source_id_by_output_name
            )
        summary_rows = _public_report_json_records(summary)

    default_source = sources[0]["id"] if sources else None
    default_year = max(sources[0]["years"]) if sources and sources[0]["years"] else None
    return {
        "sources": sources,
        "summaryRows": summary_rows,
        "metrics": [
            {
                "id": "cumulative_total_dc_load_mw",
                "label": "Cumulative portfolio load",
                "shortLabel": "Portfolio load",
                "unit": "MW",
            },
            {
                "id": "cumulative_new_dc_load_mw",
                "label": "Cumulative growth load",
                "shortLabel": "Growth load",
                "unit": "MW",
            },
            {
                "id": "cumulative_total_dc_capacity_mw",
                "label": "Cumulative capacity equivalent",
                "shortLabel": "Capacity equivalent",
                "unit": "MW",
            },
        ],
        "defaultSourceId": default_source,
        "defaultMetricId": "cumulative_total_dc_load_mw",
        "defaultYear": default_year,
    }


def _write_public_report_suitability_map(
    output_dir,
    feasible_land,
    suitability,
    ranked_suitability,
    state_boundaries,
    zoning_proxy,
    permitting_proxy,
    social_friction_proxy,
    hosting_proxy,
):
    """Render a single-page D3 suitability map for quick visual review of the bounded bundle."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    map_path = output_dir / "public_report_suitability_map.html"

    feasible_geojson = json.loads(feasible_land.to_json())
    suitability_geojson = json.loads(suitability.to_json())
    state_boundary_geojson = json.loads(state_boundaries.to_json())
    zoning_proxy_geojson = json.loads(zoning_proxy.to_json())
    permitting_proxy_geojson = json.loads(permitting_proxy.to_json())
    social_friction_proxy_geojson = json.loads(social_friction_proxy.to_json())
    hosting_proxy_geojson = json.loads(hosting_proxy.to_json())
    ranked_rows = _build_public_report_suitability_map_rows(ranked_suitability)
    buildout_timeline = _build_public_report_buildout_timeline_payload(output_dir)

    suitability_percentiles = [
        feature.get("properties", {}).get("suitability_percentile")
        for feature in suitability_geojson.get("features", [])
        if feature.get("properties", {}).get("suitability_percentile") is not None
    ]
    percentile_min = min(suitability_percentiles) if suitability_percentiles else 0.0
    percentile_max = max(suitability_percentiles) if suitability_percentiles else 100.0
    map_summary = {
        "feasibleCellCount": int(len(feasible_land)),
        "mappedCellCount": int(len(suitability)),
        "topPercentile": float(percentile_max),
        "percentileMin": float(percentile_min),
        "percentileMax": float(percentile_max),
    }

    html = f"""<!DOCTYPE html>
<html lang=\"en\" data-theme-mode=\"system\" data-theme=\"light\">
<head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <title>Executive Siting and Buildout View</title>
    <script src=\"https://d3js.org/d3.v7.min.js\"></script>
    <script>
        (() => {{
            const THEME_STORAGE_KEY = "reveal-report-theme";
            const validThemeModes = ["light", "dark", "system"];
            const readStoredThemeMode = () => {{
                try {{
                    return localStorage.getItem(THEME_STORAGE_KEY) || "system";
                }} catch (error) {{
                    return "system";
                }}
            }};
            const storedMode = readStoredThemeMode();
            const mode = validThemeModes.includes(storedMode) ? storedMode : "system";
            const prefersDark = window.matchMedia?.("(prefers-color-scheme: dark)").matches;
            const resolvedTheme = mode === "dark" || (mode === "system" && prefersDark) ? "dark" : "light";
            document.documentElement.dataset.themeMode = mode;
            document.documentElement.dataset.theme = resolvedTheme;
        }})();
    </script>
    <style>
        :root {{
            color-scheme: light;
            --paper: #f5efe4;
            --ink: #1f2927;
            --muted: #6c7367;
            --line: #d8cebd;
            --card: rgba(255, 252, 246, 0.94);
            --card-border: rgba(127, 115, 88, 0.18);
            --shadow: rgba(37, 34, 24, 0.12);
            --accent: #0c5c59;
            --accent-soft: #d8ebe7;
            --active-text: #f7f3ea;
            --body-background: radial-gradient(circle at top left, rgba(20, 92, 89, 0.16), transparent 28%), radial-gradient(circle at bottom right, rgba(181, 131, 65, 0.14), transparent 24%), linear-gradient(180deg, #f9f5ee 0%, #efe6d8 100%);
            --map-background: linear-gradient(180deg, rgba(255,255,255,0.7), rgba(239,230,216,0.72));
            --map-cover: rgba(255, 255, 255, 0.42);
            --note-bg: rgba(216, 235, 231, 0.8);
            --note-ink: #21403f;
            --layer-panel-bg: rgba(245, 239, 228, 0.82);
            --stat-bg: rgba(12, 92, 89, 0.06);
            --stat-border: rgba(12, 92, 89, 0.08);
            --control-bg: rgba(255, 250, 240, 0.92);
            --control-border: rgba(45, 40, 29, 0.14);
            --control-shadow: rgba(24, 35, 35, 0.12);
            --legend-border: rgba(45, 40, 29, 0.14);
            --row-active-bg: rgba(12, 92, 89, 0.12);
            --feasible-fill: #ddd2bf;
            --cell-stroke: rgba(255, 255, 255, 0.92);
            --state-stroke: rgba(31, 41, 39, 0.42);
            --hex-state-stroke: rgba(31, 41, 39, 0.64);
            --active-stroke: #c45c13;
            --active-filter: drop-shadow(0 0 3px rgba(196, 92, 19, 0.45));
            --tooltip-bg: rgba(30, 36, 35, 0.94);
            --tooltip-ink: #f7f3ea;
            --empty-map-text: #5a625a;
        }}
        html[data-theme="dark"] {{
            color-scheme: dark;
            --paper: #101715;
            --ink: #edf2eb;
            --muted: #aeb8ad;
            --line: #33403b;
            --card: rgba(24, 31, 29, 0.94);
            --card-border: rgba(187, 205, 195, 0.16);
            --shadow: rgba(0, 0, 0, 0.34);
            --accent: #75c9bd;
            --accent-soft: #173b39;
            --active-text: #071311;
            --body-background: radial-gradient(circle at top left, rgba(117, 201, 189, 0.12), transparent 28%), radial-gradient(circle at bottom right, rgba(218, 153, 76, 0.12), transparent 24%), linear-gradient(180deg, #0b1110 0%, #161d1b 100%);
            --map-background: linear-gradient(180deg, rgba(21, 29, 27, 0.96), rgba(13, 18, 17, 0.96));
            --map-cover: rgba(9, 13, 12, 0.36);
            --note-bg: rgba(28, 63, 59, 0.72);
            --note-ink: #d7eee9;
            --layer-panel-bg: rgba(23, 30, 28, 0.9);
            --stat-bg: rgba(117, 201, 189, 0.1);
            --stat-border: rgba(117, 201, 189, 0.18);
            --control-bg: rgba(20, 27, 25, 0.94);
            --control-border: rgba(187, 205, 195, 0.18);
            --control-shadow: rgba(0, 0, 0, 0.38);
            --legend-border: rgba(187, 205, 195, 0.22);
            --row-active-bg: rgba(117, 201, 189, 0.16);
            --feasible-fill: #3a4037;
            --cell-stroke: rgba(13, 18, 17, 0.78);
            --state-stroke: rgba(225, 236, 230, 0.54);
            --hex-state-stroke: rgba(225, 236, 230, 0.74);
            --active-stroke: #f0a45f;
            --active-filter: drop-shadow(0 0 4px rgba(240, 164, 95, 0.6));
            --tooltip-bg: rgba(236, 241, 234, 0.96);
            --tooltip-ink: #101715;
            --empty-map-text: #d0d8d0;
        }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            font-family: \"Avenir Next\", \"Gill Sans\", sans-serif;
            color: var(--ink);
            background: var(--body-background);
            min-height: 100vh;
        }}
        .page {{
            width: min(1360px, calc(100vw - 32px));
            margin: 0 auto;
            padding: 28px 0 36px;
        }}
        .hero {{
            display: grid;
            gap: 10px;
            margin-bottom: 18px;
        }}
        .hero h1 {{
            margin: 0;
            font-family: Charter, \"Iowan Old Style\", \"Palatino Linotype\", serif;
            font-size: clamp(2rem, 4vw, 3.4rem);
            line-height: 0.96;
            letter-spacing: -0.03em;
        }}
        .hero p {{
            margin: 0;
            max-width: 72ch;
            font-size: 1rem;
            line-height: 1.55;
            color: var(--muted);
        }}
        .layout {{
            display: grid;
            grid-template-columns: minmax(0, 1.8fr) minmax(320px, 0.95fr);
            gap: 18px;
            align-items: start;
        }}
        .card {{
            background: var(--card);
            border: 1px solid var(--card-border);
            border-radius: 24px;
            box-shadow: 0 18px 40px var(--shadow);
            backdrop-filter: blur(8px);
        }}
        .map-card {{
            overflow: hidden;
            position: relative;
        }}
        .map-frame {{
            padding: 18px 18px 8px;
        }}
        #map {{
            display: block;
            width: 100%;
            height: auto;
            min-height: 620px;
            border-radius: 18px;
            background: var(--map-background);
        }}
        .legend {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            padding: 0 18px 18px;
            font-size: 0.93rem;
            color: var(--muted);
        }}
        .legend-bar {{
            flex: 1;
            height: 12px;
            border-radius: 999px;
            background: linear-gradient(90deg, #440154 0%, #3b528b 25%, #21918c 60%, #5dc863 82%, #fde725 100%);
            border: 1px solid var(--legend-border);
        }}
        .panel {{
            padding: 18px;
            display: grid;
            gap: 16px;
        }}
        .eyebrow {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-size: 0.74rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: var(--accent);
        }}
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 12px;
        }}
        .stat {{
            padding: 14px;
            border-radius: 18px;
            background: var(--stat-bg);
            border: 1px solid var(--stat-border);
        }}
        .stat-label {{
            font-size: 0.72rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: var(--muted);
            margin-bottom: 6px;
        }}
        .stat-value {{
            font-size: 1.5rem;
            font-weight: 600;
        }}
        .note {{
            padding: 14px 16px;
            border-radius: 18px;
            background: var(--note-bg);
            color: var(--note-ink);
            line-height: 1.5;
        }}
        .layer-panel {{
            background: var(--layer-panel-bg);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.92rem;
        }}
        th, td {{
            padding: 10px 8px;
            text-align: left;
            border-bottom: 1px solid var(--line);
            vertical-align: top;
        }}
        th {{
            font-size: 0.74rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--muted);
        }}
        tbody tr {{
            transition: background-color 120ms ease;
        }}
        tbody tr.is-active {{
            background: var(--row-active-bg);
        }}
        .cell-name {{
            display: block;
            font-weight: 600;
            color: var(--ink);
        }}
        .cell-meta {{
            display: block;
            margin-top: 4px;
            font-size: 0.78rem;
            color: var(--muted);
        }}
        .layer-stack {{
            display: grid;
            gap: 10px;
        }}
        .layer-toggle {{
            appearance: none;
            border: 1px solid rgba(12, 92, 89, 0.22);
            background: rgba(12, 92, 89, 0.06);
            color: var(--accent);
            border-radius: 999px;
            padding: 10px 14px;
            font: inherit;
            font-weight: 600;
            text-align: left;
            cursor: pointer;
            transition: background-color 120ms ease, color 120ms ease, border-color 120ms ease;
        }}
        .layer-toggle.is-active {{
            background: var(--accent);
            color: var(--active-text);
            border-color: var(--accent);
        }}
        .map-controls {{
            position: absolute;
            top: 16px;
            right: 16px;
            display: flex;
            flex-wrap: wrap;
            justify-content: flex-end;
            gap: 8px;
            max-width: calc(100% - 32px);
            z-index: 2;
        }}
        .mode-control,
        .shape-control {{
            display: inline-grid;
            grid-auto-flow: column;
            gap: 4px;
            padding: 4px;
            border-radius: 8px;
            background: var(--control-bg);
            border: 1px solid var(--control-border);
            box-shadow: 0 10px 24px var(--control-shadow);
        }}
        .theme-control {{
            display: inline-grid;
            grid-auto-flow: column;
            gap: 4px;
            padding: 4px;
            border-radius: 8px;
            background: var(--control-bg);
            border: 1px solid var(--control-border);
            box-shadow: 0 10px 24px var(--control-shadow);
        }}
        .mode-toggle,
        .shape-toggle,
        .theme-toggle {{
            border: 0;
            border-radius: 6px;
            background: transparent;
            color: var(--muted);
            padding: 7px 10px;
            font: inherit;
            font-size: 0.82rem;
            cursor: pointer;
        }}
        .mode-toggle.is-active,
        .shape-toggle.is-active,
        .theme-toggle.is-active {{
            background: var(--accent);
            color: var(--active-text);
        }}
        .timeline-panel {{
            display: grid;
            gap: 12px;
        }}
        .timeline-controls {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 10px;
        }}
        .timeline-control {{
            display: grid;
            gap: 5px;
            color: var(--muted);
            font-size: 0.78rem;
        }}
        .timeline-control select,
        .timeline-control input[type="range"] {{
            width: 100%;
            min-width: 0;
        }}
        .timeline-control select {{
            border: 1px solid var(--control-border);
            border-radius: 8px;
            padding: 8px 10px;
            color: var(--ink);
            background: var(--control-bg);
            font: inherit;
        }}
        .timeline-year-row {{
            grid-column: 1 / -1;
        }}
        .timeline-summary {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 8px;
        }}
        .timeline-summary .stat {{
            border-radius: 12px;
            padding: 10px;
        }}
        .timeline-summary .stat-value {{
            font-size: 1.05rem;
        }}
        .layer-note {{
            margin: 0;
            color: var(--muted);
            font-size: 0.84rem;
            line-height: 1.5;
        }}
        .layer-legend {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 8px 12px;
            font-size: 0.8rem;
            color: var(--muted);
        }}
        .layer-chip {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }}
        .layer-swatch {{
            width: 12px;
            height: 12px;
            border-radius: 999px;
            border: 1px solid var(--legend-border);
        }}
        .map-background {{
            fill: var(--map-cover);
        }}
        .feasible-hex {{
            fill: var(--feasible-fill);
            stroke: var(--cell-stroke);
        }}
        .suitability-cell,
        .buildout-cell {{
            transition: stroke 120ms ease, stroke-width 120ms ease, filter 120ms ease;
            stroke: var(--cell-stroke);
        }}
        .suitability-cell.is-active,
        .buildout-cell.is-active {{
            stroke: var(--active-stroke);
            stroke-width: 1.8;
            filter: var(--active-filter);
        }}
        .zoning-proxy-cell {{
            pointer-events: none;
        }}
        .permitting-proxy-cell {{
            pointer-events: none;
        }}
        .social-friction-proxy-cell {{
            pointer-events: none;
        }}
        .hosting-proxy-cell {{
            pointer-events: none;
        }}
        .state-boundary {{
            pointer-events: none;
            transition: opacity 120ms ease, stroke 120ms ease;
            stroke: var(--state-stroke);
        }}
        .state-boundary.is-display-reference {{
            opacity: 0.55;
        }}
        .hex-state-boundary {{
            pointer-events: none;
            fill: none;
            stroke: var(--hex-state-stroke);
            stroke-width: 1.25;
            stroke-linecap: round;
            stroke-linejoin: round;
        }}
        .tooltip {{
            position: fixed;
            pointer-events: none;
            opacity: 0;
            transform: translate(-50%, calc(-100% - 14px));
            background: var(--tooltip-bg);
            color: var(--tooltip-ink);
            padding: 10px 12px;
            border-radius: 12px;
            font-size: 0.88rem;
            line-height: 1.45;
            box-shadow: 0 12px 22px rgba(0, 0, 0, 0.24);
            transition: opacity 120ms ease;
            max-width: 260px;
            z-index: 10;
        }}
        @media (max-width: 980px) {{
            .layout {{
                grid-template-columns: 1fr;
            }}
            #map {{
                min-height: 480px;
            }}
        }}
    </style>
</head>
<body>
    <div class=\"page\">
        <header class=\"hero\">
            <span class=\"eyebrow\">Executive Planning Readout</span>
            <h1>Executive Siting and Buildout View</h1>
            <p>This report summarizes where the bounded public approximation concentrates data-center siting advantage, how modeled demand accumulates over time, and which contextual risks should shape the next leadership discussion. Use it for portfolio screening and prioritization, not as a parcel-level entitlement or report-equivalent reproduction.</p>
        </header>
        <div class=\"layout\">
            <section class=\"card map-card\">
                <div class=\"map-frame\">
                    <div class="map-controls">
                        <div class="theme-control" role="group" aria-label="Theme">
                            <button type="button" class="theme-toggle" id="system-theme-toggle" aria-pressed="false">System</button>
                            <button type="button" class="theme-toggle" id="light-theme-toggle" aria-pressed="false">Light</button>
                            <button type="button" class="theme-toggle" id="dark-theme-toggle" aria-pressed="false">Dark</button>
                        </div>
                        <div class="shape-control" role="group" aria-label="Cell display shape">
                            <button type="button" class="shape-toggle is-active" id="square-shape-toggle" aria-pressed="true">Squares</button>
                            <button type="button" class="shape-toggle" id="hex-shape-toggle" aria-pressed="false">Hexes</button>
                        </div>
                    </div>
                    <svg id=\"map\" viewBox=\"0 0 960 640\" preserveAspectRatio=\"xMidYMid meet\"></svg>
                </div>
                <div class=\"legend\">
                    <p class="note">Color shows relative screening strength or the selected buildout measure. The view keeps the portfolio footprint visible, including water and wetland exclusions clamped to 0 suitability, so leadership can see both opportunity and screened-out geography. Risk overlays are directional signals for due diligence; they do not establish entitlement, community acceptance, or interconnection feasibility.</p>
                    <div class=\"legend-bar\"></div>
                    <span id="legend-label">Higher suitability percentile</span>
                </div>
            </section>
            <aside class=\"card panel\">
                <div>
                    <span class=\"eyebrow\">Executive Readout</span>
                    <p class="note">Read this as a portfolio decision screen. The map highlights candidate geography, modeled buildout pressure, and contextual risk indicators in one place so leaders can align on where to investigate next, which assumptions are bounded, and what evidence is still needed before investment or policy decisions.</p>
                </div>
                <section>
                    <div class=\"stat-grid\">
                        <div class=\"stat\">
                            <div class=\"stat-label\">Candidate Footprint</div>
                            <div class=\"stat-value\" id=\"feasible-count\">0</div>
                        </div>
                        <div class=\"stat\">
                            <div class=\"stat-label\">Screened Cells</div>
                            <div class=\"stat-value\" id=\"mapped-count\">0</div>
                        </div>
                        <div class=\"stat\">
                            <div class=\"stat-label\">Highest Score</div>
                            <div class=\"stat-value\" id=\"top-percentile\">0</div>
                        </div>
                        <div class=\"stat\">
                            <div class=\"stat-label\">Score Range</div>
                            <div class=\"stat-value\" id=\"percentile-range\">0–0</div>
                        </div>
                    </div>
                </section>
                <section class="note timeline-panel" id="buildout-timeline-panel">
                    <span class="eyebrow">Decision Lens</span>
                    <div class="mode-control" role="group" aria-label="Map mode">
                        <button type="button" class="mode-toggle is-active" id="suitability-mode-toggle" aria-pressed="true">Suitability</button>
                        <button type="button" class="mode-toggle" id="buildout-mode-toggle" aria-pressed="false">Buildout</button>
                    </div>
                    <div class="timeline-controls">
                        <label class="timeline-control" for="buildout-source-select">
                            Scenario
                            <select id="buildout-source-select"></select>
                        </label>
                        <label class="timeline-control" for="buildout-metric-select">
                            Measure
                            <select id="buildout-metric-select"></select>
                        </label>
                        <label class="timeline-control timeline-year-row" for="buildout-year-range">
                            Planning Year <strong id="buildout-year-label">n/a</strong>
                            <input type="range" id="buildout-year-range" min="0" max="0" step="1" value="0">
                        </label>
                    </div>
                    <div class="timeline-summary">
                        <div class="stat">
                            <div class="stat-label">Portfolio Load</div>
                            <div class="stat-value" id="selected-buildout-total-load">n/a</div>
                        </div>
                        <div class="stat">
                            <div class="stat-label">Growth Load</div>
                            <div class="stat-value" id="selected-buildout-new-load">n/a</div>
                        </div>
                        <div class="stat">
                            <div class="stat-label">Capacity Equivalent</div>
                            <div class="stat-value" id="selected-buildout-capacity">n/a</div>
                        </div>
                    </div>
                </section>
                <section>
                    <span class="eyebrow">Risk Overlays</span>
                    <div class="layer-stack">
                        <div class="note layer-panel">
                            <button type="button" class="layer-toggle" id="zoning-layer-toggle" aria-pressed="false">Show Zoning Proxy</button>
                            <p class="layer-note">Zoning Proxy: early land-use context. Treat as a due-diligence prompt, not parcel zoning or an allowed-use decision.</p>
                            <div class="layer-legend">
                                <span class="layer-chip"><span class="layer-swatch" style="background: rgba(129, 140, 115, 0.42);"></span>Non-developed context</span>
                                <span class="layer-chip"><span class="layer-swatch" style="background: rgba(209, 168, 72, 0.42);"></span>Developed neighborhood</span>
                                <span class="layer-chip"><span class="layer-swatch" style="background: rgba(184, 81, 53, 0.46);"></span>Urban core</span>
                            </div>
                        </div>
                        <div class="note layer-panel">
                            <button type="button" class="layer-toggle" id="permitting-layer-toggle" aria-pressed="false">Show Permitting / Ordinance Proxy</button>
                            <p class="layer-note">Permitting / Ordinance Proxy: public evidence that may affect execution risk. It is not permit readiness, legal entitlement, or ordinance compatibility.</p>
                            <div class="layer-legend">
                                <span class="layer-chip"><span class="layer-swatch" style="background: rgba(108, 115, 103, 0.08);"></span>No public evidence recorded</span>
                                <span class="layer-chip"><span class="layer-swatch" style="background: rgba(12, 92, 89, 0.40);"></span>Permit activity record</span>
                                <span class="layer-chip"><span class="layer-swatch" style="background: rgba(198, 92, 19, 0.58);"></span>Public friction signal</span>
                                <span class="layer-chip"><span class="layer-swatch" style="background: rgba(159, 45, 32, 0.72);"></span>Restrictive ordinance evidence</span>
                            </div>
                        </div>
                        <div class="note layer-panel">
                            <button type="button" class="layer-toggle" id="social-friction-layer-toggle" aria-pressed="false">Show Social-Friction Proxy</button>
                            <p class="layer-note">Social-Friction Proxy: public concern and engagement evidence that may affect stakeholder strategy. It is not a measure of actual community acceptance or social license.</p>
                            <div class="layer-legend">
                                <span class="layer-chip"><span class="layer-swatch" style="background: rgba(108, 115, 103, 0.08);"></span>No public evidence recorded</span>
                                <span class="layer-chip"><span class="layer-swatch" style="background: rgba(12, 92, 89, 0.36);"></span>Engagement record</span>
                                <span class="layer-chip"><span class="layer-swatch" style="background: rgba(198, 92, 19, 0.58);"></span>Public concern signal</span>
                                <span class="layer-chip"><span class="layer-swatch" style="background: rgba(159, 45, 32, 0.72);"></span>Organized opposition evidence</span>
                            </div>
                        </div>
                        <div class="note layer-panel">
                            <button type="button" class="layer-toggle" id="hosting-layer-toggle" aria-pressed="false">Show Hosting Capacity Proxy</button>
                            <p class="layer-note">Hosting Capacity Proxy: regional headroom context for planning discussion. It is not local interconnection or hosting-capacity approval.</p>
                            <div class="layer-legend">
                                <span class="layer-chip"><span class="layer-swatch" style="background: rgba(159, 45, 32, 0.78);"></span>Deficit</span>
                                <span class="layer-chip"><span class="layer-swatch" style="background: rgba(198, 92, 19, 0.68);"></span>Tight</span>
                                <span class="layer-chip"><span class="layer-swatch" style="background: rgba(204, 153, 0, 0.62);"></span>Moderate</span>
                                <span class="layer-chip"><span class="layer-swatch" style="background: rgba(12, 92, 89, 0.52);"></span>Headroom</span>
                            </div>
                        </div>
                    </div>
                </section>
                <section>
                    <span class=\"eyebrow\">Priority Candidates</span>
                    <table>
                        <thead>
                            <tr>
                                <th>Rank</th>
                                <th>Cell</th>
                                <th>Percentile</th>
                                <th>Capacity MW</th>
                            </tr>
                        </thead>
                        <tbody id=\"ranked-table\"></tbody>
                    </table>
                </section>
            </aside>
        </div>
    </div>
    <div class=\"tooltip\" id=\"tooltip\"></div>
    <script>
        const feasibleGeoJson = {json.dumps(feasible_geojson, separators=(",", ":"))};
        const suitabilityGeoJson = {json.dumps(suitability_geojson, separators=(",", ":"))};
        const stateBoundaryGeoJson = {json.dumps(state_boundary_geojson, separators=(",", ":"))};
        const zoningProxyGeoJson = {json.dumps(zoning_proxy_geojson, separators=(",", ":"))};
        const permittingProxyGeoJson = {json.dumps(permitting_proxy_geojson, separators=(",", ":"))};
        const socialFrictionProxyGeoJson = {json.dumps(social_friction_proxy_geojson, separators=(",", ":"))};
        const hostingProxyGeoJson = {json.dumps(hosting_proxy_geojson, separators=(",", ":"))};
        const buildoutTimelineData = {json.dumps(buildout_timeline, separators=(",", ":"))};
        const rankedRows = {json.dumps(ranked_rows, separators=(",", ":"))};
        const mapSummary = {json.dumps(map_summary, separators=(",", ":"))};

        const htmlElement = document.documentElement;
        const THEME_STORAGE_KEY = "reveal-report-theme";
        const themeModes = ["light", "dark", "system"];
        const systemThemeQuery = window.matchMedia("(prefers-color-scheme: dark)");
        const readThemeMode = () => {{
            try {{
                const savedMode = localStorage.getItem(THEME_STORAGE_KEY);
                return themeModes.includes(savedMode) ? savedMode : "system";
            }} catch (error) {{
                return "system";
            }}
        }};
        const resolveThemeMode = (mode) => mode === "system" && systemThemeQuery.matches ? "dark" : mode === "dark" ? "dark" : "light";
        const themeToggleByMode = new Map(themeModes.map((mode) => [mode, d3.select(`#${{mode}}-theme-toggle`)]));
        const applyThemeMode = (mode) => {{
            const normalizedMode = themeModes.includes(mode) ? mode : "system";
            const resolvedTheme = resolveThemeMode(normalizedMode);
            htmlElement.dataset.themeMode = normalizedMode;
            htmlElement.dataset.theme = resolvedTheme;
            themeToggleByMode.forEach((toggle, themeMode) => {{
                toggle
                    .classed("is-active", themeMode === normalizedMode)
                    .attr("aria-pressed", themeMode === normalizedMode ? "true" : "false");
            }});
        }};
        const setThemeMode = (mode) => {{
            applyThemeMode(mode);
            try {{
                localStorage.setItem(THEME_STORAGE_KEY, mode);
            }} catch (error) {{
                return;
            }}
        }};
        themeToggleByMode.forEach((toggle, mode) => {{
            toggle.on("click", () => setThemeMode(mode));
        }});
        systemThemeQuery.addEventListener?.("change", () => {{
            if (htmlElement.dataset.themeMode === "system") {{
                applyThemeMode("system");
            }}
        }});
        applyThemeMode(readThemeMode());

        const width = 960;
        const height = 640;
        const svg = d3.select("#map");
        const tooltip = d3.select("#tooltip");
        const features = suitabilityGeoJson.features || [];
        const feasibleFeatures = feasibleGeoJson.features || [];
        const stateBoundaryFeatures = stateBoundaryGeoJson.features || [];
        const zoningProxyFeatures = zoningProxyGeoJson.features || [];
        const permittingProxyFeatures = permittingProxyGeoJson.features || [];
        const socialFrictionProxyFeatures = socialFrictionProxyGeoJson.features || [];
        const hostingProxyFeatures = hostingProxyGeoJson.features || [];
        const extentSource = features.length ? suitabilityGeoJson : feasibleGeoJson;

        d3.select("#feasible-count").text(mapSummary.feasibleCellCount.toLocaleString());
        d3.select("#mapped-count").text(mapSummary.mappedCellCount.toLocaleString());
        d3.select("#top-percentile").text(d3.format(".1f")(mapSummary.topPercentile));
        d3.select("#percentile-range").text(`${{d3.format(".1f")(mapSummary.percentileMin)}}–${{d3.format(".1f")(mapSummary.percentileMax)}}`);

        const cellKeyFromObject = (value) => {{
            const raw = value?.cell_id ?? value?.sc_point_gid ?? value?.gid ?? null;
            return raw == null ? "" : String(raw);
        }};
        const cellPathsByKey = new Map();
        const tableRowsByKey = new Map();
        const zoningProxyByKey = new Map();
        const permittingProxyByKey = new Map();
        const socialFrictionProxyByKey = new Map();
        const hostingProxyByKey = new Map();
        const suitabilityPropsByKey = new Map();
        const buildoutCellPathsByKey = new Map();
        const buildoutSources = buildoutTimelineData.sources || [];
        const buildoutSourceById = new Map(buildoutSources.map((source) => [source.id, source]));
        const buildoutMetricById = new Map((buildoutTimelineData.metrics || []).map((metric) => [metric.id, metric]));
        const buildoutSummaryBySourceYear = new Map((buildoutTimelineData.summaryRows || []).map((row) => [`${{row.source_id}}:${{row.year}}`, row]));
        let mapMode = "suitability";
        let selectedBuildoutSourceId = buildoutTimelineData.defaultSourceId;
        let selectedBuildoutMetricId = buildoutTimelineData.defaultMetricId || "cumulative_total_dc_load_mw";
        let selectedBuildoutYear = buildoutTimelineData.defaultYear;
        const suitabilityModeToggle = d3.select("#suitability-mode-toggle");
        const buildoutModeToggle = d3.select("#buildout-mode-toggle");
        const buildoutSourceSelect = d3.select("#buildout-source-select");
        const buildoutMetricSelect = d3.select("#buildout-metric-select");
        const buildoutYearRange = d3.select("#buildout-year-range");
        const buildoutYearLabel = d3.select("#buildout-year-label");
        const legendLabel = d3.select("#legend-label");
        const formatMw = (value) => value == null || !Number.isFinite(Number(value)) ? "n/a" : `${{d3.format(",.0f")(Number(value))}} MW`;
        const selectedBuildoutSource = () => buildoutSourceById.get(selectedBuildoutSourceId) || buildoutSources[0] || null;
        const selectedBuildoutMetric = () => buildoutMetricById.get(selectedBuildoutMetricId) || (buildoutTimelineData.metrics || [])[0] || {{ id: selectedBuildoutMetricId, shortLabel: selectedBuildoutMetricId, unit: "MW" }};
        const selectedBuildoutSummary = () => buildoutSummaryBySourceYear.get(`${{selectedBuildoutSourceId}}:${{selectedBuildoutYear}}`) || null;
        const selectedBuildoutFeatures = () => {{
            const source = selectedBuildoutSource();
            return (source?.geoJson?.features || []).filter((feature) => Number(feature.properties?.year) === Number(selectedBuildoutYear));
        }};
        const zoningProxyClassLabels = {{
            non_developed_context: "Non-developed context",
            developed_neighborhood_context: "Developed neighborhood context",
            urban_core_context: "Urban core context",
            unknown: "Unavailable",
        }};
        const zoningProxyClassColors = {{
            non_developed_context: "rgba(129, 140, 115, 0.42)",
            developed_neighborhood_context: "rgba(209, 168, 72, 0.42)",
            urban_core_context: "rgba(184, 81, 53, 0.46)",
            unknown: "rgba(108, 115, 103, 0.0)",
        }};
        const permittingProxyClassLabels = {{
            no_public_evidence_recorded: "No public evidence recorded",
            permit_activity_record: "Permit activity record",
            public_friction_signal: "Public friction signal",
            restrictive_ordinance_evidence: "Restrictive ordinance evidence",
            unknown: "Unavailable",
        }};
        const permittingProxyClassColors = {{
            no_public_evidence_recorded: "rgba(108, 115, 103, 0.08)",
            permit_activity_record: "rgba(12, 92, 89, 0.40)",
            public_friction_signal: "rgba(198, 92, 19, 0.58)",
            restrictive_ordinance_evidence: "rgba(159, 45, 32, 0.72)",
            unknown: "rgba(108, 115, 103, 0.0)",
        }};
        const socialFrictionProxyClassLabels = {{
            no_public_evidence_recorded: "No public evidence recorded",
            community_engagement_record: "Community engagement record",
            public_concern_signal: "Public concern signal",
            organized_opposition_evidence: "Organized opposition evidence",
            unknown: "Unavailable",
        }};
        const socialFrictionProxyClassColors = {{
            no_public_evidence_recorded: "rgba(108, 115, 103, 0.08)",
            community_engagement_record: "rgba(12, 92, 89, 0.36)",
            public_concern_signal: "rgba(198, 92, 19, 0.58)",
            organized_opposition_evidence: "rgba(159, 45, 32, 0.72)",
            unknown: "rgba(108, 115, 103, 0.0)",
        }};
        const hostingProxyClassLabels = {{
            deficit: "Deficit",
            tight: "Tight",
            moderate: "Moderate",
            headroom: "Headroom",
            unknown: "Unavailable",
        }};
        const hostingProxyClassColors = {{
            deficit: "rgba(159, 45, 32, 0.78)",
            tight: "rgba(198, 92, 19, 0.68)",
            moderate: "rgba(204, 153, 0, 0.62)",
            headroom: "rgba(12, 92, 89, 0.52)",
            unknown: "rgba(108, 115, 103, 0.0)",
        }};
        features.forEach((feature) => {{
            const key = cellKeyFromObject(feature.properties || {{}});
            if (key) {{
                suitabilityPropsByKey.set(key, feature.properties || {{}});
            }}
        }});
        let activeCellKey = null;
        const setActiveCellKey = (nextKey) => {{
            const normalizedKey = nextKey == null || nextKey === "" ? null : String(nextKey);
            if (activeCellKey === normalizedKey) {{
                return;
            }}
            if (activeCellKey) {{
                cellPathsByKey.get(activeCellKey)?.classed("is-active", false);
                buildoutCellPathsByKey.get(activeCellKey)?.classed("is-active", false);
                tableRowsByKey.get(activeCellKey)?.classed("is-active", false);
            }}
            activeCellKey = normalizedKey;
            if (activeCellKey) {{
                cellPathsByKey.get(activeCellKey)?.classed("is-active", true);
                buildoutCellPathsByKey.get(activeCellKey)?.classed("is-active", true);
                tableRowsByKey.get(activeCellKey)?.classed("is-active", true);
            }}
        }};
        const positionTooltip = (event) => {{
            tooltip
                .style("left", `${{event.clientX}}px`)
                .style("top", `${{event.clientY}}px`);
        }};
        const cellNameBasisLabels = {{
            metro: "metro/city",
            natural: "natural or regional anchor",
        }};
        const cellNameScopeLabels = {{
            in_cell: "in-cell",
            nearest_catalog_fallback: "nearest catalog fallback",
        }};
        const formatCellNameBasis = (basis, scope) => {{
            const basisLabel = cellNameBasisLabels[basis] ?? basis ?? "n/a";
            const scopeLabel = cellNameScopeLabels[scope] ?? scope;
            return scopeLabel ? `${{scopeLabel}} ${{basisLabel}}` : basisLabel;
        }};
        const normalizeDisplayName = (value) => (value ?? "").toString().toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
        const displayCellName = (row) => row?.display_cell_name ?? row?.general_american_cell_name ?? row?.cell_name ?? `Cell ${{cellKeyFromObject(row)}}`;
        const displayContextCellName = (row) => {{
            const contextName = row?.display_context_name ?? row?.local_cell_name;
            const contextDisplayName = normalizeDisplayName(contextName);
            const generalDisplayName = normalizeDisplayName(displayCellName(row));
            if (!contextDisplayName || !generalDisplayName) {{
                return contextName ?? null;
            }}
            return ` ${{generalDisplayName}} `.includes(` ${{contextDisplayName}} `) ? null : contextName;
        }};
        const renderTooltip = (props, cellKey, zoningProps, permittingProps, socialFrictionProps, hostingProps, buildoutProps = null) => {{
            const zoningClass = zoningProps?.zoning_proxy_class ?? "unknown";
            const zoningLabel = zoningProxyClassLabels[zoningClass] ?? zoningProxyClassLabels.unknown;
            const permittingClass = permittingProps?.permitting_proxy_class ?? "unknown";
            const permittingLabel = permittingProxyClassLabels[permittingClass] ?? permittingProxyClassLabels.unknown;
            const socialFrictionClass = socialFrictionProps?.social_friction_proxy_class ?? "unknown";
            const socialFrictionLabel = socialFrictionProxyClassLabels[socialFrictionClass] ?? socialFrictionProxyClassLabels.unknown;
            const proxyClass = hostingProps?.hosting_capacity_proxy_class ?? "unknown";
            const proxyLabel = hostingProxyClassLabels[proxyClass] ?? hostingProxyClassLabels.unknown;
            const metric = selectedBuildoutMetric();
            const buildoutLines = buildoutProps ? `
                    Buildout scenario: ${{selectedBuildoutSource()?.label ?? "n/a"}}<br>
                    Planning year: ${{buildoutProps.year ?? selectedBuildoutYear ?? "n/a"}}<br>
                    ${{metric.shortLabel ?? metric.label}}: ${{formatMw(buildoutProps[metric.id])}}<br>
                    Cumulative total load: ${{formatMw(buildoutProps.cumulative_total_dc_load_mw)}}<br>
                    Cumulative new load: ${{formatMw(buildoutProps.cumulative_new_dc_load_mw)}}<br>
                    Cumulative total capacity: ${{formatMw(buildoutProps.cumulative_total_dc_capacity_mw)}}<br>
                ` : "";
            tooltip
                .style("opacity", 1)
                .html(`
                    <strong>${{displayCellName(props)}}</strong><br>
                    Cell ID: ${{cellKey}}<br>
                    ${{buildoutLines}}
                    Local identity: ${{props.local_cell_name ?? "n/a"}}<br>
                    Identity stack: ${{props.general_american_cell_name_layer ?? "n/a"}} / ${{props.local_cell_name_layer ?? "n/a"}}<br>
                    Label source: ${{formatCellNameBasis(props.cell_name_basis, props.cell_name_match_scope)}}<br>
                    Suitability percentile: ${{props.suitability_percentile == null ? "n/a" : d3.format(".1f")(props.suitability_percentile)}}<br>
                    Suitability score: ${{props.suitability_score == null ? "n/a" : d3.format(".3f")(props.suitability_score)}}<br>
                    Zoning proxy: ${{zoningLabel}}<br>
                    Developed share: ${{zoningProps?.developed_share == null ? "n/a" : d3.format(".0%")(zoningProps.developed_share)}}<br>
                    Permitting proxy: ${{permittingLabel}}<br>
                    Permitting evidence count: ${{permittingProps?.evidence_count == null ? "n/a" : permittingProps.evidence_count}}<br>
                    Social-friction proxy: ${{socialFrictionLabel}}<br>
                    Social evidence count: ${{socialFrictionProps?.evidence_count == null ? "n/a" : socialFrictionProps.evidence_count}}<br>
                    Hosting proxy: ${{proxyLabel}}<br>
                    Min headroom 2026-2030: ${{hostingProps?.min_margin_headroom_2026_2030 == null ? "n/a" : d3.format(".1f")(hostingProps.min_margin_headroom_2026_2030)}}<br>
                    Assessment area: ${{hostingProps?.assessment_area ?? "n/a"}}<br>
                    Developable capacity: ${{props.developable_capacity_mw == null ? "n/a" : d3.format(",.0f")(props.developable_capacity_mw)}} MW
                `);
        }};

        const tableBody = d3.select("#ranked-table");
        const tableRows = tableBody.selectAll("tr")
            .data(rankedRows)
            .join("tr")
            .attr("data-cell-key", (row) => cellKeyFromObject(row))
            .on("mouseenter", (event, row) => {{
                setActiveCellKey(cellKeyFromObject(row));
            }})
            .on("mouseleave", () => {{
                setActiveCellKey(null);
            }})
            .html((row) => `
                <td>${{row.national_rank ?? ""}}</td>
                <td>
                    <span class="cell-name">${{displayCellName(row)}}</span>
                    ${{displayContextCellName(row) ? `<span class="cell-meta">${{displayContextCellName(row)}}</span>` : ""}}
                    <span class="cell-meta buildout-cell-meta"></span>
                </td>
                <td>${{row.suitability_percentile == null ? "" : d3.format(".1f")(row.suitability_percentile)}}</td>
                <td>${{row.developable_capacity_mw == null ? "" : d3.format(",.0f")(row.developable_capacity_mw)}}</td>
            `);
        tableRows.each(function(row) {{
            const key = cellKeyFromObject(row);
            if (key) {{
                tableRowsByKey.set(key, d3.select(this));
            }}
        }});
        const updateBuildoutTableMeta = () => {{
            const metric = selectedBuildoutMetric();
            const buildoutByKey = new Map(selectedBuildoutFeatures().map((feature) => [cellKeyFromObject(feature.properties || {{}}), feature.properties || {{}}]));
            tableRows.select(".buildout-cell-meta")
                .style("display", mapMode === "buildout" ? null : "none")
                .text((row) => {{
                    if (mapMode !== "buildout") {{
                        return "";
                    }}
                    const buildoutProps = buildoutByKey.get(cellKeyFromObject(row));
                    return `${{selectedBuildoutYear ?? "n/a"}} ${{metric.shortLabel ?? metric.label}}: ${{formatMw(buildoutProps?.[metric.id])}}`;
                }});
        }};

        const zoningLayerToggle = d3.select("#zoning-layer-toggle");
        const permittingLayerToggle = d3.select("#permitting-layer-toggle");
        const socialFrictionLayerToggle = d3.select("#social-friction-layer-toggle");
        const hostingLayerToggle = d3.select("#hosting-layer-toggle");

        if ((extentSource.features || []).length) {{
            const projection = d3.geoIdentity().reflectY(true);
            projection.fitExtent([[24, 24], [width - 24, height - 24]], extentSource);
            const path = d3.geoPath(projection);
            const median = (values) => {{
                const clean = values
                    .filter((value) => Number.isFinite(value) && value > 0)
                    .sort(d3.ascending);
                if (!clean.length) {{
                    return null;
                }}
                const middle = Math.floor(clean.length / 2);
                return clean.length % 2
                    ? clean[middle]
                    : (clean[middle - 1] + clean[middle]) / 2;
            }};
            const projectedFeatureBounds = features
                .map((feature) => path.bounds(feature))
                .filter((bounds) =>
                    Number.isFinite(bounds[0][0])
                    && Number.isFinite(bounds[0][1])
                    && Number.isFinite(bounds[1][0])
                    && Number.isFinite(bounds[1][1])
                );
            const projectedFeatureCenters = features
                .map((feature) => {{
                    const centroid = path.centroid(feature);
                    return {{ feature, centroid }};
                }})
                .filter((entry) => Number.isFinite(entry.centroid[0]) && Number.isFinite(entry.centroid[1]));
            const clusteredPitch = (values, fallback) => {{
                const sorted = values
                    .filter((value) => Number.isFinite(value))
                    .sort(d3.ascending);
                if (sorted.length < 2) {{
                    return fallback;
                }}
                const clusters = [];
                sorted.forEach((value) => {{
                    const previous = clusters[clusters.length - 1];
                    if (previous == null || Math.abs(value - previous) > 1) {{
                        clusters.push(value);
                    }} else {{
                        clusters[clusters.length - 1] = (previous + value) / 2;
                    }}
                }});
                const deltas = d3.pairs(clusters).map((pair) => Math.abs(pair[1] - pair[0]));
                return median(deltas) || fallback;
            }};
            const sourceGeometryBounds = (geometry) => {{
                const coordinates = [];
                const collectCoordinates = (value) => {{
                    if (!Array.isArray(value)) {{
                        return;
                    }}
                    if (typeof value[0] === "number" && typeof value[1] === "number") {{
                        coordinates.push(value);
                        return;
                    }}
                    value.forEach(collectCoordinates);
                }};
                collectCoordinates(geometry?.coordinates || []);
                if (!coordinates.length) {{
                    return null;
                }}
                const xValues = coordinates.map((point) => point[0]);
                const yValues = coordinates.map((point) => point[1]);
                return [
                    [d3.min(xValues), d3.min(yValues)],
                    [d3.max(xValues), d3.max(yValues)],
                ];
            }};
            const sourceFeatureCenter = (feature) => {{
                const bounds = sourceGeometryBounds(feature.geometry);
                if (!bounds) {{
                    return null;
                }}
                return [
                    (bounds[0][0] + bounds[1][0]) / 2,
                    (bounds[0][1] + bounds[1][1]) / 2,
                ];
            }};
            const pointInRing = (point, ring) => {{
                let inside = false;
                for (let index = 0, previousIndex = ring.length - 1; index < ring.length; previousIndex = index++) {{
                    const current = ring[index];
                    const previous = ring[previousIndex];
                    const intersects = ((current[1] > point[1]) !== (previous[1] > point[1]))
                        && (point[0] < ((previous[0] - current[0]) * (point[1] - current[1])) / (previous[1] - current[1]) + current[0]);
                    if (intersects) {{
                        inside = !inside;
                    }}
                }}
                return inside;
            }};
            const pointInPolygonCoordinates = (point, polygonCoordinates) => {{
                if (!polygonCoordinates?.length || !pointInRing(point, polygonCoordinates[0])) {{
                    return false;
                }}
                return !polygonCoordinates.slice(1).some((ring) => pointInRing(point, ring));
            }};
            const pointInGeometry = (point, geometry) => {{
                if (!point || !geometry) {{
                    return false;
                }}
                if (geometry.type === "Polygon") {{
                    return pointInPolygonCoordinates(point, geometry.coordinates);
                }}
                if (geometry.type === "MultiPolygon") {{
                    return geometry.coordinates.some((polygon) => pointInPolygonCoordinates(point, polygon));
                }}
                return false;
            }};
            const assignStateCodeForFeature = (feature) => {{
                const center = sourceFeatureCenter(feature);
                const state = stateBoundaryFeatures.find((stateFeature) => pointInGeometry(center, stateFeature.geometry));
                return state?.properties?.state_code || null;
            }};
            const buildHexTileMetrics = () => {{
                const sourceXPitch = clusteredPitch(
                    projectedFeatureCenters.map((entry) => entry.centroid[0]),
                    median(projectedFeatureBounds.map((bounds) => Math.abs(bounds[1][0] - bounds[0][0]))) || 8,
                );
                const sourceYPitch = clusteredPitch(
                    projectedFeatureCenters.map((entry) => entry.centroid[1]),
                    median(projectedFeatureBounds.map((bounds) => Math.abs(bounds[1][1] - bounds[0][1]))) || sourceXPitch,
                );
                const sourceXValues = projectedFeatureCenters.map((entry) => entry.centroid[0]);
                const sourceYValues = projectedFeatureCenters.map((entry) => entry.centroid[1]);
                const sourceXMin = d3.min(sourceXValues) ?? 0;
                const sourceXMax = d3.max(sourceXValues) ?? sourceXMin;
                const sourceYMin = d3.min(sourceYValues) ?? 0;
                const sourceYMax = d3.max(sourceYValues) ?? sourceYMin;
                const sourceColumns = projectedFeatureCenters.map((entry) => Math.round((entry.centroid[0] - sourceXMin) / sourceXPitch));
                const sourceRows = projectedFeatureCenters.map((entry) => Math.round((entry.centroid[1] - sourceYMin) / sourceYPitch));
                const minColumn = d3.min(sourceColumns) ?? 0;
                const maxColumn = d3.max(sourceColumns) ?? minColumn;
                const minRow = d3.min(sourceRows) ?? 0;
                const maxRow = d3.max(sourceRows) ?? minRow;
                const metrics = {{ sourceXPitch, sourceYPitch, sourceXMin, sourceYMin }};
                metrics.radius = Math.max(2.4, metrics.sourceYPitch / Math.sqrt(3));
                metrics.xPitch = 1.5 * metrics.radius;
                metrics.yPitch = Math.sqrt(3) * metrics.radius;
                const displayWidth = Math.max(0, maxColumn - minColumn) * metrics.xPitch;
                const displayHeight = Math.max(0, maxRow - minRow) * metrics.yPitch + metrics.yPitch / 2;
                metrics.xOrigin = sourceXMin + ((sourceXMax - sourceXMin) - displayWidth) / 2 - minColumn * metrics.xPitch;
                metrics.yOrigin = sourceYMin + ((sourceYMax - sourceYMin) - displayHeight) / 2 - minRow * metrics.yPitch;
                return metrics;
            }};
            const hexTileMetrics = buildHexTileMetrics();
            const honeycombSlotFromCentroid = (centroid, metrics = hexTileMetrics) => {{
                if (!Number.isFinite(centroid[0]) || !Number.isFinite(centroid[1])) {{
                    return null;
                }}
                const column = Math.round((centroid[0] - metrics.sourceXMin) / metrics.sourceXPitch);
                const row = Math.round((centroid[1] - metrics.sourceYMin) / metrics.sourceYPitch);
                return {{ column, row }};
            }};
            const honeycombCenterFromSlot = (slot, metrics = hexTileMetrics) => {{
                const {{ column, row }} = slot;
                return [
                    metrics.xOrigin + column * metrics.xPitch,
                    metrics.yOrigin + row * metrics.yPitch + (Math.abs(column) % 2) * (metrics.yPitch / 2),
                ];
            }};
            const honeycombCenterFromCentroid = (centroid, metrics = hexTileMetrics) => {{
                const slot = honeycombSlotFromCentroid(centroid, metrics);
                return slot ? honeycombCenterFromSlot(slot, metrics) : centroid;
            }};
            const hexDisplayCentersByKey = new Map();
            const hexDisplaySlotsByKey = new Map();
            const cellStateCodeByKey = new Map();
            projectedFeatureCenters.forEach((entry) => {{
                const key = cellKeyFromObject(entry.feature.properties || {{}});
                if (key) {{
                    const slot = honeycombSlotFromCentroid(entry.centroid, hexTileMetrics);
                    if (slot) {{
                        hexDisplaySlotsByKey.set(key, slot);
                        hexDisplayCentersByKey.set(key, honeycombCenterFromSlot(slot, hexTileMetrics));
                    }}
                    cellStateCodeByKey.set(key, assignStateCodeForFeature(entry.feature));
                }}
            }});
            const hexPointsForCenter = (displayCentroid, radius) => [
                [displayCentroid[0] + radius, displayCentroid[1]],
                [displayCentroid[0] + radius / 2, displayCentroid[1] + (Math.sqrt(3) * radius) / 2],
                [displayCentroid[0] - radius / 2, displayCentroid[1] + (Math.sqrt(3) * radius) / 2],
                [displayCentroid[0] - radius, displayCentroid[1]],
                [displayCentroid[0] - radius / 2, displayCentroid[1] - (Math.sqrt(3) * radius) / 2],
                [displayCentroid[0] + radius / 2, displayCentroid[1] - (Math.sqrt(3) * radius) / 2],
            ];
            const hexNeighborSlotForEdge = (slot, edgeIndex) => {{
                const isOddColumn = Math.abs(slot.column) % 2 === 1;
                const deltas = isOddColumn
                    ? [[1, 1], [0, 1], [-1, 1], [-1, 0], [0, -1], [1, 0]]
                    : [[1, 0], [0, 1], [-1, 0], [-1, -1], [0, -1], [1, -1]];
                const delta = deltas[edgeIndex];
                return {{ column: slot.column + delta[0], row: slot.row + delta[1] }};
            }};
            const slotKey = (slot) => `${{slot.column}}:${{slot.row}}`;
            const buildHexStateBoundarySegments = () => {{
                const slotsByKey = new Map();
                const cellKeysBySlot = new Map();
                hexDisplaySlotsByKey.forEach((slot, key) => {{
                    const encodedSlot = slotKey(slot);
                    slotsByKey.set(encodedSlot, slot);
                    cellKeysBySlot.set(encodedSlot, key);
                }});
                const seenSegments = new Set();
                const segments = [];
                const segmentKey = (start, end) => [start, end]
                    .map((point) => `${{point[0].toFixed(3)}},${{point[1].toFixed(3)}}`)
                    .sort()
                    .join("|");
                hexDisplaySlotsByKey.forEach((slot, key) => {{
                    const stateCode = cellStateCodeByKey.get(key) || "unassigned";
                    const center = hexDisplayCentersByKey.get(key);
                    if (!center) {{
                        return;
                    }}
                    const points = hexPointsForCenter(center, hexTileMetrics.radius);
                    const edges = [
                        [points[0], points[1]],
                        [points[1], points[2]],
                        [points[2], points[3]],
                        [points[3], points[4]],
                        [points[4], points[5]],
                        [points[5], points[0]],
                    ];
                    edges.forEach((edge, edgeIndex) => {{
                        const neighborSlot = hexNeighborSlotForEdge(slot, edgeIndex);
                        const neighborKey = cellKeysBySlot.get(slotKey(neighborSlot));
                        const neighborStateCode = neighborKey ? (cellStateCodeByKey.get(neighborKey) || "unassigned") : "unassigned";
                        if (stateCode === neighborStateCode) {{
                            return;
                        }}
                        const encodedSegment = segmentKey(edge[0], edge[1]);
                        if (seenSegments.has(encodedSegment)) {{
                            return;
                        }}
                        seenSegments.add(encodedSegment);
                        segments.push({{
                            stateCode,
                            d: `M${{edge[0][0]}},${{edge[0][1]}}L${{edge[1][0]}},${{edge[1][1]}}`,
                        }});
                    }});
                }});
                return segments;
            }};
            const projectedHexPath = (feature, metrics = hexTileMetrics) => {{
                const centroid = path.centroid(feature);
                if (!Number.isFinite(centroid[0]) || !Number.isFinite(centroid[1])) {{
                    return path(feature);
                }}
                const key = cellKeyFromObject(feature.properties || {{}});
                const displayCentroid = hexDisplayCentersByKey.get(key) || honeycombCenterFromCentroid(centroid, metrics);
                const radius = metrics.radius;
                const points = hexPointsForCenter(displayCentroid, radius);
                return "M" + points.map((point) => point[0] + "," + point[1]).join("L") + "Z";
            }};
            const hexDisplayPath = (feature) => projectedHexPath(feature, hexTileMetrics);
            const squareDisplayPath = (feature) => path(feature);
            let displayMode = "square";
            const displayPathForMode = (feature) => displayMode === "hex" ? hexDisplayPath(feature) : squareDisplayPath(feature);
            const displayPathSelections = [];
            const registerDisplayPathSelection = (selection) => {{
                displayPathSelections.push(selection);
                return selection;
            }};
            const squareShapeToggle = d3.select("#square-shape-toggle");
            const hexShapeToggle = d3.select("#hex-shape-toggle");
            let stateBoundaryPaths = null;
            let hexStateBoundaryPaths = null;
            let buildoutPaths = null;
            const updateCellDisplayGeometry = () => {{
                svg.attr("data-display-mode", displayMode);
                displayPathSelections.forEach((selection) => {{
                    selection.attr("d", (feature) => displayPathForMode(feature));
                }});
                if (buildoutPaths) {{
                    buildoutPaths.attr("d", (feature) => displayPathForMode(feature));
                }}
                if (stateBoundaryPaths) {{
                    stateBoundaryPaths.classed("is-display-reference", displayMode === "hex");
                    stateBoundaryPaths.style("display", displayMode === "hex" ? "none" : null);
                }}
                if (hexStateBoundaryPaths) {{
                    hexStateBoundaryPaths.style("display", displayMode === "hex" ? null : "none");
                }}
                squareShapeToggle
                    .classed("is-active", displayMode === "square")
                    .attr("aria-pressed", displayMode === "square" ? "true" : "false");
                hexShapeToggle
                    .classed("is-active", displayMode === "hex")
                    .attr("aria-pressed", displayMode === "hex" ? "true" : "false");
            }};
            const setDisplayMode = (nextMode) => {{
                if (!["square", "hex"].includes(nextMode)) {{
                    return;
                }}
                displayMode = nextMode;
                updateCellDisplayGeometry();
            }};
            squareShapeToggle.on("click", () => setDisplayMode("square"));
            hexShapeToggle.on("click", () => setDisplayMode("hex"));
            const color = d3.scaleSequential()
                .domain([mapSummary.percentileMin || 0, mapSummary.percentileMax || 100])
                .interpolator(d3.interpolateViridis);

            svg.append("rect")
                .attr("class", "map-background")
                .attr("x", 0)
                .attr("y", 0)
                .attr("width", width)
                .attr("height", height)
                .attr("fill", "rgba(255,255,255,0.42)");

            const feasiblePaths = svg.append("g")
                .selectAll("path")
                .data(feasibleFeatures)
                .join("path")
                .attr("class", "feasible-hex")
                .attr("d", (feature) => displayPathForMode(feature))
                .attr("fill", "#ddd2bf")
                .attr("stroke", "#f8f6ef")
                .attr("stroke-width", 0.8)
                .attr("opacity", 0.7);
            registerDisplayPathSelection(feasiblePaths);

            const suitabilityPaths = svg.append("g")
                .selectAll("path")
                .data(features)
                .join("path")
                .attr("class", "suitability-cell suitability-hex")
                .attr("data-cell-key", (feature) => cellKeyFromObject(feature.properties || {{}}))
                .attr("d", (feature) => displayPathForMode(feature))
                .attr("fill", (feature) => color(feature.properties?.suitability_percentile ?? mapSummary.percentileMin))
                .attr("stroke", "rgba(255,255,255,0.92)")
                .attr("stroke-width", 0.9)
                .on("mouseenter", (event, feature) => {{
                    const props = feature.properties || {{}};
                    const cellKey = cellKeyFromObject(props);
                    setActiveCellKey(cellKey);
                    positionTooltip(event);
                    renderTooltip(
                        props,
                        cellKey,
                        zoningProxyByKey.get(cellKey),
                        permittingProxyByKey.get(cellKey),
                        socialFrictionProxyByKey.get(cellKey),
                        hostingProxyByKey.get(cellKey),
                    );
                }})
                .on("mousemove", (event) => {{
                    positionTooltip(event);
                }})
                .on("mouseleave", () => {{
                    setActiveCellKey(null);
                    tooltip.style("opacity", 0);
                }});
            suitabilityPaths.each(function(feature) {{
                const key = cellKeyFromObject(feature.properties || {{}});
                if (key) {{
                    cellPathsByKey.set(key, d3.select(this));
                }}
            }});
            registerDisplayPathSelection(suitabilityPaths);

            const zoningProxyGroup = svg.append("g")
                .attr("class", "zoning-proxy-layer")
                .style("display", "none");
            const zoningProxyPaths = zoningProxyGroup
                .selectAll("path")
                .data(zoningProxyFeatures)
                .join("path")
                .attr("class", "zoning-proxy-cell")
                .attr("data-cell-key", (feature) => cellKeyFromObject(feature.properties || {{}}))
                .attr("d", (feature) => displayPathForMode(feature))
                .attr("fill", (feature) => zoningProxyClassColors[feature.properties?.zoning_proxy_class ?? "unknown"])
                .attr("opacity", 0.28)
                .attr("stroke", "none");
            registerDisplayPathSelection(zoningProxyPaths);
            zoningProxyFeatures.forEach((feature) => {{
                const key = cellKeyFromObject(feature.properties || {{}});
                if (key) {{
                    zoningProxyByKey.set(key, feature.properties || {{}});
                }}
            }});

            let showZoningProxy = false;
            const syncZoningLayer = () => {{
                zoningProxyGroup.style("display", showZoningProxy ? null : "none");
                zoningLayerToggle
                    .classed("is-active", showZoningProxy)
                    .attr("aria-pressed", showZoningProxy ? "true" : "false")
                    .text(showZoningProxy ? "Hide Zoning Proxy" : "Show Zoning Proxy");
            }};
            zoningLayerToggle.on("click", () => {{
                showZoningProxy = !showZoningProxy;
                syncZoningLayer();
            }});
            syncZoningLayer();

            const permittingProxyGroup = svg.append("g")
                .attr("class", "permitting-proxy-layer")
                .style("display", "none");
            const permittingProxyPaths = permittingProxyGroup
                .selectAll("path")
                .data(permittingProxyFeatures)
                .join("path")
                .attr("class", "permitting-proxy-cell")
                .attr("data-cell-key", (feature) => cellKeyFromObject(feature.properties || {{}}))
                .attr("d", (feature) => displayPathForMode(feature))
                .attr("fill", (feature) => permittingProxyClassColors[feature.properties?.permitting_proxy_class ?? "unknown"])
                .attr("opacity", 0.38)
                .attr("stroke", "none");
            registerDisplayPathSelection(permittingProxyPaths);
            permittingProxyFeatures.forEach((feature) => {{
                const key = cellKeyFromObject(feature.properties || {{}});
                if (key) {{
                    permittingProxyByKey.set(key, feature.properties || {{}});
                }}
            }});

            let showPermittingProxy = false;
            const syncPermittingLayer = () => {{
                permittingProxyGroup.style("display", showPermittingProxy ? null : "none");
                permittingLayerToggle
                    .classed("is-active", showPermittingProxy)
                    .attr("aria-pressed", showPermittingProxy ? "true" : "false")
                    .text(showPermittingProxy ? "Hide Permitting / Ordinance Proxy" : "Show Permitting / Ordinance Proxy");
            }};
            permittingLayerToggle.on("click", () => {{
                showPermittingProxy = !showPermittingProxy;
                syncPermittingLayer();
            }});
            syncPermittingLayer();

            const socialFrictionProxyGroup = svg.append("g")
                .attr("class", "social-friction-proxy-layer")
                .style("display", "none");
            const socialFrictionProxyPaths = socialFrictionProxyGroup
                .selectAll("path")
                .data(socialFrictionProxyFeatures)
                .join("path")
                .attr("class", "social-friction-proxy-cell")
                .attr("data-cell-key", (feature) => cellKeyFromObject(feature.properties || {{}}))
                .attr("d", (feature) => displayPathForMode(feature))
                .attr("fill", (feature) => socialFrictionProxyClassColors[feature.properties?.social_friction_proxy_class ?? "unknown"])
                .attr("opacity", 0.38)
                .attr("stroke", "none");
            registerDisplayPathSelection(socialFrictionProxyPaths);
            socialFrictionProxyFeatures.forEach((feature) => {{
                const key = cellKeyFromObject(feature.properties || {{}});
                if (key) {{
                    socialFrictionProxyByKey.set(key, feature.properties || {{}});
                }}
            }});

            let showSocialFrictionProxy = false;
            const syncSocialFrictionLayer = () => {{
                socialFrictionProxyGroup.style("display", showSocialFrictionProxy ? null : "none");
                socialFrictionLayerToggle
                    .classed("is-active", showSocialFrictionProxy)
                    .attr("aria-pressed", showSocialFrictionProxy ? "true" : "false")
                    .text(showSocialFrictionProxy ? "Hide Social-Friction Proxy" : "Show Social-Friction Proxy");
            }};
            socialFrictionLayerToggle.on("click", () => {{
                showSocialFrictionProxy = !showSocialFrictionProxy;
                syncSocialFrictionLayer();
            }});
            syncSocialFrictionLayer();

            const hostingProxyGroup = svg.append("g")
                .attr("class", "hosting-proxy-layer")
                .style("display", "none");
            const hostingProxyPaths = hostingProxyGroup
                .selectAll("path")
                .data(hostingProxyFeatures)
                .join("path")
                .attr("class", "hosting-proxy-cell")
                .attr("data-cell-key", (feature) => cellKeyFromObject(feature.properties || {{}}))
                .attr("d", (feature) => displayPathForMode(feature))
                .attr("fill", (feature) => hostingProxyClassColors[feature.properties?.hosting_capacity_proxy_class ?? "unknown"])
                .attr("opacity", 0.32)
                .attr("stroke", "none");
            registerDisplayPathSelection(hostingProxyPaths);
            hostingProxyFeatures.forEach((feature) => {{
                const key = cellKeyFromObject(feature.properties || {{}});
                if (key) {{
                    hostingProxyByKey.set(key, feature.properties || {{}});
                }}
            }});

            let showHostingProxy = false;
            const syncHostingLayer = () => {{
                hostingProxyGroup.style("display", showHostingProxy ? null : "none");
                hostingLayerToggle
                    .classed("is-active", showHostingProxy)
                    .attr("aria-pressed", showHostingProxy ? "true" : "false")
                    .text(showHostingProxy ? "Hide Hosting Capacity Proxy" : "Show Hosting Capacity Proxy");
            }};
            hostingLayerToggle.on("click", () => {{
                showHostingProxy = !showHostingProxy;
                syncHostingLayer();
            }});
            syncHostingLayer();

            buildoutSourceSelect
                .selectAll("option")
                .data(buildoutSources)
                .join("option")
                .attr("value", (source) => source.id)
                .text((source) => source.label);
            buildoutMetricSelect
                .selectAll("option")
                .data(buildoutTimelineData.metrics || [])
                .join("option")
                .attr("value", (metric) => metric.id)
                .text((metric) => metric.label);

            const buildoutMetricMax = () => {{
                const source = selectedBuildoutSource();
                const metric = selectedBuildoutMetric();
                return d3.max((source?.geoJson?.features || []), (feature) => Number(feature.properties?.[metric.id]) || 0) || 1;
            }};
            const syncBuildoutSummary = () => {{
                const summary = selectedBuildoutSummary();
                d3.select("#selected-buildout-total-load").text(formatMw(summary?.cumulative_total_dc_load_mw));
                d3.select("#selected-buildout-new-load").text(formatMw(summary?.cumulative_new_dc_load_mw));
                d3.select("#selected-buildout-capacity").text(formatMw(summary?.cumulative_total_dc_capacity_mw));
            }};
            const syncBuildoutTimelineControls = () => {{
                const source = selectedBuildoutSource();
                const years = source?.years || [];
                if (!years.length) {{
                    selectedBuildoutYear = null;
                }} else if (!years.includes(Number(selectedBuildoutYear))) {{
                    selectedBuildoutYear = d3.max(years);
                }}
                const yearIndex = Math.max(0, years.indexOf(Number(selectedBuildoutYear)));
                buildoutSourceSelect
                    .property("value", selectedBuildoutSourceId || "")
                    .property("disabled", !buildoutSources.length);
                buildoutMetricSelect
                    .property("value", selectedBuildoutMetricId)
                    .property("disabled", !(buildoutTimelineData.metrics || []).length);
                buildoutYearRange
                    .attr("max", Math.max(0, years.length - 1))
                    .property("value", yearIndex)
                    .property("disabled", !years.length);
                buildoutYearLabel.text(selectedBuildoutYear ?? "n/a");
                syncBuildoutSummary();
                updateBuildoutTableMeta();
            }};
            const buildoutGroup = svg.append("g")
                .attr("class", "buildout-timeline-layer")
                .style("display", "none");
            const renderBuildoutLayer = () => {{
                const metric = selectedBuildoutMetric();
                const maxValue = buildoutMetricMax();
                const buildoutColor = d3.scaleSequential()
                    .domain([0, maxValue])
                    .interpolator(d3.interpolatePlasma);
                buildoutCellPathsByKey.clear();
                buildoutPaths = buildoutGroup
                    .selectAll("path")
                    .data(selectedBuildoutFeatures(), (feature) => cellKeyFromObject(feature.properties || {{}}))
                    .join("path")
                    .attr("class", "buildout-cell")
                    .attr("data-cell-key", (feature) => cellKeyFromObject(feature.properties || {{}}))
                    .attr("d", (feature) => displayPathForMode(feature))
                    .attr("fill", (feature) => buildoutColor(Number(feature.properties?.[metric.id]) || 0))
                    .attr("opacity", 0.84)
                    .attr("stroke", "rgba(255,255,255,0.92)")
                    .attr("stroke-width", 0.9)
                    .on("mouseenter", (event, feature) => {{
                        const buildoutProps = feature.properties || {{}};
                        const cellKey = cellKeyFromObject(buildoutProps);
                        const props = suitabilityPropsByKey.get(cellKey) || buildoutProps;
                        setActiveCellKey(cellKey);
                        positionTooltip(event);
                        renderTooltip(
                            props,
                            cellKey,
                            zoningProxyByKey.get(cellKey),
                            permittingProxyByKey.get(cellKey),
                            socialFrictionProxyByKey.get(cellKey),
                            hostingProxyByKey.get(cellKey),
                            buildoutProps,
                        );
                    }})
                    .on("mousemove", (event) => {{
                        positionTooltip(event);
                    }})
                    .on("mouseleave", () => {{
                        setActiveCellKey(null);
                        tooltip.style("opacity", 0);
                    }});
                buildoutPaths.each(function(feature) {{
                    const key = cellKeyFromObject(feature.properties || {{}});
                    if (key) {{
                        buildoutCellPathsByKey.set(key, d3.select(this));
                    }}
                }});
            }};
            const syncMapMode = () => {{
                const buildoutModeAvailable = Boolean(selectedBuildoutSource());
                if (mapMode === "buildout" && !buildoutModeAvailable) {{
                    mapMode = "suitability";
                }}
                suitabilityPaths.style("display", mapMode === "suitability" ? null : "none");
                buildoutGroup.style("display", mapMode === "buildout" ? null : "none");
                suitabilityModeToggle
                    .classed("is-active", mapMode === "suitability")
                    .attr("aria-pressed", mapMode === "suitability" ? "true" : "false");
                buildoutModeToggle
                    .classed("is-active", mapMode === "buildout")
                    .attr("aria-pressed", mapMode === "buildout" ? "true" : "false")
                    .property("disabled", !buildoutModeAvailable);
                const metric = selectedBuildoutMetric();
                legendLabel.text(mapMode === "buildout" ? `Higher selected ${{metric.shortLabel ?? metric.label}}` : "Higher suitability percentile");
                updateBuildoutTableMeta();
            }};
            const setMapMode = (nextMode) => {{
                if (!['suitability', 'buildout'].includes(nextMode)) {{
                    return;
                }}
                mapMode = nextMode;
                renderBuildoutLayer();
                syncMapMode();
            }};
            suitabilityModeToggle.on("click", () => setMapMode("suitability"));
            buildoutModeToggle.on("click", () => setMapMode("buildout"));
            buildoutSourceSelect.on("change", (event) => {{
                selectedBuildoutSourceId = event.target.value;
                selectedBuildoutYear = null;
                syncBuildoutTimelineControls();
                renderBuildoutLayer();
                syncMapMode();
            }});
            buildoutMetricSelect.on("change", (event) => {{
                selectedBuildoutMetricId = event.target.value;
                syncBuildoutTimelineControls();
                renderBuildoutLayer();
                syncMapMode();
            }});
            buildoutYearRange.on("input", (event) => {{
                const source = selectedBuildoutSource();
                const years = source?.years || [];
                selectedBuildoutYear = years[Number(event.target.value)] ?? selectedBuildoutYear;
                syncBuildoutTimelineControls();
                renderBuildoutLayer();
                syncMapMode();
            }});
            syncBuildoutTimelineControls();
            renderBuildoutLayer();
            syncMapMode();

            stateBoundaryPaths = svg.append("g")
                .selectAll("path")
                .data(stateBoundaryFeatures)
                .join("path")
                .attr("class", "state-boundary")
                .attr("d", path)
                .attr("fill", "none")
                .attr("stroke", "rgba(31, 41, 39, 0.42)")
                .attr("stroke-width", 1.1)
                .attr("stroke-linejoin", "round");
            hexStateBoundaryPaths = svg.append("g")
                .attr("class", "hex-state-boundary-layer")
                .selectAll("path")
                .data(buildHexStateBoundarySegments())
                .join("path")
                .attr("class", "hex-state-boundary")
                .attr("data-state-code", (segment) => segment.stateCode)
                .attr("d", (segment) => segment.d);
            updateCellDisplayGeometry();
        }} else {{
            svg.append("text")
                .attr("x", width / 2)
                .attr("y", height / 2)
                .attr("text-anchor", "middle")
                .attr("fill", "var(--empty-map-text)")
                .attr("font-size", 18)
                .text("No feasible suitability cells were available for map export.");
        }}
    </script>
</body>
</html>
"""
    map_path.write_text(html)
    return map_path


def _read_public_report_bundle_columns(path):
    """Read the top-level columns for one bundle artifact."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path, nrows=0).columns.tolist()
    if suffix == ".gpkg":
        return gpd.read_file(path).columns.tolist()
    raise ValueError(f"Unsupported bundle artifact type for schema inspection: {path}")


def _build_public_report_reeds_handoff_products(output_dir):
    """Return the current ReEDS-facing handoff products for the bounded report bundle."""
    output_dir = Path(output_dir)
    return [
        {
            "label": "public_eer_total_downscaled_cumulative_buildout",
            "path": (output_dir / "public_eer_total_downscaled_cumulative_buildout.gpkg").as_posix(),
            "role": "national grid-cell annual cumulative load buildout for bounded ReEDS-facing screening",
            "file_format": "GeoPackage",
            "required_columns": [
                "sc_point_gid",
                "year",
                "baseline_total_dc_load_mw",
                "cumulative_new_dc_load_mw",
                "cumulative_total_dc_load_mw",
                "new_dc_capacity_mw",
                "baseline_total_dc_capacity_mw",
                "cumulative_new_dc_capacity_mw",
                "cumulative_total_dc_capacity_mw",
                "utilization_factor",
                "max_site_addition_per_time_step_mw",
                "per_site_time_step_capacity_limit_exceeded",
                "geometry",
            ],
            "units": {
                "baseline_total_dc_load_mw": "MW",
                "cumulative_new_dc_load_mw": "MW",
                "cumulative_total_dc_load_mw": "MW",
                "new_dc_capacity_mw": "MW",
                "baseline_total_dc_capacity_mw": "MW",
                "cumulative_new_dc_capacity_mw": "MW",
                "cumulative_total_dc_capacity_mw": "MW",
            },
            "primary_join_keys": ["sc_point_gid", "year"],
        },
        {
            "label": "public_eer_regional_downscaled_cumulative_buildout",
            "path": (output_dir / "public_eer_regional_downscaled_cumulative_buildout.gpkg").as_posix(),
            "role": "region-group grid-cell annual cumulative load buildout for bounded ReEDS-facing screening",
            "file_format": "GeoPackage",
            "required_columns": [
                "sc_point_gid",
                "zone_group",
                "year",
                "baseline_total_dc_load_mw",
                "cumulative_new_dc_load_mw",
                "cumulative_total_dc_load_mw",
                "new_dc_capacity_mw",
                "baseline_total_dc_capacity_mw",
                "cumulative_new_dc_capacity_mw",
                "cumulative_total_dc_capacity_mw",
                "utilization_factor",
                "max_site_addition_per_time_step_mw",
                "per_site_time_step_capacity_limit_exceeded",
                "geometry",
            ],
            "units": {
                "baseline_total_dc_load_mw": "MW",
                "cumulative_new_dc_load_mw": "MW",
                "cumulative_total_dc_load_mw": "MW",
                "new_dc_capacity_mw": "MW",
                "baseline_total_dc_capacity_mw": "MW",
                "cumulative_new_dc_capacity_mw": "MW",
                "cumulative_total_dc_capacity_mw": "MW",
            },
            "primary_join_keys": ["zone_group", "sc_point_gid", "year"],
        },
        {
            "label": "public_report_bundle_cumulative_buildout_summary",
            "path": (output_dir / "public_report_bundle_cumulative_buildout_summary.csv").as_posix(),
            "role": "annual reconciliation summary for bundle-level load handoff checks",
            "file_format": "CSV",
            "required_columns": [
                "source_output_name",
                "year",
                "cell_count",
                "baseline_total_dc_load_mw",
                "cumulative_new_dc_load_mw",
                "cumulative_total_dc_load_mw",
                "baseline_total_dc_capacity_mw",
                "cumulative_new_dc_capacity_mw",
                "cumulative_total_dc_capacity_mw",
                "max_new_dc_capacity_mw",
                "per_site_time_step_capacity_limit_exceeded",
            ],
            "units": {
                "baseline_total_dc_load_mw": "MW",
                "cumulative_new_dc_load_mw": "MW",
                "cumulative_total_dc_load_mw": "MW",
                "baseline_total_dc_capacity_mw": "MW",
                "cumulative_new_dc_capacity_mw": "MW",
                "cumulative_total_dc_capacity_mw": "MW",
                "max_new_dc_capacity_mw": "MW",
            },
            "primary_join_keys": ["source_output_name", "year"],
        },
        {
            "label": "public_report_suitability_ranked_cells",
            "path": (output_dir / "public_report_suitability_ranked_cells.csv").as_posix(),
            "role": "supplemental ranked screening table for candidate-cell ordering in ReEDS-facing workflows",
            "file_format": "CSV",
            "required_columns": [
                "national_rank",
                "cell_id",
                "cell_name",
                "cell_name_basis",
                "sc_point_gid",
                "developable_capacity_mw",
                "suitability_score",
                "suitability_percentile",
            ],
            "units": {
                "developable_capacity_mw": "MW",
                "suitability_percentile": "percent",
            },
            "primary_join_keys": ["national_rank", "cell_id"],
        },
    ]


def _build_public_report_reeds_validation_checks(output_dir, handoff_products):
    """Validate the current bounded bundle against the ReEDS-facing handoff contract."""
    output_dir = Path(output_dir)
    checks = []

    missing_products = [
        product["label"]
        for product in handoff_products
        if not Path(product["path"]).exists()
    ]
    checks.append(
        {
            "name": "required_handoff_products_exist",
            "status": "passed" if not missing_products else "failed",
            "detail": "All required ReEDS-facing handoff artifacts are present in the bounded bundle.",
            "missing_products": missing_products,
        }
    )

    for product in handoff_products:
        artifact_path = Path(product["path"])
        missing_columns = []
        actual_columns = []
        if artifact_path.exists():
            actual_columns = _read_public_report_bundle_columns(artifact_path)
            missing_columns = sorted(set(product["required_columns"]) - set(actual_columns))
        checks.append(
            {
                "name": f"{product['label']}_required_columns",
                "status": "passed" if not missing_columns else "failed",
                "path": artifact_path.as_posix(),
                "required_columns": product["required_columns"],
                "actual_columns": actual_columns,
                "missing_columns": missing_columns,
            }
        )

    total_years = []
    regional_years = []
    summary_years = []
    summary_source_names = []
    capacity_limit_violations = 0
    total_path = output_dir / "public_eer_total_downscaled_cumulative_buildout.gpkg"
    regional_path = output_dir / "public_eer_regional_downscaled_cumulative_buildout.gpkg"
    summary_path = output_dir / "public_report_bundle_cumulative_buildout_summary.csv"

    if total_path.exists():
        total_years = sorted(int(year) for year in gpd.read_file(total_path)["year"].dropna().unique())
    if regional_path.exists():
        regional_years = sorted(int(year) for year in gpd.read_file(regional_path)["year"].dropna().unique())
    if summary_path.exists():
        summary = pd.read_csv(summary_path)
        summary_years = sorted(int(year) for year in summary["year"].dropna().unique())
        summary_source_names = sorted(summary["source_output_name"].dropna().unique().tolist())
        if "per_site_time_step_capacity_limit_exceeded" in summary.columns:
            capacity_limit_violations = int(
                summary["per_site_time_step_capacity_limit_exceeded"].fillna(0).sum()
            )

    expected_source_names = [
        "public_eer_regional_downscaled",
        "public_eer_total_downscaled",
    ]
    year_alignment_passed = (
        total_years
        and regional_years
        and summary_years
        and total_years == regional_years == summary_years
        and summary_source_names == expected_source_names
    )
    checks.append(
        {
            "name": "temporal_year_alignment",
            "status": "passed" if year_alignment_passed else "failed",
            "detail": "Total, regional, and summary artifacts share one annual modeled-year set and the expected source labels.",
            "total_cumulative_years": total_years,
            "regional_cumulative_years": regional_years,
            "summary_years": summary_years,
            "summary_source_names": summary_source_names,
        }
    )

    checks.append(
        {
            "name": "per_site_time_step_capacity_limit",
            "status": "passed" if capacity_limit_violations == 0 else "failed",
            "detail": "No generated cumulative buildout row exceeds the configured per-site time-step capacity limit.",
            "violation_count": capacity_limit_violations,
        }
    )

    return checks


def _build_public_report_reeds_integration_contract(repo_root, output_dir):
    """Build the bounded reVeal-to-ReEDS handoff contract for report outputs."""
    repo_root = Path(repo_root).resolve()
    output_dir = Path(output_dir)
    summary_path = output_dir / "public_report_bundle_cumulative_buildout_summary.csv"
    summary = pd.read_csv(summary_path)
    modeled_years = sorted(int(year) for year in summary["year"].dropna().unique())
    temporal_assumptions = _build_public_report_temporal_assumptions(repo_root, output_dir)
    capacity_constraint_assumptions = _build_public_report_capacity_constraint_assumptions(
        _load_public_report_bundle_smoke_configs(repo_root)
    )
    spatial_grid_contract = _build_public_report_grid_resolution_contract(repo_root)
    allocation_assumption_contract = _build_public_report_allocation_assumption_contract(
        repo_root,
        output_dir=output_dir,
        temporal_assumptions=temporal_assumptions,
        spatial_grid_contract=spatial_grid_contract,
        capacity_constraint_assumptions=capacity_constraint_assumptions,
    )
    baxtel_schema_contract = _build_public_report_baxtel_schema_contract(repo_root)

    handoff_products = _build_public_report_reeds_handoff_products(output_dir)
    validation_checks = _build_public_report_reeds_validation_checks(output_dir, handoff_products)

    return {
        "contract_type": "bounded-public-report-reeds-integration-contract",
        "bundle_label": "bounded-public-report-bundle",
        "integration_target": "ReEDS high-resolution load forecasting",
        "contract_mode": "bounded-public-approximation",
        "handoff_products": handoff_products,
        "temporal_contract": {
            "time_granularity": "annual",
            "current_bundle_baseline_year": PUBLIC_REPORT_BUNDLE_BASELINE_YEAR,
            "report_reference_baseline_year": PUBLIC_REPORT_BUNDLE_REPORT_BASELINE_YEAR,
            "modeled_years": modeled_years,
            "report_reference_modeled_years": temporal_assumptions["report_reference"]["modeled_years"],
            "current_bundle_starting_stock_year": temporal_assumptions["current_bundle"][
                "starting_stock_year"
            ],
            "report_reference_starting_stock_year": temporal_assumptions["report_reference"][
                "starting_stock_year"
            ],
            "current_bundle_starting_stock_source": temporal_assumptions["current_bundle"][
                "starting_stock_source"
            ],
            "report_reference_starting_stock_source": temporal_assumptions["report_reference"][
                "starting_stock_source"
            ],
            "current_bundle_buildout_horizon_years": temporal_assumptions["current_bundle"][
                "buildout_horizon_years"
            ],
            "report_reference_buildout_horizon_years": temporal_assumptions["report_reference"][
                "buildout_horizon_years"
            ],
            "temporal_parity_status": temporal_assumptions["parity_status"],
            "temporal_parity_blockers": temporal_assumptions["parity_blockers"],
            "cumulative_buildout_interpretation": "Each annual record represents bounded cumulative total load and bounded cumulative new load by grid cell.",
        },
        "capacity_constraint_contract": {
            "utilization_factor": PUBLIC_REPORT_REFERENCE_UTILIZATION_FACTOR,
            "max_site_addition_per_time_step_mw": PUBLIC_REPORT_REFERENCE_MAX_SITE_ADDITION_PER_TIME_STEP_MW,
            "load_to_capacity_rule": "capacity_mw = load_mw / utilization_factor",
            "current_bundle_capacity_assumptions": capacity_constraint_assumptions["current_bundle"],
            "per_site_time_step_capacity_validation_status": next(
                check["status"]
                for check in validation_checks
                if check["name"] == "per_site_time_step_capacity_limit"
            ),
        },
        "allocation_contract": {
            "allocation_parity_status": allocation_assumption_contract["parity_status"],
            "allocation_parity_blockers": allocation_assumption_contract["parity_blockers"],
            "allocation_contract_path": (
                output_dir / "public_report_allocation_assumption_contract.json"
            ).as_posix(),
            "current_bundle_allocation_algorithm": allocation_assumption_contract[
                "current_bundle"
            ]["allocation_algorithm"],
            "current_bundle_projection_resolutions": allocation_assumption_contract[
                "current_bundle"
            ]["projection_resolutions"],
            "report_reference_allocation_mode": allocation_assumption_contract[
                "report_reference"
            ]["allocation_mode"],
        },
        "baxtel_schema_contract": {
            "baxtel_schema_parity_status": baxtel_schema_contract["parity_status"],
            "baxtel_schema_parity_blockers": baxtel_schema_contract["parity_blockers"],
            "baxtel_schema_contract_path": (
                output_dir / "public_report_baxtel_schema_contract.json"
            ).as_posix(),
            "trained_suitability_parity_path": baxtel_schema_contract["decision"][
                "trained_suitability_parity_path"
            ],
            "baxtel_schema_available": baxtel_schema_contract["current_evidence"][
                "baxtel_schema_available"
            ],
            "public_baseline_available": baxtel_schema_contract["current_evidence"][
                "public_baseline_available"
            ],
        },
        "spatial_contract": {
            "grid_cell_key": "sc_point_gid",
            "regional_group_key": "zone_group",
            "current_bundle_grid_path": (repo_root / PUBLIC_REPORT_BUNDLE_GRID_PATH).as_posix(),
            "current_bundle_grid_priority": PUBLIC_REPORT_BUNDLE_GRID_PRIORITY,
            "report_reference_grid_resolution_km": PUBLIC_REPORT_REFERENCE_GRID_RESOLUTION_KM,
            "linkedin_aggregation_grid_resolution_km": PUBLIC_REPORT_LINKEDIN_AGGREGATION_GRID_RESOLUTION_KM,
            "current_bundle_grid_resolution_km": spatial_grid_contract["current_bundle"][
                "median_equivalent_square_resolution_km"
            ],
            "spatial_parity_status": spatial_grid_contract["parity_status"],
            "spatial_parity_blockers": spatial_grid_contract["parity_blockers"],
            "grid_resolution_contract_path": (
                output_dir / "public_report_grid_resolution_contract.json"
            ).as_posix(),
            "bounded_spatial_note": "The current contract is anchored to the fixture execution grid and bounded feasible-land rule, not a reproduced nationwide report surface.",
        },
        "supporting_artifacts": {
            "assumption_registry_path": (output_dir / "public_report_assumption_registry.json").as_posix(),
            "allocation_contract_path": (
                output_dir / "public_report_allocation_assumption_contract.json"
            ).as_posix(),
            "baxtel_schema_contract_path": (
                output_dir / "public_report_baxtel_schema_contract.json"
            ).as_posix(),
            "limitations_path": (output_dir / "public_report_limitations.md").as_posix(),
            "deviation_note_path": (output_dir / "public_report_bundle_deviations.md").as_posix(),
        },
        "validation_checks": validation_checks,
    }


def _write_public_report_reeds_integration_contract(repo_root, output_dir):
    """Write and validate the bounded reVeal-to-ReEDS handoff contract."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    contract_path = output_dir / "public_report_reeds_integration_contract.json"
    contract = _build_public_report_reeds_integration_contract(repo_root, output_dir)
    failed_checks = [check["name"] for check in contract["validation_checks"] if check["status"] != "passed"]
    if failed_checks:
        raise ValueError(
            "ReEDS integration contract validation failed for: "
            + ", ".join(sorted(failed_checks))
        )
    contract_path.write_text(json.dumps(contract, indent=2))
    return contract_path


def _select_public_buildout_cell_key(frame):
    """Select the stable cell identifier column used to accumulate buildout over time."""
    for column in ("sc_point_gid", "gid"):
        if column in frame.columns:
            return column
    raise ValueError("Buildout frame must include either sc_point_gid or gid")


def _public_report_bundle_config_by_output(repo_root):
    return {
        output_label: config
        for output_label, _, config in _load_public_report_bundle_smoke_configs(repo_root)
    }


def _build_public_cumulative_buildout_frame(
    frame,
    utilization_factor=1.0,
    max_site_addition_per_time_step_mw=None,
):
    """Add cumulative buildout columns using existing load plus cumulative new additions by cell."""
    required_columns = {"year", "new_dc_load_mw", "total_dc_load_mw"}
    missing_columns = sorted(required_columns.difference(frame.columns))
    if missing_columns:
        raise ValueError(f"Buildout frame is missing required columns: {missing_columns}")

    cell_key = _select_public_buildout_cell_key(frame)
    frame = frame.sort_values([cell_key, "year"]).reset_index(drop=True).copy()
    grouped = frame.groupby(cell_key, sort=False)
    frame["baseline_total_dc_load_mw"] = (
        grouped["total_dc_load_mw"].transform("first")
        - grouped["new_dc_load_mw"].transform("first")
    )
    frame["cumulative_new_dc_load_mw"] = grouped["new_dc_load_mw"].cumsum()
    frame["cumulative_total_dc_load_mw"] = (
        frame["baseline_total_dc_load_mw"] + frame["cumulative_new_dc_load_mw"]
    )

    utilization_factor = float(utilization_factor or 1.0)
    if utilization_factor <= 0 or utilization_factor > 1:
        raise ValueError("utilization_factor must be greater than 0 and no greater than 1")
    frame["utilization_factor"] = utilization_factor
    frame["new_dc_capacity_mw"] = frame["new_dc_load_mw"] / utilization_factor
    frame["baseline_total_dc_capacity_mw"] = (
        frame["baseline_total_dc_load_mw"] / utilization_factor
    )
    frame["cumulative_new_dc_capacity_mw"] = (
        frame["cumulative_new_dc_load_mw"] / utilization_factor
    )
    frame["cumulative_total_dc_capacity_mw"] = (
        frame["cumulative_total_dc_load_mw"] / utilization_factor
    )
    frame["max_site_addition_per_time_step_mw"] = max_site_addition_per_time_step_mw
    if max_site_addition_per_time_step_mw is None:
        frame["per_site_time_step_capacity_limit_exceeded"] = False
    else:
        frame["per_site_time_step_capacity_limit_exceeded"] = (
            frame["new_dc_capacity_mw"] > float(max_site_addition_per_time_step_mw) + 1e-6
        )

    if not np.allclose(
        frame["cumulative_total_dc_load_mw"],
        frame["total_dc_load_mw"],
        rtol=1e-9,
        atol=1e-6,
    ):
        raise ValueError(
            "Cumulative buildout derivation does not reconcile with total_dc_load_mw"
        )

    return frame


def _build_public_cumulative_buildout_summary(frame, source_output_name):
    """Summarize cumulative buildout by output source and year."""
    cell_key = _select_public_buildout_cell_key(frame)
    summary = (
        frame.groupby("year", dropna=False)
        .agg(
            cell_count=(cell_key, "nunique"),
            baseline_total_dc_load_mw=("baseline_total_dc_load_mw", "sum"),
            cumulative_new_dc_load_mw=("cumulative_new_dc_load_mw", "sum"),
            cumulative_total_dc_load_mw=("cumulative_total_dc_load_mw", "sum"),
            baseline_total_dc_capacity_mw=("baseline_total_dc_capacity_mw", "sum"),
            cumulative_new_dc_capacity_mw=("cumulative_new_dc_capacity_mw", "sum"),
            cumulative_total_dc_capacity_mw=("cumulative_total_dc_capacity_mw", "sum"),
            max_new_dc_capacity_mw=("new_dc_capacity_mw", "max"),
            per_site_time_step_capacity_limit_exceeded=(
                "per_site_time_step_capacity_limit_exceeded",
                "sum",
            ),
        )
        .reset_index()
        .sort_values("year")
    )
    summary.insert(0, "source_output_name", source_output_name)
    return summary


def _collect_public_report_bundle_outputs(bundle_status_path):
    """Collect output paths already produced by completed report-bundle workflow steps."""
    bundle_status_path = Path(bundle_status_path)
    if not bundle_status_path.exists():
        return []

    bundle_status = json.loads(bundle_status_path.read_text())
    output_paths = []
    for step_id, result in bundle_status.get("step_results", {}).items():
        if step_id == "run_public_reproduction":
            continue
        output_paths.extend(_collect_workflow_output_paths(result))
    return output_paths


def _build_public_report_bundle_manifest(
    repo_root,
    output_dir,
    reproduction_status_path,
    bundle_status_path,
    deviation_path,
):
    """Build the machine-readable manifest for the bounded public report bundle."""
    repo_root = Path(repo_root).resolve()
    output_dir = Path(output_dir)
    reproduction_status_path = Path(reproduction_status_path)
    reproduction_status = json.loads(reproduction_status_path.read_text())
    output_paths = []
    for result in reproduction_status.get("step_results", {}).values():
        output_paths.extend(_collect_workflow_output_paths(result))
    output_paths.extend(_collect_public_report_bundle_outputs(bundle_status_path))

    return {
        "bundle_type": "bounded-public-report-bundle",
        "workflow": "run-public-report-bundle",
        "repo_root": repo_root.as_posix(),
        "output_dir": output_dir.as_posix(),
        "bundle_status_path": Path(bundle_status_path).as_posix(),
        "reproduction_status_path": reproduction_status_path.as_posix(),
        "deviation_path": Path(deviation_path).as_posix(),
        "baseline_year": PUBLIC_REPORT_BUNDLE_BASELINE_YEAR,
        "report_baseline_year": PUBLIC_REPORT_BUNDLE_REPORT_BASELINE_YEAR,
        "grid_path": (repo_root / PUBLIC_REPORT_BUNDLE_GRID_PATH).as_posix(),
        "grid_priority": PUBLIC_REPORT_BUNDLE_GRID_PRIORITY,
        "completed_steps": reproduction_status.get("completed_steps", []),
        "output_paths": sorted(set(output_paths)),
    }


def _resolve_public_report_bundle_reproduction_status_path(
    bundle_status_path,
    reproduction_status_path,
):
    """Resolve the nested reproduction status path from either the default path or the saved step result."""
    reproduction_status_path = Path(reproduction_status_path)
    if reproduction_status_path.exists():
        return reproduction_status_path

    bundle_status_path = Path(bundle_status_path)
    if not bundle_status_path.exists():
        return reproduction_status_path

    bundle_status = json.loads(bundle_status_path.read_text())
    nested_status_path = bundle_status.get("step_results", {}).get("run_public_reproduction")
    if isinstance(nested_status_path, str):
        return Path(nested_status_path)
    return reproduction_status_path


def _write_public_report_bundle_manifest(
    repo_root,
    output_dir,
    reproduction_status_path,
    bundle_status_path,
):
    """Write the machine-readable manifest for the bounded public report bundle."""
    output_dir = Path(output_dir)
    manifest_path = output_dir / "public_report_bundle_manifest.json"
    deviation_path = output_dir / "public_report_bundle_deviations.md"
    reproduction_status_path = _resolve_public_report_bundle_reproduction_status_path(
        bundle_status_path,
        reproduction_status_path,
    )
    manifest = _build_public_report_bundle_manifest(
        repo_root,
        output_dir,
        reproduction_status_path,
        bundle_status_path,
        deviation_path,
    )
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return manifest_path


def _write_public_report_bundle_deviations(repo_root, output_dir):
    """Write the human-readable deviation note for the bounded public report bundle."""
    output_dir = Path(output_dir)
    deviation_path = output_dir / "public_report_bundle_deviations.md"
    deviation_path.write_text("\n".join(_report_bundle_deviation_lines(repo_root)) + "\n")
    return deviation_path


def _write_public_report_bundle_cumulative_buildout(
    repo_root,
    output_dir,
    reproduction_status_path,
    bundle_status_path=None,
):
    """Write cumulative buildout artifacts derived from the existing downscaled smoke outputs."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    reproduction_status_path = _resolve_public_report_bundle_reproduction_status_path(
        bundle_status_path or reproduction_status_path,
        reproduction_status_path,
    )
    reproduction_status = json.loads(reproduction_status_path.read_text())
    step_results = reproduction_status.get("step_results", {})
    config_by_output = _public_report_bundle_config_by_output(repo_root)

    cumulative_output_paths = []
    summary_frames = []
    for step_id in ("total_smoke", "regional_smoke"):
        step_result = step_results.get(step_id, {})
        if not isinstance(step_result, dict):
            continue
        output_path = step_result.get("output_path")
        if not isinstance(output_path, str):
            continue

        source_path = Path(output_path)
        source_config = config_by_output.get(source_path.stem, {})
        buildout_frame = _build_public_cumulative_buildout_frame(
            gpd.read_file(source_path),
            utilization_factor=source_config.get("utilization_factor", 1.0),
            max_site_addition_per_time_step_mw=source_config.get(
                "max_site_addition_per_time_step"
            ),
        )
        cumulative_path = output_dir / f"{source_path.stem}_cumulative_buildout.gpkg"
        buildout_frame.to_file(cumulative_path, driver="GPKG")
        cumulative_output_paths.append(cumulative_path.as_posix())
        summary_frames.append(
            _build_public_cumulative_buildout_summary(buildout_frame, source_path.stem)
        )

    if not cumulative_output_paths:
        raise ValueError("No downscale smoke outputs were available for cumulative buildout export")

    summary_path = output_dir / "public_report_bundle_cumulative_buildout_summary.csv"
    pd.concat(summary_frames, ignore_index=True).to_csv(summary_path, index=False)
    cumulative_output_paths.append(summary_path.as_posix())
    return {"outputs": cumulative_output_paths}


def _write_public_report_bundle_grid_surfaces(repo_root, output_dir, use_census_geolookup=True):
    """Write bounded feasible-land and suitability-percentile surfaces from the execution grid."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    grid_frame, _ = _load_public_report_bundle_grid(repo_root)

    feasible_land = _build_public_report_feasible_land_frame(repo_root, grid_frame)
    feasible_land_path = output_dir / "public_report_feasible_land.gpkg"
    feasible_land.to_file(feasible_land_path, driver="GPKG")

    suitability_base = _build_public_report_suitability_percentile_frame(feasible_land)
    census_geographies = None
    if use_census_geolookup:
        census_geographies = _fetch_public_report_census_geographies(
            suitability_base,
            cache_path=output_dir / "public_report_census_geography_cache.json",
            progress_label="Census GeoLookup",
        )
    suitability = _annotate_public_report_cell_names(
        suitability_base,
        census_geographies=census_geographies,
    )
    state_boundaries, state_boundary_path = _write_public_report_state_boundaries(
        output_dir,
        suitability,
    )
    ranked_suitability = _build_public_report_ranked_suitability_summary(suitability)
    census_miss_frame = _build_public_report_census_geolookup_miss_frame(
        ranked_suitability,
        state_boundaries,
    )
    suitability = _apply_public_report_census_miss_classification(suitability, census_miss_frame)
    ranked_suitability = _apply_public_report_census_miss_classification(
        ranked_suitability,
        census_miss_frame,
    )
    census_miss_outputs = _write_public_report_census_geolookup_miss_artifacts(
        output_dir,
        ranked_suitability,
        census_miss_frame,
    )

    suitability_path = output_dir / "public_report_suitability_percentiles.gpkg"
    suitability.to_file(suitability_path, driver="GPKG")

    ranked_suitability_path = output_dir / "public_report_suitability_ranked_cells.csv"
    ranked_suitability.to_csv(ranked_suitability_path, index=False)

    zoning_proxy, zoning_proxy_path = _write_public_report_zoning_proxy(
        output_dir,
        repo_root,
        suitability,
    )
    permitting_proxy, permitting_proxy_path = _write_public_report_permitting_proxy(
        output_dir,
        repo_root,
        suitability,
    )
    social_friction_proxy, social_friction_proxy_path = _write_public_report_social_friction_proxy(
        output_dir,
        repo_root,
        suitability,
    )
    hosting_proxy, hosting_capacity_proxy_path = _write_public_report_hosting_capacity_proxy(
        output_dir,
        repo_root,
        suitability,
    )

    suitability_map_path = _write_public_report_suitability_map(
        output_dir,
        feasible_land,
        suitability,
        ranked_suitability,
        state_boundaries,
        zoning_proxy,
        permitting_proxy,
        social_friction_proxy,
        hosting_proxy,
    )

    return {
        "outputs": [
            feasible_land_path.as_posix(),
            suitability_path.as_posix(),
            ranked_suitability_path.as_posix(),
            *census_miss_outputs["outputs"],
            state_boundary_path.as_posix(),
            zoning_proxy_path.as_posix(),
            permitting_proxy_path.as_posix(),
            social_friction_proxy_path.as_posix(),
            hosting_capacity_proxy_path.as_posix(),
            suitability_map_path.as_posix(),
        ]
    }


def run_public_report_bundle(
    repo_root=".",
    output_dir=None,
    status_path=None,
    reproduction_status_path=None,
    resume=False,
    force=False,
    use_census_geolookup=True,
):
    """Materialize the bounded public report-output bundle and its explicit deviations."""
    repo_root = Path(repo_root).resolve()
    output_dir = Path(output_dir) if output_dir is not None else _default_public_report_bundle_output_dir(repo_root)
    bundle_status_path = (
        Path(status_path) if status_path is not None else _default_public_report_bundle_status_path(output_dir)
    )
    reproduction_status_path = (
        Path(reproduction_status_path)
        if reproduction_status_path is not None
        else _default_public_report_bundle_reproduction_status_path(output_dir)
    )

    if force and output_dir.exists() and not resume:
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_public_report_bundle_readme(output_dir)

    steps = [
        {
            "step_id": "run_public_reproduction",
            "runner": lambda: run_public_reproduction_workflow(
                repo_root=repo_root,
                status_path=reproduction_status_path,
                resume=resume,
                force=force,
            ),
        },
        {
            "step_id": "write_cumulative_buildout",
            "runner": lambda: _write_public_report_bundle_cumulative_buildout(
                repo_root,
                output_dir,
                reproduction_status_path,
                bundle_status_path=bundle_status_path,
            ),
        },
        {
            "step_id": "write_grid_surfaces",
            "runner": lambda: _write_public_report_bundle_grid_surfaces(
                repo_root,
                output_dir,
                use_census_geolookup=use_census_geolookup,
            ),
        },
        {
            "step_id": "write_grid_resolution_contract",
            "runner": lambda: _write_public_report_grid_resolution_contract(
                repo_root,
                output_dir,
            ),
        },
        {
            "step_id": "write_allocation_assumption_contract",
            "runner": lambda: _write_public_report_allocation_assumption_contract(
                repo_root,
                output_dir,
            ),
        },
        {
            "step_id": "write_baxtel_schema_contract",
            "runner": lambda: _write_public_report_baxtel_schema_contract(
                repo_root,
                output_dir,
            ),
        },
        {
            "step_id": "write_assumption_registry",
            "runner": lambda: _write_public_report_assumption_registry(
                repo_root,
                output_dir,
            ),
        },
        {
            "step_id": "write_limitations_note",
            "runner": lambda: _write_public_report_limitations(output_dir),
        },
        {
            "step_id": "write_reeds_integration_contract",
            "runner": lambda: _write_public_report_reeds_integration_contract(
                repo_root,
                output_dir,
            ),
        },
        {
            "step_id": "write_bundle_manifest",
            "runner": lambda: _write_public_report_bundle_manifest(
                repo_root,
                output_dir,
                reproduction_status_path,
                bundle_status_path,
            ),
        },
        {
            "step_id": "write_bundle_deviations",
            "runner": lambda: _write_public_report_bundle_deviations(repo_root, output_dir),
        },
    ]

    _run_checkpointed_workflow(
        "run-public-report-bundle",
        steps,
        repo_root=repo_root,
        status_path=bundle_status_path,
        resume=resume,
        force=force,
    )
    return output_dir


def run_public_reproduction_workflow(repo_root=".", status_path=None, resume=False, force=False):
    """Run the bounded public-data reproduction workflow with checkpointed step status."""
    steps = _build_public_reproduction_steps(repo_root)
    return _run_checkpointed_workflow(
        "run-public-reproduction",
        steps,
        repo_root=repo_root,
        status_path=status_path,
        default_status_relpath="external-data/derived/public_reproduction_status.json",
        resume=resume,
        force=force,
    )


def stage_public_dataset(
    dataset_id,
    repo_root=".",
    force=False,
    download_url_override=None,
    download_representative=False,
    resume=False,
):
    """
    Stage a public dataset into the local ``external-data/raw`` surface.

    Manual datasets receive a ``MANUAL_DOWNLOAD.txt`` instruction file. Direct
    datasets are downloaded to the configured target path. Manual datasets can also
    download a representative payload when ``download_representative`` is true and a
    direct package URL is available.
    """
    if dataset_id not in PUBLIC_DATASET_CATALOG:
        raise KeyError(f"Unknown dataset_id: {dataset_id}")

    repo_root = Path(repo_root)
    spec = PUBLIC_DATASET_CATALOG[dataset_id]
    output_path = repo_root / spec.output_relpath
    output_path.parent.mkdir(parents=True, exist_ok=True)
    download_url = download_url_override or spec.download_url

    if output_path.exists() and not force and not (resume and spec.acquisition_mode == "direct"):
        return output_path

    if spec.acquisition_mode == "direct":
        if download_url is None:
            raise ValueError(f"Missing download URL for dataset: {dataset_id}")
        return _download_with_progress(download_url, output_path, resume=resume)

    if force or not output_path.exists():
        _write_manual_dataset_note(output_path, spec, download_url)

    if not download_representative:
        return output_path

    if dataset_id == "nlcd":
        _, tif_path, _ = _resolve_public_nlcd_representative_paths(repo_root)
        if tif_path.exists() and not force:
            return tif_path

    if download_url is None:
        raise ValueError(f"Missing representative download URL for dataset: {dataset_id}")

    representative_path = output_path.parent / _resolve_download_filename(
        download_url, dataset_id
    )
    if representative_path.exists() and not force and not resume:
        if dataset_id == "nlcd" and representative_path.suffix.lower() == ".zip":
            if not zipfile.is_zipfile(representative_path):
                representative_path.unlink(missing_ok=True)
            else:
                return representative_path
        else:
            return representative_path

    if dataset_id != "nlcd":
        return _download_with_progress(download_url, representative_path, resume=resume)

    try:
        return _download_with_progress(download_url, representative_path, resume=resume)
    except (urllib.error.URLError, OSError):
        representative_path.unlink(missing_ok=True)
        return _stage_public_nlcd_wms_fallback(repo_root, force=force)


def _write_example_json(path, payload):
    """Write a small JSON payload used by an example bundle."""
    path.write_text(json.dumps(payload, indent=2))


def _write_minimal_mapping_workbook(xlsx_path):
    """Write a minimal mapping workbook for the public water example bundle."""
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
        f'<si><t xml:space="preserve">{value}</t></si>' for value in shared_strings
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


def _write_public_data_center_example_bundle(bundle_dir):
    """Stage a minimal runnable input bundle for the data-center baseline."""
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
    ).to_csv(bundle_dir / "manual_data_centers.csv", index=False)
    _write_example_json(
        bundle_dir / "osm_data_centers.json",
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
        },
    )
    _write_example_json(
        bundle_dir / "wikidata_data_centers.json",
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
        },
    )


def _write_public_power_example_bundle(bundle_dir):
    """Stage a minimal runnable input bundle for the power baseline."""
    _write_example_json(
        bundle_dir / "osm_transmission_lines.json",
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
        },
    )
    _write_example_json(
        bundle_dir / "osm_substations.json",
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
        },
    )


def _write_public_fiber_example_bundle(bundle_dir):
    """Stage a minimal runnable input bundle for the fiber proxy workflow."""
    _write_example_json(
        bundle_dir / "osm_fiber_lines.json",
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
        },
    )
    gpd.GeoDataFrame(
        {"technology": ["Fiber to the Premises"]},
        geometry=[box(-105.0, 39.69, -104.96, 39.71)],
        crs="EPSG:4326",
    ).to_file(bundle_dir / "fcc_bdc_fiber_availability.gpkg", driver="GPKG")
    with rasterio.open(
        bundle_dir / "template.tif",
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


def _write_public_gas_example_bundle(bundle_dir):
    """Stage a minimal runnable input bundle for the gas territory workflow."""
    gpd.GeoDataFrame(
        {"utility_name": ["Lone Star Gas"]},
        geometry=[box(-97.0, 31.0, -96.5, 31.5)],
        crs="EPSG:4326",
    ).to_file(bundle_dir / "texas_gas.gpkg", driver="GPKG")
    pd.DataFrame(
        [
            {
                "state": "TX",
                "path": "texas_gas.gpkg",
                "utility_field": "utility_name",
            }
        ]
    ).to_csv(bundle_dir / "state_gas_service_territories.csv", index=False)


def _write_example_zone_bundle(path):
    """Write a one-zone example GeoPackage."""
    gpd.GeoDataFrame(
        {"emm_zone": ["North"], "zone_group": ["East"]},
        geometry=[box(-100.0, 30.0, -99.0, 31.0)],
        crs="EPSG:4326",
    ).to_file(path, driver="GPKG")


def _write_public_land_value_example_bundle(bundle_dir):
    """Stage a minimal runnable input bundle for the land-value proxy workflow."""
    pd.DataFrame(
        [
            {
                "county_id": "001",
                "state": "TX",
                "land_value_proxy_usd_per_acre": 1000.0,
            },
            {
                "county_id": "003",
                "state": "TX",
                "land_value_proxy_usd_per_acre": 3000.0,
            },
        ]
    ).to_csv(bundle_dir / "county_land_value_proxy.csv", index=False)
    gpd.GeoDataFrame(
        {"county_id": ["001", "003"], "state": ["TX", "TX"]},
        geometry=[
            box(-100.0, 30.0, -99.5, 30.5),
            box(-99.5, 30.0, -99.0, 30.5),
        ],
        crs="EPSG:4326",
    ).to_file(bundle_dir / "county_land_value_counties.gpkg", driver="GPKG")
    _write_example_zone_bundle(bundle_dir / "zones.gpkg")


def _write_public_construction_cost_example_bundle(bundle_dir):
    """Stage a minimal runnable input bundle for the construction-cost proxy workflow."""
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
    ).to_csv(bundle_dir / "county_construction_cost_proxy.csv", index=False)
    gpd.GeoDataFrame(
        {"county_id": ["001", "003"], "state": ["TX", "OK"]},
        geometry=[
            box(-100.0, 30.0, -99.5, 30.5),
            box(-99.5, 30.0, -99.0, 30.5),
        ],
        crs="EPSG:4326",
    ).to_file(bundle_dir / "county_construction_cost_counties.gpkg", driver="GPKG")
    _write_example_zone_bundle(bundle_dir / "zones.gpkg")


def _write_public_water_example_bundle(bundle_dir):
    """Stage a minimal runnable input bundle for the water proxy workflow."""
    pd.DataFrame(
        [
            {
                "state": "alpha",
                "freshwater_withdrawal_mgd": 120.0,
            }
        ]
    ).to_csv(bundle_dir / "usgs_state_water_use_proxy.csv", index=False)
    _write_minimal_mapping_workbook(bundle_dir / "state_zone_mapping.xlsx")
    _write_example_zone_bundle(bundle_dir / "zones.gpkg")


PUBLIC_EXAMPLE_BUNDLE_CATALOG = {
    "public_data_center_baseline": PublicExampleBundleSpec(
        bundle_id="public_data_center_baseline",
        output_relpath="external-data/examples/public_data_center_baseline",
        writer=_write_public_data_center_example_bundle,
        command=(
            "python",
            "-m",
            "reVeal.public_data",
            "generate-data-center-baseline",
            "--osm-payload",
            "external-data/examples/public_data_center_baseline/osm_data_centers.json",
            "--wikidata-payload",
            "external-data/examples/public_data_center_baseline/wikidata_data_centers.json",
            "--manual-csv",
            "external-data/examples/public_data_center_baseline/manual_data_centers.csv",
            "--output-dir",
            "external-data/examples/public_data_center_baseline/output",
        ),
        expected_outputs=(
            "public_data_center_baseline.csv",
            "public_data_center_baseline.gpkg",
        ),
        notes="Minimal OSM, Wikidata, and manual augmentation inputs.",
    ),
    "public_power_infrastructure_baseline": PublicExampleBundleSpec(
        bundle_id="public_power_infrastructure_baseline",
        output_relpath="external-data/examples/public_power_infrastructure_baseline",
        writer=_write_public_power_example_bundle,
        command=(
            "python",
            "-m",
            "reVeal.public_data",
            "generate-power-infrastructure-baseline",
            "--line-payload",
            "external-data/examples/public_power_infrastructure_baseline/osm_transmission_lines.json",
            "--substation-payload",
            "external-data/examples/public_power_infrastructure_baseline/osm_substations.json",
            "--output-dir",
            "external-data/examples/public_power_infrastructure_baseline/output",
        ),
        expected_outputs=(
            "public_transmission_lines_135kv.gpkg",
            "public_substations.gpkg",
        ),
        notes="Minimal OSM transmission-line and substation payloads.",
    ),
    "public_fiber_proxy_baseline": PublicExampleBundleSpec(
        bundle_id="public_fiber_proxy_baseline",
        output_relpath="external-data/examples/public_fiber_proxy_baseline",
        writer=_write_public_fiber_example_bundle,
        command=(
            "python",
            "-m",
            "reVeal.public_data",
            "generate-fiber-proxy-rasters",
            "--osm-payload",
            "external-data/examples/public_fiber_proxy_baseline/osm_fiber_lines.json",
            "--fcc-availability",
            "external-data/examples/public_fiber_proxy_baseline/fcc_bdc_fiber_availability.gpkg",
            "--template-raster",
            "external-data/examples/public_fiber_proxy_baseline/template.tif",
            "--output-dir",
            "external-data/examples/public_fiber_proxy_baseline/output",
        ),
        expected_outputs=(
            "public_fiber_route_proxy.gpkg",
            "fiber_lines_onshore_proximity.tif",
            "fiber_availability_binary.tif",
        ),
        notes="Minimal OSM fiber linework, FCC availability geometry, and aligned raster.",
    ),
    "public_gas_service_territory_baseline": PublicExampleBundleSpec(
        bundle_id="public_gas_service_territory_baseline",
        output_relpath="external-data/examples/public_gas_service_territory_baseline",
        writer=_write_public_gas_example_bundle,
        command=(
            "python",
            "-m",
            "reVeal.public_data",
            "generate-gas-service-territory-baseline",
            "--manifest-csv",
            "external-data/examples/public_gas_service_territory_baseline/state_gas_service_territories.csv",
            "--output-dir",
            "external-data/examples/public_gas_service_territory_baseline/output",
        ),
        expected_outputs=(
            "public_gas_service_territories.gpkg",
            "public_gas_service_territories_state_index.csv",
        ),
        notes="Minimal state extract plus manifest for a one-state assembly example.",
    ),
    "public_land_value_proxy": PublicExampleBundleSpec(
        bundle_id="public_land_value_proxy",
        output_relpath="external-data/examples/public_land_value_proxy",
        writer=_write_public_land_value_example_bundle,
        command=(
            "python",
            "-m",
            "reVeal.public_data",
            "generate-land-value-proxy-features",
            "--county-proxy-csv",
            "external-data/examples/public_land_value_proxy/county_land_value_proxy.csv",
            "--county-polygons",
            "external-data/examples/public_land_value_proxy/county_land_value_counties.gpkg",
            "--regions",
            "external-data/examples/public_land_value_proxy/zones.gpkg",
            "--output-dir",
            "external-data/examples/public_land_value_proxy/output",
        ),
        expected_outputs=(
            "public_land_value_county.gpkg",
            "public_land_value_emm_zone.gpkg",
        ),
        notes="Minimal county proxy CSV, county polygons, and zone geometry.",
    ),
    "public_construction_cost_proxy": PublicExampleBundleSpec(
        bundle_id="public_construction_cost_proxy",
        output_relpath="external-data/examples/public_construction_cost_proxy",
        writer=_write_public_construction_cost_example_bundle,
        command=(
            "python",
            "-m",
            "reVeal.public_data",
            "generate-construction-cost-proxy-features",
            "--county-proxy-csv",
            "external-data/examples/public_construction_cost_proxy/county_construction_cost_proxy.csv",
            "--county-polygons",
            "external-data/examples/public_construction_cost_proxy/county_construction_cost_counties.gpkg",
            "--regions",
            "external-data/examples/public_construction_cost_proxy/zones.gpkg",
            "--output-dir",
            "external-data/examples/public_construction_cost_proxy/output",
        ),
        expected_outputs=(
            "public_construction_cost_county.gpkg",
            "public_construction_cost_emm_zone.gpkg",
        ),
        notes="Minimal county wage-and-price proxy inputs plus zone geometry.",
    ),
    "public_water_availability_proxy": PublicExampleBundleSpec(
        bundle_id="public_water_availability_proxy",
        output_relpath="external-data/examples/public_water_availability_proxy",
        writer=_write_public_water_example_bundle,
        command=(
            "python",
            "-m",
            "reVeal.public_data",
            "generate-water-availability-proxy-features",
            "--state-proxy-csv",
            "external-data/examples/public_water_availability_proxy/usgs_state_water_use_proxy.csv",
            "--mapping-workbook",
            "external-data/examples/public_water_availability_proxy/state_zone_mapping.xlsx",
            "--regions",
            "external-data/examples/public_water_availability_proxy/zones.gpkg",
            "--output-dir",
            "external-data/examples/public_water_availability_proxy/output",
        ),
        expected_outputs=(
            "public_water_availability_state_proxy.csv",
            "public_water_availability_emm_zone.gpkg",
        ),
        notes="Minimal state proxy CSV, mapping workbook, and zone geometry.",
    ),
}


def _write_example_bundle_readme(bundle_dir, spec):
    """Write the README that documents a runnable example command for a bundle."""
    output_dir = Path(spec.output_relpath) / "output"
    readme_path = bundle_dir / "README.md"
    readme_path.write_text(
        "\n".join(
            [
                f"# {spec.bundle_id}",
                "",
                spec.notes,
                "",
                "Run from the repository root:",
                "",
                "```bash",
                " ".join(spec.command),
                "```",
                "",
                f"Expected outputs under `{output_dir.as_posix()}`:",
                "",
                *[f"- `{name}`" for name in spec.expected_outputs],
                "",
            ]
        )
    )


def stage_public_example_bundle(bundle_id, repo_root=".", force=False):
    """Stage a minimal runnable example-input bundle for a generated public workflow."""
    if bundle_id not in PUBLIC_EXAMPLE_BUNDLE_CATALOG:
        raise KeyError(f"Unknown bundle_id: {bundle_id}")

    repo_root = Path(repo_root)
    spec = PUBLIC_EXAMPLE_BUNDLE_CATALOG[bundle_id]
    bundle_dir = repo_root / spec.output_relpath

    if bundle_dir.exists():
        if not force:
            return bundle_dir
        shutil.rmtree(bundle_dir)

    bundle_dir.mkdir(parents=True, exist_ok=True)
    (bundle_dir / "output").mkdir(parents=True, exist_ok=True)
    spec.writer(bundle_dir)
    _write_example_bundle_readme(bundle_dir, spec)
    return bundle_dir


def _build_parser():
    """Build the command-line parser for public-data workflows."""
    parser = argparse.ArgumentParser(description="reVeal public-data utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list-datasets", help="List staged dataset specs")
    list_parser.set_defaults(command="list-datasets")

    stage_parser = subparsers.add_parser("stage-dataset", help="Stage a public dataset")
    stage_parser.add_argument("dataset_id", choices=sorted(PUBLIC_DATASET_CATALOG))
    stage_parser.add_argument("--repo-root", default=".")
    stage_parser.add_argument("--force", action="store_true")
    stage_parser.add_argument("--resume", action="store_true")
    stage_parser.add_argument("--download-representative", action="store_true")
    stage_parser.add_argument("--dfirm-id")
    stage_parser.add_argument("--state")
    stage_parser.add_argument("--county")
    stage_parser.add_argument("--file-name")

    example_parser = subparsers.add_parser(
        "stage-example-bundle",
        help="Stage a runnable example-input bundle for a generated public-data workflow",
    )
    example_parser.add_argument("bundle_id", choices=sorted(PUBLIC_EXAMPLE_BUNDLE_CATALOG))
    example_parser.add_argument("--repo-root", default=".")
    example_parser.add_argument("--force", action="store_true")

    workflow_parser = subparsers.add_parser(
        "run-public-reproduction",
        help="Run the bounded public-data reproduction workflow with checkpointed resume support",
    )
    workflow_parser.add_argument("--repo-root", default=".")
    workflow_parser.add_argument(
        "--status-path",
        default="external-data/derived/public_reproduction_status.json",
    )
    workflow_parser.add_argument("--resume", action="store_true")
    workflow_parser.add_argument("--force", action="store_true")

    report_bundle_parser = subparsers.add_parser(
        "run-public-report-bundle",
        help="Materialize the bounded public report-output bundle plus explicit deviations",
    )
    report_bundle_parser.add_argument("--repo-root", default=".")
    report_bundle_parser.add_argument("--output-dir")
    report_bundle_parser.add_argument("--status-path")
    report_bundle_parser.add_argument("--reproduction-status-path")
    report_bundle_parser.add_argument("--resume", action="store_true")
    report_bundle_parser.add_argument("--force", action="store_true")
    report_bundle_parser.add_argument(
        "--no-census-geolookup",
        dest="use_census_geolookup",
        action="store_false",
        help="Skip live Census coordinate GeoLookup identity enrichment",
    )
    report_bundle_parser.set_defaults(use_census_geolookup=True)

    example_workflow_parser = subparsers.add_parser(
        "run-public-example-workflows",
        help="Run the generated public example workflows with checkpointed resume support",
    )
    example_workflow_parser.add_argument("--repo-root", default=".")
    example_workflow_parser.add_argument(
        "--status-path",
        default="external-data/derived/public_example_workflows_status.json",
    )
    example_workflow_parser.add_argument("--resume", action="store_true")
    example_workflow_parser.add_argument("--force", action="store_true")
    example_workflow_parser.add_argument("--force-stage", action="store_true")

    summary_parser = subparsers.add_parser(
        "summarize-public-workflow-status",
        help="Print a compact summary of a checkpointed public workflow status file",
    )
    summary_parser.add_argument(
        "--status-path",
        default="external-data/derived/public_reproduction_status.json",
    )

    ribits_parser = subparsers.add_parser(
        "download-ribits-bank-sites",
        help="Download a repo-local RIBITS bank/site snapshot through the public webservices",
    )
    ribits_parser.add_argument(
        "--output-path",
        default="external-data/raw/ribits/ribits_bank_sites_snapshot.json",
    )
    ribits_parser.add_argument("--filters-json")
    ribits_parser.add_argument("--limit", type=int)
    ribits_parser.add_argument("--webconsumer-email")
    ribits_parser.add_argument("--resume", action="store_true")
    ribits_parser.add_argument("--checkpoint-path")
    ribits_parser.set_defaults(
        include_service_area=True,
        include_footprint=True,
        include_contacts=False,
        include_ledger=False,
    )
    ribits_parser.add_argument(
        "--no-service-area",
        dest="include_service_area",
        action="store_false",
    )
    ribits_parser.add_argument(
        "--no-footprint",
        dest="include_footprint",
        action="store_false",
    )
    ribits_parser.add_argument(
        "--include-contacts",
        dest="include_contacts",
        action="store_true",
    )
    ribits_parser.add_argument(
        "--include-ledger",
        dest="include_ledger",
        action="store_true",
    )

    fema_parser = subparsers.add_parser(
        "build-fema-download-url",
        help="Build a direct FEMA NFHL ZIP download URL for a community package",
    )
    fema_parser.add_argument("--dfirm-id", required=True)
    fema_parser.add_argument("--state", required=True)
    fema_parser.add_argument("--county", required=True)
    fema_parser.add_argument("--file-name", required=True)

    assess_parser = subparsers.add_parser(
        "assess-eer-drop-in",
        help="Assess whether the staged public EER workbook is a direct replacement",
    )
    assess_parser.add_argument(
        "--workbook",
        default="external-data/unpacked/eer/ADP2024_detailed_output_data.xlsx",
    )
    assess_parser.add_argument(
        "--total-anchor",
        default="tests/data/downscale/inputs/load_growth_projections/eer_us-adp-2024-central_national.csv",
    )
    assess_parser.add_argument(
        "--regional-anchor",
        default="tests/data/downscale/inputs/load_growth_projections/eer_us-adp-2024-central_region_groups.csv",
    )
    assess_parser.add_argument(
        "--generated-total",
        default="external-data/derived/eer/eer_public_central_high_data_center_national.csv",
    )
    assess_parser.add_argument(
        "--generated-regional",
        default="external-data/derived/eer/eer_public_central_high_data_center_region_groups.csv",
    )

    generate_parser = subparsers.add_parser(
        "generate-eer-loads",
        help="Generate reVeal-compatible public EER load-projection CSVs",
    )
    generate_parser.add_argument("--workbook", required=True)
    generate_parser.add_argument("--regions", required=True)
    generate_parser.add_argument("--output-dir", required=True)
    generate_parser.add_argument("--scenario", default=EER_PUBLIC_SCENARIO)

    data_center_parser = subparsers.add_parser(
        "generate-data-center-baseline",
        help="Generate a first-pass public data center baseline from local OSM and Wikidata payloads",
    )
    data_center_parser.add_argument("--osm-payload", required=True)
    data_center_parser.add_argument("--wikidata-payload", required=True)
    data_center_parser.add_argument("--output-dir", required=True)
    data_center_parser.add_argument("--manual-csv")

    power_parser = subparsers.add_parser(
        "generate-power-infrastructure-baseline",
        help="Generate first-pass public transmission-line and substation baseline layers from local OSM payloads",
    )
    power_parser.add_argument("--line-payload", required=True)
    power_parser.add_argument("--substation-payload", required=True)
    power_parser.add_argument("--output-dir", required=True)
    power_parser.add_argument("--min-voltage-kv", type=float, default=135.0)

    fiber_parser = subparsers.add_parser(
        "generate-fiber-proxy-rasters",
        help="Generate first-pass public fiber proxy artifacts from OSM linework and FCC availability geometry",
    )
    fiber_parser.add_argument("--osm-payload", required=True)
    fiber_parser.add_argument("--fcc-availability", required=True)
    fiber_parser.add_argument("--template-raster", required=True)
    fiber_parser.add_argument("--output-dir", required=True)

    gas_parser = subparsers.add_parser(
        "generate-gas-service-territory-baseline",
        help="Generate a merged public gas service territory layer from state-by-state extracts",
    )
    gas_parser.add_argument("--manifest-csv", required=True)
    gas_parser.add_argument("--output-dir", required=True)

    water_parser = subparsers.add_parser(
        "generate-water-availability-proxy-features",
        help="Generate a first-pass zonal water-availability proxy from state water-use inputs",
    )
    water_parser.add_argument("--state-proxy-csv", required=True)
    water_parser.add_argument("--mapping-workbook", required=True)
    water_parser.add_argument("--regions", required=True)
    water_parser.add_argument("--output-dir", required=True)
    water_parser.add_argument("--value-column", default="freshwater_withdrawal_mgd")

    land_parser = subparsers.add_parser(
        "generate-land-value-proxy-features",
        help="Generate first-pass county and zonal land-value proxy features",
    )
    land_parser.add_argument("--county-proxy-csv", required=True)
    land_parser.add_argument("--county-polygons", required=True)
    land_parser.add_argument("--regions", required=True)
    land_parser.add_argument("--output-dir", required=True)
    land_parser.add_argument("--value-column", default="land_value_proxy_usd_per_acre")

    construction_parser = subparsers.add_parser(
        "generate-construction-cost-proxy-features",
        help="Generate first-pass county and zonal construction-cost proxy features",
    )
    construction_parser.add_argument("--county-proxy-csv", required=True)
    construction_parser.add_argument("--county-polygons", required=True)
    construction_parser.add_argument("--regions", required=True)
    construction_parser.add_argument("--output-dir", required=True)
    construction_parser.add_argument(
        "--wage-column",
        default="construction_worker_mean_wage_usd",
    )
    construction_parser.add_argument(
        "--price-column",
        default="regional_price_parity_index",
    )

    nerc_parser = subparsers.add_parser(
        "generate-nerc-reserve-margin-features",
        help="Generate NERC reserve-margin artifacts for reVeal EMM zones and an optional grid",
    )
    nerc_parser.add_argument("--regions", required=True)
    nerc_parser.add_argument("--output-dir", required=True)
    nerc_parser.add_argument("--grid")

    return parser


def main(args=None):
    """CLI entry point for the public-data utilities."""
    parser = _build_parser()
    parsed = parser.parse_args(args=args)

    if parsed.command == "list-datasets":
        for dataset_id, spec in sorted(PUBLIC_DATASET_CATALOG.items()):
            print(f"{dataset_id}\t{spec.acquisition_mode}\t{spec.output_relpath}")
        return 0

    if parsed.command == "stage-dataset":
        fema_fields = (parsed.dfirm_id, parsed.state, parsed.county, parsed.file_name)
        if parsed.dataset_id != "fema_nfhl" and any(fema_fields):
            parser.error("FEMA download-url arguments are only valid with dataset_id=fema_nfhl")

        download_url_override = None
        if parsed.dataset_id == "fema_nfhl":
            if any(fema_fields) and not all(fema_fields):
                parser.error(
                    "FEMA staging requires --dfirm-id, --state, --county, and --file-name together"
                )
            if parsed.download_representative and not all(fema_fields):
                parser.error(
                    "FEMA representative download requires --dfirm-id, --state, --county, and --file-name"
                )
            if all(fema_fields):
                download_url_override = build_fema_nfhl_download_url(
                    parsed.dfirm_id,
                    parsed.state,
                    parsed.county,
                    parsed.file_name,
                )

        output_path = stage_public_dataset(
            parsed.dataset_id,
            repo_root=parsed.repo_root,
            force=parsed.force,
            download_url_override=download_url_override,
            download_representative=parsed.download_representative,
            resume=parsed.resume,
        )
        print(output_path)
        return 0

    if parsed.command == "stage-example-bundle":
        output_path = stage_public_example_bundle(
            parsed.bundle_id,
            repo_root=parsed.repo_root,
            force=parsed.force,
        )
        print(output_path)
        return 0

    if parsed.command == "run-public-reproduction":
        status_path = run_public_reproduction_workflow(
            repo_root=parsed.repo_root,
            status_path=parsed.status_path,
            resume=parsed.resume,
            force=parsed.force,
        )
        print(status_path)
        return 0

    if parsed.command == "run-public-report-bundle":
        output_dir = run_public_report_bundle(
            repo_root=parsed.repo_root,
            output_dir=parsed.output_dir,
            status_path=parsed.status_path,
            reproduction_status_path=parsed.reproduction_status_path,
            resume=parsed.resume,
            force=parsed.force,
            use_census_geolookup=parsed.use_census_geolookup,
        )
        print(output_dir)
        return 0

    if parsed.command == "run-public-example-workflows":
        status_path = run_public_example_workflows(
            repo_root=parsed.repo_root,
            status_path=parsed.status_path,
            resume=parsed.resume,
            force=parsed.force,
            force_stage=parsed.force_stage,
        )
        print(status_path)
        return 0

    if parsed.command == "summarize-public-workflow-status":
        for line in summarize_public_workflow_status(parsed.status_path):
            print(line)
        return 0

    if parsed.command == "download-ribits-bank-sites":
        filters = None
        if parsed.filters_json:
            try:
                filters = json.loads(parsed.filters_json)
            except json.JSONDecodeError as exc:
                parser.error(f"Invalid --filters-json payload: {exc}")
            if not isinstance(filters, dict):
                parser.error("--filters-json must decode to a JSON object")

        output_path = download_ribits_bank_site_snapshot(
            parsed.output_path,
            filters=filters,
            limit=parsed.limit,
            include_service_area=parsed.include_service_area,
            include_footprint=parsed.include_footprint,
            include_contacts=parsed.include_contacts,
            include_ledger=parsed.include_ledger,
            consumer_email=parsed.webconsumer_email,
            checkpoint_path=parsed.checkpoint_path,
            resume=parsed.resume,
        )
        print(output_path)
        return 0

    if parsed.command == "build-fema-download-url":
        print(
            build_fema_nfhl_download_url(
                parsed.dfirm_id,
                parsed.state,
                parsed.county,
                parsed.file_name,
            )
        )
        return 0

    if parsed.command == "assess-eer-drop-in":
        assessment = _run_with_progress(
            "assess-eer-drop-in",
            lambda: assess_public_eer_drop_in_compatibility_from_paths(
                parsed.workbook,
                parsed.total_anchor,
                parsed.regional_anchor,
                generated_total_path=parsed.generated_total,
                generated_regional_path=parsed.generated_regional,
            ),
        )
        for line in _format_drop_in_assessment(assessment):
            print(line)
        return 0

    if parsed.command == "generate-eer-loads":
        total_path, regional_path, grouped_path = _run_with_progress(
            "generate-eer-loads",
            lambda: generate_eer_public_projection_csvs(
                parsed.workbook,
                parsed.regions,
                parsed.output_dir,
                scenario_column=parsed.scenario,
            ),
        )
        print(total_path)
        print(regional_path)
        print(grouped_path)
        return 0

    if parsed.command == "generate-data-center-baseline":
        csv_path, gpkg_path = _run_with_progress(
            "generate-data-center-baseline",
            lambda: generate_public_data_center_baseline(
                parsed.osm_payload,
                parsed.wikidata_payload,
                parsed.output_dir,
                manual_csv_path=parsed.manual_csv,
            ),
        )
        print(csv_path)
        print(gpkg_path)
        return 0

    if parsed.command == "generate-power-infrastructure-baseline":
        line_path, substation_path = _run_with_progress(
            "generate-power-infrastructure-baseline",
            lambda: generate_public_power_infrastructure_baseline(
                parsed.line_payload,
                parsed.substation_payload,
                parsed.output_dir,
                min_voltage_kv=parsed.min_voltage_kv,
            ),
        )
        print(line_path)
        print(substation_path)
        return 0

    if parsed.command == "generate-fiber-proxy-rasters":
        line_vector_path, proximity_raster_path, availability_raster_path = _run_with_progress(
            "generate-fiber-proxy-rasters",
            lambda: generate_public_fiber_proxy_rasters(
                parsed.osm_payload,
                parsed.fcc_availability,
                parsed.template_raster,
                parsed.output_dir,
            ),
        )
        print(line_vector_path)
        print(proximity_raster_path)
        print(availability_raster_path)
        return 0

    if parsed.command == "generate-gas-service-territory-baseline":
        gpkg_path, summary_csv_path = _run_with_progress(
            "generate-gas-service-territory-baseline",
            lambda: generate_public_gas_service_territory_baseline(
                parsed.manifest_csv,
                parsed.output_dir,
            ),
        )
        print(gpkg_path)
        print(summary_csv_path)
        return 0

    if parsed.command == "generate-water-availability-proxy-features":
        state_output_path, zone_output_path = _run_with_progress(
            "generate-water-availability-proxy-features",
            lambda: generate_public_water_availability_proxy_features(
                parsed.state_proxy_csv,
                parsed.mapping_workbook,
                parsed.regions,
                parsed.output_dir,
                value_column=parsed.value_column,
            ),
        )
        print(state_output_path)
        print(zone_output_path)
        return 0

    if parsed.command == "generate-land-value-proxy-features":
        county_output_path, zone_output_path = _run_with_progress(
            "generate-land-value-proxy-features",
            lambda: generate_public_land_value_proxy_features(
                parsed.county_proxy_csv,
                parsed.county_polygons,
                parsed.regions,
                parsed.output_dir,
                value_column=parsed.value_column,
            ),
        )
        print(county_output_path)
        print(zone_output_path)
        return 0

    if parsed.command == "generate-construction-cost-proxy-features":
        county_output_path, zone_output_path = _run_with_progress(
            "generate-construction-cost-proxy-features",
            lambda: generate_public_construction_cost_proxy_features(
                parsed.county_proxy_csv,
                parsed.county_polygons,
                parsed.regions,
                parsed.output_dir,
                wage_column=parsed.wage_column,
                price_column=parsed.price_column,
            ),
        )
        print(county_output_path)
        print(zone_output_path)
        return 0

    if parsed.command == "generate-nerc-reserve-margin-features":
        assessment_path, zone_path, grid_path = _run_with_progress(
            "generate-nerc-reserve-margin-features",
            lambda: generate_nerc_reserve_margin_features(
                parsed.regions,
                parsed.output_dir,
                grid_path=parsed.grid,
            ),
        )
        print(assessment_path)
        print(zone_path)
        if grid_path is not None:
            print(grid_path)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())