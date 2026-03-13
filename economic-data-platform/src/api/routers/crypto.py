"""
Crypto API Router - Cryptocurrency market data endpoints.

Provides endpoints for:
- Coin listings and metadata
- Current and historical prices
- Market statistics
- Fear & Greed Index
"""

from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query, HTTPException, Path
from pydantic import BaseModel, Field

from src.ingestion.crypto import CoinGeckoClient, FearGreedClient
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class CoinInfo(BaseModel):
    """Coin information model."""
    coin_id: str
    symbol: str
    name: str
    current_price_usd: Optional[float] = None
    market_cap_usd: Optional[float] = None
    market_cap_rank: Optional[int] = None
    price_change_24h_pct: Optional[float] = None
    volume_24h_usd: Optional[float] = None


class PriceData(BaseModel):
    """Price data model."""
    coin_id: str
    symbol: str
    timestamp: datetime
    price_usd: float
    volume_usd: Optional[float] = None
    market_cap_usd: Optional[float] = None


class HistoricalPrice(BaseModel):
    """Historical price data point."""
    date: date
    price: float
    volume: Optional[float] = None
    market_cap: Optional[float] = None


class FearGreedData(BaseModel):
    """Fear & Greed Index data."""
    date: date
    value: int
    classification: str
    sentiment_score: Optional[float] = None


