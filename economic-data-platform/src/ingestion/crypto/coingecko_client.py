"""
CoinGecko API Client for cryptocurrency market data.

CoinGecko provides comprehensive cryptocurrency data including:
- Current prices and market data
- Historical price data
- Coin metadata and descriptions
- Market cap rankings
- Trading volumes
- Exchange data

API Documentation: https://www.coingecko.com/api/documentation
Rate Limits: Free tier - 50 calls/min, Pro - higher limits
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from src.ingestion.base_client import BaseAPIClient
from src.ingestion.config import settings
from src.utils.helpers import parse_date, timestamp_to_datetime


class CoinGeckoClient(BaseAPIClient):
    """
    Client for CoinGecko cryptocurrency data API.
    
    Provides methods to fetch:
    - Coin list and metadata
    - Current prices and market data
    - Historical prices (OHLCV)
    - Market cap rankings
    - Global crypto market stats
    
    Example:
        client = CoinGeckoClient()
        
        # Get current prices
        prices = client.get_prices(['bitcoin', 'ethereum'])
        
        # Get market data
        markets = client.get_markets(vs_currency='usd', per_page=100)
        
        # Get historical data
        history = client.get_coin_market_chart('bitcoin', days=30)
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize CoinGecko client.
        
        Args:
            api_key: Optional API key for Pro tier access
        """
        super().__init__(
            base_url=settings.COINGECKO_API_URL,
            api_key=api_key or settings.COINGECKO_API_KEY,
            rate_limit=settings.RATE_LIMIT_COINGECKO,
            timeout=30,
            max_retries=3,
            cache_ttl=60,  # 1 minute cache
        )
    
    def _get_headers(self) -> Dict[str, str]:
        """Override headers for CoinGecko API."""
        headers = super()._get_headers()
        
        # CoinGecko Pro uses x-cg-pro-api-key header
        if self.api_key:
            headers["x-cg-pro-api-key"] = self.api_key
            del headers["Authorization"]
        
        return headers
    
    def get_source_name(self) -> str:
        """Return source name."""
        return "coingecko"
    
    def health_check(self) -> bool:
        """Check if CoinGecko API is accessible."""
        try:
            response = self.get("/ping")
            return response.get("gecko_says") == "(V3) To the Moon!"
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    # =========================================================================
    # SIMPLE ENDPOINTS
    # =========================================================================
    
    def get_price(
        self,
        ids: Union[str, List[str]],
        vs_currencies: Union[str, List[str]] = "usd",
        include_market_cap: bool = True,
        include_24h_vol: bool = True,
        include_24h_change: bool = True,
        include_last_updated_at: bool = True,
    ) -> Dict[str, Dict[str, float]]:
        """
        Get current price of coins.
        
        Args:
            ids: Coin ID(s) (e.g., 'bitcoin' or ['bitcoin', 'ethereum'])
            vs_currencies: Target currency(ies) (e.g., 'usd' or ['usd', 'eur'])
            include_market_cap: Include market cap
            include_24h_vol: Include 24h volume
            include_24h_change: Include 24h change
            include_last_updated_at: Include last updated timestamp
            
        Returns:
            Dict mapping coin IDs to their price data
        """
        if isinstance(ids, list):
            ids = ",".join(ids)
        if isinstance(vs_currencies, list):
            vs_currencies = ",".join(vs_currencies)
        
        params = {
            "ids": ids,
            "vs_currencies": vs_currencies,
            "include_market_cap": str(include_market_cap).lower(),
            "include_24hr_vol": str(include_24h_vol).lower(),
            "include_24hr_change": str(include_24h_change).lower(),
            "include_last_updated_at": str(include_last_updated_at).lower(),
        }
        
        return self.get("/simple/price", params=params)
    
    def get_supported_vs_currencies(self) -> List[str]:
        """Get list of supported vs currencies."""
        return self.get("/simple/supported_vs_currencies")
    
    # =========================================================================
    # COINS ENDPOINTS
    # =========================================================================
    
    def get_coins_list(self, include_platform: bool = False) -> List[Dict[str, str]]:
        """
        Get list of all supported coins.
        
        Args:
            include_platform: Include platform contract addresses
            
        Returns:
            List of coins with id, symbol, name
        """
        params = {"include_platform": str(include_platform).lower()}
        return self.get("/coins/list", params=params)
    
    def get_markets(
        self,
        vs_currency: str = "usd",
        ids: Optional[Union[str, List[str]]] = None,
        category: Optional[str] = None,
        order: str = "market_cap_desc",
        per_page: int = 100,
        page: int = 1,
        sparkline: bool = False,
        price_change_percentage: Optional[str] = "1h,24h,7d",
    ) -> List[Dict[str, Any]]:
        """
        Get coins market data.
        
        Args:
            vs_currency: Target currency (default: usd)
            ids: Filter by coin IDs
            category: Filter by category
            order: Sort order (market_cap_desc, volume_desc, etc.)
            per_page: Results per page (max 250)
            page: Page number
            sparkline: Include 7d sparkline data
            price_change_percentage: Price change periods
            
        Returns:
            List of coins with market data
        """
        if isinstance(ids, list):
            ids = ",".join(ids)
        
        params = {
            "vs_currency": vs_currency,
            "order": order,
            "per_page": min(per_page, 250),
            "page": page,
            "sparkline": str(sparkline).lower(),
        }
        
        if ids:
            params["ids"] = ids
        if category:
            params["category"] = category
        if price_change_percentage:
            params["price_change_percentage"] = price_change_percentage
        
        return self.get("/coins/markets", params=params)
    
    def get_coin(
        self,
        coin_id: str,
        localization: bool = False,
        tickers: bool = True,
        market_data: bool = True,
        community_data: bool = True,
        developer_data: bool = True,
        sparkline: bool = False,
    ) -> Dict[str, Any]:
        """
        Get detailed coin data.
        
        Args:
            coin_id: Coin ID (e.g., 'bitcoin')
            localization: Include all localizations
            tickers: Include tickers data
            market_data: Include market data
            community_data: Include community data
            developer_data: Include developer data
            sparkline: Include 7d sparkline
            
        Returns:
            Detailed coin data
        """
        params = {
            "localization": str(localization).lower(),
            "tickers": str(tickers).lower(),
            "market_data": str(market_data).lower(),
            "community_data": str(community_data).lower(),
            "developer_data": str(developer_data).lower(),
            "sparkline": str(sparkline).lower(),
        }
        
        return self.get(f"/coins/{coin_id}", params=params)
    
    def get_coin_tickers(
        self,
        coin_id: str,
        exchange_ids: Optional[str] = None,
        include_exchange_logo: bool = False,
        page: int = 1,
        order: str = "trust_score_desc",
        depth: bool = False,
    ) -> Dict[str, Any]:
        """
        Get coin tickers (trading pairs) data.
        
        Args:
            coin_id: Coin ID
            exchange_ids: Filter by exchange IDs
            include_exchange_logo: Include exchange logos
            page: Page number
            order: Sort order
            depth: Include order book depth
            
        Returns:
            Ticker data for the coin
        """
        params = {
            "include_exchange_logo": str(include_exchange_logo).lower(),
            "page": page,
            "order": order,
            "depth": str(depth).lower(),
        }
        
        if exchange_ids:
            params["exchange_ids"] = exchange_ids
        
        return self.get(f"/coins/{coin_id}/tickers", params=params)
    
    def get_coin_history(
        self,
        coin_id: str,
        date: Union[str, datetime],
        localization: bool = False,
    ) -> Dict[str, Any]:
        """
        Get historical data for a coin on a specific date.
        
        Args:
            coin_id: Coin ID
            date: Date (dd-mm-yyyy format or datetime object)
            localization: Include localizations
            
        Returns:
            Historical data for the date
        """
        if isinstance(date, datetime):
            date = date.strftime("%d-%m-%Y")
        
        params = {
            "date": date,
            "localization": str(localization).lower(),
        }
        
        return self.get(f"/coins/{coin_id}/history", params=params)
    
    def get_coin_market_chart(
        self,
        coin_id: str,
        vs_currency: str = "usd",
        days: Union[int, str] = 30,
        interval: Optional[str] = None,
    ) -> Dict[str, List]:
        """
        Get historical market chart data.
        
        Args:
            coin_id: Coin ID
            vs_currency: Target currency
            days: Number of days (1, 7, 14, 30, 90, 180, 365, max)
            interval: Data interval (daily for 90+ days)
            
        Returns:
            Dict with prices, market_caps, total_volumes arrays
        """
        params = {
            "vs_currency": vs_currency,
            "days": str(days),
        }
        
        if interval:
            params["interval"] = interval
        
        return self.get(f"/coins/{coin_id}/market_chart", params=params)
    
    def get_coin_market_chart_range(
        self,
        coin_id: str,
        vs_currency: str,
        from_timestamp: int,
        to_timestamp: int,
    ) -> Dict[str, List]:
        """
        Get historical market chart data for a date range.
        
        Args:
            coin_id: Coin ID
            vs_currency: Target currency
            from_timestamp: Start timestamp (Unix)
            to_timestamp: End timestamp (Unix)
            
        Returns:
            Dict with prices, market_caps, total_volumes arrays
        """
        params = {
            "vs_currency": vs_currency,
            "from": from_timestamp,
            "to": to_timestamp,
        }
        
        return self.get(f"/coins/{coin_id}/market_chart/range", params=params)
    
    def get_coin_ohlc(
        self,
        coin_id: str,
        vs_currency: str = "usd",
        days: Union[int, str] = 7,
    ) -> List[List[float]]:
        """
        Get OHLC data for a coin.
        
        Args:
            coin_id: Coin ID
            vs_currency: Target currency
            days: Number of days (1, 7, 14, 30, 90, 180, 365, max)
            
        Returns:
            List of [timestamp, open, high, low, close]
        """
        params = {
            "vs_currency": vs_currency,
            "days": str(days),
        }
        
        return self.get(f"/coins/{coin_id}/ohlc", params=params)
    
    # =========================================================================
    # GLOBAL ENDPOINTS
    # =========================================================================
    
    def get_global(self) -> Dict[str, Any]:
        """
        Get global cryptocurrency market data.
        
        Returns:
            Global market statistics
        """
        return self.get("/global")
    
    def get_global_defi(self) -> Dict[str, Any]:
        """
        Get global DeFi market data.
        
        Returns:
            Global DeFi statistics
        """
        return self.get("/global/decentralized_finance_defi")
    
    # =========================================================================
    # CATEGORIES ENDPOINTS
    # =========================================================================
    
    def get_categories_list(self) -> List[Dict[str, str]]:
        """Get list of all coin categories."""
        return self.get("/coins/categories/list")
    
    def get_categories(
        self,
        order: str = "market_cap_desc",
    ) -> List[Dict[str, Any]]:
        """
        Get categories with market data.
        
        Args:
            order: Sort order
            
        Returns:
            List of categories with market data
        """
        params = {"order": order}
        return self.get("/coins/categories", params=params)
    
    # =========================================================================
    # EXCHANGES ENDPOINTS
    # =========================================================================
    
    def get_exchanges(
        self,
        per_page: int = 100,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Get list of exchanges.
        
        Args:
            per_page: Results per page
            page: Page number
            
        Returns:
            List of exchanges
        """
        params = {
            "per_page": min(per_page, 250),
            "page": page,
        }
        return self.get("/exchanges", params=params)
    
    def get_exchange(self, exchange_id: str) -> Dict[str, Any]:
        """
        Get exchange data.
        
        Args:
            exchange_id: Exchange ID
            
        Returns:
            Exchange data
        """
        return self.get(f"/exchanges/{exchange_id}")
    
    # =========================================================================
    # TRENDING ENDPOINTS
    # =========================================================================
    
    def get_trending(self) -> Dict[str, Any]:
        """
        Get trending search coins.
        
        Returns:
            Trending coins, NFTs, and categories
        """
        return self.get("/search/trending")
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def get_top_coins(
        self,
        n: int = 100,
        vs_currency: str = "usd",
    ) -> List[Dict[str, Any]]:
        """
        Get top N coins by market cap.
        
        Args:
            n: Number of coins to fetch
            vs_currency: Target currency
            
        Returns:
            List of top coins with market data
        """
        all_coins = []
        per_page = min(n, 250)
        pages_needed = (n + per_page - 1) // per_page
        
        for page in range(1, pages_needed + 1):
            coins = self.get_markets(
                vs_currency=vs_currency,
                per_page=per_page,
                page=page,
            )
            all_coins.extend(coins)
            
            if len(all_coins) >= n:
                break
        
        return all_coins[:n]
    
    def get_historical_prices(
        self,
        coin_id: str,
        days: int = 365,
        vs_currency: str = "usd",
    ) -> List[Dict[str, Any]]:
        """
        Get historical daily prices formatted for analysis.
        
        Args:
            coin_id: Coin ID
            days: Number of days
            vs_currency: Target currency
            
        Returns:
            List of price records with date, price, volume, market_cap
        """
        data = self.get_coin_market_chart(
            coin_id=coin_id,
            vs_currency=vs_currency,
            days=days,
            interval="daily" if days > 90 else None,
        )
        
        prices = data.get("prices", [])
        volumes = data.get("total_volumes", [])
        market_caps = data.get("market_caps", [])
        
        result = []
        for i, (timestamp, price) in enumerate(prices):
            record = {
                "timestamp": timestamp,
                "date": timestamp_to_datetime(timestamp),
                "price": price,
                "volume": volumes[i][1] if i < len(volumes) else None,
                "market_cap": market_caps[i][1] if i < len(market_caps) else None,
            }
            result.append(record)
        
        return result
