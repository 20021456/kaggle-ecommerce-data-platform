# 🚀 Economic Data Engineering Platform

A complete end-to-end data engineering platform demonstrating modern data stack with data sourced from Microsoft SQL Server.

## 🎯 Project Overview

This project showcases a production-grade data engineering pipeline that:
- Ingests data from Microsoft SQL Server (external MSSQL database - xomdata_dataset)
- Stores raw data in PostgreSQL (Bronze layer)
- Processes data using Apache Spark and dbt
- Implements medallion architecture (Bronze → Silver → Gold)
- Deploys to production using Dokploy
- Monitors with Prometheus and Grafana

## 🏗️ Architecture

```
MSSQL Server → Python Ingestion → PostgreSQL (Bronze)
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

## 📊 Data Source

**Microsoft SQL Server (External)**
- Host: `45.124.94.158`
- Port: `1433`
- Database: `xomdata_dataset`
- Multiple relational tables

## 🛠️ Tech Stack

**Data Ingestion:**
- Python 3.11+
- pymssql (MSSQL connector)
- Great Expectations (data quality)

**Storage:**
- PostgreSQL 16 - Transactional data (Bronze/Silver)
- ClickHouse 24.1 - Analytics (Gold)
- Redis 7 - Caching
- MinIO - Object storage

**Processing:**
- Apache Spark 3.5.x - ELT jobs
- dbt 1.7+ - SQL transformations
- PySpark - Python API

**Orchestration:**
- Apache Airflow 2.8+
- LocalExecutor

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
- MSSQL Server credentials
- 16GB RAM minimum (32GB recommended)

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/economic-data-platform.git
cd economic-data-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your MSSQL credentials and other configurations

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
Spark Master: http://localhost:8081
```

## 📂 Project Structure

```
.
├── economic-data-platform/
│   ├── src/
│   │   ├── ingestion/
│   │   │   ├── mssql_client.py     # MSSQL data ingestion client
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

### 1. Ingestion (Airflow DAG: `mssql_ingestion_dag`)
- Connect to MSSQL Server and read datasets
- Validate data quality with Great Expectations
- Store raw data in PostgreSQL `bronze_*` tables

### 2. ELT Processing (Airflow DAG: `spark_elt_dag`)
- Read from Bronze layer using Spark
- Clean and validate data
- Write to PostgreSQL Silver tables

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
dokploy deploy --project economic-data-platform
```

## 📚 Documentation

- [Architecture Details](.sisyphus/plans/)
- [Deployment Guide](economic-data-platform/DEPLOYMENT_GUIDE.md)

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

- [Microsoft SQL Server](https://www.microsoft.com/sql-server) - Input data source
- [Apache Airflow](https://airflow.apache.org/) - Workflow orchestration
- [dbt](https://www.getdbt.com/) - Data transformations
- [Dokploy](https://dokploy.com/) - Deployment platform

## 📞 Contact

- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com
- LinkedIn: [Your Name](https://linkedin.com/in/yourprofile)

---

**Built with ❤️ for Data Engineering**
