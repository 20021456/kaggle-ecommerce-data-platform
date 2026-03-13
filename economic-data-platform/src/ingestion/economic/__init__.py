"""
Economic Data Ingestion Clients.

This module provides clients for various economic data sources:
- FRED: Federal Reserve Economic Data (800,000+ time series)
- BEA: Bureau of Economic Analysis (GDP, income, trade)
- BLS: Bureau of Labor Statistics (employment, CPI)
- Census: US Census Bureau (demographics)
- Treasury: US Treasury (interest rates, bonds)
- World Bank: International development indicators
- IMF: International Monetary Fund data
- OECD: OECD statistics
"""

from src.ingestion.economic.fred_client import FREDClient
from src.ingestion.economic.bea_client import BEAClient
from src.ingestion.economic.worldbank_client import WorldBankClient
from src.ingestion.economic.treasury_client import TreasuryClient
from src.ingestion.economic.bls_client import BLSClient

__all__ = [
    "FREDClient",
    "BEAClient",
    "WorldBankClient",
    "TreasuryClient",
    "BLSClient",
]
