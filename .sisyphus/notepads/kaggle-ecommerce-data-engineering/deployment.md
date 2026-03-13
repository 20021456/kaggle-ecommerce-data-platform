# Deployment Configuration

## Application

- *Name*: Kaggle E-Commerce Data Engineering Platform
- *Type*: Data Pipeline (Python + Airflow + Spark + dbt)
- *Repo*: kaggle-ecommerce-data-platform
- *Dataset*: Brazilian E-Commerce Olist (9 CSV tables, 100k+ orders)

## Dokploy

- *Project*: E-Commerce System
- *Application ID*: [To be assigned after creation]
- *Branch*: main
- *Port*: 8000 (FastAPI), 8080 (Airflow), 3000 (Grafana)
- *Server IP*: 49.12.105.103
- *Dashboard*: https://dokploy.evanguyen3110.space/dashboard/projects

## Domain

- *Production URL*: data.evanguyen3110.space
- *Airflow UI*: airflow.evanguyen3110.space
- *Grafana*: grafana.evanguyen3110.space
- *API*: api.evanguyen3110.space
- *MinIO Console*: minio.evanguyen3110.space
- *Prometheus*: prometheus.evanguyen3110.space
- *DNS Target*: 49.12.105.103 (A record)
- *Proxied*: false (Traefik handles SSL)

## Local Development

- *Airflow UI*: http://localhost:8080 (admin/admin)
- *Grafana*: http://localhost:3000 (admin/admin)
- *API*: http://localhost:8000
- *MinIO Console*: http://localhost:9001
- *Prometheus*: http://localhost:9090
- *HDFS NameNode*: http://localhost:9870
- *HDFS DataNode*: http://localhost:9864
- *Spark Master*: http://localhost:8081
- *Spark Worker*: http://localhost:8082

## PostgreSQL (OLTP)

- *Host*: localhost (dev) / postgres (docker) / 49.12.105.103 (prod)
- *Port*: 5432
- *Database*: economic_data
- *Username*: economic_user
- *Password*: from DATABASE_URL env var (see .credentials/CREDENTIALS.md)
- *Connection String*: postgresql://economic_user:password@49.12.105.103:5432/economic_data
- *Schemas*: bronze (raw), silver (cleaned), gold (analytics)

## ClickHouse (OLAP)

- *Host*: localhost (dev) / clickhouse (docker) / [production-ip] (prod)
- *HTTP Port*: 8123
- *Native Port*: 9000
- *Database*: economic_data
- *Username*: default
- *Password*: from CLICKHOUSE_PASSWORD env var
- *HTTP URL*: http://localhost:8123
- *Use Case*: Analytics queries, data marts, aggregations

## Redis (Cache)

- *Host*: localhost (dev) / redis (docker) / [production-ip] (prod)
- *Port*: 6379
- *Password*: from REDIS_PASSWORD env var
- *Connection String*: redis://:[password]@localhost:6379/0
- *Key Namespaces*: cache:*, queue:*, checkpoint:*, metrics:*

## HDFS (Data Lake)

- *NameNode Host*: localhost (dev) / hdfs-namenode (docker)
- *NameNode Port*: 9000
- *NameNode HTTP*: 9870
- *DataNode Port*: 9864
- *WebHDFS Port*: 9870
- *Connection URI*: hdfs://localhost:9000
- *Data Paths*: /bronze/olist/{orders,customers,products,sellers,order_items,payments,reviews,geolocation,category_translation}

## Kafka (Streaming)

- *Host*: localhost (dev) / kafka (docker)
- *Port*: 9092
- *Zookeeper*: localhost:2181
- *Topics*: raw_data, processed_data, alerts

## Spark (Processing)

- *Master URL*: spark://localhost:7077
- *Master UI*: http://localhost:8081
- *Worker UI*: http://localhost:8082
- *Executor Memory*: 2g
- *Driver Memory*: 1g

## Monitoring

- *Prometheus*: http://localhost:9090 (metrics collection)
- *Grafana*: http://localhost:3000 (visualization)
- *Airflow Alerts*: Email/Slack notifications on DAG failures
- *Great Expectations*: Data quality validation reports

## Environment Variables

