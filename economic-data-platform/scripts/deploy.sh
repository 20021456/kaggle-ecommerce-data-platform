#!/bin/bash
# Deployment Script for Economic Data Platform
# Handles deployment to production environment

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-production}
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${PROJECT_ROOT}/backups/${TIMESTAMP}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Economic Data Platform Deployment${NC}"
echo -e "${GREEN}Environment: ${ENVIRONMENT}${NC}"
echo -e "${GREEN}========================================${NC}"

# Function to print status
print_status() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Pre-deployment checks
print_status "Running pre-deployment checks..."

# Check if required files exist
if [ ! -f "${PROJECT_ROOT}/.env.${ENVIRONMENT}" ]; then
    print_error "Environment file .env.${ENVIRONMENT} not found"
    exit 1
fi

if [ ! -f "${PROJECT_ROOT}/docker-compose.yml" ]; then
    print_error "docker-compose.yml not found"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running"
    exit 1
fi

# Check if required environment variables are set
source "${PROJECT_ROOT}/.env.${ENVIRONMENT}"

required_vars=("POSTGRES_PASSWORD" "CLICKHOUSE_PASSWORD" "AIRFLOW_FERNET_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        print_error "Required environment variable $var is not set"
        exit 1
    fi
done

print_status "✓ Pre-deployment checks passed"

# Create backup
print_status "Creating backup..."
mkdir -p "${BACKUP_DIR}"

# Backup databases
if docker ps | grep -q economic-postgres; then
    print_status "Backing up PostgreSQL..."
    docker exec economic-postgres pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > "${BACKUP_DIR}/postgres_backup.sql"
fi

if docker ps | grep -q economic-clickhouse; then
    print_status "Backing up ClickHouse..."
    docker exec economic-clickhouse clickhouse-client --query "BACKUP DATABASE economic_data TO Disk('backups', '${TIMESTAMP}')"
fi

print_status "✓ Backup completed: ${BACKUP_DIR}"

# Pull latest code
print_status "Pulling latest code..."
git fetch origin
git checkout ${ENVIRONMENT}
git pull origin ${ENVIRONMENT}

print_status "✓ Code updated"

# Build Docker images
print_status "Building Docker images..."
docker-compose -f docker-compose.yml build --no-cache

print_status "✓ Images built"

# Stop existing services
print_status "Stopping existing services..."
docker-compose -f docker-compose.yml down

print_status "✓ Services stopped"

# Start services
print_status "Starting services..."
docker-compose -f docker-compose.yml up -d

# Wait for services to be healthy
print_status "Waiting for services to be healthy..."
sleep 30

# Check service health
services=("economic-postgres" "economic-clickhouse" "economic-redis" "economic-kafka")
for service in "${services[@]}"; do
    if docker ps | grep -q ${service}; then
        print_status "✓ ${service} is running"
    else
        print_error "${service} failed to start"
        exit 1
    fi
done

# Run database migrations
print_status "Running database migrations..."
docker exec economic-postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -f /docker-entrypoint-initdb.d/init.sql

print_status "✓ Migrations completed"

# Initialize Airflow
print_status "Initializing Airflow..."
docker-compose run --rm airflow-webserver airflow db init
docker-compose run --rm airflow-webserver airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password ${AIRFLOW_ADMIN_PASSWORD}

print_status "✓ Airflow initialized"

# Run dbt tests
print_status "Running dbt tests..."
cd "${PROJECT_ROOT}/src/processing/dbt_project"
dbt deps
dbt test --profiles-dir ./profiles

if [ $? -eq 0 ]; then
    print_status "✓ dbt tests passed"
else
    print_warning "Some dbt tests failed. Check logs for details."
fi

# Verify deployment
print_status "Verifying deployment..."

# Check if services are responding
services_urls=(
    "http://localhost:5432|PostgreSQL"
    "http://localhost:8123|ClickHouse"
    "http://localhost:8080|Airflow"
    "http://localhost:9000|MinIO"
)

for service_url in "${services_urls[@]}"; do
    IFS='|' read -r url name <<< "$service_url"
    if curl -s -o /dev/null -w "%{http_code}" ${url} | grep -q "200\|302"; then
        print_status "✓ ${name} is responding"
    else
        print_warning "${name} is not responding at ${url}"
    fi
done

# Post-deployment tasks
print_status "Running post-deployment tasks..."

# Trigger initial data ingestion
print_status "Triggering initial data ingestion..."
docker-compose run --rm airflow-webserver airflow dags trigger crypto_data_ingestion
docker-compose run --rm airflow-webserver airflow dags trigger economic_data_ingestion

print_status "✓ Initial ingestion triggered"

# Generate deployment report
print_status "Generating deployment report..."
cat > "${BACKUP_DIR}/deployment_report.txt" << EOF
Deployment Report
=================
Environment: ${ENVIRONMENT}
Timestamp: ${TIMESTAMP}
Git Commit: $(git rev-parse HEAD)
Git Branch: $(git rev-parse --abbrev-ref HEAD)

Services Status:
$(docker-compose ps)

Backup Location: ${BACKUP_DIR}

Deployment completed successfully!
EOF

print_status "✓ Deployment report generated"

# Final message
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Access points:"
echo "  - Airflow UI: http://localhost:8080"
echo "  - MinIO Console: http://localhost:9001"
echo "  - Grafana: http://localhost:3000"
echo ""
echo "Backup location: ${BACKUP_DIR}"
echo ""
echo "To view logs: docker-compose logs -f [service-name]"
echo "To stop services: docker-compose down"
echo ""
