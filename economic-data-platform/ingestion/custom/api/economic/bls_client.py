"""
BLS (Bureau of Labor Statistics) API Client.

BLS provides data on:
- Employment and unemployment
- Consumer Price Index (CPI)
- Producer Price Index (PPI)
- Wages and earnings
- Productivity
- Import/Export prices

API Documentation: https://www.bls.gov/developers/
Rate Limits: 
- Without key: 25 requests/day, 10 years of data
- With key: 500 requests/day, 20 years of data
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from src.ingestion.base_client import BaseAPIClient
from src.ingestion.config import settings


class BLSClient(BaseAPIClient):
    """
    Client for Bureau of Labor Statistics API.
    
    Provides methods to fetch:
    - Employment statistics
    - Consumer Price Index (CPI)
    - Producer Price Index (PPI)
    - Wages and earnings
    - Productivity data
    
    Key Series IDs:
    - LNS14000000: Unemployment Rate
    - CES0000000001: Total Nonfarm Employment
    - CUUR0000SA0: CPI-U All Items
    - CUSR0000SA0: CPI-U All Items (Seasonally Adjusted)
    - WPUFD4: PPI Final Demand
    - PRS85006092: Nonfarm Business Labor Productivity
    
    Example:
        client = BLSClient()
        
        # Get unemployment rate
        unemployment = client.get_series('LNS14000000')
        
        # Get CPI data
        cpi = client.get_series('CUUR0000SA0')
        
        # Get multiple series
        data = client.get_multiple_series(['LNS14000000', 'CUUR0000SA0'])
    """
    
    # Key BLS series
    KEY_SERIES = {
        # Employment
        'LNS14000000': 'Unemployment Rate',
        'LNS11000000': 'Civilian Labor Force Level',
        'LNS12000000': 'Employment Level',
        'LNS13000000': 'Unemployment Level',
        'CES0000000001': 'Total Nonfarm Employment',
        'CES0500000001': 'Total Private Employment',
        'LNS11300000': 'Labor Force Participation Rate',
        
        # Consumer Prices
        'CUUR0000SA0': 'CPI-U All Items (Unadjusted)',
        'CUSR0000SA0': 'CPI-U All Items (Seasonally Adjusted)',
        'CUUR0000SA0L1E': 'CPI-U Core (Less Food & Energy)',
        'CUSR0000SA0L1E': 'CPI-U Core (Less Food & Energy, SA)',
        'CUUR0000SAF1': 'CPI-U Food',
        'CUUR0000SETA01': 'CPI-U Gasoline',
        'CUUR0000SEHA': 'CPI-U Rent',
        
        # Producer Prices
        'WPUFD4': 'PPI Final Demand',
        'WPUFD49104': 'PPI Final Demand Less Foods and Energy',
        'WPU00000000': 'PPI All Commodities',
        
        # Wages
        'CES0500000003': 'Average Hourly Earnings (Private)',
        'CES0500000011': 'Average Weekly Earnings (Private)',
        'LEU0252881500': 'Median Usual Weekly Earnings',
        
        # Productivity
        'PRS85006092': 'Nonfarm Business Labor Productivity',
        'PRS85006112': 'Nonfarm Business Unit Labor Costs',
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize BLS client.
        
        Args:
            api_key: BLS API key (get from https://data.bls.gov/registrationEngine/)
        """
        # Use v2 endpoint if API key is provided
        base_url = "https://api.bls.gov/publicAPI/v2" if api_key or settings.BLS_API_KEY else "https://api.bls.gov/publicAPI/v1"
        
        super().__init__(
            base_url=base_url,
            api_key=api_key or settings.BLS_API_KEY,
            rate_limit=50,  # Conservative limit
            timeout=30,
            max_retries=3,
            cache_ttl=3600,
        )
        
        self._has_key = bool(self.api_key)
    
    def get_source_name(self) -> str:
        """Return source name."""
        return "bls"
    
    def health_check(self) -> bool:
        """Check if BLS API is accessible."""
        try:
            # Simple series request
            response = self.post(
                "/timeseries/data/",
                data={
                    "seriesid": ["LNS14000000"],
                    "startyear": str(datetime.now().year - 1),
                    "endyear": str(datetime.now().year),
                }
            )
            return response.get("status") == "REQUEST_SUCCEEDED"
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    def _build_request_data(
        self,
        series_ids: List[str],
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        calculations: bool = False,
        annual_average: bool = False,
        aspects: bool = False,
        catalog: bool = False,
    ) -> Dict[str, Any]:
        """Build request data for BLS API."""
        current_year = datetime.now().year
        
        # Default to last 10 years (or 20 with key)
        max_years = 20 if self._has_key else 10
        
        if start_year is None:
            start_year = current_year - max_years + 1
        if end_year is None:
            end_year = current_year
        
        data = {
            "seriesid": series_ids[:50],  # Max 50 series per request
            "startyear": str(start_year),
            "endyear": str(end_year),
        }
        
        if self._has_key:
            data["registrationkey"] = self.api_key
            
            if calculations:
                data["calculations"] = True
            if annual_average:
                data["annualaverage"] = True
            if aspects:
                data["aspects"] = True
            if catalog:
                data["catalog"] = True
        
        return data
    
    def _parse_response(self, response: Dict) -> Dict[str, Any]:
        """Parse BLS API response."""
        if response.get("status") != "REQUEST_SUCCEEDED":
            error_msg = response.get("message", [])
            self.logger.error(f"BLS API Error: {error_msg}")
            return {"Results": {"series": []}}
        
        return response
    
    # =========================================================================
    # DATA ENDPOINTS
    # =========================================================================
    
    def get_series(
        self,
        series_id: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        calculations: bool = True,
        annual_average: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get data for a single BLS series.
        
        Args:
            series_id: BLS series ID
            start_year: Start year
            end_year: End year
            calculations: Include calculations (percent changes)
            annual_average: Include annual averages
            
        Returns:
            List of observations
        """
        request_data = self._build_request_data(
            series_ids=[series_id],
            start_year=start_year,
            end_year=end_year,
            calculations=calculations,
            annual_average=annual_average,
        )
        
        response = self.post("/timeseries/data/", data=request_data)
        parsed = self._parse_response(response)
        
        series_data = parsed.get("Results", {}).get("series", [])
        if not series_data:
            return []
        
        observations = series_data[0].get("data", [])
        
        # Parse observations
        result = []
        for obs in observations:
            record = {
                "series_id": series_id,
                "year": int(obs.get("year")),
                "period": obs.get("period"),
                "period_name": obs.get("periodName"),
                "value": float(obs.get("value")) if obs.get("value") else None,
                "footnotes": obs.get("footnotes", []),
            }
            
            # Add calculations if present
            if "calculations" in obs:
                calcs = obs["calculations"]
                if "pct_changes" in calcs:
                    record["pct_change_1m"] = calcs["pct_changes"].get("1")
                    record["pct_change_3m"] = calcs["pct_changes"].get("3")
                    record["pct_change_6m"] = calcs["pct_changes"].get("6")
                    record["pct_change_12m"] = calcs["pct_changes"].get("12")
            
            result.append(record)
        
        return result
    
    def get_multiple_series(
        self,
        series_ids: List[str],
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        calculations: bool = True,
        annual_average: bool = True,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get data for multiple BLS series.
        
        Args:
            series_ids: List of BLS series IDs
            start_year: Start year
            end_year: End year
            calculations: Include calculations
            annual_average: Include annual averages
            
        Returns:
            Dict mapping series IDs to their observations
        """
        # BLS allows max 50 series per request
        result = {}
        
        for i in range(0, len(series_ids), 50):
            batch = series_ids[i:i + 50]
            
            request_data = self._build_request_data(
                series_ids=batch,
                start_year=start_year,
                end_year=end_year,
                calculations=calculations,
                annual_average=annual_average,
            )
            
            response = self.post("/timeseries/data/", data=request_data)
            parsed = self._parse_response(response)
            
            for series in parsed.get("Results", {}).get("series", []):
                series_id = series.get("seriesID")
                observations = []
                
                for obs in series.get("data", []):
                    record = {
                        "series_id": series_id,
                        "year": int(obs.get("year")),
                        "period": obs.get("period"),
                        "period_name": obs.get("periodName"),
                        "value": float(obs.get("value")) if obs.get("value") else None,
                    }
                    observations.append(record)
                
                result[series_id] = observations
        
        return result
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def get_unemployment_rate(
        self,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get unemployment rate data.
        
        Args:
            start_year: Start year
            end_year: End year
            
        Returns:
            Unemployment rate observations
        """
        return self.get_series(
            'LNS14000000',
            start_year=start_year,
            end_year=end_year,
        )
    
    def get_cpi(
        self,
        seasonally_adjusted: bool = True,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get Consumer Price Index data.
        
        Args:
            seasonally_adjusted: Use seasonally adjusted series
            start_year: Start year
            end_year: End year
            
        Returns:
            CPI observations
        """
        series_id = 'CUSR0000SA0' if seasonally_adjusted else 'CUUR0000SA0'
        return self.get_series(series_id, start_year=start_year, end_year=end_year)
    
    def get_core_cpi(
        self,
        seasonally_adjusted: bool = True,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get Core CPI (less food and energy) data.
        
        Args:
            seasonally_adjusted: Use seasonally adjusted series
            start_year: Start year
            end_year: End year
            
        Returns:
            Core CPI observations
        """
        series_id = 'CUSR0000SA0L1E' if seasonally_adjusted else 'CUUR0000SA0L1E'
        return self.get_series(series_id, start_year=start_year, end_year=end_year)
    
    def get_nonfarm_payrolls(
        self,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get Total Nonfarm Payrolls data.
        
        Args:
            start_year: Start year
            end_year: End year
            
        Returns:
            Nonfarm payrolls observations
        """
        return self.get_series(
            'CES0000000001',
            start_year=start_year,
            end_year=end_year,
        )
    
    def get_average_hourly_earnings(
        self,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get Average Hourly Earnings data.
        
        Args:
            start_year: Start year
            end_year: End year
            
        Returns:
            Average hourly earnings observations
        """
        return self.get_series(
            'CES0500000003',
            start_year=start_year,
            end_year=end_year,
        )
    
    def get_ppi(
        self,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get Producer Price Index data.
        
        Args:
            start_year: Start year
            end_year: End year
            
        Returns:
            PPI observations
        """
        return self.get_series('WPUFD4', start_year=start_year, end_year=end_year)
    
    def get_key_indicators(
        self,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all key economic indicators.
        
        Args:
            start_year: Start year
            end_year: End year
            
        Returns:
            Dict mapping series IDs to their observations
        """
        key_ids = [
            'LNS14000000',  # Unemployment
            'CES0000000001',  # Nonfarm Payrolls
            'CUSR0000SA0',  # CPI
            'CUSR0000SA0L1E',  # Core CPI
            'WPUFD4',  # PPI
            'CES0500000003',  # Hourly Earnings
        ]
        
        return self.get_multiple_series(
            key_ids,
            start_year=start_year,
            end_year=end_year,
        )
    
    def get_latest_values(self) -> Dict[str, Dict[str, Any]]:
        """
        Get latest values for key indicators.
        
        Returns:
            Dict mapping series IDs to their latest values
        """
        current_year = datetime.now().year
        
        data = self.get_key_indicators(
            start_year=current_year - 1,
            end_year=current_year,
        )
        
        result = {}
        for series_id, observations in data.items():
            if observations:
                # Get most recent (first in list, as data is usually newest first)
                latest = observations[0]
                result[series_id] = {
                    "name": self.KEY_SERIES.get(series_id, series_id),
                    **latest,
                }
        
        return result
