# 🚀 Dokploy Deployment Guide

Quick deployment guide for Economic Data Analytics Platform on Dokploy.

## 📋 Overview

The platform is split into two Dokploy projects:

1. **shared-databases** - All database services (PostgreSQL, ClickHouse, Redis, MinIO, Kafka)
2. **application** - API, monitoring, and workers

## 🛠️ Step-by-Step Deployment

### 1. Install Dokploy on your VPS

```bash
curl -sSL https://dokploy.com/install.sh | sh
```

Access Dokploy at `http://YOUR_VPS_IP:3000`

### 2. Create Network

In Dokploy terminal or SSH:
```bash
docker network create dokploy-network
```

### 3. Deploy Shared Databases

1. In Dokploy, create project: **"shared-databases"**

2. Add Docker Compose application:
   - Source: `dokploy/shared-databases/docker-compose.yml`
   
3. Configure environment variables:
   ```env
   DOMAIN=yourdomain.com
   POSTGRES_PASSWORD=secure_password_123
   CLICKHOUSE_PASSWORD=secure_password_456
   REDIS_PASSWORD=secure_password_789
   MINIO_ACCESS_KEY=minioadmin
   MINIO_SECRET_KEY=miniosecret123
   ```

4. Deploy and wait for all services to be healthy

### 4. Initialize Databases

Connect to PostgreSQL and run schema files:

```bash
# In Dokploy terminal
docker exec -it shared-postgres psql -U economic_user -d economic_data

# Run schemas (copy content from sql/postgres/*.sql files)
```

### 5. Deploy Application

1. Create project: **"economic-data-platform"**

2. Add Docker Compose application:
   - Source: `dokploy/application/docker-compose.yml`

3. Configure environment variables:
   ```env
   DOMAIN=yourdomain.com
   
   # Same passwords as shared-databases
   POSTGRES_USER=economic_user
   POSTGRES_PASSWORD=secure_password_123
   POSTGRES_DB=economic_data
   REDIS_PASSWORD=secure_password_789
   MINIO_ACCESS_KEY=minioadmin
   MINIO_SECRET_KEY=miniosecret123
   
   # Generate this
   JWT_SECRET_KEY=your_jwt_secret_32_chars
   
   # API Keys
   FRED_API_KEY=your_key
   
   # Grafana
   GRAFANA_ADMIN_PASSWORD=grafana_password
   ```

4. Deploy!

### 6. Configure Domains

In Dokploy Settings → Domains:

| Subdomain | Service | Port |
|-----------|---------|------|
| api.yourdomain.com | economic-api | 8000 |
| grafana.yourdomain.com | economic-grafana | 3000 |
| minio.yourdomain.com | shared-minio | 9001 |

### 7. Verify Deployment

```bash
# Health check
curl https://api.yourdomain.com/health

# API docs
open https://api.yourdomain.com/docs

# Test endpoint
curl https://api.yourdomain.com/api/v1/crypto/coins?limit=5
```

## 📁 File Structure

```
dokploy/
├── README.md                    # This file
├── shared-databases/
│   ├── docker-compose.yml       # All databases
│   └── .env.example
├── application/
│   ├── docker-compose.yml       # API + Monitoring
│   └── .env.example
└── databases/                   # Individual DB compose files
    ├── docker-compose.postgres.yml
    ├── docker-compose.redis.yml
    └── docker-compose.clickhouse.yml
```

## 🔧 Common Commands

```bash
# View all containers
docker ps

# View logs
docker logs economic-api -f

# Restart API
docker restart economic-api

# Access PostgreSQL
docker exec -it shared-postgres psql -U economic_user -d economic_data

# Access Redis
docker exec -it shared-redis redis-cli -a YOUR_PASSWORD
```

## 📊 Resource Requirements

| Service | Memory | CPU |
|---------|--------|-----|
| PostgreSQL | 2GB | 1 core |
| ClickHouse | 4GB | 2 cores |
| Redis | 512MB | 0.5 core |
| MinIO | 1GB | 1 core |
| Kafka | 2GB | 1 core |
| API | 2GB | 2 cores |
| **Total** | **~12GB** | **~8 cores** |

Recommended VPS: **16GB RAM, 8 vCPU**

## 🆘 Troubleshooting

### API can't connect to database
- Ensure shared-databases is running first
- Check network: both must use `dokploy-network`
- Verify passwords match in both .env files

### SSL certificate issues
- Ensure domain DNS points to VPS IP
- Wait a few minutes for Let's Encrypt

### Out of memory
- Reduce resource limits in compose files
- Scale down ClickHouse/Kafka if not needed

## 📚 More Info

See full documentation: [DOKPLOY_DEPLOYMENT.md](../docs/DOKPLOY_DEPLOYMENT.md)
