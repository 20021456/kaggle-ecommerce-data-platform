"""Tests for dbt model SQL structure and conventions.

Validates:
- All models follow naming conventions (stg_, int_, fct_, dim_, mart_)
- All .yml test files exist for each layer
- Models reference correct sources / refs
- No hardcoded table names (should use ref() or source())
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

DBT_MODELS_DIR = Path(__file__).resolve().parents[2] / "dbt" / "models"


# ── Helpers ─────────────────────────────────────────────────────────

def _sql_files(subdir: str) -> list[Path]:
    """Return all .sql files under dbt/models/{subdir}/."""
    d = DBT_MODELS_DIR / subdir
    if not d.exists():
        return []
    return sorted(d.rglob("*.sql"))


def _yml_files(subdir: str) -> list[Path]:
    """Return all .yml files under dbt/models/{subdir}/."""
    d = DBT_MODELS_DIR / subdir
    if not d.exists():
        return []
    return sorted(d.rglob("*.yml"))


# ── Test: staging models follow naming conventions ──────────────────

class TestStagingModels:
    """Verify staging layer models."""

    sql_files = _sql_files("stagings")

    @pytest.mark.skipif(not _sql_files("stagings"), reason="No staging models found")
    def test_staging_files_exist(self):
        assert len(self.sql_files) >= 7, (
            f"Expected at least 7 staging models (7 Olist + crypto + economic), "
            f"found {len(self.sql_files)}"
        )

    @pytest.mark.skipif(not _sql_files("stagings"), reason="No staging models found")
    @pytest.mark.parametrize("sql_file", _sql_files("stagings"), ids=lambda f: f.name)
    def test_staging_prefix(self, sql_file: Path):
        assert sql_file.stem.startswith("stg_"), (
            f"Staging model {sql_file.name} should start with 'stg_'"
        )

    @pytest.mark.skipif(not _sql_files("stagings"), reason="No staging models found")
    @pytest.mark.parametrize("sql_file", _sql_files("stagings"), ids=lambda f: f.name)
    def test_staging_uses_source(self, sql_file: Path):
        content = sql_file.read_text(encoding="utf-8")
        assert "source(" in content or "ref(" in content, (
            f"Staging model {sql_file.name} should use source() or ref(), not raw table names"
        )

    def test_staging_yml_exists(self):
        yml = _yml_files("stagings")
        assert len(yml) >= 1, "At least one _stagings.yml test file should exist"


# ── Test: intermediate models follow conventions ────────────────────

class TestIntermediateModels:
    """Verify intermediate layer models."""

    sql_files = _sql_files("intermediate")

    @pytest.mark.skipif(not _sql_files("intermediate"), reason="No intermediate models")
    def test_intermediate_files_exist(self):
        assert len(self.sql_files) >= 4, (
            f"Expected at least 4 intermediate models, found {len(self.sql_files)}"
        )

    @pytest.mark.skipif(not _sql_files("intermediate"), reason="No intermediate models")
    @pytest.mark.parametrize("sql_file", _sql_files("intermediate"), ids=lambda f: f.name)
    def test_intermediate_prefix(self, sql_file: Path):
        assert sql_file.stem.startswith("int_"), (
            f"Intermediate model {sql_file.name} should start with 'int_'"
        )

    @pytest.mark.skipif(not _sql_files("intermediate"), reason="No intermediate models")
    @pytest.mark.parametrize("sql_file", _sql_files("intermediate"), ids=lambda f: f.name)
    def test_intermediate_uses_ref(self, sql_file: Path):
        content = sql_file.read_text(encoding="utf-8")
        assert "ref(" in content, (
            f"Intermediate model {sql_file.name} should use ref() to reference staging models"
        )

    def test_intermediate_yml_exists(self):
        yml = _yml_files("intermediate")
        assert len(yml) >= 1, "At least one _intermediate.yml test file should exist"


# ── Test: mart models follow conventions ────────────────────────────

class TestMartModels:
    """Verify mart (Gold) layer models."""

    sql_files = _sql_files("marts")

    @pytest.mark.skipif(not _sql_files("marts"), reason="No mart models")
    def test_mart_files_exist(self):
        assert len(self.sql_files) >= 6, (
            f"Expected at least 6 mart models (fact + dim + marts), found {len(self.sql_files)}"
        )

    @pytest.mark.skipif(not _sql_files("marts"), reason="No mart models")
    @pytest.mark.parametrize("sql_file", _sql_files("marts"), ids=lambda f: f.name)
    def test_mart_valid_prefix(self, sql_file: Path):
        valid_prefixes = ("fct_", "dim_", "mart_")
        assert any(sql_file.stem.startswith(p) for p in valid_prefixes), (
            f"Mart model {sql_file.name} should start with fct_, dim_, or mart_"
        )

    @pytest.mark.skipif(not _sql_files("marts"), reason="No mart models")
    @pytest.mark.parametrize("sql_file", _sql_files("marts"), ids=lambda f: f.name)
    def test_mart_uses_ref(self, sql_file: Path):
        content = sql_file.read_text(encoding="utf-8")
        assert "ref(" in content or "source(" in content, (
            f"Mart model {sql_file.name} should use ref() or source()"
        )

    def test_mart_yml_exists(self):
        yml = _yml_files("marts")
        assert len(yml) >= 1, "At least one _marts.yml test file should exist"


# ── Test: no hardcoded schema references ────────────────────────────

class TestNoHardcodedTables:
    """Ensure models use ref()/source() instead of raw table names."""

    all_sql = list(DBT_MODELS_DIR.rglob("*.sql"))
    HARDCODED_PATTERN = re.compile(
        r"\bFROM\s+(bronze|silver|gold|staging|public)\.\w+",
        re.IGNORECASE,
    )

    @pytest.mark.skipif(not list(DBT_MODELS_DIR.rglob("*.sql")), reason="No SQL models")
    @pytest.mark.parametrize("sql_file", list(DBT_MODELS_DIR.rglob("*.sql")), ids=lambda f: f.name)
    def test_no_hardcoded_schema(self, sql_file: Path):
        content = sql_file.read_text(encoding="utf-8")
        matches = self.HARDCODED_PATTERN.findall(content)
        # Allow source() / ref() macros to resolve — only flag raw schema.table
        # Filter out Jinja template contexts
        raw_refs = [
            m for m in self.HARDCODED_PATTERN.finditer(content)
            if "{{" not in content[max(0, m.start() - 20): m.start()]
        ]
        assert len(raw_refs) == 0, (
            f"Model {sql_file.name} has hardcoded table references: "
            f"{[m.group() for m in raw_refs]}. Use ref() or source() instead."
        )


# ── Test: star schema completeness (ecommerce) ─────────────────────

class TestStarSchemaCompleteness:
    """Verify e-commerce star schema has required fact + dimension tables."""

    ecommerce_marts = _sql_files("marts/ecommerce")
    names = [f.stem for f in ecommerce_marts]

    def test_has_fact_orders(self):
        assert "fct_orders" in self.names, "Missing fct_orders in ecommerce marts"

    def test_has_dim_customers(self):
        assert "dim_customers" in self.names, "Missing dim_customers"

    def test_has_dim_products(self):
        assert "dim_products" in self.names, "Missing dim_products"

    def test_has_dim_sellers(self):
        assert "dim_sellers" in self.names, "Missing dim_sellers"

    def test_has_dim_time(self):
        assert "dim_time" in self.names, "Missing dim_time"

    def test_has_dim_geography(self):
        assert "dim_geography" in self.names, "Missing dim_geography"

    def test_has_mart_sales(self):
        assert "mart_sales" in self.names, "Missing mart_sales"

    def test_has_mart_customers(self):
        assert "mart_customers" in self.names, "Missing mart_customers"

    def test_has_mart_logistics(self):
        assert "mart_logistics" in self.names, "Missing mart_logistics"


# ── Test: sources.yml defines olist tables ──────────────────────────

class TestSourcesYml:
    """Verify sources.yml has all required source definitions."""

    sources_file = DBT_MODELS_DIR / "sources" / "sources.yml"

    def test_sources_yml_exists(self):
        assert self.sources_file.exists(), "dbt/models/sources/sources.yml is missing"

    def test_sources_has_olist(self):
        content = self.sources_file.read_text(encoding="utf-8")
        assert "olist_raw" in content, "sources.yml should define olist_raw source"

    def test_sources_has_crypto(self):
        content = self.sources_file.read_text(encoding="utf-8")
        assert "crypto_raw" in content, "sources.yml should define crypto_raw source"

    def test_sources_has_economic(self):
        content = self.sources_file.read_text(encoding="utf-8")
        assert "economic_raw" in content or "us_economic_raw" in content, (
            "sources.yml should define economic source"
        )
