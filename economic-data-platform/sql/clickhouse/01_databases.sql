-- =============================================================================
-- ClickHouse Database Setup
-- Economic Data Analytics Platform
-- =============================================================================
-- ClickHouse uses databases (not schemas). We mirror the medallion layers.
-- =============================================================================

CREATE DATABASE IF NOT EXISTS bronze;
CREATE DATABASE IF NOT EXISTS silver;
CREATE DATABASE IF NOT EXISTS gold;
