# 🎯 Kaggle E-Commerce Data Engineering Platform - Implementation Plan

## 📋 Project Overview

**Mục tiêu:** Xây dựng hệ thống Data Engineering hoàn chỉnh sử dụng Brazilian E-Commerce Olist dataset từ Kaggle, với kiến trúc hiện đại bao gồm data ingestion, ELT pipeline, HDFS, Data Warehouse, Data Mart, orchestration và monitoring.

**Dataset chính:** Brazilian E-Commerce Public Dataset by Olist
- **9 CSV files** có quan hệ với nhau
- **100,000+ orders** từ 2016-2018
- **Relational structure** phù hợp cho dimensional modeling

**Tech Stack:**
- **Data Sources:** Kaggle datasets (Olist E-commerce)
- **Ingestion:** Python, Kaggle API
- **Storage:** PostgreSQL (transactional), ClickHouse (analytics), HDFS (raw data lake)
- **Processing:** Apache Spark, dbt (transformations)
- **Orchestration:** Apache Airflow
- **Deployment:** Dokploy (multi-database setup)
- **Monitoring:** Prometheus, Grafana, Great Expectations
- **Containerization:** Docker, Docker Compose

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 0: DATA SOURCES                         │
│                                                                   │
│  Kaggle API → Brazilian E-Commerce Olist Dataset (9 tables)     │
│  - olist_orders_dataset.csv                                      │
│  - olist_order_items_dataset.csv                                 │
│  - olist_order_payments_dataset.csv                              │
│  - olist_order_reviews_dataset.csv                               │
│  - olist_customers_dataset.csv                                   │
│  - olist_products_dataset.csv                                    │
│  - olist_sellers_dataset.csv                                     │
│  - olist_geolocation_dataset.csv                                 │
│  - product_category_name_translation.csv                         │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              LAYER 1: DATA INGESTION (Python + Airflow)          │
│                                                                   │
│  Kaggle API Client → Download CSVs → Validate → Checkpoint      │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│           LAYER 2: RAW DATA LAKE (HDFS - Bronze Layer)          │
│                                                                   │
│  HDFS Cluster (Docker) → Store raw CSVs → Partitioned by date   │
│  /bronze/olist/orders/YYYY-MM-DD/                                │
│  /bronze/olist/customers/YYYY-MM-DD/                             │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│         LAYER 3: ELT PROCESSING (Spark + dbt)                    │
│                                                                   │
│  Spark Jobs:                                                     │
│  - Read from HDFS → Clean → Validate → Write to Postgres        │
│                                                                   │
│  dbt Transformations:                                            │
│  - Staging (Silver): Clean, standardize                          │
│  - Intermediate: Join, aggregate                                 │
│  - Marts (Gold): Business logic, dimensional models              │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│        LAYER 4: DATA WAREHOUSE (PostgreSQL + ClickHouse)         │
│                                                                   │
│  PostgreSQL (OLTP):                                              │
│  - bronze_* tables (raw from HDFS)                               │
│  - silver_* tables (cleaned)                                     │
│                                                                   │
│  ClickHouse (OLAP):                                              │
│  - gold_* tables (analytics-ready)                               │
│  - Optimized for aggregations                                    │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              LAYER 5: DATA MARTS (Dimensional Models)            │
│                                                                   │
│  Star Schema Design:                                             │
│  - fct_orders (fact table)                                       │
│  - dim_customers, dim_products, dim_sellers, dim_time            │
│                                                                   │
│  Business-specific marts:                                        │
│  - sales_mart: Revenue, trends                                   │
│  - customer_mart: Segmentation, behavior                         │
│  - logistics_mart: Delivery performance                          │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│         LAYER 6: ORCHESTRATION & MONITORING                      │
│                                                                   │
│  Airflow DAGs:                                                   │
│  - kaggle_ingestion_dag: Download from Kaggle                    │
│  - hdfs_load_dag: Load to HDFS                                   │
│  - spark_elt_dag: Spark transformations                          │
│  - dbt_transformation_dag: dbt models                            │
│  - data_quality_dag: Great Expectations tests                    │
│                                                                   │
│  Monitoring:                                                     │
│  - Prometheus: Metrics collection                                │
│  - Grafana: Dashboards                                           │
│  - Great Expectations: Data quality                              │
│  - Airflow alerts: Email/Slack notifications                     │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              LAYER 7: SERVING & ANALYTICS                        │
│                                                                   │
│  FastAPI: REST API for data access                               │
│  Grafana: Business dashboards                                    │
│  Jupyter: Ad-hoc analysis                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Olist Dataset Structure

