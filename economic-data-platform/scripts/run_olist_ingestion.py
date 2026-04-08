#!/usr/bin/env python3
"""Run the full Olist ingestion pipeline.

Steps:
    1. Read CSV files from data/raw/olist/
    2. Validate with Pydantic schemas
    3. Convert to Parquet and upload to MinIO bronze
    4. Load from MinIO into PostgreSQL bronze tables
    5. Run data quality checks

Usage:
    python scripts/run_olist_ingestion.py
    python scripts/run_olist_ingestion.py --skip-upload    # local only, no MinIO
    python scripts/run_olist_ingestion.py --skip-pg        # MinIO only, no PG
    python scripts/run_olist_ingestion.py --quality-only   # just run quality checks
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("olist_ingestion")


def get_minio_client():
    from data_platform.io.minio_client import MinIOClient
    return MinIOClient(
        endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
        access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
    )


def get_pg_connection():
    import psycopg2
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "economic_data"),
        user=os.getenv("POSTGRES_USER", "economic_user"),
        password=os.getenv("POSTGRES_PASSWORD", "economic_password"),
    )


def main():
    parser = argparse.ArgumentParser(description="Olist E-Commerce ingestion pipeline")
    parser.add_argument("--data-dir", default="data/raw/olist", help="Path to Olist CSV files")
    parser.add_argument("--skip-upload", action="store_true", help="Skip MinIO upload")
    parser.add_argument("--skip-pg", action="store_true", help="Skip PostgreSQL load")
    parser.add_argument("--skip-validate", action="store_true", help="Skip Pydantic validation")
    parser.add_argument("--quality-only", action="store_true", help="Only run quality checks")
    parser.add_argument("--tables", nargs="*", help="Specific tables to ingest (default: all)")
    args = parser.parse_args()

    started = datetime.now(timezone.utc)
    logger.info("=" * 70)
    logger.info("  Olist Ingestion Pipeline")
    logger.info("=" * 70)
    logger.info("  Data dir:   %s", args.data_dir)
    logger.info("  Upload:     %s", "yes" if not args.skip_upload else "skip")
    logger.info("  PG load:    %s", "yes" if not args.skip_pg else "skip")
    logger.info("  Validate:   %s", "yes" if not args.skip_validate else "skip")
    logger.info("=" * 70)

    # Initialize clients
    minio_client = None if args.skip_upload else get_minio_client()
    pg_conn = None if (args.skip_pg and not args.quality_only) else get_pg_connection()

    if args.quality_only:
        logger.info("Running quality checks only...")
        from ingestion.custom.api.ecommerce.quality_check import BronzeQualityChecker
        checker = BronzeQualityChecker(pg_conn, minio_client, data_dir=args.data_dir)
        results = checker.run_all()
        checker.print_report(results)
        pg_conn.close()
        return

    # ── Step 1+2+3: CSV → Validate → Parquet → MinIO ──────────────────
    from ingestion.custom.api.ecommerce.olist_loader import OlistLoader

    loader = OlistLoader(data_dir=args.data_dir, minio_client=minio_client)
    available = loader.list_tables()
    logger.info("Found %d tables: %s", len(available), available)

    tables_to_process = args.tables or available
    skip_tables = [t for t in available if t not in tables_to_process]

    ingest_results = loader.ingest_all(
        validate=not args.skip_validate,
        upload=not args.skip_upload,
        skip_tables=skip_tables,
    )

    logger.info("\n--- Ingestion Results ---")
    for table, result in ingest_results.items():
        rows = result.get("valid_rows", result.get("raw_rows", "?"))
        errs = result.get("error_count", 0)
        size = result.get("parquet_size_bytes", 0)
        path = result.get("minio_path", "n/a")
        logger.info(
            "  %s: %s rows, %d errors, %.1f KB → %s",
            table, rows, errs, size / 1024, path,
        )

    # ── Step 4: MinIO → PostgreSQL bronze ──────────────────────────────
    if not args.skip_pg and pg_conn is not None and minio_client is not None:
        from ingestion.custom.api.ecommerce.bronze_loader import BronzeLoader

        logger.info("\n--- Loading into PostgreSQL bronze ---")
        bronze = BronzeLoader(pg_conn, minio_client)
        load_results = bronze.load_all_olist(skip_tables=skip_tables)

        for table, result in load_results.items():
            rows = result.get("rows", 0)
            dur = result.get("duration_seconds", 0)
            logger.info("  %s: %d rows loaded (%.1fs)", table, rows, dur)

    # ── Step 5: Quality checks ─────────────────────────────────────────
    if pg_conn is not None:
        from ingestion.custom.api.ecommerce.quality_check import BronzeQualityChecker

        logger.info("\n--- Running quality checks ---")
        checker = BronzeQualityChecker(pg_conn, minio_client, data_dir=args.data_dir)
        qc_results = checker.run_all()
        checker.print_report(qc_results)

    # ── Summary ────────────────────────────────────────────────────────
    finished = datetime.now(timezone.utc)
    total_rows = sum(r.get("valid_rows", 0) for r in ingest_results.values())
    logger.info("=" * 70)
    logger.info("  Pipeline complete in %.1f seconds", (finished - started).total_seconds())
    logger.info("  Total rows processed: %d", total_rows)
    logger.info("=" * 70)

    if pg_conn:
        pg_conn.close()


if __name__ == "__main__":
    main()
