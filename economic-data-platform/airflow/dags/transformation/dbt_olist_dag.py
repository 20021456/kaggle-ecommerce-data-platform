"""dbt Olist Transformation DAG.

Schedule: Daily at 4 AM (after ingestion DAGs)
Flow:
    1. dbt run — staging models (tag: ecommerce, staging)
    2. dbt run — intermediate models (tag: ecommerce, intermediate)
    3. dbt run — mart models (tag: ecommerce, mart)
    4. dbt test — all ecommerce models
"""

from datetime import datetime

from airflow.decorators import dag, task
from common.default_args import DEFAULT_ARGS

DBT_DIR = "/opt/airflow/dbt"


@dag(
    dag_id="dbt_olist_transforms",
    default_args=DEFAULT_ARGS,
    description="dbt: Olist staging → intermediate → marts + tests",
    schedule="0 4 * * *",  # Daily 4 AM
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["transformation", "dbt", "ecommerce", "daily"],
)
def dbt_olist_transforms():

    @task()
    def dbt_run_staging():
        """Run dbt staging models for ecommerce."""
        import subprocess
        result = subprocess.run(
            ["dbt", "run",
             "--select", "tag:ecommerce,tag:staging",
             "--profiles-dir", DBT_DIR,
             "--project-dir", DBT_DIR],
            capture_output=True, text=True, timeout=1800,
        )
        if result.returncode != 0:
            raise RuntimeError(f"dbt staging failed:\n{result.stderr}")
        return {"stage": "staging", "output": result.stdout[-500:]}

    @task()
    def dbt_run_intermediate():
        """Run dbt intermediate models."""
        import subprocess
        result = subprocess.run(
            ["dbt", "run",
             "--select", "tag:ecommerce,tag:intermediate",
             "--profiles-dir", DBT_DIR,
             "--project-dir", DBT_DIR],
            capture_output=True, text=True, timeout=1800,
        )
        if result.returncode != 0:
            raise RuntimeError(f"dbt intermediate failed:\n{result.stderr}")
        return {"stage": "intermediate", "output": result.stdout[-500:]}

    @task()
    def dbt_run_marts():
        """Run dbt mart models."""
        import subprocess
        result = subprocess.run(
            ["dbt", "run",
             "--select", "tag:ecommerce,tag:mart",
             "--profiles-dir", DBT_DIR,
             "--project-dir", DBT_DIR],
            capture_output=True, text=True, timeout=3600,
        )
        if result.returncode != 0:
            raise RuntimeError(f"dbt marts failed:\n{result.stderr}")
        return {"stage": "marts", "output": result.stdout[-500:]}

    @task()
    def dbt_test():
        """Run dbt tests for all ecommerce models."""
        import subprocess
        result = subprocess.run(
            ["dbt", "test",
             "--select", "tag:ecommerce",
             "--profiles-dir", DBT_DIR,
             "--project-dir", DBT_DIR],
            capture_output=True, text=True, timeout=1800,
        )
        if result.returncode != 0:
            raise RuntimeError(f"dbt test failed:\n{result.stderr}")
        return {"stage": "test", "output": result.stdout[-500:]}

    # Sequential: staging → intermediate → marts → test
    stg = dbt_run_staging()
    inter = dbt_run_intermediate()
    marts = dbt_run_marts()
    tests = dbt_test()

    stg >> inter >> marts >> tests


dbt_olist_transforms()
