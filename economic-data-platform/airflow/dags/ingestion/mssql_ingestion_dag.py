"""MSSQL Server Ingestion DAG.

Schedule: Daily at 2 AM
Flow:
    1. Connect to external MSSQL server
    2. Read tables in batches
    3. Convert to Parquet + upload to MinIO bronze
    4. Load into PostgreSQL bronze.mssql_raw (JSONB)
    5. Update Redis checkpoint
"""

from datetime import datetime

from airflow.decorators import dag, task
from common.default_args import DEFAULT_ARGS


@dag(
    dag_id="mssql_ingestion",
    default_args=DEFAULT_ARGS,
    description="MSSQL → Parquet → MinIO → PostgreSQL bronze",
    schedule="0 2 * * *",  # Daily 2 AM
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ingestion", "mssql", "daily"],
)
def mssql_ingestion():

    @task()
    def ingest_to_minio():
        """Read MSSQL tables, convert to Parquet, upload to MinIO."""
        import os
        from ingestion.custom.mssql_client import MSSQLClient
        from data_platform.io.minio_client import MinIOClient
        from ingestion.custom.api.ecommerce.mssql_to_minio import MSSQLToMinIOLoader

        mssql = MSSQLClient(
            host=os.getenv("MSSQL_HOST", "45.124.94.158"),
            port=int(os.getenv("MSSQL_PORT", "1433")),
            database=os.getenv("MSSQL_DATABASE", "xomdata_dataset"),
            user=os.getenv("MSSQL_USER"),
            password=os.getenv("MSSQL_PASSWORD"),
        )
        minio = MinIOClient(endpoint=os.getenv("MINIO_ENDPOINT", "minio:9000"))
        loader = MSSQLToMinIOLoader(mssql, minio)
        results = loader.ingest_all()
        return results

    @task()
    def load_to_postgres(ingest_results: dict):
        """Load MSSQL Parquet from MinIO into PostgreSQL bronze.mssql_raw."""
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

        results = {}
        for key, info in ingest_results.items():
            if info.get("error"):
                continue
            parts = key.split(".", 1)
            if len(parts) == 2:
                schema, table = parts
                results[key] = loader.load_mssql_table(schema, table)
        pg.close()
        return results

    @task()
    def update_checkpoint(load_results: dict):
        """Update Redis checkpoint."""
        import redis
        import os
        from datetime import datetime as dt, timezone
        from ingestion.custom.api.ecommerce.checkpoint import CheckpointManager

        r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"))
        mgr = CheckpointManager(r)
        today = dt.now(timezone.utc).strftime("%Y-%m-%d")

        for table, result in load_results.items():
            if result.get("rows", 0) > 0:
                mgr.mark_done("mssql", table, today, row_count=result["rows"])
        return {"date": today, "tables": len(load_results)}

    ingested = ingest_to_minio()
    loaded = load_to_postgres(ingested)
    update_checkpoint(loaded)


mssql_ingestion()
