"""
CryptoCompare API Client for historical cryptocurrency data.

CryptoCompare provides:
- Historical OHLCV data (minute, hour, day)
- Social stats and developer activity
- Exchange volume data
- News and analysis
- Mining data

API Documentation: https://min-api.cryptocompare.com/documentation
Rate Limits: Free tier - 100k calls/month
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from src.ingestion.base_client import BaseAPIClient
from src.ingestion.config import settings
from src.utils.helpers import timestamp_to_datetime, datetime_to_timestamp


class CryptoCompareClient(BaseAPIClient):
    """
    Client for CryptoCompare cryptocurrency data API.
    
    Provides methods to fetch:
    - Historical OHLCV data at various intervals
    - Social media stats
    - Exchange data
    - News articles
    
    Example:
        client = CryptoCompareClient()
        
        # Get daily historical data
        data = client.get_historical_daily('BTC', 'USD', limit=365)
        
        # Get hourly data
        data = client.get_historical_hourly('ETH', 'USD', limit=24)
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize CryptoCompare client.
        
        Args:
            api_key: CryptoCompare API key
        """
        super().__init__(
            base_url=settings.CRYPTOCOMPARE_API_URL,
            api_key=api_key or settings.CRYPTOCOMPARE_API_KEY,
            rate_limit=50,  # Conservative rate limit
            timeout=30,
            max_retries=3,
            cache_ttl=300,  # 5 minutes cache
        )
    
    def _get_headers(self) -> Dict[str, str]:
        """Override headers for CryptoCompare API."""
        headers = super()._get_headers()
        
        if self.api_key:
            headers["authorization"] = f"Apikey {self.api_key}"
            del headers["Authorization"]
        
        return headers
    
    def get_source_name(self) -> str:
        """Return source name."""
        return "cryptocompare"
    
    def health_check(self) -> bool:
        """Check if CryptoCompare API is accessible."""
        try:
            response = self.get("/price", params={"fsym": "BTC", "tsyms": "USD"})
            return "USD" in response
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    # =========================================================================
    # PRICE ENDPOINTS
    # =========================================================================
    
    def get_price(
        self,
        fsym: str,
        tsyms: Union[str, List[str]],
        exchanges: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        """
        Get current price of a symbol.
        
        Args:
            fsym: From symbol (e.g., 'BTC')
            tsyms: To symbol(s) (e.g., 'USD' or ['USD', 'EUR'])
            exchanges: Specific exchanges to use
            
        Returns:
            Dict mapping target currencies to prices
        """
        if isinstance(tsyms, list):
            tsyms = ",".join(tsyms)
        
        params = {"fsym": fsym.upper(), "tsyms": tsyms.upper()}
        
        if exchanges:
            params["e"] = ",".join(exchanges)
        
        return self.get("/price", params=params)
    
    def get_price_multi(
        self,
        fsyms: List[str],
        tsyms: Union[str, List[str]],
    ) -> Dict[str, Dict[str, float]]:
        """
        Get current prices for multiple symbols.
        
        Args:
            fsyms: From symbols (e.g., ['BTC', 'ETH'])
            tsyms: To symbol(s) (e.g., 'USD' or ['USD', 'EUR'])
            
        Returns:
            Nested dict mapping symbols to currency prices
        """
        if isinstance(tsyms, list):
            tsyms = ",".join(tsyms)
        
        params = {
            "fsyms": ",".join([s.upper() for s in fsyms]),
            "tsyms": tsyms.upper(),
        }
        
        return self.get("/pricemulti", params=params)
    
    def get_price_full(
        self,
        fsyms: Union[str, List[str]],
        tsyms: Union[str, List[str]],
    ) -> Dict[str, Any]:
        """
        Get full price data including market info.
        
        Args:
            fsyms: From symbol(s)
            tsyms: To symbol(s)
            
        Returns:
            Full price data with RAW and DISPLAY formats
        """
        if isinstance(fsyms, list):
            fsyms = ",".join(fsyms)
        if isinstance(tsyms, list):
            tsyms = ",".join(tsyms)
        
        params = {"fsyms": fsyms.upper(), "tsyms": tsyms.upper()}
        
        return self.get("/pricemultifull", params=params)
    
    # =========================================================================
    # HISTORICAL DATA ENDPOINTS
    # =========================================================================
    
    def get_historical_minute(
        self,
        fsym: str,
        tsym: str = "USD",
        limit: int = 60,
        to_ts: Optional[int] = None,
        exchange: Optional[str] = None,
        aggregate: int = 1,
    ) -> Dict[str, Any]:
        """
        Get minute-level historical OHLCV data.
        
        Args:
            fsym: From symbol (e.g., 'BTC')
            tsym: To symbol (e.g., 'USD')
            limit: Number of data points (max 2000)
            to_ts: End timestamp
            exchange: Specific exchange
            aggregate: Aggregation period
            
        Returns:
            Historical data with Response and Data fields
        """
        params = {
            "fsym": fsym.upper(),
            "tsym": tsym.upper(),
            "limit": min(limit, 2000),
            "aggregate": aggregate,
        }
        
        if to_ts:
            params["toTs"] = to_ts
        if exchange:
            params["e"] = exchange
        
        return self.get("/v2/histominute", params=params)
    
    def get_historical_hourly(
        self,
        fsym: str,
        tsym: str = "USD",
        limit: int = 24,
        to_ts: Optional[int] = None,
        exchange: Optional[str] = None,
        aggregate: int = 1,
    ) -> Dict[str, Any]:
        """
        Get hourly historical OHLCV data.
        
        Args:
            fsym: From symbol
            tsym: To symbol
            limit: Number of data points (max 2000)
            to_ts: End timestamp
            exchange: Specific exchange
            aggregate: Aggregation period
            
        Returns:
            Historical data with Response and Data fields
        """
        params = {
            "fsym": fsym.upper(),
            "tsym": tsym.upper(),
            "limit": min(limit, 2000),
            "aggregate": aggregate,
        }
        
        if to_ts:
            params["toTs"] = to_ts
        if exchange:
            params["e"] = exchange
        
        return self.get("/v2/histohour", params=params)
    
    def get_historical_daily(
        self,
        fsym: str,
        tsym: str = "USD",
        limit: int = 30,
        to_ts: Optional[int] = None,
        exchange: Optional[str] = None,
        aggregate: int = 1,
        all_data: bool = False,
    ) -> Dict[str, Any]:
        """
        Get daily historical OHLCV data.
        
        Args:
            fsym: From symbol
            tsym: To symbol
            limit: Number of data points (max 2000)
            to_ts: End timestamp
            exchange: Specific exchange
            aggregate: Aggregation period
            all_data: Get all available data
            
        Returns:
            Historical data with Response and Data fields
        """
        params = {
            "fsym": fsym.upper(),
            "tsym": tsym.upper(),
            "limit": min(limit, 2000),
            "aggregate": aggregate,
        }
        
        if to_ts:
            params["toTs"] = to_ts
        if exchange:
            params["e"] = exchange
        if all_data:
            params["allData"] = "true"
        
        return self.get("/v2/histoday", params=params)
    
    # =========================================================================
    # SOCIAL & STATS ENDPOINTS
    # =========================================================================
    
    def get_social_stats(self, coin_id: int) -> Dict[str, Any]:
        """
        Get social stats for a coin.
        
        Args:
            coin_id: CryptoCompare coin ID
            
        Returns:
            Social stats data
        """
        params = {"coinId": coin_id}
        return self.get("/social/coin/latest", params=params)
    
    def get_social_stats_historical(
        self,
        coin_id: int,
        limit: int = 30,
        to_ts: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get historical social stats.
        
        Args:
            coin_id: CryptoCompare coin ID
            limit: Number of data points
            to_ts: End timestamp
            
        Returns:
            Historical social stats
        """
        params = {"coinId": coin_id, "limit": limit}
        
        if to_ts:
            params["toTs"] = to_ts
        
        return self.get("/social/coin/histo/day", params=params)
    
    # =========================================================================
    # TOP LISTS ENDPOINTS
    # =========================================================================
    
    def get_top_by_volume(
        self,
        tsym: str = "USD",
        limit: int = 50,
        page: int = 0,
    ) -> Dict[str, Any]:
        """
        Get top coins by total volume.
        
        Args:
            tsym: Target currency
            limit: Number of results
            page: Page number
            
        Returns:
            Top coins by volume
        """
        params = {
            "tsym": tsym.upper(),
            "limit": limit,
            "page": page,
        }
        
        return self.get("/top/totalvolfull", params=params)
    
    def get_top_by_market_cap(
        self,
        tsym: str = "USD",
        limit: int = 50,
        page: int = 0,
    ) -> Dict[str, Any]:
        """
        Get top coins by market cap.
        
        Args:
            tsym: Target currency
            limit: Number of results
            page: Page number
            
        Returns:
            Top coins by market cap
        """
        params = {
            "tsym": tsym.upper(),
            "limit": limit,
            "page": page,
        }
        
        return self.get("/top/mktcapfull", params=params)
    
    def get_top_exchanges(
        self,
        fsym: str,
        tsym: str = "USD",
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Get top exchanges for a trading pair.
        
        Args:
            fsym: From symbol
            tsym: To symbol
            limit: Number of results
            
        Returns:
            Top exchanges by volume
        """
        params = {
            "fsym": fsym.upper(),
            "tsym": tsym.upper(),
            "limit": limit,
        }
        
        return self.get("/top/exchanges", params=params)
    
    # =========================================================================
    # NEWS ENDPOINTS
    # =========================================================================
    
    def get_news(
        self,
        categories: Optional[List[str]] = None,
        feeds: Optional[List[str]] = None,
        lang: str = "EN",
    ) -> Dict[str, Any]:
        """
        Get latest crypto news.
        
        Args:
            categories: Filter by categories
            feeds: Filter by news sources
            lang: Language code
            
        Returns:
            Latest news articles
        """
        params = {"lang": lang}
        
        if categories:
            params["categories"] = ",".join(categories)
        if feeds:
            params["feeds"] = ",".join(feeds)
        
        # News endpoint is at different base
        response = self.get("/v2/news/", params=params)
        return response
    
    # =========================================================================
    # COIN LIST ENDPOINTS
    # =========================================================================
    
    def get_coin_list(self) -> Dict[str, Dict[str, Any]]:
        """
        Get list of all coins with metadata.
        
        Returns:
            Dict mapping symbols to coin info
        """
        return self.get("/all/coinlist")
    
    def get_coin_snapshot(self, fsym: str, tsym: str = "USD") -> Dict[str, Any]:
        """
        Get full coin snapshot/summary.
        
        Args:
            fsym: From symbol
            tsym: To symbol
            
        Returns:
            Complete coin data snapshot
        """
        params = {"fsym": fsym.upper(), "tsym": tsym.upper()}
        return self.get("/top/exchanges/full", params=params)
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def get_ohlcv_dataframe(
        self,
        fsym: str,
        tsym: str = "USD",
        period: str = "day",
        limit: int = 365,
    ) -> List[Dict[str, Any]]:
        """
        Get OHLCV data formatted for analysis.
        
        Args:
            fsym: From symbol
            tsym: To symbol
            period: 'minute', 'hour', or 'day'
            limit: Number of data points
            
        Returns:
            List of OHLCV records
        """
        if period == "minute":
            response = self.get_historical_minute(fsym, tsym, limit)
        elif period == "hour":
            response = self.get_historical_hourly(fsym, tsym, limit)
        else:
            response = self.get_historical_daily(fsym, tsym, limit)
        
        data = response.get("Data", {}).get("Data", [])
        
        result = []
        for item in data:
            record = {
                "timestamp": item.get("time"),
                "datetime": timestamp_to_datetime(item.get("time")),
                "open": item.get("open"),
                "high": item.get("high"),
                "low": item.get("low"),
                "close": item.get("close"),
                "volume_from": item.get("volumefrom"),
                "volume_to": item.get("volumeto"),
            }
            result.append(record)
        
        return result
