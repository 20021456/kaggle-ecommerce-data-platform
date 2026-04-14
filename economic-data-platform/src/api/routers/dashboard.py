"""
Dashboard API Router — analytics data endpoints for the Next.js UI.

Serves pre-aggregated KPIs, time-series trends, product rankings,
customer segments, and delivery performance from the Olist e-commerce
data stored in the Gold layer (ClickHouse primary, PostgreSQL fallback).

Endpoints:
- GET /kpis                  → headline metrics
- GET /revenue-trends        → revenue time-series (daily/weekly/monthly)
- GET /top-products          → product rankings by revenue
- GET /customer-segments     → RFM distribution
- GET /delivery-performance  → logistics metrics
- GET /order-status          → order status distribution
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import psycopg2
import psycopg2.extras
import redis
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.api.config import api_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

CACHE_TTL = 300  # 5 minutes

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
        logger.debug("Redis unavailable for dashboard cache: %s", exc)
        _redis_client = None
        return None


def _cache_key(endpoint: str, **params) -> str:
    raw = json.dumps(params, sort_keys=True, default=str)
    h = hashlib.md5(raw.encode()).hexdigest()[:12]
    return f"dashboard:{endpoint}:{h}"


def _cache_get(key: str) -> Optional[Any]:
    r = _get_redis()
    if r is None:
        return None
    try:
        raw = r.get(key)
        return json.loads(raw) if raw else None
    except Exception as exc:
        logger.debug("Cache read error for key %s: %s", key, exc)
        return None


def _cache_set(key: str, value: Any, ttl: int = CACHE_TTL) -> None:
    r = _get_redis()
    if r is None:
        return
    try:
        r.setex(key, ttl, json.dumps(value, default=str))
    except Exception as exc:
        logger.debug("Cache write error for key %s: %s", key, exc)


def _get_pg_conn():
    return psycopg2.connect(
        host=api_settings.POSTGRES_HOST,
        port=api_settings.POSTGRES_PORT,
        user=api_settings.POSTGRES_USER,
        password=api_settings.POSTGRES_PASSWORD,
        dbname=api_settings.POSTGRES_DB,
        connect_timeout=5,
    )


def _get_clickhouse():
    """Return a clickhouse-connect Client or None."""
    try:
        import clickhouse_connect

        return clickhouse_connect.get_client(
            host=api_settings.CLICKHOUSE_HOST,
            port=int(api_settings.CLICKHOUSE_PORT),
            username=api_settings.CLICKHOUSE_USER,
            password=api_settings.CLICKHOUSE_PASSWORD,
            database=api_settings.CLICKHOUSE_DB,
            connect_timeout=5,
        )
    except Exception as exc:
        logger.debug("ClickHouse unavailable: %s", exc)
        return None


def _query(sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    """Execute *sql* against ClickHouse first, fall back to PostgreSQL.

    Returns a list of dicts (column→value).
    """
    # --- ClickHouse attempt ---
    ch = _get_clickhouse()
    if ch is not None:
        try:
            result = ch.query(sql)
            cols = result.column_names
            return [dict(zip(cols, row)) for row in result.result_rows]
        except Exception as exc:
            logger.debug(f"ClickHouse query failed, falling back to PG: {exc}")
        finally:
            try:
                ch.close()
            except Exception as exc:
                logger.debug("ClickHouse close error: %s", exc)

    # --- PostgreSQL fallback ---
    try:
        conn = _get_pg_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        conn.close()
        return rows
    except Exception as exc:
        logger.error(f"Dashboard query failed on both backends: {exc}")
        raise HTTPException(status_code=503, detail="Database unavailable")


# ---------------------------------------------------------------------------
# Helper — schema-aware SQL
# ---------------------------------------------------------------------------

def _table(name: str) -> str:
    """Return the fully-qualified table name.

    Tries gold schema first; if the gold tables have not been
    materialised yet, callers should catch errors and retry with
    bronze/silver equivalents.
    """
    return f"gold.{name}"


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class KPIResponse(BaseModel):
    total_orders: int = 0
    total_revenue: float = 0.0
    total_customers: int = 0
    avg_order_value: float = 0.0
    avg_delivery_days: Optional[float] = None
    avg_review_score: Optional[float] = None
    on_time_delivery_pct: Optional[float] = None
    period: str = "all_time"
    generated_at: str = ""


class RevenueTrendPoint(BaseModel):
    period: str
    revenue: float
    order_count: int


class TopProduct(BaseModel):
    product_category: str
    revenue: float
    order_count: int
    avg_review_score: Optional[float] = None


class CustomerSegment(BaseModel):
    segment: str
    customer_count: int
    pct_of_total: float
    avg_monetary: Optional[float] = None


class DeliveryMetrics(BaseModel):
    avg_delivery_days: float
    on_time_pct: float
    late_pct: float
    avg_freight_value: float
    total_delivered: int
    generated_at: str = ""


class OrderStatusCount(BaseModel):
    status: str
    count: int
    pct: float


# ---------------------------------------------------------------------------
# Endpoints — KPIs
# ---------------------------------------------------------------------------

@router.get("/kpis", response_model=KPIResponse)
async def get_kpis(
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
):
    """
    Headline KPI metrics for the analytics dashboard.

    Tries the gold layer first; falls back to bronze Olist tables.
    """
    ck = _cache_key("kpis", start=start_date, end=end_date)
    cached = _cache_get(ck)
    if cached is not None:
        return cached

    date_filter = ""
    if start_date:
        date_filter += f" AND o.order_purchase_timestamp >= '{start_date}'"
    if end_date:
        date_filter += f" AND o.order_purchase_timestamp <= '{end_date}'"

    # Try gold layer
    sql = f"""
        SELECT
            count(DISTINCT o.order_id)                          AS total_orders,
            coalesce(sum(oi.price + oi.freight_value), 0)       AS total_revenue,
            count(DISTINCT o.customer_id)                       AS total_customers,
            coalesce(avg(oi.price + oi.freight_value), 0)       AS avg_order_value,
            avg(
                EXTRACT(EPOCH FROM (o.order_delivered_customer_date - o.order_purchase_timestamp)) / 86400
            )                                                   AS avg_delivery_days,
            avg(r.review_score)                                 AS avg_review_score
        FROM bronze.olist_orders        o
        LEFT JOIN bronze.olist_order_items oi ON oi.order_id = o.order_id
        LEFT JOIN bronze.olist_reviews     r  ON r.order_id  = o.order_id
        WHERE o.order_status = 'delivered'
        {date_filter}
    """

    try:
        rows = _query(sql)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"KPI query error: {exc}")
        raise HTTPException(status_code=503, detail="Could not compute KPIs")

    row = rows[0] if rows else {}

    total_orders = int(row.get("total_orders") or 0)
    total_revenue = float(row.get("total_revenue") or 0)

    # On-time delivery %
    on_time_sql = f"""
        SELECT
            count(*) FILTER (
                WHERE order_delivered_customer_date <= order_estimated_delivery_date
            ) * 100.0 / NULLIF(count(*), 0) AS on_time_pct
        FROM bronze.olist_orders
        WHERE order_status = 'delivered'
          AND order_delivered_customer_date IS NOT NULL
          AND order_estimated_delivery_date IS NOT NULL
          {date_filter.replace('o.', '')}
    """
    try:
        ot_rows = _query(on_time_sql)
        on_time_pct = float(ot_rows[0].get("on_time_pct") or 0) if ot_rows else None
    except Exception as exc:
        logger.debug("On-time delivery query error: %s", exc)
        on_time_pct = None

    result = KPIResponse(
        total_orders=total_orders,
        total_revenue=round(total_revenue, 2),
        total_customers=int(row.get("total_customers") or 0),
        avg_order_value=round(float(row.get("avg_order_value") or 0), 2),
        avg_delivery_days=round(float(row.get("avg_delivery_days") or 0), 1) if row.get("avg_delivery_days") else None,
        avg_review_score=round(float(row.get("avg_review_score") or 0), 2) if row.get("avg_review_score") else None,
        on_time_delivery_pct=round(on_time_pct, 1) if on_time_pct else None,
        period="all_time" if not start_date and not end_date else f"{start_date or '...'} to {end_date or '...'}",
        generated_at=datetime.now(timezone.utc).isoformat(),
    )

    _cache_set(ck, result.model_dump())
    return result


# ---------------------------------------------------------------------------
# Endpoints — Revenue trends
# ---------------------------------------------------------------------------

@router.get("/revenue-trends", response_model=List[RevenueTrendPoint])
async def get_revenue_trends(
    granularity: str = Query(
        default="monthly",
        description="Aggregation: daily, weekly, monthly",
    ),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    limit: int = Query(default=60, ge=1, le=365, description="Max data points"),
):
    """
    Revenue time-series at chosen granularity.
    """
    ck = _cache_key("revenue_trends", g=granularity, s=start_date, e=end_date, l=limit)
    cached = _cache_get(ck)
    if cached is not None:
        return cached

    trunc_map = {"daily": "day", "weekly": "week", "monthly": "month"}
    trunc = trunc_map.get(granularity, "month")

    date_filter = ""
    if start_date:
        date_filter += f" AND o.order_purchase_timestamp >= '{start_date}'"
    if end_date:
        date_filter += f" AND o.order_purchase_timestamp <= '{end_date}'"

    sql = f"""
        SELECT
            date_trunc('{trunc}', o.order_purchase_timestamp)::date AS period,
            coalesce(sum(oi.price + oi.freight_value), 0)          AS revenue,
            count(DISTINCT o.order_id)                              AS order_count
        FROM bronze.olist_orders        o
        JOIN bronze.olist_order_items   oi ON oi.order_id = o.order_id
        WHERE o.order_status != 'canceled'
        {date_filter}
        GROUP BY 1
        ORDER BY 1 DESC
        LIMIT {limit}
    """

    rows = _query(sql)
    result = [
        RevenueTrendPoint(
            period=str(r["period"]),
            revenue=round(float(r["revenue"]), 2),
            order_count=int(r["order_count"]),
        )
        for r in rows
    ]
    result.reverse()  # chronological order

    _cache_set(ck, [r.model_dump() for r in result])
    return result


# ---------------------------------------------------------------------------
# Endpoints — Top products
# ---------------------------------------------------------------------------

@router.get("/top-products", response_model=List[TopProduct])
async def get_top_products(
    limit: int = Query(default=20, ge=1, le=100, description="Number of categories"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """
    Product category rankings by total revenue.
    """
    ck = _cache_key("top_products", l=limit, s=start_date, e=end_date)
    cached = _cache_get(ck)
    if cached is not None:
        return cached

    date_filter = ""
    if start_date:
        date_filter += f" AND o.order_purchase_timestamp >= '{start_date}'"
    if end_date:
        date_filter += f" AND o.order_purchase_timestamp <= '{end_date}'"

    sql = f"""
        SELECT
            coalesce(p.product_category_name, 'unknown') AS product_category,
            sum(oi.price + oi.freight_value)             AS revenue,
            count(DISTINCT o.order_id)                   AS order_count,
            avg(r.review_score)                          AS avg_review_score
        FROM bronze.olist_order_items oi
        JOIN bronze.olist_orders      o ON o.order_id  = oi.order_id
        JOIN bronze.olist_products    p ON p.product_id = oi.product_id
        LEFT JOIN bronze.olist_reviews r ON r.order_id  = o.order_id
        WHERE o.order_status != 'canceled'
        {date_filter}
        GROUP BY 1
        ORDER BY revenue DESC
        LIMIT {limit}
    """

    rows = _query(sql)
    result = [
        TopProduct(
            product_category=r["product_category"],
            revenue=round(float(r["revenue"]), 2),
            order_count=int(r["order_count"]),
            avg_review_score=round(float(r["avg_review_score"]), 2) if r.get("avg_review_score") else None,
        )
        for r in rows
    ]

    _cache_set(ck, [r.model_dump() for r in result])
    return result


# ---------------------------------------------------------------------------
# Endpoints — Customer segments (RFM)
# ---------------------------------------------------------------------------

@router.get("/customer-segments", response_model=List[CustomerSegment])
async def get_customer_segments():
    """
    RFM-based customer segmentation distribution.

    Segments: Champions, Loyal, At Risk, Hibernating, New.
    Computed from order recency / frequency / monetary value.
    """
    ck = _cache_key("customer_segments")
    cached = _cache_get(ck)
    if cached is not None:
        return cached

    sql = """
        WITH rfm AS (
            SELECT
                customer_id,
                max(order_purchase_timestamp)                   AS last_order,
                count(DISTINCT order_id)                        AS frequency,
                sum(oi.price + oi.freight_value)                AS monetary
            FROM bronze.olist_orders o
            JOIN bronze.olist_order_items oi ON oi.order_id = o.order_id
            WHERE o.order_status = 'delivered'
            GROUP BY customer_id
        ),
        scored AS (
            SELECT *,
                ntile(5) OVER (ORDER BY last_order DESC)   AS r_score,
                ntile(5) OVER (ORDER BY frequency  ASC)    AS f_score,
                ntile(5) OVER (ORDER BY monetary   ASC)    AS m_score
            FROM rfm
        ),
        segmented AS (
            SELECT *,
                CASE
                    WHEN r_score >= 4 AND f_score >= 4 THEN 'Champions'
                    WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyal'
                    WHEN r_score >= 3 AND f_score <= 2 THEN 'New'
                    WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
                    ELSE 'Hibernating'
                END AS segment
            FROM scored
        )
        SELECT
            segment,
            count(*)                                AS customer_count,
            round(avg(monetary)::numeric, 2)        AS avg_monetary
        FROM segmented
        GROUP BY segment
        ORDER BY customer_count DESC
    """

    rows = _query(sql)
    total = sum(int(r["customer_count"]) for r in rows) or 1
    result = [
        CustomerSegment(
            segment=r["segment"],
            customer_count=int(r["customer_count"]),
            pct_of_total=round(int(r["customer_count"]) / total * 100, 1),
            avg_monetary=float(r["avg_monetary"]) if r.get("avg_monetary") else None,
        )
        for r in rows
    ]

    _cache_set(ck, [r.model_dump() for r in result])
    return result


# ---------------------------------------------------------------------------
# Endpoints — Delivery performance
# ---------------------------------------------------------------------------

@router.get("/delivery-performance", response_model=DeliveryMetrics)
async def get_delivery_performance(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """
    Logistics / delivery performance metrics.
    """
    ck = _cache_key("delivery_perf", s=start_date, e=end_date)
    cached = _cache_get(ck)
    if cached is not None:
        return cached

    date_filter = ""
    if start_date:
        date_filter += f" AND order_purchase_timestamp >= '{start_date}'"
    if end_date:
        date_filter += f" AND order_purchase_timestamp <= '{end_date}'"

    sql = f"""
        SELECT
            avg(
                EXTRACT(EPOCH FROM (order_delivered_customer_date - order_purchase_timestamp)) / 86400
            )                                                       AS avg_delivery_days,
            count(*) FILTER (
                WHERE order_delivered_customer_date <= order_estimated_delivery_date
            ) * 100.0 / NULLIF(count(*), 0)                        AS on_time_pct,
            count(*) FILTER (
                WHERE order_delivered_customer_date > order_estimated_delivery_date
            ) * 100.0 / NULLIF(count(*), 0)                        AS late_pct,
            count(*)                                                AS total_delivered
        FROM bronze.olist_orders
        WHERE order_status = 'delivered'
          AND order_delivered_customer_date IS NOT NULL
          {date_filter}
    """

    freight_sql = f"""
        SELECT avg(oi.freight_value) AS avg_freight
        FROM bronze.olist_order_items oi
        JOIN bronze.olist_orders      o ON o.order_id = oi.order_id
        WHERE o.order_status = 'delivered'
        {date_filter.replace("order_purchase_timestamp", "o.order_purchase_timestamp")}
    """

    rows = _query(sql)
    row = rows[0] if rows else {}

    try:
        freight_rows = _query(freight_sql)
        avg_freight = float(freight_rows[0].get("avg_freight") or 0) if freight_rows else 0
    except Exception as exc:
        logger.debug("Freight query error: %s", exc)
        avg_freight = 0

    result = DeliveryMetrics(
        avg_delivery_days=round(float(row.get("avg_delivery_days") or 0), 1),
        on_time_pct=round(float(row.get("on_time_pct") or 0), 1),
        late_pct=round(float(row.get("late_pct") or 0), 1),
        avg_freight_value=round(avg_freight, 2),
        total_delivered=int(row.get("total_delivered") or 0),
        generated_at=datetime.now(timezone.utc).isoformat(),
    )

    _cache_set(ck, result.model_dump())
    return result


# ---------------------------------------------------------------------------
# Endpoints — Order status distribution
# ---------------------------------------------------------------------------

@router.get("/order-status", response_model=List[OrderStatusCount])
async def get_order_status_distribution():
    """
    Distribution of order statuses (delivered, shipped, canceled, …).
    """
    ck = _cache_key("order_status")
    cached = _cache_get(ck)
    if cached is not None:
        return cached

    sql = """
        SELECT order_status AS status, count(*) AS cnt
        FROM bronze.olist_orders
        GROUP BY order_status
        ORDER BY cnt DESC
    """

    rows = _query(sql)
    total = sum(int(r["cnt"]) for r in rows) or 1
    result = [
        OrderStatusCount(
            status=r["status"],
            count=int(r["cnt"]),
            pct=round(int(r["cnt"]) / total * 100, 1),
        )
        for r in rows
    ]

    _cache_set(ck, [r.model_dump() for r in result])
    return result
