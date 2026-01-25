#!/bin/bash
# KnowledgeTree - SSL Certificate Setup with Let's Encrypt
# Sets up SSL certificates using Certbot

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}KnowledgeTree SSL Setup${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if domain is provided
if [ -z "$1" ]; then
    echo -e "${RED}Usage: $0 <domain.com>${NC}"
    echo "Example: $0 knowledgetree.com"
    exit 1
fi

DOMAIN=$1
EMAIL=${2:-"admin@$DOMAIN"}

echo "Domain: $DOMAIN"
echo "Email: $EMAIL"
echo ""

# Check if Certbot is installed
if ! command -v certbot &> /dev/null; then
    echo -e "${YELLOW}Installing Certbot...${NC}"
    sudo apt-get update
    sudo apt-get install -y certbot
fi

# Create required directories
echo -e "${YELLOW}Creating directories...${NC}"
sudo mkdir -p /home/jarek/projects/knowledgetree/docker/ssl
sudo mkdir -p /home/jarek/projects/knowledgetree/docker/certbot-www

# Get initial certificate
echo -e "${YELLOW}Obtaining SSL certificate...${NC}"
sudo certbot certonly --webroot \
    -w /home/jarek/projects/knowledgetree/docker/certbot-www \
    -d "$DOMAIN" \
    -d "www.$DOMAIN" \
    -d "api.$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email

# Setup certificate renewal
echo -e "${YELLOW}Setting up auto-renewal...${NC}"
echo "0 0,12 * * * root certbot renew --quiet --deploy-hook 'docker kill -s HUP nginx'" | sudo tee -a /etc/crontab

# Copy certificates to nginx directory
echo -e "${YELLOW}Copying certificates...${NC}"
sudo cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" /home/jarek/projects/knowledgetree/docker/ssl/
sudo cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" /home/jarek/projects/knowledgetree/docker/ssl/
sudo cp "/etc/letsencrypt/live/$DOMAIN/chain.pem" /home/jarek/projects/knowledgetree/docker/ssl/

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SSL Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Certificates installed for:"
echo "  - $DOMAIN"
echo "  - www.$DOMAIN"
echo "  - api.$DOMAIN"
echo ""
echo "Certificates location:"
echo "  /etc/letsencrypt/live/$DOMAIN/"
echo ""
echo "To test certificate renewal:"
echo "  sudo certbot renew --dry-run"
