"""Olist dataset loader — reads local CSVs, validates, converts to Parquet,
uploads to MinIO bronze bucket.

Usage:
    loader = OlistLoader(data_dir="data/raw/olist")
    results = loader.ingest_all()
    # results = {"orders": 99441, "order_items": 112650, ...}
"""

from __future__ import annotations

import io
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd
from pydantic import ValidationError

from ingestion.custom.api.ecommerce.olist_schemas import OLIST_TABLES

logger = logging.getLogger(__name__)


class OlistLoader:
    """Load Olist CSV files, validate, convert to Parquet, upload to MinIO."""

    def __init__(
        self,
        data_dir: str = "data/raw/olist",
        minio_client: Optional[object] = None,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.minio_client = minio_client

        if not self.data_dir.exists():
            raise FileNotFoundError(
                f"Olist data directory not found: {self.data_dir}. "
                "Extract olist_dataset.zip to data/raw/olist/ first."
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_tables(self) -> list[str]:
        """Return available table names based on CSV files found on disk."""
        available = []
        for table_name, (csv_file, _) in OLIST_TABLES.items():
            if (self.data_dir / csv_file).exists():
                available.append(table_name)
        return available

    def read_table(self, table_name: str) -> pd.DataFrame:
        """Read a single Olist CSV table into a DataFrame."""
        if table_name not in OLIST_TABLES:
            raise ValueError(
                f"Unknown table '{table_name}'. "
                f"Valid tables: {list(OLIST_TABLES.keys())}"
            )

        csv_file, _ = OLIST_TABLES[table_name]
        csv_path = self.data_dir / csv_file

        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        logger.info("Reading %s from %s", table_name, csv_path)
        df = pd.read_csv(csv_path, dtype=str)  # read all as str first
        logger.info("Loaded %s: %d rows, %d columns", table_name, len(df), len(df.columns))
        return df

    def validate_table(self, table_name: str, df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
        """Validate DataFrame rows against Pydantic schema.

        Returns:
            (valid_df, errors) where errors is a list of
            {"row": int, "error": str} dicts.
        """
        _, schema_cls = OLIST_TABLES[table_name]
        errors: list[dict] = []
        valid_indices: list[int] = []

        for idx, row in df.iterrows():
            try:
                row_dict = row.to_dict()
                # Replace NaN / empty string with None
                row_dict = {
                    k: (None if pd.isna(v) or v == "" else v)
                    for k, v in row_dict.items()
                }
                schema_cls.model_validate(row_dict)
                valid_indices.append(idx)
            except (ValidationError, Exception) as exc:
                errors.append({"row": idx, "error": str(exc)})

        valid_df = df.loc[valid_indices].copy()
        if errors:
            logger.warning(
                "%s validation: %d valid, %d errors",
                table_name, len(valid_df), len(errors),
            )
        else:
            logger.info("%s validation: all %d rows valid", table_name, len(valid_df))

        return valid_df, errors

    def to_parquet_bytes(self, df: pd.DataFrame) -> bytes:
        """Convert DataFrame to Parquet bytes (in-memory)."""
        buf = io.BytesIO()
        df.to_parquet(buf, engine="pyarrow", index=False)
        return buf.getvalue()

    def upload_to_minio(
        self,
        table_name: str,
        parquet_bytes: bytes,
        partition_date: Optional[str] = None,
    ) -> str:
        """Upload Parquet bytes to MinIO bronze bucket.

        Returns the object path in MinIO.
        """
        if self.minio_client is None:
            raise RuntimeError("MinIO client not configured")

        if partition_date is None:
            partition_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        object_path = f"olist/{table_name}/{partition_date}.parquet"
        bucket = "bronze"

        logger.info(
            "Uploading %s to minio://%s/%s (%d bytes)",
            table_name, bucket, object_path, len(parquet_bytes),
        )

        self.minio_client.upload_bytes(
            bucket=bucket,
            key=object_path,
            data=parquet_bytes,
            content_type="application/octet-stream",
        )

        return f"{bucket}/{object_path}"

    def ingest_table(
        self,
        table_name: str,
        validate: bool = True,
        upload: bool = True,
    ) -> dict:
        """Full ingestion pipeline for a single table.

        1. Read CSV
        2. Validate (optional)
        3. Convert to Parquet
        4. Upload to MinIO (optional)

        Returns a summary dict.
        """
        started = datetime.now(timezone.utc)

        # Step 1: Read
        df = self.read_table(table_name)
        raw_rows = len(df)

        # Step 2: Validate
        errors = []
        if validate:
            df, errors = self.validate_table(table_name, df)

        # Step 3: Convert
        parquet_bytes = self.to_parquet_bytes(df)

        # Step 4: Upload
        minio_path = None
        if upload and self.minio_client is not None:
            minio_path = self.upload_to_minio(table_name, parquet_bytes)

        finished = datetime.now(timezone.utc)

        return {
            "table": table_name,
            "raw_rows": raw_rows,
            "valid_rows": len(df),
            "error_count": len(errors),
            "parquet_size_bytes": len(parquet_bytes),
            "minio_path": minio_path,
            "duration_seconds": (finished - started).total_seconds(),
        }

    def ingest_all(
        self,
        validate: bool = True,
        upload: bool = True,
        skip_tables: Optional[list[str]] = None,
    ) -> dict[str, dict]:
        """Ingest all Olist tables.

        Returns dict of table_name → summary.
        """
        skip = set(skip_tables or [])
        results: dict[str, dict] = {}

        for table_name in self.list_tables():
            if table_name in skip:
                logger.info("Skipping %s", table_name)
                continue
            try:
                results[table_name] = self.ingest_table(
                    table_name, validate=validate, upload=upload,
                )
            except Exception:
                logger.exception("Failed to ingest %s", table_name)
                results[table_name] = {"table": table_name, "error": "ingestion_failed"}

        # Summary
        total_rows = sum(r.get("valid_rows", 0) for r in results.values())
        total_errors = sum(r.get("error_count", 0) for r in results.values())
        logger.info(
            "Olist ingestion complete: %d tables, %d total rows, %d errors",
            len(results), total_rows, total_errors,
        )
        return results
