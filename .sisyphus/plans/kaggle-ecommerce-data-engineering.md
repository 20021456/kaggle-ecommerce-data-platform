# 🎯 E-Commerce Data Engineering Platform — Implementation Plan v2

## 📋 Project Overview

**Mục tiêu:** Xây dựng hệ thống Data Engineering hoàn chỉnh với dual data sources (Kaggle Olist + MSSQL Server), data lake nhỏ gọn (MinIO Parquet + Trino), Data Warehouse (PostgreSQL + ClickHouse), Data Marts (star schema), orchestration (Airflow), monitoring (Prometheus + Grafana), và management UI (Next.js).

**Data Sources:**
- **Olist (Local CSV):** Brazilian E-Commerce dataset — 9 CSV files pre-downloaded in `data/raw/olist/`, 100k+ orders (2016-2018)
- **MSSQL Server:** External database at `45.124.94.158:1433/xomdata_dataset` — production business data

**Core Architecture Change (v1 → v2):**
- ~~HDFS cluster~~ → **MinIO** (S3-compatible, already deployed) + **Trino** (SQL query engine)
- Dual ingestion: Kaggle API client (new) + MSSQL client (exists)
- UI: 3 management pages (Airflow monitor, Ingestion monitor, Analytics dashboard)
- Feasibility: proxy all monitoring through FastAPI backend → Next.js frontend

**Tech Stack:**
- **Data Sources:** Kaggle API + MSSQL Server (pymssql)
- **Data Lake:** MinIO (Parquet files) — bronze/silver/gold buckets
- **Query Engine:** Trino (Hive connector → MinIO S3) for federated queries
- **Storage:** PostgreSQL (OLTP, dbt target), ClickHouse (OLAP, analytics)
- **Processing:** dbt (SQL transforms), Apache Spark (optional heavy jobs)
- **Orchestration:** Apache Airflow
- **Monitoring:** Prometheus + Grafana + Great Expectations
- **UI:** Next.js + shadcn/ui — Airflow monitor, Ingestion monitor, Dashboard
- **API:** FastAPI — proxies Airflow API, serves ingestion metrics, analytics data
- **Deployment:** Dokploy (Docker PaaS)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 0: DATA SOURCES                         │
│                                                                  │
│  Kaggle API → Olist Dataset (9 CSV tables)     ✨ NEW CLIENT    │
│  MSSQL Server → xomdata_dataset               ✅ EXISTS         │
│  (45.124.94.158:1433)                                           │
└──────────────┬──────────────────────────┬───────────────────────┘
               │                          │
               ▼                          ▼
