# 🚀 Dokploy Deployment Guide

This guide walks you through deploying the Economic Data Analytics Platform on Dokploy.

## 📋 Prerequisites

### 1. VPS Requirements
- **CPU**: 4 cores minimum (8 recommended)
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 100GB SSD minimum
- **OS**: Ubuntu 22.04 LTS or Debian 12

### 2. Domain Setup
- Domain name pointing to your VPS IP
- Subdomains configured:
  - `api.yourdomain.com` → API
  - `grafana.yourdomain.com` → Monitoring
  - `minio.yourdomain.com` → Object Storage
  - `airflow.yourdomain.com` → Orchestration (optional)

## 🛠️ Step 1: Install Dokploy

SSH into your VPS and run:

```bash
# Install Dokploy (one command)
curl -sSL https://dokploy.com/install.sh | sh

# Access Dokploy at http://YOUR_VPS_IP:3000
# Create your admin account
```

## 📦 Step 2: Prepare the Project

### Option A: Deploy from GitHub

1. Push the project to GitHub:
```bash
cd economic-data-platform
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/economic-data-platform.git
git push -u origin main
```

2. In Dokploy:
   - Create new project: "Economic Data Platform"
   - Add application → Git Repository
   - Connect your GitHub repo
   - Select branch: `main`

### Option B: Deploy via Direct Upload

1. Create a zip of the project:
```bash
zip -r economic-data-platform.zip economic-data-platform/
```

2. Upload to your VPS via SCP:
```bash
scp economic-data-platform.zip user@your-vps:/opt/
```

3. Extract on VPS:
```bash
ssh user@your-vps
cd /opt
unzip economic-data-platform.zip
cd economic-data-platform
```

## ⚙️ Step 3: Configure Environment

### 1. Copy environment template
```bash
cp .env.dokploy .env
```

### 2. Edit environment variables
```bash
nano .env
```

**Critical variables to change:**
```env
# Domain
DOMAIN=yourdomain.com

# Database passwords (use strong passwords!)
POSTGRES_PASSWORD=your_secure_postgres_password
REDIS_PASSWORD=your_secure_redis_password
CLICKHOUSE_PASSWORD=your_secure_clickhouse_password

# JWT Secret (generate with: openssl rand -hex 32)
JWT_SECRET_KEY=your_generated_jwt_secret

# MinIO credentials
MINIO_ACCESS_KEY=your_minio_access_key
MINIO_SECRET_KEY=your_minio_secret_key_min_8_chars

# API Keys
FRED_API_KEY=your_fred_api_key
BEA_API_KEY=your_bea_api_key

# Grafana
GRAFANA_ADMIN_PASSWORD=your_grafana_password
```

### 3. Generate Airflow Fernet Key (if using Airflow)
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## 🚀 Step 4: Deploy Services

### Using Dokploy UI

1. **Create Shared Databases Project:**
   - In Dokploy, create project: "Shared Databases"
   - Add PostgreSQL service
   - Add Redis service
   - Add ClickHouse service

2. **Configure each database:**
   - Set environment variables from your `.env`
   - Configure storage volumes
   - Set resource limits

3. **Create Application Project:**
   - Create project: "Economic Data Platform"
   - Add Docker Compose application
   - Select `docker-compose.dokploy.yml`
   - Link to Shared Databases network

### Using Command Line

```bash
# Make deploy script executable
chmod +x scripts/deploy-dokploy.sh

# Run deployment
./scripts/deploy-dokploy.sh
```

## 🗄️ Step 5: Database Setup in Dokploy

### PostgreSQL Setup

1. In Dokploy, go to **Services** → **Add Service** → **PostgreSQL**

2. Configuration:
```yaml
Service Name: economic-postgres
Image: postgres:16-alpine
Port: 5432

Environment Variables:
  POSTGRES_USER: economic_user
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
  POSTGRES_DB: economic_data

Volumes:
  - postgres_data:/var/lib/postgresql/data

Resources:
  Memory: 2GB
  CPU: 1 core
```

3. Run initial schemas:
```bash
# Connect to PostgreSQL
docker exec -it economic-postgres psql -U economic_user -d economic_data

# Run schema files (copy-paste from sql/postgres/ files)
\i /docker-entrypoint-initdb.d/01_bronze_schema.sql
\i /docker-entrypoint-initdb.d/02_silver_schema.sql
\i /docker-entrypoint-initdb.d/03_gold_crypto.sql
\i /docker-entrypoint-initdb.d/04_gold_economic.sql
\i /docker-entrypoint-initdb.d/05_gold_combined.sql
```

