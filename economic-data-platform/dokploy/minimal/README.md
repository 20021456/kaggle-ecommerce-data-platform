# 🚀 Minimal VPS Deployment (2 vCPU, 4GB RAM)

Optimized deployment for small VPS với chi phí thấp (~$3.49/tháng).

## 📊 Resource Allocation

| Service | RAM | CPU | Notes |
|---------|-----|-----|-------|
| PostgreSQL | 768MB | 0.5 | Main database |
| Redis | 192MB | 0.25 | Cache |
| API | 512MB | 0.75 | FastAPI app |
| System | ~500MB | 0.5 | OS + Docker |
| **Total** | **~2GB** | **2 cores** | Fits 4GB VPS |

## ❌ Removed Services (Too Heavy)

- ~~ClickHouse~~ → Use PostgreSQL for analytics
- ~~Kafka~~ → Direct API calls instead of streaming
- ~~Zookeeper~~ → Not needed without Kafka
- ~~Airflow~~ → Use cron jobs instead
- ~~MinIO~~ → Store data in PostgreSQL
- ~~Prometheus~~ → Optional, use Grafana Cloud free tier

## ✅ Included Services

- **PostgreSQL** - Database cho cả OLTP và analytics
- **Redis** - Cache để giảm tải API calls
- **FastAPI** - REST API endpoints
- **Grafana** - Monitoring (optional)

## 🛠️ Quick Deploy

### 1. SSH vào VPS

```bash
ssh root@your-vps-ip
```

### 2. Install Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sh
apt install docker-compose-plugin -y

# Start Docker
systemctl enable docker
systemctl start docker
```

### 3. Clone/Upload Project

```bash
# Option A: Clone từ GitHub
git clone https://github.com/yourusername/economic-data-platform.git
cd economic-data-platform/dokploy/minimal

# Option B: Upload từ local
scp -r economic-data-platform root@your-vps-ip:/opt/
ssh root@your-vps-ip
cd /opt/economic-data-platform/dokploy/minimal
```

### 4. Configure

```bash
cp .env.example .env
nano .env
```

Thay đổi:
```env
DOMAIN=yourdomain.com
POSTGRES_PASSWORD=your_secure_password
REDIS_PASSWORD=your_redis_password
JWT_SECRET_KEY=generate_random_32_chars
```

### 5. Deploy

```bash
chmod +x deploy.sh
./deploy.sh
```

### 6. Setup SSL (Optional)

Nếu có domain, dùng Caddy (nhẹ hơn Traefik/Nginx):

```bash
# Install Caddy
apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt update && apt install caddy

# Configure
cat > /etc/caddy/Caddyfile << 'EOF'
api.yourdomain.com {
    reverse_proxy localhost:8000
}
EOF

# Restart
systemctl restart caddy
```

## 📝 Usage

### API Endpoints

```bash
# Health check
curl http://your-vps-ip:8000/health

# API docs
open http://your-vps-ip:8000/docs

# Get crypto prices
curl http://your-vps-ip:8000/api/v1/crypto/coins?limit=10

# Get economic data
curl http://your-vps-ip:8000/api/v1/economic/fred/latest
```

### Database Access

```bash
# Connect to PostgreSQL
docker exec -it economic-postgres psql -U economic_user -d economic_data

# Check tables
\dt bronze.*
\dt silver.*
```

### View Logs

```bash
# All services
docker-compose logs -f

# API only
docker-compose logs -f api
```

### Monitor Resources

```bash
# Memory usage
docker stats

# Disk usage
df -h
du -sh /var/lib/docker/volumes/*
```

## ⚡ Performance Tips

### 1. Enable Swap (Khuyến nghị)

```bash
# Create 2GB swap
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Set swappiness
echo 'vm.swappiness=10' >> /etc/sysctl.conf
sysctl -p
```

### 2. Clean Docker Regularly

```bash
# Add to crontab
crontab -e

# Add line:
0 3 * * * docker system prune -af --volumes
```

### 3. Limit Log Size

```bash
# /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}

# Restart Docker
systemctl restart docker
```

## 🔧 Common Commands

```bash
# Restart all
docker-compose restart

# Restart API only
docker-compose restart api

# Stop all
docker-compose down

# Update API
docker-compose build api
docker-compose up -d api

# Backup database
docker exec economic-postgres pg_dump -U economic_user economic_data > backup.sql

# Restore database
cat backup.sql | docker exec -i economic-postgres psql -U economic_user economic_data
```

## 🆘 Troubleshooting

### Out of Memory

```bash
# Check memory
free -h

# Enable swap (see above)

# Reduce PostgreSQL memory
# Edit docker-compose.yml: shared_buffers=128MB
```

### API Slow

```bash
# Check if Redis is working
docker exec economic-redis redis-cli -a YOUR_PASSWORD ping

# Increase rate limit cooldown
# Edit .env: API_RATE_LIMIT_PERIOD=120
```

### Disk Full

```bash
# Check disk
df -h

# Clean Docker
docker system prune -af

# Clean old logs
truncate -s 0 /var/lib/docker/containers/*/*-json.log
```

## 📈 Scaling Up

Khi cần mở rộng (upgrade VPS):

1. **4GB → 8GB RAM**: Enable Grafana monitoring
2. **8GB → 16GB RAM**: Add MinIO for data lake
3. **16GB+ RAM**: Full stack với ClickHouse, Kafka

## 💡 Alternative: Dokploy UI

Nếu muốn dùng Dokploy UI thay vì command line:

1. Install Dokploy: `curl -sSL https://dokploy.com/install.sh | sh`
2. Dokploy chiếm ~500MB RAM
3. Upload `docker-compose.yml` qua UI
4. Configure environment variables qua UI
5. Deploy!

**Note**: Với 4GB RAM, Dokploy UI có thể hơi nặng. Recommend dùng docker-compose trực tiếp.
