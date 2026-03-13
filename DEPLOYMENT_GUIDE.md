# 🚀 Quick Deployment Guide

## ⚠️ Before You Start

**IMPORTANT**: All sensitive credentials are stored in `.credentials/CREDENTIALS.md`

---

## 📋 Pre-Deployment Checklist

### 1. GitHub Repository Setup
```bash
# Repository already configured
Repository: https://github.com/20021456/kaggle-ecommerce-data-platform
Remote: origin → https://github.com/20021456/kaggle-ecommerce-data-platform.git
Branch: main
```

### 2. VPS Access
```bash
# SSH into VPS
ssh root@49.12.105.103

# Verify Docker is installed
docker --version
docker-compose --version
```

### 3. Dokploy Access
- Dashboard: https://dokploy.evanguyen3110.space/dashboard/projects
- Login: nguyenevan3110@gmail.com / Minhtrung02@
- Project: E-Commerce System

---

## 🔐 Step 1: Setup Credentials

### Generate Required Passwords
```bash
# PostgreSQL password
openssl rand -base64 20

# ClickHouse password
openssl rand -base64 20

# Redis password
openssl rand -base64 20

# Airflow Fernet key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# MinIO access key (20 chars)
openssl rand -base64 15

# MinIO secret key (40 chars)
openssl rand -base64 30
```

### Setup Kaggle API
```bash
# On your local machine
# 1. Go to https://www.kaggle.com/settings
# 2. Click "Create New API Token"
# 3. Download kaggle.json
# 4. Move to ~/.kaggle/kaggle.json
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json
```

---

## 🌐 Step 2: Configure DNS

### Add A Records to evanguyen3110.space
```
data.evanguyen3110.space      → 49.12.105.103
airflow.evanguyen3110.space   → 49.12.105.103
grafana.evanguyen3110.space   → 49.12.105.103
api.evanguyen3110.space       → 49.12.105.103
minio.evanguyen3110.space     → 49.12.105.103
prometheus.evanguyen3110.space → 49.12.105.103
```

**Note**: Set Proxy status to "DNS only" (not proxied) - Traefik will handle SSL

---

## 📦 Step 3: Push to GitHub

```bash
# Verify git status
cd "D:\Cursor\Python\Database system"
git status

# Push to GitHub
git push -u origin main

# If authentication required, use:
# Username: 20021456
# Password: Minhtrung02@ (or use Personal Access Token)
```

---

## 🚀 Step 4: Deploy to Dokploy

### Option A: Via Dokploy Dashboard (Recommended)

1. **Login to Dokploy**
   - Go to: https://dokploy.evanguyen3110.space/dashboard/projects
   - Login: nguyenevan3110@gmail.com / Minhtrung02@

2. **Create New Application**
   - Click "E-Commerce System" project
   - Click "Create Application"
   - Select "GitHub Repository"

3. **Configure Application**
   ```
   Name: kaggle-data-platform
   Repository: https://github.com/20021456/kaggle-ecommerce-data-platform
   Branch: main
   Build Type: Docker Compose
   Compose File: docker-compose.dokploy.yml
   ```

4. **Add Environment Variables**
   - Click "Environment" tab
   - Add all variables from `.credentials/CREDENTIALS.md`
   - Key variables:
     - DATABASE_URL
     - CLICKHOUSE_PASSWORD
     - REDIS_PASSWORD
     - KAGGLE_USERNAME
     - KAGGLE_KEY
     - AIRFLOW_FERNET_KEY
     - AWS_ACCESS_KEY_ID
     - AWS_SECRET_ACCESS_KEY

5. **Configure Domains**
   - Add domains:
     - data.evanguyen3110.space (port 8000)
     - airflow.evanguyen3110.space (port 8080)
     - grafana.evanguyen3110.space (port 3000)
     - api.evanguyen3110.space (port 8000)
     - minio.evanguyen3110.space (port 9001)

6. **Deploy**
   - Click "Deploy" button
   - Monitor logs for any errors

