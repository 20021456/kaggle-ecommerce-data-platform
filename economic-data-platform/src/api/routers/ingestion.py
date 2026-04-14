"""
Ingestion API Router — data-source monitoring endpoints.

Provides the Next.js *Ingestion Monitor* page with:
- Source catalogue (all known data sources)
- Per-source health / last-run status
- Ingestion run history (from Redis checkpoints)
- Row-count statistics (from PostgreSQL bronze tables)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import psycopg2
import psycopg2.extras
import redis
from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel, Field

from src.api.config import api_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# Known data sources registry
# ---------------------------------------------------------------------------

KNOWN_SOURCES: Dict[str, Dict[str, Any]] = {
    "olist": {
        "name": "Olist E-Commerce",
        "type": "csv",
        "domain": "ecommerce",
        "schedule": "weekly",
        "tables": [
            "orders",
            "order_items",
            "customers",
            "products",
            "sellers",
            "payments",
            "reviews",
            "geolocation",
            "product_category_name_translation",
        ],
    },
    "mssql": {
        "name": "MSSQL Server",
        "type": "database",
        "domain": "business",
        "schedule": "daily",
        "host": "45.124.94.158:1433",
        "tables": [],  # discovered dynamically
    },
    "coingecko": {
        "name": "CoinGecko",
        "type": "api",
        "domain": "crypto",
        "schedule": "every 5 min",
        "tables": ["markets", "coins", "global"],
    },
    "cryptocompare": {
        "name": "CryptoCompare",
        "type": "api",
        "domain": "crypto",
        "schedule": "hourly",
        "tables": ["ohlcv", "social"],
    },
    "blockchain": {
        "name": "Blockchain.info",
        "type": "api",
        "domain": "crypto",
        "schedule": "daily",
        "tables": ["stats"],
    },
    "fear_greed": {
        "name": "Fear & Greed Index",
        "type": "api",
        "domain": "crypto",
        "schedule": "daily",
        "tables": ["index"],
    },
    "fred": {
        "name": "FRED (Federal Reserve)",
        "type": "api",
        "domain": "economic",
        "schedule": "daily",
        "tables": ["series"],
    },
    "bea": {
        "name": "BEA (Bureau of Economic Analysis)",
        "type": "api",
        "domain": "economic",
        "schedule": "quarterly",
        "tables": ["gdp", "income"],
    },
    "bls": {
        "name": "BLS (Bureau of Labor Statistics)",
        "type": "api",
        "domain": "economic",
        "schedule": "monthly",
        "tables": ["unemployment", "cpi", "payrolls"],
    },
    "treasury": {
        "name": "US Treasury",
        "type": "api",
        "domain": "economic",
        "schedule": "daily",
        "tables": ["rates", "debt"],
    },
    "worldbank": {
        "name": "World Bank",
        "type": "api",
        "domain": "international",
        "schedule": "weekly",
        "tables": ["indicators", "countries"],
    },
}

# Bronze table mapping (source → PostgreSQL table names)
BRONZE_TABLE_MAP: Dict[str, List[str]] = {
    "olist": [
        "bronze.olist_orders",
        "bronze.olist_order_items",
        "bronze.olist_customers",
        "bronze.olist_products",
        "bronze.olist_sellers",
        "bronze.olist_payments",
        "bronze.olist_reviews",
        "bronze.olist_geolocation",
    ],
    "mssql": [],  # populated dynamically
}


# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------

_redis_client: Optional[redis.Redis] = None


def _get_redis() -> Optional[redis.Redis]:
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        _redis_client = redis.Redis(
            host=api_settings.REDIS_HOST,
            port=api_settings.REDIS_PORT,
            password=api_settings.REDIS_PASSWORD or None,
            db=api_settings.REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=2,
        )
        _redis_client.ping()
        return _redis_client
    except Exception as exc:
        logger.debug("Redis unavailable for ingestion monitoring: %s", exc)
        _redis_client = None
        return None


def _get_pg_conn():
    """Create a short-lived PostgreSQL connection."""
    return psycopg2.connect(
        host=api_settings.POSTGRES_HOST,
        port=api_settings.POSTGRES_PORT,
        user=api_settings.POSTGRES_USER,
        password=api_settings.POSTGRES_PASSWORD,
        dbname=api_settings.POSTGRES_DB,
        connect_timeout=5,
    )


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class SourceInfo(BaseModel):
    source_id: str
    name: str
    type: str  # api | database | csv
    domain: str
    schedule: str
    tables: List[str] = Field(default_factory=list)
    extra: Dict[str, Any] = Field(default_factory=dict)


class SourceStatus(BaseModel):
    source_id: str
    name: str
    status: str  # healthy | degraded | unknown | error
    last_ingestion: Optional[Dict[str, Any]] = None
    tables_ingested: int = 0
    total_rows: int = 0
    checked_at: str


class IngestionRecord(BaseModel):
    source: str
    table: str
    date: str
    row_count: int = 0
    minio_path: Optional[str] = None
    completed_at: Optional[str] = None


class IngestionStats(BaseModel):
    source_id: str
    name: str
    tables: List[Dict[str, Any]]
    total_rows: int


# ---------------------------------------------------------------------------
# Endpoints — Source catalogue
# ---------------------------------------------------------------------------

@router.get("/sources", response_model=List[SourceInfo])
async def list_sources(
    domain: Optional[str] = Query(
        None, description="Filter by domain (crypto, economic, ecommerce, international)"
    ),
):
    """
    List all known data sources.

    Optionally filter by domain.
    """
    result = []
    for src_id, meta in KNOWN_SOURCES.items():
        if domain and meta["domain"] != domain:
            continue
        extra = {k: v for k, v in meta.items() if k not in ("name", "type", "domain", "schedule", "tables")}
        result.append(
            SourceInfo(
                source_id=src_id,
                name=meta["name"],
                type=meta["type"],
                domain=meta["domain"],
                schedule=meta["schedule"],
                tables=meta.get("tables", []),
                extra=extra,
            )
        )
    return result


# ---------------------------------------------------------------------------
# Endpoints — Per-source status
# ---------------------------------------------------------------------------

@router.get("/sources/{source}/status", response_model=SourceStatus)
async def get_source_status(
    source: str = Path(..., description="Source identifier (e.g. olist, fred, coingecko)"),
):
    """
    Health check + last run info for a specific source.

    Reads the most recent Redis checkpoint to determine status.
    """
    if source not in KNOWN_SOURCES:
        raise HTTPException(status_code=404, detail=f"Unknown source: {source}")

    meta = KNOWN_SOURCES[source]
    r = _get_redis()

    last_ingestion: Optional[Dict[str, Any]] = None
    tables_ingested = 0
    total_rows = 0
    status = "unknown"

    if r:
        try:
            # Scan for all checkpoints belonging to this source
            pattern = f"checkpoint:{source}:*"
            keys = r.keys(pattern)
            tables_ingested = len(set(
                k.split(":")[2] for k in keys if k.count(":") >= 3
            ))

            # Find the most recent checkpoint
            latest_time = ""
            for key in keys:
                raw = r.get(key)
                if not raw:
                    continue
                info = json.loads(raw)
                total_rows += info.get("row_count", 0)
                completed = info.get("completed_at", "")
                if completed > latest_time:
                    latest_time = completed
                    last_ingestion = info

            if last_ingestion:
                status = "healthy"
            else:
                status = "unknown"
        except Exception as exc:
            logger.warning(f"Redis error reading checkpoints for {source}: {exc}")
            status = "degraded"
    else:
        status = "degraded"

    return SourceStatus(
        source_id=source,
        name=meta["name"],
        status=status,
        last_ingestion=last_ingestion,
        tables_ingested=tables_ingested,
        total_rows=total_rows,
        checked_at=datetime.now(timezone.utc).isoformat(),
    )


# ---------------------------------------------------------------------------
# Endpoints — Ingestion history
# ---------------------------------------------------------------------------

@router.get("/sources/{source}/history", response_model=List[IngestionRecord])
async def get_source_history(
    source: str = Path(..., description="Source identifier"),
    table: Optional[str] = Query(None, description="Filter by table name"),
    limit: int = Query(default=50, ge=1, le=500, description="Max records"),
):
    """
    Ingestion run history for a source, read from Redis checkpoints.

    Returns chronologically sorted list of ingestion records.
    """
    if source not in KNOWN_SOURCES:
        raise HTTPException(status_code=404, detail=f"Unknown source: {source}")

    r = _get_redis()
    if r is None:
        raise HTTPException(status_code=503, detail="Redis unavailable — cannot read history")

    table_pattern = table if table else "*"
    pattern = f"checkpoint:{source}:{table_pattern}:*"

    try:
        keys = r.keys(pattern)
    except Exception as exc:
        logger.error(f"Redis keys error: {exc}")
        raise HTTPException(status_code=503, detail="Redis error")

    records: List[IngestionRecord] = []
    for key in keys:
        raw = r.get(key)
        if not raw:
            continue
        info = json.loads(raw)
        records.append(
            IngestionRecord(
                source=info.get("source", source),
                table=info.get("table", ""),
                date=info.get("date", ""),
                row_count=info.get("row_count", 0),
                minio_path=info.get("minio_path"),
                completed_at=info.get("completed_at"),
            )
        )

    # Sort by completed_at descending
    records.sort(key=lambda r: r.completed_at or "", reverse=True)
    return records[:limit]


# ---------------------------------------------------------------------------
# Endpoints — Row-count statistics
# ---------------------------------------------------------------------------

@router.get("/stats", response_model=List[IngestionStats])
async def get_ingestion_stats(
    source: Optional[str] = Query(None, description="Filter by source"),
):
    """
    Row counts per source / table from PostgreSQL bronze layer.

    Falls back to Redis checkpoint row counts if PostgreSQL is unavailable.
    """
    sources_to_check = (
        {source: KNOWN_SOURCES[source]} if source and source in KNOWN_SOURCES else KNOWN_SOURCES
    )

    results: List[IngestionStats] = []

    # Try PostgreSQL for actual row counts
    pg_row_counts: Dict[str, int] = {}
    try:
        conn = _get_pg_conn()
        cur = conn.cursor()
        # Discover all bronze tables
        cur.execute(
            """
            SELECT schemaname || '.' || tablename AS full_name
            FROM pg_tables
            WHERE schemaname = 'bronze'
            ORDER BY tablename
            """
        )
        bronze_tables = [row[0] for row in cur.fetchall()]

        for tbl in bronze_tables:
            try:
                cur.execute(f"SELECT count(*) FROM {tbl}")  # noqa: S608
                pg_row_counts[tbl] = cur.fetchone()[0]
            except Exception as exc:
                logger.debug("Row count query failed for %s: %s", tbl, exc)
                pg_row_counts[tbl] = -1
                conn.rollback()

        cur.close()
        conn.close()
    except Exception as exc:
        logger.warning(f"PostgreSQL unavailable for stats: {exc}")

    for src_id, meta in sources_to_check.items():
        table_stats: List[Dict[str, Any]] = []
        total = 0

        # Match bronze tables to this source
        prefix = f"bronze.{src_id}_" if src_id != "olist" else "bronze.olist_"
        for tbl, count in pg_row_counts.items():
            if tbl.startswith(prefix):
                short_name = tbl.replace("bronze.", "")
                table_stats.append({"table": short_name, "row_count": count, "source": "postgresql"})
                if count > 0:
                    total += count

        # If no PG data, try Redis checkpoint totals
        if not table_stats:
            r = _get_redis()
            if r:
                try:
                    keys = r.keys(f"checkpoint:{src_id}:*")
                    seen_tables: Dict[str, int] = {}
                    for key in keys:
                        raw = r.get(key)
                        if not raw:
                            continue
                        info = json.loads(raw)
                        tbl_name = info.get("table", "unknown")
                        rc = info.get("row_count", 0)
                        seen_tables[tbl_name] = seen_tables.get(tbl_name, 0) + rc
                    for tbl_name, rc in seen_tables.items():
                        table_stats.append({"table": tbl_name, "row_count": rc, "source": "redis_checkpoint"})
                        total += rc
                except Exception as exc:
                    logger.debug("Redis checkpoint read error for %s: %s", src_id, exc)

        results.append(
            IngestionStats(
                source_id=src_id,
                name=meta["name"],
                tables=table_stats,
                total_rows=total,
            )
        )

    return results


# ---------------------------------------------------------------------------
# Endpoints — Overview
# ---------------------------------------------------------------------------

@router.get("/overview")
async def get_ingestion_overview():
    """
    High-level overview of all ingestion sources.

    Useful for the dashboard's quick-glance cards.
    """
    r = _get_redis()
    total_sources = len(KNOWN_SOURCES)
    healthy = 0
    degraded = 0
    unknown = 0
    total_rows = 0

    for src_id in KNOWN_SOURCES:
        if r:
            try:
                keys = r.keys(f"checkpoint:{src_id}:*")
                if keys:
                    healthy += 1
                    for key in keys:
                        raw = r.get(key)
                        if raw:
                            info = json.loads(raw)
                            total_rows += info.get("row_count", 0)
                else:
                    unknown += 1
            except Exception as exc:
                logger.debug("Redis overview error for %s: %s", src_id, exc)
                degraded += 1
        else:
            unknown += 1

    return {
        "total_sources": total_sources,
        "healthy": healthy,
        "degraded": degraded,
        "unknown": unknown,
        "total_rows_ingested": total_rows,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
