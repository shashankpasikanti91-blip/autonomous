# Quick Start - Production-Ready Orchestration

**Get the system running in 5 minutes!**

## Prerequisites

- Python 3.8+
- Git or zip download
- 5 minutes of your time

## Step 1: Setup (2 minutes)

```bash
# Clone or navigate to project
cd c:\Users\User\Desktop\emergentic AI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure (1 minute)

```bash
# Copy environment template
cp .env.example .env

# Edit .env - minimal configuration
# Just these are needed for local testing:
# ENV=development
# API_PORT=8000
# EMAIL_PROVIDER=smtp
# LOG_LEVEL=INFO
```

## Step 3: Run Server (1 minute)

```bash
# Start the API server
python main.py

# Should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete
```

## Step 4: Test API (1 minute)

### In another terminal:

```bash
# Health check
curl http://localhost:8000/health

# List agents
curl http://localhost:8000/agents

# List N8N workflows
curl http://localhost:8000/webhooks/n8n/workflows

# Start onboarding workflow
curl -X POST http://localhost:8000/api/workflows/onboarding/start \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "EMP001",
    "employee_name": "John Doe",
    "employee_email": "john@company.com",
    "department": "Engineering",
    "position": "Software Engineer",
    "start_date": "2026-03-01"
  }'

# You should see:
# {
#   "execution_id": "...",
#   "status": "completed",
#   "welcome_email_sent": true,
#   "steps_completed": [...]
# }
```

---

## Testing All Workflows

### 1. Recruitment Screening

```bash
curl -X POST http://localhost:8000/api/workflows/recruitment/screen \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_id": "CAN001",
    "candidate_name": "Jane Smith",
    "candidate_email": "jane@example.com",
    "position_id": "POS456",
    "resume_url": "https://example.com/resume.pdf"
  }'
```

### 2. Payroll Processing

```bash
curl -X POST http://localhost:8000/api/workflows/payroll/process \
  -H "Content-Type: application/json" \
  -d '{
    "payroll_period": "2026-02",
    "company_id": "COM123",
    "employee_ids": ["EMP001", "EMP002", "EMP003"]
  }'
```

### 3. Invoice Generation

```bash
curl -X POST http://localhost:8000/api/workflows/invoice/generate \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "CLI001",
    "client_name": "Acme Corp",
    "client_email": "finance@acmecorp.com",
    "items": [
      {"description": "Consulting", "quantity": 10, "unit_price": 150}
    ],
    "amount_due": 1500.00,
    "due_date": "2026-03-15"
  }'
```

### 4. Meeting Scheduling

```bash
curl -X POST http://localhost:8000/api/workflows/meeting/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Team Standup",
    "participants": ["user1@company.com", "user2@company.com"],
    "start_time": "2026-02-28T14:00:00Z",
    "duration_minutes": 30,
    "room_required": true
  }'
```

### 5. Sales Lead Generation

```bash
curl -X POST http://localhost:8000/api/workflows/sales/generate-lead \
  -H "Content-Type: application/json" \
  -d '{
    "lead_name": "John Prospect",
    "lead_email": "john@prospect.com",
    "company_name": "Prospect Corp",
    "lead_source": "website",
    "lead_budget": 50000.0
  }'
```

---

## Testing N8N Webhooks

### Webhook Endpoint Format

Each workflow has a corresponding N8N webhook:

```bash
# Employee Onboarding
POST /webhooks/n8n/onboarding

# Recruitment
POST /webhooks/n8n/recruitment

# Payroll
POST /webhooks/n8n/payroll

# Invoice
POST /webhooks/n8n/invoice

# Meeting
POST /webhooks/n8n/meeting

# Sales
POST /webhooks/n8n/sales
```

### Example: Test Onboarding Webhook

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

# Response:
# {
#   "success": true,
#   "execution_id": "...",
#   "status": "completed",
#   "results": {...}
# }
```

---

## Using Python Client

### Client Example

```python
import httpx
import asyncio
from datetime import datetime, timedelta

async def test_workflows():
    async with httpx.AsyncClient() as client:
        # Test onboarding
        response = await client.post(
            "http://localhost:8000/api/workflows/onboarding/start",
            json={
                "employee_id": "EMP001",
                "employee_name": "John Doe",
                "employee_email": "john@company.com",
                "department": "Engineering",
                "position": "Software Engineer",
                "start_date": "2026-03-01"
            }
        )
        print("Onboarding:", response.json()["status"])
        
        # Test N8N webhook
        response = await client.post(
            "http://localhost:8000/webhooks/n8n/recruitment",
            json={
                "workflow_id": "n8n_recruitment",
                "trigger_name": "candidate_applied",
                "data": {
                    "candidate_id": "CAN001",
                    "candidate_name": "Jane Smith",
                    "candidate_email": "jane@example.com",
                    "position_id": "POS456",
                    "resume_url": "https://example.com/resume.pdf"
                }
            }
        )
        print("Webhook:", response.json()["success"])

# Run it
asyncio.run(test_workflows())
```