### Option B: Via SSH (Manual)

```bash
# SSH into VPS
ssh root@49.12.105.103

# Clone repository
cd /opt
git clone https://github.com/20021456/kaggle-ecommerce-data-platform.git
cd kaggle-ecommerce-data-platform

# Create .env file
nano .env
# Paste environment variables from .credentials/CREDENTIALS.md

# Start services
docker-compose -f docker-compose.dokploy.yml up -d

# Check logs
docker-compose logs -f
```

---

## ✅ Step 5: Verify Deployment

### Check Services
```bash
# On VPS
docker ps

# Should see containers:
# - postgres
# - clickhouse
# - redis
# - hdfs-namenode
# - hdfs-datanode1
# - hdfs-datanode2
# - airflow-webserver
# - airflow-scheduler
# - grafana
# - prometheus
# - api
```

### Test Endpoints
```bash
# API Health Check
curl https://api.evanguyen3110.space/api/v1/health

# Airflow UI
# Open: https://airflow.evanguyen3110.space
# Login: admin / [AIRFLOW_ADMIN_PASSWORD]

# Grafana
# Open: https://grafana.evanguyen3110.space
# Login: admin / [GRAFANA_ADMIN_PASSWORD]
```

---

## 🔧 Step 6: Initialize Data Pipeline

### 1. Setup Databases
```bash
# SSH into VPS
ssh root@49.12.105.103

# Run database initialization
docker exec -it postgres psql -U economic_user -d economic_data -f /docker-entrypoint-initdb.d/01_bronze_schema.sql
docker exec -it postgres psql -U economic_user -d economic_data -f /docker-entrypoint-initdb.d/02_silver_schema.sql
```

### 2. Download Kaggle Dataset
```bash
# On VPS or trigger via Airflow DAG
docker exec -it airflow-scheduler airflow dags trigger kaggle_ingestion_dag
```

### 3. Monitor Pipeline
- Go to: https://airflow.evanguyen3110.space
- Check DAG runs
- Monitor logs

---

## 📊 Step 7: Setup Monitoring

### Grafana Dashboards
1. Login to Grafana: https://grafana.evanguyen3110.space
2. Add Prometheus data source: http://prometheus:9090
3. Import dashboards from `monitoring/grafana/dashboards/`

### Prometheus Targets
- Check: https://prometheus.evanguyen3110.space/targets
- Verify all targets are UP

---

## 🐛 Troubleshooting

### Logs
```bash
# View all logs
docker-compose logs -f

# Specific service
docker-compose logs -f airflow-scheduler
docker-compose logs -f postgres
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart airflow-scheduler
```

### Database Connection Issues
```bash
# Test PostgreSQL
docker exec -it postgres psql -U economic_user -d economic_data -c "SELECT 1;"

# Test ClickHouse
curl http://49.12.105.103:8123/ping
```

---

## 📝 Post-Deployment Tasks

- [ ] Verify all services are running
- [ ] Test API endpoints
- [ ] Run initial data ingestion
- [ ] Setup Grafana dashboards
- [ ] Configure Airflow DAGs
- [ ] Test data pipeline end-to-end
- [ ] Setup backup strategy
- [ ] Configure monitoring alerts
- [ ] Document any custom configurations

---

## 🔒 Security Checklist

- [ ] Change all default passwords
- [ ] Enable firewall on VPS
- [ ] Configure SSL certificates (auto via Traefik)
- [ ] Restrict database access to localhost
- [ ] Setup SSH key authentication
- [ ] Disable root SSH login
- [ ] Enable fail2ban
- [ ] Regular security updates

---

## 📞 Support

- **Credentials**: See `.credentials/CREDENTIALS.md`
- **Deployment Config**: See `.sisyphus/notepads/kaggle-ecommerce-data-engineering/deployment.md`
- **Architecture**: See `.sisyphus/plans/kaggle-ecommerce-data-engineering.md`

---

**Last Updated**: 2026-03-13
