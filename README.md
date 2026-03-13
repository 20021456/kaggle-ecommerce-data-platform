# 🚀 Kaggle E-Commerce Data Engineering Platform

A complete end-to-end data engineering platform demonstrating modern data stack with Brazilian E-Commerce dataset from Kaggle.

## 🎯 Project Overview

This project showcases a production-grade data engineering pipeline that:
- Ingests data from Kaggle (Brazilian E-Commerce Olist dataset - 9 relational tables)
- Stores raw data in HDFS (Hadoop Distributed File System)
- Processes data using Apache Spark and dbt
- Implements medallion architecture (Bronze → Silver → Gold)
- Deploys to production using Dokploy
- Monitors with Prometheus and Grafana

## 🏗️ Architecture

```
Kaggle API → Python Ingestion → HDFS (Bronze)
                                   ↓
                          Spark ELT Processing
                                   ↓
                    PostgreSQL (Silver) + ClickHouse (Gold)
                                   ↓
                          dbt Transformations
                                   ↓
                    Data Marts (Star Schema)
                                   ↓
                    FastAPI + Grafana Dashboards
```

**Orchestration:** Apache Airflow  
**Monitoring:** Prometheus + Grafana + Great Expectations  
**Deployment:** Dokploy (Docker-based PaaS)

## 📊 Dataset

**Brazilian E-Commerce Public Dataset by Olist**
- 100,000+ orders from 2016-2018
- 9 relational CSV files
- Real-world e-commerce data

**Tables:**
1. Orders
2. Order Items
3. Payments
4. Reviews
5. Customers
6. Products
7. Sellers
8. Geolocation
9. Category Translation

## 🛠️ Tech Stack

**Data Ingestion:**
- Python 3.11+
- Kaggle API
- Great Expectations (data quality)

**Storage:**
- HDFS (Hadoop 3.3.x) - Raw data lake
- PostgreSQL 16 - Transactional data
- ClickHouse 24.1 - Analytics
- Redis 7 - Caching

**Processing:**
- Apache Spark 3.5.x - ELT jobs
- dbt 1.7+ - SQL transformations
- PySpark - Python API

**Orchestration:**
- Apache Airflow 2.8+
- Celery executor

**Monitoring:**
- Prometheus
- Grafana
- Airflow alerts

**Deployment:**
- Docker & Docker Compose
- Dokploy (self-hosted PaaS)

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git
- Kaggle API credentials
- 16GB RAM minimum (32GB recommended)

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/kaggle-ecommerce-data-engineering.git
cd kaggle-ecommerce-data-engineering

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup Kaggle credentials
mkdir -p ~/.kaggle
cp kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json

# Copy environment file
cp .env.example .env
# Edit .env with your configurations

# Start infrastructure
docker-compose up -d

# Initialize databases
python scripts/init_databases.py

# Run Airflow setup
airflow db init
airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com

# Start Airflow
airflow webserver -p 8080 &
airflow scheduler &
```

### Access Services

```
Airflow UI: http://localhost:8080 (admin/admin)
Grafana: http://localhost:3000 (admin/admin)
API: http://localhost:8000
HDFS NameNode: http://localhost:9870
Spark Master: http://localhost:8081
```

## 📂 Project Structure

```
.
├── economic-data-platform/
│   ├── src/
│   │   ├── ingestion/
│   │   │   ├── ecommerce/          # Kaggle ingestion clients
│   │   │   ├── crypto/
│   │   │   └── economic/
│   │   ├── processing/
│   │   │   ├── spark_jobs/         # Spark ELT jobs
│   │   │   └── dbt_project/        # dbt transformations
│   │   ├── orchestration/
│   │   │   └── dags/               # Airflow DAGs
│   │   ├── api/                    # FastAPI application
│   │   └── utils/
│   ├── sql/                        # Database schemas
│   ├── tests/                      # Unit & integration tests
│   ├── monitoring/                 # Prometheus/Grafana configs
│   ├── dokploy/                    # Deployment configs
│   └── docker-compose.yml
├── .sisyphus/                      # Orchestration metadata
│   ├── plans/
│   └── notepads/
└── README.md
```

## 🔄 Data Pipeline

### 1. Ingestion (Airflow DAG: `kaggle_ingestion_dag`)
- Download datasets from Kaggle API
- Validate data quality with Great Expectations
- Store raw CSVs in HDFS `/bronze/olist/`

### 2. ELT Processing (Airflow DAG: `spark_elt_dag`)
- Read from HDFS using Spark
- Clean and validate data
- Write to PostgreSQL `bronze_*` tables

### 3. dbt Transformations (Airflow DAG: `dbt_transformation_dag`)
- **Staging (Silver):** Clean, standardize, deduplicate
- **Intermediate:** Join tables, calculate metrics
- **Marts (Gold):** Dimensional models (star schema)

### 4. Data Marts
- `fct_orders` - Fact table (order transactions)
- `dim_customers` - Customer dimension
- `dim_products` - Product dimension
- `dim_sellers` - Seller dimension
- `dim_time` - Time dimension
- `dim_geography` - Geographic dimension

### 5. Analytics Layer
- ClickHouse for fast aggregations
- FastAPI for data access
- Grafana dashboards for visualization

## 📊 Data Models

### Star Schema (Data Mart)

```sql
-- Fact Table
fct_orders (
  order_id PK,
  customer_key FK,
  product_key FK,
  seller_key FK,
  time_key FK,
  geography_key FK,
  order_value,
  freight_value,
  payment_value,
  review_score
)

-- Dimension Tables
dim_customers (customer_key PK, customer_id, city, state, ...)
dim_products (product_key PK, product_id, category, ...)
dim_sellers (seller_key PK, seller_id, city, state, ...)
dim_time (time_key PK, date, year, month, quarter, ...)
dim_geography (geography_key PK, zip_code, city, state, ...)
```

## 🔍 Monitoring & Alerting

### Data Quality
- Great Expectations validation suites
- dbt tests (schema, data, relationships)
- Custom data quality metrics

### Pipeline Monitoring
- Airflow DAG success/failure alerts
- Spark job metrics
- Database performance metrics

### Infrastructure Monitoring
- Prometheus metrics collection
- Grafana dashboards
- HDFS health checks
- Database connection pools

## 🚢 Deployment

### Local Development
```bash
docker-compose up -d
```

### Dokploy Production
```bash
# Push to GitHub
git push origin main

# Deploy via Dokploy UI
# Or use CLI
dokploy deploy --project kaggle-ecommerce
```

## 📚 Documentation

- [Architecture Details](.sisyphus/plans/kaggle-ecommerce-data-engineering.md)
- [Deployment Guide](.sisyphus/notepads/kaggle-ecommerce-data-engineering/deployment.md)
- [Architectural Decisions](.sisyphus/notepads/kaggle-ecommerce-data-engineering/decisions.md)
- [Known Issues](.sisyphus/notepads/kaggle-ecommerce-data-engineering/issues.md)

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test suite
pytest tests/unit/test_ingestion.py
pytest tests/integration/test_pipeline.py
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- [Kaggle](https://www.kaggle.com/) - Dataset platform
- [Olist](https://olist.com/) - Brazilian E-Commerce dataset
- [Apache Airflow](https://airflow.apache.org/) - Workflow orchestration
- [dbt](https://www.getdbt.com/) - Data transformations
- [Dokploy](https://dokploy.com/) - Deployment platform

## 📞 Contact

- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com
- LinkedIn: [Your Name](https://linkedin.com/in/yourprofile)

---

**Built with ❤️ for Data Engineering**
