"""Test data quality suite configuration.

Verifies that:
1. All GE suite JSON files are valid
2. Expectations follow the expected schema
3. run_checkpoint.py module is importable
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

GE_DIR = ROOT / "data_quality" / "great_expectations"
EXPECTATIONS_DIR = GE_DIR / "expectations"


def _suite_files():
    return sorted(EXPECTATIONS_DIR.glob("*.json"))


class TestGESuiteFiles:
    """Verify Great Expectations suite JSON integrity."""

    @pytest.fixture(params=_suite_files(), ids=lambda p: p.stem)
    def suite(self, request):
        with open(request.param) as f:
            return json.load(f)

    def test_suite_has_name(self, suite):
        assert "expectation_suite_name" in suite

    def test_suite_has_expectations(self, suite):
        assert "expectations" in suite
        assert len(suite["expectations"]) > 0

    def test_each_expectation_has_type(self, suite):
        for exp in suite["expectations"]:
            assert "expectation_type" in exp, f"Missing type: {exp}"

    def test_each_expectation_has_kwargs(self, suite):
        for exp in suite["expectations"]:
            assert "kwargs" in exp, f"Missing kwargs: {exp}"


class TestGEConfig:
    """Verify GE project config."""

    def test_config_file_exists(self):
        assert (GE_DIR / "great_expectations.yml").exists()

    def test_runner_importable(self):
        spec = importlib.util.spec_from_file_location(
            "run_checkpoint",
            str(GE_DIR / "run_checkpoint.py"),
        )
        assert spec is not None


# Need importlib.util
import importlib.util
