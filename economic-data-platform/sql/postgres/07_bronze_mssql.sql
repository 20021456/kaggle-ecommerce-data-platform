-- =============================================================================
-- BRONZE SCHEMA - MSSQL Source Data (Auto-generated structure)
-- Economic Data Analytics Platform
-- =============================================================================
-- Tables from external MSSQL Server (45.124.94.158:1433/xomdata_dataset).
-- Actual table definitions are generated dynamically from MSSQL schema
-- discovery (see scripts/test_mssql_connection.py --generate-sql).
--
-- This file provides the base structure and a template for each table.
-- Run the generator to produce exact DDL matching the source schema.
-- =============================================================================

SET search_path TO bronze, public;

-- =============================================================================
-- MSSQL GENERIC STAGING TABLE
-- =============================================================================
-- Used when exact schema is unknown or for ad-hoc ingestion.
-- Stores all source data as JSONB for maximum flexibility.

CREATE TABLE IF NOT EXISTS bronze.mssql_raw (
    id              BIGSERIAL PRIMARY KEY,
    ingested_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    source_schema   VARCHAR(100) NOT NULL,
    source_table    VARCHAR(200) NOT NULL,
    source_row_id   VARCHAR(200),
    record_data     JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_mssql_raw_source
    ON bronze.mssql_raw(source_schema, source_table);
CREATE INDEX IF NOT EXISTS idx_mssql_raw_ingested
    ON bronze.mssql_raw(ingested_at);
CREATE INDEX IF NOT EXISTS idx_mssql_raw_data
    ON bronze.mssql_raw USING gin(record_data);

-- =============================================================================
-- MSSQL INGESTION LOG
-- =============================================================================
-- Tracks every ingestion run for auditing and monitoring.

CREATE TABLE IF NOT EXISTS bronze.mssql_ingestion_log (
    id              BIGSERIAL PRIMARY KEY,
    started_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    finished_at     TIMESTAMP WITH TIME ZONE,

    source_schema   VARCHAR(100) NOT NULL,
    source_table    VARCHAR(200) NOT NULL,
    row_count       INTEGER DEFAULT 0,
    parquet_size    BIGINT DEFAULT 0,
    minio_path      VARCHAR(500),
    status          VARCHAR(20) DEFAULT 'running',  -- running, success, failed
    error_message   TEXT
);

CREATE INDEX IF NOT EXISTS idx_mssql_log_table
    ON bronze.mssql_ingestion_log(source_schema, source_table);
CREATE INDEX IF NOT EXISTS idx_mssql_log_status
    ON bronze.mssql_ingestion_log(status);

-- =============================================================================
-- COMMENTS
-- =============================================================================
COMMENT ON TABLE bronze.mssql_raw IS 'Raw data from external MSSQL server stored as JSONB';
COMMENT ON TABLE bronze.mssql_ingestion_log IS 'Audit log of MSSQL ingestion runs';
COMMENT ON COLUMN bronze.mssql_raw.record_data IS 'Full row data as JSON object — keys match source column names';
