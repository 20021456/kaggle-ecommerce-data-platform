"""
Configuration management for Economic Data Platform.

Loads settings from environment variables with sensible defaults.
"""

from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # ==========================================================================
    # General Settings
    # ==========================================================================
    ENVIRONMENT: str = Field(default="development", description="Environment name")
    DEBUG: bool = Field(default=True, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    # ==========================================================================
    # Crypto API Keys
    # ==========================================================================
    BINANCE_API_KEY: Optional[str] = Field(default=None, description="Binance API key")
    BINANCE_API_SECRET: Optional[str] = Field(default=None, description="Binance API secret")
    COINGECKO_API_KEY: Optional[str] = Field(default=None, description="CoinGecko API key")
    CRYPTOCOMPARE_API_KEY: Optional[str] = Field(default=None, description="CryptoCompare API key")
    
    # ==========================================================================
    # Economic API Keys
    # ==========================================================================
    FRED_API_KEY: Optional[str] = Field(default=None, description="FRED API key")
    BEA_API_KEY: Optional[str] = Field(default=None, description="BEA API key")
    CENSUS_API_KEY: Optional[str] = Field(default=None, description="Census API key")
    BLS_API_KEY: Optional[str] = Field(default=None, description="BLS API key")
    
    # ==========================================================================
    # Research Data Credentials
    # ==========================================================================
    AEA_ICPSR_USERNAME: Optional[str] = Field(default=None, description="AEA ICPSR username")
    AEA_ICPSR_PASSWORD: Optional[str] = Field(default=None, description="AEA ICPSR password")
    IPUMS_API_KEY: Optional[str] = Field(default=None, description="IPUMS API key")
    
    # ==========================================================================
    # Microsoft SQL Server (Input Data Source)
    # ==========================================================================
    MSSQL_HOST: str = Field(default="45.124.94.158", description="MSSQL Server host")
    MSSQL_PORT: int = Field(default=1433, description="MSSQL Server port")
    MSSQL_DATABASE: str = Field(default="xomdata_dataset", description="MSSQL database name")
    MSSQL_USER: str = Field(description="MSSQL username")
    MSSQL_PASSWORD: str = Field(description="MSSQL password")
    
    @property
    def MSSQL_CONNECTION_STRING(self) -> str:
        """Construct MSSQL connection string for pymssql."""
        return f"mssql+pymssql://{self.MSSQL_USER}:{self.MSSQL_PASSWORD}@{self.MSSQL_HOST}:{self.MSSQL_PORT}/{self.MSSQL_DATABASE}"
    
    # ==========================================================================
    # PostgreSQL Database
    # ==========================================================================
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    POSTGRES_USER: str = Field(default="economic_user", description="PostgreSQL user")
    POSTGRES_PASSWORD: str = Field(default="economic_password", description="PostgreSQL password")
    POSTGRES_DB: str = Field(default="economic_data", description="PostgreSQL database")
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct PostgreSQL connection URL."""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Construct async PostgreSQL connection URL."""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # ==========================================================================
    # ClickHouse Database
    # ==========================================================================
    CLICKHOUSE_HOST: str = Field(default="localhost", description="ClickHouse host")
    CLICKHOUSE_PORT: int = Field(default=9000, description="ClickHouse native port")
    CLICKHOUSE_HTTP_PORT: int = Field(default=8123, description="ClickHouse HTTP port")
    CLICKHOUSE_USER: str = Field(default="default", description="ClickHouse user")
    CLICKHOUSE_PASSWORD: str = Field(default="", description="ClickHouse password")
    CLICKHOUSE_DB: str = Field(default="economic_data", description="ClickHouse database")
    
    # ==========================================================================
    # Redis Cache
    # ==========================================================================
    REDIS_HOST: str = Field(default="localhost", description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_PASSWORD: str = Field(default="", description="Redis password")
    REDIS_DB: int = Field(default=0, description="Redis database number")
    
    @property
    def REDIS_URL(self) -> str:
        """Construct Redis connection URL."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # ==========================================================================
    # Apache Kafka
    # ==========================================================================
    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="localhost:9092", description="Kafka bootstrap servers")
    KAFKA_SCHEMA_REGISTRY_URL: str = Field(default="http://localhost:8081", description="Schema Registry URL")
    KAFKA_TOPIC_CRYPTO_TRADES: str = Field(default="crypto.trades", description="Crypto trades topic")
    KAFKA_TOPIC_CRYPTO_PRICES: str = Field(default="crypto.prices", description="Crypto prices topic")
    KAFKA_TOPIC_ECONOMIC_DATA: str = Field(default="economic.data", description="Economic data topic")
    
    # ==========================================================================
    # MinIO / S3
    # ==========================================================================
    MINIO_ENDPOINT: str = Field(default="localhost:9000", description="MinIO endpoint")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin", description="MinIO access key")
    MINIO_SECRET_KEY: str = Field(default="minioadmin", description="MinIO secret key")
    MINIO_SECURE: bool = Field(default=False, description="Use HTTPS for MinIO")
    MINIO_BUCKET_BRONZE: str = Field(default="bronze", description="Bronze layer bucket")
    MINIO_BUCKET_SILVER: str = Field(default="silver", description="Silver layer bucket")
    MINIO_BUCKET_GOLD: str = Field(default="gold", description="Gold layer bucket")
    
    # ==========================================================================
    # Trino (Query Engine for MinIO Data Lake)
    # ==========================================================================
    TRINO_HOST: str = Field(default="localhost", description="Trino host")
    TRINO_PORT: int = Field(default=8085, description="Trino port")
    TRINO_USER: str = Field(default="trino", description="Trino user")
    TRINO_CATALOG: str = Field(default="minio", description="Trino catalog name")
    TRINO_SCHEMA: str = Field(default="bronze", description="Default Trino schema")
    
    # ==========================================================================
    # Olist Dataset (Local CSV files)
    # ==========================================================================
    OLIST_DATA_DIR: str = Field(default="data/raw/olist", description="Path to extracted Olist CSV files")
    
    # ==========================================================================
    # Airflow REST API (for monitoring proxy)
    # ==========================================================================
    AIRFLOW_API_URL: str = Field(default="http://localhost:8080/api/v1", description="Airflow REST API base URL")
    AIRFLOW_API_USERNAME: str = Field(default="admin", description="Airflow API username")
    AIRFLOW_API_PASSWORD: str = Field(default="admin", description="Airflow API password")
    
    # ==========================================================================
    # FastAPI Settings
    # ==========================================================================
    API_HOST: str = Field(default="0.0.0.0", description="API host")
    API_PORT: int = Field(default=8000, description="API port")
    API_RELOAD: bool = Field(default=True, description="API auto-reload")
    API_WORKERS: int = Field(default=4, description="Number of API workers")
    
    # JWT Authentication
    JWT_SECRET_KEY: str = Field(description="JWT secret key — generate with: openssl rand -hex 32")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="JWT token expiration")
    
    # Rate Limiting
    API_RATE_LIMIT_REQUESTS: int = Field(default=100, description="Rate limit requests")
    API_RATE_LIMIT_PERIOD: int = Field(default=60, description="Rate limit period in seconds")
    
    # ==========================================================================
    # Data Ingestion Settings
    # ==========================================================================
    CRYPTO_REALTIME_ENABLED: bool = Field(default=True, description="Enable real-time crypto streaming")
    CRYPTO_PRICE_REFRESH_INTERVAL: int = Field(default=300, description="Crypto price refresh interval (seconds)")
    CRYPTO_OHLCV_REFRESH_INTERVAL: int = Field(default=3600, description="OHLCV refresh interval (seconds)")
    
    ECONOMIC_DAILY_REFRESH_HOUR: int = Field(default=6, description="Economic data refresh hour (UTC)")
    ECONOMIC_MONTHLY_REFRESH_DAY: int = Field(default=1, description="Economic monthly refresh day")
    
    BATCH_SIZE_CRYPTO: int = Field(default=1000, description="Crypto batch size")
    BATCH_SIZE_ECONOMIC: int = Field(default=500, description="Economic batch size")
    
    # Rate limits (requests per minute)
    RATE_LIMIT_COINGECKO: int = Field(default=50, description="CoinGecko rate limit")
    RATE_LIMIT_FRED: int = Field(default=120, description="FRED rate limit")
    RATE_LIMIT_WORLDBANK: int = Field(default=60, description="World Bank rate limit")
    
    # ==========================================================================
    # External API Base URLs
    # ==========================================================================
    BINANCE_WS_URL: str = Field(default="wss://stream.binance.com:9443/ws", description="Binance WebSocket URL")
    BINANCE_API_URL: str = Field(default="https://api.binance.com", description="Binance API URL")
    COINGECKO_API_URL: str = Field(default="https://api.coingecko.com/api/v3", description="CoinGecko API URL")
    CRYPTOCOMPARE_API_URL: str = Field(default="https://min-api.cryptocompare.com/data", description="CryptoCompare API URL")
    BLOCKCHAIN_INFO_URL: str = Field(default="https://blockchain.info", description="Blockchain.info URL")
    FEAR_GREED_URL: str = Field(default="https://api.alternative.me/fng", description="Fear & Greed Index URL")
    
    FRED_API_URL: str = Field(default="https://api.stlouisfed.org/fred", description="FRED API URL")
    BEA_API_URL: str = Field(default="https://apps.bea.gov/api/data", description="BEA API URL")
    BLS_API_URL: str = Field(default="https://api.bls.gov/publicAPI/v2", description="BLS API URL")
    CENSUS_API_URL: str = Field(default="https://api.census.gov/data", description="Census API URL")
    TREASURY_API_URL: str = Field(default="https://api.fiscaldata.treasury.gov/services/api/fiscal_service", description="Treasury API URL")
    
    WORLDBANK_API_URL: str = Field(default="https://api.worldbank.org/v2", description="World Bank API URL")
    IMF_API_URL: str = Field(default="https://dataservices.imf.org/REST/SDMX_JSON.svc", description="IMF API URL")
    OECD_API_URL: str = Field(default="https://stats.oecd.org/SDMX-JSON", description="OECD API URL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
