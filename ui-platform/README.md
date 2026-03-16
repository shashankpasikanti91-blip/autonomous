# SRP Autonomous OS - Phase 8 UI Platform

Complete, production-ready React/TypeScript UI platform for the SRP Enterprise Autonomous AI Platform. Integrates seamlessly with Phase 7 backend via clean REST API boundaries.

## 📋 Documentation

| Document | Purpose |
|----------|---------|
| [SETUP_GUIDE.md](./SETUP_GUIDE.md) | Installation, configuration, running locally, deployment |
| [API_REFERENCE.md](./API_REFERENCE.md) | Complete REST API endpoint documentation |
| [TESTING_GUIDE.md](./TESTING_GUIDE.md) | Testing strategy, examples, and best practices |
| [PERFORMANCE_GUIDE.md](./PERFORMANCE_GUIDE.md) | Optimization strategies and benchmarks |
| [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) | Common issues and solutions |

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm 9+
- Phase 7 backend running on `http://localhost:8000`
- 500MB disk space, 2GB RAM

### Installation (3 minutes)

```bash
# 1. Install dependencies
npm install

# 2. Configure environment
cp .env.example .env
# Edit .env to set API URL if needed

# 3. Start development server
npm run dev

# 4. Open browser
# http://localhost:3000
```

## 📁 Project Structure

```
ui-platform/
├── src/
│   ├── __tests__/              # Test files
│   │   ├── setup.ts           # Test environment
│   │   ├── utils/             # Utility tests
│   │   ├── services/          # Service tests
│   │   ├── hooks/             # Hook tests
│   │   ├── components/        # Component tests
│   │   ├── pages/             # Page tests
│   │   └── mocks/             # API mocks (MSW)
│   │
│   ├── components/
│   │   ├── common/
│   │   │   └── UIComponents.tsx      # 11 reusable components
│   │   └── layouts/
│   │       └── MainLayout.tsx        # App layout + sidebar
│   │
│   ├── pages/
│   │   ├── AdminConsole.tsx          # Platform admin (tenants, health, revenue)
│   │   ├── TenantDashboard.tsx       # Tenant overview (usage, billing, resources)
│   │   ├── AppManagement.tsx         # App lifecycle (deploy, pause, delete, logs)
│   │   ├── RBACManagement.tsx        # User/role/permission management
│   │   ├── BillingDashboard.tsx      # Subscription, invoices, quotas
│   │   ├── ObservabilityDashboard.tsx # Metrics, alerts, SLA compliance
│   │   └── index.ts                  # Barrel exports
│   │
│   ├── services/
│   │   ├── auth.ts                   # Authentication, token management
│   │   ├── tenant.ts                 # Tenant CRUD, quota management
│   │   ├── apps.ts                   # App lifecycle, metrics, logs
│   │   ├── billing.ts                # Subscriptions, invoices
│   │   ├── metrics.ts                # Health, metrics, alerts with caching
│   │   ├── users.ts                  # User/role/permission/audit operations
│   │   └── index.ts                  # Barrel exports
│   │
│   ├── hooks/
│   │   ├── useAuth.tsx               # Auth state + context provider
│   │   ├── useTenant.tsx             # Tenant state + context provider
│   │   ├── useMetrics.ts             # Metrics with polling
│   │   ├── usePermission.ts          # RBAC permission checking
│   │   └── index.ts                  # Barrel exports
│   │
│   ├── types/
│   │   └── index.ts                  # 300+ lines of enterprise types
│   │
│   ├── utils/
│   │   ├── formatting.ts             # 13 formatting functions
│   │   ├── validation.ts             # 15+ validation functions
│   │   ├── constants.ts              # App-wide constants
│   │   └── index.ts                  # Barrel exports
│   │
│   ├── styles/
│   │   └── globals.css               # Tailwind + custom CSS
│   │
│   └── App.tsx                       # Root component with routing
│
├── public/                            # Static assets
├── dist/                              # Build output
│
├── .env.example                       # Environment template
├── package.json                       # Dependencies & scripts
├── tsconfig.json                      # TypeScript config
├── vite.config.ts                    # Vite build config
├── vitest.config.ts                  # Vitest test config
├── tailwind.config.js                # Tailwind theme
├── postcss.config.js                 # PostCSS plugins
├── eslint.config.js                  # ESLint rules
│
├── API_REFERENCE.md                  # API documentation
├── SETUP_GUIDE.md                    # Setup & deployment
├── TESTING_GUIDE.md                  # Testing guide
├── PERFORMANCE_GUIDE.md              # Performance optimization
├── TROUBLESHOOTING.md                # Debugging help
└── README.md                         # This file
```

