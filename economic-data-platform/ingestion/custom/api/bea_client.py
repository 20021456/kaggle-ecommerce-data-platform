"""
BEA (Bureau of Economic Analysis) API Client.

BEA provides official US economic statistics including:
- National Income and Product Accounts (NIPA)
- GDP and components
- Personal income and outlays
- International transactions
- Regional economic accounts

API Documentation: https://apps.bea.gov/api/
Rate Limits: 100 requests per minute, 100MB per day
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from src.ingestion.base_client import BaseAPIClient
from src.ingestion.config import settings


class BEAClient(BaseAPIClient):
    """
    Client for BEA (Bureau of Economic Analysis) API.
    
    Provides methods to fetch:
    - GDP and national accounts data
    - Personal income data
    - Regional economic data
    - International transactions
    
    Datasets:
    - NIPA: National Income and Product Accounts
    - NIUnderlyingDetail: NIPA Underlying Detail
    - FixedAssets: Fixed Assets
    - ITA: International Transactions
    - IIP: International Investment Position
    - Regional: Regional data
    - InputOutput: Input-Output
    - GDPbyIndustry: GDP by Industry
    
    Example:
        client = BEAClient()
        
        # Get GDP data
        gdp = client.get_nipa_data(table_name='T10101', frequency='Q')
        
        # Get personal income
        income = client.get_nipa_data(table_name='T20100', frequency='M')
    """
    
    # Common NIPA tables
    NIPA_TABLES = {
        'T10101': 'Percent Change From Preceding Period in Real GDP',
        'T10105': 'Gross Domestic Product',
        'T10106': 'Real Gross Domestic Product, Chained Dollars',
        'T10107': 'Percent Change From Preceding Period in Real GDP (Contributions)',
        'T20100': 'Personal Income and Its Disposition',
        'T20200': 'Personal Income and Its Disposition (Monthly)',
        'T20301': 'Personal Consumption Expenditures by Major Type of Product',
        'T20305': 'Personal Consumption Expenditures by Major Type of Product (Monthly)',
        'T20600': 'Real Personal Consumption Expenditures by Major Type of Product',
        'T30100': 'Government Current Receipts and Expenditures',
        'T40100': 'Foreign Transactions in the NIPA',
        'T50100': 'Saving and Investment',
        'T70100': 'Transactions of Nonprofit Institutions',
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize BEA client.
        
        Args:
            api_key: BEA API key (get from https://apps.bea.gov/api/signup/)
        """
        super().__init__(
            base_url=settings.BEA_API_URL,
            api_key=api_key or settings.BEA_API_KEY,
            rate_limit=100,
            timeout=30,
            max_retries=3,
            cache_ttl=3600,  # 1 hour cache
        )
    
    def get_source_name(self) -> str:
        """Return source name."""
        return "bea"
    
    def health_check(self) -> bool:
        """Check if BEA API is accessible."""
        try:
            response = self._make_request(
                "GET", "",
                params={
                    "UserID": self.api_key,
                    "method": "GETDATASETLIST",
                    "ResultFormat": "JSON",
                }
            )
            return "BEAAPI" in response
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    def _build_params(self, method: str, **kwargs) -> Dict[str, Any]:
        """Build request parameters with API key."""
        params = {
            "UserID": self.api_key,
            "method": method,
            "ResultFormat": "JSON",
        }
        params.update(kwargs)
        return params
    
    def _parse_response(self, response: Dict) -> Dict[str, Any]:
        """Parse BEA API response."""
        beaapi = response.get("BEAAPI", {})
        results = beaapi.get("Results", {})
        
        # Check for errors
        if "Error" in results:
            error = results["Error"]
            self.logger.error(f"BEA API Error: {error}")
            return {}
        
        return results
    
    # =========================================================================
    # METADATA ENDPOINTS
    # =========================================================================
    
    def get_dataset_list(self) -> List[Dict[str, Any]]:
        """
        Get list of available datasets.
        
        Returns:
            List of available BEA datasets
        """
        params = self._build_params("GETDATASETLIST")
        response = self._make_request("GET", "", params=params)
        results = self._parse_response(response)
        return results.get("Dataset", [])
    
    def get_parameter_list(self, dataset_name: str) -> List[Dict[str, Any]]:
        """
        Get parameters for a dataset.
        
        Args:
            dataset_name: Name of the dataset
            
        Returns:
            List of parameters
        """
        params = self._build_params("GETPARAMETERLIST", DatasetName=dataset_name)
        response = self._make_request("GET", "", params=params)
        results = self._parse_response(response)
        return results.get("Parameter", [])
    
    def get_parameter_values(
        self,
        dataset_name: str,
        parameter_name: str,
    ) -> List[Dict[str, Any]]:
        """
        Get valid values for a parameter.
        
        Args:
            dataset_name: Name of the dataset
            parameter_name: Name of the parameter
            
        Returns:
            List of valid parameter values
        """
        params = self._build_params(
            "GETPARAMETERVALUES",
            DatasetName=dataset_name,
            ParameterName=parameter_name,
        )
        response = self._make_request("GET", "", params=params)
        results = self._parse_response(response)
        return results.get("ParamValue", [])
    
    # =========================================================================
    # DATA ENDPOINTS
    # =========================================================================
    
    def get_data(
        self,
        dataset_name: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Get data from a BEA dataset.
        
        Args:
            dataset_name: Name of the dataset
            **kwargs: Dataset-specific parameters
            
        Returns:
            Dataset results
        """
        params = self._build_params("GETDATA", DatasetName=dataset_name, **kwargs)
        response = self._make_request("GET", "", params=params)
        return self._parse_response(response)
    
    def get_nipa_data(
        self,
        table_name: str,
        frequency: str = "Q",
        year: Optional[Union[str, List[str]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get NIPA (National Income and Product Accounts) data.
        
        Args:
            table_name: NIPA table name (e.g., 'T10101')
            frequency: 'A' (Annual), 'Q' (Quarterly), 'M' (Monthly)
            year: Year(s) to fetch ('X' for latest, 'ALL', or specific year(s))
            
        Returns:
            List of NIPA data observations
        """
        if year is None:
            year = "X"  # Latest year
        elif isinstance(year, list):
            year = ",".join(str(y) for y in year)
        
        results = self.get_data(
            dataset_name="NIPA",
            TableName=table_name,
            Frequency=frequency,
            Year=year,
        )
        
        data = results.get("Data", [])
        
        # Parse data
        parsed = []
        for item in data:
            parsed.append({
                "table_name": item.get("TableName"),
                "series_code": item.get("SeriesCode"),
                "line_number": item.get("LineNumber"),
                "line_description": item.get("LineDescription"),
                "time_period": item.get("TimePeriod"),
                "value": float(item.get("DataValue", 0).replace(",", "")) if item.get("DataValue") else None,
                "note_ref": item.get("NoteRef"),
            })
        
        return parsed
    
    def get_fixed_assets_data(
        self,
        table_name: str,
        year: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get Fixed Assets data.
        
        Args:
            table_name: Fixed Assets table name
            year: Year(s) to fetch
            
        Returns:
            List of Fixed Assets data
        """
        if year is None:
            year = "X"
        
        results = self.get_data(
            dataset_name="FixedAssets",
            TableName=table_name,
            Year=year,
        )
        
        return results.get("Data", [])
    
    def get_regional_data(
        self,
        table_name: str,
        line_code: str,
        geo_fips: str = "STATE",
        year: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get Regional economic data.
        
        Args:
            table_name: Regional table name (e.g., 'CAINC1')
            line_code: Line code for the data series
            geo_fips: Geographic area ('STATE', 'COUNTY', or specific FIPS)
            year: Year(s) to fetch
            
        Returns:
            List of Regional data
        """
        if year is None:
            year = "LAST5"
        
        results = self.get_data(
            dataset_name="Regional",
            TableName=table_name,
            LineCode=line_code,
            GeoFips=geo_fips,
            Year=year,
        )
        
        return results.get("Data", [])
    
    def get_gdp_by_industry(
        self,
        table_id: str,
        frequency: str = "Q",
        year: Optional[str] = None,
        industry: str = "ALL",
    ) -> List[Dict[str, Any]]:
        """
        Get GDP by Industry data.
        
        Args:
            table_id: Table ID
            frequency: 'A' (Annual) or 'Q' (Quarterly)
            year: Year(s) to fetch
            industry: Industry code(s)
            
        Returns:
            List of GDP by Industry data
        """
        if year is None:
            year = "LAST5"
        
        results = self.get_data(
            dataset_name="GDPbyIndustry",
            TableID=table_id,
            Frequency=frequency,
            Year=year,
            Industry=industry,
        )
        
        return results.get("Data", [])
    
    def get_international_transactions(
        self,
        indicator: str = "ALL",
        area_or_country: str = "ALL",
        frequency: str = "Q",
        year: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get International Transactions data.
        
        Args:
            indicator: Indicator code
            area_or_country: Area or country code
            frequency: 'A' (Annual) or 'Q' (Quarterly)
            year: Year(s) to fetch
            
        Returns:
            List of ITA data
        """
        if year is None:
            year = "LAST5"
        
        results = self.get_data(
            dataset_name="ITA",
            Indicator=indicator,
            AreaOrCountry=area_or_country,
            Frequency=frequency,
            Year=year,
        )
        
        return results.get("Data", [])
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def get_gdp_growth(
        self,
        frequency: str = "Q",
        years: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Get GDP growth rate data.
        
        Args:
            frequency: 'Q' (Quarterly) or 'A' (Annual)
            years: Number of years to fetch
            
        Returns:
            GDP growth data
        """
        current_year = datetime.now().year
        year_list = [str(y) for y in range(current_year - years, current_year + 1)]
        
        return self.get_nipa_data(
            table_name="T10101",
            frequency=frequency,
            year=year_list,
        )
    
    def get_personal_income(
        self,
        frequency: str = "M",
        years: int = 2,
    ) -> List[Dict[str, Any]]:
        """
        Get personal income data.
        
        Args:
            frequency: 'M' (Monthly), 'Q' (Quarterly), or 'A' (Annual)
            years: Number of years to fetch
            
        Returns:
            Personal income data
        """
        current_year = datetime.now().year
        year_list = [str(y) for y in range(current_year - years, current_year + 1)]
        
        return self.get_nipa_data(
            table_name="T20100" if frequency in ['Q', 'A'] else "T20200",
            frequency=frequency,
            year=year_list,
        )
    
    def get_pce_data(
        self,
        frequency: str = "Q",
        years: int = 2,
    ) -> List[Dict[str, Any]]:
        """
        Get Personal Consumption Expenditures data.
        
        Args:
            frequency: 'M' (Monthly) or 'Q' (Quarterly)
            years: Number of years to fetch
            
        Returns:
            PCE data
        """
        current_year = datetime.now().year
        year_list = [str(y) for y in range(current_year - years, current_year + 1)]
        
        return self.get_nipa_data(
            table_name="T20301" if frequency == 'Q' else "T20305",
            frequency=frequency,
            year=year_list,
        )
    
    def get_latest_gdp(self) -> Dict[str, Any]:
        """
        Get latest GDP data summary.
        
        Returns:
            Latest GDP data
        """
        data = self.get_nipa_data(table_name="T10101", frequency="Q", year="X")
        
        if data:
            # Filter for headline GDP growth
            headline = [d for d in data if d.get("line_number") == "1"]
            if headline:
                return headline[-1]
        
        return {}