### Tables & Relationships

```
┌─────────────────┐
│  olist_orders   │ (100k orders)
│  - order_id (PK)│
│  - customer_id  │───┐
│  - order_status │   │
│  - timestamps   │   │
└─────────────────┘   │
         │            │
         │            ▼
         │     ┌──────────────────┐
         │     │ olist_customers  │
         │     │ - customer_id(PK)│
         │     │ - zip_code       │
         │     │ - city, state    │
         │     └──────────────────┘
         │
         ▼
┌──────────────────────┐
│ olist_order_items    │ (112k items)
│ - order_id (FK)      │
│ - order_item_id      │
│ - product_id (FK)────┼──────┐
│ - seller_id (FK)─────┼───┐  │
│ - price, freight     │   │  │
└──────────────────────┘   │  │
         │                 │  │
         │                 │  ▼
         │                 │ ┌─────────────────┐
         │                 │ │ olist_products  │
         │                 │ │ - product_id(PK)│
         │                 │ │ - category      │
         │                 │ │ - dimensions    │
         │                 │ └─────────────────┘
         │                 │
         │                 ▼
         │          ┌─────────────────┐
         │          │ olist_sellers   │
         │          │ - seller_id (PK)│
         │          │ - zip_code      │
         │          └─────────────────┘
         │
         ▼
┌──────────────────────┐
│ olist_order_payments │
│ - order_id (FK)      │
│ - payment_type       │
│ - installments       │
│ - value              │
└──────────────────────┘
         │
         ▼
┌──────────────────────┐
│ olist_order_reviews  │
│ - review_id (PK)     │
│ - order_id (FK)      │
│ - score (1-5)        │
│ - comment            │
└──────────────────────┘
```

---

## ✅ Implementation Tasks

### Phase 1: Infrastructure Setup (Week 1)

- [ ] **T1.1:** Setup Dokploy project và configure VPS
  - Create Dokploy project
  - Configure domain và SSL
  - Setup network và security groups
  - **Parallelizable:** No
  - **Estimated time:** 4 hours

- [ ] **T1.2:** Deploy PostgreSQL database via Dokploy
  - Use dokploy/databases/docker-compose.postgres.yml
  - Configure connection pooling
  - Setup backup strategy
  - **Parallelizable:** No (depends on T1.1)
  - **Estimated time:** 2 hours

- [ ] **T1.3:** Deploy ClickHouse database via Dokploy
  - Use dokploy/databases/docker-compose.clickhouse.yml
  - Configure for OLAP workloads
  - Setup retention policies
  - **Parallelizable:** Yes (with T1.2)
  - **Estimated time:** 2 hours

- [ ] **T1.4:** Deploy Redis cache via Dokploy
  - Use dokploy/databases/docker-compose.redis.yml
  - Configure persistence
  - Setup for caching và checkpointing
  - **Parallelizable:** Yes (with T1.2, T1.3)
  - **Estimated time:** 1 hour

- [ ] **T1.5:** Setup HDFS cluster with Docker
  - Create docker-compose.hdfs.yml
  - Configure namenode + 3 datanodes
  - Setup volumes và networking
  - Test HDFS operations
  - **Parallelizable:** No (needs base infrastructure)
  - **Estimated time:** 4 hours

### Phase 2: Data Ingestion Layer (Week 2)

- [ ] **T2.1:** Create Kaggle API integration
  - Install kaggle package
  - Configure API credentials
  - Create KaggleClient class
  - Implement download_dataset() method
  - **Parallelizable:** No
  - **Estimated time:** 3 hours

- [ ] **T2.2:** Build data validation module
  - Create schema validators for 9 CSV files
  - Implement data quality checks
  - Add error handling và logging
  - **Parallelizable:** Yes (with T2.1)
  - **Estimated time:** 4 hours

- [ ] **T2.3:** Create HDFS loader
  - Implement HDFSClient class
  - Create upload_to_hdfs() method
  - Add partitioning logic (by date)
  - Test with sample data
  - **Parallelizable:** No (depends on T1.5)
  - **Estimated time:** 3 hours

- [ ] **T2.4:** Build checkpoint manager
  - Track ingestion progress
  - Store in Redis
  - Implement resume logic
  - **Parallelizable:** Yes (with T2.3)
  - **Estimated time:** 2 hours

### Phase 3: ELT Pipeline - Spark Jobs (Week 3)

- [ ] **T3.1:** Setup Apache Spark in Docker
  - Create docker-compose.spark.yml
  - Configure master + 2 workers
  - Setup Spark UI
  - Test cluster connectivity
  - **Parallelizable:** No
  - **Estimated time:** 3 hours