## 🎯 Features

### 6 Complete Dashboards

| Dashboard | Access | Features |
|-----------|--------|----------|
| **Admin Console** | Admin, Owner | Platform overview, tenant registry, health, revenue |
| **Tenant Dashboard** | All users | Org info, usage metrics, quota tracking, billing |
| **Billing Dashboard** | All users | Plans, quotas, invoices, cost projections |
| **Observability** | All users | Metrics, alerts, SLA compliance, cost breakdown |
| **App Management** | Developers | Deploy, pause, delete, logs, versions, metrics |
| **RBAC Management** | Admin, Owner | Users, roles, API keys, audit logs |

### Architecture Highlights

- ✅ **100% TypeScript** - Strict mode, enterprise-grade type safety
- ✅ **Service Layer** - Clean API integration, no backend modifications
- ✅ **React Context** - Lightweight state management (no Redux)
- ✅ **Custom Hooks** - Reusable logic, polling, caching
- ✅ **Component Library** - 11 reusable UI components
- ✅ **Dark Theme** - Professional enterprise design with Tailwind CSS
- ✅ **RBAC** - 6 roles with permission-based rendering
- ✅ **Multi-tenant** - Automatic tenant isolation via headers
- ✅ **Caching** - Smart cache invalidation, configurable TTL
- ✅ **Error Handling** - Comprehensive error states and recovery
- ✅ **Responsive** - Works on desktop (mobile in Phase 9)

## 🛠️ Available Scripts

```bash
# Development
npm run dev          # Start dev server (port 3000, auto-open)
npm run preview      # Preview production build locally

# Building
npm run build        # Production build to dist/
npm run build:analyze # Analyze bundle size

# Quality
npm run lint         # ESLint + Prettier
npm run type-check   # TypeScript strict check
npm run format       # Auto-format code

# Testing
npm run test         # Run all tests (Vitest)
npm run test:watch   # Watch mode
npm run test:coverage # Generate coverage report
```

## 🔐 Authentication & Authorization

### Token-Based Auth

```
1. User logs in with email + password
2. Backend validates, returns JWT token
3. Token stored in localStorage
4. All API requests include: Authorization: Bearer {token}
5. Token auto-refreshes via refresh_token (Phase 7)
6. Session expires or user logs out → cleared
```

### RBAC (6 Roles)

| Role | Permissions | UI Access |
|------|-------------|-----------|
| **Owner** | All | Everything + Admin Console |
| **Admin** | Most | Everything except billing override |
| **Manager** | Moderate | Dashboard, Apps, Metrics, Users (read) |
| **Developer** | App focus | Dashboard, Apps, Metrics |
| **User** | Limited | Dashboard, Metrics (read-only) |
| **Viewer** | Read-only | Dashboard, Metrics (view-only) |

