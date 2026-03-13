# Architectural Decisions - Kaggle E-Commerce Data Engineering Platform

## [2026-03-13] Core Architecture Decisions

### Decision 1: Dataset Selection
**Choice:** Brazilian E-Commerce Olist dataset from Kaggle
**Rationale:**
- 9 relational tables with clear relationships
- Real-world e-commerce data (100k+ orders)
- Rich for dimensional modeling (customers, products, sellers, orders)
- Suitable for demonstrating full data engineering pipeline
- Public dataset with good documentation

### Decision 2: HDFS Integration Strategy
**Choice:** Add Hadoop HDFS cluster via Docker alongside existing databases
**Rationale:**
- User specifically requested HDFS for raw data lake
- Separates raw storage (HDFS) from processed storage (Postgres/ClickHouse)
- Demonstrates big data ecosystem knowledge
- Docker-based setup for easy deployment
**Implementation:** Use bitnami/hadoop or apache/hadoop Docker images

### Decision 3: Database Layer Architecture
**Choice:** Three-tier database strategy
- **HDFS:** Raw data lake (Bronze layer)
- **PostgreSQL:** Staging and intermediate tables (Silver layer)
- **ClickHouse:** Analytics and data marts (Gold layer)
**Rationale:**
- HDFS for scalable raw storage
- PostgreSQL for transactional integrity during transformations
- ClickHouse for high-performance analytics queries
- Matches user's requirement for "multiple databases"

### Decision 4: ELT vs ETL
**Choice:** ELT (Extract-Load-Transform) approach
**Rationale:**
- Load raw data to HDFS first (preserve original)
- Transform using Spark + dbt after loading
- Leverages modern data warehouse capabilities
- Easier to reprocess if transformation logic changes

### Decision 5: Orchestration Tool
**Choice:** Apache Airflow (already in codebase)
**Rationale:**
- Already configured in existing platform
- Industry standard for data pipeline orchestration
- Rich operator ecosystem (KaggleOperator, SparkOperator, etc.)
- Good monitoring and alerting capabilities

### Decision 6: Data Quality Framework
**Choice:** Great Expectations + dbt tests
**Rationale:**
- Great Expectations for data validation at ingestion
- dbt tests for transformation quality checks
- User specifically mentioned monitoring/alerting
- Integrates well with Airflow

### Decision 7: Dimensional Modeling Approach
**Choice:** Star schema with fact and dimension tables
**Rationale:**
- Olist dataset naturally fits star schema
- Fact table: orders/order_items (transactions)
- Dimensions: customers, products, sellers, time, geography
- Optimized for analytical queries
- Standard approach for data marts

### Decision 8: Deployment Strategy
**Choice:** Dokploy for production deployment
**Rationale:**
- User specifically requested Dokploy
- Self-hosted PaaS (cost-effective)
- Supports multi-container deployments
- Existing docker-compose configurations can be reused

### Decision 9: Processing Engine
**Choice:** Apache Spark for HDFS → Database ELT
**Rationale:**
- Standard tool for reading from HDFS
- Handles large-scale data processing
- Good integration with Airflow (SparkSubmitOperator)
- Can write to both PostgreSQL and ClickHouse

### Decision 10: Monitoring Stack
**Choice:** Prometheus + Grafana + Airflow alerts
**Rationale:**
- Already configured in existing platform
- Prometheus for metrics collection
- Grafana for visualization
- Airflow for pipeline-specific alerts
- Covers infrastructure and data pipeline monitoring
