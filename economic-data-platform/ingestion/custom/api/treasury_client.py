"""
US Treasury API Client for financial data.

Treasury Fiscal Data provides:
- Interest rates and yields
- Treasury securities data
- Debt information
- Savings bonds rates
- Exchange rates

API Documentation: https://fiscaldata.treasury.gov/api-documentation/
Rate Limits: No strict limits
"""

from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union

from src.ingestion.base_client import BaseAPIClient
from src.ingestion.config import settings
from src.utils.helpers import parse_date


class TreasuryClient(BaseAPIClient):
    """
    Client for US Treasury Fiscal Data API.
    
    Provides methods to fetch:
    - Treasury yield rates
    - Interest rates
    - Debt statistics
    - Exchange rates
    
    Key Datasets:
    - /v2/accounting/od/avg_interest_rates: Average Interest Rates on Treasury Securities
    - /v1/accounting/od/rates_of_exchange: Treasury Reporting Rates of Exchange
    - /v2/accounting/od/debt_to_penny: Debt to the Penny
    - /v2/accounting/od/debt_outstanding: Debt Outstanding
    
    Example:
        client = TreasuryClient()
        
        # Get interest rates
        rates = client.get_interest_rates(security_type='Marketable')
        
        # Get debt statistics
        debt = client.get_debt_to_penny()
        
        # Get exchange rates
        exchange = client.get_exchange_rates(country='Euro Zone')
    """
    
    # Common security types
    SECURITY_TYPES = [
        'Treasury Bills',
        'Treasury Notes',
        'Treasury Bonds',
        'Treasury Inflation-Protected Securities (TIPS)',
        'Treasury Floating Rate Notes (FRN)',
        'Marketable',
        'Non-Marketable',
    ]
    
    def __init__(self):
        """Initialize Treasury client."""
        super().__init__(
            base_url=settings.TREASURY_API_URL,
            api_key=None,  # No API key required
            rate_limit=60,
            timeout=30,
            max_retries=3,
            cache_ttl=3600,  # 1 hour cache
        )
    
    def get_source_name(self) -> str:
        """Return source name."""
        return "treasury"
    
    def health_check(self) -> bool:
        """Check if Treasury API is accessible."""
        try:
            response = self.get(
                "/v2/accounting/od/avg_interest_rates",
                params={"page[size]": 1, "format": "json"}
            )
            return "data" in response
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    def _build_params(
        self,
        page_size: int = 100,
        page_number: int = 1,
        sort: Optional[str] = None,
        filter_str: Optional[str] = None,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Build request parameters."""
        params = {
            "page[size]": page_size,
            "page[number]": page_number,
            "format": "json",
        }
        
        if sort:
            params["sort"] = sort
        
        if filter_str:
            params["filter"] = filter_str
        
        if fields:
            params["fields"] = ",".join(fields)
        
        return params
    
    def _parse_response(self, response: Dict) -> List[Dict[str, Any]]:
        """Parse Treasury API response."""
        return response.get("data", [])
    
    # =========================================================================
    # INTEREST RATES ENDPOINTS
    # =========================================================================
    
    def get_interest_rates(
        self,
        security_type: Optional[str] = None,
        security_desc: Optional[str] = None,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        page_size: int = 100,
        sort: str = "-record_date",
    ) -> List[Dict[str, Any]]:
        """
        Get average interest rates on Treasury securities.
        
        Args:
            security_type: Security type filter
            security_desc: Security description filter
            start_date: Start date
            end_date: End date
            page_size: Results per page
            sort: Sort field (prefix with - for descending)
            
        Returns:
            List of interest rate records
        """
        filters = []
        
        if security_type:
            filters.append(f"security_type_desc:eq:{security_type}")
        
        if security_desc:
            filters.append(f"security_desc:eq:{security_desc}")
        
        if start_date:
            start_dt = parse_date(start_date)
            if start_dt:
                filters.append(f"record_date:gte:{start_dt.strftime('%Y-%m-%d')}")
        
        if end_date:
            end_dt = parse_date(end_date)
            if end_dt:
                filters.append(f"record_date:lte:{end_dt.strftime('%Y-%m-%d')}")
        
        params = self._build_params(
            page_size=page_size,
            sort=sort,
            filter_str=",".join(filters) if filters else None,
        )
        
        response = self.get("/v2/accounting/od/avg_interest_rates", params=params)
        return self._parse_response(response)
    
    def get_treasury_yield_curve(
        self,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get Treasury yield curve rates for different maturities.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Yield curve data
        """
        # Get rates for each maturity
        maturities = [
            'Treasury Bills',
            'Treasury Notes',
            'Treasury Bonds',
        ]
        
        all_rates = []
        for security_type in maturities:
            rates = self.get_interest_rates(
                security_type=security_type,
                start_date=start_date,
                end_date=end_date,
            )
            all_rates.extend(rates)
        
        return all_rates
    
    # =========================================================================
    # DEBT ENDPOINTS
    # =========================================================================
    
    def get_debt_to_penny(
        self,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        page_size: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get daily debt to the penny data.
        
        Args:
            start_date: Start date
            end_date: End date
            page_size: Results per page
            
        Returns:
            List of debt records
        """
        filters = []
        
        if start_date:
            start_dt = parse_date(start_date)
            if start_dt:
                filters.append(f"record_date:gte:{start_dt.strftime('%Y-%m-%d')}")
        
        if end_date:
            end_dt = parse_date(end_date)
            if end_dt:
                filters.append(f"record_date:lte:{end_dt.strftime('%Y-%m-%d')}")
        
        params = self._build_params(
            page_size=page_size,
            sort="-record_date",
            filter_str=",".join(filters) if filters else None,
        )
        
        response = self.get("/v2/accounting/od/debt_to_penny", params=params)
        data = self._parse_response(response)
        
        # Parse numeric values
        for item in data:
            for key in ['tot_pub_debt_out_amt', 'intragov_hold_amt', 'debt_held_public_amt']:
                if item.get(key):
                    try:
                        item[key] = float(item[key])
                    except (ValueError, TypeError):
                        pass
        
        return data
    
    def get_debt_outstanding(
        self,
        debt_type: Optional[str] = None,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get debt outstanding by type.
        
        Args:
            debt_type: Filter by debt type
            start_date: Start date
            end_date: End date
            
        Returns:
            List of debt outstanding records
        """
        filters = []
        
        if debt_type:
            filters.append(f"debt_type_desc:eq:{debt_type}")
        
        if start_date:
            start_dt = parse_date(start_date)
            if start_dt:
                filters.append(f"record_date:gte:{start_dt.strftime('%Y-%m-%d')}")
        
        if end_date:
            end_dt = parse_date(end_date)
            if end_dt:
                filters.append(f"record_date:lte:{end_dt.strftime('%Y-%m-%d')}")
        
        params = self._build_params(
            page_size=100,
            sort="-record_date",
            filter_str=",".join(filters) if filters else None,
        )
        
        response = self.get("/v2/accounting/od/debt_outstanding", params=params)
        return self._parse_response(response)
    
    # =========================================================================
    # EXCHANGE RATES ENDPOINTS
    # =========================================================================
    
    def get_exchange_rates(
        self,
        country: Optional[str] = None,
        currency: Optional[str] = None,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        page_size: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get Treasury reporting rates of exchange.
        
        Args:
            country: Country name filter
            currency: Currency filter
            start_date: Start date
            end_date: End date
            page_size: Results per page
            
        Returns:
            List of exchange rate records
        """
        filters = []
        
        if country:
            filters.append(f"country:eq:{country}")
        
        if currency:
            filters.append(f"currency:eq:{currency}")
        
        if start_date:
            start_dt = parse_date(start_date)
            if start_dt:
                filters.append(f"record_date:gte:{start_dt.strftime('%Y-%m-%d')}")
        
        if end_date:
            end_dt = parse_date(end_date)
            if end_dt:
                filters.append(f"record_date:lte:{end_dt.strftime('%Y-%m-%d')}")
        
        params = self._build_params(
            page_size=page_size,
            sort="-record_date",
            filter_str=",".join(filters) if filters else None,
        )
        
        response = self.get("/v1/accounting/od/rates_of_exchange", params=params)
        return self._parse_response(response)
    
    # =========================================================================
    # SAVINGS BONDS ENDPOINTS
    # =========================================================================
    
    def get_savings_bond_rates(
        self,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get savings bond interest rates.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List of savings bond rate records
        """
        filters = []
        
        if start_date:
            start_dt = parse_date(start_date)
            if start_dt:
                filters.append(f"record_date:gte:{start_dt.strftime('%Y-%m-%d')}")
        
        if end_date:
            end_dt = parse_date(end_date)
            if end_dt:
                filters.append(f"record_date:lte:{end_dt.strftime('%Y-%m-%d')}")
        
        params = self._build_params(
            page_size=100,
            sort="-record_date",
            filter_str=",".join(filters) if filters else None,
        )
        
        response = self.get("/v2/accounting/od/sb_int_rates", params=params)
        return self._parse_response(response)
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def get_current_debt(self) -> Dict[str, Any]:
        """
        Get current total debt statistics.
        
        Returns:
            Current debt summary
        """
        data = self.get_debt_to_penny(page_size=1)
        return data[0] if data else {}
    
    def get_current_rates(self) -> List[Dict[str, Any]]:
        """
        Get current interest rates for all securities.
        
        Returns:
            Current interest rates
        """
        return self.get_interest_rates(page_size=50)
    
    def get_debt_history(
        self,
        years: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get historical debt data.
        
        Args:
            years: Number of years of history
            
        Returns:
            Historical debt data (end of each year)
        """
        current_year = datetime.now().year
        start_year = current_year - years
        
        # Get data for each year (typically reported monthly/daily)
        return self.get_debt_to_penny(
            start_date=f"{start_year}-01-01",
            end_date=f"{current_year}-12-31",
            page_size=years * 12,  # Roughly monthly
        )
    
    def get_rate_by_maturity(
        self,
        maturity_years: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Get current rate for a specific maturity.
        
        Args:
            maturity_years: Bond maturity in years (2, 5, 10, 30)
            
        Returns:
            Rate data for the maturity
        """
        maturity_map = {
            2: 'Treasury Notes',
            5: 'Treasury Notes',
            10: 'Treasury Notes',
            30: 'Treasury Bonds',
        }
        
        security_type = maturity_map.get(maturity_years)
        if not security_type:
            return None
        
        rates = self.get_interest_rates(
            security_type=security_type,
            page_size=10,
        )
        
        # Find matching maturity
        for rate in rates:
            desc = rate.get('security_desc', '')
            if str(maturity_years) in desc:
                return rate
        
        return rates[0] if rates else None