┌─────────────────────────────────────────────────────────────────┐
│           LAYER 1: DATA LAKE — MinIO (S3-compatible)            │
│                                                                  │
│  bronze/olist/{table}/YYYY-MM-DD.parquet                        │
│  bronze/mssql/{table}/YYYY-MM-DD.parquet                        │
│  silver/... (cleaned, typed)                                    │
│  gold/... (analytics-ready)                                     │
│                                                                  │
│  ✅ MinIO already deployed (docker-compose.yml)                  │
│  ✅ MinIOClient already built (data_platform/io/minio_client.py) │
│  ✅ Auto bucket creation (bronze/silver/gold)                    │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│     LAYER 2: QUERY ENGINE — Trino + Hive Metastore ✨ NEW       │
│                                                                  │
│  Trino (trinodb/trino) → Hive connector → MinIO S3             │
│  Hive Metastore → PostgreSQL (metadata catalog)                 │
│  Enables SQL queries directly on MinIO Parquet files            │
│  CREATE SCHEMA minio.bronze / minio.silver / minio.gold         │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│        LAYER 3: DATA WAREHOUSE (PostgreSQL + ClickHouse)         │
│                                                                  │
│  PostgreSQL (OLTP): ✅ EXISTS                                    │
│  - bronze_* tables (raw from ingestion)                          │
│  - dbt staging/intermediate models                               │
│                                                                  │
│  ClickHouse (OLAP): ✅ EXISTS                                    │
│  - gold_* tables (analytics-ready, fast aggregations)            │
│  - S3Queue from MinIO (auto-ingest Parquet)                     │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│     LAYER 4: TRANSFORMATIONS — dbt (staging → marts)             │
│                                                                  │
│  ✅ dbt project exists (crypto + economic models)                │
│  ✨ NEW: Olist staging/intermediate/marts models                 │
│  Star Schema: fct_orders + dim_customers/products/sellers/time  │
│  Business Marts: sales_mart, customer_mart, logistics_mart      │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│     LAYER 5: DATA MARTS (Dimensional Models in ClickHouse)       │
│                                                                  │
│  fct_orders (fact), dim_customers, dim_products, dim_sellers     │
│  dim_time, dim_geography                                        │
│  sales_mart: Revenue, trends, payment analysis                  │
│  customer_mart: RFM segmentation, LTV, churn                   │
│  logistics_mart: Delivery times, freight cost, seller perf      │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│         LAYER 6: ORCHESTRATION — Airflow ✅ EXISTS               │
│                                                                  │
│  DAGs:                                                           │
│  - kaggle_ingestion_dag ✨ NEW: Kaggle API → MinIO              │
│  - mssql_ingestion_dag ✨ NEW: MSSQL → MinIO                   │
│  - dbt_transformation_dag ✨ NEW: Olist dbt models              │
│  - data_quality_dag ✨ NEW: Great Expectations                  │
│  - etl_daily ✅ EXISTS (crypto + economic)                      │
│                                                                  │
│  Airflow REST API → FastAPI proxy → Next.js UI                  │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│    LAYER 7: SERVING & MONITORING                                 │
│                                                                  │
│  FastAPI ✅ EXISTS (extend with Airflow proxy + ingestion API)   │
│  Next.js UI ⚠️ NEEDS 3 NEW PAGES:                               │
│    1. Airflow Monitor: DAG status, run history, trigger         │
│    2. Ingestion Monitor: sources, row counts, health            │
│    3. Analytics Dashboard: KPIs, charts, trends                 │
│  Grafana ✅ EXISTS: Infrastructure dashboards                    │
│  Prometheus ✅ EXISTS: Metrics collection                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔌 UI Architecture Decision

**Approach: FastAPI Backend Proxy → Next.js Frontend**

```
Next.js UI → FastAPI /api/v1/monitor/* → Airflow REST API (basic auth)
Next.js UI → FastAPI /api/v1/ingestion/* → PostgreSQL/Redis metrics
Next.js UI → FastAPI /api/v1/analytics/* → ClickHouse/PostgreSQL queries
```

**Why proxy through FastAPI (not direct Airflow API from browser):**
- Airflow API uses basic auth — can't expose credentials to browser
- Unify all APIs under one endpoint (8000)
- Add caching, rate limiting, error handling in one place
- CORS already configured on FastAPI

---

## ✅ Implementation Tasks (42 Tasks)

### Phase 1: Infrastructure Setup (5 tasks)

- [ ] **T1.1:** Add Trino + Hive Metastore to docker-compose
  - Add `trino` service (trinodb/trino:latest)
  - Add `hive-metastore` service with PostgreSQL backend (reuse existing PG)
  - Create Trino catalog config: `etc/catalog/minio.properties` (Hive connector → MinIO)
  - Create Trino configs: `config.properties`, `jvm.config`, `node.properties`
  - Create Hive Metastore `metastore-site.xml` (S3 endpoint → MinIO)
  - Mount configs via volumes
  - **Port mapping:** Trino UI at 8085 (avoid conflict with Airflow 8080)
  - **Depends on:** minio, postgres
  - **Parallelizable:** No
  - **Estimated time:** 4 hours

- [ ] **T1.2:** Configure Trino-MinIO integration
  - Create Trino schemas: `minio.bronze`, `minio.silver`, `minio.gold`
  - Test CREATE TABLE with Parquet format pointing to MinIO
  - Test INSERT/SELECT on Parquet files in MinIO
  - Verify ClickHouse S3Queue still works alongside Trino
  - **Parallelizable:** No (depends on T1.1)
  - **Estimated time:** 2 hours

- [ ] **T1.3:** Configure Airflow REST API
  - Enable Airflow REST API via environment variables
  - Set `AIRFLOW__API__AUTH_BACKENDS=airflow.api.auth.backend.basic_auth`
  - Create API user: `airflow users create --role Admin --username api_user`
  - Test API endpoints: GET /api/v1/dags, /api/v1/dagRuns
  - **Parallelizable:** Yes (with T1.1)
  - **Estimated time:** 1 hour

- [ ] **T1.4:** Update Dokploy deployment configs
  - Update `dokploy/shared-databases/docker-compose.yml` with Trino + Hive
  - Update `dokploy/application/docker-compose.yml`
  - Update `.env.example` with Trino settings
  - **Parallelizable:** Yes (with T1.2)
  - **Estimated time:** 2 hours

