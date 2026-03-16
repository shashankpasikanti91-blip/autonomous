# Hetzner Deployment Guide — SRP Autonomous OS

## Server Details
- **IP**: 5.223.67.236
- **Password**: 856Reey@nsh (stored securely)
- **SSH User**: `root` or `ubuntu` (confirm which is available)

---

## Step 1: Connect via SSH

```bash
# Try root first (most common on Hetzner)
ssh root@5.223.67.236

# If that doesn't work, try ubuntu
ssh ubuntu@5.223.67.236

# Password: 856Reey@nsh
```

---

## Step 2: Create Database for SRP Autonomous OS

On the server, **DO NOT touch other project databases**. Create a dedicated database:

```bash
# Connect to PostgreSQL as admin
sudo -u postgres psql

# Create new database ONLY for SRP Autonomous (do not modify other DBs)
CREATE DATABASE srp_autonomous OWNER postgres;
\q
```

Get the connection string:
```bash
DATABASE_URL=postgresql://postgres:<postgres_password>@localhost:5432/srp_autonomous
```

---

## Step 3: Clone and Set Up Project

```bash
sudo mkdir -p /srv/autonomous
sudo chown ubuntu:ubuntu /srv/autonomous

cd /srv/autonomous
git clone <your-repo-url> .

# Create venv
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

---

## Step 4: Configure Production `.env`

```bash
cat > /srv/autonomous/.env << 'EOF'
# ============================================================================
# Production Environment — Hetzner Deployment
# ============================================================================
ENV=production
DEBUG=false
LOG_LEVEL=INFO

# ============================================================================
# API Configuration
# ============================================================================
API_HOST=127.0.0.1
API_PORT=8010
API_RELOAD=false

# ============================================================================
# Database — Only SRP Autonomous (do NOT touch other project DBs)
# ============================================================================
DATABASE_URL=postgresql://postgres:<YOUR_POSTGRES_PASSWORD>@localhost:5432/srp_autonomous

# ============================================================================
# CORS & Security
# ============================================================================
ALLOWED_ORIGINS=https://autonomous.srpailabs.com,https://*.autonomous.srpailabs.com
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
TRUST_PROXY_HEADERS=true

# ============================================================================
# Platform Identity
# ============================================================================
PLATFORM_NAME=SRP Autonomous OS
PLATFORM_DOMAIN=autonomous.srpailabs.com

# ============================================================================
# Integrations (Stub Mode — configure with real credentials later)
# ============================================================================
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=noreply@example.com
SMTP_PASSWORD=your-app-password

WHATSAPP_API_TOKEN=test-token
WHATSAPP_BUSINESS_ACCOUNT_ID=123456789

CALENDAR_PROVIDER=google
CALENDAR_CLIENT_ID=your-client-id.apps.googleusercontent.com
CALENDAR_CLIENT_SECRET=your-client-secret

CRM_PROVIDER=hubspot
HUBSPOT_API_KEY=your-hubspot-key

N8N_URL=https://n8n.example.com
N8N_API_KEY=your-n8n-key

PYDANTIC_AI_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=sk-your-anthropic-key

# ============================================================================
# Payroll Configuration
# ============================================================================
PAYROLL_TAX_RATE=0.15
HEALTH_INSURANCE=200.0
PENSION_RATE=0.05

# ============================================================================
# Invoice Configuration
# ============================================================================
INVOICE_BUSINESS_NAME=SRP Autonomous OS
INVOICE_TAX_ID=12-3456789
INVOICE_PREFIX=INV
INVOICE_PAYMENT_TERMS_DAYS=30
EOF
```

---

## Step 5: Deploy Systemd Service

```bash
sudo cp /srv/autonomous/deploy/srp-autonomous.service /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable srp-autonomous
sudo systemctl start srp-autonomous
sudo systemctl status srp-autonomous

# Tail logs
sudo journalctl -u srp-autonomous -f
```

---

## Step 6: Deploy Nginx Reverse Proxy

```bash
sudo cp /srv/autonomous/deploy/nginx.conf /etc/nginx/sites-available/autonomous
sudo ln -s /etc/nginx/sites-available/autonomous /etc/nginx/sites-enabled/autonomous

sudo nginx -t
sudo systemctl reload nginx
```

---

## Step 7: SSL Certificate (Cloudflare)

1. Create Cloudflare Origin Certificate (valid 15 years):
   - Domain: `autonomous.srpailabs.com`
   - Wildcard: `*.autonomous.srpailabs.com`

2. Place certificates on server:
```bash
sudo mkdir -p /etc/ssl/autonomous.srpailabs.com
sudo nano /etc/ssl/autonomous.srpailabs.com/cert.pem          # Paste cert
sudo nano /etc/ssl/autonomous.srpailabs.com/key.pem           # Paste key
sudo chmod 600 /etc/ssl/autonomous.srpailabs.com/key.pem
```

3. In Cloudflare: Set SSL mode to **"Full (Strict)"**

---

## Step 8: DNS Configuration

In Cloudflare DNS:
- `A autonomous.srpailabs.com → 5.223.67.236` (Proxied - orange cloud)
- `A *.autonomous.srpailabs.com → 5.223.67.236` (Proxied - orange cloud)

---

## Step 9: Verify Deployment

```bash
# Check backend health (local)
curl -s http://127.0.0.1:8010/health | jq .

# Check via Nginx (local)
curl -s http://localhost/health | jq .

# Check public endpoint (after DNS propagation)
curl -s https://autonomous.srpailabs.com/health | jq .
```

---

## Step 10: Run E2E Tests Against Production

```bash
# On your local machine
BASE_URL=https://autonomous.srpailabs.com pytest tests/test_e2e.py -v
```

---

## Monitoring & Maintenance

```bash
# View logs
sudo journalctl -u srp-autonomous -n 100 -f

# Restart service
sudo systemctl restart srp-autonomous

# Check database
psql -U postgres -d srp_autonomous -c "SELECT * FROM core_users;"

# Backup database
pg_dump srp_autonomous > backup-$(date +%Y%m%d).sql
```

---

## Troubleshooting

| Issue | Fix |
|---|---|
| 502 Bad Gateway | Check `systemctl status srp-autonomous` |
| Database connection error | Verify `DATABASE_URL` in `.env` and Postgres running |
| CORS errors | Ensure `ALLOWED_ORIGINS` in `.env` matches domain |
| SSL certificate issues | Verify Cloudflare Origin Cert in `/etc/ssl/autonomous.srpailabs.com/` |
| Port already in use | Change `API_PORT` to unused port (default 8010) |

---

## Important: DO NOT MODIFY OTHER DATABASES

⚠️ **The server hosts other projects.** This deployment:
- Creates **new** database: `srp_autonomous`
- Listens on port **8010** (isolated from other projects)
- Binds to **127.0.0.1** (only accessible via Nginx)
- **Never touches** other project DBs, files, or services

---

## Quick Commands Summary

```bash
# SSH to server
ssh root@5.223.67.236

# Start/stop backend
sudo systemctl start srp-autonomous
sudo systemctl stop srp-autonomous
sudo systemctl restart srp-autonomous

# View logs
sudo journalctl -u srp-autonomous -f

# Check status
sudo systemctl status srp-autonomous

# Restart Nginx
sudo systemctl reload nginx
```

---

**After deployment**, the platform will be live at:
- **Main**: https://autonomous.srpailabs.com
- **Tenant 1**: https://acme.autonomous.srpailabs.com
- **Tenant 2**: https://beta.autonomous.srpailabs.com
- ... (unlimited subdomains)
