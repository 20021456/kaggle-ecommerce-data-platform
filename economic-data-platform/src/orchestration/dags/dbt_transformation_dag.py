"""
dbt Transformation DAG
Orchestrates dbt model runs with proper dependency management
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.utils.task_group import TaskGroup

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': True,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=3),
}

dag = DAG(
    'dbt_transformation_pipeline',
    default_args=default_args,
    description='Run dbt transformations following medallion architecture',
    schedule_interval='0 */4 * * *',  # Every 4 hours
    catchup=False,
    max_active_runs=1,
    tags=['dbt', 'transformation', 'medallion'],
)

# DBT project path
DBT_PROJECT_PATH = '/opt/airflow/dbt/economic_data_platform'
DBT_PROFILES_DIR = '/opt/airflow/dbt/profiles'


# Wait for ingestion DAGs to complete
wait_for_crypto_ingestion = ExternalTaskSensor(
    task_id='wait_for_crypto_ingestion',
    external_dag_id='crypto_data_ingestion',
    external_task_id=None,  # Wait for entire DAG
    timeout=3600,
    mode='reschedule',
    dag=dag,
)

wait_for_economic_ingestion = ExternalTaskSensor(
    task_id='wait_for_economic_ingestion',
    external_dag_id='economic_data_ingestion',
    external_task_id=None,  # Wait for entire DAG
    timeout=3600,
    mode='reschedule',
    dag=dag,
)


# Task Group: Staging Layer
with TaskGroup('staging_layer', dag=dag) as staging_layer:
    
    dbt_staging_crypto = BashOperator(
        task_id='dbt_run_staging_crypto',
        bash_command=f'cd {DBT_PROJECT_PATH} && dbt run --select tag:crypto tag:staging --profiles-dir {DBT_PROFILES_DIR}',
    )
    
    dbt_staging_economic = BashOperator(
        task_id='dbt_run_staging_economic',
        bash_command=f'cd {DBT_PROJECT_PATH} && dbt run --select tag:economic tag:staging --profiles-dir {DBT_PROFILES_DIR}',
    )
    
    dbt_test_staging = BashOperator(
        task_id='dbt_test_staging',
        bash_command=f'cd {DBT_PROJECT_PATH} && dbt test --select tag:staging --profiles-dir {DBT_PROFILES_DIR}',
    )
    
    # Staging models run in parallel, then tests
    [dbt_staging_crypto, dbt_staging_economic] >> dbt_test_staging


# Task Group: Intermediate Layer
with TaskGroup('intermediate_layer', dag=dag) as intermediate_layer:
    
    dbt_intermediate_crypto = BashOperator(
        task_id='dbt_run_intermediate_crypto',
        bash_command=f'cd {DBT_PROJECT_PATH} && dbt run --select tag:crypto tag:intermediate --profiles-dir {DBT_PROFILES_DIR}',
    )
    
    dbt_intermediate_economic = BashOperator(
        task_id='dbt_run_intermediate_economic',
        bash_command=f'cd {DBT_PROJECT_PATH} && dbt run --select tag:economic tag:intermediate --profiles-dir {DBT_PROFILES_DIR}',
    )
    
    dbt_intermediate_combined = BashOperator(
        task_id='dbt_run_intermediate_combined',
        bash_command=f'cd {DBT_PROJECT_PATH} && dbt run --select tag:combined tag:intermediate --profiles-dir {DBT_PROFILES_DIR}',
    )
    
    dbt_test_intermediate = BashOperator(
        task_id='dbt_test_intermediate',
        bash_command=f'cd {DBT_PROJECT_PATH} && dbt test --select tag:intermediate --profiles-dir {DBT_PROFILES_DIR}',
    )
    
    # Domain-specific intermediate models run in parallel
    [dbt_intermediate_crypto, dbt_intermediate_economic] >> dbt_intermediate_combined >> dbt_test_intermediate


# Task Group: Marts Layer
with TaskGroup('marts_layer', dag=dag) as marts_layer:
    
    dbt_marts_crypto = BashOperator(
        task_id='dbt_run_marts_crypto',
        bash_command=f'cd {DBT_PROJECT_PATH} && dbt run --select tag:crypto tag:mart --profiles-dir {DBT_PROFILES_DIR}',
    )
    
    dbt_marts_economic = BashOperator(
        task_id='dbt_run_marts_economic',
        bash_command=f'cd {DBT_PROJECT_PATH} && dbt run --select tag:economic tag:mart --profiles-dir {DBT_PROFILES_DIR}',
    )
    
    dbt_marts_combined = BashOperator(
        task_id='dbt_run_marts_combined',
        bash_command=f'cd {DBT_PROJECT_PATH} && dbt run --select tag:combined tag:mart --profiles-dir {DBT_PROFILES_DIR}',
    )
    
    dbt_test_marts = BashOperator(
        task_id='dbt_test_marts',
        bash_command=f'cd {DBT_PROJECT_PATH} && dbt test --select tag:mart --profiles-dir {DBT_PROFILES_DIR}',
    )
    
    # Domain-specific marts run in parallel
    [dbt_marts_crypto, dbt_marts_economic] >> dbt_marts_combined >> dbt_test_marts


# Generate dbt documentation
dbt_docs_generate = BashOperator(
    task_id='dbt_docs_generate',
    bash_command=f'cd {DBT_PROJECT_PATH} && dbt docs generate --profiles-dir {DBT_PROFILES_DIR}',
    dag=dag,
)


# Snapshot critical tables
dbt_snapshot = BashOperator(
    task_id='dbt_snapshot',
    bash_command=f'cd {DBT_PROJECT_PATH} && dbt snapshot --profiles-dir {DBT_PROFILES_DIR}',
    dag=dag,
)


# Define dependencies
[wait_for_crypto_ingestion, wait_for_economic_ingestion] >> staging_layer
staging_layer >> intermediate_layer
intermediate_layer >> marts_layer
marts_layer >> [dbt_docs_generate, dbt_snapshot]
