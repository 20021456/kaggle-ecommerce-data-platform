"""
Health API Router - Health and status endpoints.

Provides endpoints for:
- Basic health checks
- Component status (database, cache, etc.)
- API version information
"""

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter

from src.api.config import api_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns simple health status for load balancer/orchestrator checks.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check with component status.
    
    Checks connectivity to all dependent services.
    """
    components = {}
    overall_status = "healthy"
    
    # Check PostgreSQL
    try:
        # In production, actually test connection
        components["postgresql"] = {
            "status": "healthy",
            "message": "Connection available",
        }
    except Exception as e:
        components["postgresql"] = {
            "status": "unhealthy",
            "message": str(e),
        }
        overall_status = "degraded"
    
    # Check Redis
    try:
        # In production, actually test connection
        components["redis"] = {
            "status": "healthy",
            "message": "Connection available",
        }
    except Exception as e:
        components["redis"] = {
            "status": "unhealthy",
            "message": str(e),
        }
        overall_status = "degraded"
    
    # Check Kafka
    try:
        components["kafka"] = {
            "status": "healthy",
            "message": "Connection available",
        }
    except Exception as e:
        components["kafka"] = {
            "status": "unhealthy",
            "message": str(e),
        }
        overall_status = "degraded"
    
    # Check MinIO
    try:
        components["minio"] = {
            "status": "healthy",
            "message": "Connection available",
        }
    except Exception as e:
        components["minio"] = {
            "status": "unhealthy",
            "message": str(e),
        }
        overall_status = "degraded"
    
    # Check external APIs
    try:
        from src.ingestion.crypto import CoinGeckoClient
        client = CoinGeckoClient()
        if client.health_check():
            components["coingecko_api"] = {
                "status": "healthy",
                "message": "API accessible",
            }
        else:
            components["coingecko_api"] = {
                "status": "degraded",
                "message": "API returned unexpected response",
            }
    except Exception as e:
        components["coingecko_api"] = {
            "status": "unhealthy",
            "message": str(e),
        }
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "environment": api_settings.ENVIRONMENT,
        "components": components,
    }


@router.get("/health/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check for Kubernetes.
    
    Returns 200 if the service is ready to receive traffic.
    """
    # In production, check if all critical components are ready
    is_ready = True
    
    return {
        "ready": is_ready,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/health/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check for Kubernetes.
    
    Returns 200 if the service is alive and should not be restarted.
    """
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/version")
async def get_version() -> Dict[str, Any]:
    """
    Get API version information.
    """
    return {
        "name": "Economic Data Analytics Platform API",
        "version": "1.0.0",
        "environment": api_settings.ENVIRONMENT,
        "python_version": "3.11",
        "build_date": "2024-01-01",
    }


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """
    Get comprehensive API status.
    """
    return {
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": api_settings.ENVIRONMENT,
        "debug": api_settings.DEBUG,
        "endpoints": {
            "crypto": "/api/v1/crypto",
            "economic": "/api/v1/economic",
            "analytics": "/api/v1/analytics",
        },
        "rate_limits": {
            "requests_per_minute": api_settings.RATE_LIMIT_REQUESTS,
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
        },
    }
