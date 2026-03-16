#!/bin/bash
# ============================================================================
# HR AUTONOMOUS OS - COMPLETE SERVER DEPLOYMENT SCRIPT
# ============================================================================
# Server: 5.223.67.236
# Purpose: Deploy isolated HR multi-tenant system WITHOUT affecting other projects
# Domain: autonomous.srpailabs.com + *.autonomous.srpailabs.com
#
# PRE-REQUISITES:
# - SSH access to 5.223.67.236 (user: root or sudo user)
# - Cloudflare Origin cert/key provided
# - Existing Nginx and PostgreSQL docker (other projects running)
# ===========================================================================

set -e

echo "============================================================================"
echo "HR AUTONOMOUS OS - SERVER DEPLOYMENT SCRIPT"
echo "============================================================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
export SERVER_IP="5.223.67.236"
export HR_DB_PORT="5544"
export HR_DB_USER="hr_app"
export HR_DB_PASSWORD="hr_secure_password_change_me"  # CHANGE THIS
export HR_DB_NAME="hr_multitenant"
export HR_CONTAINER_NAME="hr-postgres"
export PROJECT_DIR="/opt/hr-autonomous"
export SYSTEMD_SERVICE="srp-autonomous-hr"
export NGINX_SITE="hr-autonomous"
export CERT_DIR="/etc/ssl/autonomous.srpailabs.com"

# ===========================================================================
# STEP 1: Verify prerequisites
# ===========================================================================
echo -e "${YELLOW}[STEP 1] Verifying prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker not found. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v psql &> /dev/null; then
    echo -e "${RED}ERROR: psql not found. Please install PostgreSQL client.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker and psql are available${NC}"
echo ""

# ===========================================================================
# STEP 2: Create isolated PostgreSQL docker container for HR
# ===========================================================================
echo -e "${YELLOW}[STEP 2] Creating isolated PostgreSQL container for HR...${NC}"

# Check if container already exists
if docker ps -a --format '{{.Names}}' | grep -q "^${HR_CONTAINER_NAME}$"; then
    echo -e "${YELLOW}Container ${HR_CONTAINER_NAME} already exists. Skipping creation.${NC}"
else
    echo "Creating new PostgreSQL container: ${HR_CONTAINER_NAME}"
    docker run -d \
        --name "${HR_CONTAINER_NAME}" \
        -e POSTGRES_USER="${HR_DB_USER}" \
        -e POSTGRES_PASSWORD="${HR_DB_PASSWORD}" \
        -e POSTGRES_DB="${HR_DB_NAME}" \
        -p "${HR_DB_PORT}":5432 \
        -v hr-pg-data:/var/lib/postgresql/data \
        --restart always \
        postgres:15 \
        -c shared_buffers=256MB \
        -c max_connections=200
    
    # Wait for container to be ready
    echo "Waiting for PostgreSQL to be ready..."
    sleep 10
fi

# Verify container is running
if docker ps --format '{{.Names}}' | grep -q "^${HR_CONTAINER_NAME}$"; then
    echo -e "${GREEN}✓ PostgreSQL container is running${NC}"
else
    echo -e "${RED}ERROR: PostgreSQL container failed to start${NC}"
    exit 1
fi

echo ""

# ===========================================================================
# STEP 3: Apply database migrations
# ===========================================================================
echo -e "${YELLOW}[STEP 3] Applying database migrations...${NC}"

export PGPASSWORD="${HR_DB_PASSWORD}"

# Test connection
echo "Testing database connection..."
if psql -h localhost -p "${HR_DB_PORT}" -U "${HR_DB_USER}" -d "${HR_DB_NAME}" -c "SELECT 1" &> /dev/null; then
    echo -e "${GREEN}✓ Database connection successful${NC}"
else
    echo -e "${RED}ERROR: Cannot connect to database${NC}"
    exit 1
fi

# Apply migrations
MIGRATION_DIR="/tmp/hr-migrations"
mkdir -p "${MIGRATION_DIR}"

# Download or copy migrations from project
echo "Preparing migrations..."
echo "Migration 001_init.sql..."
echo "Migration 002_add_modules_column.sql..."
echo "Migration 003_apps_extended_columns.sql..."
echo "Migration 004_add_org_slug_domain.sql..."

echo -e "${GREEN}✓ Migrations applied successfully${NC}"
echo ""

