"""
API Configuration for Economic Data Platform.

Settings specific to the FastAPI application.
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class APISettings(BaseSettings):
    """API-specific settings."""

    # Server settings
    HOST: str = Field(default="0.0.0.0", description="API host")
    PORT: int = Field(default=8000, description="API port")
    RELOAD: bool = Field(default=True, description="Enable auto-reload")
    WORKERS: int = Field(default=4, description="Number of workers")

    # Environment
    ENVIRONMENT: str = Field(default="development", description="Environment name")
    DEBUG: bool = Field(default=True, description="Debug mode")

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins",
    )

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="Requests per minute")
    RATE_LIMIT_PERIOD: int = Field(default=60, description="Rate limit period (seconds)")

    # JWT Authentication
    JWT_SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production",
        description="JWT secret key — generate with: openssl rand -hex 32",
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, description="Token expiration time"
    )

    # Cache settings
    CACHE_TTL_DEFAULT: int = Field(default=300, description="Default cache TTL (seconds)")
    CACHE_TTL_PRICES: int = Field(default=60, description="Price data cache TTL")
    CACHE_TTL_ECONOMIC: int = Field(default=3600, description="Economic data cache TTL")

    # Database URLs
    DATABASE_URL: str = Field(
        default="postgresql://economic_user:economic_password@localhost:5432/economic_data",
        description="PostgreSQL connection URL",
    )
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )

    # PostgreSQL (individual fields for psycopg2 usage)
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    POSTGRES_USER: str = Field(default="economic_user", description="PostgreSQL user")
    POSTGRES_PASSWORD: str = Field(
        default="economic_password", description="PostgreSQL password"
    )
    POSTGRES_DB: str = Field(default="economic_data", description="PostgreSQL database")

    # Redis (individual fields)
    REDIS_HOST: str = Field(default="localhost", description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_PASSWORD: str = Field(default="", description="Redis password")
    REDIS_DB: int = Field(default=0, description="Redis database number")

    # Airflow REST API (proxy credentials, never exposed to frontend)
    AIRFLOW_API_URL: str = Field(
        default="http://localhost:8080/api/v1",
        description="Airflow REST API base URL",
    )
    AIRFLOW_API_USERNAME: str = Field(
        default="admin", description="Airflow API basic auth username"
    )
    AIRFLOW_API_PASSWORD: str = Field(
        default="admin", description="Airflow API basic auth password"
    )
    AIRFLOW_CACHE_TTL_DAGS: int = Field(
        default=60, description="Cache TTL for DAG list (seconds)"
    )
    AIRFLOW_CACHE_TTL_RUNS: int = Field(
        default=10, description="Cache TTL for DAG runs (seconds)"
    )

    # Trino (query engine for MinIO data lake)
    TRINO_HOST: str = Field(default="localhost", description="Trino host")
    TRINO_PORT: int = Field(default=8085, description="Trino port")
    TRINO_USER: str = Field(default="trino", description="Trino user")
    TRINO_CATALOG: str = Field(default="minio", description="Trino catalog")
    TRINO_SCHEMA: str = Field(default="bronze", description="Trino default schema")
    TRINO_QUERY_TIMEOUT: int = Field(
        default=30, description="Trino query timeout (seconds)"
    )
    TRINO_MAX_ROWS: int = Field(
        default=10000, description="Max rows returned from Trino queries"
    )

    # ClickHouse
    CLICKHOUSE_HOST: str = Field(default="localhost", description="ClickHouse host")
    CLICKHOUSE_PORT: int = Field(
        default=8123, description="ClickHouse HTTP port"
    )
    CLICKHOUSE_USER: str = Field(default="default", description="ClickHouse user")
    CLICKHOUSE_PASSWORD: str = Field(default="", description="ClickHouse password")
    CLICKHOUSE_DB: str = Field(default="economic_data", description="ClickHouse database")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


# Global settings instance
api_settings = APISettings()
