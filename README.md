# Emergentic AI

**Enterprise-grade autonomous operations platform** — describe your business in plain language and get a fully-wired application with AI-generated schemas, multi-tenant isolation, and automated workflows.

🌐 **Live: [https://autonomous.srpailabs.com](https://autonomous.srpailabs.com)**  
📖 **API Docs: [https://autonomous.srpailabs.com/docs](https://autonomous.srpailabs.com/docs)**  
💚 **Health: [https://autonomous.srpailabs.com/health](https://autonomous.srpailabs.com/health)**

---

## What it does

Emergentic AI lets teams describe their internal operations in plain language, and the platform AI-generates a custom database application (tables, schemas, CRUD API) tailored to their industry. Ships with pre-built workflow automation for onboarding, payroll, invoicing, recruitment, scheduling, and sales lead management — all multi-tenant, all production-ready.

---

## Key features

| Feature | Status |
|---|---|
| AI app generation from natural language | ✅ Live |
| Multi-industry templates (7 industries) | ✅ Live |
| Multi-tenant subdomain routing | ✅ Live |
| Workflow automation (6 workflows) | ✅ Live |
| PostgreSQL persistence (apps, schemas, records) | ✅ Live |
| Execution logging + audit trail | ✅ Live |
| N8N webhook integration | ✅ Live |
| Demo accounts pre-seeded | ✅ Live |
| Gmail / WhatsApp / Calendar / HubSpot integrations | ⚙️ Configurable (stub) |
| Firebase auth | ⚙️ Configurable (stub) |

---

## Demo accounts

All demo accounts use password: **`Demo@123`**

| Email | Role | Organization |
|---|---|---|
| admin@demo.com | Admin | Demo Corp (IT Company) |
| owner@demo.com | Owner | HealthFirst Hospital |
| hr@demo.com | Manager | EduTech Academy |
| finance@demo.com | Manager | FinanceFlow Ltd |
| sales@demo.com | User | SalesEdge Agency |
| dev@demo.com | User | TechBuild Solutions |
| recruiter@demo.com | User | RecruitPro Agency |
| ops@demo.com | User | OpsCore Services |

---

## Supported industries

| ID | Industry | Default modules |
|---|---|---|
| `hospital` | Healthcare / Hospital | Patients, Appointments, Medical Records, Staff |
| `school` | Education / School | Students, Classes, Attendance, Fee Payments |
| `it_company` | IT / Software Company | Projects, Tasks, Timesheets |
| `recruitment` | Recruitment Agency | Candidates, Job Openings, Placements |
| `payroll_finance` | Payroll & Finance | Employees, Payroll Runs, Tax Records |
| `service_business` | Service Business | Clients, Jobs, Invoices |
| `generic` | General Operations | Flexible / custom |

---

## Tech stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, Pydantic v2
- **Database**: PostgreSQL 16 (Docker container on Hetzner)
- **Frontend**: React 18, TypeScript, Tailwind CSS (`ui-platform/`)
- **Hosting**: Hetzner VPS (5.223.67.236), Docker, Nginx
- **Domain**: `autonomous.srpailabs.com` + `*.autonomous.srpailabs.com`
- **SSL**: Let's Encrypt (auto-renewed via certbot)

---

## Local development

### 1. Prerequisites

- Python 3.11+
- PostgreSQL running locally (database `hr_multitenant` must exist)
- Node.js 18+ (for frontend)

### 2. Clone and set up

```bash
git clone <your-repo>
cd "emergentic AI"

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env — set DATABASE_URL and any API keys you have
```

Minimum required in `.env` for local dev:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/hr_multitenant
ENV=development
API_PORT=8000
```

### 4. Run backend

```bash
python main.py
```

Run database migrations (local):

```bash
psql "${DATABASE_URL}" -f db/migrations/001_init.sql
psql "${DATABASE_URL}" -f db/migrations/002_add_modules_column.sql
psql "${DATABASE_URL}" -f db/migrations/003_apps_extended_columns.sql
psql "${DATABASE_URL}" -f db/migrations/004_add_org_slug_domain.sql
```

API available at: `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs`

### 5. Run frontend (optional)

```bash
cd ui-platform
npm install
npm run dev
```

Frontend available at: `http://localhost:5173`

---

## API overview

### Core endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check + platform info |
| `GET` | `/api/platform/info` | Platform metadata, supported industries |
| `GET` | `/api/industries` | List all 7 supported industries |
| `GET` | `/api/industries/{id}` | Get single industry config |

### App generation

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/apps` | Create app from natural language prompt |
| `GET` | `/api/apps` | List all apps for org |
| `GET` | `/api/apps/{id}` | Get app details + schema |
| `DELETE` | `/api/apps/{id}` | Delete app |

### Workflow automation

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/workflows/onboarding/start` | Employee onboarding |
| `POST` | `/api/workflows/recruitment/screen` | Candidate screening + scoring |
| `POST` | `/api/workflows/payroll/process` | Payroll processing |
| `POST` | `/api/workflows/invoice/generate` | Invoice generation |
| `POST` | `/api/workflows/meeting/schedule` | Meeting scheduling |
| `POST` | `/api/workflows/sales/generate-lead` | Sales lead qualification |

### N8N webhooks

| Method | Path | Description |
|---|---|---|
| `POST` | `/webhooks/n8n/onboarding` | N8N onboarding trigger |
| `POST` | `/webhooks/n8n/payroll` | N8N payroll trigger |
| `POST` | `/webhooks/n8n/invoice` | N8N invoice trigger |
| `POST` | `/webhooks/n8n/meeting` | N8N meeting trigger |

---

## Multi-tenant model

Each tenant is identified by a subdomain or custom domain you provide:

- `hr.example.com` → main platform (no tenant slug)
- `acme.hr.example.com` → tenant `acme`
- `beta.hr.example.com` → tenant `beta`
- Custom domain: map `custom_domain` per organization (e.g., `people.acme.com`).

The `TenantMiddleware` extracts the slug from the `Host` header and sets `request.state.tenant_slug` for all downstream handlers.

---

## Environment variables reference

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | — | PostgreSQL connection string (required). Use separate DB per environment/tenant project (e.g., `hr_multitenant` locally; a different name on server). |
| `ENV` | `development` | `development` or `production` |
| `API_PORT` | `8000` | HTTP port (use `8010` in production) |
| `API_HOST` | `0.0.0.0` | Bind host |
| `ALLOWED_ORIGINS` | localhost | Comma-separated CORS origins |
| `SECRET_KEY` | change-me | JWT / session signing key |
| `PLATFORM_NAME` | HR Autonomous OS | Displayed in health / info responses |
| `PLATFORM_DOMAIN` | hr.local | Used for tenant resolution (set to your prod domain) |
| `TRUST_PROXY_HEADERS` | `true` | Trust `X-Forwarded-For` from Nginx |
| `PYDANTIC_AI_MODEL` | claude-3-5-sonnet-20241022 | AI model for app generation |
| `ANTHROPIC_API_KEY` | — | Required for AI app generation |
| `EMAIL_PROVIDER` | `smtp` | `smtp`, `gmail`, or `sendgrid` |
| `N8N_URL` | localhost:5678 | N8N instance URL |

See `.env.example` for the full list.

---

## Production deployment (VPS + reverse proxy)

### Overview

HR Autonomous OS deploys as an **isolated multi-tenant system** with its own PostgreSQL database. This deployment uses:

- **Server**: Hetzner VPS (5.223.67.236) running existing infrastructure
- **Database**: Separate Docker container (port 5544) for HR project isolation
- **Domain**: `autonomous.srpailabs.com` + `*.autonomous.srpailabs.com`
- **TLS**: Cloudflare Origin Certificate
- **Reverse Proxy**: Nginx (existing; new HR vhost added)
- **Isolation**: Separate systemd service + environment variables ensure no cross-project contamination

**IMPORTANT**: This deployment does NOT affect existing projects (hospital, etc.) because:
1. Database is in a separate Docker container with separate credentials
2. Backend runs in separate systemd service with isolated environment
3. Nginx routes via new vhost config
4. All configuration is environment-driven

### Step 1: Prepare deployment script

Copy the deployment script to your server:

```bash
# On your local machine
scp deploy/deploy.sh root@5.223.67.236:/opt/hr-deploy.sh
chmod +x /opt/hr-deploy.sh
```

### Step 2: Execute automated deployment

SSH to the server and run the comprehensive deployment script:

```bash
ssh root@5.223.67.236

# Run the automated deployment (handles all steps below)
bash /opt/hr-deploy.sh
```

This single script will:
1. ✅ Create isolated PostgreSQL docker container (port 5544)
2. ✅ Apply all 4 database migrations
3. ✅ Install Cloudflare Origin certificate
4. ✅ Deploy backend code and dependencies
5. ✅ Configure systemd service
6. ✅ Build frontend
7. ✅ Configure Nginx with SSL
8. ✅ Verify all services are running

### Step 3: Prepare Cloudflare Origin Certificate

Before running deployment script, place your certificate and key on the server:

```bash
# On your local machine, if you have cert files
scp ~/cert.pem root@5.223.67.236:/etc/ssl/autonomous.srpailabs.com/
scp ~/key.pem root@5.223.67.236:/etc/ssl/autonomous.srpailabs.com/
```

The deployment script will wait for these if not already present.

### OR: Step-by-step manual deployment

If you prefer manual control, run each step:

#### 3.1. Create isolated PostgreSQL container

```bash
# On server
docker run -d \
  --name hr-postgres \
  -e POSTGRES_USER=hr_app \
  -e POSTGRES_PASSWORD=hr_secure_password_change_me \
  -e POSTGRES_DB=hr_multitenant \
  -p 5544:5432 \
  -v hr-pg-data:/var/lib/postgresql/data \
  --restart always \
  postgres:15

# Verify container is running
docker ps | grep hr-postgres
```

#### 3.2. Apply database migrations

```bash
bash deploy/apply-migrations.sh localhost 5544 hr_app hr_secure_password_change_me hr_multitenant
```

#### 3.3. Clone and deploy backend

```bash
git clone <your-repo> /opt/hr-autonomous
cd /opt/hr-autonomous
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy production environment
cp .env.production .env
# Edit .env and set secure password and SECRET_KEY
nano .env
```

#### 3.4. Create systemd service

```bash
sudo tee /etc/systemd/system/srp-autonomous-hr.service > /dev/null <<EOF
[Unit]
Description=HR Autonomous OS Backend
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/hr-autonomous
Environment="PATH=/opt/hr-autonomous/venv/bin"
ExecStart=/opt/hr-autonomous/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable srp-autonomous-hr
sudo systemctl start srp-autonomous-hr
```

#### 3.5. Install TLS certificate

```bash
sudo mkdir -p /etc/ssl/autonomous.srpailabs.com
sudo cp cert.pem /etc/ssl/autonomous.srpailabs.com/
sudo cp key.pem /etc/ssl/autonomous.srpailabs.com/
sudo chmod 600 /etc/ssl/autonomous.srpailabs.com/key.pem
```

#### 3.6. Configure Nginx

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/hr-autonomous
sudo ln -s /etc/nginx/sites-available/hr-autonomous /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 3.7. Build frontend

```bash
cd /opt/hr-autonomous/ui-platform
npm install --legacy-peer-deps
npm run build
```

### Step 4: Verify deployment

```bash
# Check backend service
sudo systemctl status srp-autonomous-hr

# Check database container
docker ps | grep hr-postgres

# Test health endpoint
curl http://localhost:8010/health

# Check Nginx
sudo nginx -t
```

### Step 5: DNS configuration

Ensure your DNS records point to the server:

```
A    app.autonomous.srpailabs.com          5.223.67.236
A    *.autonomous.srpailabs.com            5.223.67.236
```

## Running E2E Tests

### Automated E2E Testing

```bash
# On server or local machine (with API running)
export API_URL=https://autonomous.srpailabs.com
bash deploy/e2e-test.sh ${API_URL}
```

Or run locally against local dev server:

```bash
# Start backend locally
python main.py &

# Run e2e tests
bash deploy/e2e-test.sh http://localhost:8000
```

### Test Coverage

The E2E test suite validates:

1. ✅ **API Connectivity** — Health check, base endpoints
2. ✅ **Tenant Management** — Create, list, fetch organizations
3. ✅ **Multi-tenant Isolation** — Data isolation between orgs
4. ✅ **App Management** — Create, read, delete applications
5. ✅ **Schemas & Records** — Create database schemas dynamically
6. ✅ **Industry Modules** — Verify all 7 industries available
7. ✅ **AI Reasoning** — Test reasoning engine integration
8. ✅ **Authentication** — Verify auth requirements
9. ✅ **CORS** — Test multi-domain support
10. ✅ **Database Integrity** — Verify schema completeness

### Test API Manually

Create a test tenant:

```bash
curl -X POST https://autonomous.srpailabs.com/api/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "owner_email": "admin@test-hr.com",
    "name": "Test Organization",
    "slug": "test-org-'$(date +%s)'",
    "industry": "payroll_finance"
  }'
```

Create an app in the tenant:

```bash
curl -X POST https://autonomous.srpailabs.com/api/records/apps \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: <tenant-id-from-above>" \
  -d '{
    "name": "Test App",
    "type": "hr_workflow",
    "description": "Test application"
  }'
```

### Python Unit Tests

```bash
# Unit + integration tests
pytest tests/ -v

# Specific test file
pytest tests/test_e2e.py -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

---

## Troubleshooting deployment

| Issue | Solution |
|---|---|
| PostgreSQL container won't start | Check port 5544 is available: `sudo lsof -i :5544` |
| Backend service fails to start | Check `.env` DATABASE_URL is correct and container is running |
| Nginx returns 502 | Verify backend is running: `curl http://127.0.0.1:8010/health` |
| SSL certificate errors | Verify cert path in `.env`: `ls -la /etc/ssl/autonomous.srpailabs.com/` |
| Multi-tenant not working | Check TenantMiddleware extracts Host correctly: `sudo journalctl -u srp-autonomous-hr -f` |
| Frontend not loading | Verify frontend build exists: `ls -la /opt/hr-autonomous/ui-platform/dist/` |

## Monitoring and maintenance

### View backend logs

```bash
sudo journalctl -u srp-autonomous-hr -f
```

### View Nginx logs

```bash
tail -f /var/log/nginx/hr-autonomous-access.log
tail -f /var/log/nginx/hr-autonomous-error.log
```

### Restart services

```bash
# Backend
sudo systemctl restart srp-autonomous-hr

# Nginx
sudo systemctl reload nginx

# PostgreSQL
docker restart hr-postgres
```

### Database backups

```bash
# Backup HR database
docker exec hr-postgres pg_dump -U hr_app hr_multitenant > hr-backup-$(date +%Y%m%d).sql

# Restore from backup
docker exec -i hr-postgres psql -U hr_app hr_multitenant < hr-backup-20260316.sql
```

---

## Running pytest tests

```bash
# Unit + integration tests
pytest tests/ -v

# E2E tests (requires running backend)
BASE_URL=http://localhost:8000 pytest tests/test_e2e.py -v
```

---

## Project structure

```
├── main.py                     # Entrypoint — runs uvicorn
├── app/
│   ├── api/                    # FastAPI routers
│   │   ├── main.py             # App factory, middleware, router registration
│   │   ├── workflows.py        # 6 workflow endpoints
│   │   ├── records.py          # App / schema / record CRUD
│   │   ├── industry_router.py  # Industry metadata endpoints
│   │   └── ...
│   ├── config/settings.py      # All env-var config (pydantic-settings)
│   ├── db/                     # SQLAlchemy models, migrations, service layer
│   ├── industry/config.py      # 7-industry abstraction layer
│   ├── middleware/tenant.py    # Subdomain → tenant_slug middleware
│   ├── integrations/           # Gmail, WhatsApp, Calendar, HubSpot, Firebase (stub)
│   └── services/               # Connectors, orchestration, n8n webhooks
├── backend/
│   └── templates/              # Business app templates (7 templates + keyword map)
├── ui-platform/                # React + TypeScript frontend
├── deploy/
│   ├── nginx.conf              # Nginx vhost config (wildcard subdomain)
│   └── srp-autonomous.service  # Systemd unit file
├── tests/
│   ├── test_e2e.py             # End-to-end API tests
│   └── ...
└── .env.example                # Full environment variable reference
```

---

## Known limitations

- **External integrations are stub implementations**: Gmail, WhatsApp, Google Calendar, HubSpot, and Firebase are wired up but operate in simulation mode until real API credentials are provided via `.env`.
- **AI app generation requires Anthropic API key**: Without `ANTHROPIC_API_KEY`, app generation falls back to template matching only.
- **Single database**: All tenants share the `srp_os` PostgreSQL database; row-level tenant isolation is enforced via `org_id`. Dedicated per-tenant databases are a future roadmap item.
- **No built-in authentication**: The platform currently relies on Cloudflare Access or an upstream auth proxy for authentication. JWT-based auth is planned.

---

## License

Proprietary — SRP AI Labs. All rights reserved.