### ClickHouse Setup

1. In Dokploy, add ClickHouse service:
```yaml
Service Name: economic-clickhouse
Image: clickhouse/clickhouse-server:24.1
Ports: 
  - 8123:8123 (HTTP)
  - 9000:9000 (Native)

Resources:
  Memory: 4GB
  CPU: 2 cores
```

### Redis Setup

1. In Dokploy, add Redis service:
```yaml
Service Name: economic-redis
Image: redis:7-alpine
Port: 6379
Command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}

Resources:
  Memory: 512MB
  CPU: 0.5 core
```

## 🌐 Step 6: Configure Traefik (SSL/HTTPS)

Dokploy uses Traefik for reverse proxy. Configure domains:

1. In Dokploy → **Settings** → **Domains**

2. Add domains:
```
api.yourdomain.com     → economic-api:8000
grafana.yourdomain.com → economic-grafana:3000
minio.yourdomain.com   → economic-minio:9001
```

3. Enable SSL:
   - Dokploy automatically provisions Let's Encrypt certificates
   - Ensure ports 80 and 443 are open in firewall

## ✅ Step 7: Verify Deployment

### Health Checks

```bash
# API Health
curl https://api.yourdomain.com/health

# API Docs
open https://api.yourdomain.com/docs

# Database connection
curl https://api.yourdomain.com/health/detailed
```

### Test Endpoints

```bash
# Get crypto prices
curl https://api.yourdomain.com/api/v1/crypto/coins?limit=10

# Get economic indicators
curl https://api.yourdomain.com/api/v1/economic/fred/latest

# Get Fear & Greed Index
curl https://api.yourdomain.com/api/v1/crypto/fear-greed
```

## 📊 Step 8: Setup Monitoring

### Grafana Setup

1. Access Grafana: `https://grafana.yourdomain.com`
2. Login with credentials from `.env`
3. Add data sources:
   - Prometheus: `http://prometheus:9090`
   - PostgreSQL: `postgres:5432`
   - ClickHouse: `clickhouse:8123`

4. Import dashboards from `monitoring/grafana/dashboards/`

### Prometheus Targets

Verify all targets are healthy:
- `http://prometheus:9090/targets`

## 🔧 Common Operations

### View Logs
```bash
# All services
docker-compose -f docker-compose.dokploy.yml logs -f

# Specific service
docker-compose -f docker-compose.dokploy.yml logs -f api
```

### Restart Services
```bash
# Restart API
docker-compose -f docker-compose.dokploy.yml restart api

# Restart all
docker-compose -f docker-compose.dokploy.yml restart
```

### Backup Databases
```bash
# PostgreSQL backup
docker exec economic-postgres pg_dump -U economic_user economic_data > backup.sql

# Restore
cat backup.sql | docker exec -i economic-postgres psql -U economic_user economic_data
```

### Update Application
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.dokploy.yml build api
docker-compose -f docker-compose.dokploy.yml up -d api
```

## 🔒 Security Checklist

- [ ] Strong passwords for all services
- [ ] HTTPS enabled on all public endpoints
- [ ] Firewall configured (only 80, 443 open)
- [ ] API keys stored securely in `.env`
- [ ] Database not exposed publicly
- [ ] Regular backups configured
- [ ] Monitoring alerts set up

## 🆘 Troubleshooting

### API won't start
```bash
# Check logs
docker-compose -f docker-compose.dokploy.yml logs api

# Common issues:
# - Database not ready: Ensure postgres is healthy first
# - Missing env vars: Check .env file
# - Port conflict: Check if 8000 is in use
```

### Database connection failed
```bash
# Test PostgreSQL connection
docker exec -it economic-postgres psql -U economic_user -d economic_data -c "SELECT 1"

# Test Redis connection
docker exec -it economic-redis redis-cli -a $REDIS_PASSWORD ping
```

### SSL certificate issues
```bash
# Check Traefik logs
docker logs traefik

# Ensure domain DNS is correct
dig api.yourdomain.com
```

## 📈 Scaling

For high traffic, consider:

1. **Horizontal scaling**: Add more API containers
2. **Database replicas**: PostgreSQL read replicas
3. **Redis cluster**: For high-throughput caching
4. **CDN**: For static assets and API responses

## 📚 Additional Resources

- [Dokploy Documentation](https://docs.dokploy.com/)
- [Traefik Documentation](https://doc.traefik.io/)
- [PostgreSQL Docker](https://hub.docker.com/_/postgres)
- [ClickHouse Docker](https://hub.docker.com/r/clickhouse/clickhouse-server)
