"""
Main FastAPI Application - Economic Data Analytics Platform

This module creates and configures the FastAPI application with:
- CORS middleware
- Rate limiting
- Health checks
- API routers for different domains
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from src.api.config import api_settings
from src.api.routers import crypto, economic, analytics, health
from src.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Economic Data Platform API...")
    logger.info(f"Environment: {api_settings.ENVIRONMENT}")
    
    # Initialize connections, caches, etc.
    # await init_database()
    # await init_redis()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Economic Data Platform API...")
    # await close_database()
    # await close_redis()


# Create FastAPI application
app = FastAPI(
    title="Economic Data Analytics Platform API",
    description="""
    Multi-Domain Data Analytics Platform combining:
    - **Crypto/Financial Markets** - Real-time and historical crypto data
    - **Economic Indicators** - FRED, BEA, World Bank data
    - **Cross-Domain Analytics** - Crypto-macro correlations and analysis
    
    ## Features
    - Real-time cryptocurrency prices and market data
    - US and international economic indicators
    - Bitcoin as inflation hedge analysis
    - Market regime classification
    - Historical data with various frequencies
    
    ## Authentication
    API endpoints require JWT authentication. Get your token from `/api/v1/auth/token`.
    
    ## Rate Limits
    - Free tier: 100 requests/minute
    - Pro tier: 1000 requests/minute
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# =============================================================================
# MIDDLEWARE
# =============================================================================

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=api_settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start_time = datetime.utcnow()
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = (datetime.utcnow() - start_time).total_seconds()
    
    # Log request
    logger.info(
        "request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_seconds=duration,
        client_ip=request.client.host if request.client else None,
    )
    
    return response


# Rate limiting middleware (basic implementation)
request_counts: Dict[str, list] = {}


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    """Simple rate limiting middleware."""
    client_ip = request.client.host if request.client else "unknown"
    
    # Get current minute
    current_minute = datetime.utcnow().replace(second=0, microsecond=0)
    
    # Initialize or clean up request counts
    if client_ip not in request_counts:
        request_counts[client_ip] = []
    
    # Remove old timestamps
    request_counts[client_ip] = [
        ts for ts in request_counts[client_ip]
        if ts > current_minute
    ]
    
    # Check rate limit
    if len(request_counts[client_ip]) >= api_settings.RATE_LIMIT_REQUESTS:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please try again later."}
        )
    
    # Add current request
    request_counts[client_ip].append(datetime.utcnow())
    
    return await call_next(request)


# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "status_code": 500,
        }
    )


# =============================================================================
# ROUTERS
# =============================================================================

# Include API routers
app.include_router(health.router, tags=["Health"])
app.include_router(crypto.router, prefix="/api/v1/crypto", tags=["Crypto"])
app.include_router(economic.router, prefix="/api/v1/economic", tags=["Economic"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# =============================================================================
# ROOT ENDPOINTS
# =============================================================================

@app.get("/", response_model=Dict[str, Any])
async def root():
    """
    API Root - Welcome endpoint.
    
    Returns basic information about the API.
    """
    return {
        "name": "Economic Data Analytics Platform API",
        "version": "1.0.0",
        "description": "Multi-domain data analytics combining crypto and economic data",
        "documentation": "/docs",
        "health": "/health",
        "endpoints": {
            "crypto": "/api/v1/crypto",
            "economic": "/api/v1/economic",
            "analytics": "/api/v1/analytics",
        }
    }


@app.get("/health")
async def health_check():
    """
    Quick health check endpoint.
    
    Returns basic health status.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


# =============================================================================
# RUN APPLICATION
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host=api_settings.HOST,
        port=api_settings.PORT,
        reload=api_settings.RELOAD,
        workers=1 if api_settings.RELOAD else api_settings.WORKERS,
    )
