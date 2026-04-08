"""MSSQL → MinIO Parquet loader.

Reads tables from the external MSSQL server, converts to Parquet, and
uploads to MinIO bronze bucket.

Usage:
    loader = MSSQLToMinIOLoader(mssql_client, minio_client)
    results = loader.ingest_all()
"""

from __future__ import annotations

import io
import logging
from datetime import datetime, timezone
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


class MSSQLToMinIOLoader:
    """Read MSSQL tables → Parquet → MinIO bronze bucket."""

    def __init__(
        self,
        mssql_client: object,
        minio_client: object,
    ) -> None:
        self.mssql = mssql_client
        self.minio = minio_client

    def list_tables(self) -> list[tuple[str, str, int]]:
        """List available MSSQL tables.

        Returns list of (schema, table_name, row_count).
        """
        return self.mssql.list_tables()

    def ingest_table(
        self,
        schema: str,
        table_name: str,
        batch_size: int = 50_000,
    ) -> dict:
        """Ingest a single MSSQL table to MinIO.

        1. Read from MSSQL (batched for large tables)
        2. Convert to Parquet
        3. Upload to MinIO bronze/mssql/{table}/YYYY-MM-DD.parquet
        """
        started = datetime.now(timezone.utc)
        partition_date = started.strftime("%Y-%m-%d")
        safe_name = table_name.lower().replace(" ", "_").replace("-", "_")

        logger.info("Reading [%s].[%s] from MSSQL", schema, table_name)

        try:
            df = self.mssql.read_table(schema=schema, table=table_name)
        except Exception:
            logger.exception("Failed to read [%s].[%s]", schema, table_name)
            return {
                "table": f"{schema}.{table_name}",
                "error": "read_failed",
            }

        if df.empty:
            logger.warning("[%s].[%s] is empty, skipping", schema, table_name)
            return {
                "table": f"{schema}.{table_name}",
                "raw_rows": 0,
                "skipped": True,
            }

        # Convert to Parquet
        buf = io.BytesIO()
        df.to_parquet(buf, engine="pyarrow", index=False)
        parquet_bytes = buf.getvalue()

        # Upload to MinIO
        object_path = f"mssql/{safe_name}/{partition_date}.parquet"
        bucket = "bronze"

        logger.info(
            "Uploading %s to minio://%s/%s (%d rows, %d bytes)",
            safe_name, bucket, object_path, len(df), len(parquet_bytes),
        )

        self.minio.upload_bytes(
            bucket=bucket,
            key=object_path,
            data=parquet_bytes,
            content_type="application/octet-stream",
        )

        finished = datetime.now(timezone.utc)

        return {
            "table": f"{schema}.{table_name}",
            "raw_rows": len(df),
            "parquet_size_bytes": len(parquet_bytes),
            "minio_path": f"{bucket}/{object_path}",
            "duration_seconds": (finished - started).total_seconds(),
        }

    def ingest_all(
        self,
        skip_tables: Optional[list[str]] = None,
    ) -> dict[str, dict]:
        """Ingest all MSSQL tables to MinIO.

        Returns dict of table_key → summary.
        """
        skip = set(skip_tables or [])
        results: dict[str, dict] = {}

        tables = self.list_tables()
        logger.info("Found %d MSSQL tables", len(tables))

        for schema, table_name, row_count in tables:
            key = f"{schema}.{table_name}"
            if key in skip or table_name in skip:
                logger.info("Skipping %s", key)
                continue

            try:
                results[key] = self.ingest_table(schema, table_name)
            except Exception:
                logger.exception("Failed to ingest %s", key)
                results[key] = {"table": key, "error": "ingestion_failed"}

        total_rows = sum(r.get("raw_rows", 0) for r in results.values())
        logger.info(
            "MSSQL ingestion complete: %d tables, %d total rows",
            len(results), total_rows,
        )
        return results
