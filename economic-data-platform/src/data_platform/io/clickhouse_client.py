"""ClickHouse client for analytics queries and data insertion.

Usage:
    from data_platform.io.clickhouse_client import ClickHouseClient

    ch = ClickHouseClient()
    ch.execute("INSERT INTO bronze.fear_greed_index ...", data)
    df = ch.query_df("SELECT * FROM gold.fct_crypto_daily WHERE coin_id = 'bitcoin'")
"""

from __future__ import annotations

import logging
from typing import Any

import clickhouse_connect

logger = logging.getLogger(__name__)


class ClickHouseClient:
    """Thin wrapper around clickhouse-connect for the analytics pipeline."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        username: str | None = None,
        password: str | None = None,
        database: str = "default",
    ) -> None:
        import os

        self._host = host or os.environ.get("CLICKHOUSE_HOST", "localhost")
        self._port = port or int(os.environ.get("CLICKHOUSE_PORT", "8123"))
        self._username = username or os.environ.get("CLICKHOUSE_USER", "default")
        self._password = password or os.environ.get("CLICKHOUSE_PASSWORD", "")
        self._database = database
        self._client: clickhouse_connect.driver.Client | None = None

    @property
    def client(self) -> clickhouse_connect.driver.Client:
        if self._client is None:
            self._client = clickhouse_connect.get_client(
                host=self._host,
                port=self._port,
                username=self._username,
                password=self._password,
                database=self._database,
            )
        return self._client

    # ── Query ─────────────────────────────────────────────────────────────

    def execute(self, query: str, parameters: dict[str, Any] | None = None) -> Any:
        """Execute a query (DDL, INSERT, etc.)."""
        result = self.client.command(query, parameters=parameters)
        logger.debug("Executed: %s", query[:120])
        return result

    def query(self, query: str, parameters: dict[str, Any] | None = None) -> list[tuple]:
        """Execute a SELECT and return rows as list of tuples."""
        result = self.client.query(query, parameters=parameters)
        return result.result_rows

    def query_df(self, query: str, parameters: dict[str, Any] | None = None):
        """Execute a SELECT and return a pandas DataFrame."""
        return self.client.query_df(query, parameters=parameters)

    # ── Bulk insert ───────────────────────────────────────────────────────

    def insert_df(self, table: str, df, database: str | None = None) -> None:
        """Insert a pandas DataFrame into a ClickHouse table."""
        db = database or self._database
        full_table = f"{db}.{table}" if db != "default" else table
        self.client.insert_df(full_table, df)
        logger.info("Inserted %d rows into %s", len(df), full_table)

    def insert_rows(self, table: str, rows: list[list], column_names: list[str], database: str | None = None) -> None:
        """Insert rows (list of lists) into a ClickHouse table."""
        db = database or self._database
        full_table = f"{db}.{table}" if db != "default" else table
        self.client.insert(full_table, rows, column_names=column_names)
        logger.info("Inserted %d rows into %s", len(rows), full_table)

    # ── Schema helpers ────────────────────────────────────────────────────

    def run_sql_file(self, filepath: str) -> None:
        """Execute a SQL file with multiple statements (split by ';')."""
        from pathlib import Path

        content = Path(filepath).read_text(encoding="utf-8")
        statements = [s.strip() for s in content.split(";") if s.strip() and not s.strip().startswith("--")]
        for stmt in statements:
            try:
                self.execute(stmt)
            except Exception as e:
                logger.error("Failed: %s\nError: %s", stmt[:200], e)
                raise

    def table_exists(self, table: str, database: str = "default") -> bool:
        result = self.query(f"EXISTS TABLE {database}.{table}")
        return bool(result and result[0][0])

    def get_row_count(self, table: str, database: str = "default") -> int:
        result = self.query(f"SELECT count() FROM {database}.{table}")
        return result[0][0] if result else 0

    # ── Cleanup ───────────────────────────────────────────────────────────

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None
