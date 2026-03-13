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
        description="Allowed CORS origins"
    )
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="Requests per minute")
    RATE_LIMIT_PERIOD: int = Field(default=60, description="Rate limit period (seconds)")
    
    # JWT Authentication
    JWT_SECRET_KEY: str = Field(
        default="your_jwt_secret_key_change_in_production",
        description="JWT secret key"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Token expiration time"
    )
    
    # Cache settings
    CACHE_TTL_DEFAULT: int = Field(default=300, description="Default cache TTL (seconds)")
    CACHE_TTL_PRICES: int = Field(default=60, description="Price data cache TTL")
    CACHE_TTL_ECONOMIC: int = Field(default=3600, description="Economic data cache TTL")
    
    # Database URLs (from main config)
    DATABASE_URL: str = Field(
        default="postgresql://economic_user:economic_password@localhost:5432/economic_data",
        description="PostgreSQL connection URL"
    )
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


# Global settings instance
api_settings = APISettings()