- [ ] **T1.5:** Verify all services running
  - `docker-compose up -d` full stack
  - Health check: PostgreSQL, ClickHouse, Redis, Kafka, MinIO, Trino, Airflow
  - Verify MinIO buckets (bronze/silver/gold)
  - Verify Trino UI accessible
  - Verify Airflow REST API accessible
  - **Parallelizable:** No (depends on all above)
  - **Estimated time:** 1 hour

### Phase 2: Data Ingestion Layer (5 tasks)

- [ ] **T2.1:** Create Kaggle API client
  - Install `kaggle` package
  - Create `ingestion/custom/api/ecommerce/kaggle_client.py`
  - Extend `BaseAPIClient` pattern from existing clients
  - Methods: `download_dataset()`, `extract_csvs()`, `get_dataset_metadata()`
  - Download Olist dataset: `olistbr/brazilian-ecommerce`
  - Parse 9 CSV files into DataFrames
  - Store Kaggle credentials in `.env` (KAGGLE_USERNAME, KAGGLE_KEY)
  - **Parallelizable:** No
  - **Estimated time:** 3 hours

- [ ] **T2.2:** Build Olist data validation module
  - Create schema validators for 9 Olist CSV tables
  - Validate: column names, data types, nulls, referential integrity
  - Validate: order_id → customer_id, product_id → seller_id relationships
  - Use Pydantic models for each table
  - Log validation results to Prometheus metrics
  - **Parallelizable:** Yes (with T2.1)
  - **Estimated time:** 4 hours

- [ ] **T2.3:** Create MinIO data lake loader (Olist)
  - Write Olist CSVs to MinIO as Parquet: `bronze/olist/{table}/YYYY-MM-DD.parquet`
  - Use existing `MinIOClient.write_to_layer()`
  - Add partition-by-date logic
  - Test read-back with `MinIOClient.read_from_layer()`
  - Verify Trino can query the Parquet files
  - **Parallelizable:** No (depends on T2.1, T1.2)
  - **Estimated time:** 3 hours

- [ ] **T2.4:** Create MinIO data lake loader (MSSQL)
  - Read tables from MSSQL using existing `MSSQLClient`
  - Write to MinIO as Parquet: `bronze/mssql/{table}/YYYY-MM-DD.parquet`
  - Handle large tables with batched reads
  - Track ingestion progress in Redis (checkpoint)
  - **Parallelizable:** Yes (with T2.3)
  - **Estimated time:** 3 hours

- [ ] **T2.5:** Build ingestion checkpoint manager
  - Track which tables/dates have been ingested
  - Store checkpoints in Redis
  - Implement resume logic (skip already-ingested partitions)
  - Support both Kaggle and MSSQL sources
  - **Parallelizable:** Yes (with T2.3)
  - **Estimated time:** 2 hours

### Phase 3: PostgreSQL Bronze Layer (4 tasks)

- [ ] **T3.1:** Create Olist bronze schema DDL
  - Create `sql/postgres/06_bronze_olist.sql`
  - 9 tables: `bronze.olist_orders`, `bronze.olist_order_items`, `bronze.olist_customers`, etc.
  - Match exact Kaggle CSV column names and types
  - Add `ingested_at`, `source_file` metadata columns
  - Create indexes on primary keys and ingested_at
  - **Parallelizable:** No
  - **Estimated time:** 3 hours

- [ ] **T3.2:** Create MSSQL bronze schema DDL
  - Create `sql/postgres/07_bronze_mssql.sql`
  - Auto-generate from MSSQL schema discovery (use test_mssql_connection.py --generate-sql)
  - Add `ingested_at`, `source_schema`, `source_table` metadata columns
  - **Parallelizable:** Yes (with T3.1)
  - **Estimated time:** 2 hours

- [ ] **T3.3:** Build MinIO → PostgreSQL loader
  - Read Parquet from MinIO bronze bucket
  - Insert into PostgreSQL bronze tables
  - Handle upserts (avoid duplicates on re-runs)
  - Track load metrics (rows inserted, duration)
  - **Parallelizable:** No (depends on T3.1, T3.2)
  - **Estimated time:** 4 hours

