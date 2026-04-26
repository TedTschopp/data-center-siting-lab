#!/usr/bin/env python3
"""Run smoke-test downscaling from a copied config file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from reVeal.grid import RegionalDownscaleGrid, TotalDownscaleGrid


def _resolve_repo_paths(config, repo_root):
    """Resolve repo-relative file paths in a copied config."""
    resolved = dict(config)
    path_keys = ["grid", "load_projections", "regions"]
    for key in path_keys:
        if key in resolved and resolved[key] is not None:
            resolved[key] = str(repo_root / resolved[key])
    return resolved


def _run_grid(config):
    """Instantiate and run the appropriate downscale grid."""
    if config["projection_resolution"].lower() == "regional":
        return RegionalDownscaleGrid(config).run()
    return TotalDownscaleGrid(config).run()


def _summarize_result(result):
    """Summarize smoke-test output for both long-form and wide-form load shapes."""
    summary = {"rows": len(result)}

    if "year" in result.columns:
        years = sorted({int(year) for year in result["year"].dropna().tolist()})
        summary["years"] = years

    load_cols = [
        column
        for column in ("total_dc_load_mw", "new_dc_load_mw")
        if column in result.columns
    ]
    if load_cols:
        summary["load_cols"] = load_cols

    year_cols = [column for column in result.columns if column.startswith("dc_load_mw_")]
    if year_cols:
        summary["year_cols"] = year_cols

    return summary


def main(args=None):
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Run reVeal public-EER smoke test")
    parser.add_argument("config", help="Repo-relative path to copied smoke config")
    parser.add_argument(
        "--output",
        required=True,
        help="Repo-relative output GeoPackage path",
    )
    parsed = parser.parse_args(args=args)

    repo_root = Path(__file__).resolve().parents[3]
    config_path = repo_root / parsed.config
    output_path = repo_root / parsed.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with config_path.open() as f:
        config = json.load(f)

    resolved = _resolve_repo_paths(config, repo_root)
    result = _run_grid(resolved)
    result.to_file(output_path, driver="GPKG")

    summary = _summarize_result(result)
    print(output_path)
    print(f"rows {summary['rows']}")
    if "years" in summary:
        print(f"years {summary['years']}")
    if "load_cols" in summary:
        print(f"load_cols {summary['load_cols']}")
    if "year_cols" in summary:
        print(f"year_cols {summary['year_cols']}")


if __name__ == "__main__":
    main()