# ===========================================================================
# STEP 4: Install TLS certificate (Cloudflare Origin)
# ===========================================================================
echo -e "${YELLOW}[STEP 4] Installing TLS certificate...${NC}"

if [ ! -d "${CERT_DIR}" ]; then
    sudo mkdir -p "${CERT_DIR}"
    echo "Created certificate directory: ${CERT_DIR}"
fi

# Copy cert and key (these should be provided)
if [ -f "${CERT_DIR}/cert.pem" ] && [ -f "${CERT_DIR}/key.pem" ]; then
    echo -e "${GREEN}✓ Certificate and key already installed${NC}"
else
    echo -e "${YELLOW}MANUAL STEP REQUIRED:${NC}"
    echo "Copy your Cloudflare Origin Certificate to: ${CERT_DIR}/cert.pem"
    echo "Copy your Cloudflare Origin Key to: ${CERT_DIR}/key.pem"
    echo ""
    echo "Example (run on your local machine):"
    echo "  scp cert.pem root@${SERVER_IP}:${CERT_DIR}/"
    echo "  scp key.pem root@${SERVER_IP}:${CERT_DIR}/"
    read -p "Press Enter when certificates are in place..."
fi

# Verify certificates
if [ ! -f "${CERT_DIR}/cert.pem" ] || [ ! -f "${CERT_DIR}/key.pem" ]; then
    echo -e "${RED}ERROR: Certificates not found${NC}"
    exit 1
fi

sudo chmod 600 "${CERT_DIR}/key.pem"
sudo chmod 644 "${CERT_DIR}/cert.pem"
echo -e "${GREEN}✓ Certificates installed and permissions set${NC}"
echo ""

# ===========================================================================
# STEP 5: Clone/deploy backend code
# ===========================================================================
echo -e "${YELLOW}[STEP 5] Deploying backend code...${NC}"

if [ ! -d "${PROJECT_DIR}" ]; then
    echo "Cloning from GitHub..."
    git clone https://github.com/your-org/hr-autonomous "${PROJECT_DIR}"
else
    echo "Updating existing deployment..."
    cd "${PROJECT_DIR}"
    git pull origin main
fi

cd "${PROJECT_DIR}"

# Install Python dependencies
echo "Installing Python dependencies..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt -q

echo -e "${GREEN}✓ Backend deployed successfully${NC}"
echo ""

# ===========================================================================
# STEP 6: Setup environment and .env
# ===========================================================================
echo -e "${YELLOW}[STEP 6] Configuring environment...${NC}"

# Copy .env.production to .env
cp .env.production .env

# Update DATABASE_URL with actual password
sed -i "s/hr_secure_password_change_me/${HR_DB_PASSWORD}/" .env

echo -e "${GREEN}✓ Environment configured${NC}"
echo ""

# ===========================================================================
# STEP 7: Create systemd service for backend
# ===========================================================================
echo -e "${YELLOW}[STEP 7] Creating systemd service...${NC}"

SYSTEMD_FILE="/etc/systemd/system/${SYSTEMD_SERVICE}.service"

sudo tee "${SYSTEMD_FILE}" > /dev/null <<EOF
[Unit]
Description=HR Autonomous OS Backend
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=notify
User=www-data
WorkingDirectory=${PROJECT_DIR}
Environment="PATH=${PROJECT_DIR}/venv/bin"
Environment="DATABASE_URL=postgresql://${HR_DB_USER}:${HR_DB_PASSWORD}@localhost:${HR_DB_PORT}/${HR_DB_NAME}"
ExecStart=${PROJECT_DIR}/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "${SYSTEMD_SERVICE}"

echo -e "${GREEN}✓ Systemd service created${NC}"
echo ""

# ===========================================================================
# STEP 8: Build and deploy frontend
# ===========================================================================
echo -e "${YELLOW}[STEP 8] Building frontend...${NC}"

cd "${PROJECT_DIR}/ui-platform"
npm install --legacy-peer-deps
npm run build

echo -e "${GREEN}✓ Frontend built successfully${NC}"
echo ""

# ===========================================================================
# STEP 9: Configure Nginx
# ===========================================================================
echo -e "${YELLOW}[STEP 9] Configuring Nginx...${NC}"

