"""
API Routers for Economic Data Platform.

Provides endpoint routers for:
- Crypto: Cryptocurrency market data
- Economic: Economic indicators and data
- Analytics: Cross-domain analytics
- Health: Health and status endpoints
- Monitor: Airflow proxy (Phase 7)
- Ingestion: Data source monitoring (Phase 7)
- Dashboard: E-commerce analytics (Phase 7)
- Query: Ad-hoc Trino SQL (Phase 7)
"""

from src.api.routers import (
    crypto,
    economic,
    analytics,
    health,
    monitor,
    ingestion,
    dashboard,
    query,
)

__all__ = [
    "crypto",
    "economic",
    "analytics",
    "health",
    "monitor",
    "ingestion",
    "dashboard",
    "query",
]
