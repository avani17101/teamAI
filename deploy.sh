#!/bin/bash
# TeamAI VM Deployment Script
# Usage: ./deploy.sh

set -e

echo "========================================="
echo "  TeamAI Deployment Script"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}Warning: Running as root. Consider using a non-root user.${NC}"
fi

# Step 1: Check/Install Docker
echo -e "\n${GREEN}[1/5] Checking Docker installation...${NC}"
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing..."
    sudo apt-get update
    sudo apt-get install -y docker.io docker-compose
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
    echo -e "${YELLOW}Docker installed. You may need to log out and back in for group changes.${NC}"
else
    echo "Docker is already installed: $(docker --version)"
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Installing docker-compose..."
    sudo apt-get install -y docker-compose
fi
echo "Docker Compose: $(docker-compose --version)"

# Step 2: Check .env file
echo -e "\n${GREEN}[2/5] Checking environment configuration...${NC}"
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Creating .env from template..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${YELLOW}Please edit .env with your actual values:${NC}"
        echo "  nano .env"
        exit 1
    else
        echo -e "${RED}No .env.example found. Please create .env manually.${NC}"
        exit 1
    fi
else
    echo ".env file found"
fi

# Verify required variables
REQUIRED_VARS=("K2_API_KEY" "NOTION_API_KEY" "NOTION_DATABASE_ID")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if ! grep -q "^${var}=.\+" .env; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo -e "${YELLOW}Warning: Missing or empty required variables:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
fi

# Step 3: Create data directory
echo -e "\n${GREEN}[3/5] Setting up data directory...${NC}"
mkdir -p data
chmod 755 data
echo "Data directory ready"

# Step 4: Build and deploy
echo -e "\n${GREEN}[4/5] Building and deploying containers...${NC}"
docker-compose down 2>/dev/null || true
docker-compose build --no-cache
docker-compose up -d

# Step 5: Health check
echo -e "\n${GREEN}[5/5] Performing health check...${NC}"
echo "Waiting for service to start..."
sleep 5

MAX_RETRIES=12
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -sf http://localhost:8001/api/openclaw/status > /dev/null 2>&1; then
        echo -e "${GREEN}Health check passed!${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Waiting for service... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 5
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${YELLOW}Service may still be starting. Check logs:${NC}"
    echo "  docker-compose logs -f"
fi

# Summary
echo -e "\n========================================="
echo -e "${GREEN}  Deployment Complete!${NC}"
echo "========================================="
echo ""
echo "Service Status:"
docker-compose ps
echo ""
echo "Access TeamAI at: http://$(hostname -I | awk '{print $1}'):8001"
echo ""
echo "Useful commands:"
echo "  docker-compose logs -f     # View logs"
echo "  docker-compose restart     # Restart service"
echo "  docker-compose down        # Stop service"
echo "  docker-compose up -d       # Start service"
echo ""