- [ ] **T3.4:** Verify data quality in bronze layer
  - Row count validation (MinIO Parquet vs PostgreSQL bronze)
  - Spot-check column values
  - Test Trino queries against MinIO match PostgreSQL bronze
  - **Parallelizable:** No (depends on T3.3)
  - **Estimated time:** 2 hours

### Phase 4: dbt Transformations — Olist (4 tasks)

- [ ] **T4.1:** Add Olist sources to dbt
  - Update `dbt/models/sources/sources.yml` with olist source tables
  - Add source freshness tests
  - Define relationships between tables
  - **Parallelizable:** No
  - **Estimated time:** 2 hours

- [ ] **T4.2:** Create Olist staging models (Silver)
  - `stg_olist_orders.sql` — clean timestamps, status enum
  - `stg_olist_order_items.sql` — clean prices, freight values
  - `stg_olist_customers.sql` — standardize city/state names
  - `stg_olist_products.sql` — translate categories, clean dimensions
  - `stg_olist_sellers.sql` — standardize location data
  - `stg_olist_payments.sql` — clean payment types, installments
  - `stg_olist_reviews.sql` — clean review text, normalize scores
  - Create `_olist_stagings.yml` with tests and docs
  - **Parallelizable:** No (depends on T4.1)
  - **Estimated time:** 6 hours

- [ ] **T4.3:** Create Olist intermediate models
  - `int_orders_enriched.sql` — join orders + items + payments + reviews
  - `int_customer_metrics.sql` — aggregate customer stats (order count, total spend, avg review)
  - `int_product_performance.sql` — product sales, revenue, review scores
  - `int_seller_performance.sql` — seller metrics, delivery times
  - Create `_olist_intermediate.yml` with tests
  - **Parallelizable:** No (depends on T4.2)
  - **Estimated time:** 5 hours

- [ ] **T4.4:** Create dimensional models (Gold layer)
  - `dim_customers.sql` — customer dimension with segments
  - `dim_products.sql` — product dimension with categories
  - `dim_sellers.sql` — seller dimension with geography
  - `dim_time.sql` — date dimension (year, quarter, month, week, day)
  - `dim_geography.sql` — geographic dimension (city, state, region)
  - `fct_orders.sql` — central fact table with all foreign keys
  - Create `_olist_marts.yml` with tests and docs
  - **Parallelizable:** No (depends on T4.3)
  - **Estimated time:** 6 hours

### Phase 5: Data Marts (4 tasks)

- [ ] **T5.1:** Build sales_mart
  - Daily/weekly/monthly revenue aggregations
  - Product category performance rankings
  - Payment method distribution analysis
  - Seasonal trends and forecasting features
  - Write to ClickHouse for fast queries
  - **Parallelizable:** No (depends on T4.4)
  - **Estimated time:** 4 hours

- [ ] **T5.2:** Build customer_mart
  - RFM segmentation (Recency, Frequency, Monetary)
  - Customer lifetime value (CLV) calculations
  - Geographic distribution analysis
  - Churn prediction features
  - **Parallelizable:** Yes (with T5.1)
  - **Estimated time:** 4 hours

- [ ] **T5.3:** Build logistics_mart
  - Delivery time analysis (estimated vs actual)
  - Freight cost optimization insights
  - Seller performance by region
  - Late delivery rate calculations
  - **Parallelizable:** Yes (with T5.1, T5.2)
  - **Estimated time:** 4 hours

- [ ] **T5.4:** Create mart refresh strategy
  - Incremental vs full refresh logic for each mart
  - Schedule optimization (which marts when)
  - Dependency management between marts
  - Write refresh to MinIO gold bucket (Parquet archive)
  - **Parallelizable:** No (depends on T5.1-T5.3)
  - **Estimated time:** 3 hours

### Phase 6: Orchestration — Airflow DAGs (5 tasks)

- [ ] **T6.1:** Create kaggle_ingestion_dag
  - Task 1: Download from Kaggle API
  - Task 2: Validate CSV schemas
  - Task 3: Convert to Parquet + upload to MinIO bronze
  - Task 4: Load from MinIO to PostgreSQL bronze
  - Task 5: Update Redis checkpoint
  - Schedule: Weekly (Olist data is static, re-download for freshness)
  - **Parallelizable:** No
  - **Estimated time:** 4 hours

