"""
Crypto Data Ingestion Clients.

This module provides clients for various cryptocurrency data sources:
- Binance: Real-time trades and OHLCV via WebSocket
- CoinGecko: Market data, coin metadata, prices
- CryptoCompare: Historical OHLCV, social stats
- Blockchain.info: Bitcoin blockchain data
- Fear & Greed Index: Market sentiment
"""

from src.ingestion.crypto.coingecko_client import CoinGeckoClient
from src.ingestion.crypto.binance_websocket import BinanceWebSocket
from src.ingestion.crypto.cryptocompare_client import CryptoCompareClient
from src.ingestion.crypto.blockchain_client import BlockchainClient
from src.ingestion.crypto.fear_greed_client import FearGreedClient

__all__ = [
    "CoinGeckoClient",
    "BinanceWebSocket",
    "CryptoCompareClient",
    "BlockchainClient",
    "FearGreedClient",
]