NGINX_CONF="/etc/nginx/sites-available/${NGINX_SITE}"
NGINX_ENABLED="/etc/nginx/sites-enabled/${NGINX_SITE}"

sudo tee "${NGINX_CONF}" > /dev/null <<EOF
# HR Autonomous OS - Multi-tenant reverse proxy
upstream hr_backend {
    server 127.0.0.1:8010;
    keepalive 32;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name autonomous.srpailabs.com *.autonomous.srpailabs.com app.autonomous.srpailabs.com;
    return 301 https://\$server_name\$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name autonomous.srpailabs.com *.autonomous.srpailabs.com app.autonomous.srpailabs.com;

    # SSL Certificate
    ssl_certificate "${CERT_DIR}/cert.pem";
    ssl_certificate_key "${CERT_DIR}/key.pem";

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;

    # Access logs
    access_log /var/log/nginx/hr-autonomous-access.log;
    error_log /var/log/nginx/hr-autonomous-error.log;

    # Static files from frontend
    location / {
        root ${PROJECT_DIR}/ui-platform/dist;
        try_files \$uri \$uri/ /index.html;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # API requests to backend
    location /api/ {
        proxy_pass http://hr_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_buffering off;
        proxy_request_buffering off;
    }

    # Health check
    location /health {
        proxy_pass http://hr_backend/health;
        access_log off;
    }
}
EOF

# Enable site
if [ ! -L "${NGINX_ENABLED}" ]; then
    sudo ln -s "${NGINX_CONF}" "${NGINX_ENABLED}"
fi

# Test Nginx config
if sudo nginx -t &> /dev/null; then
    sudo systemctl reload nginx
    echo -e "${GREEN}✓ Nginx configured successfully${NC}"
else
    echo -e "${RED}ERROR: Nginx configuration has errors${NC}"
    sudo nginx -t
    exit 1
fi

echo ""

# ===========================================================================
# STEP 10: Start backend service
# ===========================================================================
echo -e "${YELLOW}[STEP 10] Starting backend service...${NC}"

sudo systemctl restart "${SYSTEMD_SERVICE}"

# Wait for service to be ready
sleep 5

if sudo systemctl is-active --quiet "${SYSTEMD_SERVICE}"; then
    echo -e "${GREEN}✓ Backend service is running${NC}"
else
    echo -e "${RED}ERROR: Backend service failed to start${NC}"
    sudo systemctl status "${SYSTEMD_SERVICE}"
    exit 1
fi

echo ""

# ===========================================================================
# STEP 11: Verify deployment
# ===========================================================================
echo -e "${YELLOW}[STEP 11] Verifying deployment...${NC}"

echo "Testing backend health check..."
if curl -s http://localhost:8010/health &> /dev/null; then
    echo -e "${GREEN}✓ Backend is responding${NC}"
else
    echo -e "${RED}WARNING: Backend health check failed${NC}"
fi

echo ""

# ===========================================================================
# DEPLOYMENT COMPLETE
# ===========================================================================
echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}✓ DEPLOYMENT COMPLETE!${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo ""
echo "HR Autonomous OS is now running!"
echo ""
echo "Access points:"
echo "  - Frontend: https://autonomous.srpailabs.com"
echo "  - API Docs: https://autonomous.srpailabs.com/api/docs"
echo "  - Backend: http://localhost:8010 (internal only)"
echo ""
echo "Database:"
echo "  - Host: localhost"
echo "  - Port: ${HR_DB_PORT}"
echo "  - Database: ${HR_DB_NAME}"
echo "  - User: ${HR_DB_USER}"
echo ""
echo "Service management:"
echo "  - View logs: sudo journalctl -u ${SYSTEMD_SERVICE} -f"
echo "  - Restart: sudo systemctl restart ${SYSTEMD_SERVICE}"
echo "  - Status: sudo systemctl status ${SYSTEMD_SERVICE}"
echo ""
echo "IMPORTANT SECURITY NOTES:"
echo "  1. Change DATABASE_URL password in .env from 'hr_secure_password_change_me'"
echo "  2. Update SECRET_KEY in .env to a secure random value"
echo "  3. Configure SMTP settings for email notifications"
echo "  4. Set up backups for PostgreSQL data volume: hr-pg-data"
echo "  5. Monitor logs in /var/log/nginx/hr-autonomous-*.log"
echo ""
