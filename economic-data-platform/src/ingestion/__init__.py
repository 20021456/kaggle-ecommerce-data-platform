"""
Data Ingestion Module for Economic Data Platform.

This module contains clients for various data sources:
- Crypto: Binance, CoinGecko, CryptoCompare, etc.
- Economic: FRED, BEA, World Bank, etc.
- Research: AEA ICPSR, IPUMS, etc.
"""

from src.ingestion.config import settings
from src.ingestion.base_client import BaseAPIClient

__all__ = ["settings", "BaseAPIClient"]
