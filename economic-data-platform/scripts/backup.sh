#!/bin/bash
# Backup Script for Economic Data Platform
# Creates backups of databases and configurations

set -e

# Configuration
BACKUP_ROOT="/opt/backups/economic-data-platform"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_ROOT}/${TIMESTAMP}"
RETENTION_DAYS=30

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Starting backup process...${NC}"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Backup PostgreSQL
echo "Backing up PostgreSQL..."
docker exec economic-postgres pg_dump -U economic_user economic_data | gzip > "${BACKUP_DIR}/postgres_backup.sql.gz"

# Backup ClickHouse
echo "Backing up ClickHouse..."
docker exec economic-clickhouse clickhouse-client --query "SELECT * FROM system.tables WHERE database = 'economic_data'" > "${BACKUP_DIR}/clickhouse_schema.txt"

# Backup configurations
echo "Backing up configurations..."
cp -r ./src/orchestration/dags "${BACKUP_DIR}/dags_backup"
cp -r ./src/processing/dbt_project "${BACKUP_DIR}/dbt_backup"
cp .env.production "${BACKUP_DIR}/env_backup"

# Backup MinIO data
echo "Backing up MinIO..."
docker exec economic-minio mc mirror local/bronze "${BACKUP_DIR}/minio_bronze"
docker exec economic-minio mc mirror local/silver "${BACKUP_DIR}/minio_silver"
docker exec economic-minio mc mirror local/gold "${BACKUP_DIR}/minio_gold"

# Create backup manifest
cat > "${BACKUP_DIR}/manifest.txt" << EOF
Backup Manifest
===============
Timestamp: ${TIMESTAMP}
Backup Directory: ${BACKUP_DIR}

Contents:
- PostgreSQL database dump
- ClickHouse schema
- Airflow DAGs
- dbt project
- Environment configuration
- MinIO data (bronze, silver, gold layers)

Backup Size: $(du -sh ${BACKUP_DIR} | cut -f1)
EOF

echo -e "${GREEN}✓ Backup completed: ${BACKUP_DIR}${NC}"

# Cleanup old backups
echo "Cleaning up old backups (older than ${RETENTION_DAYS} days)..."
find "${BACKUP_ROOT}" -type d -mtime +${RETENTION_DAYS} -exec rm -rf {} +

echo -e "${GREEN}✓ Backup process completed${NC}"