- [ ] **T3.2:** Create Spark job: HDFS → Bronze (Postgres)
  - Read CSVs from HDFS
  - Minimal transformations (type casting)
  - Write to bronze_* tables in Postgres
  - Handle incremental loads
  - **Parallelizable:** No (depends on T3.1)
  - **Estimated time:** 5 hours

- [ ] **T3.3:** Create Spark job: Data quality checks
  - Implement Great Expectations integration
  - Check nulls, duplicates, referential integrity
  - Log results to monitoring
  - **Parallelizable:** Yes (with T3.2)
  - **Estimated time:** 4 hours

- [ ] **T3.4:** Optimize Spark jobs
  - Add partitioning strategies
  - Configure memory settings
  - Implement caching
  - **Parallelizable:** No (depends on T3.2)
  - **Estimated time:** 3 hours

### Phase 4: dbt Transformations (Week 4)

- [ ] **T4.1:** Setup dbt project structure
  - Configure profiles.yml for Postgres + ClickHouse
  - Create staging/intermediate/marts folders
  - Setup sources.yml
  - **Parallelizable:** No
  - **Estimated time:** 2 hours

- [ ] **T4.2:** Create staging models (Silver layer)
  - stg_olist_orders.sql
  - stg_olist_order_items.sql
  - stg_olist_customers.sql
  - stg_olist_products.sql
  - stg_olist_sellers.sql
  - stg_olist_payments.sql
  - stg_olist_reviews.sql
  - **Parallelizable:** No (depends on T4.1)
  - **Estimated time:** 6 hours

- [ ] **T4.3:** Create intermediate models
  - int_orders_enriched.sql (join orders + items + payments)
  - int_customer_metrics.sql (aggregate customer stats)
  - int_product_performance.sql (product analytics)
  - int_seller_performance.sql (seller metrics)
  - **Parallelizable:** No (depends on T4.2)
  - **Estimated time:** 5 hours

- [ ] **T4.4:** Create dimensional models (Gold layer)
  - dim_customers.sql
  - dim_products.sql
  - dim_sellers.sql
  - dim_time.sql
  - fct_orders.sql (fact table)
  - **Parallelizable:** No (depends on T4.3)
  - **Estimated time:** 6 hours

### Phase 5: Data Marts (Week 5)

- [ ] **T5.1:** Design sales_mart
  - Daily/weekly/monthly revenue aggregations
  - Product category performance
  - Payment method analysis
  - Write to ClickHouse for fast queries
  - **Parallelizable:** No (depends on T4.4)
  - **Estimated time:** 4 hours

- [ ] **T5.2:** Design customer_mart
  - Customer segmentation (RFM analysis)
  - Lifetime value calculations
  - Geographic distribution
  - Churn prediction features
  - **Parallelizable:** Yes (with T5.1)
  - **Estimated time:** 4 hours

- [ ] **T5.3:** Design logistics_mart
  - Delivery time analysis
  - Freight cost optimization
  - Seller performance by region
  - Late delivery predictions
  - **Parallelizable:** Yes (with T5.1, T5.2)
  - **Estimated time:** 4 hours

- [ ] **T5.4:** Create mart refresh strategy
  - Incremental vs full refresh logic
  - Schedule optimization
  - Dependency management
  - **Parallelizable:** No (depends on T5.1-T5.3)
  - **Estimated time:** 3 hours

### Phase 6: Orchestration with Airflow (Week 6)

- [ ] **T6.1:** Setup Airflow in Docker
  - Use existing docker-compose.yml
  - Configure executor (LocalExecutor or CeleryExecutor)
  - Setup connections to all databases
  - **Parallelizable:** No
  - **Estimated time:** 3 hours

- [ ] **T6.2:** Create kaggle_ingestion_dag
  - Task 1: Download from Kaggle API
  - Task 2: Validate CSVs
  - Task 3: Upload to HDFS
  - Task 4: Update checkpoint
  - Schedule: Daily at 2 AM
  - **Parallelizable:** No (depends on T6.1)
  - **Estimated time:** 4 hours

- [ ] **T6.3:** Create spark_elt_dag
  - Task 1: Read from HDFS
  - Task 2: Transform with Spark
  - Task 3: Load to bronze tables
  - Task 4: Data quality checks
  - Schedule: Daily at 3 AM (after ingestion)
  - **Parallelizable:** Yes (with T6.2)
  - **Estimated time:** 4 hours

