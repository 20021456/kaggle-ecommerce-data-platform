# 🌐 Deployment & Configuration Reference

## 📋 Table of Contents
- [Server & Web URLs](#server--web-urls)
- [Database Connections](#database-connections)
- [API Endpoints](#api-endpoints)
- [File Paths & Directories](#file-paths--directories)
- [GitHub Repository](#github-repository)
- [MCP Server Configuration](#mcp-server-configuration)
- [Environment Variables](#environment-variables)
- [Dokploy Configuration](#dokploy-configuration)
- [Monitoring & Observability](#monitoring--observability)

---

## 🌍 Server & Web URLs

### Production URLs (Dokploy Deployment)
```
Main Domain: https://yourdomain.com
Dokploy Dashboard: https://dokploy.yourdomain.com
Airflow UI: https://airflow.yourdomain.com
Grafana: https://grafana.yourdomain.com
API: https://api.yourdomain.com
MinIO Console: https://minio.yourdomain.com
Prometheus: https://prometheus.yourdomain.com
```

### Local Development URLs
```
Airflow UI: http://localhost:8080
Grafana: http://localhost:3000
API: http://localhost:8000
MinIO Console: http://localhost:9001
Prometheus: http://localhost:9090
PostgreSQL: localhost:5432
ClickHouse HTTP: http://localhost:8123
ClickHouse Native: localhost:9000
Redis: localhost:6379
Kafka: localhost:9092
HDFS NameNode UI: http://localhost:9870
HDFS DataNode UI: http://localhost:9864
Spark Master UI: http://localhost:8081
Spark Worker UI: http://localhost:8082
```

### Kaggle URLs
```
Kaggle Website: https://www.kaggle.com
Kaggle API Docs: https://www.kaggle.com/docs/api
Brazilian E-Commerce Dataset: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
Kaggle Profile: https://www.kaggle.com/[your-username]
```

---

## 🗄️ Database Connections

### PostgreSQL (OLTP - Transactional)
```yaml
Host: localhost (dev) / postgres (docker) / [production-ip] (prod)
Port: 5432
Database: economic_data
Username: economic_user
Password: [from .env]
Connection String: postgresql://economic_user:password@localhost:5432/economic_data
JDBC URL: jdbc:postgresql://localhost:5432/economic_data
```

**Schemas:**
- `bronze` - Raw data from HDFS
- `silver` - Cleaned and validated data
- `gold` - Analytics-ready data
- `public` - Default schema

### ClickHouse (OLAP - Analytics)
```yaml
Host: localhost (dev) / clickhouse (docker) / [production-ip] (prod)
HTTP Port: 8123
Native Port: 9000
Database: economic_data
Username: default
Password: [from .env]
HTTP URL: http://localhost:8123
JDBC URL: jdbc:clickhouse://localhost:8123/economic_data
```

**Databases:**
- `economic_data` - Main analytics database
- `system` - ClickHouse system tables

### Redis (Cache & Queue)
```yaml
Host: localhost (dev) / redis (docker) / [production-ip] (prod)
Port: 6379
Password: [from .env]
Connection String: redis://:[password]@localhost:6379/0
```

**Key Namespaces:**
- `cache:*` - Application cache
- `queue:*` - Task queues
- `checkpoint:*` - Pipeline checkpoints
- `metrics:*` - Real-time metrics

### HDFS (Data Lake)
```yaml
NameNode Host: localhost (dev) / hdfs-namenode (docker)
NameNode Port: 9000
NameNode HTTP: 9870
DataNode Port: 9864
WebHDFS Port: 9870
Connection URI: hdfs://localhost:9000
```

**HDFS Paths:**
```
/bronze/olist/orders/
/bronze/olist/customers/
/bronze/olist/products/
/bronze/olist/sellers/
/bronze/olist/order_items/
/bronze/olist/payments/
/bronze/olist/reviews/
/bronze/olist/geolocation/
/bronze/olist/category_translation/
```

---

## 🔌 API Endpoints

### FastAPI Application
```
Base URL (Local): http://localhost:8000
Base URL (Prod): https://api.yourdomain.com
API Docs: /docs
OpenAPI Schema: /openapi.json
Health Check: /api/v1/health
```

### Endpoint Categories
```
Crypto Endpoints:
  GET  /api/v1/crypto/coins
  GET  /api/v1/crypto/coins/{symbol}
  GET  /api/v1/crypto/prices/{symbol}

Economic Endpoints:
  GET  /api/v1/economic/indicators
  GET  /api/v1/economic/gdp/{country}
  GET  /api/v1/economic/inflation/history

E-Commerce Endpoints (New):
  GET  /api/v1/ecommerce/orders
  GET  /api/v1/ecommerce/orders/{order_id}
  GET  /api/v1/ecommerce/customers/{customer_id}
  GET  /api/v1/ecommerce/products
  GET  /api/v1/ecommerce/sellers
  GET  /api/v1/ecommerce/analytics/sales
  GET  /api/v1/ecommerce/analytics/customer-segments

Analytics Endpoints:
  GET  /api/v1/analytics/btc-inflation-correlation
  GET  /api/v1/analytics/macro-crypto-overview
```

---

## 📂 File Paths & Directories

### Project Root
```
Windows: D:\Cursor\Python\Database system
Linux/Mac: /path/to/Database system
```

### Key Directories
```
Project Structure:
D:\Cursor\Python\Database system\
├── economic-data-platform/          # Main application
│   ├── src/
│   │   ├── ingestion/              # Data ingestion clients
│   │   │   ├── crypto/
│   │   │   ├── economic/
│   │   │   └── ecommerce/          # NEW: Kaggle/Olist ingestion
│   │   ├── processing/
│   │   │   ├── spark_jobs/         # NEW: Spark ELT jobs
│   │   │   └── dbt_project/        # dbt transformations
│   │   ├── orchestration/
│   │   │   └── dags/               # Airflow DAGs
│   │   ├── api/                    # FastAPI application
│   │   └── utils/
│   ├── sql/                        # SQL schemas
│   │   ├── postgres/
│   │   └── clickhouse/
│   ├── monitoring/                 # Prometheus/Grafana configs
│   ├── dokploy/                    # Dokploy deployment configs
│   ├── tests/                      # Unit & integration tests
│   └── docker-compose.yml
├── .sisyphus/                      # Orchestration metadata
│   ├── plans/
│   └── notepads/
└── ECONOMIC_DATA_PLATFORM_IMPLEMENTATION_PLAN.md
```

### Configuration Files
```
Environment Files:
  .env                              # Local development
  .env.example                      # Template
  .env.dokploy                      # Dokploy production
  dokploy/.env.example              # Dokploy template

Docker Files:
  docker-compose.yml                # Main compose file
  docker-compose.dokploy.yml        # Dokploy variant
  Dockerfile                        # Main app image
  Dockerfile.minimal                # Minimal image

Airflow:
  src/orchestration/dags/           # DAG definitions
  airflow.cfg                       # Airflow configuration

dbt:
  src/processing/dbt_project/dbt_project.yml
  src/processing/dbt_project/profiles.yml

Monitoring:
  monitoring/prometheus/prometheus.yml
  monitoring/grafana/dashboards/
```

### Data Directories
```
Local Data Storage:
  data/raw/                         # Raw downloaded data
  data/processed/                   # Processed data
  data/kaggle/                      # Kaggle datasets
  data/kaggle/olist/                # Olist e-commerce data

Docker Volumes:
  postgres_data/                    # PostgreSQL data
  clickhouse_data/                  # ClickHouse data
  redis_data/                       # Redis data
  hdfs_namenode/                    # HDFS NameNode data
  hdfs_datanode1/                   # HDFS DataNode 1 data
  hdfs_datanode2/                   # HDFS DataNode 2 data
  minio_data/                       # MinIO/S3 data
  airflow_logs/                     # Airflow logs
```

---

## 🐙 GitHub Repository

### Repository Information
```
Repository Name: kaggle-ecommerce-data-platform
GitHub URL: https://github.com/[your-username]/kaggle-ecommerce-data-platform
Clone URL (HTTPS): https://github.com/[your-username]/kaggle-ecommerce-data-platform.git
Clone URL (SSH): git@github.com:[your-username]/kaggle-ecommerce-data-platform.git
```

### Git Configuration
```bash
# Initialize repository
git init
git remote add origin https://github.com/[your-username]/kaggle-ecommerce-data-platform.git

# Branch structure
main                    # Production-ready code
develop                 # Development branch
feature/*               # Feature branches
hotfix/*                # Hotfix branches
release/*               # Release branches
```

### GitHub Actions Workflows
```
.github/workflows/
├── ci.yml              # Continuous Integration
├── cd.yml              # Continuous Deployment
├── tests.yml           # Run tests
├── lint.yml            # Code linting
└── docker-build.yml    # Docker image build
```

### GitHub Secrets (Required)
```
KAGGLE_USERNAME         # Kaggle API username
KAGGLE_KEY              # Kaggle API key
DOKPLOY_TOKEN           # Dokploy deployment token
POSTGRES_PASSWORD       # PostgreSQL password
CLICKHOUSE_PASSWORD     # ClickHouse password
REDIS_PASSWORD          # Redis password
AIRFLOW_FERNET_KEY      # Airflow encryption key
```

---

## 🔧 MCP Server Configuration

### MCP Servers in Use

#### 1. Playwright MCP (Browser Automation)
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@executeautomation/playwright-mcp-server"]
    }
  }
}
```

#### 2. Context7 MCP (Documentation)
```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
```

#### 3. Exa Web Search MCP
```json
{
  "mcpServers": {
    "exa": {
      "command": "npx",
      "args": ["-y", "@upstash/exa-mcp"],
      "env": {
        "EXA_API_KEY": "your-exa-api-key"
      }
    }
  }
}
```

#### 4. GitHub MCP (Repository Management)
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your-github-token"
      }
    }
  }
}
```

#### 5. PostgreSQL MCP (Database Operations)
```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_CONNECTION_STRING": "postgresql://economic_user:password@localhost:5432/economic_data"
      }
    }
  }
}
```

### MCP Configuration File Location
```
Windows: %APPDATA%\Code\User\globalStorage\rooveterinaryinc.roo-cline\settings\cline_mcp_settings.json
Linux/Mac: ~/.config/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json
```

### Complete MCP Configuration
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@executeautomation/playwright-mcp-server"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token_here"
      }
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_CONNECTION_STRING": "postgresql://economic_user:password@localhost:5432/economic_data"
      }
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    },
    "exa": {
      "command": "npx",
      "args": ["-y", "@upstash/exa-mcp"],
      "env": {
        "EXA_API_KEY": "your_exa_api_key_here"
      }
    }
  }
}
```

---

## 🔐 Environment Variables

### Required Environment Variables

#### Kaggle API
```bash
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_KEY=your_kaggle_api_key
```

#### Database Credentials
```bash
# PostgreSQL
POSTGRES_USER=economic_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=economic_data
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# ClickHouse
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=your_secure_password
CLICKHOUSE_DB=economic_data
CLICKHOUSE_HOST=localhost
CLICKHOUSE_HTTP_PORT=8123
CLICKHOUSE_NATIVE_PORT=9000

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_secure_password
```

#### HDFS Configuration
```bash
HDFS_NAMENODE_HOST=localhost
HDFS_NAMENODE_PORT=9000
HDFS_REPLICATION_FACTOR=2
HDFS_BLOCK_SIZE=134217728
```

#### Airflow Configuration
```bash
AIRFLOW_HOME=/opt/airflow
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql://economic_user:password@postgres:5432/airflow
AIRFLOW__CORE__FERNET_KEY=your_fernet_key_here
AIRFLOW__CORE__LOAD_EXAMPLES=false
AIRFLOW__WEBSERVER__SECRET_KEY=your_secret_key_here
```

#### Spark Configuration
```bash
SPARK_MASTER_URL=spark://localhost:7077
SPARK_DRIVER_MEMORY=2g
SPARK_EXECUTOR_MEMORY=2g
SPARK_EXECUTOR_CORES=2
```

#### API Configuration
```bash
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_RELOAD=true
```

#### Monitoring
```bash
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=your_secure_password
```

### Environment File Template (.env.example)
```bash
# Copy this file to .env and fill in your values
# DO NOT commit .env to version control

# Kaggle API
KAGGLE_USERNAME=
KAGGLE_KEY=

# PostgreSQL
POSTGRES_USER=economic_user
POSTGRES_PASSWORD=
POSTGRES_DB=economic_data

# ClickHouse
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=
CLICKHOUSE_DB=economic_data

# Redis
REDIS_PASSWORD=

# Airflow
AIRFLOW__CORE__FERNET_KEY=
AIRFLOW__WEBSERVER__SECRET_KEY=

# Grafana
GRAFANA_ADMIN_PASSWORD=

# GitHub
GITHUB_TOKEN=

# MCP Servers
EXA_API_KEY=
```

---

## 🚀 Dokploy Configuration

### Dokploy Server Setup
```bash
# Dokploy Installation
curl -sSL https://dokploy.com/install.sh | sh

# Access Dokploy
URL: https://dokploy.yourdomain.com
Default Port: 3000
```

### Dokploy Project Structure
```
Project Name: kaggle-ecommerce-platform

Applications:
├── api-service              # FastAPI application
├── airflow-webserver        # Airflow UI
├── airflow-scheduler        # Airflow scheduler
└── spark-master             # Spark master node

Databases:
├── postgres                 # PostgreSQL database
├── clickhouse               # ClickHouse database
├── redis                    # Redis cache
└── hdfs-cluster             # HDFS cluster

Networks:
└── economic-network         # Shared network
```

### Dokploy Deployment Files
```
dokploy/
├── application/
│   └── docker-compose.yml          # Main application
├── databases/
│   ├── docker-compose.postgres.yml
│   ├── docker-compose.clickhouse.yml
│   ├── docker-compose.redis.yml
│   └── docker-compose.hdfs.yml
├── shared-databases/
│   └── docker-compose.yml          # Shared DB services
└── minimal/
    └── docker-compose.yml          # Minimal setup
```

### Dokploy Environment Variables
```bash
# Set in Dokploy UI under each service
DOKPLOY_PROJECT_NAME=kaggle-ecommerce-platform
DOKPLOY_DOMAIN=yourdomain.com
DOKPLOY_SSL_EMAIL=your@email.com
```

---

## 📊 Monitoring & Observability

### Prometheus Targets
```yaml
# monitoring/prometheus/prometheus.yml
scrape_configs:
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
  
  - job_name: 'clickhouse'
    static_configs:
      - targets: ['clickhouse:8123']
  
  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
  
  - job_name: 'airflow'
    static_configs:
      - targets: ['airflow-webserver:8080']
  
  - job_name: 'api'
    static_configs:
      - targets: ['api:8000']
  
  - job_name: 'hdfs-namenode'
    static_configs:
      - targets: ['hdfs-namenode:9870']
```

### Grafana Dashboards
```
Dashboard URLs:
  System Overview: http://localhost:3000/d/system-overview
  Database Metrics: http://localhost:3000/d/database-metrics
  Airflow Metrics: http://localhost:3000/d/airflow-metrics
  Data Pipeline: http://localhost:3000/d/data-pipeline
  HDFS Cluster: http://localhost:3000/d/hdfs-cluster
```

### Log Locations
```
Application Logs:
  API: logs/api/app.log
  Airflow: airflow_logs/
  Spark: logs/spark/

Docker Logs:
  docker-compose logs -f [service-name]
  docker logs [container-name]

System Logs:
  /var/log/syslog (Linux)
  Event Viewer (Windows)
```

---

## 📝 Quick Reference Commands

### Start Services
```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d postgres clickhouse redis

# Start with HDFS
docker-compose --profile hdfs up -d

# Start with Airflow
docker-compose --profile airflow up -d
```

### Check Status
```bash
# Check all containers
docker-compose ps

# Check logs
docker-compose logs -f [service-name]

# Check resource usage
docker stats
```

### Database Access
```bash
# PostgreSQL
docker exec -it economic-postgres psql -U economic_user -d economic_data

# ClickHouse
docker exec -it economic-clickhouse clickhouse-client

# Redis
docker exec -it economic-redis redis-cli
```

### HDFS Commands
```bash
# List HDFS files
docker exec -it hdfs-namenode hdfs dfs -ls /

# Upload to HDFS
docker exec -it hdfs-namenode hdfs dfs -put /local/path /hdfs/path

# Download from HDFS
docker exec -it hdfs-namenode hdfs dfs -get /hdfs/path /local/path
```

---

## 🔗 External Resources

### Documentation
- Kaggle API: https://github.com/Kaggle/kaggle-api
- Apache Airflow: https://airflow.apache.org/docs/
- Apache Spark: https://spark.apache.org/docs/latest/
- dbt: https://docs.getdbt.com/
- Dokploy: https://dokploy.com/docs
- HDFS: https://hadoop.apache.org/docs/stable/
- PostgreSQL: https://www.postgresql.org/docs/
- ClickHouse: https://clickhouse.com/docs/
- Great Expectations: https://docs.greatexpectations.io/

### Community
- Airflow Slack: https://apache-airflow.slack.com/
- dbt Slack: https://www.getdbt.com/community/join-the-community/
- Data Engineering Subreddit: https://reddit.com/r/dataengineering

---

**Last Updated:** 2026-03-13
**Maintained By:** Data Engineering Team
**Version:** 1.0.0
