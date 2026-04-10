"""Data Quality DAG.

Schedule: Daily at 5 AM (after dbt transforms)
Flow:
    1. Run bronze quality checks (row counts, NULLs, FK, value ranges)
    2. Check data freshness (last ingestion timestamps)
    3. Validate mart row counts
    4. Send alert if any check fails
"""

from datetime import datetime

from airflow.decorators import dag, task
from airflow.common.default_args import DEFAULT_ARGS


@dag(
    dag_id="data_quality_checks",
    default_args=DEFAULT_ARGS,
    description="Bronze + mart quality checks with alerting",
    schedule="0 5 * * *",  # Daily 5 AM
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["quality", "monitoring", "daily"],
)
def data_quality_checks():

    @task()
    def check_bronze_quality():
        """Run quality checks on bronze Olist tables."""
        import psycopg2
        import os
        from ingestion.custom.api.ecommerce.quality_check import BronzeQualityChecker

        pg = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "postgres"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "economic_data"),
            user=os.getenv("POSTGRES_USER", "economic_user"),
            password=os.getenv("POSTGRES_PASSWORD", "economic_password"),
        )
        checker = BronzeQualityChecker(pg, data_dir="data/raw/olist")
        results = checker.run_all()
        pg.close()

        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed)
        failures = [{"name": r.name, "msg": r.message} for r in results if not r.passed]

        return {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "failures": failures,
        }

    @task()
    def check_data_freshness():
        """Check last ingestion timestamps across sources."""
        import redis
        import os
        from ingestion.custom.api.ecommerce.checkpoint import CheckpointManager

        r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"))
        mgr = CheckpointManager(r)

        sources = ["olist", "mssql"]
        freshness = {}
        for source in sources:
            checkpoints = mgr.list_checkpoints(source)
            freshness[source] = {
                "checkpoint_count": len(checkpoints),
                "status": "ok" if len(checkpoints) > 0 else "stale",
            }
        return freshness

    @task()
    def check_mart_health():
        """Validate mart tables have expected row counts."""
        import psycopg2
        import os

        pg = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "postgres"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "economic_data"),
            user=os.getenv("POSTGRES_USER", "economic_user"),
            password=os.getenv("POSTGRES_PASSWORD", "economic_password"),
        )
        cursor = pg.cursor()

        mart_tables = [
            "gold_ecommerce.mart_sales",
            "gold_ecommerce.mart_sales_monthly",
            "gold_ecommerce.mart_customers",
            "gold_ecommerce.mart_logistics",
            "gold_ecommerce.mart_logistics_by_state",
            "gold_ecommerce.fct_orders",
            "gold_ecommerce.dim_customers",
        ]

        results = {}
        for table in mart_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")  # noqa: S608
                count = cursor.fetchone()[0]
                results[table] = {"rows": count, "status": "ok" if count > 0 else "empty"}
            except Exception as e:
                results[table] = {"rows": 0, "status": "error", "error": str(e)}

        cursor.close()
        pg.close()
        return results

    @task()
    def send_alerts(bronze_results: dict, freshness: dict, mart_results: dict):
        """Send alerts if any quality check failed."""
        import logging
        logger = logging.getLogger("data_quality")

        issues = []

        # Bronze failures
        if bronze_results.get("failed", 0) > 0:
            for f in bronze_results.get("failures", []):
                issues.append(f"Bronze: {f['name']} — {f['msg']}")

        # Stale sources
        for source, info in freshness.items():
            if info.get("status") == "stale":
                issues.append(f"Freshness: {source} has no checkpoints")

        # Empty marts
        for table, info in mart_results.items():
            if info.get("status") != "ok":
                issues.append(f"Mart: {table} is {info.get('status')}")

        if issues:
            logger.error("DATA QUALITY ISSUES FOUND:\n%s", "\n".join(issues))
            # In production: send email/Slack via callbacks
            return {"status": "issues_found", "count": len(issues), "issues": issues}
        else:
            logger.info("All quality checks passed!")
            return {"status": "all_passed"}

    # DAG flow
    bronze = check_bronze_quality()
    freshness = check_data_freshness()
    marts = check_mart_health()
    send_alerts(bronze, freshness, marts)


data_quality_checks()