- [ ] **T6.2:** Create mssql_ingestion_dag
  - Task 1: Connect to MSSQL, list tables
  - Task 2: Read tables (batched for large ones)
  - Task 3: Write to MinIO bronze as Parquet
  - Task 4: Load from MinIO to PostgreSQL bronze
  - Task 5: Update Redis checkpoint
  - Schedule: Daily at 2 AM
  - **Parallelizable:** Yes (with T6.1)
  - **Estimated time:** 4 hours

- [ ] **T6.3:** Create dbt_olist_dag
  - Task 1: dbt run --select tag:olist,tag:staging
  - Task 2: dbt run --select tag:olist,tag:intermediate
  - Task 3: dbt run --select tag:olist,tag:mart
  - Task 4: dbt test --select tag:olist
  - Schedule: Daily at 4 AM (after ingestion)
  - **Parallelizable:** Yes (with T6.2)
  - **Estimated time:** 3 hours

- [ ] **T6.4:** Create data_quality_dag
  - Task 1: Run Great Expectations suites on bronze tables
  - Task 2: Check data freshness (last ingestion timestamp)
  - Task 3: Validate mart row counts and metrics
  - Task 4: Send alerts on failure (email/Slack)
  - Schedule: Daily at 5 AM (after transforms)
  - **Parallelizable:** Yes (with T6.3)
  - **Estimated time:** 4 hours

- [ ] **T6.5:** Create mart_export_dag
  - Task 1: Export gold marts from PostgreSQL → ClickHouse
  - Task 2: Archive gold data to MinIO gold bucket (Parquet)
  - Task 3: Refresh Trino table metadata
  - Task 4: Invalidate Redis cache
  - Schedule: Daily at 6 AM (after quality checks)
  - **Parallelizable:** Yes (with T6.4)
  - **Estimated time:** 3 hours

### Phase 7: FastAPI Backend Extensions (4 tasks)

- [ ] **T7.1:** Create Airflow proxy router
  - New router: `src/api/routers/monitor.py`
  - Proxy endpoints:
    - GET /api/v1/monitor/dags → Airflow GET /api/v1/dags
    - GET /api/v1/monitor/dags/{dag_id}/runs → Airflow dagRuns
    - GET /api/v1/monitor/dags/{dag_id}/runs/{run_id}/tasks → task instances
    - POST /api/v1/monitor/dags/{dag_id}/trigger → trigger DAG run
    - PATCH /api/v1/monitor/dags/{dag_id} → pause/unpause
  - Basic auth to Airflow (credentials from .env, never exposed to frontend)
  - Add Redis caching (60s TTL for DAG list, 10s for runs)
  - **Parallelizable:** No
  - **Estimated time:** 4 hours

- [ ] **T7.2:** Create ingestion metrics router
  - New router: `src/api/routers/ingestion.py`
  - Endpoints:
    - GET /api/v1/ingestion/sources — list all sources (kaggle, mssql, crypto APIs)
    - GET /api/v1/ingestion/sources/{source}/status — health check + last run
    - GET /api/v1/ingestion/sources/{source}/history — ingestion run history
    - GET /api/v1/ingestion/stats — row counts per source, per table
  - Read from Redis checkpoints + PostgreSQL metadata
  - **Parallelizable:** Yes (with T7.1)
  - **Estimated time:** 3 hours

- [ ] **T7.3:** Create analytics data router
  - New router: `src/api/routers/dashboard.py`
  - Endpoints:
    - GET /api/v1/dashboard/kpis — key metrics (total orders, revenue, customers)
    - GET /api/v1/dashboard/revenue-trends — time series data
    - GET /api/v1/dashboard/top-products — product rankings
    - GET /api/v1/dashboard/customer-segments — RFM distribution
    - GET /api/v1/dashboard/delivery-performance — logistics metrics
  - Query from ClickHouse (fast) or PostgreSQL gold tables
  - Cache results in Redis (5 min TTL)
  - **Parallelizable:** Yes (with T7.1, T7.2)
  - **Estimated time:** 4 hours

- [ ] **T7.4:** Add Trino query endpoint
  - Endpoint: POST /api/v1/query/trino — execute SQL on Trino
  - Read-only queries against MinIO data lake
  - Pagination, timeout, result size limits
  - For ad-hoc exploration of raw data in MinIO
  - **Parallelizable:** Yes (with T7.3)
  - **Estimated time:** 2 hours

### Phase 8: Next.js UI — Management Pages (5 tasks)

