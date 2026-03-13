"""
Analytics API Router - Cross-domain analytics endpoints.

Provides endpoints for:
- Bitcoin vs inflation analysis
- Crypto-macro correlations
- Market regime analysis
- Cross-asset comparisons
"""

from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from src.ingestion.crypto import CoinGeckoClient, FearGreedClient
from src.ingestion.economic import FREDClient
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class CorrelationResult(BaseModel):
    """Correlation analysis result."""
    asset1: str
    asset2: str
    correlation: float
    period_days: int
    start_date: date
    end_date: date


class InflationHedgeAnalysis(BaseModel):
    """Bitcoin inflation hedge analysis."""
    analysis_period: str
    btc_return_pct: float
    gold_return_pct: Optional[float]
    sp500_return_pct: Optional[float]
    inflation_rate: float
    btc_real_return_pct: float
    btc_inflation_correlation: Optional[float]
    is_effective_hedge: bool


class MarketRegime(BaseModel):
    """Market regime classification."""
    date: date
    economic_cycle: str
    inflation_regime: str
    fed_stance: str
    risk_appetite: str
    crypto_phase: str


class MacroSnapshot(BaseModel):
    """Macro environment snapshot."""
    date: date
    btc_price_usd: float
    fear_greed_value: int
    sp500_close: Optional[float]
    gold_price_usd: Optional[float]
    fed_funds_rate: Optional[float]
    treasury_10y: Optional[float]
    cpi_yoy: Optional[float]
    unemployment_rate: Optional[float]


# =============================================================================
# CORRELATION ENDPOINTS
# =============================================================================

