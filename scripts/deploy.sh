#!/bin/bash
# KnowledgeTree - Production Deployment Script
# Deploys the application to a VPS using Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.production.yml"
ENV_FILE="$PROJECT_DIR/.env.production"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}KnowledgeTree Production Deployment${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if .env.production exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: .env.production not found!${NC}"
    echo "Please create .env.production with required environment variables."
    echo ""
    echo "Required variables:"
    echo "  DB_PASSWORD=your_secure_password"
    echo "  SECRET_KEY=your_secret_key"
    echo "  ANTHROPIC_API_KEY=your_anthropic_key"
    echo "  FIRECRAWL_API_KEY=your_firecrawl_key (optional)"
    echo "  SERPER_API_KEY=your_serper_key (optional)"
    echo "  STRIPE_API_KEY=your_stripe_key (optional)"
    echo "  FRONTEND_URL=https://yourdomain.com"
    echo "  API_URL=https://api.yourdomain.com"
    exit 1
fi

# Load environment variables
export $(grep -v '^#' "$ENV_FILE" | xargs)

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed!${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed!${NC}"
    exit 1
fi

# Pull latest images
echo -e "${YELLOW}Pulling latest Docker images...${NC}"
docker-compose -f "$COMPOSE_FILE" pull

# Build images
echo -e "${YELLOW}Building Docker images...${NC}"
docker-compose -f "$COMPOSE_FILE" build --no-cache

# Stop existing containers
echo -e "${YELLOW}Stopping existing containers...${NC}"
docker-compose -f "$COMPOSE_FILE" down

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
docker-compose -f "$COMPOSE_FILE" run --rm backend alembic upgrade head

# Start services
echo -e "${YELLOW}Starting services...${NC}"
docker-compose -f "$COMPOSE_FILE" up -d

# Wait for services to be healthy
echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
sleep 20

# Check service status
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Service Status${NC}"
echo -e "${GREEN}========================================${NC}"
docker-compose -f "$COMPOSE_FILE" ps

# Run health check
echo ""
echo -e "${YELLOW}Running health check...${NC}"
HEALTH_URL="http://localhost:8765/health"
if curl -f -s "$HEALTH_URL" > /dev/null; then
    echo -e "${GREEN}✓ Backend is healthy${NC}"
else
    echo -e "${RED}✗ Backend health check failed${NC}"
    docker-compose -f "$COMPOSE_FILE" logs backend --tail 50
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Services running:"
echo "  - Frontend: http://localhost:3555"
echo "  - Backend API: http://localhost:8765"
echo "  - API Docs: http://localhost:8765/docs"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose.production.yml logs -f"
echo ""
echo "To stop services:"
echo "  docker-compose -f docker-compose.production.yml down"