---

## API Documentation

### Base URLs

- **Local**: `http://localhost:8000`
- **Production**: `https://api.your-domain.com`

### Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Server health check |
| `/agents` | GET | List all agents |
| `/agents/{id}` | GET | Get agent status |
| `/agents/{id}/tools` | GET | Get agent tools |
| `/api/workflows/onboarding/start` | POST | Start onboarding |
| `/api/workflows/recruitment/screen` | POST | Screen candidate |
| `/api/workflows/payroll/process` | POST | Process payroll |
| `/api/workflows/invoice/generate` | POST | Generate invoice |
| `/api/workflows/meeting/schedule` | POST | Schedule meeting |
| `/api/workflows/sales/generate-lead` | POST | Generate lead |
| `/webhooks/n8n/workflows` | GET | List N8N workflows |
| `/webhooks/n8n/*` | POST | N8N webhook triggers |

### Response Format

All endpoints return JSON:

```json
{
  "execution_id": "string",
  "workflow_id": "string",
  "status": "completed|failed|pending",
  "results": {
    "key": "value"
  },
  "error_messages": [],
  "timestamp": "2026-02-22T14:23:45.123Z"
}
```

---

## Monitoring

### Check Real-Time Logs

```bash
# Terminal 1: Running server shows:
tail -f output

# Look for:
# [ORCHESTRATION] ...
# [WORKFLOW] ...
# [N8N] ...
```

### Query Webhook Status

```bash
# Get status of a webhook execution
curl http://localhost:8000/webhooks/n8n/status/{execution_id}

# Get logs for a workflow
curl "http://localhost:8000/webhooks/n8n/logs/n8n_employee_onboarding?limit=10"
```

---

## Common Tasks

### Add New Workflow

1. Create endpoint in `app/api/workflows.py`
2. Add N8N webhook in `app/api/n8n.py`
3. Register in `app/api/main.py`
4. Test with curl

### Integrate External Service

1. Create connector class in `app/services/connectors.py`
2. Register in orchestration service in `app/api/main.py`
3. Use from workflow step

### Enable Real Email Sending

1. Update `.env`:
   ```
   EMAIL_PROVIDER=gmail
   GMAIL_SERVICE_ACCOUNT_KEY=your-key
   ```

2. Or use SMTP:
   ```
   EMAIL_PROVIDER=smtp
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   ```

---

## Troubleshooting

### Server won't start

```bash
# Check port is available
lsof -i :8000

# Try different port
export API_PORT=8001
python main.py
```

### Can't connect to API

```bash
# Check server is running
curl http://localhost:8000/health

# Check firewall
sudo ufw allow 8000/tcp  # Linux

# Check .env configuration
cat .env | grep API
```

### Webhooks returning errors

```bash
# Check required fields
curl -X POST http://localhost:8000/webhooks/n8n/onboarding \
  -H "Content-Type: application/json" \
  -d '{"workflow_id": "test", "trigger_name": "test", "data": {}}'

# Should tell you which fields are missing
```

---

## What's Next?

### Level 1: Understand the System
- [ ] Read `ARCHITECTURE_ENHANCED_AI.md` for system design
- [ ] Check `PRODUCTION_DEPLOYMENT_GUIDE.md` for detailed setup
- [ ] Explore source code in `app/` directory

### Level 2: Test Integration
- [ ] Configure real email service (Gmail/SMTP)
- [ ] Connect Firebase project
- [ ] Setup N8N instance
- [ ] Test end-to-end workflows

### Level 3: Deploy to Production
- [ ] Prepare production environment
- [ ] Configure external services
- [ ] Deploy with Docker
- [ ] Enable monitoring

### Level 4: Extend Platform
- [ ] Add custom workflows
- [ ] Integrate more services
- [ ] Build custom agents
- [ ] Implement advanced features

---

## Key Files

| File | Purpose |
|------|---------|
| `app/api/main.py` | API entry point |
| `app/api/workflows.py` | Workflow endpoints |
| `app/api/n8n.py` | N8N webhooks |
| `app/services/orchestration.py` | Agent orchestration |
| `app/services/connectors.py` | Service integrations |
| `app/services/n8n_webhooks.py` | N8N support |
| `app/config/settings.py` | Configuration |
| `.env` | Environment variables |
| `main.py` | Server launcher |

---

## Support

**Having issues?**

1. Check logs: `tail -f output`
2. Review troubleshooting section above
3. See `PRODUCTION_DEPLOYMENT_GUIDE.md` for advanced setup
4. Check test file: `tests/test_api.py`

**Want to learn the codebase?**

1. Start with `ARCHITECTURE_ENHANCED_AI.md`
2. Read `IMPLEMENTATION_ROADMAP_UPDATED.md`
3. Explore examples in `examples/`
4. Review test cases in `tests/`

---

**Happy orchestrating! 🚀**

Status: ✅ **READY TO RUN**  
Last Updated: February 22, 2026
