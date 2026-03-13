"""
Crypto Data Ingestion DAG
Orchestrates cryptocurrency data collection from multiple sources
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.task_group import TaskGroup
from airflow.sensors.external_task import ExternalTaskSensor

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=1),
}

dag = DAG(
    'crypto_data_ingestion',
    default_args=default_args,
    description='Ingest cryptocurrency data from multiple sources',
    schedule_interval='*/15 * * * *',  # Every 15 minutes
    catchup=False,
    max_active_runs=1,
    tags=['crypto', 'ingestion', 'real-time'],
)


def ingest_binance_trades(**context):
    """Ingest real-time trades from Binance"""
    from src.ingestion.crypto.binance_client import BinanceClient
    
    client = BinanceClient()
    execution_date = context['execution_date']
    
    # Ingest trades for last 15 minutes
    trades = client.get_recent_trades(
        symbols=['BTCUSDT', 'ETHUSDT', 'BNBUSDT'],
        lookback_minutes=15
    )
    
    # Store to bronze layer
    client.save_to_bronze(trades, execution_date)
    
    return len(trades)


def ingest_coingecko_prices(**context):
    """Ingest current prices from CoinGecko"""
    from src.ingestion.crypto.coingecko_client import CoinGeckoClient
    
    client = CoinGeckoClient()
    execution_date = context['execution_date']
    
    # Get prices for top coins
    prices = client.get_prices(
        coin_ids=['bitcoin', 'ethereum', 'binancecoin', 'solana', 'cardano']
    )
    
    # Store to bronze layer
    client.save_to_bronze(prices, execution_date)
    
    return len(prices)


def ingest_cryptocompare_ohlcv(**context):
    """Ingest OHLCV data from CryptoCompare"""
    from src.ingestion.crypto.cryptocompare_client import CryptoCompareClient
    
    client = CryptoCompareClient()
    execution_date = context['execution_date']
    
    # Get hourly OHLCV
    ohlcv = client.get_hourly_ohlcv(
        symbols=['BTC', 'ETH', 'BNB'],
        hours=24
    )
    
    # Store to bronze layer
    client.save_to_bronze(ohlcv, execution_date)
    
    return len(ohlcv)


def ingest_fear_greed_index(**context):
    """Ingest Crypto Fear & Greed Index"""
    from src.ingestion.crypto.fear_greed_client import FearGreedClient
    
    client = FearGreedClient()
    execution_date = context['execution_date']
    
    # Get current index
    index_data = client.get_current_index()
    
    # Store to bronze layer
    client.save_to_bronze(index_data, execution_date)
    
    return 1


def validate_crypto_data(**context):
    """Validate ingested crypto data quality"""
    from src.utils.data_quality import CryptoDataValidator
    
    validator = CryptoDataValidator()
    execution_date = context['execution_date']
    
    # Run validation checks
    results = validator.validate_batch(execution_date)
    
    if not results['is_valid']:
        raise ValueError(f"Data quality check failed: {results['errors']}")
    
    return results


# Task Group: Crypto Data Ingestion
with TaskGroup('crypto_ingestion', dag=dag) as crypto_ingestion:
    
    ingest_binance = PythonOperator(
        task_id='ingest_binance_trades',
        python_callable=ingest_binance_trades,
        provide_context=True,
    )
    
    ingest_coingecko = PythonOperator(
        task_id='ingest_coingecko_prices',
        python_callable=ingest_coingecko_prices,
        provide_context=True,
    )
    
    ingest_cryptocompare = PythonOperator(
        task_id='ingest_cryptocompare_ohlcv',
        python_callable=ingest_cryptocompare_ohlcv,
        provide_context=True,
    )
    
    ingest_fear_greed = PythonOperator(
        task_id='ingest_fear_greed_index',
        python_callable=ingest_fear_greed_index,
        provide_context=True,
    )
    
    # All ingestion tasks run in parallel
    [ingest_binance, ingest_coingecko, ingest_cryptocompare, ingest_fear_greed]


# Data Quality Validation
validate_data = PythonOperator(
    task_id='validate_crypto_data',
    python_callable=validate_crypto_data,
    provide_context=True,
    dag=dag,
)


# Trigger dbt transformation
trigger_dbt_crypto = BashOperator(
    task_id='trigger_dbt_crypto_staging',
    bash_command='cd /opt/airflow/dbt && dbt run --select tag:crypto tag:staging',
    dag=dag,
)


# Define dependencies
crypto_ingestion >> validate_data >> trigger_dbt_crypto
