# SRP Autonomous OS - UI Platform Setup Guide

Complete setup instructions for the SRP Autonomous OS UI Platform - Enterprise Autonomous AI Control Surface.

## System Requirements

- **Node.js**: 18.0.0 or higher
- **npm**: 9.0.0 or higher
- **Operating System**: Windows, macOS, or Linux
- **Disk Space**: 500MB minimum
- **Memory**: 2GB RAM minimum (4GB recommended)
- **Backend**: Phase 7 SRP Platform API running on port 8000

## Quick Start (3 minutes)

### 1. Installation

```bash
# Clone or navigate to the ui-platform directory
cd c:\Users\User\Desktop\emergentic\ AI\ui-platform

# Install dependencies
npm install

# Copy environment configuration
cp .env.example .env

# Edit .env with your configuration (if needed)
# Default: REACT_APP_API_URL=http://localhost:8000
```

### 2. Start Development Server

```bash
npm run dev
```

The application will automatically open at `http://localhost:3000`

### 3. Login

1. Use credentials from your Phase 7 tenant
2. Select your organization
3. Access your dashboard

## Environment Configuration

### Development (.env)

```bash
REACT_APP_API_URL=http://localhost:8000
REACT_APP_THEME=dark
REACT_APP_METRICS_POLL_INTERVAL=30000
REACT_APP_ENABLE_ADMIN_CONSOLE=true
```

### Production (.env.production)

```bash
REACT_APP_API_URL=https://api.yourcompany.com
REACT_APP_API_TIMEOUT=30000
REACT_APP_METRICS_POLL_INTERVAL=60000
REACT_APP_ANALYTICS_ENABLED=true
```

## Project Structure

```
ui-platform/
├── src/
│   ├── components/           # Reusable React components
│   │   ├── common/          # UIComponents
│   │   └── layouts/         # Layout components (MainLayout)
│   ├── pages/               # Full-page components
│   │   ├── AdminConsole.tsx
│   │   ├── TenantDashboard.tsx
│   │   ├── AppManagement.tsx
│   │   ├── BillingDashboard.tsx
│   │   ├── RBACManagement.tsx
│   │   └── ObservabilityDashboard.tsx
│   ├── hooks/               # Custom React hooks
│   │   ├── useAuth.tsx
│   │   ├── useTenant.tsx
│   │   ├── useMetrics.ts
│   │   └── usePermission.ts
│   ├── services/            # API integration layer
│   │   ├── auth.ts
│   │   ├── tenant.ts
│   │   ├── apps.ts
│   │   ├── billing.ts
│   │   ├── metrics.ts
│   │   └── users.ts
│   ├── types/               # TypeScript type definitions
│   ├── utils/               # Utility functions
│   │   ├── formatting.ts
│   │   ├── validation.ts
│   │   └── constants.ts
│   ├── styles/              # CSS and Tailwind
│   └── App.tsx              # Main app component
├── index.html               # Entry HTML
├── package.json             # Dependencies
├── tsconfig.json            # TypeScript config
├── vite.config.ts           # Vite build config
├── tailwind.config.js       # Tailwind config
└── README.md                # This file
```

## Available Scripts

### Development

```bash
# Start development server with hot reload
npm run dev

# Type checking
npm run type-check

# Linting
npm run lint

# Format code
npm run format
```

### Production

```bash
# Build for production
npm run build

# Preview production build locally
npm run preview

# Run tests
npm run test
```

## Dashboard Pages

### 1. **Platform Admin Console** (`/admin`)
   - Global tenant registry
   - Platform health metrics
   - Revenue breakdown
   - Worker pool management
   - System configuration
   - **Access**: Admin & Owner roles

### 2. **Tenant Dashboard** (`/dashboard`)
   - Organization overview
   - Usage metrics
   - Quota tracking
   - Billing information
   - Resource allocation
   - **Access**: All authenticated users

### 3. **App Management** (`/apps`)
   - Application listing
   - Deployment status
   - Execution logs
   - Version management
   - Rollback capabilities
   - **Access**: Developer & Admin roles

### 4. **RBAC Management** (`/users`)
   - User management
   - Role assignment
   - API key generation
   - Audit logs
   - Permission matrix
   - **Access**: Admin & Owner roles

### 5. **Billing Dashboard** (`/billing`)
   - Current subscription
   - Usage vs quota
   - Cost tracking
   - Invoice history
   - Plan upgrades/downgrades
   - **Access**: All users (own billing), Admin (all tenants)

### 6. **Observability Dashboard** (`/metrics`)
   - Real-time metrics
   - Alert management
   - Execution history
   - Cost analysis
   - SLA compliance
   - **Access**: All authenticated users

## API Integration

The UI integrates with Phase 7 Platform via FastAPI endpoints:

### Authentication

```bash
POST /platform/ui/login
POST /platform/ui/auth/validate
POST /platform/ui/auth/refresh
```

### Tenant Management

```bash
GET    /platform/ui/tenant
GET    /platform/tenants
POST   /platform/tenants
PATCH  /platform/tenants/{id}
```

### Applications

```bash
GET    /platform/ui/apps
POST   /platform/tenants/{id}/apps
PATCH  /platform/apps/{id}
DELETE /platform/apps/{id}
```

### Metrics & Observability

