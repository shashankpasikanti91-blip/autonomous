# Phase 4: Integration Adapter Quick Reference

**TL;DR**: All providers now have unified resilient adapters with automatic retry, rate limiting, and health monitoring.

---

## 1. Use Any Adapter

```python
from app.integrations.adapters import (
    get_email_adapter,
    get_messaging_adapter,
    get_calendar_adapter,
    get_crm_adapter,
)

# All adapters have same interface
response = await adapter.call(
    operation="operation_name",
    parameters={...},
    correlation_id="req-123"
)

if response.success:
    print(response.data)
else:
    print(response.error.message)
    print(f"Retryable: {response.error.is_retryable}")
```

### Supported Operations Per Adapter

**EmailAdapter**
- `send_email` - Send single email
- `send_batch_emails` - Send templated batch

**MessagingAdapter**
- `send_message` - Send SMS/WhatsApp text
- `send_template_message` - Send template
- `get_message_status` - Check delivery

**CalendarAdapter**
- `create_event` - Create calendar event
- `find_available_slots` - Find free time
- `update_event` - Modify event
- `delete_event` - Remove event

**CRMAdapter**
- `create_contact` - Create contact
- `get_contact` - Fetch contact
- `update_contact` - Update contact
- `create_deal` - Create deal
- `log_activity` - Log call/email/meeting
- `search_contacts` - Search by query

---

## 2. Error Handling

```python
from app.integrations.adapters import (
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)

response = await adapter.call(...)

# Check error type
if isinstance(response.error, ProviderAuthError):
    # Need new credentials
    pass
elif isinstance(response.error, ProviderRateLimitError):
    # Rate limited, try again later
    pass
elif response.error.is_transient():
    # Transient error, will auto-retry
    pass
elif response.error.should_fallback():
    # Should try fallback provider
    pass
```

---

## 3. Monitor Provider Health

```python
from app.integrations import get_health_monitor, get_email_adapter

monitor = get_health_monitor()

# Register adapters for monitoring
monitor.register_adapter(get_email_adapter())

# Start periodic health checks (60-second interval)
await monitor.start()

# Check status anytime
if monitor.is_provider_healthy("email"):
    print("Email ready!")

if monitor.is_provider_degraded("crm_hubspot"):
    print("CRM degraded - using fallback")

# Get system-wide health
health = monitor.get_overall_health()
print(f"Status: {health['status']}")  # healthy, degraded, critical
```

---

## 4. Use Sandbox Mode for Testing

```python
from app.integrations.sandbox import (
    SandboxMode,
    set_sandbox_mode,
    get_mock_email_provider,
)

# Enable mock providers
set_sandbox_mode(SandboxMode.SANDBOX)

# Now all adapters use mocks (no real API calls)
response = await adapter.call(...)

# Inspect what happened in test
mock = get_mock_email_provider()
emails = mock.get_sent_emails()
assert len(emails) == 1
assert emails[0]["to"] == "user@test.com"

# Reset between tests
from app.integrations.sandbox import reset_all_mocks
reset_all_mocks()
```

---

## 5. Check Provider Metrics

```python
from app.integrations import get_integration_telemetry

telemetry = get_integration_telemetry()

# Get provider metrics
metrics = telemetry.get_metrics("email")
print(f"Success rate: {metrics.success_rate:.1%}")
print(f"Avg latency: {metrics.avg_latency_ms:.0f}ms")
print(f"Reliability: {metrics.reliability_score:.2f}/1.0")

# Get operation-specific stats
stats = telemetry.get_operation_stats("crm_hubspot", "create_contact")
print(f"Latency: {stats['avg_ms']:.0f}ms ± {stats['stdev_ms']:.0f}ms")

# See recent errors
events = telemetry.get_provider_events(
    provider="email",
    operation="send_email",
    limit=10
)
for event in events[-3:]:  # Last 3
    print(f"{event.timestamp}: {event.error_message}")

# Reliability ranking
for provider, score in telemetry.get_reliability_ranking():
    print(f"{provider}: {score:.2f}/1.0")
```

---

## 6. Manage Credentials

```python
from app.integrations import get_credential_manager, Credential
from datetime import datetime, timedelta

manager = get_credential_manager()

# Store credential
cred = Credential(
    credential_id="user_gmail_123",
    provider="gmail",
    access_token="ya29.abc123",
    refresh_token="1//xyz",
    expires_at=datetime.utcnow() + timedelta(hours=1),
)
await manager.store_credential(cred)

# Get (auto-refreshes if expired)
token = await manager.get_credential("user_gmail_123")

# Check what's expiring soon
expiring = await manager.get_expiring_soon(seconds=3600)
for cred in expiring:
    print(f"⚠️  {cred.credential_id} expires in 1 hour")

# Rotate to new credential
new_cred = Credential(...)
await manager.rotate_credential("user_gmail_123", new_cred)

# Stats
stats = manager.get_stats()
print(f"Total credentials: {stats['total_credentials']}")
```

---

## 7. API Response Structure

```python
@dataclass
class AdapterResponse:
    success: bool                           # Operation succeeded
    data: Any                               # Result on success
    error: Optional[AdapterError]          # Error on failure
    operation_took_seconds: float          # Latency
    correlation_id: str                    # For tracing
    retry_count: int                       # Retries performed

# Example:
response = await adapter.call(...)
```