- [ ] **T6.4:** Create dbt_transformation_dag
  - Task 1: dbt run (staging)
  - Task 2: dbt run (intermediate)
  - Task 3: dbt run (marts)
  - Task 4: dbt test
  - Schedule: Daily at 4 AM (after ELT)
  - **Parallelizable:** Yes (with T6.3)
  - **Estimated time:** 3 hours

- [ ] **T6.5:** Create data_quality_dag
  - Task 1: Run Great Expectations suites
  - Task 2: Check data freshness
  - Task 3: Validate mart metrics
  - Task 4: Send alerts if failures
  - Schedule: Daily at 5 AM (after transformations)
  - **Parallelizable:** Yes (with T6.4)
  - **Estimated time:** 4 hours

### Phase 7: Monitoring & Alerting (Week 7)

- [ ] **T7.1:** Setup Prometheus
  - Configure scraping for all services
  - Add custom metrics for pipelines
  - Setup retention policies
  - **Parallelizable:** No
  - **Estimated time:** 3 hours

- [ ] **T7.2:** Create Grafana dashboards
  - Pipeline health dashboard
  - Data quality metrics
  - Resource utilization (CPU, memory, disk)
  - Business metrics (orders, revenue)
  - **Parallelizable:** No (depends on T7.1)
  - **Estimated time:** 5 hours

- [ ] **T7.3:** Configure Great Expectations
  - Create expectation suites for each table
  - Setup data docs generation
  - Integrate with Airflow
  - **Parallelizable:** Yes (with T7.2)
  - **Estimated time:** 4 hours

- [ ] **T7.4:** Setup alerting
  - Email alerts for DAG failures
  - Slack integration for critical issues
  - PagerDuty for production incidents
  - **Parallelizable:** Yes (with T7.3)
  - **Estimated time:** 3 hours

### Phase 8: API & Serving Layer (Week 8)

- [ ] **T8.1:** Create FastAPI application
  - Setup project structure
  - Configure database connections
  - Add authentication middleware
  - **Parallelizable:** No
  - **Estimated time:** 3 hours

- [ ] **T8.2:** Build API endpoints
  - GET /api/v1/orders
  - GET /api/v1/customers/{id}
  - GET /api/v1/products/top-selling
  - GET /api/v1/analytics/revenue-trends
  - GET /api/v1/analytics/customer-segments
  - **Parallelizable:** No (depends on T8.1)
  - **Estimated time:** 6 hours

- [ ] **T8.3:** Add caching layer
  - Redis caching for frequent queries
  - Cache invalidation strategy
  - TTL configuration
  - **Parallelizable:** Yes (with T8.2)
  - **Estimated time:** 2 hours

- [ ] **T8.4:** Deploy API to Dokploy
  - Create Dockerfile
  - Configure docker-compose.yml
  - Setup reverse proxy
  - Add SSL certificate
  - **Parallelizable:** No (depends on T8.2)
  - **Estimated time:** 3 hours

### Phase 9: Testing & Documentation (Week 9)

- [ ] **T9.1:** Write unit tests
  - Test ingestion clients
  - Test Spark transformations
  - Test dbt models
  - Test API endpoints
  - **Parallelizable:** No
  - **Estimated time:** 8 hours

- [ ] **T9.2:** Write integration tests
  - End-to-end pipeline tests
  - Database integration tests
  - API integration tests
  - **Parallelizable:** Yes (with T9.1)
  - **Estimated time:** 6 hours

- [ ] **T9.3:** Create documentation
  - Architecture documentation
  - Setup guide
  - API documentation (OpenAPI/Swagger)
  - Runbook for operations
  - **Parallelizable:** Yes (with T9.2)
  - **Estimated time:** 6 hours

- [ ] **T9.4:** Performance testing
  - Load testing for API
  - Benchmark Spark jobs
  - Query performance tuning
  - **Parallelizable:** No (depends on T9.1, T9.2)
  - **Estimated time:** 4 hours

### Phase 10: Final Verification Wave

- [ ] **F1: Code Quality Review**
  - All code follows PEP 8
  - No linting errors
  - Proper error handling
  - Comprehensive logging
  - **Reviewer:** Code Quality Agent
  - **Verdict:** APPROVE/REJECT

- [ ] **F2: Architecture Review**
  - Follows best practices
  - Scalable design
  - Proper separation of concerns
  - Security considerations
  - **Reviewer:** Architecture Agent
  - **Verdict:** APPROVE/REJECT

