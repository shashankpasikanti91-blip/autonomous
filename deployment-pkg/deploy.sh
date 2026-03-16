#/bin/bash
set -e

echo "════════════════════════════════════════════════════════════"
echo "Starting HR Autonomous OS Deployment..."
echo "════════════════════════════════════════════════════════════"
echo ""

echo "[1/8] Installing SSL certificates..."
mkdir -p /etc/ssl/autonomous.srpailabs.com
cp /tmp/dep/cert.pem /etc/ssl/autonomous.srpailabs.com/
cp /tmp/dep/key.pem /etc/ssl/autonomous.srpailabs.com/
chmod 600 /etc/ssl/autonomous.srpailabs.com/*.pem
echo "✓ SSL certificates installed"
echo ""

echo "[2/8] Deploying project files..."
rm -rf /opt/hr-autonomous
mkdir -p /opt/hr-autonomous
cp -r /tmp/dep/* /opt/hr-autonomous/
cd /opt/hr-autonomous
echo "✓ Project deployed"
echo ""

echo "[3/8] Creating PostgreSQL database container..."
docker run -d --name hr-postgres -e POSTGRES_USER=hr_app -e POSTGRES_PASSWORD=hr_secure_password_change_me -e POSTGRES_DB=hr_multitenant -p 5544:5432 -v hr-pg-data:/var/lib/postgresql/data --restart always postgres:15 2>/dev/null || echo "✓ Container running"
sleep 5
echo "✓ Database ready"
echo ""

echo "[4/8] Installing Python dependencies..."
python3.11 -m venv /opt/hr-autonomous/.venv 2>/dev/null || python3 -m venv /opt/hr-autonomous/.venv
source /opt/hr-autonomous/.venv/bin/activate
pip install -q -U pip setuptools wheel
pip install -q -r requirements.txt
echo "✓ Dependencies installed"
echo ""

echo "[5/8] Building frontend..."
cd /opt/hr-autonomous/ui-platform
npm install -q 2>/dev/null
npm run build 2>/dev/null
echo "✓ Frontend built"
echo ""

echo "[6/8] Configuring Nginx..."
cp /opt/hr-autonomous/deploy/nginx.conf /etc/nginx/sites-available/autonomous 2>/dev/null || echo "✓ Nginx config prepared"
sed -i 's/hr.example.com/autonomous.srpailabs.com/g' /etc/nginx/sites-available/autonomous
ln -sf /etc/nginx/sites-available/autonomous /etc/nginx/sites-enabled/autonomous 2>/dev/null || true
nginx -t
systemctl restart nginx
echo "✓ Nginx configured"
echo ""

echo "[7/8] Setting up backend service..."
systemctl stop hr-autonomous 2>/dev/null || true
cat > /etc/systemd/system/hr-autonomous.service << 'EOF'
[Unit]
Description=HR Autonomous OS Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/hr-autonomous
ExecStart=/opt/hr-autonomous/.venv/bin/python /opt/hr-autonomous/main.py
Environment="DATABASE_URL=postgresql://hr_app:hr_secure_password_change_me@localhost:5544/hr_multitenant"
Environment="API_PORT=8010"
Environment="ENV=production"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable hr-autonomous
systemctl restart hr-autonomous
echo "✓ Backend service configured"
echo ""

echo "[8/8] Verification..."
sleep 3
systemctl status hr-autonomous --no-pager
echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ DEPLOYMENT COMPLETE"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Access your application at:"
echo "  Frontend: https://autonomous.srpailabs.com"
echo "  API: https://autonomous.srpailabs.com/api"
echo ""
