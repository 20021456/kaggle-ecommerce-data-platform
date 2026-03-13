"""
Economic API Router - Economic indicators and data endpoints.

Provides endpoints for:
- US economic indicators (FRED)
- International data (World Bank)
- Treasury rates
- Employment statistics
- Inflation metrics
"""

from datetime import datetime, date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query, HTTPException, Path
from pydantic import BaseModel, Field

from src.ingestion.economic import FREDClient, WorldBankClient, TreasuryClient, BLSClient
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class EconomicIndicator(BaseModel):
    """Economic indicator observation."""
    series_id: str
    name: Optional[str] = None
    date: date
    value: float
    units: Optional[str] = None


class IndicatorSeries(BaseModel):
    """Economic indicator time series."""
    series_id: str
    name: str
    units: Optional[str] = None
    frequency: Optional[str] = None
    observations: List[EconomicIndicator]


class CountryIndicator(BaseModel):
    """Country economic indicator."""
    country_code: str
    country_name: str
    indicator_id: str
    indicator_name: str
    year: int
    value: Optional[float]


class TreasuryYield(BaseModel):
    """Treasury yield data."""
    date: date
    yield_1m: Optional[float] = None
    yield_3m: Optional[float] = None
    yield_6m: Optional[float] = None
    yield_1y: Optional[float] = None
    yield_2y: Optional[float] = None
    yield_5y: Optional[float] = None
    yield_10y: Optional[float] = None
    yield_30y: Optional[float] = None
    spread_10y_2y: Optional[float] = None


class EmploymentData(BaseModel):
    """Employment statistics."""
    date: date
    unemployment_rate: Optional[float]
    nonfarm_payrolls_thousands: Optional[int]
    labor_force_participation: Optional[float]


class InflationData(BaseModel):
    """Inflation metrics."""
    date: date
    cpi_yoy: Optional[float]
    core_cpi_yoy: Optional[float]
    pce_yoy: Optional[float]


# =============================================================================
# FRED ENDPOINTS
# =============================================================================

