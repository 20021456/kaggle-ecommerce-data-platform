"""Test SQL injection protection in the Trino query router."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.api.routers.query import _validate_sql, _ensure_limit


class TestSQLValidation:
    """Verify SQL injection protection and read-only enforcement."""

    def test_select_allowed(self):
        result = _validate_sql("SELECT * FROM my_table")
        assert result.strip().upper().startswith("SELECT")

    def test_show_allowed(self):
        result = _validate_sql("SHOW TABLES")
        assert "SHOW" in result.upper()

    def test_describe_allowed(self):
        result = _validate_sql("DESCRIBE my_table")
        assert "DESCRIBE" in result.upper()

    def test_with_cte_allowed(self):
        result = _validate_sql("WITH cte AS (SELECT 1) SELECT * FROM cte")
        assert result.strip().upper().startswith("WITH")

    def test_insert_blocked(self):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            _validate_sql("INSERT INTO t VALUES (1)")
        assert exc_info.value.status_code == 400

    def test_drop_blocked(self):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            _validate_sql("SELECT 1; DROP TABLE users")
        assert exc_info.value.status_code == 400

    def test_delete_blocked(self):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            _validate_sql("DELETE FROM orders")
        assert exc_info.value.status_code == 400

    def test_update_blocked(self):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            _validate_sql("UPDATE users SET name='x'")
        assert exc_info.value.status_code == 400

    def test_semicolon_blocked(self):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            _validate_sql("SELECT 1; SELECT 2")
        assert exc_info.value.status_code == 400

    def test_empty_blocked(self):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            _validate_sql("")
        assert exc_info.value.status_code == 400


class TestEnsureLimit:
    """Verify LIMIT is automatically appended."""

    def test_adds_limit_when_missing(self):
        result = _ensure_limit("SELECT * FROM t", 1000)
        assert "LIMIT" in result.upper()

    def test_respects_existing_limit(self):
        result = _ensure_limit("SELECT * FROM t LIMIT 5", 1000)
        # Should not add a second LIMIT
        assert result.upper().count("LIMIT") == 1

    def test_caps_at_max(self):
        result = _ensure_limit("SELECT * FROM t", 100)
        assert "LIMIT 100" in result.upper() or "LIMIT  100" in result.upper()
