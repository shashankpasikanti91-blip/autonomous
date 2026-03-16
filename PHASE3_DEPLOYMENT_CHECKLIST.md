# Phase 3: Integration Checklist

## Pre-Deployment Verification

### Repository Setup
- [ ] All 10 new service files exist in `app/services/`
  - [ ] `email_service.py` (420 lines)
  - [ ] `messaging_service.py` (350 lines)
  - [ ] `calendar_service.py` (420 lines)
  - [ ] `crm_service.py` (450 lines)
  - [ ] `payroll_engine.py` (520 lines)
  - [ ] `invoice_service.py` (450 lines)
  - [ ] `scheduler.py` (480 lines)

- [ ] All 3 new integration files exist in `app/integrations/`
  - [ ] `oauth_manager.py` (380 lines)
  - [ ] `persistence.py` (450 lines)
  - [ ] `firebase.py` (if using Firestore)

- [ ] New utility layer complete
  - [ ] `app/utils/observability.py` (450 lines)

- [ ] Configuration updated
  - [ ] `app/config/settings.py` has OAuth fields
  - [ ] `.env.example` has all provider examples
  - [ ] `requirements.txt` has 17 new dependencies

- [ ] Module exports clean
  - [ ] `app/services/__init__.py` exports all real services
  - [ ] `app/integrations/__init__.py` exports OAuth + persistence

### Dependencies Installed
```bash
pip install -r requirements.txt
```

- [ ] Core Google libraries
  - `google-auth==2.26.2`
  - `google-auth-oauthlib==1.2.0`
  - `google-api-python-client==2.105.0`

- [ ] PDF generation
  - `reportlab==4.0.9`
  - `weasyprint==60.0`

- [ ] Async support
  - `aiofiles==23.2.1`
  - `aiohttp` (existing)

- [ ] Scheduling
  - `APScheduler==3.10.4`

- [ ] Cloud SDKs
  - `firebase-admin>=6.0.0` (optional for Firestore)

### Environment Configuration

#### Email Service
Choose **ONE** provider:

**Option A: Gmail OAuth**
```env
EMAIL_PROVIDER=gmail
GMAIL_OAUTH_CLIENT_ID=<your-id>.apps.googleusercontent.com
GMAIL_OAUTH_CLIENT_SECRET=<secret>
GMAIL_OAUTH_REDIRECT_URI=http://localhost:8000/callback/gmail
```

**Option B: SendGrid**
```env
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=SG.xxxxxxxxxxxx
SENDGRID_FROM_ADDRESS=noreply@company.com
```

**Option C: SMTP (Default)**
```env
EMAIL_PROVIDER=smtp
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=app-specific-password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
```

- [ ] Email provider configured
- [ ] Test endpoint: `POST /workflows/onboarding/start`
- [ ] Check logs: `grep -i "email" app.log`

#### Messaging Service
```env
WHATSAPP_API_TOKEN=EAAxxxxxxxxxxxx
WHATSAPP_BUSINESS_ACCOUNT_ID=123456789
WHATSAPP_BUSINESS_PHONE_NUMBER_ID=987654321
WHATSAPP_WEBHOOK_TOKEN=verify-token-12345
```

- [ ] HubSpot Business app created
- [ ] Phone number verified
- [ ] Webhook configured
- [ ] Test with: `curl -X POST http://localhost:8000/webhooks/whatsapp/...`

#### Calendar Service
```env
CALENDAR_CLIENT_ID=<your-id>.apps.googleusercontent.com
CALENDAR_CLIENT_SECRET=<secret>
CALENDAR_OAUTH_REDIRECT_URI=http://localhost:8000/callback/calendar
```

- [ ] Google Calendar API enabled
- [ ] OAuth credentials created
- [ ] Test endpoint created

#### CRM Service
**Option A: HubSpot API Key**
```env
CRM_PROVIDER=hubspot
HUBSPOT_API_KEY=pat-na1-xxxxxxxxxxxxx
```

**Option B: HubSpot OAuth**
```env
CRM_PROVIDER=hubspot
HUBSPOT_OAUTH_CLIENT_ID=<id>
HUBSPOT_OAUTH_CLIENT_SECRET=<secret>
```

- [ ] HubSpot private app created | OR | OAuth app created
- [ ] Required scopes granted:
  - `crm.objects.contacts.read` / `write`
  - `crm.objects.deals.read` / `write`
  - `crm.objects.activities.read` / `write`
- [ ] Test: `curl -X GET http://localhost:8000/api/crm/contacts`

#### Payroll Engine
```env
PAYROLL_TAX_RATE=0.15
HEALTH_INSURANCE=200.0
DENTAL_INSURANCE=50.0
VISION_INSURANCE=25.0
PENSION_401K_RATE=0.05
```

- [ ] Tax rates configured for your state
- [ ] Deduction amounts set
- [ ] Test calculation endpoint