See [SETUP_GUIDE.md](./SETUP_GUIDE.md#rbac--permissions) for complete permission matrix.

## 📊 Dashboards Overview

### AdminConsole
- Platform KPIs (tenants, revenue, executions, uptime)
- Platform health (status, latency, error rate, cache rate)
- Worker pool metrics (connections, utilization)
- Tenant registry table (filter, sort, manage)
- Revenue breakdown by plan
- System config (API version, database, cache, region)

### TenantDashboard
- Organization stats (name, plan, monthly cost, platform status)
- 6 usage metrics (executions, storage, duration, etc.)
- 6 quota limits with progress bars + warnings
- Current billing cycle info
- Resource allocation (DB connections, worker pool)

### BillingDashboard
- Current subscription overview (plan, price, features)
- Usage summary (executions, API calls, storage, success rate)
- 6 quotas vs actual with progress bars
- Recent invoices with download
- Plan upgrade/downgrade/cancel options

### AppManagement
- App list with metrics (name, version, status, executions, cost)
- Action buttons (logs, versions, deploy, pause, delete)
- Logs modal (scrollable JSON)
- Versions modal (rollback capability)
- Permission-based button visibility

### RBACManagement
- **Users tab**: List, add, assign role, disable/enable, MFA
- **API Keys tab**: Create, list, revoke, view scopes
- **Audit Logs tab**: Action history with timestamp, IP, status

### ObservabilityDashboard
- 4 KPIs (status, uptime, latency, error rate)
- Execution metrics (total, failed, success rate, duration)
- SLA compliance (3 metrics with targets)
- Cost analysis (monthly total + daily breakdown chart)
- Active alerts table
- Recent executions table

## 🔌 API Integration

### Phase 7 Endpoints Used

```
Authentication:
  POST   /platform/ui/login                    # User login
  POST   /platform/ui/auth/validate            # Token validation
  POST   /platform/ui/auth/refresh             # Token refresh

Tenant Management:
  GET    /platform/ui/tenant                   # Current tenant
  GET    /platform/tenants                     # List (admin)
  GET    /platform/tenants/{id}/quota          # Quota info
  
Applications:
  GET    /platform/ui/apps                     # List apps
  POST   /platform/apps/{id}/deploy            # Deploy
  POST   /platform/apps/{id}/pause             # Pause
  GET    /platform/apps/{id}/metrics           # App metrics

Billing:
  GET    /platform/tenants/{id}/subscription   # Current plan
  GET    /platform/tenants/{id}/invoices       # Invoice list
  POST   /platform/tenants/{id}/subscription/upgrade # Upgrade

Metrics & Monitoring:
  GET    /platform/health                      # Platform health
  GET    /platform/tenants/{id}/metrics        # Tenant metrics
  GET    /platform/tenants/{id}/sla            # SLA compliance

Users & RBAC:
  GET    /platform/ui/me                       # Current user
  GET    /platform/tenants/{id}/users          # User list
  POST   /platform/users/{id}/permissions/check # Permission check
  GET    /platform/tenants/{id}/audit-logs     # Audit trail
```

Complete documentation: [API_REFERENCE.md](./API_REFERENCE.md)

## 🎨 Styling & Theme

### Dark Professional Theme

- **Primary**: Blue (#2563eb)
- **Success**: Green (#10b981)
- **Warning**: Amber (#f59e0b)
- **Error**: Red (#ef4444)
- **Background**: Dark gray (#111827, text: gray (#f3f4f6))
- **Borders**: Subtle gray (#374151)

### Tailwind CSS

All components use Tailwind utility classes. Custom theme defined in [tailwind.config.js](./tailwind.config.js).

### Responsive Design

- Desktop-first approach (Phase 8)
- Mobile optimization planned for Phase 9
- All dashboards tested at 1024px+ width

## 📈 Performance Targets

| Metric | Target | How to measure |
|--------|--------|-----------------|
| Dashboard load | < 1 second | Chrome DevTools Lighthouse |
| API response | < 200ms (p95) | Network tab, metrics service |
| Bundle size | < 300KB gzipped | `npm run build:analyze` |
| First Paint | < 1.5s | Lighthouse LCP |
| Time to Interactive | < 3.5s | Lighthouse TTI |

Details: [PERFORMANCE_GUIDE.md](./PERFORMANCE_GUIDE.md)

## 🧪 Testing

### Testing Stack

- **Framework**: Vitest (Jest alternative, faster)
- **Component**: React Testing Library
- **API Mocking**: MSW (Mock Service Worker)
- **Coverage Target**: 80% (lines, functions, branches)

### Running Tests

```bash
npm run test                # Run all tests
npm run test:watch         # Watch mode for development
npm run test:coverage      # Generate coverage report
```

Example tests included for:
- Formatting utilities
- Validation functions
- Authentication service
- Dashboard components

Details: [TESTING_GUIDE.md](./TESTING_GUIDE.md)

## 🐛 Troubleshooting

### Common Issues

- **401 Unauthorized**: Phase 7 not running, check backend
- **"Failed to fetch"**: CORS issue, verify API URL
- **Dashboard blank**: Check Network tab for API errors
- **Styling not applied**: Clear cache, rebuild CSS
- **Slow performance**: Check metrics polling interval, use DevTools Profiler

Quick fixes and full debugging guide: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

## 🚢 Deployment

### Development

```bash
npm install
npm run dev
# Navigate to http://localhost:3000
```

### Production Build

```bash
npm run build
# dist/ folder ready for deployment
```

### Docker

```bash
docker build -t srp-ui:latest .
docker run -p 80:80 srp-ui:latest
```

### Cloud Platforms

- **Vercel**: `vercel deploy` (recommended for React)
- **AWS**: S3 + CloudFront + CloudFormation
- **Azure**: Static Web App
- **Google Cloud**: Cloud Storage + Cloud CDN

Full deployment guide: [SETUP_GUIDE.md](./SETUP_GUIDE.md#deployment)

## 📦 Dependencies

### Production (18 packages)
- react 18.2.0
- react-router-dom 6.20.0
- axios 1.6.2
- tailwindcss 3.3.6

### Development (12 packages)
- typescript 5.3.2
- vite 5.0.8
- vitest (latest)
- eslint, prettier

Total bundle: < 300KB gzipped

## 🔄 Integration with Phase 7

### Zero Modifications
✅ No changes to Phase 7 backend
✅ Clean API boundary via service layer
✅ All calls through REST endpoints
✅ Can operate independently

### Compatibility
✅ Phase 1-7 all work
✅ Can be deployed anywhere
✅ No shared dependencies
✅ Versioned API responses

## 🗺️ Project Phases

| Phase | Status | Deliverables |
|-------|--------|--------------|
| 1-7 | ✅ Complete | Backend infrastructure, multi-tenancy, RBAC, billing |
| **8** | ✅ **Complete** | **UI Platform (this repo), 6 dashboards, full API integration** |
| 9 | 🔜 Planned | Marketplace, community apps, ratings, publication |
| 10+ | 🔜 Planned | Analytics, advanced reporting, ML features |

## 📞 Support

### Documentation
- [API_REFERENCE.md](./API_REFERENCE.md) - Complete API docs
- [SETUP_GUIDE.md](./SETUP_GUIDE.md) - Installation & deployment
- [TESTING_GUIDE.md](./TESTING_GUIDE.md) - Testing guide
- [PERFORMANCE_GUIDE.md](./PERFORMANCE_GUIDE.md) - Optimization tips
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Common issues

### Development Tips
- See `SETUP_GUIDE.md` → Development section
- Check `TESTING_GUIDE.md` for test patterns
- Review `TROUBLESHOOTING.md` before filing bugs

## 📄 License

This project is part of the SRP Autonomous OS. All rights reserved.

---

## Summary

**Phase 8 - Enterprise UI Platform**

✅ **7,500+ lines** of production-grade React/TypeScript code
✅ **6 complete dashboards** for platform admin, tenants, billing, apps, users, metrics
✅ **100% TypeScript** with strict mode
✅ **Clean API integration** with Phase 7
✅ **Dark professional theme** with Tailwind CSS
✅ **Complete documentation** including API, testing, performance, troubleshooting
✅ **Ready to deploy** to Vercel, AWS, Docker, or any host

### Quick Start
```bash
npm install && npm run dev
# Open http://localhost:3000
```

**Status**: ✅ Production Ready

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Maintainer**: SRP Team