- *DATABASE_URL* — PostgreSQL connection string
- *CLICKHOUSE_URL* — ClickHouse HTTP endpoint
- *CLICKHOUSE_PASSWORD* — ClickHouse authentication
- *REDIS_PASSWORD* — Redis authentication
- *KAGGLE_USERNAME* — Kaggle API username
- *KAGGLE_KEY* — Kaggle API key (from ~/.kaggle/kaggle.json)
- *AIRFLOW_FERNET_KEY* — Airflow encryption key
- *AIRFLOW__CORE__SQL_ALCHEMY_CONN* — Airflow metadata DB
- *AWS_ACCESS_KEY_ID* — MinIO/S3 access key
- *AWS_SECRET_ACCESS_KEY* — MinIO/S3 secret key
- *HDFS_NAMENODE_URL* — HDFS connection URI
- *SPARK_MASTER_URL* — Spark cluster master URL

## GitHub

- *Repository*: https://github.com/20021456/kaggle-ecommerce-data-platform
- *Clone URL (HTTPS)*: https://github.com/20021456/kaggle-ecommerce-data-platform.git
- *Clone URL (SSH)*: git@github.com:20021456/kaggle-ecommerce-data-platform.git
- *Branch Strategy*: main (production), develop (development), feature/* (features)
- *CI/CD*: GitHub Actions (test, build, deploy)
- *Username*: 20021456
- *Email*: nguyenevan3110@gmail.com

## Kaggle

- *Dataset*: Brazilian E-Commerce Public Dataset by Olist
- *Dataset URL*: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
- *API Docs*: https://www.kaggle.com/docs/api
- *Credentials*: ~/.kaggle/kaggle.json (chmod 600)
- *Download Command*: kaggle datasets download -d olistbr/brazilian-ecommerce

## File Paths

- *Project Root*: D:\Cursor\Python\Database system
- *Application*: economic-data-platform/
- *Ingestion*: src/ingestion/ecommerce/
- *Spark Jobs*: src/processing/spark_jobs/
- *dbt Project*: src/processing/dbt_project/
- *Airflow DAGs*: src/orchestration/dags/
- *SQL Schemas*: sql/postgres/, sql/clickhouse/
- *Docker Compose*: docker-compose.yml, docker-compose.dokploy.yml
- *Plans*: .sisyphus/plans/kaggle-ecommerce-data-engineering.md
- *Notepads*: .sisyphus/notepads/kaggle-ecommerce-data-engineering/

## Docker Volumes

- *postgres_data* — PostgreSQL data persistence
- *clickhouse_data* — ClickHouse data persistence
- *redis_data* — Redis data persistence
- *hdfs_namenode* — HDFS NameNode metadata
- *hdfs_datanode1* — HDFS DataNode 1 data
- *hdfs_datanode2* — HDFS DataNode 2 data
- *minio_data* — MinIO/S3 object storage
- *airflow_logs* — Airflow task logs
- *prometheus_data* — Prometheus metrics storage
- *grafana_data* — Grafana dashboards and settings

## MCP Servers

- *Playwright* — Browser automation (Kaggle scraping)
- *Context7* — Documentation lookup (library APIs)
- *WebSearch (Exa)* — Web search for research
- *GitHub CLI* — Repository operations

## Notes

- Platform has two deployment modes: local development (Docker Compose) and production (Dokploy)
- HDFS cluster runs 1 NameNode + 2 DataNodes for redundancy
- Data flow: Kaggle API → HDFS (Bronze) → Spark ELT → PostgreSQL (Silver) → dbt → ClickHouse (Gold)
- Airflow orchestrates entire pipeline with 3 main DAGs: kaggle_ingestion, spark_elt, dbt_transformation
- Great Expectations validates data quality at ingestion and transformation stages
- Monitoring stack (Prometheus + Grafana) tracks infrastructure and pipeline metrics
- MinIO provides S3-compatible object storage for backups and intermediate data
- dbt implements medallion architecture: staging (silver) → intermediate → marts (gold)
- Star schema in data marts: fct_orders (fact) + dim_customers, dim_products, dim_sellers, dim_time, dim_geography (dimensions)
- System requirements: 16GB RAM minimum, 32GB recommended for full stack
