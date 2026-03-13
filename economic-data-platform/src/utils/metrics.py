"""
Metrics collection for the Economic Data Platform.

Provides Prometheus metrics for monitoring data ingestion,
processing, and API performance.
"""

from prometheus_client import Counter, Histogram, Gauge, Info
from functools import wraps
import time
from typing import Callable


# =============================================================================
# DATA INGESTION METRICS
# =============================================================================

# Records ingested counter
RECORDS_INGESTED = Counter(
    'economic_platform_records_ingested_total',
    'Total number of records ingested',
    ['source', 'domain', 'status']
)

# Ingestion duration histogram
INGESTION_DURATION = Histogram(
    'economic_platform_ingestion_duration_seconds',
    'Time spent on data ingestion',
    ['source', 'domain'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0)
)

# API calls counter
API_CALLS = Counter(
    'economic_platform_api_calls_total',
    'Total number of external API calls',
    ['source', 'endpoint', 'status']
)

# API rate limit remaining
RATE_LIMIT_REMAINING = Gauge(
    'economic_platform_rate_limit_remaining',
    'Remaining API rate limit',
    ['source']
)


# =============================================================================
# DATA PROCESSING METRICS
# =============================================================================

# Transformation duration
TRANSFORMATION_DURATION = Histogram(
    'economic_platform_transformation_duration_seconds',
    'Time spent on data transformation',
    ['layer', 'domain'],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0)
)

# Records processed
RECORDS_PROCESSED = Counter(
    'economic_platform_records_processed_total',
    'Total number of records processed',
    ['layer', 'domain', 'status']
)

# Data quality issues
DATA_QUALITY_ISSUES = Counter(
    'economic_platform_data_quality_issues_total',
    'Number of data quality issues detected',
    ['domain', 'issue_type']
)


# =============================================================================
# API METRICS
# =============================================================================

# HTTP requests
HTTP_REQUESTS = Counter(
    'economic_platform_http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code']
)

# HTTP request duration
HTTP_REQUEST_DURATION = Histogram(
    'economic_platform_http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0)
)

# Active connections
ACTIVE_CONNECTIONS = Gauge(
    'economic_platform_active_connections',
    'Number of active connections',
    ['type']
)


# =============================================================================
# DATABASE METRICS
# =============================================================================

# Database query duration
DB_QUERY_DURATION = Histogram(
    'economic_platform_db_query_duration_seconds',
    'Database query latency',
    ['database', 'operation'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# Database pool size
DB_POOL_SIZE = Gauge(
    'economic_platform_db_pool_size',
    'Database connection pool size',
    ['database']
)


# =============================================================================
# SYSTEM METRICS
# =============================================================================

# Application info
APP_INFO = Info(
    'economic_platform_app',
    'Application information'
)

# Data freshness (age of latest data in seconds)
DATA_FRESHNESS = Gauge(
    'economic_platform_data_freshness_seconds',
    'Age of the latest data',
    ['source', 'domain']
)


# =============================================================================
# METRIC DECORATORS
# =============================================================================

def track_ingestion_time(source: str, domain: str):
    """Decorator to track ingestion duration."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            with INGESTION_DURATION.labels(source=source, domain=domain).time():
                return func(*args, **kwargs)
        return wrapper
    return decorator


def track_api_call(source: str, endpoint: str):
    """Decorator to track API calls."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                API_CALLS.labels(source=source, endpoint=endpoint, status='success').inc()
                return result
            except Exception as e:
                API_CALLS.labels(source=source, endpoint=endpoint, status='error').inc()
                raise
        return wrapper
    return decorator


def track_processing_time(layer: str, domain: str):
    """Decorator to track processing duration."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            with TRANSFORMATION_DURATION.labels(layer=layer, domain=domain).time():
                return func(*args, **kwargs)
        return wrapper
    return decorator


def track_http_request(method: str, endpoint: str):
    """Decorator to track HTTP request metrics."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                response = await func(*args, **kwargs)
                status_code = getattr(response, 'status_code', 200)
                HTTP_REQUESTS.labels(
                    method=method, 
                    endpoint=endpoint, 
                    status_code=status_code
                ).inc()
                return response
            except Exception as e:
                HTTP_REQUESTS.labels(
                    method=method, 
                    endpoint=endpoint, 
                    status_code=500
                ).inc()
                raise
            finally:
                HTTP_REQUEST_DURATION.labels(
                    method=method, 
                    endpoint=endpoint
                ).observe(time.time() - start_time)
        return wrapper
    return decorator


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def record_ingestion(source: str, domain: str, count: int, status: str = 'success'):
    """Record ingested records count."""
    RECORDS_INGESTED.labels(source=source, domain=domain, status=status).inc(count)


def record_processing(layer: str, domain: str, count: int, status: str = 'success'):
    """Record processed records count."""
    RECORDS_PROCESSED.labels(layer=layer, domain=domain, status=status).inc(count)


def record_data_quality_issue(domain: str, issue_type: str, count: int = 1):
    """Record data quality issue."""
    DATA_QUALITY_ISSUES.labels(domain=domain, issue_type=issue_type).inc(count)


def update_rate_limit(source: str, remaining: int):
    """Update rate limit remaining gauge."""
    RATE_LIMIT_REMAINING.labels(source=source).set(remaining)


def update_data_freshness(source: str, domain: str, age_seconds: float):
    """Update data freshness gauge."""
    DATA_FRESHNESS.labels(source=source, domain=domain).set(age_seconds)


def set_app_info(version: str, environment: str):
    """Set application info."""
    APP_INFO.info({
        'version': version,
        'environment': environment
    })