```bash
GET /platform/health
GET /platform/tenants/{id}/metrics
GET /platform/tenants/{id}/sla
GET /platform/tenants/{id}/alerts
```

### Billing

```bash
GET    /platform/tenants/{id}/subscription
POST   /platform/tenants/{id}/subscription/upgrade
GET    /platform/tenants/{id}/invoices
```

### Users & RBAC

```bash
GET    /platform/ui/me
GET    /platform/tenants/{id}/users
POST   /platform/users/{id}/permissions/check
GET    /platform/tenants/{id}/audit-logs
```

## Styling & Theming

### Tailwind CSS

All components use Tailwind CSS with:
- Dark professional theme (primary: gray-900, secondary: gray-800)
- Minimal enterprise design (no gradients or excessive decoration)
- Responsive grid layouts
- Role-based UI rendering

### Color Palette

```css
Primary:   #2563eb (Blue)
Success:   #10b981 (Green)
Warning:   #f59e0b (Amber)
Error:     #ef4444 (Red)
Dark:      #111827 (Charcoal)
```

## Authentication Flow

1. **Login**: Email + password to Phase 7 auth
2. **Token Storage**: Bearer token in localStorage
3. **Tenant Context**: Tenant ID in localStorage + X-Tenant-ID header
4. **Auto-Refresh**: Token validation on app load
5. **Protected Routes**: Redirects to `/login` if no token

## RBAC & Permissions

### Roles

- **Owner**: Full platform access
- **Admin**: Tenant management, user management
- **Manager**: App and user management
- **Developer**: App creation and deployment
- **User**: Basic app access
- **Viewer**: Read-only access

### Permission Checking

```typescript
const { can } = usePermission();

// Check permission
if (can("apps:deploy")) {
  // Show deploy button
}
```

## Performance Optimization

### Built-in Features

- **Code Splitting**: Vite automatically chunks components
- **Lazy Loading**: React.lazy for heavy components
- **API Caching**: Metrics cached for 60s by default
- **Request Debouncing**: Polling not too frequent
- **Image Optimization**: Vite handles images

### Targets

- Dashboard load: < 1 second
- API response: < 500ms
- Metrics update: Every 30 seconds (configurable)

## Deployment

### Prerequisites

- Docker or cloud platform account
- Phase 7 Platform API accessible
- SSL certificate (for production)

### Docker Deployment

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "preview"]
```

### Build & Deploy

```bash
# 1. Build for production
npm run build

# 2. Deploy dist/ folder to:
#    - Vercel (auto from GitHub)
#    - AWS S3 + CloudFront
#    - Docker container
#    - Traditional web server

# 3. Configure environment
#    - Set REACT_APP_API_URL to production API
#    - Enable analytics if desired
```

### Production Checklist

- [ ] `REACT_APP_API_URL` points to production backend
- [ ] SSL/TLS enabled on frontend
- [ ] CORS properly configured on backend
- [ ] Token expiration and refresh working
- [ ] Error boundaries implemented
- [ ] Analytics/monitoring enabled
- [ ] Performance metrics reviewed
- [ ] Security headers configured

## Troubleshooting

### "Cannot connect to API"

```bash
# Check backend is running
curl http://localhost:8000/health

# Check environment variable
echo $REACT_APP_API_URL

# Check CORS in backend
# Add to Phase 7: "origins": ["http://localhost:3000"]
```

### "Login fails"

1. Verify tenant exists in Phase 7
2. Check credentials are correct
3. Verify Phase 7 auth endpoint is working
4. Check browser console for errors

### "Metrics not loading"

1. Verify metrics service is running
2. Check tenant has data to display
3. Verify user has permission to view metrics
4. Check API response in browser network tab

### "Page is slow"

1. Check network tab for slow API calls
2. Verify metrics polling interval (default 30s)
3. Check browser DevTools Performance tab
4. Consider reducing data pagination limit

## Development Tips

### Component Creation

```typescript
import React from "react";
import { Card, Button } from "../components/common/UIComponents";
import { useAuth, usePermission } from "../hooks";

export const MyComponent: React.FC = () => {
  const { user } = useAuth();
  const { can } = usePermission();

  return (
    <Card title="My Component">
      {can("action:perform") && <Button>Perform Action</Button>}
    </Card>
  );
};
```

### API Service Usage

```typescript
import { appService } from "../services";

// List apps
const apps = await appService.listApps(undefined, 50);

// Get single app
const app = await appService.getApp(appId);

// Perform action
await appService.deployApp(appId);
```

### Hook Usage

```typescript
import { useAuth, useTenant, useMetrics, usePermission } from "../hooks";

export const MyPage = () => {
  const { user, tenant } = useAuth();
  const { quota, refreshQuota } = useTenant();
  const { tenantMetrics } = useMetrics({ pollInterval: 30000 });
  const { can, isAdmin } = usePermission();

  // Use in your component
};
```

## Future Enhancements (Phase 9)

- Marketplace integration
- Custom dashboard widgets
- Report generation
- Advanced analytics
- Integration with external services

## Support & Resources

- **Documentation**: Check PHASE8_DELIVERABLES.md
- **Phase 7 API**: See PHASE7_API_REFERENCE.md
- **Tailwind CSS**: https://tailwindcss.com/docs
- **React Patterns**: https://react.dev

## License

Proprietary - SRP Autonomous OS Platform

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Status**: Production Ready
