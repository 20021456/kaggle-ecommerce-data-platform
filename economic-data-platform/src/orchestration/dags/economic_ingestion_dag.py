"""
Economic Data Ingestion DAG
Orchestrates economic indicator collection from government and international sources
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.task_group import TaskGroup

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
    'execution_timeout': timedelta(hours=2),
}

dag = DAG(
    'economic_data_ingestion',
    default_args=default_args,
    description='Ingest economic indicators from FRED, BEA, World Bank, etc.',
    schedule_interval='0 6 * * *',  # Daily at 6 AM
    catchup=False,
    max_active_runs=1,
    tags=['economic', 'ingestion', 'batch'],
)


def ingest_fred_indicators(**context):
    """Ingest economic indicators from FRED API"""
    from src.ingestion.economic.fred_client import FREDClient
    
    client = FREDClient()
    execution_date = context['execution_date']
    
    # Key economic series
    series_ids = [
        'GDP', 'GDPC1', 'GDPPOT',  # GDP
        'CPIAUCSL', 'CPILFESL', 'PCEPI',  # Inflation
        'UNRATE', 'PAYEMS', 'CIVPART',  # Employment
        'FEDFUNDS', 'DGS10', 'DGS2', 'T10Y2Y',  # Interest rates
        'M2SL', 'M1SL', 'BOGMBASE',  # Money supply
    ]
    
    data = client.get_series_observations(
        series_ids=series_ids,
        lookback_days=90  # Get last 90 days
    )
    
    # Store to bronze layer
    client.save_to_bronze(data, execution_date)
    
    return len(data)


def ingest_bea_gdp(**context):
    """Ingest GDP data from Bureau of Economic Analysis"""
    from src.ingestion.economic.bea_client import BEAClient
    
    client = BEAClient()
    execution_date = context['execution_date']
    
    # Get GDP data
    gdp_data = client.get_gdp_data(
        table_name='T10101',  # GDP table
        frequency='Q',  # Quarterly
        years=5
    )
    
    # Store to bronze layer
    client.save_to_bronze(gdp_data, execution_date)
    
    return len(gdp_data)


def ingest_bls_employment(**context):
    """Ingest employment data from Bureau of Labor Statistics"""
    from src.ingestion.economic.bls_client import BLSClient
    
    client = BLSClient()
    execution_date = context['execution_date']
    
    # Key employment series
    series_ids = [
        'LNS14000000',  # Unemployment rate
        'CES0000000001',  # Total nonfarm employment
        'LNS11300000',  # Labor force participation rate
    ]
    
    data = client.get_series_data(
        series_ids=series_ids,
        years=5
    )
    
    # Store to bronze layer
    client.save_to_bronze(data, execution_date)
    
    return len(data)


def ingest_worldbank_indicators(**context):
    """Ingest indicators from World Bank API"""
    from src.ingestion.economic.worldbank_client import WorldBankClient
    
    client = WorldBankClient()
    execution_date = context['execution_date']
    
    # Key indicators
    indicators = [
        'NY.GDP.MKTP.CD',  # GDP (current US$)
        'FP.CPI.TOTL.ZG',  # Inflation, consumer prices
        'SL.UEM.TOTL.ZS',  # Unemployment, total
        'NE.TRD.GNFS.ZS',  # Trade (% of GDP)
    ]
    
    # Major economies
    countries = ['USA', 'CHN', 'JPN', 'DEU', 'GBR', 'FRA', 'IND', 'ITA', 'BRA', 'CAN']
    
    data = client.get_indicators(
        indicators=indicators,
        countries=countries,
        years=10
    )
    
    # Store to bronze layer
    client.save_to_bronze(data, execution_date)
    
    return len(data)


def ingest_treasury_rates(**context):
    """Ingest Treasury rates from US Treasury API"""
    from src.ingestion.economic.treasury_client import TreasuryClient
    
    client = TreasuryClient()
    execution_date = context['execution_date']
    
    # Get Treasury rates
    rates = client.get_daily_rates(
        lookback_days=90
    )
    
    # Store to bronze layer
    client.save_to_bronze(rates, execution_date)
    
    return len(rates)


def validate_economic_data(**context):
    """Validate ingested economic data quality"""
    from src.utils.data_quality import EconomicDataValidator
    
    validator = EconomicDataValidator()
    execution_date = context['execution_date']
    
    # Run validation checks
    results = validator.validate_batch(execution_date)
    
    if not results['is_valid']:
        raise ValueError(f"Data quality check failed: {results['errors']}")
    
    return results


# Task Group: US Economic Data
with TaskGroup('us_economic_data', dag=dag) as us_economic:
    
    ingest_fred = PythonOperator(
        task_id='ingest_fred_indicators',
        python_callable=ingest_fred_indicators,
        provide_context=True,
    )
    
    ingest_bea = PythonOperator(
        task_id='ingest_bea_gdp',
        python_callable=ingest_bea_gdp,
        provide_context=True,
    )
    
    ingest_bls = PythonOperator(
        task_id='ingest_bls_employment',
        python_callable=ingest_bls_employment,
        provide_context=True,
    )
    
    ingest_treasury = PythonOperator(
        task_id='ingest_treasury_rates',
        python_callable=ingest_treasury_rates,
        provide_context=True,
    )
    
    # All US data ingestion tasks run in parallel
    [ingest_fred, ingest_bea, ingest_bls, ingest_treasury]


# Task Group: International Economic Data
with TaskGroup('international_economic_data', dag=dag) as international_economic:
    
    ingest_worldbank = PythonOperator(
        task_id='ingest_worldbank_indicators',
        python_callable=ingest_worldbank_indicators,
        provide_context=True,
    )


# Data Quality Validation
validate_data = PythonOperator(
    task_id='validate_economic_data',
    python_callable=validate_economic_data,
    provide_context=True,
    dag=dag,
)


# Trigger dbt transformation
trigger_dbt_economic = BashOperator(
    task_id='trigger_dbt_economic_staging',
    bash_command='cd /opt/airflow/dbt && dbt run --select tag:economic tag:staging',
    dag=dag,
)


# Define dependencies
[us_economic, international_economic] >> validate_data >> trigger_dbt_economic
