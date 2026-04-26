# -*- coding: utf-8 -*-
"""Tests for the public EER downscale smoke-test runner."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pandas as pd


def _load_runner_module():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "external-data"
        / "derived"
        / "eer"
        / "run_downscale_smoke.py"
    )
    spec = spec_from_file_location("run_downscale_smoke", module_path)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_summarize_result_reports_long_form_load_output():
    """Regional smoke output should be summarized from long-form year/load columns."""

    module = _load_runner_module()
    result = pd.DataFrame(
        {
            "year": [2024, 2030],
            "total_dc_load_mw": [100.0, 110.0],
            "new_dc_load_mw": [10.0, 15.0],
        }
    )

    summary = module._summarize_result(result)

    assert summary == {
        "rows": 2,
        "years": [2024, 2030],
        "load_cols": ["total_dc_load_mw", "new_dc_load_mw"],
    }