---

## 8. Error Types

All inherit from `AdapterError`:

| Error Type | Category | Retryable | Example |
|-----------|----------|-----------|---------|
| `ProviderAuthError` | AUTHENTICATION | ❌ | Invalid API key, 401 |
| `ProviderRateLimitError` | RATE_LIMIT | ✅ | 429 Too Many Requests |
| `ProviderConnectionError` | SERVICE_UNAVAILABLE | ✅ | Connection refused |
| `ProviderTimeoutError` | SERVICE_UNAVAILABLE | ✅ | Timeout after 30s |
| `ProviderValidationError` | VALIDATION | ❌ | Missing required field |
| `ProviderNotFoundError` | NOT_FOUND | ❌ | 404 Resource not found |
| `ProviderConflictError` | CONFLICT | ✅ | 409 State conflict |

---

## 9. Configuration

### Environment Variables

```env
# Retry behavior
ADAPTER_RETRY_MAX_ATTEMPTS=3

# Health monitoring
HEALTH_CHECK_INTERVAL_SECONDS=60
HEALTH_DEGRADED_THRESHOLD=3

# Sandbox mode
SANDBOX_MODE=production  # or sandbox, hybrid

# Telemetry
TELEMETRY_RETENTION_HOURS=24
```

### Presets

```python
from app.integrations.adapters import (
    CONSERVATIVE_RETRY,      # 2 attempts
    MODERATE_RETRY,          # 3 attempts (default)
    AGGRESSIVE_RETRY,        # 5 attempts
    VERY_AGGRESSIVE_RETRY,   # 10 attempts
)

from app.integrations.adapters import (
    GMAIL_RATE_LIMIT,        # 10 req/s
    HUBSPOT_RATE_LIMIT,      # 10 req/s
    WHATSAPP_RATE_LIMIT,     # 10 req/s
)
```

---

## 10. Common Patterns

### Send Email with Fallback

```python
adapter = get_email_adapter()
response = await adapter.call(
    operation="send_email",
    parameters={...}
)
# If Gmail fails → SendGrid tried → SMTP tried (automatic)
```

### Create Contact with Retry

```python
adapter = get_crm_adapter()
response = await adapter.call(
    operation="create_contact",
    parameters={...}
)
# If HubSpot API timeout → auto-retry 2 more times with backoff
```

### Find Available Time Slots

```python
adapter = get_calendar_adapter()
response = await adapter.call(
    operation="find_available_slots",
    parameters={
        "oauth_token": token,
        "start_time": datetime.now(),
        "end_time": datetime.now() + timedelta(days=7),
        "duration_minutes": 60,
        "attendee_emails": ["alice@company.com"]
    }
)
if response.success:
    slots = response.data  # List of available time blocks
```

### Test with Sandbox

```python
# In test
from app.integrations.sandbox import set_sandbox_mode, SandboxMode
set_sandbox_mode(SandboxMode.SANDBOX)

response = await adapter.call(...)  # Uses mock

# Mock provides what was "sent"
from app.integrations.sandbox import get_mock_email_provider
mock = get_mock_email_provider()
assert mock.get_sent_emails()  # Can inspect
```

---

## 11. Troubleshooting

| Issue | Solution |
|-------|----------|
| Provider keeps failing | `monitor.get_health_status("provider")` - Check status |
| Rate limited | Check `rate_limiter.get_available()` or increase limit |
| Auth failing | Check credentials not expired: `cred.is_expired()` |
| Want to test without API calls | `set_sandbox_mode(SandboxMode.SANDBOX)` |
| Want to see what happened | `telemetry.get_provider_events()` - Query events |
| Credential about to expire | `manager.get_expiring_soon()` - Find soon-expiring |

---

## 12. For Advanced Users

### Custom Retry Policy

```python
from app.integrations.adapters import (
    RetryPolicy,
    RetryStrategy,
    ProviderRetryConfig,
)

custom_policy = RetryPolicy(
    max_attempts=5,
    base_delay_seconds=0.5,
    max_delay_seconds=60.0,
    strategy=RetryStrategy.EXPONENTIAL,
    jitter=0.1,
)

retry_config = ProviderRetryConfig(
    default=custom_policy,
    overrides={
        "send_batch_emails": custom_policy,
    }
)

adapter = EmailAdapter(retry_config=retry_config)
```

### Custom Rate Limit

```python
from app.integrations.adapters import RateLimitConfig

config = RateLimitConfig(
    requests_per_second=20.0,  # 20 req/s
    burst_size=100,            # Allow bursts up to 100
    per_operation={
        "expensive_op": 5.0,   # Only 5/s for this one
    }
)

adapter = EmailAdapter(rate_limit_config=config)
```

### Register Refresh Callback

```python
from app.integrations import get_credential_manager

manager = get_credential_manager()

async def refresh_gmail(credential):
    """Custom refresh logic for Gmail."""
    # Call your OAuth flow
    new_cred = await oauth_manager.refresh_token(credential)
    return new_cred

manager.register_refresh_callback("gmail", refresh_gmail)

# Now credentials auto-refresh before expiration
```

---

## Status

✅ All integrations hardened with:
- Automatic retry & exponential backoff
- Rate limit protection
- Health monitoring
- Credential lifecycle
- Event telemetry
- Sandbox testing support

🚀 Ready for production use without additional configuration
