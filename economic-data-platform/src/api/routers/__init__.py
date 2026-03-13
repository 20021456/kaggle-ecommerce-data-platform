"""
API Routers for Economic Data Platform.

Provides endpoint routers for:
- Crypto: Cryptocurrency market data
- Economic: Economic indicators and data
- Analytics: Cross-domain analytics
- Health: Health and status endpoints
"""

from src.api.routers import crypto, economic, analytics, health

__all__ = ["crypto", "economic", "analytics", "health"]