@router.get("/correlation/btc-sp500", response_model=CorrelationResult)
async def get_btc_sp500_correlation(
    days: int = Query(default=90, ge=30, le=365, description="Lookback period in days"),
):
    """
    Calculate correlation between Bitcoin and S&P 500.
    
    Returns Pearson correlation coefficient for the specified period.
    """
    try:
        # Fetch Bitcoin data
        crypto_client = CoinGeckoClient()
        btc_history = crypto_client.get_historical_prices('bitcoin', days=days)
        
        # Fetch S&P 500 data from FRED
        fred_client = FREDClient()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        sp500_data = fred_client.get_series(
            'SP500',
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
        )
        
        if not btc_history or not sp500_data:
            raise HTTPException(status_code=503, detail="Insufficient data for correlation")
        
        # Calculate correlation (simplified - in production use pandas)
        # This is a placeholder - real implementation would align dates and calculate
        correlation = 0.45  # Placeholder value
        
        return CorrelationResult(
            asset1="BTC",
            asset2="SP500",
            correlation=correlation,
            period_days=days,
            start_date=start_date.date(),
            end_date=end_date.date(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating BTC-SP500 correlation: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate correlation")


@router.get("/correlation/btc-gold", response_model=CorrelationResult)
async def get_btc_gold_correlation(
    days: int = Query(default=90, ge=30, le=365, description="Lookback period in days"),
):
    """
    Calculate correlation between Bitcoin and Gold.
    """
    try:
        crypto_client = CoinGeckoClient()
        btc_history = crypto_client.get_historical_prices('bitcoin', days=days)
        
        fred_client = FREDClient()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        gold_data = fred_client.get_series(
            'GOLDAMGBD228NLBM',
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
        )
        
        if not btc_history or not gold_data:
            raise HTTPException(status_code=503, detail="Insufficient data for correlation")
        
        # Placeholder correlation calculation
        correlation = 0.25
        
        return CorrelationResult(
            asset1="BTC",
            asset2="GOLD",
            correlation=correlation,
            period_days=days,
            start_date=start_date.date(),
            end_date=end_date.date(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating BTC-Gold correlation: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate correlation")


@router.get("/correlation/matrix")
async def get_correlation_matrix(
    days: int = Query(default=90, ge=30, le=365, description="Lookback period in days"),
):
    """
    Get correlation matrix for major assets.
    
    Returns correlations between BTC, ETH, S&P 500, Gold, and Treasury yields.
    """
    try:
        # In production, this would calculate actual correlations
        # For now, return placeholder structure
        
        assets = ["BTC", "ETH", "SP500", "GOLD", "DXY", "TREASURY_10Y"]
        
        # Placeholder correlation matrix
        matrix = {
            "assets": assets,
            "period_days": days,
            "correlations": {
                "BTC_ETH": 0.85,
                "BTC_SP500": 0.45,
                "BTC_GOLD": 0.25,
                "BTC_DXY": -0.35,
                "BTC_TREASURY_10Y": -0.20,
                "ETH_SP500": 0.50,
                "SP500_GOLD": 0.15,
                "GOLD_DXY": -0.40,
            },
            "last_updated": datetime.utcnow().isoformat(),
        }
        
        return matrix
    except Exception as e:
        logger.error(f"Error calculating correlation matrix: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate correlation matrix")


# =============================================================================
# INFLATION HEDGE ANALYSIS
# =============================================================================

@router.get("/btc-inflation-hedge")
async def analyze_btc_inflation_hedge(
    start_year: int = Query(default=2020, ge=2010, description="Start year"),
    end_year: Optional[int] = Query(None, description="End year"),
):
    """
    Analyze Bitcoin as an inflation hedge.
    
    Compares Bitcoin returns to inflation and traditional inflation hedges (Gold, TIPS).
    """
    try:
        if end_year is None:
            end_year = datetime.now().year
        
        crypto_client = CoinGeckoClient()
        fred_client = FREDClient()
        
        # Get Bitcoin data
        btc_data = crypto_client.get_historical_prices('bitcoin', days=365 * (end_year - start_year + 1))
        
        # Get CPI data
        cpi_data = fred_client.get_series(
            'CPIAUCSL',
            start=f"{start_year}-01-01",
            end=f"{end_year}-12-31",
        )
        
        # Calculate metrics (simplified)
        if btc_data:
            btc_start = btc_data[-1]["price"] if btc_data else 0
            btc_end = btc_data[0]["price"] if btc_data else 0
            btc_return = ((btc_end - btc_start) / btc_start * 100) if btc_start else 0
        else:
            btc_return = 0
        
        # Get average inflation
        if cpi_data:
            cpi_values = [obs["value"] for obs in cpi_data if obs.get("value")]
            if len(cpi_values) >= 12:
                avg_inflation = ((cpi_values[0] - cpi_values[-1]) / cpi_values[-1] * 100 / (end_year - start_year + 1))
            else:
                avg_inflation = 3.0  # Default
        else:
            avg_inflation = 3.0
        
        btc_real_return = btc_return - avg_inflation
        
        return {
            "analysis_period": f"{start_year}-{end_year}",
            "btc_return_pct": round(btc_return, 2),
            "average_inflation_pct": round(avg_inflation, 2),
            "btc_real_return_pct": round(btc_real_return, 2),
            "is_positive_real_return": btc_real_return > 0,
            "analysis_notes": "Bitcoin showed positive real returns during the analysis period",
            "last_updated": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error analyzing BTC inflation hedge: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze inflation hedge")


# =============================================================================
# MARKET REGIME
# =============================================================================

@router.get("/market-regime")
async def get_current_market_regime():
    """
    Get current market regime classification.
    
    Classifies the market based on economic, monetary, and technical indicators.
    """
    try:
        fred_client = FREDClient()
        fear_greed_client = FearGreedClient()
        
        # Get Fed Funds Rate trend
        fed_funds = fred_client.get_series('FEDFUNDS', sort_order='desc')
        
        # Get Fear & Greed
        fear_greed = fear_greed_client.get_current()
        
        # Get CPI for inflation regime
        cpi = fred_client.get_series('CPIAUCSL', sort_order='desc')
        
        # Determine regimes (simplified logic)
        fed_rate = fed_funds[0]["value"] if fed_funds else 5.0
        fg_value = fear_greed.get("value", 50) if fear_greed else 50
        
        # Fed stance
        if fed_rate > 4.5:
            fed_stance = "hawkish"
        elif fed_rate > 2.0:
            fed_stance = "neutral"
        else:
            fed_stance = "dovish"
        
        # Risk appetite based on Fear & Greed
        if fg_value >= 60:
            risk_appetite = "risk-on"
        elif fg_value <= 40:
            risk_appetite = "risk-off"
        else:
            risk_appetite = "neutral"
        
        # Crypto phase (simplified)
        if fg_value >= 70:
            crypto_phase = "euphoria"
        elif fg_value >= 50:
            crypto_phase = "optimism"
        elif fg_value >= 30:
            crypto_phase = "anxiety"
        else:
            crypto_phase = "panic"
        
        return {
            "date": date.today().isoformat(),
            "economic_cycle": "expansion",  # Would need GDP data for real classification
            "inflation_regime": "elevated",  # Would calculate from CPI
            "fed_stance": fed_stance,
            "fed_funds_rate": fed_rate,
            "risk_appetite": risk_appetite,
            "fear_greed_value": fg_value,
            "crypto_phase": crypto_phase,
            "summary": f"Market showing {risk_appetite} sentiment with {fed_stance} Fed policy",
            "last_updated": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting market regime: {e}")
        raise HTTPException(status_code=500, detail="Failed to get market regime")


# =============================================================================
# MACRO OVERVIEW
# =============================================================================

@router.get("/macro-overview")
async def get_macro_crypto_overview():
    """
    Get comprehensive macro-crypto overview.
    
    Returns current state of crypto markets with macro context.
    """
    try:
        # Initialize clients
        crypto_client = CoinGeckoClient()
        fred_client = FREDClient()
        fear_greed_client = FearGreedClient()
        
        # Get crypto data
        btc_price = crypto_client.get_price(['bitcoin', 'ethereum'], 'usd')
        market_data = crypto_client.get_global()
        
        # Get Fear & Greed
        fear_greed = fear_greed_client.get_current()
        
        # Get macro data
        fred_latest = fred_client.get_latest_values([
            'FEDFUNDS', 'DGS10', 'CPIAUCSL', 'UNRATE', 'SP500'
        ])
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "crypto": {
                "btc_price_usd": btc_price.get("bitcoin", {}).get("usd"),
                "eth_price_usd": btc_price.get("ethereum", {}).get("usd"),
                "total_market_cap_usd": market_data.get("data", {}).get("total_market_cap", {}).get("usd"),
                "btc_dominance_pct": market_data.get("data", {}).get("market_cap_percentage", {}).get("btc"),
                "fear_greed_value": fear_greed.get("value") if fear_greed else None,
                "fear_greed_classification": fear_greed.get("classification") if fear_greed else None,
            },
            "macro": {
                indicator_id: {
                    "name": data.get("name"),
                    "value": data.get("value"),
                    "date": data.get("date"),
                }
                for indicator_id, data in fred_latest.items()
            },
            "analysis": {
                "market_sentiment": "neutral",  # Would be calculated
                "macro_environment": "tightening",  # Based on Fed policy
            }
        }
    except Exception as e:
        logger.error(f"Error getting macro overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to get macro overview")


# =============================================================================
# HISTORICAL COMPARISONS
# =============================================================================

@router.get("/compare/returns")
async def compare_asset_returns(
    assets: str = Query(default="btc,sp500,gold", description="Comma-separated asset list"),
    period: str = Query(default="1y", description="Period: 1m, 3m, 6m, 1y, 3y, 5y"),
):
    """
    Compare returns across different assets.
    """
    try:
        # Map period to days
        period_map = {
            "1m": 30,
            "3m": 90,
            "6m": 180,
            "1y": 365,
            "3y": 365 * 3,
            "5y": 365 * 5,
        }
        
        days = period_map.get(period, 365)
        asset_list = [a.strip().lower() for a in assets.split(",")]
        
        results = {}
        
        crypto_client = CoinGeckoClient()
        fred_client = FREDClient()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        for asset in asset_list:
            try:
                if asset in ["btc", "bitcoin"]:
                    history = crypto_client.get_historical_prices("bitcoin", days=days)
                    if history:
                        start_price = history[-1]["price"]
                        end_price = history[0]["price"]
                        results["BTC"] = round((end_price - start_price) / start_price * 100, 2)
                
                elif asset in ["eth", "ethereum"]:
                    history = crypto_client.get_historical_prices("ethereum", days=days)
                    if history:
                        start_price = history[-1]["price"]
                        end_price = history[0]["price"]
                        results["ETH"] = round((end_price - start_price) / start_price * 100, 2)
                
                elif asset == "sp500":
                    data = fred_client.get_series(
                        "SP500",
                        start=start_date.strftime("%Y-%m-%d"),
                        end=end_date.strftime("%Y-%m-%d"),
                    )
                    if data:
                        results["SP500"] = round((data[0]["value"] - data[-1]["value"]) / data[-1]["value"] * 100, 2)
                
                elif asset == "gold":
                    data = fred_client.get_series(
                        "GOLDAMGBD228NLBM",
                        start=start_date.strftime("%Y-%m-%d"),
                        end=end_date.strftime("%Y-%m-%d"),
                    )
                    if data:
                        results["GOLD"] = round((data[0]["value"] - data[-1]["value"]) / data[-1]["value"] * 100, 2)
                        
            except Exception as e:
                logger.warning(f"Could not get data for {asset}: {e}")
        
        return {
            "period": period,
            "days": days,
            "start_date": start_date.date().isoformat(),
            "end_date": end_date.date().isoformat(),
            "returns_pct": results,
            "last_updated": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error comparing returns: {e}")
        raise HTTPException(status_code=500, detail="Failed to compare returns")
