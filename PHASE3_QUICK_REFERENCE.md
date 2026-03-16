# Phase 3: Quick Reference - Real Service Integration

**TL;DR**: Replace mocks with real production APIs in 5 minutes.

## Installation

```bash
# Update requirements
pip install -r requirements.txt

# New packages include:
# - google-auth, google-auth-oauthlib (OAuth)
# - google-api-python-client (Gmail, Calendar)
# - reportlab, weasyprint (PDF)
# - APScheduler (scheduled jobs)
```

## Key Changes from Phase 2

| Aspect | Phase 2 | Phase 3 |
|--------|---------|---------|
| Email | Mock async simulation | Real Gmail/SendGrid/SMTP |
| Messaging | Mock response | Real WhatsApp Cloud API |
| Calendar | Mock availability | Real Google Calendar with slot detection |
| CRM | Mock lead creation | Real HubSpot API with deals |
| Payroll | Mock calculation | Real 2024 tax engine |
| Invoice | Mock JSON | Real PDF generation + storage |
| Storage | Memory-only | Firestore persistence |
| Auth | Not implemented | OAuth 2.0 flows |
| Monitoring | Basic logging | Structured traces + metrics |

---

## 5-Minute Setup

### 1. Configure Email (Choose One)

**Gmail OAuth:**
```env
EMAIL_PROVIDER=gmail
GMAIL_OAUTH_CLIENT_ID=xxx.apps.googleusercontent.com
GMAIL_OAUTH_CLIENT_SECRET=secret
```

**SendGrid:**
```env
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=SG.xxxx
```

**SMTP (default):**
```env
EMAIL_PROVIDER=smtp
SMTP_USERNAME=you@gmail.com
SMTP_PASSWORD=app-password
```

### 2. Configure Messaging

```env
WHATSAPP_API_TOKEN=EAAxxxxx
WHATSAPP_BUSINESS_ACCOUNT_ID=123456789
```

### 3. Configure Calendar

```env
CALENDAR_CLIENT_ID=xxx.apps.googleusercontent.com
CALENDAR_CLIENT_SECRET=secret
```

### 4. Configure CRM

```env
CRM_PROVIDER=hubspot
HUBSPOT_API_KEY=pat-na1-xxxxxx
# OR for OAuth:
HUBSPOT_OAUTH_CLIENT_ID=id
HUBSPOT_OAUTH_CLIENT_SECRET=secret
```

### 5. Start Server

```bash
python main.py
```

---

## Common Tasks

### Send Email

```python
from app.services.email_service import get_email_service

svc = get_email_service()
await svc.send_email(
    to_address="user@example.com",
    subject="Hello",
    body_html="<p>Test</p>"
)
```

### Send WhatsApp

```python
from app.services.messaging_service import get_whatsapp_service

svc = get_whatsapp_service()
await svc.send_message("+1234567890", "Hello!")
```

### Create Calendar Event

```python
from app.services.calendar_service import get_google_calendar_service
from datetime import datetime, timedelta

svc = get_google_calendar_service()
await svc.create_event(
    oauth_token=token,
    title="Meeting",
    start_time=datetime.utcnow() + timedelta(days=1),
    end_time=datetime.utcnow() + timedelta(days=1, hours=1),
    attendees=["alice@company.com"]
)
```

### Create CRM Contact

```python
from app.services.crm_service import get_crm_service

svc = get_crm_service()
await svc.create_contact(
    email="john@company.com",
    first_name="John",
    last_name="Doe"
)
```

### Calculate Paycheck

```python
from app.services.payroll_engine import get_payroll_engine
from decimal import Decimal

svc = get_payroll_engine()
paycheck = await svc.calculate_paycheck(
    employee_id="EMP123",
    gross_amount=Decimal("5000"),
    annual_gross=Decimal("130000")
)
```

### Generate Invoice

```python
from app.services.invoice_service import get_invoice_generator, InvoiceLineItem
from decimal import Decimal

svc = get_invoice_generator()
invoice = await svc.generate_invoice(
    client_name="Acme Corp",
    client_email="accounting@acme.com",
    client_address="123 Main St",
    line_items=[
        InvoiceLineItem("Consulting", Decimal("40"), Decimal("150"))
    ]
)
```

