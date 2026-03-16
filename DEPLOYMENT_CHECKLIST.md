# HR AUTONOMOUS OS - DEPLOYMENT CHECKLIST

## Pre-Deployment

- [ ] Review all environment variables in `.env.production`
- [ ] Obtain Cloudflare Origin Certificate (cert.pem) and Key (key.pem)
- [ ] Verify server access (SSH to 5.223.67.236)
- [ ] Confirm DNS records point to server IP (app.autonomous.srpailabs.com + *.autonomous.srpailabs.com)
- [ ] Backup any existing databases on the server
- [ ] Review GitHub changes and README updates

## Deployment (Automated)

### Option A: One-Command Deployment (Recommended)

```bash
# From your local machine
scp deploy/deploy.sh root@5.223.67.236:/opt/hr-deploy.sh
ssh root@5.223.67.236
chmod +x /opt/hr-deploy.sh
bash /opt/hr-deploy.sh
```

**What this does:**
- Creates isolated PostgreSQL docker container (port 5544)
- Applies all 4 database migrations
- Installs Cloudflare Origin certificate
- Deploys backend with all dependencies
- Builds React frontend
- Configures Nginx with SSL
- Starts all services
- Verifies deployment

### Option B: Step-by-Step Manual Deployment

Follow each section in README.md under "OR: Step-by-step manual deployment"

## Post-Deployment Verification

### 1. Services Running

```bash
# Check backend service
sudo systemctl status srp-autonomous-hr

# Check PostgreSQL container
docker ps | grep hr-postgres

# Check Nginx
sudo systemctl status nginx
```

Expected output:
```
✓ srp-autonomous-hr is running
✓ hr-postgres is up
✓ nginx is running and configured
```

### 2. API Connectivity

```bash
# Test health endpoint (local)
curl http://localhost:8010/health

# Test health endpoint (external)
curl https://autonomous.srpailabs.com/health
```

Expected response:
```json
{
  "status": "ok",
  "platform": "HR Autonomous OS",
  "version": "1.0.0"
}
```

### 3. Database Connectivity

```bash
# Test database connection
psql -h localhost -p 5544 -U hr_app -d hr_multitenant -c "SELECT COUNT(*) FROM organizations;"
```

Expected output:
```
count
-------
    0
(1 row)
```

### 4. Run E2E Tests

```bash
# Set API URL (use deployed server)
export API_URL=https://autonomous.srpailabs.com

# Run e2e test suite
bash deploy/e2e-test.sh ${API_URL}
```

Expected output: All 10 test sections should show ✓

## Post-Deployment Configuration

### 1. Update Database Password

In `.env` on server:

```bash
# IMPORTANT: Change from default
sed -i 's/hr_secure_password_change_me/YOUR_SECURE_PASSWORD_HERE/' .env
sudo systemctl restart srp-autonomous-hr
```

### 2. Set Up Secure Secret Key

```bash
# Generate secure key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env on server
SECRET_KEY=<generated-key-above>
```

### 3. Configure Email (Optional)

Configure SMTP in `.env`:

```env
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@autonomous.srpailabs.com
```

### 4. Set Up Database Backups

```bash
# Create daily backup script
sudo tee /usr/local/bin/backup-hr-postgres.sh > /dev/null <<'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/hr-autonomous"
mkdir -p ${BACKUP_DIR}
docker exec hr-postgres pg_dump -U hr_app hr_multitenant | gzip > ${BACKUP_DIR}/hr-backup-$(date +%Y%m%d-%H%M%S).sql.gz
# Keep last 7 days
find ${BACKUP_DIR} -name "*.sql.gz" -mtime +7 -delete
EOF

sudo chmod +x /usr/local/bin/backup-hr-postgres.sh

# Add to crontab (daily at 3 AM)
sudo sh -c 'echo "0 3 * * * /usr/local/bin/backup-hr-postgres.sh" | crontab'
```

## Creating Test Tenant

After deployment, create a test organization:

