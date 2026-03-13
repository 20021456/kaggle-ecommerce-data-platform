# Learnings - Kaggle E-Commerce Data Engineering Platform

## [2026-03-13] Initial Research Phase

### Dataset Information: Brazilian E-Commerce Olist
- **Source:** Kaggle (olistbr/brazilian-ecommerce)
- **Size:** 100,000+ orders (2016-2018)
- **Structure:** 9 relational CSV files
- **Domain:** E-commerce transactions in Brazil

### Key Tables Identified:
1. `olist_orders_dataset.csv` - Main orders table
2. `olist_order_items_dataset.csv` - Order line items
3. `olist_order_payments_dataset.csv` - Payment transactions
4. `olist_order_reviews_dataset.csv` - Customer reviews
5. `olist_customers_dataset.csv` - Customer information
6. `olist_products_dataset.csv` - Product catalog
7. `olist_sellers_dataset.csv` - Seller information
8. `olist_geolocation_dataset.csv` - Geographic data
9. `product_category_name_translation.csv` - Category translations

### Existing Codebase Analysis:
- **Platform:** economic-data-platform (crypto + economic data)
- **Databases:** PostgreSQL, ClickHouse, Redis
- **Orchestration:** Airflow DAGs already configured
- **Transformations:** dbt project with staging/intermediate/marts layers
- **Deployment:** Dokploy setup with docker-compose
- **Monitoring:** Prometheus + Grafana configured

### Technology Stack Decisions:
- **HDFS:** Need to add Hadoop cluster (currently missing)
- **Spark:** For ELT from HDFS to databases
- **dbt:** Reuse existing dbt structure for transformations
- **Airflow:** Extend existing DAGs for Kaggle ingestion
- **Great Expectations:** Add for data quality checks

### Architecture Patterns Found:
- Medallion architecture: Bronze (raw) → Silver (cleaned) → Gold (analytics)
- Separation of OLTP (PostgreSQL) and OLAP (ClickHouse)
- Docker-based microservices
- Environment-based configuration (.env files)

### Dokploy Insights:
- Open-source PaaS alternative to Heroku/Vercel
- Supports multi-database deployment
- Traefik integration for routing
- Automatic SSL with Let's Encrypt
- Docker Compose native