### Schedule Background Job

```python
from app.services.scheduler import get_scheduler, JobFrequency
from app.services.scheduler import payroll_cycle_job

scheduler = get_scheduler()
await scheduler.start()

job_id = await scheduler.schedule_job(
    name="Bi-weekly Payroll",
    handler=payroll_cycle_job,
    frequency=JobFrequency.CUSTOM,
    first_run_delay_seconds=3600
)
```

### Track Metrics

```python
from app.utils.observability import get_observability

obs = get_observability()
obs.metrics.record_metric("email_sent", 1.0, tags={"provider": "gmail"})
stats = obs.metrics.get_metric_stats("email_sent")
```

---

## OAuth Flow

### Google OAuth (Gmail + Calendar)

```python
from app.integrations.oauth_manager import get_oauth_manager

oauth = get_oauth_manager()

# 1. Get authorization URL
url = oauth.get_authorization_url("google")
# -> Send to user: https://accounts.google.com/o/oauth2/auth?...

# 2. User authorizes, you get code
authorization_code = "4/..."

# 3. Exchange for token
token = await oauth.exchange_code("google", authorization_code)

# 4. Store token
persistence = get_persistence()
await persistence.store_credential(
    credential_id="gmail_user@example.com",
    provider="gmail",
    credential_data=token.to_dict()
)

# 5. Use in services
email_svc = get_email_service()
await email_svc.send_email(..., oauth_token=token)
```

---

## Environment Variables Reference

### Required for Production

```env
# Firebase (for persistence)
FIREBASE_PROJECT_ID=your-project
FIREBASE_PRIVATE_KEY=...
FIREBASE_CLIENT_EMAIL=...

# Email (at least one)
EMAIL_PROVIDER=smtp|gmail|sendgrid
# ... provider-specific keys

# Messaging
WHATSAPP_API_TOKEN=...
WHATSAPP_BUSINESS_ACCOUNT_ID=...

# Calendar
CALENDAR_CLIENT_ID=...
CALENDAR_CLIENT_SECRET=...

# CRM
CRM_PROVIDER=hubspot
HUBSPOT_API_KEY=...

# Payroll
PAYROLL_TAX_RATE=0.15
HEALTH_INSURANCE=200.0
PENSION_RATE=0.05

# Invoice
INVOICE_BUSINESS_NAME=...
INVOICE_TAX_ID=...

# Scheduler/Observability
MAX_WORKERS=10
LOG_LEVEL=INFO
```

---

## Testing Real Services

### Email

```bash
curl -X POST http://localhost:8000/api/workflows/onboarding/start \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "name": "Test User"}'
```

### Messaging

```bash
curl -X POST http://localhost:8000/webhooks/n8n/onboarding \
  -H "Content-Type: application/json" \
  -d '{"phone": "+1234567890", "name": "Test"}'
```

### Calendar

Visit endpoint that uses calendar service, verify event appears in Google Calendar

### CRM

Visit endpoint that uses CRM service, verify contact appears in HubSpot

---

## Monitoring & Debugging

### Check Health

```python
from app.utils.observability import get_observability

obs = get_observability()
health = obs.get_health_status()
print(health)  # {status, errors, metrics}
```

### View Recent Errors

```python
summary = obs.errors.get_error_summary()
print(summary)  # {total_errors, unique_types, error_counts}
```

### View Service Metrics

```python
stats = obs.metrics.get_metric_stats("email_send_duration_ms")
print(stats)  # {count, min, max, avg, sum}
```

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "Gmail API not found" | Enable Gmail API in Google Cloud Console |
| "WhatsApp token invalid" | Regenerate token in Meta Business Manager |
| "CalendarApiError" | Verify OAuth scopes include calendar.events |
| "HubSpot 401" | Check API key format (should be `pat-na1-...`) |
| "Firestore connection error" | Ensure Firebase credentials in environment |
| "Scheduler not running" | Call `await scheduler.start()` in app startup |

---

## Next Phase (Phase 4)

- [ ] Database query optimization
- [ ] Vector embedding caching
- [ ] Real-time data sync
- [ ] Advanced search
- [ ] Enterprise features

---

**Document Version**: 3.0.0-Quick  
**Last Updated**: February 22, 2026
