"""Olist E-Commerce Ingestion DAG.

Schedule: Weekly (dataset is static, re-ingest for pipeline freshness demo)
Flow:
    1. Read CSVs from data/raw/olist/
    2. Validate with Pydantic schemas
    3. Convert to Parquet + upload to MinIO bronze
    4. Load from MinIO into PostgreSQL bronze tables
    5. Update Redis checkpoint
"""

from datetime import datetime

from airflow.decorators import dag, task
from airflow.common.default_args import DEFAULT_ARGS


@dag(
    dag_id="olist_ingestion",
    default_args=DEFAULT_ARGS,
    description="Olist CSV → validate → Parquet → MinIO → PostgreSQL bronze",
    schedule="0 2 * * 0",  # Weekly, Sunday 2 AM
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ingestion", "ecommerce", "olist", "weekly"],
)
def olist_ingestion():

    @task()
    def ingest_to_minio():
        """Read CSVs, validate, convert to Parquet, upload to MinIO."""
        from ingestion.custom.api.ecommerce.olist_loader import OlistLoader
        from data_platform.io.minio_client import MinIOClient

        minio = MinIOClient()
        loader = OlistLoader(data_dir="data/raw/olist", minio_client=minio)
        results = loader.ingest_all(validate=True, upload=True)
        return results

    @task()
    def load_to_postgres(ingest_results: dict):
        """Load Parquet from MinIO into PostgreSQL bronze tables."""
        import psycopg2
        import os
        from data_platform.io.minio_client import MinIOClient
        from ingestion.custom.api.ecommerce.bronze_loader import BronzeLoader

        pg = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "postgres"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "economic_data"),
            user=os.getenv("POSTGRES_USER", "economic_user"),
            password=os.getenv("POSTGRES_PASSWORD", "economic_password"),
        )
        minio = MinIOClient(endpoint=os.getenv("MINIO_ENDPOINT", "minio:9000"))
        loader = BronzeLoader(pg, minio)
        results = loader.load_all_olist()
        pg.close()
        return results

    @task()
    def update_checkpoint(load_results: dict):
        """Update Redis checkpoint for each loaded table."""
        import redis
        import os
        from datetime import datetime, timezone
        from ingestion.custom.api.ecommerce.checkpoint import CheckpointManager

        r = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", "6379")),
        )
        mgr = CheckpointManager(r)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        for table, result in load_results.items():
            if result.get("rows", 0) > 0:
                mgr.mark_done(
                    source="olist",
                    table=table,
                    date=today,
                    row_count=result["rows"],
                    minio_path=result.get("source", ""),
                )
        return {"checkpoint_date": today, "tables": len(load_results)}

    # DAG flow
    ingested = ingest_to_minio()
    loaded = load_to_postgres(ingested)
    update_checkpoint(loaded)


olist_ingestion()
