#!/bin/bash
# =============================================================================
# Dokploy Deployment Script
# Economic Data Analytics Platform
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.dokploy.yml"
ENV_FILE=".env"
PROJECT_NAME="economic-data-platform"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Economic Data Platform - Dokploy Deploy${NC}"
echo -e "${BLUE}========================================${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

if ! command_exists docker; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command_exists docker-compose; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose are available${NC}"

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo -e "${YELLOW}Please copy .env.dokploy to .env and configure it${NC}"
    echo -e "  cp .env.dokploy .env"
    echo -e "  nano .env"
    exit 1
fi

echo -e "${GREEN}✓ Environment file found${NC}"

# Create Dokploy network if not exists
echo -e "\n${YELLOW}Creating Dokploy network...${NC}"
docker network create dokploy-network 2>/dev/null || true
echo -e "${GREEN}✓ Network ready${NC}"

# Pull latest images
echo -e "\n${YELLOW}Pulling latest images...${NC}"
docker-compose -f $COMPOSE_FILE pull

# Build application image
echo -e "\n${YELLOW}Building application image...${NC}"
docker-compose -f $COMPOSE_FILE build --no-cache api

# Stop existing containers
echo -e "\n${YELLOW}Stopping existing containers...${NC}"
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME down --remove-orphans || true

# Start databases first
echo -e "\n${YELLOW}Starting databases...${NC}"
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d postgres redis clickhouse

# Wait for databases to be healthy
echo -e "\n${YELLOW}Waiting for databases to be healthy...${NC}"
sleep 10

# Check PostgreSQL
until docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME exec -T postgres pg_isready -U economic_user; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done
echo -e "${GREEN}✓ PostgreSQL is ready${NC}"

# Check Redis
until docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME exec -T redis redis-cli -a $REDIS_PASSWORD ping | grep -q PONG; do
    echo "Waiting for Redis..."
    sleep 2
done
echo -e "${GREEN}✓ Redis is ready${NC}"

# Run database migrations
echo -e "\n${YELLOW}Running database migrations...${NC}"
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME exec -T postgres psql -U economic_user -d economic_data -f /docker-entrypoint-initdb.d/01_bronze_schema.sql || true
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME exec -T postgres psql -U economic_user -d economic_data -f /docker-entrypoint-initdb.d/02_silver_schema.sql || true
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME exec -T postgres psql -U economic_user -d economic_data -f /docker-entrypoint-initdb.d/03_gold_crypto.sql || true
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME exec -T postgres psql -U economic_user -d economic_data -f /docker-entrypoint-initdb.d/04_gold_economic.sql || true
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME exec -T postgres psql -U economic_user -d economic_data -f /docker-entrypoint-initdb.d/05_gold_combined.sql || true
echo -e "${GREEN}✓ Database migrations completed${NC}"

# Start message queue
echo -e "\n${YELLOW}Starting message queue...${NC}"
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d zookeeper kafka

# Wait for Kafka
sleep 10

# Start MinIO
echo -e "\n${YELLOW}Starting object storage...${NC}"
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d minio minio-init

# Wait for MinIO
sleep 5

# Start monitoring
echo -e "\n${YELLOW}Starting monitoring...${NC}"
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d prometheus grafana

# Start API
echo -e "\n${YELLOW}Starting API server...${NC}"
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d api

# Wait for API to be healthy
echo -e "\n${YELLOW}Waiting for API to be healthy...${NC}"
sleep 10
until curl -sf http://localhost:8000/health > /dev/null; do
    echo "Waiting for API..."
    sleep 3
done
echo -e "${GREEN}✓ API is healthy${NC}"

# Show status
echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "\n${YELLOW}Services Status:${NC}"
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME ps

echo -e "\n${YELLOW}Access URLs (replace with your domain):${NC}"
echo -e "  API:      https://api.your-domain.com"
echo -e "  Docs:     https://api.your-domain.com/docs"
echo -e "  Grafana:  https://grafana.your-domain.com"
echo -e "  MinIO:    https://minio.your-domain.com"

echo -e "\n${YELLOW}Useful commands:${NC}"
echo -e "  View logs:    docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME logs -f"
echo -e "  Stop all:     docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME down"
echo -e "  Restart API:  docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME restart api"

echo -e "\n${GREEN}Done!${NC}"