- [ ] **T8.1:** Create Airflow Monitor page
  - Route: `/monitor/airflow`
  - Components:
    - DAG list table (name, schedule, last run, status, actions)
    - DAG run history timeline
    - Task instance status grid (success/failed/running/queued)
    - Trigger DAG button + pause/unpause toggle
  - Fetch from FastAPI `/api/v1/monitor/*`
  - Auto-refresh every 30s
  - **Parallelizable:** No
  - **Estimated time:** 6 hours

- [ ] **T8.2:** Create Ingestion Monitor page
  - Route: `/monitor/ingestion`
  - Components:
    - Source cards (Kaggle, MSSQL, CoinGecko, FRED, etc.)
    - Health status badges (green/yellow/red)
    - Row count table per source per table
    - Last ingestion timestamp + next scheduled
    - Ingestion history chart (rows/day over time)
  - Fetch from FastAPI `/api/v1/ingestion/*`
  - **Parallelizable:** Yes (with T8.1)
  - **Estimated time:** 5 hours

- [ ] **T8.3:** Create Analytics Dashboard page
  - Route: `/dashboard`
  - Components:
    - KPI cards (total orders, revenue, avg order value, avg delivery time)
    - Revenue trend chart (line chart, daily/weekly/monthly toggle)
    - Top products bar chart
    - Customer segment pie chart (RFM)
    - Delivery performance gauge
    - Geographic heatmap (orders by state)
  - Use charting library (recharts or chart.js)
  - Fetch from FastAPI `/api/v1/dashboard/*`
  - **Parallelizable:** Yes (with T8.1, T8.2)
  - **Estimated time:** 8 hours

- [ ] **T8.4:** Update sidebar navigation
  - Add new sections:
    - "Monitoring": Airflow Monitor, Ingestion Monitor
    - "Analytics": Dashboard
  - Keep existing "Báo cáo" section
  - Active state highlighting
  - Icon updates (lucide-react)
  - **Parallelizable:** Yes (with T8.1)
  - **Estimated time:** 1 hour

- [ ] **T8.5:** Add shared UI components
  - StatusBadge component (healthy/degraded/error)
  - RefreshButton with auto-refresh toggle
  - DataTable with sorting/filtering/pagination
  - KPICard component
  - TimeSeriesChart wrapper
  - **Parallelizable:** Yes (with T8.1)
  - **Estimated time:** 3 hours

### Phase 9: Monitoring & Data Quality (4 tasks)

- [ ] **T9.1:** Setup Prometheus metrics for new pipelines
  - Add metrics: ingestion_rows_total, ingestion_duration_seconds, ingestion_errors_total
  - Add metrics: dbt_run_duration_seconds, dbt_test_pass_rate
  - Add metrics: trino_query_duration_seconds
  - Export from FastAPI via existing /metrics endpoint
  - **Parallelizable:** No
  - **Estimated time:** 3 hours

- [ ] **T9.2:** Create Grafana dashboards
  - Pipeline health dashboard (DAG success/failure rates)
  - Data freshness dashboard (last ingestion per source)
  - Data quality dashboard (test pass rates, row counts)
  - Resource utilization (CPU, memory, disk per service)
  - **Parallelizable:** No (depends on T9.1)
  - **Estimated time:** 5 hours

- [ ] **T9.3:** Configure Great Expectations
  - Create expectation suites for Olist bronze tables
  - Create expectation suites for MSSQL bronze tables
  - Validate: not null, unique, accepted values, referential integrity
  - Generate data docs (HTML reports)
  - Integrate with Airflow data_quality_dag
  - **Parallelizable:** Yes (with T9.2)
  - **Estimated time:** 4 hours

- [ ] **T9.4:** Setup alerting
  - Email alerts for DAG failures
  - Slack webhook integration for critical issues
  - Data quality alert thresholds
  - Configure Airflow callbacks (already scaffolded in callbacks.py)
  - **Parallelizable:** Yes (with T9.3)
  - **Estimated time:** 3 hours

### Phase 10: Testing & Documentation (2 tasks)

- [ ] **T10.1:** Write tests
  - Unit tests: Kaggle client, validation module, MinIO loader
  - Integration tests: end-to-end ingestion pipeline
  - dbt tests: run `dbt test` for all Olist models
  - API tests: FastAPI endpoints (monitor, ingestion, dashboard)
  - **Parallelizable:** No
  - **Estimated time:** 8 hours

