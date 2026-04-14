"""CLI entry-point for Olist CSV ingestion.

Invoked by Makefile:
    make ingest-olist   →  python -m ingestion.custom.api.ecommerce.ingest_csv

Workflow:
    1. Try to download from Kaggle (skip if already present)
    2. Read CSV files from data/raw/olist/
    3. Validate rows with Pydantic schemas
    4. Convert to Parquet and upload to MinIO bronze/olist/
    5. Load into PostgreSQL bronze.olist_* tables
    6. Update Redis checkpoints
"""

from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Run the full Olist ingestion pipeline."""
    start = time.monotonic()

    # ── Step 1: Ensure CSV files are present ──────────────────────────
    data_dir = Path("data/raw/olist")

    if not data_dir.exists() or len(list(data_dir.glob("*.csv"))) < 7:
        logger.info("CSV files not found — attempting Kaggle download...")
        try:
            from ingestion.custom.api.ecommerce.kaggle_client import KaggleClient

            client = KaggleClient(data_dir=str(data_dir))
            client.download_dataset()
        except Exception as exc:
            # Fallback: try extracting from olist_dataset.zip
            zip_path = Path("olist_dataset.zip")
            if not zip_path.exists():
                zip_path = Path("economic-data-platform/olist_dataset.zip")
            if zip_path.exists():
                logger.info("Extracting from %s...", zip_path)
                import zipfile

                data_dir.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(zip_path, "r") as zf:
                    zf.extractall(data_dir)
            else:
                logger.error(
                    "Cannot obtain Olist data: %s. "
                    "Download from Kaggle or place olist_dataset.zip in project root.",
                    exc,
                )
                sys.exit(1)

    csv_count = len(list(data_dir.glob("*.csv")))
    logger.info("Found %d CSV files in %s", csv_count, data_dir)

    # ── Step 2: Load, validate, and upload to MinIO ───────────────────
    try:
        from ingestion.custom.api.ecommerce.olist_loader import OlistLoader

        # Try to get MinIO client
        minio_client = None
        try:
            from src.data_platform.io.minio_client import MinIOClient

            minio_client = MinIOClient()
            logger.info("MinIO client initialized")
        except Exception as exc:
            logger.warning("MinIO unavailable, skipping data lake upload: %s", exc)

        loader = OlistLoader(data_dir=str(data_dir), minio_client=minio_client)
        results = loader.ingest_all()

        logger.info("MinIO ingestion results:")
        total_rows = 0
        for table, count in results.items():
            logger.info("  %-30s → %d rows", table, count)
            total_rows += count

    except Exception as exc:
        logger.error("Ingestion to MinIO failed: %s", exc)
        results = {}
        total_rows = 0

    # ── Step 3: Load from MinIO to PostgreSQL bronze ──────────────────
    try:
        from ingestion.custom.api.ecommerce.bronze_loader import BronzeLoader
        import psycopg2

        pg_url = os.getenv(
            "DATABASE_URL",
            "postgresql://economic_user:economic_password@localhost:5432/economic_data",
        )
        conn = psycopg2.connect(pg_url)
        pg_loader = BronzeLoader(pg_conn=conn, minio_client=minio_client)
        pg_results = pg_loader.load_all_olist()
        conn.close()

        logger.info("PostgreSQL bronze load results:")
        for table, info in pg_results.items():
            logger.info("  %-30s → %s", table, info)
    except Exception as exc:
        logger.warning("PostgreSQL bronze load skipped: %s", exc)

    # ── Step 4: Update checkpoint ─────────────────────────────────────
    try:
        from ingestion.custom.api.ecommerce.checkpoint import CheckpointManager

        ckpt = CheckpointManager()
        for table, count in results.items():
            ckpt.update(source="olist", table=table, row_count=count)
        logger.info("Checkpoints updated for %d tables", len(results))
    except Exception as exc:
        logger.debug("Checkpoint update skipped: %s", exc)

    elapsed = time.monotonic() - start
    logger.info(
        "Olist ingestion complete: %d tables, %d total rows in %.1fs",
        len(results),
        total_rows,
        elapsed,
    )


if __name__ == "__main__":
    main()
