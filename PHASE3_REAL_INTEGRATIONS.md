# Phase 3: Real External Service Integration Guide

**Version**: 3.0.0 - Production Real Integration  
**Date**: February 22, 2026  
**Status**: ✅ Implementation Complete

## Overview

This document explains how to set up and integrate real external services to replace mock implementations. Phase 3 replaces all mock connectors with production-grade real service implementations with full OAuth support, persistence, and observability.

### What's New in Phase 3

- ✅ **Real Email Service** - Gmail API, SendGrid, SMTP with OAuth support
- ✅ **Real Messaging** - WhatsApp Cloud API for business messaging
- ✅ **Real Calendar** - Google Calendar API with availability detection
- ✅ **Real CRM** - HubSpot API with lead management
- ✅ **Real Payroll Engine** - Tax calculations with 2024 rates, deductions
- ✅ **Real Invoice Generation** - PDF creation with storage
- ✅ **Background Scheduler** - Async job processing with retry logic
- ✅ **Observability** - Structured logging, metrics, error tracking
- ✅ **Persistence Layer** - Firestore state and credential storage
- ✅ **OAuth Framework** - OAuth 2.0 support for Google and HubSpot

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
├─────────────────────────────────────────────────────────────┤
│ API Endpoints (6 workflows + N8N webhooks)                  │
├─────────────────────────────────────────────────────────────┤
│            Orchestration Service                             │
│  (Task Routing, Retry Logic, Execution Strategies)          │
├─────────────────────────────────────────────────────────────┤
│              Service Integration Layer                       │
│  ┌──────────────┬──────────────┬──────────────┐             │
│  │Email Service │Messaging Svc │Calendar Svc  │             │
│  │  (Gmail API) │  (WhatsApp)  │(Google Cal)  │             │
│  └──────────────┴──────────────┴──────────────┘             │
│  ┌──────────────┬──────────────┬──────────────┐             │
│  │ CRM Service  │ Payroll Eng  │Invoice Svc   │             │
│  │  (HubSpot)   │ (Tax Calcs)  │(PDF Gen)     │             │
│  └──────────────┴──────────────┴──────────────┘             │
├─────────────────────────────────────────────────────────────┤
│              Supporting Services                             │
│  ┌──────────────┬──────────────┬──────────────┐             │
│  │OAuth Manager │ Persistence  │ Scheduler    │             │
│  │              │ (Firestore)  │(Async Jobs)  │             │
│  └──────────────┴──────────────┴──────────────┘             │
│  ┌──────────────────────────────────────────┐               │
│  │    Observability (Logging, Metrics,     │ │               │
│  │    Tracing, Error Tracking)              │               │
│  └──────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

---

## Service Setup Guide

### 1. Email Service Setup

#### Option A: Gmail API (Recommended for Automated Sending)

**Prerequisites:**
- Google Cloud Project
- Gmail API enabled
- Service Account or OAuth credentials

**Setup Steps:**

1. **Create a Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create new project
   - Enable Gmail API
   - Create Service Account (for automation) or OAuth 2.0 Credentials (for user delegation)

2. **For OAuth (Recommended):**
   ```bash
   # In Google Cloud Console:
   # 1. Create "Desktop application" OAuth credentials
   # 2. Set redirect URI to: http://localhost:8000/auth/callback/google
   # 3. Download credentials JSON
   ```

3. **Environment Setup:**
   ```env
   EMAIL_PROVIDER=gmail
   GMAIL_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GMAIL_OAUTH_CLIENT_SECRET=your-client-secret
   GMAIL_FROM_ADDRESS=noreply@company.com
   ```

4. **OAuth Token Exchange:**
   ```python
   from app.integrations.oauth_manager import get_oauth_manager
   
   oauth_mgr = get_oauth_manager()
   # Get user to visit: oauth_mgr.get_authorization_url("google")
   # Exchange code for token:
   # token = await oauth_mgr.exchange_code("google", authorization_code)
   ```

#### Option B: SendGrid (Recommended for High Volume)

**Setup:**
```env
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=SG.your-api-key
SENDGRID_FROM_ADDRESS=noreply@company.com
```

