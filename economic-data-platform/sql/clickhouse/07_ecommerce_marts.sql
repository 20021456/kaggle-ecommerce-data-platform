-- =============================================================================
-- ClickHouse Gold Layer — E-Commerce Data Marts
-- =============================================================================
-- Replicated from PostgreSQL gold_ecommerce schema for fast analytics.
-- Populated via Airflow mart_export_dag or manual INSERT FROM s3().
-- =============================================================================

-- ─── Sales Daily Mart ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gold.ecommerce_sales_daily
(
    order_date          Date,
    order_count         UInt32,
    gross_revenue       Decimal128(2),
    net_revenue         Decimal128(2),
    total_freight       Decimal128(2),
    avg_order_value     Decimal128(2),
    items_sold          UInt32,
    unique_customers    UInt32,
    avg_review          Decimal64(2),
    canceled_orders     UInt32,
    cancellation_rate_pct Decimal64(2),
    top_category        String,
    top_payment_type    String,
    cumulative_revenue  Decimal128(2),
    revenue_7d_avg      Decimal128(2)
)
ENGINE = ReplacingMergeTree()
ORDER BY order_date;

-- ─── Sales Monthly Mart ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gold.ecommerce_sales_monthly
(
    month               Date,
    year_month          String,
    order_count         UInt32,
    gross_revenue       Decimal128(2),
    net_revenue         Decimal128(2),
    avg_order_value     Decimal128(2),
    unique_customers    UInt32,
    revenue_mom_pct     Decimal64(1),
    orders_mom_pct      Decimal64(1)
)
ENGINE = ReplacingMergeTree()
ORDER BY month;

-- ─── Customer Mart ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gold.ecommerce_customers
(
    customer_unique_id  String,
    state               LowCardinality(String),
    customer_segment    LowCardinality(String),
    order_count         UInt32,
    total_spend         Decimal128(2),
    avg_order_value     Decimal128(2),
    rfm_segment         LowCardinality(String),
    rfm_total           UInt8,
    estimated_annual_value Decimal128(2),
    is_churned          Bool,
    avg_review_score    Decimal64(2)
)
ENGINE = ReplacingMergeTree()
ORDER BY customer_unique_id;

-- ─── Logistics Daily Mart ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gold.ecommerce_logistics_daily
(
    order_date              Date,
    delivered_orders        UInt32,
    avg_delivery_days       Decimal64(1),
    median_delivery_days    Decimal64(1),
    p95_delivery_days       Decimal64(1),
    avg_freight             Decimal128(2),
    on_time_rate_pct        Decimal64(1),
    late_deliveries         UInt32,
    delivery_days_7d_avg    Decimal64(1),
    on_time_rate_7d_avg     Decimal64(1)
)
ENGINE = ReplacingMergeTree()
ORDER BY order_date;

-- ─── Logistics by State ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gold.ecommerce_logistics_by_state
(
    state                   LowCardinality(String),
    total_deliveries        UInt32,
    avg_delivery_days       Decimal64(1),
    avg_freight             Decimal128(2),
    on_time_rate_pct        Decimal64(1),
    avg_review              Decimal64(2),
    avg_order_value         Decimal128(2),
    total_freight_revenue   Decimal128(2)
)
ENGINE = ReplacingMergeTree()
ORDER BY state;