@router.get("/fred/series/{series_id}", response_model=IndicatorSeries)
async def get_fred_series(
    series_id: str = Path(..., description="FRED series ID (e.g., 'GDP', 'CPIAUCSL')"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    units: str = Query(default="lin", description="Units transformation"),
    frequency: Optional[str] = Query(None, description="Frequency aggregation"),
):
    """
    Get FRED time series data.
    
    Common series IDs:
    - GDP: Gross Domestic Product
    - UNRATE: Unemployment Rate
    - CPIAUCSL: Consumer Price Index
    - FEDFUNDS: Federal Funds Rate
    - DGS10: 10-Year Treasury Rate
    """
    try:
        client = FREDClient()
        
        # Get series metadata
        series_info = client.get_series_info(series_id)
        
        # Get observations
        observations = client.get_series(
            series_id,
            start=start_date,
            end=end_date,
            units=units,
            frequency=frequency,
        )
        
        return IndicatorSeries(
            series_id=series_id,
            name=series_info.get("title", series_id),
            units=series_info.get("units"),
            frequency=series_info.get("frequency"),
            observations=[
                EconomicIndicator(
                    series_id=series_id,
                    date=datetime.strptime(obs["date"], "%Y-%m-%d").date(),
                    value=obs["value"],
                )
                for obs in observations
            ]
        )
    except Exception as e:
        logger.error(f"Error fetching FRED series {series_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch FRED series {series_id}")


@router.get("/fred/search")
async def search_fred_series(
    query: str = Query(..., description="Search query"),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum results"),
):
    """
    Search for FRED series by keyword.
    """
    try:
        client = FREDClient()
        results = client.search_series(query, limit=limit)
        
        return [
            {
                "series_id": s.get("id"),
                "title": s.get("title"),
                "units": s.get("units"),
                "frequency": s.get("frequency"),
                "seasonal_adjustment": s.get("seasonal_adjustment"),
                "popularity": s.get("popularity"),
            }
            for s in results
        ]
    except Exception as e:
        logger.error(f"Error searching FRED: {e}")
        raise HTTPException(status_code=500, detail="Failed to search FRED")


@router.get("/fred/latest")
async def get_fred_latest():
    """
    Get latest values for key economic indicators.
    
    Returns most recent data for GDP, unemployment, CPI, Fed Funds, etc.
    """
    try:
        client = FREDClient()
        latest = client.get_latest_values()
        
        return latest
    except Exception as e:
        logger.error(f"Error fetching latest FRED data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch latest indicators")


# =============================================================================
# WORLD BANK ENDPOINTS
# =============================================================================

@router.get("/worldbank/indicators/{indicator_id}")
async def get_worldbank_indicator(
    indicator_id: str = Path(..., description="World Bank indicator ID"),
    countries: Optional[str] = Query(None, description="Comma-separated country codes"),
    start_year: Optional[int] = Query(None, description="Start year"),
    end_year: Optional[int] = Query(None, description="End year"),
):
    """
    Get World Bank indicator data.
    
    Common indicators:
    - NY.GDP.MKTP.CD: GDP (current US$)
    - FP.CPI.TOTL.ZG: Inflation rate
    - SL.UEM.TOTL.ZS: Unemployment rate
    """
    try:
        client = WorldBankClient()
        
        country_list = countries.split(",") if countries else None
        
        data = client.get_indicator_data(
            indicator_id,
            country=country_list,
            start_year=start_year,
            end_year=end_year,
        )
        
        return data
    except Exception as e:
        logger.error(f"Error fetching World Bank indicator {indicator_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch indicator {indicator_id}")


@router.get("/worldbank/countries/{country_code}")
async def get_country_data(
    country_code: str = Path(..., description="ISO 2-letter country code"),
    indicators: Optional[str] = Query(None, description="Comma-separated indicator IDs"),
    start_year: Optional[int] = Query(default=2010, description="Start year"),
    end_year: Optional[int] = Query(None, description="End year"),
):
    """
    Get multiple indicators for a specific country.
    """
    try:
        client = WorldBankClient()
        
        indicator_list = indicators.split(",") if indicators else None
        
        data = client.get_country_data(
            country_code,
            indicators=indicator_list,
            start_year=start_year,
            end_year=end_year,
        )
        
        return data
    except Exception as e:
        logger.error(f"Error fetching country data for {country_code}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch data for {country_code}")


@router.get("/worldbank/gdp")
async def get_gdp_data(
    countries: Optional[str] = Query(None, description="Comma-separated country codes"),
    start_year: int = Query(default=2000, description="Start year"),
    end_year: Optional[int] = Query(None, description="End year"),
):
    """
    Get GDP data for countries.
    
    Returns GDP in current US dollars.
    """
    try:
        client = WorldBankClient()
        
        country_list = countries.split(",") if countries else None
        
        data = client.get_gdp_data(
            countries=country_list,
            start_year=start_year,
            end_year=end_year,
        )
        
        return data
    except Exception as e:
        logger.error(f"Error fetching GDP data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch GDP data")


# =============================================================================
# TREASURY ENDPOINTS
# =============================================================================

@router.get("/treasury/yields")
async def get_treasury_yields(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(default=30, ge=1, le=365, description="Number of records"),
):
    """
    Get Treasury yield curve data.
    
    Returns yields for various maturities (1M to 30Y).
    """
    try:
        client = TreasuryClient()
        
        rates = client.get_interest_rates(
            start_date=start_date,
            end_date=end_date,
            page_size=limit,
        )
        
        return rates
    except Exception as e:
        logger.error(f"Error fetching Treasury yields: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Treasury yields")


@router.get("/treasury/debt")
async def get_us_debt(
    start_date: Optional[str] = Query(None, description="Start date"),
    end_date: Optional[str] = Query(None, description="End date"),
    limit: int = Query(default=30, ge=1, le=365, description="Number of records"),
):
    """
    Get US national debt statistics.
    
    Returns total public debt, intragovernmental holdings, etc.
    """
    try:
        client = TreasuryClient()
        
        debt = client.get_debt_to_penny(
            start_date=start_date,
            end_date=end_date,
            page_size=limit,
        )
        
        return debt
    except Exception as e:
        logger.error(f"Error fetching US debt: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch US debt data")


# =============================================================================
# BLS ENDPOINTS
# =============================================================================

@router.get("/bls/unemployment")
async def get_unemployment(
    start_year: Optional[int] = Query(None, description="Start year"),
    end_year: Optional[int] = Query(None, description="End year"),
):
    """
    Get unemployment rate data from BLS.
    """
    try:
        client = BLSClient()
        
        data = client.get_unemployment_rate(
            start_year=start_year,
            end_year=end_year,
        )
        
        return data
    except Exception as e:
        logger.error(f"Error fetching unemployment: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch unemployment data")


@router.get("/bls/cpi")
async def get_cpi(
    start_year: Optional[int] = Query(None, description="Start year"),
    end_year: Optional[int] = Query(None, description="End year"),
    seasonally_adjusted: bool = Query(default=True, description="Use seasonally adjusted data"),
):
    """
    Get Consumer Price Index (CPI) data from BLS.
    """
    try:
        client = BLSClient()
        
        data = client.get_cpi(
            seasonally_adjusted=seasonally_adjusted,
            start_year=start_year,
            end_year=end_year,
        )
        
        return data
    except Exception as e:
        logger.error(f"Error fetching CPI: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch CPI data")


@router.get("/bls/payrolls")
async def get_nonfarm_payrolls(
    start_year: Optional[int] = Query(None, description="Start year"),
    end_year: Optional[int] = Query(None, description="End year"),
):
    """
    Get Total Nonfarm Payrolls data from BLS.
    """
    try:
        client = BLSClient()
        
        data = client.get_nonfarm_payrolls(
            start_year=start_year,
            end_year=end_year,
        )
        
        return data
    except Exception as e:
        logger.error(f"Error fetching payrolls: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch payrolls data")


# =============================================================================
# SUMMARY ENDPOINTS
# =============================================================================

@router.get("/summary/us")
async def get_us_economic_summary():
    """
    Get comprehensive US economic summary.
    
    Returns latest values for key indicators.
    """
    try:
        # Initialize clients
        fred_client = FREDClient()
        bls_client = BLSClient()
        treasury_client = TreasuryClient()
        
        # Fetch data
        fred_latest = fred_client.get_latest_values([
            'GDP', 'UNRATE', 'CPIAUCSL', 'FEDFUNDS', 'DGS10', 'M2SL'
        ])
        
        current_debt = treasury_client.get_current_debt()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "indicators": fred_latest,
            "national_debt": current_debt,
        }
    except Exception as e:
        logger.error(f"Error fetching US summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch US economic summary")