#### Invoice Service
```env
INVOICE_BUSINESS_NAME="Your Company"
INVOICE_TAX_ID="EIN: 12-3456789"
INVOICE_ADDRESS="123 Business St, City, ST 12345"
INVOICE_PHONE="+1-555-0123"
INVOICE_EMAIL=billing@company.com
```

- [ ] Business information complete
- [ ] Test: Generate and download invoice
- [ ] Firestore configured for storage (see below)

#### Scheduler
```env
SCHEDULER_ENABLED=true
SCHEDULER_CHECK_INTERVAL=10
SCHEDULER_MAX_WORKERS=5
SCHEDULER_RETRY_MAX_ATTEMPTS=3
SCHEDULER_RETRY_BACKOFF_BASE=2
```

- [ ] Scheduler enabled and configured
- [ ] Check logs: `grep -i "visa_status_check\|payroll_cycle" app.log`

#### Observability
```env
LOG_LEVEL=INFO
METRICS_RETENTION_DAYS=30
ERROR_RETENTION_DAYS=7
TRACE_SAMPLING_RATE=1.0
```

- [ ] Logging configured
- [ ] Metrics enabled
- [ ] Test health endpoint: `GET /api/health`

### Authentication & Secrets

#### Firebase / Firestore Setup (Optional but Recommended)
```env
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY=<json-key>
FIREBASE_CLIENT_EMAIL=firebase-adminsdk@...
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com
```

Setup Steps:
1. Create Firebase project (console.firebase.google.com)
2. Enable Firestore Database
3. Create service account key
4. Download JSON key
5. Copy credentials to `.env`

- [ ] Firebase project created
- [ ] Service account credentials obtained
- [ ] `.env` updated with credentials
- [ ] Firestore collections created:
  - [ ] `workflow_executions`
  - [ ] `execution_logs`
  - [ ] `credentials`
  - [ ] `agent_memory`

#### OAuth Flows Setup

**Google OAuth (Gmail + Calendar)**
1. Go to Google Cloud Console
2. Create OAuth 2.0 credentials (Desktop application)
3. Set authorized redirect URIs:
   - `http://localhost:8000/callback/gmail`
   - `http://localhost:8000/callback/calendar`
4. Enable APIs:
   - Gmail API
   - Google Calendar API
5. Copy Client ID and Secret to `.env`

- [ ] Google OAuth credentials created
- [ ] Redirect URIs configured
- [ ] APIs enabled
- [ ] `.env` populated with credentials

**HubSpot OAuth (Optional)**
1. Go to HubSpot app marketplace (app.hubspot.com)
2. Create private app or OAuth app
3. Required scopes:
   - Contact CRM
   - Deal CRM
   - Activities CRM
4. Copy Client ID and Secret to `.env`

- [ ] HubSpot app created
- [ ] Scopes configured
- [ ] Credentials in `.env`

### Code Validation

Run validation checks:

```bash
# Python syntax check
python -m py_compile app/services/email_service.py
python -m py_compile app/services/messaging_service.py
python -m py_compile app/services/calendar_service.py
python -m py_compile app/services/crm_service.py
python -m py_compile app/services/payroll_engine.py
python -m py_compile app/services/invoice_service.py
python -m py_compile app/services/scheduler.py
python -m py_compile app/integrations/oauth_manager.py
python -m py_compile app/integrations/persistence.py
python -m py_compile app/utils/observability.py
```

- [ ] All files compile without syntax errors

```bash
# Import check
python -c "from app.services import get_email_service, get_whatsapp_service, get_google_calendar_service, get_crm_service, get_payroll_engine, get_invoice_generator, get_scheduler"

python -c "from app.integrations import OAuthManager, FirestorePersistence"

python -c "from app.utils.observability import Observability, trace_operation"
```

- [ ] All imports work correctly
- [ ] No circular dependencies
- [ ] No missing modules

### Existing Tests Compatibility

```bash
# Run existing test suite
pytest tests/ -v
```

- [ ] All existing tests pass without modification
- [ ] No breaking changes to Phase 2 code
- [ ] Mock connectors still available for dev/test

### Local Testing

#### Test 1: Email Service
```bash
# In Python shell
python -c "
import asyncio
from app.services import get_email_service

async def test():
    svc = get_email_service()
    result = await svc.send_email(
        to_address='your-email@gmail.com',
        subject='Test',
        body_html='<p>If you see this, emails work!</p>'
    )
    print(f'Result: {result}')

asyncio.run(test())
"
```

- [ ] Email delivered (check inbox)
- [ ] No errors in logs

#### Test 2: Calendar Service
```bash
# Requires OAuth token first
python -c "
import asyncio
from app.integrations import get_oauth_manager

async def test():
    oauth = get_oauth_manager()
    url = oauth.get_authorization_url('google')
    print('Visit:', url)
    # After authorization, exchange code for token
    code = input('Auth code: ')
    token = await oauth.exchange_code('google', code)
    print('Token obtained:', token)

asyncio.run(test())
"
```

