"""
World Bank API Client for international economic data.

The World Bank provides data for 200+ countries with 1400+ indicators:
- GDP and Economic Growth
- Population and Demographics
- Health and Education
- Trade and Finance
- Environment and Energy
- Poverty and Inequality

API Documentation: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
Rate Limits: No strict limits, but be reasonable
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from src.ingestion.base_client import BaseAPIClient
from src.ingestion.config import settings


class WorldBankClient(BaseAPIClient):
    """
    Client for World Bank Open Data API.
    
    Provides methods to fetch:
    - Country data and metadata
    - Indicator data and metadata
    - Time series data by country/indicator
    
    Key Indicators:
    - NY.GDP.MKTP.CD: GDP (current US$)
    - NY.GDP.MKTP.KD.ZG: GDP growth (annual %)
    - FP.CPI.TOTL.ZG: Inflation, consumer prices (annual %)
    - SL.UEM.TOTL.ZS: Unemployment rate (%)
    - NE.TRD.GNFS.ZS: Trade (% of GDP)
    
    Example:
        client = WorldBankClient()
        
        # Get GDP data for US
        gdp = client.get_indicator_data('NY.GDP.MKTP.CD', country='US')
        
        # Get inflation for multiple countries
        inflation = client.get_indicator_data(
            'FP.CPI.TOTL.ZG',
            country=['US', 'GB', 'DE', 'JP']
        )
    """
    
    # Key World Bank indicators
    KEY_INDICATORS = {
        # GDP and Growth
        'NY.GDP.MKTP.CD': 'GDP (current US$)',
        'NY.GDP.MKTP.KD.ZG': 'GDP growth (annual %)',
        'NY.GDP.PCAP.CD': 'GDP per capita (current US$)',
        'NY.GDP.PCAP.KD.ZG': 'GDP per capita growth (annual %)',
        'NV.IND.MANF.ZS': 'Manufacturing, value added (% of GDP)',
        
        # Prices and Inflation
        'FP.CPI.TOTL.ZG': 'Inflation, consumer prices (annual %)',
        'FP.CPI.TOTL': 'Consumer price index (2010 = 100)',
        
        # Employment
        'SL.UEM.TOTL.ZS': 'Unemployment, total (% of labor force)',
        'SL.UEM.TOTL.NE.ZS': 'Unemployment rate (national estimate)',
        'SL.TLF.TOTL.IN': 'Labor force, total',
        'SL.TLF.CACT.ZS': 'Labor force participation rate (%)',
        
        # Trade
        'NE.TRD.GNFS.ZS': 'Trade (% of GDP)',
        'NE.EXP.GNFS.ZS': 'Exports of goods and services (% of GDP)',
        'NE.IMP.GNFS.ZS': 'Imports of goods and services (% of GDP)',
        'BX.KLT.DINV.WD.GD.ZS': 'Foreign direct investment (% of GDP)',
        
        # Finance
        'GC.DOD.TOTL.GD.ZS': 'Central government debt (% of GDP)',
        'GC.REV.XGRT.GD.ZS': 'Revenue (% of GDP)',
        'GC.XPN.TOTL.GD.ZS': 'Expense (% of GDP)',
        'BN.CAB.XOKA.GD.ZS': 'Current account balance (% of GDP)',
        
        # Population
        'SP.POP.TOTL': 'Population, total',
        'SP.POP.GROW': 'Population growth (annual %)',
        'SP.URB.TOTL.IN.ZS': 'Urban population (% of total)',
        
        # Development
        'SI.POV.GINI': 'Gini index',
        'NY.GNP.PCAP.CD': 'GNI per capita (current US$)',
        'HD.HCI.OVRL': 'Human Capital Index',
    }
    
    # Major country codes
    MAJOR_ECONOMIES = ['US', 'CN', 'JP', 'DE', 'GB', 'FR', 'IN', 'IT', 'BR', 'CA']
    
    def __init__(self):
        """Initialize World Bank client."""
        super().__init__(
            base_url=settings.WORLDBANK_API_URL,
            api_key=None,  # No API key required
            rate_limit=settings.RATE_LIMIT_WORLDBANK,
            timeout=30,
            max_retries=3,
            cache_ttl=3600,  # 1 hour cache
        )
    
    def get_source_name(self) -> str:
        """Return source name."""
        return "worldbank"
    
    def health_check(self) -> bool:
        """Check if World Bank API is accessible."""
        try:
            response = self.get("/countries", params={"format": "json", "per_page": 1})
            return len(response) > 1 and response[1] is not None
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    def _parse_response(self, response: Any) -> List[Dict[str, Any]]:
        """
        Parse World Bank API response.
        
        World Bank returns [metadata, data] format.
        """
        if isinstance(response, list) and len(response) > 1:
            return response[1] if response[1] else []
        return []
    
    # =========================================================================
    # COUNTRIES ENDPOINTS
    # =========================================================================
    
    def get_countries(
        self,
        per_page: int = 100,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Get list of all countries.
        
        Args:
            per_page: Results per page
            page: Page number
            
        Returns:
            List of countries with metadata
        """
        params = {
            "format": "json",
            "per_page": per_page,
            "page": page,
        }
        
        response = self.get("/countries", params=params)
        return self._parse_response(response)
    
    def get_country(self, country_code: str) -> Dict[str, Any]:
        """
        Get country information.
        
        Args:
            country_code: ISO 2-letter country code
            
        Returns:
            Country metadata
        """
        params = {"format": "json"}
        response = self.get(f"/countries/{country_code}", params=params)
        data = self._parse_response(response)
        return data[0] if data else {}
    
    # =========================================================================
    # INDICATORS ENDPOINTS
    # =========================================================================
    
    def get_indicators(
        self,
        per_page: int = 100,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Get list of all indicators.
        
        Args:
            per_page: Results per page
            page: Page number
            
        Returns:
            List of indicators with metadata
        """
        params = {
            "format": "json",
            "per_page": per_page,
            "page": page,
        }
        
        response = self.get("/indicators", params=params)
        return self._parse_response(response)
    
    def get_indicator(self, indicator_id: str) -> Dict[str, Any]:
        """
        Get indicator information.
        
        Args:
            indicator_id: Indicator code
            
        Returns:
            Indicator metadata
        """
        params = {"format": "json"}
        response = self.get(f"/indicators/{indicator_id}", params=params)
        data = self._parse_response(response)
        return data[0] if data else {}
    
    def search_indicators(
        self,
        query: str,
        per_page: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Search for indicators.
        
        Args:
            query: Search query
            per_page: Results per page
            
        Returns:
            List of matching indicators
        """
        # World Bank doesn't have a search endpoint, so we get all and filter
        all_indicators = []
        page = 1
        
        while True:
            indicators = self.get_indicators(per_page=1000, page=page)
            if not indicators:
                break
            
            all_indicators.extend(indicators)
            
            if len(indicators) < 1000:
                break
            page += 1
        
        # Filter by query
        query_lower = query.lower()
        matches = [
            ind for ind in all_indicators
            if query_lower in ind.get('name', '').lower()
            or query_lower in ind.get('id', '').lower()
        ]
        
        return matches[:per_page]
    
    # =========================================================================
    # DATA ENDPOINTS
    # =========================================================================
    
    def get_indicator_data(
        self,
        indicator_id: str,
        country: Optional[Union[str, List[str]]] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        per_page: int = 1000,
        mrv: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get indicator data for country(ies).
        
        Args:
            indicator_id: Indicator code
            country: Country code(s) or 'all'
            start_year: Start year
            end_year: End year
            per_page: Results per page
            mrv: Most recent values to return
            
        Returns:
            List of data observations
        """
        if country is None:
            country = "all"
        elif isinstance(country, list):
            country = ";".join(country)
        
        params = {
            "format": "json",
            "per_page": per_page,
        }
        
        if start_year and end_year:
            params["date"] = f"{start_year}:{end_year}"
        elif mrv:
            params["mrv"] = mrv
        
        endpoint = f"/countries/{country}/indicators/{indicator_id}"
        response = self.get(endpoint, params=params)
        data = self._parse_response(response)
        
        # Parse and clean data
        result = []
        for item in data:
            if item.get("value") is not None:
                result.append({
                    "country_id": item.get("country", {}).get("id"),
                    "country_name": item.get("country", {}).get("value"),
                    "indicator_id": item.get("indicator", {}).get("id"),
                    "indicator_name": item.get("indicator", {}).get("value"),
                    "year": int(item.get("date")) if item.get("date") else None,
                    "value": float(item.get("value")) if item.get("value") else None,
                    "decimal": item.get("decimal"),
                })
        
        return result
    
    def get_country_data(
        self,
        country_code: str,
        indicators: Optional[List[str]] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get multiple indicators for a country.
        
        Args:
            country_code: Country code
            indicators: List of indicator IDs (defaults to key indicators)
            start_year: Start year
            end_year: End year
            
        Returns:
            Dict mapping indicators to their data
        """
        if indicators is None:
            indicators = list(self.KEY_INDICATORS.keys())[:10]
        
        result = {}
        for indicator_id in indicators:
            try:
                data = self.get_indicator_data(
                    indicator_id,
                    country=country_code,
                    start_year=start_year,
                    end_year=end_year,
                )
                result[indicator_id] = data
            except Exception as e:
                self.logger.error(f"Failed to fetch {indicator_id} for {country_code}: {e}")
                result[indicator_id] = []
        
        return result
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def get_gdp_data(
        self,
        countries: Optional[List[str]] = None,
        start_year: int = 2000,
        end_year: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get GDP data for countries.
        
        Args:
            countries: List of country codes (defaults to major economies)
            start_year: Start year
            end_year: End year
            
        Returns:
            GDP data for all countries
        """
        if countries is None:
            countries = self.MAJOR_ECONOMIES
        if end_year is None:
            end_year = datetime.now().year
        
        return self.get_indicator_data(
            'NY.GDP.MKTP.CD',
            country=countries,
            start_year=start_year,
            end_year=end_year,
        )
    
    def get_inflation_data(
        self,
        countries: Optional[List[str]] = None,
        start_year: int = 2000,
        end_year: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get inflation data for countries.
        
        Args:
            countries: List of country codes
            start_year: Start year
            end_year: End year
            
        Returns:
            Inflation data for all countries
        """
        if countries is None:
            countries = self.MAJOR_ECONOMIES
        if end_year is None:
            end_year = datetime.now().year
        
        return self.get_indicator_data(
            'FP.CPI.TOTL.ZG',
            country=countries,
            start_year=start_year,
            end_year=end_year,
        )
    
    def get_unemployment_data(
        self,
        countries: Optional[List[str]] = None,
        start_year: int = 2000,
        end_year: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get unemployment data for countries.
        
        Args:
            countries: List of country codes
            start_year: Start year
            end_year: End year
            
        Returns:
            Unemployment data for all countries
        """
        if countries is None:
            countries = self.MAJOR_ECONOMIES
        if end_year is None:
            end_year = datetime.now().year
        
        return self.get_indicator_data(
            'SL.UEM.TOTL.ZS',
            country=countries,
            start_year=start_year,
            end_year=end_year,
        )
    
    def get_latest_indicators(
        self,
        country_code: str = 'US',
        indicators: Optional[List[str]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get latest values for multiple indicators.
        
        Args:
            country_code: Country code
            indicators: List of indicator IDs
            
        Returns:
            Dict mapping indicators to their latest values
        """
        if indicators is None:
            indicators = list(self.KEY_INDICATORS.keys())[:15]
        
        result = {}
        for indicator_id in indicators:
            try:
                data = self.get_indicator_data(
                    indicator_id,
                    country=country_code,
                    mrv=1,
                )
                if data:
                    result[indicator_id] = {
                        "name": self.KEY_INDICATORS.get(indicator_id, indicator_id),
                        **data[0],
                    }
            except Exception as e:
                self.logger.error(f"Failed to fetch {indicator_id}: {e}")
        
        return result
    
    def compare_countries(
        self,
        indicator_id: str,
        countries: List[str],
        year: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Compare indicator values across countries.
        
        Args:
            indicator_id: Indicator code
            countries: List of country codes
            year: Year for comparison (latest if not specified)
            
        Returns:
            Comparison data sorted by value
        """
        if year:
            data = self.get_indicator_data(
                indicator_id,
                country=countries,
                start_year=year,
                end_year=year,
            )
        else:
            data = self.get_indicator_data(
                indicator_id,
                country=countries,
                mrv=1,
            )
        
        # Sort by value descending
        return sorted(data, key=lambda x: x.get("value", 0) or 0, reverse=True)