```bash
curl -X POST https://autonomous.srpailabs.com/api/tenants \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: admin" \
  -d '{
    "owner_email": "admin@test-hr.com",
    "name": "Test HR Organization",
    "slug": "test-hr-'$(date +%s)'",
    "industry": "payroll_finance",
    "custom_domain": null
  }'
```

## Monitoring

### View Service Logs

```bash
# Backend logs (last 100 lines, follow mode)
sudo journalctl -u srp-autonomous-hr -n 100 -f

# Nginx access logs
tail -f /var/log/nginx/hr-autonomous-access.log

# Nginx error logs
tail -f /var/log/nginx/hr-autonomous-error.log

# PostgreSQL container logs
docker logs -f hr-postgres
```

### Common Issues and Fixes

| Issue | Command |
|---|---|
| Backend not starting | `sudo journalctl -u srp-autonomous-hr -n 50` |
| Database connection failed | `docker logs hr-postgres` |
| Nginx 502 bad gateway | `curl http://127.0.0.1:8010/health` |
| Certificate not loading | `sudo ls -la /etc/ssl/autonomous.srpailabs.com/` |
| Multi-tenant routes not working | Check `PLATFORM_DOMAIN` in `.env` matches Host header |

### Health Check Script

```bash
#!/bin/bash
echo "=== HR AUTONOMOUS OS - HEALTH CHECK ==="
echo ""

# Backend
echo "Backend:"
if curl -s http://localhost:8010/health &> /dev/null; then
    echo "  ✓ Responding"
else
    echo "  ✗ Not responding"
fi

# Database
echo "Database:"
if docker ps | grep -q hr-postgres; then
    echo "  ✓ Running"
else
    echo "  ✗ Not running"
fi

# Nginx
echo "Nginx:"
if sudo systemctl is-active --quiet nginx; then
    echo "  ✓ Running"
else
    echo "  ✗ Not running"
fi

# SSL Certificate
echo "SSL Certificate:"
if [ -f /etc/ssl/autonomous.srpailabs.com/cert.pem ]; then
    echo "  ✓ Installed"
else
    echo "  ✗ Missing"
fi
```

## Rollback (If Needed)

If deployment fails and you need to rollback:

```bash
# Stop services
sudo systemctl stop srp-autonomous-hr
sudo systemctl stop nginx

# Restore from backup
docker stop hr-postgres
docker rm hr-postgres
# Create new container with previous data

# Restart
sudo systemctl start srp-autonomous-hr
sudo systemctl start nginx
```

## Updating Deployment

To update the code after initial deployment:

```bash
cd /opt/hr-autonomous
git pull origin main
.venv/bin/pip install -r requirements.txt
cd ui-platform
npm install --legacy-peer-deps
npm run build
sudo systemctl restart srp-autonomous-hr
sudo systemctl reload nginx
```

## Security Recommendations

1. **Change default passwords** — Update DATABASE_URL password in `.env`
2. **Generate SECRET_KEY** — Use cryptographically secure key
3. **Enable HTTPS only** — Configure HSTS headers in Nginx
4. **Restrict API access** — Add rate limiting, API key authentication if needed
5. **Monitor logs** — Set up log aggregation (ELK, Datadog, etc.)
6. **Database backups** — Automated daily backups with 7-day retention
7. **Keep dependencies updated** — Regular `pip install --upgrade` and `npm update`
8. **Restrict SSH access** — Use key-based auth only, restrict IPs if possible

## Success Criteria

✅ Deployment is complete when:

1. Backend service is running and responding to `/health`
2. PostgreSQL container is running with hr_multitenant database
3. Frontend loads at https://autonomous.srpailabs.com
4. Multi-tenant routing works (test with https://test.autonomous.srpailabs.com)
5. E2E test suite passes all 10 sections
6. No errors in service logs
7. SSL certificate is valid (check browser)
8. Can create and manage tenants via API

## Next Steps

1. Create production tenants via `/api/tenants`
2. Configure Firebase auth or use API key auth
3. Set up monitoring and alerting
4. Configure backups and disaster recovery
5. Document custom domain setup for each tenant
6. Train admin users on platform usage

---

**Deployment Date**: _______________
**Deployed By**: _______________
**Notes**: _______________