class MarketOverview(BaseModel):
    """Market overview statistics."""
    total_market_cap_usd: float
    total_volume_24h_usd: float
    btc_dominance_pct: float
    active_coins: int
    last_updated: datetime


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/coins", response_model=List[CoinInfo])
async def get_coins(
    limit: int = Query(default=100, ge=1, le=500, description="Number of coins to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    order: str = Query(default="market_cap_desc", description="Sort order"),
):
    """
    Get list of cryptocurrencies with market data.
    
    Returns top coins sorted by market cap by default.
    """
    try:
        client = CoinGeckoClient()
        markets = client.get_markets(
            per_page=limit,
            page=(offset // limit) + 1,
            order=order,
        )
        
        return [
            CoinInfo(
                coin_id=coin.get("id"),
                symbol=coin.get("symbol", "").upper(),
                name=coin.get("name"),
                current_price_usd=coin.get("current_price"),
                market_cap_usd=coin.get("market_cap"),
                market_cap_rank=coin.get("market_cap_rank"),
                price_change_24h_pct=coin.get("price_change_percentage_24h"),
                volume_24h_usd=coin.get("total_volume"),
            )
            for coin in markets
        ]
    except Exception as e:
        logger.error(f"Error fetching coins: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch coin data")


@router.get("/coins/{coin_id}", response_model=Dict[str, Any])
async def get_coin_details(
    coin_id: str = Path(..., description="Coin ID (e.g., 'bitcoin', 'ethereum')"),
):
    """
    Get detailed information about a specific coin.
    
    Includes metadata, market data, and development stats.
    """
    try:
        client = CoinGeckoClient()
        coin = client.get_coin(coin_id)
        
        if not coin:
            raise HTTPException(status_code=404, detail=f"Coin {coin_id} not found")
        
        return coin
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching coin {coin_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch coin details")


@router.get("/prices/{symbol}", response_model=Dict[str, float])
async def get_current_price(
    symbol: str = Path(..., description="Coin symbol (e.g., 'BTC', 'ETH')"),
    currencies: str = Query(default="usd", description="Comma-separated target currencies"),
):
    """
    Get current price for a cryptocurrency.
    
    Returns price in specified currencies.
    """
    try:
        client = CoinGeckoClient()
        
        # Map common symbols to CoinGecko IDs
        symbol_map = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "USDT": "tether",
            "BNB": "binancecoin",
            "SOL": "solana",
            "XRP": "ripple",
            "ADA": "cardano",
            "DOGE": "dogecoin",
        }
        
        coin_id = symbol_map.get(symbol.upper(), symbol.lower())
        currencies_list = [c.strip() for c in currencies.split(",")]
        
        prices = client.get_price(coin_id, currencies_list)
        
        if coin_id not in prices:
            raise HTTPException(status_code=404, detail=f"Price not found for {symbol}")
        
        return prices[coin_id]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch price")


@router.get("/history/{coin_id}", response_model=List[HistoricalPrice])
async def get_price_history(
    coin_id: str = Path(..., description="Coin ID"),
    days: int = Query(default=30, ge=1, le=365, description="Number of days"),
    currency: str = Query(default="usd", description="Target currency"),
):
    """
    Get historical price data for a cryptocurrency.
    
    Returns daily OHLCV data for the specified period.
    """
    try:
        client = CoinGeckoClient()
        history = client.get_historical_prices(
            coin_id=coin_id,
            days=days,
            vs_currency=currency,
        )
        
        return [
            HistoricalPrice(
                date=item["date"].date() if item.get("date") else None,
                price=item.get("price"),
                volume=item.get("volume"),
                market_cap=item.get("market_cap"),
            )
            for item in history
            if item.get("date")
        ]
    except Exception as e:
        logger.error(f"Error fetching history for {coin_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch price history")


@router.get("/ohlc/{coin_id}")
async def get_ohlc_data(
    coin_id: str = Path(..., description="Coin ID"),
    days: int = Query(default=7, description="Number of days (1, 7, 14, 30, 90, 180, 365)"),
    currency: str = Query(default="usd", description="Target currency"),
):
    """
    Get OHLC (Open, High, Low, Close) candlestick data.
    
    Returns OHLC data for charting.
    """
    try:
        client = CoinGeckoClient()
        ohlc = client.get_coin_ohlc(coin_id, vs_currency=currency, days=days)
        
        return [
            {
                "timestamp": item[0],
                "open": item[1],
                "high": item[2],
                "low": item[3],
                "close": item[4],
            }
            for item in ohlc
        ]
    except Exception as e:
        logger.error(f"Error fetching OHLC for {coin_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch OHLC data")


@router.get("/fear-greed", response_model=FearGreedData)
async def get_fear_greed_index():
    """
    Get current Fear & Greed Index.
    
    The index measures market sentiment:
    - 0-24: Extreme Fear
    - 25-49: Fear
    - 50: Neutral
    - 51-74: Greed
    - 75-100: Extreme Greed
    """
    try:
        client = FearGreedClient()
        current = client.get_current()
        
        if not current:
            raise HTTPException(status_code=503, detail="Fear & Greed data unavailable")
        
        return FearGreedData(
            date=current["datetime"].date() if current.get("datetime") else date.today(),
            value=current.get("value", 0),
            classification=current.get("classification", "Unknown"),
            sentiment_score=current.get("sentiment_score"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Fear & Greed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Fear & Greed index")


@router.get("/fear-greed/history", response_model=List[FearGreedData])
async def get_fear_greed_history(
    days: int = Query(default=30, ge=1, le=365, description="Number of days"),
):
    """
    Get historical Fear & Greed Index data.
    """
    try:
        client = FearGreedClient()
        history = client.get_history(limit=days)
        
        return [
            FearGreedData(
                date=item["datetime"].date() if item.get("datetime") else None,
                value=item.get("value", 0),
                classification=item.get("classification", "Unknown"),
                sentiment_score=item.get("sentiment_score"),
            )
            for item in history
            if item.get("datetime")
        ]
    except Exception as e:
        logger.error(f"Error fetching Fear & Greed history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Fear & Greed history")


@router.get("/market/overview", response_model=Dict[str, Any])
async def get_market_overview():
    """
    Get overall cryptocurrency market statistics.
    
    Returns total market cap, volume, BTC dominance, etc.
    """
    try:
        client = CoinGeckoClient()
        global_data = client.get_global()
        
        data = global_data.get("data", {})
        
        return {
            "total_market_cap_usd": data.get("total_market_cap", {}).get("usd"),
            "total_volume_24h_usd": data.get("total_volume", {}).get("usd"),
            "btc_dominance_pct": data.get("market_cap_percentage", {}).get("btc"),
            "eth_dominance_pct": data.get("market_cap_percentage", {}).get("eth"),
            "active_cryptocurrencies": data.get("active_cryptocurrencies"),
            "markets": data.get("markets"),
            "market_cap_change_24h_pct": data.get("market_cap_change_percentage_24h_usd"),
            "last_updated": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error fetching market overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch market overview")


@router.get("/trending")
async def get_trending_coins():
    """
    Get trending cryptocurrencies.
    
    Returns coins that are trending based on search activity.
    """
    try:
        client = CoinGeckoClient()
        trending = client.get_trending()
        
        return trending
    except Exception as e:
        logger.error(f"Error fetching trending: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trending coins")