- [ ] **F3: Data Quality Review**
  - All Great Expectations tests pass
  - Data lineage documented
  - No data loss in pipeline
  - Referential integrity maintained
  - **Reviewer:** Data Quality Agent
  - **Verdict:** APPROVE/REJECT

- [ ] **F4: Production Readiness Review**
  - All services running on Dokploy
  - Monitoring dashboards functional
  - Alerts configured
  - Documentation complete
  - Backup strategy in place
  - **Reviewer:** Production Readiness Agent
  - **Verdict:** APPROVE/REJECT

---

## 📁 Project Structure

```
kaggle-ecommerce-platform/
├── src/
│   ├── ingestion/
│   │   ├── kaggle_client.py          # Kaggle API integration
│   │   ├── hdfs_loader.py            # HDFS upload logic
│   │   ├── validators.py             # Data validation
│   │   └── config.py                 # Configuration
│   ├── processing/
│   │   ├── spark_jobs/
│   │   │   ├── bronze_loader.py      # HDFS → Postgres
│   │   │   ├── data_quality.py       # Quality checks
│   │   │   └── utils.py              # Spark utilities
│   │   └── dbt_project/
│   │       ├── models/
│   │       │   ├── staging/          # Silver layer
│   │       │   ├── intermediate/     # Transformations
│   │       │   └── marts/            # Gold layer
│   │       ├── dbt_project.yml
│   │       └── profiles.yml
│   ├── orchestration/
│   │   └── dags/
│   │       ├── kaggle_ingestion_dag.py
│   │       ├── spark_elt_dag.py
│   │       ├── dbt_transformation_dag.py
│   │       └── data_quality_dag.py
│   ├── api/
│   │   ├── main.py                   # FastAPI app
│   │   ├── routers/
│   │   │   ├── orders.py
│   │   │   ├── customers.py
│   │   │   ├── products.py
│   │   │   └── analytics.py
│   │   └── config.py
│   └── utils/
│       ├── logger.py
│       ├── metrics.py
│       └── checkpoint_manager.py
├── sql/
│   ├── postgres/
│   │   ├── 01_bronze_schema.sql
│   │   ├── 02_silver_schema.sql
│   │   └── 03_gold_schema.sql
│   └── clickhouse/
│       └── marts_schema.sql
├── docker/
│   ├── docker-compose.hdfs.yml       # HDFS cluster
│   ├── docker-compose.spark.yml      # Spark cluster
│   └── docker-compose.yml            # All services
├── dokploy/
│   ├── databases/
│   │   ├── docker-compose.postgres.yml
│   │   ├── docker-compose.clickhouse.yml
│   │   └── docker-compose.redis.yml
│   └── application/
│       └── docker-compose.yml
├── monitoring/
│   ├── prometheus/
│   │   └── prometheus.yml
│   ├── grafana/
│   │   └── dashboards/
│   └── great_expectations/
│       └── expectations/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── SETUP.md
│   ├── API_DOCS.md
│   └── RUNBOOK.md
├── scripts/
│   ├── setup.sh
│   ├── deploy.sh
│   └── backup.sh
├── .env.example
├── requirements.txt
└── README.md
```

---

## 🎯 Success Metrics

### Technical Metrics
- ✅ Pipeline runs successfully end-to-end
- ✅ Data latency < 1 hour (from Kaggle to marts)
- ✅ Zero data loss in pipeline
- ✅ 99.9% uptime for all services
- ✅ All Great Expectations tests pass
- ✅ API response time < 200ms (p95)

### Business Metrics
- ✅ 9 tables successfully ingested from Kaggle
- ✅ 100k+ orders processed
- ✅ 3 data marts operational (sales, customer, logistics)
- ✅ 10+ business dashboards in Grafana
- ✅ 20+ API endpoints functional

### Learning Outcomes
- ✅ Hands-on experience with HDFS
- ✅ Spark for large-scale data processing
- ✅ dbt for data transformations
- ✅ Airflow for orchestration
- ✅ Dimensional modeling (star schema)
- ✅ Data quality with Great Expectations
- ✅ Production deployment with Dokploy

---

## 📝 Notes

- **Incremental approach:** Start with 1-2 tables, then scale to all 9
- **Cost optimization:** Use Docker locally first, then deploy to Dokploy
- **Data refresh:** Daily batch loads (can add real-time later)
- **Scalability:** Architecture supports adding more datasets
- **Monitoring:** Critical for production reliability

---

**Total estimated time:** 9 weeks (90-120 hours)
**Difficulty:** Intermediate to Advanced
**Portfolio value:** ⭐⭐⭐⭐⭐ (Demonstrates full data engineering stack)
