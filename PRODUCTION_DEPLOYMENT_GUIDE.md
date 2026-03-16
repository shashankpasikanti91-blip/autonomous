# Production Deployment & Operations Guide

**Version**: 2.0.0 (Production-Ready Orchestration)  
**Date**: February 22, 2026  
**Status**: ✅ Ready for Deployment

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Running Locally](#running-locally)
7. [Deployment](#deployment)
8. [API Documentation](#api-documentation)
9. [N8N Integration](#n8n-integration)
10. [Monitoring & Logging](#monitoring--logging)
11. [Troubleshooting](#troubleshooting)
12. [Production Checklist](#production-checklist)

---

## System Overview

The Autonomous HR & Business Operations Intelligence Platform is a production-ready system providing:

- **Agent Orchestration**: Coordinator, Executor, Analyzer, Planner agents with full reasoning chains
- **External Integrations**: Email, Messaging, Calendar, Payroll, Invoice, CRM, Visa monitoring
- **N8N Webhooks**: Full N8N workflow automation compatibility
- **Async Processing**: All operations async with concurrent execution
- **Memory Management**: Vector and Firestore-based memory for learning and context
- **Error Handling**: Automatic retry logic with exponential backoff
- **Comprehensive Logging**: Detailed reasoning and execution logging

---

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Gateway (Port 8000)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐   │
│  │  Workflow APIs   │  │  N8N Webhooks    │  │ Agent APIs   │   │
│  │  - Onboarding    │  │  - Email valid   │  │ - Status     │   │
│  │  - Recruitment   │  │  - Auth          │  │ - Tools      │   │
│  │  - Payroll       │  │  - Logging       │  │ - Memory     │   │
│  │  - Invoice       │  │                  │  │              │   │
│  │  - Meeting       │  │                  │  │              │   │
│  │  - Sales         │  │                  │  │              │   │
│  └──────────────────┘  └──────────────────┘  └──────────────┘   │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│                   Orchestration Service Layer                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────┐      ┌──────────────────────────┐      │
│  │ Agent Orchestrator  │      │ Service Connectors       │      │
│  │ - Routing           │   ┌──┤ - Email (Gmail/SMTP)      │      │
│  │ - Execution         │   │  │ - Messaging (WhatsApp)    │      │
│  │ - Retry Logic       │   │  │ - Calendar (Google)       │      │
│  │ - Error Handling    │─────┼─┤ - Payroll Processor      │      │
│  └─────────────────────┘   │  │ - Invoice Generator      │      │
│                            │  │ - CRM (HubSpot)          │      │
│  ┌─────────────────────┐   │  │ - Visa Monitoring        │      │
│  │ Agent Framework     │   │  └──────────────────────────┘      │
│  │ - Coordinator       │   │                                    │
│  │ - Executor          │    └─ External Services              │
│  │ - Analyzer          │                                        │
│  │ - Planner           │                                        │
│  └─────────────────────┘                                        │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│                  Memory & Data Layer                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────┐    ┌────────────────┐                       │
│  │ Vector Memory  │    │ Firestore DB   │                       │
│  │ (Embeddings)   │────┤ (State Store)  │                       │
│  └────────────────┘    │ (Real-time)    │                       │
│                        └────────────────┘                       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **Framework**: FastAPI 0.109.0
- **Server**: Uvicorn 0.27.0
- **Data Models**: Pydantic 2.5.0
- **AI Reasoning**: Pydantic-AI 0.0.12
- **Database**: Firebase/Firestore
- **Async**: Python asyncio
- **HTTP**: httpx, aiohttp
- **Environment**: Python 3.8+

---

## Prerequisites

### System Requirements

- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended)
- 2GB disk space
- Linux/macOS/Windows with WSL2

### External Services (Optional - for full integration)

- Firebase project with Firestore enabled
- Gmail account (for email sending)
- Google Calendar API credentials
- HubSpot CRM API key
- N8N instance (for workflow automation)
- WhatsApp Business account (for messaging)

---

## Installation

### 1. Clone/Download Project

```bash
cd /path/to/emergentic-ai
# or download and extract zip
```

### 2. Create Virtual Environment

```bash
# Using venv
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or using conda
conda create -n hr-platform python=3.8
conda activate hr-platform
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create Environment File

```bash
cp .env.example .env
```

---

## Configuration

### Development Setup (.env)

```bash
# Minimal working configuration
ENV=development
LOG_LEVEL=INFO
DEBUG=true

API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# Email (using SMTP)
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_ADDRESS=noreply@company.com

# Firebase (optional)
FIREBASE_PROJECT_ID=your-project-id

# N8N (optional)
N8N_URL=http://localhost:5678
```

### Production Setup (.env)

```bash
# Production environment
ENV=production
LOG_LEVEL=WARNING
DEBUG=false

API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false
API_KEY_REQUIRED=true

# Use managed email service
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=your-production-key

# Firebase project
FIREBASE_PROJECT_ID=your-prod-project
FIREBASE_CREDENTIALS_JSON=...

# N8N instance
N8N_URL=https://n8n.your-domain.com
N8N_API_KEY=your-production-key

# Other services
CRM_PROVIDER=hubspot
CRM_API_KEY=your-hubspot-key

# Application settings
MAX_WORKERS=50
MAX_RETRIES=5
REQUEST_TIMEOUT=60
```

### Configuration Files by Environment

| Environment | File | Purpose |
|-------------|------|---------|
| Development | `.env` | Local development secrets |
| Testing | `.env.test` | Test environment config |
| Staging | `.env.staging` | Pre-production config |
| Production | `.env.prod` | Production secrets (use secrets manager) |

---

## Running Locally

### Start the API Server

```bash
# Development mode (with hot reload)
python main.py

# Or directly with uvicorn
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Production mode (no reload)
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Verify Installation

```bash
# Check health
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","timestamp":"2026-02-22T..."}

# List available workflows
curl http://localhost:8000/api/workflows

# List N8N webhooks
curl http://localhost:8000/webhooks/n8n/workflows
```

### Run Existing Demonstrations

```bash
# Run reasoning demonstrations
python examples/agent_reasoning_demonstrations.py

# Should output:
# [REASONING] Coordinator analyzing workflow...
# [ORCHESTRATION] Executing workflow steps...
# ✓ Demonstrations completed
```

---

## Deployment

### Docker Deployment

```bash
# Build image
docker build -t hr-platform:latest .

# Run container
docker run -p 8000:8000 \
  --env-file .env.prod \
  hr-platform:latest

# Or with docker-compose
docker-compose -f docker-compose.yml up -d
```

### Kubernetes Deployment

```bash
# Create ConfigMap for settings
kubectl create configmap hr-platform-config --from-file=.env.prod

# Deploy
kubectl apply -f k8s/deployment.yaml

# Verify
kubectl get pods
kubectl logs -f deployment/hr-platform
```

### Cloud Platforms

#### AWS (Elastic Beanstalk)
```bash
eb init -p python-3.8 hr-platform
eb create production
eb deploy
```

#### Google Cloud (Cloud Run)
```bash
gcloud run deploy hr-platform \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Azure (App Service)
```bash
az webapp up --name hr-platform \
  --resource-group myResourceGroup \
  --runtime "PYTHON|3.8"
```

---

## API Documentation

### Workflow Endpoints

#### 1. Employee Onboarding

```bash
POST /api/workflows/onboarding/start
{
  "employee_id": "EMP001",
  "employee_name": "John Doe",
  "employee_email": "john@company.com",
  "department": "Engineering",
  "position": "Software Engineer",
  "start_date": "2026-03-01"
}

Response:
{
  "execution_id": "exec_123...",
  "workflow_id": "employee_onboarding",
  "status": "completed",
  "welcome_email_sent": true,
  "orientation_scheduled": true,
  "account_created": true
}
```

#### 2. Recruitment Screening

```bash
POST /api/workflows/recruitment/screen
{
  "candidate_id": "CAN001",
  "candidate_name": "Jane Smith",
  "candidate_email": "jane@example.com",
  "position_id": "POS456",
  "resume_url": "https://example.com/resume.pdf"
}
```

#### 3. Payroll Processing

```bash
POST /api/workflows/payroll/process
{
  "payroll_period": "2026-02",
  "company_id": "COM123",
  "employee_ids": ["EMP001", "EMP002"],
  "process_all": false
}
```

#### 4. Invoice Generation

```bash
POST /api/workflows/invoice/generate
{
  "client_id": "CLI001",
  "client_name": "Acme Corp",
  "items": [
    {"description": "Services", "quantity": 10, "unit_price": 150}
  ],
  "amount_due": 1500.00,
  "due_date": "2026-03-15"
}
```

#### 5. Meeting Scheduling

```bash
POST /api/workflows/meeting/schedule
{
  "title": "Team Standup",
  "participants": ["user1@company.com", "user2@company.com"],
  "start_time": "2026-02-28T14:00:00Z",
  "duration_minutes": 30,
  "room_required": true
}
```

#### 6. Sales Lead Generation

```bash
POST /api/workflows/sales/generate-lead
{
  "lead_name": "John Prospect",
  "lead_email": "john@prospect.com",
  "company_name": "Prospect Corp",
  "lead_source": "website"
}
```

### Agent Endpoints

```bash
# List agents
GET /agents

# Get agent details
GET /agents/{agent_id}

# Get agent tools
GET /agents/{agent_id}/tools

# Get agent state
GET /agents/{agent_id}/state
```

### Workflow Management

```bash
# List all workflows
GET /api/workflows

# Get workflow details
GET /api/workflows/{workflow_id}

# Get execution status
GET /api/workflows/{workflow_id}/executions/{execution_id}
```

---

## N8N Integration

### Setup N8N Webhook

1. **In N8N Editor**:
   - Create new workflow
   - Add "Webhook" trigger node
   - Set Method: POST
   - URL: `http://your-api-domain/webhooks/n8n/onboarding`

2. **Configure Request**:
   - Headers: `Content-Type: application/json`
   - Body: Required fields per workflow

3. **Test Webhook**:

```bash
curl -X POST http://localhost:8000/webhooks/n8n/onboarding \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "n8n_employee_onboarding",
    "trigger_name": "employee_created",
    "data": {
      "employee_id": "EMP123",
      "employee_name": "John Doe",
      "employee_email": "john@company.com",
      "department": "Engineering",
      "start_date": "2026-03-01"
    }
  }'
```

### Available Webhooks

| Endpoint | Workflow | Trigger | Fields |
|----------|----------|---------|--------|
| `/webhooks/n8n/onboarding` | Employee Onboarding | employee_created | employee_id, name, email, department, start_date |
| `/webhooks/n8n/recruitment` | Recruitment | candidate_applied | candidate_id, name, email, position_id, resume_url |
| `/webhooks/n8n/payroll` | Payroll | payroll_processing | payroll_period, employee_ids, company_id |
| `/webhooks/n8n/invoice` | Invoice | invoice_created | invoice_id, client_id, amount, due_date |
| `/webhooks/n8n/meeting` | Meeting | meeting_requested | meeting_id, participants, start_time, duration |
| `/webhooks/n8n/sales` | Sales Lead | lead_generated | lead_id, name, email, company, source |

---

## Monitoring & Logging

### Enable Detailed Logging

Set in `.env`:
```bash
LOG_LEVEL=DEBUG
```

### View Logs

```bash
# Real-time logs
tail -f logs/app.log

# Filter by component
grep "\[ORCHESTRATION\]" logs/app.log
grep "\[WORKFLOW\]" logs/app.log
grep "\[N8N\]" logs/app.log

# Search errors
grep "ERROR" logs/app.log
```

### Logging Format

```
[2026-02-22 14:23:45] [ORCHESTRATION] agent_id=executor_1 action=route_task status=completed duration_ms=145
[2026-02-22 14:23:46] [WORKFLOW] workflow_id=employee_onboarding step=send_welcome_email status=completed
[2026-02-22 14:23:47] [N8N] webhook_id=wh_123 execution=exec_456 status=completed duration_ms=320
```

### Metrics to Monitor

- Request latency (p50, p95, p99)
- Error rates by workflow type
- Agent utilization
- Memory usage
- Concurrent executions
- Retry counts

---

## Troubleshooting

### Common Issues

#### Issue: "Email sending failed"

**Solution**:
```bash
# Verify SMTP settings
echo "Test email" | python -c "
import smtplib
smtp = smtplib.SMTP('smtp.gmail.com', 587)
smtp.starttls()
smtp.login('YOUR_EMAIL', 'YOUR_PASSWORD')
print('✓ SMTP OK')
"

# Check .env configuration
cat .env | grep SMTP
```

#### Issue: "Firebase connection timeout"

**Solution**:
```bash
# Verify Firebase credentials
export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"

# Test connection
python -c "
import firebase_admin
firebase_admin.initialize_app()
print('✓ Firebase OK')
"
```

#### Issue: "N8N webhook validation failed"

**Solution**:
```bash
# Check webhook URL accessibility
curl -I http://your-api/webhooks/n8n/workflows

# Verify required fields
curl -X POST http://localhost:8000/webhooks/n8n/onboarding \
  -H "Content-Type: application/json" \
  -d '{"workflow_id": "n8n_employee_onboarding", "trigger_name": "test", "data": {}}'

# Should return validation error with missing fields
```

#### Issue: "Agent orchestration timeout"

**Solution**:
```bash
# Increase timeout in .env
REQUEST_TIMEOUT=60

# Check agent status
curl http://localhost:8000/agents

# Monitor logs
tail -f logs/app.log | grep "\[ORCHESTRATION\]"
```

---

## Production Checklist

### Pre-Deployment

- [ ] Environment variables configured for production
- [ ] External services credentials stored securely
- [ ] Database backups enabled
- [ ] Firebase security rules reviewed
- [ ] N8N instance available and tested
- [ ] Email service credentials verified
- [ ] API rate limiting configured
- [ ] Error handling tested
- [ ] Logging reviewed
- [ ] Security review completed

### Deployment

- [ ] Docker image built and pushed
- [ ] Database migrations applied
- [ ] Service deployed on production infrastructure
- [ ] Load balancer/reverse proxy configured
- [ ] SSL/TLS certificates installed
- [ ] CORS policies configured
- [ ] API keys rotated
- [ ] Monitoring enabled

### Post-Deployment

- [ ] Health checks passing
- [ ] API endpoints responding
- [ ] Workflows executing successfully
- [ ] N8N webhooks operational
- [ ] Email sending working
- [ ] Logs monitoring in place
- [ ] Uptime monitoring active
- [ ] Incident response plan activated

### Monitoring Setup

```bash
# Install monitoring tools
docker run -p 9090:9090 prom/prometheus
docker run -p 3000:3000 grafana/grafana

# Configure alerts
# - API latency > 1s
# - Error rate > 1%
# - Memory usage > 80%
# - Webhook failures > 5/min
```

---

## Support & Additional Resources

- **Logs**: Check `logs/` directory for detailed execution logs
- **Examples**: See `examples/` for demonstration code
- **Documentation**: Full architecture in `ARCHITECTURE_ENHANCED_AI.md`
- **Issues**: Check troubleshooting guide above
- **Roadmap**: See `IMPLEMENTATION_ROADMAP_UPDATED.md` for future phases

---

**Last Updated**: February 22, 2026  
**Maintained By**: Engineering Team  
**Status**: ✅ **PRODUCTION READY**
