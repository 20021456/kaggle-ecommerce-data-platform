-- =============================================================================
-- MinIO (S3) Integration — Cold storage & batch ingestion
-- =============================================================================
-- ClickHouse reads/writes to MinIO via s3() table function and S3 storage policy
-- =============================================================================

-- ─── STORAGE POLICY: Hot (local) + Cold (MinIO) ─────────────────────────────
-- Add to clickhouse config XML (config.d/storage.xml):
--
-- <storage_configuration>
--   <disks>
--     <default/>
--     <minio>
--       <type>s3</type>
--       <endpoint>http://minio:9000/gold/clickhouse/</endpoint>
--       <access_key_id>minioadmin</access_key_id>
--       <secret_access_key>minioadmin</secret_access_key>
--     </minio>
--   </disks>
--   <policies>
--     <tiered>
--       <volumes>
--         <hot><disk>default</disk></hot>
--         <cold><disk>minio</disk></cold>
--       </volumes>
--       <move_factor>0.2</move_factor>
--     </tiered>
--   </policies>
-- </storage_configuration>

-- ─── BATCH IMPORT FROM MINIO (Parquet files) ────────────────────────────────

-- Example: Load historical crypto prices from MinIO Parquet archive
-- INSERT INTO silver.crypto_prices_daily
-- SELECT
--     now64() AS processed_at,
--     coin_id, symbol, name, price_date,
--     open_price, high_price, low_price, close_price,
--     volume_usd, market_cap_usd,
--     price_change_pct, volatility,
--     'minio_archive' AS data_source,
--     0 AS is_imputed
-- FROM s3(
--     'http://minio:9000/bronze/crypto/prices/*.parquet',
--     'minioadmin', 'minioadmin',
--     'Parquet'
-- );

-- ─── S3Queue for continuous file ingestion from MinIO ────────────────────────

-- Auto-ingest new Parquet files dropped into MinIO bronze bucket
CREATE TABLE IF NOT EXISTS bronze._s3queue_crypto_files
(
    coin_id      String,
    symbol       String,
    price_date   Date,
    open_price   Decimal128(10),
    high_price   Decimal128(10),
    low_price    Decimal128(10),
    close_price  Decimal128(10),
    volume_usd   Decimal128(2),
    market_cap   Decimal128(2)
)
ENGINE = S3Queue('http://minio:9000/bronze/crypto/incoming/*.parquet',
                 'minioadmin', 'minioadmin', 'Parquet')
SETTINGS
    mode = 'unordered',
    s3queue_polling_min_timeout_ms = 5000,
    s3queue_polling_max_timeout_ms = 30000;

CREATE MATERIALIZED VIEW IF NOT EXISTS bronze.mv_s3queue_crypto
TO bronze.coingecko_prices AS
SELECT
    now64() AS ingested_at,
    coin_id,
    'usd' AS vs_currency,
    toInt64(toUnixTimestamp(toDateTime(price_date)) * 1000) AS timestamp_ms,
    close_price AS price,
    market_cap,
    volume_usd AS total_volume,
    '' AS raw_data
FROM bronze._s3queue_crypto_files;

-- ─── EXPORT TO MINIO (Gold → Parquet archive) ───────────────────────────────

-- Example: Export gold analytics to MinIO for external consumption
-- INSERT INTO FUNCTION s3(
--     'http://minio:9000/gold/exports/crypto_macro/{_partition_id}.parquet',
--     'minioadmin', 'minioadmin',
--     'Parquet'
-- )
-- PARTITION BY toYYYYMM(observation_date)
-- SELECT * FROM gold.fct_crypto_macro_daily;
