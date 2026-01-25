#!/bin/bash
# KnowledgeTree - VPS Initial Setup Script
# Prepares a fresh VPS for KnowledgeTree deployment

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}KnowledgeTree VPS Setup${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

# Update system
echo -e "${YELLOW}Updating system packages...${NC}"
apt-get update
apt-get upgrade -y

# Install Docker
echo -e "${YELLOW}Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker $SUDO_USER
    rm get-docker.sh
else
    echo "Docker already installed"
fi

# Install Docker Compose
echo -e "${YELLOW}Installing Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo "Docker Compose already installed"
fi

# Install Nginx
echo -e "${YELLOW}Installing Nginx...${NC}"
apt-get install -y nginx

# Install Certbot
echo -e "${YELLOW}Installing Certbot...${NC}"
apt-get install -y certbot python3-certbot-nginx

# Install fail2ban
echo -e "${YELLOW}Installing fail2ban...${NC}"
apt-get install -y fail2ban

# Setup firewall
echo -e "${YELLOW}Configuring firewall...${NC}"
apt-get install -y ufw
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Configure fail2ban
echo -e "${YELLOW}Configuring fail2ban...${NC}"
cat > /etc/fail2ban/jail.local <<'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
EOF

systemctl enable fail2ban
systemctl start fail2ban

# Create swap file
echo -e "${YELLOW}Creating swap file...${NC}"
if [ ! -f /swapfile ]; then
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
else
    echo "Swap file already exists"
fi

# Optimize sysctl
echo -e "${YELLOW}Optimizing system parameters...${NC}"
cat >> /etc/sysctl.conf <<'EOF'

# KnowledgeTree optimizations
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.ip_local_port_range = 1024 65535
fs.file-max = 2097152
vm.swappiness = 10
EOF

sysctl -p

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}VPS Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Copy your project to the VPS"
echo "  2. Create .env.production file"
echo "  3. Run: ./scripts/setup-ssl.sh yourdomain.com"
echo "  4. Run: ./scripts/deploy.sh"
echo ""
echo "VPS is ready for KnowledgeTree deployment!"
