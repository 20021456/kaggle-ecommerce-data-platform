#!/bin/bash
# =============================================================================
# Quick Deploy Script for Minimal VPS (2 vCPU, 4GB RAM)
# =============================================================================

set -e

echo "=========================================="
echo "  Economic Data Platform - Minimal Deploy"
echo "  Optimized for: 2 vCPU, 4GB RAM"
echo "=========================================="

# Check .env
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found!"
    echo "Run: cp .env.example .env && nano .env"
    exit 1
fi

# Create network
echo "Creating network..."
docker network create app-network 2>/dev/null || true

# Pull images
echo "Pulling images..."
docker-compose pull postgres redis

# Build API
echo "Building API image..."
docker-compose build api

# Start services
echo "Starting services..."
docker-compose up -d postgres redis

# Wait for DB
echo "Waiting for PostgreSQL..."
sleep 15
until docker-compose exec -T postgres pg_isready -U economic_user; do
    sleep 3
done

# Start API
echo "Starting API..."
docker-compose up -d api

# Wait for API
echo "Waiting for API..."
sleep 10

# Check health
echo ""
echo "=========================================="
if curl -sf http://localhost:8000/health > /dev/null; then
    echo "✓ Deployment successful!"
    echo ""
    echo "Services running:"
    docker-compose ps
    echo ""
    echo "Memory usage:"
    docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}"
    echo ""
    echo "Access:"
    echo "  API: http://localhost:8000"
    echo "  Docs: http://localhost:8000/docs"
else
    echo "✗ API health check failed"
    echo "Check logs: docker-compose logs api"
fi
echo "=========================================="