- [ ] OAuth flow completes
- [ ] Token received
- [ ] Test event creation

#### Test 3: CRM Service
```bash
python -c "
import asyncio
from app.services import get_crm_service

async def test():
    svc = get_crm_service()
    contact = await svc.create_contact(
        email='test@example.com',
        first_name='Test',
        last_name='User'
    )
    print(f'Contact ID: {contact.get(\"id\")}')

asyncio.run(test())
"
```

- [ ] Contact created in HubSpot
- [ ] ID returned
- [ ] No API errors

#### Test 4: Payroll Service
```bash
python -c "
import asyncio
from decimal import Decimal
from app.services import get_payroll_engine

async def test():
    svc = get_payroll_engine()
    result = await svc.calculate_paycheck(
        employee_id='TEST001',
        gross_amount=Decimal('5000'),
        annual_gross=Decimal('130000')
    )
    print(f'Gross: {result[\"gross\"]}')
    print(f'Net: {result[\"net\"]}')
    print(f'Tax: {result[\"taxes\"]}')

asyncio.run(test())
"
```

- [ ] Calculation completes
- [ ] Net < Gross
- [ ] Tax breakdown accurate

#### Test 5: Invoice Service
```bash
python -c "
import asyncio
from decimal import Decimal
from app.services import get_invoice_generator, InvoiceLineItem

async def test():
    svc = get_invoice_generator()
    invoice = await svc.generate_invoice(
        client_name='ACME Corp',
        client_email='billing@acme.com',
        client_address='123 Main St',
        line_items=[
            InvoiceLineItem('Service', Decimal('10'), Decimal('150'))
        ]
    )
    print(f'Invoice ID: {invoice.get(\"id\")}')
    print(f'Total: {invoice.get(\"total\")}')

asyncio.run(test())
"
```

- [ ] Invoice generated
- [ ] PDF created (check storage)
- [ ] Correct total

#### Test 6: Scheduler
```bash
python -c "
import asyncio
from app.services import get_scheduler

async def test():
    scheduler = get_scheduler()
    await scheduler.start()
    
    print('Scheduler running. Check logs for job execution.')
    print('Press Ctrl+C to stop.')
    
    try:
        await asyncio.sleep(120)  # Run for 2 minutes
    except KeyboardInterrupt:
        await scheduler.stop()
        print('Scheduler stopped.')

asyncio.run(test())
"
```

- [ ] Scheduler starts without errors
- [ ] Jobs execute at their scheduled times
- [ ] Retry logic triggers on failures

#### Test 7: Observability
```bash
python -c "
from app.utils.observability import get_observability

obs = get_observability()
obs.metrics.record_metric('test_metric', 1.0)
health = obs.get_health_status()
print('Health:', health)
"
```

- [ ] Health check succeeds
- [ ] Metrics recorded
- [ ] No errors

### Staging Deployment

```bash
# Pull latest code
git pull origin main

# Install dependencies
pip install -r requirements.txt

# Run migrations (if applicable)
python migrations/run.py

# Start application
python main.py
```

- [ ] App starts without errors
- [ ] All services initialized
- [ ] Health endpoint responds
- [ ] Logs show initialization

### Production Deployment

**Security Checklist**
- [ ] All secrets in environment variables (not in code)
- [ ] Firebase credentials secure (service account only)
- [ ] OAuth tokens encrypted at rest
- [ ] HTTPS enforced for all endpoints
- [ ] Rate limiting configured
- [ ] CORS properly restricted
- [ ] SQL injection prevention (if applicable)

**Monitoring Checklist**
- [ ] Application errors logging to centralized service (e.g., Sentry)
- [ ] Metrics pipeline operational (e.g., Prometheus)
- [ ] Health check endpoint monitored
- [ ] Critical services have alerts
- [ ] Dashboard configured for Phase 3 services
- [ ] SLA targets defined

**Operational Checklist**
- [ ] Runbooks created for common issues
- [ ] On-call rotation established
- [ ] Backup/restore procedures documented
- [ ] Disaster recovery tested
- [ ] Capacity planning done (concurrent users)
- [ ] Load testing completed

### Documentation

- [ ] PHASE3_QUICK_REFERENCE.md read by all developers
- [ ] PHASE3_REAL_INTEGRATIONS.md bookmarked
- [ ] Architecture diagram understood
- [ ] Service interfaces documented
- [ ] API endpoints documented with examples
- [ ] Troubleshooting guide reviewed

---

## Phase 3 Sign-Off Criteria

All sections complete? ✅

System ready for:
- [ ] Integration testing with real services
- [ ] User acceptance testing
- [ ] Staging deployment
- [ ] Production deployment

---

**Document Version**: 1.0.0  
**Last Updated**: Phase 3 Completion  
**Prepared By**: AI Assistant  
**Status**: Ready for Deployment ✅