- [ ] **T10.2:** Create documentation
  - Architecture documentation (updated with Trino, dual sources)
  - Setup guide (docker-compose, .env, first run)
  - API documentation (auto-generated via FastAPI /docs)
  - Runbook for operations (restart services, re-run DAGs, troubleshoot)
  - **Parallelizable:** Yes (with T10.1)
  - **Estimated time:** 4 hours

### Phase 11: Final Verification Wave (4 tasks)

- [ ] **F1: Code Quality Review**
  - All code follows PEP 8 / ESLint rules
  - No linting errors
  - Proper error handling and logging
  - Type hints on all Python functions
  - **Reviewer:** Code Quality Agent
  - **Verdict:** APPROVE/REJECT

- [ ] **F2: Architecture Review**
  - MinIO + Trino integration correct
  - Dual data source ingestion working
  - dbt transformation pipeline complete
  - API proxy architecture sound
  - **Reviewer:** Architecture Agent
  - **Verdict:** APPROVE/REJECT

- [ ] **F3: Data Quality Review**
  - All Great Expectations tests pass
  - Data lineage documented (source → bronze → silver → gold → mart)
  - No data loss in pipeline
  - Referential integrity maintained in star schema
  - **Reviewer:** Data Quality Agent
  - **Verdict:** APPROVE/REJECT

- [ ] **F4: Production Readiness Review**
  - All services running on Dokploy
  - Monitoring dashboards functional
  - Alerts configured and tested
  - Documentation complete
  - Backup strategy in place
  - UI pages functional and responsive
  - **Reviewer:** Production Readiness Agent
  - **Verdict:** APPROVE/REJECT

---

## 📊 Task Summary

| Phase | Tasks | Hours | Key Deliverable |
|-------|-------|-------|-----------------|
| 1. Infrastructure | 5 | 10h | Trino + Hive Metastore + Airflow API |
| 2. Ingestion | 5 | 15h | Kaggle client + MSSQL → MinIO Parquet |
| 3. Bronze Layer | 4 | 11h | PostgreSQL bronze tables (Olist + MSSQL) |
| 4. dbt Transforms | 4 | 19h | Olist staging → intermediate → marts |
| 5. Data Marts | 4 | 15h | Sales, Customer, Logistics marts |
| 6. Airflow DAGs | 5 | 18h | 5 orchestration DAGs |
| 7. FastAPI Backend | 4 | 13h | Monitor, Ingestion, Dashboard APIs |
| 8. Next.js UI | 5 | 23h | 3 management pages + shared components |
| 9. Monitoring | 4 | 15h | Prometheus, Grafana, GE, alerts |
| 10. Testing & Docs | 2 | 12h | Tests + documentation |
| 11. Verification | 4 | — | 4 review gates |
| **TOTAL** | **46** | **~151h** | **Complete platform** |

---

## 📝 Key Changes from Plan v1

| Aspect | Plan v1 | Plan v2 |
|--------|---------|---------|
| Data Lake | HDFS (Hadoop cluster) | MinIO (already exists) |
| Query Engine | None (Spark only) | Trino + Hive Metastore |
| Data Sources | Kaggle only | Kaggle + MSSQL (dual) |
| Spark | Required (HDFS reader) | Optional (dbt handles transforms) |
| UI Pages | None mentioned | 3 management pages |
| API Layer | Basic endpoints | Airflow proxy + ingestion + dashboard APIs |
| Total Tasks | 42 | 46 (4 more for UI + API) |
| Complexity | HDFS ops heavy | Lighter infra, richer UI |
| Resource Need | 32GB RAM (HDFS+Spark) | 16GB RAM sufficient |

---

## 📝 Notes

- **MinIO replaces HDFS**: Same bronze/silver/gold concept, Parquet instead of raw CSV, S3 API instead of HDFS API. Already deployed and tested.
- **Trino for data lake SQL**: Enables ad-hoc queries directly on MinIO without loading to PostgreSQL first. Uses Hive Metastore for schema catalog.
- **Dual data sources**: Kaggle for e-commerce demo data, MSSQL for real production data. Both flow through MinIO → PostgreSQL → dbt.
- **UI connected via FastAPI proxy**: All frontend data fetched from FastAPI backend. Airflow API proxied (auth hidden), analytics queries cached in Redis.
- **Incremental approach**: Start with Olist 2 tables (orders + items), then scale to all 9. MSSQL tables loaded in parallel.
- **Existing code preserved**: All crypto/economic ingestion, dbt models, and Airflow DAGs remain untouched.
