"""
Fear & Greed Index API Client for crypto market sentiment.

The Fear & Greed Index measures market sentiment on a scale of 0-100:
- 0-24: Extreme Fear
- 25-49: Fear
- 50: Neutral
- 51-74: Greed
- 75-100: Extreme Greed

Data sources for the index:
- Volatility (25%)
- Market Momentum/Volume (25%)
- Social Media (15%)
- Surveys (15%)
- Dominance (10%)
- Trends (10%)

API Documentation: https://alternative.me/crypto/fear-and-greed-index/
Rate Limits: No strict limits
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.ingestion.base_client import BaseAPIClient
from src.ingestion.config import settings
from src.utils.helpers import timestamp_to_datetime


class FearGreedClient(BaseAPIClient):
    """
    Client for Fear & Greed Index API.
    
    Provides methods to fetch:
    - Current sentiment index
    - Historical sentiment data
    - Sentiment classification
    
    Example:
        client = FearGreedClient()
        
        # Get current index
        current = client.get_current()
        print(f"Fear & Greed: {current['value']} ({current['classification']})")
        
        # Get historical data
        history = client.get_history(limit=30)
    """
    
    # Sentiment classifications
    CLASSIFICATIONS = {
        "extreme_fear": (0, 24),
        "fear": (25, 49),
        "neutral": (50, 50),
        "greed": (51, 74),
        "extreme_greed": (75, 100),
    }
    
    def __init__(self):
        """Initialize Fear & Greed client."""
        super().__init__(
            base_url=settings.FEAR_GREED_URL,
            api_key=None,  # No API key required
            rate_limit=30,  # Conservative rate limit
            timeout=30,
            max_retries=3,
            cache_ttl=3600,  # 1 hour cache (updates daily)
        )
    
    def get_source_name(self) -> str:
        """Return source name."""
        return "fear_greed"
    
    def health_check(self) -> bool:
        """Check if Fear & Greed API is accessible."""
        try:
            response = self.get("/", params={"limit": 1})
            return "data" in response
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Override to handle API response structure."""
        # The base URL already includes the endpoint
        if endpoint == "/":
            endpoint = ""
        
        return super()._make_request(
            method, endpoint, params, data, headers, use_cache
        )
    
    # =========================================================================
    # MAIN ENDPOINTS
    # =========================================================================
    
    def get_index(
        self,
        limit: int = 1,
        format: str = "json",
        date_format: str = "world",
    ) -> Dict[str, Any]:
        """
        Get Fear & Greed Index data.
        
        Args:
            limit: Number of data points (default 1 for current)
            format: Response format ('json' or 'csv')
            date_format: Date format ('us', 'cn', 'kr', 'world')
            
        Returns:
            Fear & Greed Index data
        """
        params = {
            "limit": limit,
            "format": format,
            "date_format": date_format,
        }
        
        return self.get("/", params=params)
    
    def get_current(self) -> Dict[str, Any]:
        """
        Get current Fear & Greed Index value.
        
        Returns:
            Current index data with value and classification
        """
        response = self.get_index(limit=1)
        data = response.get("data", [])
        
        if not data:
            return {}
        
        current = data[0]
        return self._parse_index_data(current)
    
    def get_history(
        self,
        limit: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Get historical Fear & Greed Index data.
        
        Args:
            limit: Number of days to fetch
            
        Returns:
            List of historical index data
        """
        response = self.get_index(limit=limit)
        data = response.get("data", [])
        
        return [self._parse_index_data(item) for item in data]
    
    def get_all_history(self) -> List[Dict[str, Any]]:
        """
        Get complete historical Fear & Greed Index data.
        
        Returns:
            All available historical data
        """
        # Request a large limit to get all data
        return self.get_history(limit=10000)
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _parse_index_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse raw index data into standardized format.
        
        Args:
            data: Raw index data point
            
        Returns:
            Parsed index data
        """
        value = int(data.get("value", 0))
        timestamp = int(data.get("timestamp", 0))
        
        return {
            "value": value,
            "classification": data.get("value_classification", ""),
            "timestamp": timestamp,
            "datetime": timestamp_to_datetime(timestamp),
            "time_until_update": data.get("time_until_update", ""),
            "sentiment_score": self._normalize_score(value),
        }
    
    def _normalize_score(self, value: int) -> float:
        """
        Normalize score to -1 to 1 range.
        
        Args:
            value: Raw index value (0-100)
            
        Returns:
            Normalized score (-1 to 1, where -1 is extreme fear, 1 is extreme greed)
        """
        return (value - 50) / 50
    
    @staticmethod
    def classify_value(value: int) -> str:
        """
        Classify index value into sentiment category.
        
        Args:
            value: Index value (0-100)
            
        Returns:
            Sentiment classification
        """
        if value <= 24:
            return "Extreme Fear"
        elif value <= 49:
            return "Fear"
        elif value == 50:
            return "Neutral"
        elif value <= 74:
            return "Greed"
        else:
            return "Extreme Greed"
    
    @staticmethod
    def get_trading_signal(value: int) -> str:
        """
        Get a simple trading signal based on index value.
        
        Contrarian strategy: Buy when fearful, sell when greedy.
        
        Args:
            value: Index value (0-100)
            
        Returns:
            Trading signal
        """
        if value <= 20:
            return "Strong Buy Signal"
        elif value <= 35:
            return "Buy Signal"
        elif value <= 65:
            return "Hold"
        elif value <= 80:
            return "Sell Signal"
        else:
            return "Strong Sell Signal"
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive Fear & Greed summary.
        
        Returns:
            Summary with current value, trend, and analysis
        """
        history = self.get_history(limit=30)
        
        if not history:
            return {}
        
        current = history[0]
        values = [h["value"] for h in history]
        
        # Calculate statistics
        avg_7d = sum(values[:7]) / min(7, len(values))
        avg_30d = sum(values) / len(values)
        
        # Determine trend
        if len(values) >= 7:
            recent_avg = sum(values[:3]) / 3
            earlier_avg = sum(values[4:7]) / 3
            trend = "improving" if recent_avg > earlier_avg else "declining"
        else:
            trend = "unknown"
        
        return {
            "current_value": current["value"],
            "current_classification": current["classification"],
            "trading_signal": self.get_trading_signal(current["value"]),
            "avg_7d": round(avg_7d, 1),
            "avg_30d": round(avg_30d, 1),
            "trend_7d": trend,
            "min_30d": min(values),
            "max_30d": max(values),
            "last_update": current["datetime"],
            "history": history[:7],  # Last 7 days
        }
    
    def get_extreme_events(
        self,
        threshold_fear: int = 20,
        threshold_greed: int = 80,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get historical extreme fear and greed events.
        
        Args:
            threshold_fear: Fear threshold (below this = extreme)
            threshold_greed: Greed threshold (above this = extreme)
            
        Returns:
            Dict with extreme_fear and extreme_greed events
        """
        history = self.get_all_history()
        
        extreme_fear = [
            h for h in history
            if h["value"] <= threshold_fear
        ]
        
        extreme_greed = [
            h for h in history
            if h["value"] >= threshold_greed
        ]
        
        return {
            "extreme_fear": extreme_fear,
            "extreme_greed": extreme_greed,
            "fear_count": len(extreme_fear),
            "greed_count": len(extreme_greed),
        }
