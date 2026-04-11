"""
FRED (Federal Reserve Economic Data) API Client.

FRED provides access to 800,000+ economic time series from 100+ sources:
- GDP and National Accounts
- Employment and Labor Markets
- Prices and Inflation (CPI, PPI)
- Interest Rates and Financial Markets
- Money Supply and Banking
- International Trade
- Consumer Data
- Regional Data

API Documentation: https://fred.stlouisfed.org/docs/api/fred/
Rate Limits: 120 requests per minute
"""

from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union

from src.ingestion.base_client import BaseAPIClient
from src.ingestion.config import settings
from src.utils.helpers import parse_date


class FREDClient(BaseAPIClient):
    """
    Client for FRED (Federal Reserve Economic Data) API.
    
    Provides methods to fetch:
    - Economic time series data
    - Series metadata and search
    - Release schedules
    - Source information
    
    Key Series IDs:
    - GDP: Gross Domestic Product
    - UNRATE: Unemployment Rate
    - CPIAUCSL: Consumer Price Index
    - FEDFUNDS: Federal Funds Rate
    - DGS10: 10-Year Treasury Yield
    - M2SL: M2 Money Supply
    - SP500: S&P 500 Index
    
    Example:
        client = FREDClient()
        
        # Get GDP data
        gdp = client.get_series('GDP')
        
        # Get CPI with date range
        cpi = client.get_series('CPIAUCSL', start='2020-01-01', end='2024-01-01')
        
        # Search for series
        results = client.search_series('inflation')
    """
    
    # Popular FRED series IDs
    KEY_SERIES = {
        # GDP & Output
        'GDP': 'Gross Domestic Product',
        'GDPC1': 'Real Gross Domestic Product',
        'A191RL1Q225SBEA': 'Real GDP Growth Rate',
        
        # Employment
        'UNRATE': 'Unemployment Rate',
        'PAYEMS': 'Total Nonfarm Payrolls',
        'CIVPART': 'Labor Force Participation Rate',
        'ICSA': 'Initial Claims',
        
        # Prices & Inflation
        'CPIAUCSL': 'Consumer Price Index for All Urban Consumers',
        'CPILFESL': 'Core CPI (Less Food and Energy)',
        'PCEPI': 'PCE Price Index',
        'PCEPILFE': 'Core PCE Price Index',
        'PPIACO': 'Producer Price Index',
        
        # Interest Rates
        'FEDFUNDS': 'Federal Funds Effective Rate',
        'DFF': 'Federal Funds Rate Daily',
        'DGS1': '1-Year Treasury Rate',
        'DGS2': '2-Year Treasury Rate',
        'DGS5': '5-Year Treasury Rate',
        'DGS10': '10-Year Treasury Rate',
        'DGS30': '30-Year Treasury Rate',
        'T10Y2Y': '10-Year Minus 2-Year Treasury (Yield Curve)',
        
        # Money Supply
        'M1SL': 'M1 Money Stock',
        'M2SL': 'M2 Money Stock',
        'BOGMBASE': 'Monetary Base',
        
        # Financial Markets
        'SP500': 'S&P 500',
        'DJIA': 'Dow Jones Industrial Average',
        'NASDAQCOM': 'NASDAQ Composite',
        'VIXCLS': 'CBOE Volatility Index (VIX)',
        
        # Exchange Rates
        'DEXUSEU': 'US Dollar / Euro Exchange Rate',
        'DEXJPUS': 'Japanese Yen / US Dollar',
        'DEXUSUK': 'US Dollar / British Pound',
        'DTWEXBGS': 'Trade Weighted US Dollar Index',
        
        # Commodities
        'DCOILWTICO': 'Crude Oil Prices (WTI)',
        'DCOILBRENTEU': 'Crude Oil Prices (Brent)',
        'GOLDAMGBD228NLBM': 'Gold Fixing Price',
        
        # Housing
        'CSUSHPINSA': 'S&P/Case-Shiller Home Price Index',
        'HOUST': 'Housing Starts',
        'MORTGAGE30US': '30-Year Fixed Rate Mortgage',
        
        # Consumer
        'PCE': 'Personal Consumption Expenditures',
        'RSXFS': 'Retail Sales',
        'UMCSENT': 'Consumer Sentiment',
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize FRED client.
        
        Args:
            api_key: FRED API key (get from https://fred.stlouisfed.org/docs/api/api_key.html)
        """
        super().__init__(
            base_url=settings.FRED_API_URL,
            api_key=api_key or settings.FRED_API_KEY,
            rate_limit=settings.RATE_LIMIT_FRED,
            timeout=30,
            max_retries=3,
            cache_ttl=3600,  # 1 hour cache
        )
    
    def get_source_name(self) -> str:
        """Return source name."""
        return "fred"
    
    def health_check(self) -> bool:
        """Check if FRED API is accessible."""
        try:
            response = self.get("/series", params={
                "series_id": "GDP",
                "api_key": self.api_key,
                "file_type": "json",
            })
            return "seriess" in response
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    def _add_api_key(self, params: Dict) -> Dict:
        """Add API key to request parameters."""
        params = params.copy()
        params["api_key"] = self.api_key
        params["file_type"] = "json"
        return params
    
    # =========================================================================
    # SERIES ENDPOINTS
    # =========================================================================
    
    def get_series(
        self,
        series_id: str,
        start: Optional[Union[str, datetime, date]] = None,
        end: Optional[Union[str, datetime, date]] = None,
        units: str = "lin",
        frequency: Optional[str] = None,
        aggregation_method: str = "avg",
        sort_order: str = "asc",
    ) -> List[Dict[str, Any]]:
        """
        Get observations for a FRED series.
        
        Args:
            series_id: FRED series ID (e.g., 'GDP', 'CPIAUCSL')
            start: Start date
            end: End date
            units: Data units transformation:
                   'lin' = no transformation
                   'chg' = change
                   'ch1' = change from year ago
                   'pch' = percent change
                   'pc1' = percent change from year ago
                   'pca' = compounded annual rate of change
                   'cch' = continuously compounded rate of change
                   'cca' = continuously compounded annual rate of change
                   'log' = natural log
            frequency: Aggregation frequency:
                       'd' = daily, 'w' = weekly, 'bw' = biweekly,
                       'm' = monthly, 'q' = quarterly, 'sa' = semiannual,
                       'a' = annual
            aggregation_method: Aggregation method ('avg', 'sum', 'eop')
            sort_order: 'asc' or 'desc'
            
        Returns:
            List of observations with date and value
        """
        params = {
            "series_id": series_id,
            "units": units,
            "aggregation_method": aggregation_method,
            "sort_order": sort_order,
        }
        
        if start:
            start_dt = parse_date(start)
            if start_dt:
                params["observation_start"] = start_dt.strftime("%Y-%m-%d")
        
        if end:
            end_dt = parse_date(end)
            if end_dt:
                params["observation_end"] = end_dt.strftime("%Y-%m-%d")
        
        if frequency:
            params["frequency"] = frequency
        
        response = self.get("/series/observations", params=self._add_api_key(params))
        observations = response.get("observations", [])
        
        # Parse and clean observations
        result = []
        for obs in observations:
            value = obs.get("value")
            if value and value != ".":
                result.append({
                    "date": obs.get("date"),
                    "value": float(value),
                    "series_id": series_id,
                })
        
        return result
    
    def get_series_info(self, series_id: str) -> Dict[str, Any]:
        """
        Get metadata for a FRED series.
        
        Args:
            series_id: FRED series ID
            
        Returns:
            Series metadata
        """
        params = {"series_id": series_id}
        response = self.get("/series", params=self._add_api_key(params))
        seriess = response.get("seriess", [])
        return seriess[0] if seriess else {}
    
    def get_series_categories(self, series_id: str) -> List[Dict[str, Any]]:
        """
        Get categories for a series.
        
        Args:
            series_id: FRED series ID
            
        Returns:
            List of categories
        """
        params = {"series_id": series_id}
        response = self.get("/series/categories", params=self._add_api_key(params))
        return response.get("categories", [])
    
    def get_series_release(self, series_id: str) -> Dict[str, Any]:
        """
        Get release information for a series.
        
        Args:
            series_id: FRED series ID
            
        Returns:
            Release information
        """
        params = {"series_id": series_id}
        response = self.get("/series/release", params=self._add_api_key(params))
        releases = response.get("releases", [])
        return releases[0] if releases else {}
    
    def get_series_tags(self, series_id: str) -> List[Dict[str, Any]]:
        """
        Get tags for a series.
        
        Args:
            series_id: FRED series ID
            
        Returns:
            List of tags
        """
        params = {"series_id": series_id}
        response = self.get("/series/tags", params=self._add_api_key(params))
        return response.get("tags", [])
    
    def get_series_vintagedates(
        self,
        series_id: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> List[str]:
        """
        Get vintage dates (revision dates) for a series.
        
        Args:
            series_id: FRED series ID
            start: Start date
            end: End date
            
        Returns:
            List of vintage dates
        """
        params = {"series_id": series_id}
        
        if start:
            params["realtime_start"] = start
        if end:
            params["realtime_end"] = end
        
        response = self.get("/series/vintagedates", params=self._add_api_key(params))
        return response.get("vintage_dates", [])
    
    # =========================================================================
    # SEARCH ENDPOINTS
    # =========================================================================
    
    def search_series(
        self,
        search_text: str,
        search_type: str = "full_text",
        limit: int = 100,
        offset: int = 0,
        order_by: str = "search_rank",
        sort_order: str = "desc",
        filter_variable: Optional[str] = None,
        filter_value: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for FRED series.
        
        Args:
            search_text: Search query
            search_type: 'full_text' or 'series_id'
            limit: Maximum results
            offset: Result offset
            order_by: Sort field ('search_rank', 'series_id', 'title',
                      'units', 'frequency', 'seasonal_adjustment',
                      'realtime_start', 'realtime_end', 'last_updated',
                      'observation_start', 'observation_end', 'popularity',
                      'group_popularity')
            sort_order: 'asc' or 'desc'
            filter_variable: Filter field
            filter_value: Filter value
            
        Returns:
            List of matching series
        """
        params = {
            "search_text": search_text,
            "search_type": search_type,
            "limit": min(limit, 1000),
            "offset": offset,
            "order_by": order_by,
            "sort_order": sort_order,
        }
        
        if filter_variable and filter_value:
            params["filter_variable"] = filter_variable
            params["filter_value"] = filter_value
        
        response = self.get("/series/search", params=self._add_api_key(params))
        return response.get("seriess", [])
    
    def search_series_tags(
        self,
        series_search_text: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Search for tags related to a series search.
        
        Args:
            series_search_text: Series search query
            limit: Maximum results
            
        Returns:
            List of related tags
        """
        params = {
            "series_search_text": series_search_text,
            "limit": min(limit, 1000),
        }
        
        response = self.get("/series/search/tags", params=self._add_api_key(params))
        return response.get("tags", [])
    
    # =========================================================================
    # RELEASES ENDPOINTS
    # =========================================================================
    
    def get_releases(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get all releases.
        
        Args:
            limit: Maximum results
            offset: Result offset
            
        Returns:
            List of releases
        """
        params = {
            "limit": min(limit, 1000),
            "offset": offset,
        }
        
        response = self.get("/releases", params=self._add_api_key(params))
        return response.get("releases", [])
    
    def get_release(self, release_id: int) -> Dict[str, Any]:
        """
        Get a specific release.
        
        Args:
            release_id: Release ID
            
        Returns:
            Release information
        """
        params = {"release_id": release_id}
        response = self.get("/release", params=self._add_api_key(params))
        releases = response.get("releases", [])
        return releases[0] if releases else {}
    
    def get_release_dates(
        self,
        release_id: int,
        include_release_dates_with_no_data: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get release dates for a release.
        
        Args:
            release_id: Release ID
            include_release_dates_with_no_data: Include dates without data
            
        Returns:
            List of release dates
        """
        params = {
            "release_id": release_id,
            "include_release_dates_with_no_data": str(include_release_dates_with_no_data).lower(),
        }
        
        response = self.get("/release/dates", params=self._add_api_key(params))
        return response.get("release_dates", [])
    
    def get_release_series(
        self,
        release_id: int,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get series for a release.
        
        Args:
            release_id: Release ID
            limit: Maximum results
            
        Returns:
            List of series in the release
        """
        params = {
            "release_id": release_id,
            "limit": min(limit, 1000),
        }
        
        response = self.get("/release/series", params=self._add_api_key(params))
        return response.get("seriess", [])
    
    # =========================================================================
    # CATEGORIES ENDPOINTS
    # =========================================================================
    
    def get_category(self, category_id: int = 0) -> Dict[str, Any]:
        """
        Get a category.
        
        Args:
            category_id: Category ID (0 for root)
            
        Returns:
            Category information
        """
        params = {"category_id": category_id}
        response = self.get("/category", params=self._add_api_key(params))
        categories = response.get("categories", [])
        return categories[0] if categories else {}
    
    def get_category_children(
        self,
        category_id: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get child categories.
        
        Args:
            category_id: Parent category ID (0 for root)
            
        Returns:
            List of child categories
        """
        params = {"category_id": category_id}
        response = self.get("/category/children", params=self._add_api_key(params))
        return response.get("categories", [])
    
    def get_category_series(
        self,
        category_id: int,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get series in a category.
        
        Args:
            category_id: Category ID
            limit: Maximum results
            
        Returns:
            List of series in the category
        """
        params = {
            "category_id": category_id,
            "limit": min(limit, 1000),
        }
        
        response = self.get("/category/series", params=self._add_api_key(params))
        return response.get("seriess", [])
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def get_multiple_series(
        self,
        series_ids: List[str],
        start: Optional[str] = None,
        end: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get data for multiple series.
        
        Args:
            series_ids: List of series IDs
            start: Start date
            end: End date
            **kwargs: Additional arguments passed to get_series
            
        Returns:
            Dict mapping series IDs to their observations
        """
        result = {}
        for series_id in series_ids:
            try:
                data = self.get_series(series_id, start=start, end=end, **kwargs)
                result[series_id] = data
            except Exception as e:
                self.logger.error(f"Failed to fetch {series_id}: {e}")
                result[series_id] = []
        
        return result
    
    def get_key_indicators(
        self,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get data for all key economic indicators.
        
        Args:
            start: Start date
            end: End date
            
        Returns:
            Dict mapping series IDs to their observations
        """
        key_ids = [
            'GDP', 'GDPC1', 'UNRATE', 'CPIAUCSL', 'FEDFUNDS',
            'DGS10', 'M2SL', 'SP500', 'DCOILWTICO', 'GOLDAMGBD228NLBM',
        ]
        
        return self.get_multiple_series(key_ids, start=start, end=end)
    
    def get_latest_values(
        self,
        series_ids: Optional[List[str]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get latest values for multiple series.
        
        Args:
            series_ids: List of series IDs (defaults to key indicators)
            
        Returns:
            Dict mapping series IDs to their latest observation
        """
        if series_ids is None:
            series_ids = list(self.KEY_SERIES.keys())[:20]
        
        result = {}
        for series_id in series_ids:
            try:
                data = self.get_series(series_id, sort_order="desc")
                if data:
                    result[series_id] = {
                        "name": self.KEY_SERIES.get(series_id, series_id),
                        **data[0],
                    }
            except Exception as e:
                self.logger.error(f"Failed to fetch latest {series_id}: {e}")
        
        return result
