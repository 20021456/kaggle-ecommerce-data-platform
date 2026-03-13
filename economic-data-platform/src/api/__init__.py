"""
FastAPI Application for Economic Data Platform.

Provides REST API endpoints for:
- Crypto market data
- Economic indicators
- Research datasets
- Cross-domain analytics
"""

from src.api.main import app

__all__ = ["app"]
