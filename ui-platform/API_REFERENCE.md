# Phase 8 UI Platform - API Integration Guide

Complete API documentation for the SRP Autonomous OS UI Platform integration with Phase 7 backend.

## Overview

The UI Platform communicates with Phase 7 via a clean REST API interface. All endpoints require:
- Bearer token authentication
- X-Tenant-ID header for multi-tenant operations
- JSON content type

## Base URL

```
Development:  http://localhost:8000/platform/ui
Production:   https://api.yourdomain.com/platform/ui
```

## Authentication Endpoints

### 1. Login

**POST** `/platform/ui/login`

Request:
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "tenant_id": "optional-tenant-id"
}
```

Response:
```json
{
  "status": "success",
  "data": {
    "user": {
      "user_id": "user_123",
      "email": "user@example.com",
      "name": "John Doe",
      "role": "admin",
      "created_at": "2024-01-01T00:00:00Z",
      "mfa_enabled": false
    },
    "tenant": {
      "tenant_id": "tenant_456",
      "organization_name": "Acme Corp",
      "status": "active",
      "subscription_plan": "professional"
    },
    "token": {
      "access_token": "eyJhbGc...",
      "token_type": "Bearer",
      "expires_in": 3600
    }
  }
}
```

### 2. Validate Token

**POST** `/platform/ui/auth/validate`

Headers:
```
Authorization: Bearer {token}
```

Response:
```json
{
  "status": "success",
  "data": {
    "user_id": "user_123",
    "email": "user@example.com",
    "role": "admin"
  }
}
```

### 3. Refresh Token

**POST** `/platform/ui/auth/refresh`

Request:
```json
{
  "refresh_token": "refresh_token_value"
}
```

Response:
```json
{
  "status": "success",
  "data": {
    "access_token": "new_token",
    "token_type": "Bearer",
    "expires_in": 3600
  }
}
```

## Tenant Endpoints

### 1. Get Current Tenant

**GET** `/platform/ui/tenant`

Headers:
```
Authorization: Bearer {token}
X-Tenant-ID: {tenant-id}
```

Response:
```json
{
  "status": "success",
  "data": {
    "tenant_id": "tenant_123",
    "organization_name": "Acme Corp",
    "status": "active",
    "subscription_plan": "professional",
    "owner_email": "owner@example.com",
    "created_at": "2024-01-01T00:00:00Z",
    "quota": {
      "quota_id": "quota_123",
      "max_apps": 500,
      "max_workflows_per_app": 1000,
      "max_api_calls_per_month": 10000000,
      "max_storage_gb": 500,
      "max_concurrent_connections": 50,
      "max_users": 25
    }
  }
}
```

### 2. List All Tenants (Admin Only)

**GET** `/platform/tenants?limit=50&offset=0`

Response:
```json
{
  "status": "success",
  "data": {
    "items": [...],
    "total": 150,
    "limit": 50,
    "offset": 0
  }
}
```

### 3. Get Tenant Quota

**GET** `/platform/tenants/{tenant-id}/quota`

Response:
```json
{
  "status": "success",
  "data": {
    "quota_id": "quota_123",
    "max_apps": 500,
    "max_workflows_per_app": 1000,
    "max_api_calls_per_month": 10000000,
    "max_storage_gb": 500,
    "max_concurrent_connections": 50,
    "max_users": 25
  }
}
```

## Application Endpoints

### 1. List Applications

**GET** `/platform/ui/apps?limit=50&offset=0`

Response:
```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "app_id": "app_123",
        "name": "Data Processing App",
        "version": "1.2.3",
        "status": "deployed",
        "created_at": "2024-01-15T10:30:00Z",
        "created_by": "user_456",
        "last_modified": "2024-01-20T14:22:00Z",
        "workflow_count": 5,
        "execution_count": 456
      }
    ],
    "total": 23,
    "limit": 50,
    "offset": 0
  }
}
```

### 2. Get Application Details

**GET** `/platform/apps/{app-id}`

Response: Individual app object (same as list item)

### 3. Get Application Metrics

**GET** `/platform/apps/{app-id}/metrics`

Response:
```json
{
  "status": "success",
  "data": {
    "total_executions": 1250,
    "failed_executions": 12,
    "avg_duration_ms": 234,
    "total_cost": 45.67,
    "success_rate": 99.04,
    "peak_concurrent": 8,
    "last_execution": "2024-01-22T15:45:00Z"
  }
}
```

### 4. Get Application Logs

**GET** `/platform/apps/{app-id}/logs?limit=100&offset=0`

Response:
```json
{
  "status": "success",
  "data": [
    {
      "timestamp": "2024-01-22T15:45:30Z",
      "level": "INFO",
      "message": "Execution started",
      "execution_id": "exec_789"
    }
  ]
}
```

### 5. Deploy Application

**POST** `/platform/apps/{app-id}/deploy`

Response: Updated app object with status = "deployed"

### 6. Pause Application

**POST** `/platform/apps/{app-id}/pause`

Response: Updated app object with status = "paused"

### 7. Get Application Versions

**GET** `/platform/apps/{app-id}/versions`

Response:
```json
{
  "status": "success",
  "data": [
    {
      "version_id": "v1.2.3",
      "created_at": "2024-01-20T14:22:00Z",
      "created_by": "user_456",
      "changelog": "Fixed bug in workflow parsing"
    }
  ]
}
```

### 8. Rollback to Version

**POST** `/platform/apps/{app-id}/versions/{version-id}/rollback`

Response: Updated app object with restored version

## Billing Endpoints

### 1. Get Subscription

**GET** `/platform/tenants/{tenant-id}/subscription`

Response:
```json
{
  "status": "success",
  "data": {
    "subscription_id": "sub_123",
    "plan": "professional",
    "billing_cycle_start": "2024-01-01",
    "billing_cycle_end": "2024-01-31",
    "auto_renew": true,
    "status": "active",
    "current_period_usage": {
      "api_calls": 5432100,
      "storage_gb": 234,
      "users": 12
    }
  }
}
```

### 2. Get Invoices

**GET** `/platform/tenants/{tenant-id}/invoices?limit=10&offset=0`

Response:
```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "invoice_id": "inv_123",
        "period_start": "2024-01-01",
        "period_end": "2024-01-31",
        "base_amount": 299.00,
        "overage_amount": 45.67,
        "tax_amount": 27.45,
        "total_amount": 372.12,
        "status": "paid",
        "issued_at": "2024-02-01T00:00:00Z",
        "paid_at": "2024-02-02T10:30:00Z",
        "line_items": [
          {
            "description": "Professional Plan",
            "amount": 299.00
          },
          {
            "description": "API Calls Overage (2.5M)",
            "amount": 45.67
          }
        ]
      }
    ],
    "total": 12,
    "limit": 10,
    "offset": 0
  }
}
```

### 3. Upgrade Plan

**POST** `/platform/tenants/{tenant-id}/subscription/upgrade`

Request:
```json
{
  "new_plan": "enterprise"
}
```

Response: Updated subscription object

### 4. Get Billing Events

**GET** `/platform/tenants/{tenant-id}/billing-events?start_date=2024-01-01&end_date=2024-01-31`

Response:
```json
{
  "status": "success",
  "data": {
    "total_executions": 1000000,
    "failed_executions": 10000,
    "api_calls": 5432100,
    "storage_used_gb": 234,
    "success_rate": 99.0,
    "avg_execution_duration_ms": 234,
    "total_cost": 372.12
  }
}
```

## Metrics Endpoints

### 1. Platform Health

**GET** `/platform/health`

Response:
```json
{
  "status": "success",
  "data": {
    "status": "healthy",
    "uptime_percent": 99.95,
    "response_time_p99_ms": 234,
    "error_rate_percent": 0.05,
    "active_tenants": 150,
    "active_executions": 45,
    "worker_pool_utilization": 65,
    "database_connections": {
      "used": 89,
      "total": 100
    },
    "cache_hit_rate": 92.3,
    "timestamp": "2024-01-22T15:45:00Z"
  }
}
```

### 2. Tenant Metrics

**GET** `/platform/tenants/{tenant-id}/metrics?start_date=2024-01-01&end_date=2024-01-31`

Response:
```json
{
  "status": "success",
  "data": {
    "tenant_id": "tenant_123",
    "period_start": "2024-01-01",
    "period_end": "2024-01-31",
    "executions_count": 1000000,
    "executions_failed": 10000,
    "success_rate": 99.0,
    "avg_execution_duration_ms": 234,
    "api_calls_total": 5432100,
    "storage_used_gb": 234,
    "total_cost": 372.12,
    "uptime_percent": 99.9
  }
}
```

### 3. SLA Metrics

**GET** `/platform/tenants/{tenant-id}/sla`

Response:
```json
{
  "status": "success",
  "data": {
    "uptime_percent": 99.95,
    "response_time_p99_ms": 234,
    "error_rate_percent": 0.05,
    "period": {
      "start": "2024-01-01",
      "end": "2024-01-31"
    }
  }
}
```

### 4. Cost Metrics

**GET** `/platform/tenants/{tenant-id}/cost-metrics?period=month`

Response:
```json
{
  "status": "success",
  "data": {
    "total_cost": 372.12,
    "daily_breakdown": [
      {"date": "2024-01-01", "cost": 12.00},
      {"date": "2024-01-02", "cost": 11.50}
    ],
    "cost_by_metric": {
      "base_subscription": 299.00,
      "api_calls": 45.67,
      "storage": 27.45
    }
  }
}
```

## User & RBAC Endpoints

### 1. Get Current User

**GET** `/platform/ui/me`

Response:
```json
{
  "status": "success",
  "data": {
    "user_id": "user_123",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "admin",
    "created_at": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-22T15:45:00Z",
    "disabled": false,
    "mfa_enabled": false
  }
}
```

### 2. List Users

**GET** `/platform/tenants/{tenant-id}/users?limit=50&offset=0`

Response:
```json
{
  "status": "success",
  "data": {
    "items": [...user objects...],
    "total": 12,
    "limit": 50,
    "offset": 0
  }
}
```

### 3. Create User

**POST** `/platform/tenants/{tenant-id}/users`

Request:
```json
{
  "email": "newuser@example.com",
  "name": "New User",
  "role": "developer"
}
```

Response: User object with user_id

### 4. Assign Role

**PATCH** `/platform/users/{user-id}`

Request:
```json
{
  "role": "admin"
}
```

Response: Updated user object

### 5. Check Permission

**POST** `/platform/users/{user-id}/permissions/check`

Request:
```json
{
  "permission": "apps:deploy"
}
```

Response:
```json
{
  "status": "success",
  "data": {
    "has_permission": true
  }
}
```

### 6. List API Keys

**GET** `/platform/tenants/{tenant-id}/api-keys?limit=50&offset=0`

Response:
```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "key_id": "key_123",
        "name": "CI/CD Pipeline",
        "key_prefix": "srp_live_xxxxx",
        "created_at": "2024-01-15T10:00:00Z",
        "last_used": "2024-01-22T15:30:00Z",
        "revoked": false,
        "scopes": ["apps:read", "apps:deploy"]
      }
    ],
    "total": 3,
    "limit": 50,
    "offset": 0
  }
}
```

### 7. Create API Key

**POST** `/platform/tenants/{tenant-id}/api-keys`

Request:
```json
{
  "name": "New API Key",
  "scopes": ["apps:read", "apps:write"]
}
```

Response: API key object with full key (shown only once)

### 8. Get Audit Logs

**GET** `/platform/tenants/{tenant-id}/audit-logs?limit=100&offset=0`

Response:
```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "log_id": "log_123",
        "action": "app_deployed",
        "resource_type": "application",
        "resource_id": "app_456",
        "status": "success",
        "timestamp": "2024-01-22T15:45:00Z",
        "user_id": "user_789",
        "ip_address": "192.168.1.1",
        "changes": {
          "status": ["draft", "deployed"]
        }
      }
    ],
    "total": 450,
    "limit": 100,
    "offset": 0
  }
}
```

## Error Handling

### Standard Error Response

```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "email": "Invalid email format"
    }
  },
  "timestamp": "2024-01-22T15:45:00Z",
  "request_id": "req_123abc"
}
```

### Common Error Codes

| Code | Status | Meaning |
|------|--------|---------|
| SUCCESS | 200 | Operation successful |
| INVALID_REQUEST | 400 | Malformed request |
| UNAUTHORIZED | 401 | Missing or invalid token |
| FORBIDDEN | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| CONFLICT | 409 | Resource conflict |
| RATE_LIMITED | 429 | Too many requests |
| SERVER_ERROR | 500 | Internal server error |
| QUOTA_EXCEEDED | 402 | Quota limit exceeded |

## Rate Limiting

- **Limit**: 1,000 requests per minute per API key
- **Headers**:
  ```
  X-RateLimit-Limit: 1000
  X-RateLimit-Remaining: 999
  X-RateLimit-Reset: 1234567890
  ```

## TypeScript Types

All types are defined in `src/types/index.ts`:

```typescript
import {
  Tenant,
  User,
  App,
  Subscription,
  Invoice,
  PlatformHealth,
  TenantMetrics,
  Alert,
} from "../types";
```

## Examples

### Login Flow

```typescript
import { authService } from "../services";

// 1. Login
const response = await authService.login({
  email: "user@example.com",
  password: "secure_password",
});

// 2. Auth context set automatically
// 3. Subsequent requests include token and tenant ID
```

### Fetch Metrics

```typescript
import { metricsService } from "../services";

// Get tenant metrics
const metrics = await metricsService.getTenantMetrics();

// Polling (30 second interval)
const { tenantMetrics,platformHealth } = useMetrics({
  pollInterval: 30000,
});
```

### Deploy App

```typescript
import { appService } from "../services";

// Deploy app
await appService.deployApp("app_123");

// Auto-refreshes app list
```

---

**API Version**: 1.0.0  
**Last Updated**: 2024  
**Status**: Production Ready
