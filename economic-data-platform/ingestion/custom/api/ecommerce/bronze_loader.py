"""Bronze layer loader — reads Parquet from MinIO and inserts into
PostgreSQL bronze tables.

Supports both Olist and MSSQL data sources.

Usage:
    loader = BronzeLoader(pg_conn, minio_client)
    result = loader.load_olist_table("orders")
    results = loader.load_all_olist()
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

import pandas as pd

from ingestion.custom.api.ecommerce.olist_schemas import OLIST_TABLES

logger = logging.getLogger(__name__)

# Mapping: olist table name → PostgreSQL bronze table name
OLIST_PG_TABLES: dict[str, str] = {
    "orders":               "bronze.olist_orders",
    "order_items":          "bronze.olist_order_items",
    "customers":            "bronze.olist_customers",
    "products":             "bronze.olist_products",
    "sellers":              "bronze.olist_sellers",
    "payments":             "bronze.olist_payments",
    "reviews":              "bronze.olist_reviews",
    "geolocation":          "bronze.olist_geolocation",
    "category_translation": "bronze.olist_category_translation",
}

# Columns to INSERT per table (excluding id and ingested_at which are auto)
OLIST_COLUMNS: dict[str, list[str]] = {
    "orders": [
        "source_file", "order_id", "customer_id", "order_status",
        "order_purchase_timestamp", "order_approved_at",
        "order_delivered_carrier_date", "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "order_items": [
        "source_file", "order_id", "order_item_id", "product_id",
        "seller_id", "shipping_limit_date", "price", "freight_value",
    ],
    "customers": [
        "source_file", "customer_id", "customer_unique_id",
        "customer_zip_code_prefix", "customer_city", "customer_state",
    ],
    "products": [
        "source_file", "product_id", "product_category_name",
        "product_name_lenght", "product_description_lenght",
        "product_photos_qty", "product_weight_g",
        "product_length_cm", "product_height_cm", "product_width_cm",
    ],
    "sellers": [
        "source_file", "seller_id", "seller_zip_code_prefix",
        "seller_city", "seller_state",
    ],
    "payments": [
        "source_file", "order_id", "payment_sequential",
        "payment_type", "payment_installments", "payment_value",
    ],
    "reviews": [
        "source_file", "review_id", "order_id", "review_score",
        "review_comment_title", "review_comment_message",
        "review_creation_date", "review_answer_timestamp",
    ],
    "geolocation": [
        "source_file", "geolocation_zip_code_prefix",
        "geolocation_lat", "geolocation_lng",
        "geolocation_city", "geolocation_state",
    ],
    "category_translation": [
        "source_file", "product_category_name",
        "product_category_name_english",
    ],
}


class BronzeLoader:
    """Load data from MinIO Parquet into PostgreSQL bronze tables."""

    def __init__(self, pg_conn, minio_client) -> None:
        """
        Args:
            pg_conn: psycopg2 connection (or any DB-API 2.0 connection)
            minio_client: MinIOClient instance
        """
        self.pg = pg_conn
        self.minio = minio_client

    # ------------------------------------------------------------------
    # Olist loading
    # ------------------------------------------------------------------

    def load_olist_table(
        self,
        table_name: str,
        partition_date: Optional[str] = None,
    ) -> dict:
        """Load a single Olist table from MinIO into PostgreSQL bronze.

        Reads: minio://bronze/olist/{table_name}/{date}.parquet
        Writes: bronze.olist_{table_name}
        """
        if table_name not in OLIST_PG_TABLES:
            raise ValueError(f"Unknown Olist table: {table_name}")

        if partition_date is None:
            # Find the latest partition
            objects = self.minio.list_objects("bronze", prefix=f"olist/{table_name}/")
            if not objects:
                return {"table": table_name, "error": "no_parquet_found", "rows": 0}
            # Use the most recent file
            latest = sorted(objects)[-1]
            object_key = latest
        else:
            object_key = f"olist/{table_name}/{partition_date}.parquet"

        started = datetime.now(timezone.utc)
        logger.info("Loading %s from minio://bronze/%s", table_name, object_key)

        # Read from MinIO
        df = self.minio.read_parquet("bronze", object_key)

        if df.empty:
            return {"table": table_name, "rows": 0, "skipped": True}

        # Add source_file column
        df["source_file"] = object_key

        # Insert into PostgreSQL
        pg_table = OLIST_PG_TABLES[table_name]
        columns = OLIST_COLUMNS[table_name]
        rows_inserted = self._insert_dataframe(df, pg_table, columns)

        finished = datetime.now(timezone.utc)

        return {
            "table": table_name,
            "pg_table": pg_table,
            "source": f"bronze/{object_key}",
            "rows": rows_inserted,
            "duration_seconds": (finished - started).total_seconds(),
        }

    def load_all_olist(
        self,
        partition_date: Optional[str] = None,
        skip_tables: Optional[list[str]] = None,
    ) -> dict[str, dict]:
        """Load all Olist tables from MinIO into PostgreSQL bronze."""
        skip = set(skip_tables or [])
        results: dict[str, dict] = {}

        for table_name in OLIST_PG_TABLES:
            if table_name in skip:
                logger.info("Skipping %s", table_name)
                continue
            try:
                results[table_name] = self.load_olist_table(table_name, partition_date)
            except Exception:
                logger.exception("Failed to load %s", table_name)
                results[table_name] = {"table": table_name, "error": "load_failed"}

        total = sum(r.get("rows", 0) for r in results.values())
        logger.info("Olist bronze load complete: %d tables, %d total rows", len(results), total)
        return results

    # ------------------------------------------------------------------
    # MSSQL loading (JSONB approach)
    # ------------------------------------------------------------------

    def load_mssql_table(
        self,
        schema: str,
        table_name: str,
        partition_date: Optional[str] = None,
    ) -> dict:
        """Load a single MSSQL table from MinIO Parquet into bronze.mssql_raw.

        Each row stored as JSONB for schema flexibility.
        """
        safe_name = table_name.lower().replace(" ", "_").replace("-", "_")

        if partition_date is None:
            objects = self.minio.list_objects("bronze", prefix=f"mssql/{safe_name}/")
            if not objects:
                return {"table": f"{schema}.{table_name}", "error": "no_parquet_found", "rows": 0}
            object_key = sorted(objects)[-1]
        else:
            object_key = f"mssql/{safe_name}/{partition_date}.parquet"

        started = datetime.now(timezone.utc)
        logger.info("Loading %s.%s from minio://bronze/%s", schema, table_name, object_key)

        df = self.minio.read_parquet("bronze", object_key)

        if df.empty:
            return {"table": f"{schema}.{table_name}", "rows": 0, "skipped": True}

        # Insert as JSONB rows into bronze.mssql_raw
        cursor = self.pg.cursor()
        insert_sql = """
            INSERT INTO bronze.mssql_raw (source_schema, source_table, source_row_id, record_data)
            VALUES (%s, %s, %s, %s)
        """

        rows_inserted = 0
        for _, row in df.iterrows():
            row_dict = {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}
            # Try to extract a row ID from common PK column names
            row_id = str(
                row_dict.get("id")
                or row_dict.get("ID")
                or row_dict.get(f"{table_name}_id")
                or rows_inserted
            )
            cursor.execute(insert_sql, (
                schema,
                table_name,
                row_id,
                json.dumps(row_dict, default=str),
            ))
            rows_inserted += 1

        self.pg.commit()
        cursor.close()

        # Log ingestion
        self._log_mssql_ingestion(
            schema, table_name, rows_inserted,
            minio_path=f"bronze/{object_key}",
            status="success",
        )

        finished = datetime.now(timezone.utc)

        return {
            "table": f"{schema}.{table_name}",
            "source": f"bronze/{object_key}",
            "rows": rows_inserted,
            "duration_seconds": (finished - started).total_seconds(),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _insert_dataframe(
        self,
        df: pd.DataFrame,
        pg_table: str,
        columns: list[str],
    ) -> int:
        """Batch insert DataFrame rows into PostgreSQL table."""
        cursor = self.pg.cursor()

        # Build INSERT statement
        col_list = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        insert_sql = f"INSERT INTO {pg_table} ({col_list}) VALUES ({placeholders})"

        rows_inserted = 0
        batch: list[tuple] = []
        batch_size = 1000

        for _, row in df.iterrows():
            values = []
            for col in columns:
                val = row.get(col)
                if pd.isna(val) if not isinstance(val, str) else False:
                    values.append(None)
                elif val == "":
                    values.append(None)
                else:
                    values.append(val)
            batch.append(tuple(values))

            if len(batch) >= batch_size:
                cursor.executemany(insert_sql, batch)
                rows_inserted += len(batch)
                batch = []

        # Flush remaining
        if batch:
            cursor.executemany(insert_sql, batch)
            rows_inserted += len(batch)

        self.pg.commit()
        cursor.close()

        logger.info("Inserted %d rows into %s", rows_inserted, pg_table)
        return rows_inserted

    def _log_mssql_ingestion(
        self,
        schema: str,
        table: str,
        row_count: int,
        minio_path: str = "",
        status: str = "success",
        error_message: str = "",
    ) -> None:
        """Write an entry to bronze.mssql_ingestion_log."""
        cursor = self.pg.cursor()
        cursor.execute(
            """
            INSERT INTO bronze.mssql_ingestion_log
                (source_schema, source_table, row_count, minio_path, status, error_message, finished_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """,
            (schema, table, row_count, minio_path, status, error_message),
        )
        self.pg.commit()
        cursor.close()
