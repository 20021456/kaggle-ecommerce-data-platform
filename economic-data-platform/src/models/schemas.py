"""Pydantic data models and schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class EconomicDataRecord(BaseModel):
    """Base schema for economic data."""
    id: Optional[int] = None
    timestamp: datetime
    source: str
    value: float
    unit: Optional[str] = None
    metadata: Optional[dict] = None


class CryptoPrice(BaseModel):
    """Crypto price data schema."""
    symbol: str
    price: float
    timestamp: datetime
    volume_24h: Optional[float] = None
    market_cap: Optional[float] = None


class MSSQLRecord(BaseModel):
    """Generic MSSQL record schema."""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