**Get API Key:**
- Sign up at [SendGrid](https://sendgrid.com)
- Generate API key in Settings → API Keys
- Verify sender identity

#### Option C: SMTP (Always Available)

```env
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Use App Password, not regular password
SMTP_FROM_ADDRESS=noreply@company.com
```

**Usage:**
```python
from app.services.email_service import get_email_service

email_svc = get_email_service()
result = await email_svc.send_email(
    to_address="user@example.com",
    subject="Hello",
    body_html="<p>Email body</p>",
    oauth_token=token  # If using Gmail OAuth
)
```

---

### 2. WhatsApp Messaging Setup

**Prerequisites:**
- Meta Business Account
- WhatsApp Business App
- Phone number verification

**Setup Steps:**

1. **Get WhatsApp Business API Credentials:**
   - Go to [Meta for Business](https://business.facebook.com)
   - Create Business App
   - Add WhatsApp product
   - Verify phone number
   - Get Business Account ID and API token

2. **Environment Setup:**
   ```env
   WHATSAPP_API_TOKEN=your-graph-api-token
   WHATSAPP_BUSINESS_ACCOUNT_ID=123456789
   ```

3. **Create Message Templates** (in Meta App Manager):
   - Create templates for common messages
   - Get template names: ONBOARDING_WELCOME, INVOICE_SENT, etc.

4. **Usage:**
   ```python
   from app.services.messaging_service import get_whatsapp_service
   
   whatsapp_svc = get_whatsapp_service()
   
   # Send single message
   result = await whatsapp_svc.send_message(
       phone_number="+1234567890",
       message_text="Hello from automated system!"
   )
   
   # Send template message
   result = await whatsapp_svc.send_template_message(
       phone_number="+1234567890",
       template_name="ONBOARDING_WELCOME",
       template_variables=["John Doe", "Company Name"]
   )
   ```

---

### 3. Google Calendar Setup

**Prerequisites:**
- Google Cloud Project (can use same as Gmail)
- Calendar API enabled
- OAuth credentials

**Setup:**

```env
CALENDAR_PROVIDER=google
CALENDAR_CLIENT_ID=your-client-id.apps.googleusercontent.com
CALENDAR_CLIENT_SECRET=your-client-secret
```

**Usage:**
```python
from app.services.calendar_service import get_google_calendar_service
from datetime import datetime, timedelta

cal_svc = get_google_calendar_service()

# Create event
event = await cal_svc.create_event(
    oauth_token=oauth_token,
    title="Team Meeting",
    start_time=datetime.utcnow() + timedelta(days=1),
    end_time=datetime.utcnow() + timedelta(days=1, hours=1),
    attendees=["alice@company.com", "bob@company.com"]
)

# Find available slots
slots = await cal_svc.find_available_slots(
    oauth_token=oauth_token,
    attendees=["alice@company.com", "bob@company.com"],
    duration_minutes=60
)
```

---

### 4. HubSpot CRM Setup

**Prerequisites:**
- HubSpot Account (free tier available)
- Private App key or OAuth credentials

**Setup Step 1: Get API Key**

Option A: Private App (Simple, for internal use)
```
1. Go to HubSpot Dashboard → Settings → Integrations → Private Apps
2. Create Private App with scopes:
   - crm.objects.contacts.read
   - crm.objects.contacts.write
   - crm.objects.deals.read
   - crm.objects.deals.write
3. Copy API key
```

Option B: OAuth (For user delegation)
```
1. Create OAuth app in HubSpot
2. Set redirect URI: http://localhost:8000/auth/callback/hubspot
3. Copy Client ID and Secret
```

**Environment Setup:**
```env
CRM_PROVIDER=hubspot
# Option A: Private App
HUBSPOT_API_KEY=pat-na1-your-private-app-key

# Option B: OAuth
HUBSPOT_OAUTH_CLIENT_ID=your-client-id
HUBSPOT_OAUTH_CLIENT_SECRET=your-client-secret
```

**Usage:**
```python
from app.services.crm_service import get_crm_service

crm_svc = get_crm_service()

# Create contact
contact = await crm_svc.create_contact(
    email="john@company.com",
    first_name="John",
    last_name="Doe",
    phone="+1234567890",
    company="Acme Inc",
    job_title="Manager"
)

# Create deal
deal = await crm_svc.create_deal(
    deal_name="Q1 Contract",
    contact_id=contact["contact_id"],
    amount=50000.00,
    deal_stage="negotiation"
)

# Log activity
await crm_svc.log_activity(
    contact_id=contact["contact_id"],
    activity_type="CALL",
    activity_subject="Initial Discovery Call",
    notes="Discussed requirements"
)
```

---

### 5. Payroll Engine Setup

**Configuration:**
```env
PAYROLL_TAX_RATE=0.15          # Federal tax rate
HEALTH_INSURANCE=200.00         # Monthly health insurance deduction
PENSION_RATE=0.05               # 401k/Pension contribution rate
```

**Tax Rates (2024):**
- Federal: Progressive brackets (10%-37%)
- Social Security: 6.2% up to $168,600
- Medicare: 1.45% + 0.9% additional on income over $200k
- State: Varies by location

**Usage:**
```python
from app.services.payroll_engine import get_payroll_engine, PayrollDeduction
from decimal import Decimal

payroll_svc = get_payroll_engine()

# Calculate paycheck
paycheck = await payroll_svc.calculate_paycheck(
    employee_id="EMP123",
    gross_amount=Decimal("5000"),
    annual_gross=Decimal("130000"),
    pay_period="bi-weekly",
    state_residence="CA"
)
# Returns: fedtax, fica, state_tax, deductions, net_pay

# Process payment
payment = await payroll_svc.process_payment(
    employee_id="EMP123",
    amount=paycheck["net_pay"],
    payment_method="direct_deposit",
    bank_account="****1234"
)
```

---

### 6. Invoice Generation Setup

**Configuration:**
```env
INVOICE_BUSINESS_NAME=Acme Corporation
INVOICE_TAX_ID=12-3456789
INVOICE_PREFIX=INV
INVOICE_PAYMENT_TERMS_DAYS=30
```

**Usage:**
```python
from app.services.invoice_service import get_invoice_generator, InvoiceLineItem
from decimal import Decimal

invoice_svc = get_invoice_generator()

# Create invoice
invoice = await invoice_svc.generate_invoice(
    client_name="Client Corp",
    client_email="accounting@client.com",
    client_address="123 Main St, City, ST 12345",
    line_items=[
        InvoiceLineItem(
            description="Consulting Services",
            quantity=Decimal("40"),
            unit_price=Decimal("150"),
            tax_rate=Decimal("0.1")
        ),
        InvoiceLineItem(
            description="Software License",
            quantity=Decimal("1"),
            unit_price=Decimal("5000"),
            tax_rate=Decimal("0.1")
        )
    ]
)

# Send invoice to client
sent = await invoice_svc.send_invoice(
    invoice_number=invoice["invoice_number"],
    client_email="accounting@client.com",
    client_name="Client Corp"
)
```

---

### 7. Background Scheduler Setup

Jobs automatically handle recurring tasks like:
- Visa status monitoring (daily)
- Payroll cycle processing (bi-weekly/monthly)
- Follow-up reminders (daily)
- Sales lead nurturing (hourly)

**Usage:**
```python
from app.services.scheduler import (
    get_scheduler, JobFrequency, visa_status_check_job
)

scheduler = get_scheduler()

# Start scheduler
await scheduler.start()

# Schedule visa monitoring
job_id = await scheduler.schedule_job(
    name="Daily Visa Status Check",
    handler=visa_status_check_job,
    frequency=JobFrequency.DAILY,
    first_run_delay_seconds=60
)

# Monitor job status
status = scheduler.get_job_status(job_id)

# Stop scheduler
await scheduler.stop()
```

---

### 8. Persistence Layer Setup

Firestore automatically persists:
- Workflow execution state
- Execution logs and audit trail
- Agent memory
- API credentials

**Initialize Firebase:**

```python
from app.integrations.persistence import get_persistence

persistence = get_persistence()

# Store workflow execution
execution = WorkflowExecution(
    execution_id="exec_123",
    workflow_id="onboarding",
    status="running",
    input_data={"employee_id": "EMP456"}
)
await persistence.store_workflow_execution(execution)

# Store credentials
await persistence.store_credential(
    credential_id="gmail_oauth_user1",
    provider="gmail",
    credential_data={"token": oauth_token.to_dict()},
    user_id="user123"
)

# Retrieve stored data
exec_record = await persistence.get_workflow_execution("exec_123")
cred_data = await persistence.get_credential("gmail_oauth_user1")
```

---

### 9. OAuth Authentication Flow

**For Gmail and Google Calendar:**

```python
from app.integrations.oauth_manager import get_oauth_manager

async def handle_oauth_flow():
    oauth_mgr = get_oauth_manager()
    
    # Step 1: Get authorization URL
    auth_url = oauth_mgr.get_authorization_url("google", state="state123")
    # -> Redirect user to this URL
    
    # Step 2: User authorizes and is redirected with code
    # Step 3: Exchange code for token
    token = await oauth_mgr.exchange_code("google", authorization_code)
    
    # Step 4: Store token persistently
    persistence = get_persistence()
    await persistence.store_credential(
        credential_id="gmail_user@example.com",
        provider="gmail",
        credential_data=token.to_dict(),
        user_id="user_id"
    )
    
    # Step 5: Use token in service calls
    email_svc = get_email_service()
    await email_svc.send_email(
        to_address="recipient@example.com",
        subject="Test",
        body_html="<p>Test</p>",
        oauth_token=token
    )
```

---

### 10. Observability Setup

**Structured Logging:**
```python
from app.utils.observability import get_observability, trace_operation

obs = get_observability()

async with trace_operation("email_service", "send_email", user_id="user123") as trace:
    trace.add_event("initialized", {"provider": "gmail"})
    
    try:
        result = await email_svc.send_email(...)
        trace.add_event("sent", {"message_id": result["message_id"]})
    except Exception as e:
        trace.set_error(str(e))
        raise
```

**Metrics Collection:**
```python
obs.metrics.record_metric(
    "email_send_duration_ms",
    duration_ms,
    tags={"provider": "gmail", "status": "success"}
)

stats = obs.metrics.get_metric_stats("email_send_duration_ms")
# Returns: {count, min, max, avg, sum}
```

**Error Tracking:**
```python
obs.errors.record_error(
    error_type="GmailAPIError",
    error_message="Failed to authenticate",
    context={"retry_count": 1},
    severity="error"
)

summary = obs.errors.get_error_summary()
# Returns: {total_errors, unique_types, error_counts, most_common}
```

**System Health:**
```python
health = obs.get_health_status()
# {
#   "status": "healthy | degraded",
#   "errors": {...},
#   "recent_traces": 15,
#   "metrics_recorded": 42
# }
```

---

## Testing Real Integrations

### 1. Email Service Test

```bash
curl -X POST http://localhost:8000/api/workflows/email/send \
  -H "Content-Type: application/json" \
  -d '{
    "to_address": "test@example.com",
    "subject": "Test Email",
    "body": "This is a test"
  }'
```

### 2. WhatsApp Test

```python
import asyncio
from app.services.messaging_service import get_whatsapp_service

async def test():
    svc = get_whatsapp_service()
    result = await svc.send_message(
        phone_number="+1234567890",
        message_text="Test from automation"
    )
    print(result)

asyncio.run(test())
```

### 3. Calendar Test

```python
import asyncio
from datetime import datetime, timedelta
from app.services.calendar_service import get_google_calendar_service
from app.integrations.oauth_manager import get_oauth_manager

async def test():
    oauth_mgr = get_oauth_manager()
    token = await oauth_mgr.exchange_code("google", code_from_user)
    
    cal_svc = get_google_calendar_service()
    event = await cal_svc.create_event(
        oauth_token=token,
        title="Test Event",
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=1, hours=1),
        attendees=["attendee@example.com"]
    )
    print(event)

asyncio.run(test())
```

---

## Troubleshooting

### Gmail API Issues

**"Invalid credentials" error:**
- Verify Client ID/Secret match
- Check OAuth redirect URI matches exactly
- Ensure gmail.send scope included

**"Rate limit exceeded":**
- Gmail API limits to 5000 emails/day for service accounts
- Use SendGrid for high volume
- Implement exponential backoff (already built in)

### HubSpot Issues

**"Invalid API key":**
- Generate new private app key
- Verify no spaces in key
- Check app has required scopes

**"Contact not found":**
- Email must be exact match
- Try searching first: `search_contacts(email)`

### Calendar Issues

**"Delegate user declined":**
- User must accept OAuth consent screen
- Check calendar permissions in Google account

**"No availability found":**
- Ensure attendees have shared calendars
- Verify time zone settings

---

## Production Deployment Checklist

- [ ] All OAuth credentials in secure environment variables
- [ ] Firebase Admin SDK properly configured
- [ ] Email templates tested with real service
- [ ] Workflow execution state persisted
- [ ] Scheduler started on app initialization
- [ ] Observability metrics enabled
- [ ] Error tracking configured
- [ ] Backups for Firestore data set up
- [ ] Rate limits understood for each service
- [ ] Monitoring alerts configured
- [ ] Incident response playbooks ready

---

##  Phase 4 Next Steps

Phase 4 will add:
1. ✅ ~~Real integrations~~ → DONE
2. Database optimization and query caching
3. Advanced vector embeddings and semantic search
4. Real-time collaboration features
5. Enterprise audit logging

---

## Support

For integration issues:
1. Check logs: `app/utils/observability.py`
2. Review service-specific configuration
3. Test with provided examples
4. Check service provider documentation
5. Contact support with trace IDs from observability layer

---

**Version**: 3.0.0 - Production Real Integration  
**Last Updated**: February 22, 2026  
**Status**: ✅ Production Ready
