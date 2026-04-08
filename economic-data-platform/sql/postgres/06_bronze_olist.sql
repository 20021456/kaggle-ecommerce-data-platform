-- =============================================================================
-- BRONZE SCHEMA - Olist Brazilian E-Commerce Dataset
-- Economic Data Analytics Platform
-- =============================================================================
-- 9 tables from the Olist public dataset (Kaggle).
-- Data stored exactly as received from CSV files.
-- Source: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
-- =============================================================================

SET search_path TO bronze, public;

-- =============================================================================
-- 1. ORDERS — Central transaction table
-- =============================================================================
CREATE TABLE IF NOT EXISTS bronze.olist_orders (
    id              BIGSERIAL PRIMARY KEY,
    ingested_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source_file     VARCHAR(200),

    order_id                        VARCHAR(32) NOT NULL,
    customer_id                     VARCHAR(32) NOT NULL,
    order_status                    VARCHAR(20) NOT NULL,
    order_purchase_timestamp        TIMESTAMP,
    order_approved_at               TIMESTAMP,
    order_delivered_carrier_date    TIMESTAMP,
    order_delivered_customer_date   TIMESTAMP,
    order_estimated_delivery_date   TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_olist_orders_order_id
    ON bronze.olist_orders(order_id);
CREATE INDEX IF NOT EXISTS idx_olist_orders_customer_id
    ON bronze.olist_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_olist_orders_status
    ON bronze.olist_orders(order_status);
CREATE INDEX IF NOT EXISTS idx_olist_orders_ingested
    ON bronze.olist_orders(ingested_at);

-- =============================================================================
-- 2. ORDER ITEMS — Line items per order
-- =============================================================================
CREATE TABLE IF NOT EXISTS bronze.olist_order_items (
    id              BIGSERIAL PRIMARY KEY,
    ingested_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source_file     VARCHAR(200),

    order_id            VARCHAR(32) NOT NULL,
    order_item_id       INTEGER NOT NULL,
    product_id          VARCHAR(32) NOT NULL,
    seller_id           VARCHAR(32) NOT NULL,
    shipping_limit_date TIMESTAMP,
    price               DECIMAL(10, 2),
    freight_value       DECIMAL(10, 2)
);

CREATE INDEX IF NOT EXISTS idx_olist_order_items_order_id
    ON bronze.olist_order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_olist_order_items_product_id
    ON bronze.olist_order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_olist_order_items_seller_id
    ON bronze.olist_order_items(seller_id);

-- =============================================================================
-- 3. CUSTOMERS
-- =============================================================================
CREATE TABLE IF NOT EXISTS bronze.olist_customers (
    id              BIGSERIAL PRIMARY KEY,
    ingested_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source_file     VARCHAR(200),

    customer_id             VARCHAR(32) NOT NULL,
    customer_unique_id      VARCHAR(32) NOT NULL,
    customer_zip_code_prefix VARCHAR(10),
    customer_city           VARCHAR(200),
    customer_state          VARCHAR(5)
);

CREATE INDEX IF NOT EXISTS idx_olist_customers_id
    ON bronze.olist_customers(customer_id);
CREATE INDEX IF NOT EXISTS idx_olist_customers_unique_id
    ON bronze.olist_customers(customer_unique_id);
CREATE INDEX IF NOT EXISTS idx_olist_customers_state
    ON bronze.olist_customers(customer_state);

-- =============================================================================
-- 4. PRODUCTS
-- =============================================================================
CREATE TABLE IF NOT EXISTS bronze.olist_products (
    id              BIGSERIAL PRIMARY KEY,
    ingested_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source_file     VARCHAR(200),

    product_id                  VARCHAR(32) NOT NULL,
    product_category_name       VARCHAR(200),
    product_name_lenght         INTEGER,      -- sic: original dataset typo
    product_description_lenght  INTEGER,      -- sic: original dataset typo
    product_photos_qty          INTEGER,
    product_weight_g            INTEGER,
    product_length_cm           INTEGER,
    product_height_cm           INTEGER,
    product_width_cm            INTEGER
);

CREATE INDEX IF NOT EXISTS idx_olist_products_id
    ON bronze.olist_products(product_id);
CREATE INDEX IF NOT EXISTS idx_olist_products_category
    ON bronze.olist_products(product_category_name);

-- =============================================================================
-- 5. SELLERS
-- =============================================================================
CREATE TABLE IF NOT EXISTS bronze.olist_sellers (
    id              BIGSERIAL PRIMARY KEY,
    ingested_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source_file     VARCHAR(200),

    seller_id               VARCHAR(32) NOT NULL,
    seller_zip_code_prefix  VARCHAR(10),
    seller_city             VARCHAR(200),
    seller_state            VARCHAR(5)
);

CREATE INDEX IF NOT EXISTS idx_olist_sellers_id
    ON bronze.olist_sellers(seller_id);
CREATE INDEX IF NOT EXISTS idx_olist_sellers_state
    ON bronze.olist_sellers(seller_state);

-- =============================================================================
-- 6. PAYMENTS
-- =============================================================================
CREATE TABLE IF NOT EXISTS bronze.olist_payments (
    id              BIGSERIAL PRIMARY KEY,
    ingested_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source_file     VARCHAR(200),

    order_id                VARCHAR(32) NOT NULL,
    payment_sequential      INTEGER NOT NULL,
    payment_type            VARCHAR(30) NOT NULL,
    payment_installments    INTEGER,
    payment_value           DECIMAL(10, 2)
);

CREATE INDEX IF NOT EXISTS idx_olist_payments_order_id
    ON bronze.olist_payments(order_id);
CREATE INDEX IF NOT EXISTS idx_olist_payments_type
    ON bronze.olist_payments(payment_type);

-- =============================================================================
-- 7. REVIEWS
-- =============================================================================
CREATE TABLE IF NOT EXISTS bronze.olist_reviews (
    id              BIGSERIAL PRIMARY KEY,
    ingested_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source_file     VARCHAR(200),

    review_id                VARCHAR(32) NOT NULL,
    order_id                 VARCHAR(32) NOT NULL,
    review_score             INTEGER NOT NULL,
    review_comment_title     TEXT,
    review_comment_message   TEXT,
    review_creation_date     TIMESTAMP,
    review_answer_timestamp  TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_olist_reviews_order_id
    ON bronze.olist_reviews(order_id);
CREATE INDEX IF NOT EXISTS idx_olist_reviews_score
    ON bronze.olist_reviews(review_score);

-- =============================================================================
-- 8. GEOLOCATION
-- =============================================================================
CREATE TABLE IF NOT EXISTS bronze.olist_geolocation (
    id              BIGSERIAL PRIMARY KEY,
    ingested_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source_file     VARCHAR(200),

    geolocation_zip_code_prefix VARCHAR(10) NOT NULL,
    geolocation_lat             DECIMAL(15, 10),
    geolocation_lng             DECIMAL(15, 10),
    geolocation_city            VARCHAR(200),
    geolocation_state           VARCHAR(5)
);

CREATE INDEX IF NOT EXISTS idx_olist_geo_zip
    ON bronze.olist_geolocation(geolocation_zip_code_prefix);
CREATE INDEX IF NOT EXISTS idx_olist_geo_state
    ON bronze.olist_geolocation(geolocation_state);

-- =============================================================================
-- 9. CATEGORY TRANSLATION (Portuguese → English)
-- =============================================================================
CREATE TABLE IF NOT EXISTS bronze.olist_category_translation (
    id              BIGSERIAL PRIMARY KEY,
    ingested_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source_file     VARCHAR(200),

    product_category_name           VARCHAR(200) NOT NULL,
    product_category_name_english   VARCHAR(200) NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_olist_category_name
    ON bronze.olist_category_translation(product_category_name);

-- =============================================================================
-- COMMENTS
-- =============================================================================
COMMENT ON TABLE bronze.olist_orders IS 'Raw orders from Olist Brazilian E-Commerce dataset';
COMMENT ON TABLE bronze.olist_order_items IS 'Raw order line items (products per order)';
COMMENT ON TABLE bronze.olist_customers IS 'Raw customer data with geographic info';
COMMENT ON TABLE bronze.olist_products IS 'Raw product catalog with dimensions';
COMMENT ON TABLE bronze.olist_sellers IS 'Raw seller data with geographic info';
COMMENT ON TABLE bronze.olist_payments IS 'Raw payment transactions per order';
COMMENT ON TABLE bronze.olist_reviews IS 'Raw customer reviews and ratings';
COMMENT ON TABLE bronze.olist_geolocation IS 'Raw geolocation data (zip → lat/lng)';
COMMENT ON TABLE bronze.olist_category_translation IS 'Product category Portuguese to English translation';
