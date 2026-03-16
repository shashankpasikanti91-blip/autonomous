# Phase 8 UI Platform - Performance Optimization Guide

Comprehensive performance optimization strategies for the SRP Autonomous OS UI Platform.

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| First Contentful Paint (FCP) | < 1.5s | - |
| Largest Contentful Paint (LCP) | < 2.5s | - |
| Time to Interactive (TTI) | < 3.5s | - |
| Cumulative Layout Shift (CLS) | < 0.1 | - |
| First Input Delay (FID) | < 100ms | - |
| Dashboard Load | < 1s | - |
| API Response | < 200ms (p95) | - |
| Bundle Size | < 300KB (gzipped) | - |

## 1. Code Splitting & Lazy Loading

### Current Implementation

```typescript
// App.tsx - Route-based code splitting
import { lazy, Suspense } from 'react';

const AdminConsole = lazy(() => import('./pages/AdminConsole'));
const TenantDashboard = lazy(() => import('./pages/TenantDashboard'));
const BillingDashboard = lazy(() => import('./pages/BillingDashboard'));
const ObservabilityDashboard = lazy(() => import('./pages/ObservabilityDashboard'));
const AppManagement = lazy(() => import('./pages/AppManagement'));
const RBACManagement = lazy(() => import('./pages/RBACManagement'));

<Suspense fallback={<Loading />}>
  <Routes>
    <Route path="/admin" element={<AdminConsole />} />
    <Route path="/dashboard" element={<TenantDashboard />} />
    {/* ... other routes ... */}
  </Routes>
</Suspense>
```

### Optimization Tips

```typescript
// 1. Component-level code splitting for heavy components
const ExpensiveChart = lazy(() => import('./components/ExpensiveChart'));

// 2. Prefetch routes on hover
const prefetchRoute = (pageComponent) => {
  // Trigger code split load before navigation
  pageComponent.render?.({});
};

// 3. Use React.memo to prevent unnecessary renders
const DashboardCard = memo(({ data, onRefresh }) => {
  return <Card>{/* ... */}</Card>;
});
```

## 2. Bundle Size Optimization

### Analyze Bundle

```bash
# Install analyze tool
npm install --save-dev rollup-plugin-visualizer

# Generate bundle report
npm run build

# View interactive bundle visualization
open dist/stats.html
```

### Vite Configuration

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        // Manual chunk configuration for better caching
        manualChunks: {
          // Vendor chunks
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['axios', 'tailwindcss'],
          
          // Feature chunks
          'admin': ['./src/pages/AdminConsole'],
          'billing': ['./src/pages/BillingDashboard'],
          'apps': ['./src/pages/AppManagement'],
        },
      },
    },
    
    // Optimize CSS
    cssCodeSplit: true,
    
    // Minify
    minify: 'terser',
    
    // Source maps (disable in production)
    sourcemap: process.env.NODE_ENV !== 'production',
  },
});
```

### Tree Shaking

```typescript
// ✅ GOOD - Named imports (tree-shakeable)
import { formatCurrency, formatBytes } from '@utils';

// ❌ BAD - Default imports
import * from '@utils';
import utils from '@utils';
```

## 3. Caching Strategies

### HTTP Caching

```typescript
// In fetch interceptor
const cacheHeaders = {
  'Cache-Control': 'public, max-age=3600', // 1 hour
  'ETag': 'W/"timestamp-hash"',
};

// Backend should return cache headers
// UI respects browser cache
```

### API Response Caching

```typescript
// services/metrics.ts
class MetricsService {
  private cache = new Map<string, any>();
  private cacheTTL = 60000; // 60 seconds
  
  async getTenantMetrics() {
    const cacheKey = `metrics_${this.tenantId}`;
    const cached = this.cache.get(cacheKey);
    
    if (cached && Date.now() - cached.time < this.cacheTTL) {
      return cached.data;
    }
    
    const data = await this.api.get('/metrics');
    this.cache.set(cacheKey, { data, time: Date.now() });
    return data;
  }
  
  clearCache() {
    this.cache.clear();
  }
}
```

### Component State Caching

```typescript
// Cache recently loaded pages
const pageCache = {
  '/admin': null,
  '/dashboard': null,
  '/billing': null,
};

useEffect(() => {
  const handleRouteChange = (path) => {
    if (pageCache[path]) {
      setPageData(pageCache[path]);
      return;
    }
    
    fetchPageData(path).then(data => {
      pageCache[path] = data;
      setPageData(data);
    });
  };
}, []);
```

## 4. Rendering Optimization

### Prevent Unnecessary Re-renders

```typescript
// Use memo for expensive components
export const AdminConsole = memo(({ data }) => {
  return <div>{/* ... */}</div>;
}, (prevProps, nextProps) => {
  // Custom comparison
  return prevProps.data.id === nextProps.data.id;
});
```

### Virtual Scrolling for Large Lists

```typescript
// For large tables (1000+ rows)
import { FixedSizeList } from 'react-window';

const Row = ({ index, style, data }) => (
  <div style={style}>
    {data[index].name}
  </div>
);

<FixedSizeList
  height={600}
  itemCount={data.length}
  itemSize={35}
  width="100%"
>
  {Row}
</FixedSizeList>
```

### Debounce/Throttle Handlers

```typescript
import { debounce } from 'lodash-es';

// Search with debounce
const [searchTerm, setSearchTerm] = useState('');

const debouncedSearch = debounce((term) => {
  searchAPI(term);
}, 300);

const handleSearchChange = (e) => {
  setSearchTerm(e.target.value);
  debouncedSearch(e.target.value);
};
```

### Pagination Instead of Load All

```typescript
// Instead of loading all 10,000 users at once
const [page, setPage] = useState(0);
const [limit] = useState(50);

const fetchUsers = async () => {
  const users = await userService.listUsers(limit, page * limit);
  setUsers(users);
};

// UI shows page controls
<Pagination
  current={page}
  total={Math.ceil(totalUsers / limit)}
  onPageChange={setPage}
/>
```

## 5. Network Optimization

### Parallel API Calls

```typescript
// ✅ GOOD - Parallel (concurrent)
const [tenant, metrics, apps] = await Promise.all([
  tenantService.getTenant(),
  metricsService.getTenantMetrics(),
  appService.listApps(),
]);

// ❌ SLOW - Sequential
const tenant = await tenantService.getTenant();
const metrics = await metricsService.getTenantMetrics();
const apps = await appService.listApps();
// Serial takes 3x longer if each takes 100ms
```

### Request Batching

```typescript
// Batch multiple resource requests
async batchGetApps(appIds: string[]) {
  return POST('/apps/batch', {
    ids: appIds,
  });
  // Get multiple apps in one request
  // Better than App/app1 + /apps/app2 + /apps/app3
}
```

### Compress Response Bodies

```typescript
// In backend - enable gzip compression
// Requests/responses automatically gzipped by:
// - nginx reverse proxy
// - Express/FastAPI gzip middleware
// - CDN (Cloudflare, AWS CloudFront)

// UI automatically decompresses
// Reduces bandwidth 70-90%
```

## 6. Image & Asset Optimization

### Image Optimization

```typescript
// Use WebP with JPEG fallback
<picture>
  <source srcSet={require('./image.webp')} type="image/webp" />
  <source srcSet={require('./image.jpg')} type="image/jpeg" />
  <img src={require('./image.jpg')} alt="Description" />
</picture>

// Or use next-gen format automatically
<img src={image} alt="Description" loading="lazy" />
```

### Icon Optimization

```typescript
// Use SVG icons instead of font icons
// SVG is smaller and more flexible
import { ActivityIcon } from './icons';

<ActivityIcon size={24} />

// Instead of:
// <i className="icon-activity"></i> with font file
```

### CSS Optimization

```css
/* Only import used Tailwind utilities */
@import 'tailwindcss/base';
@import 'tailwindcss/components';
@import 'tailwindcss/utilities';

/* Purge unused classes in production */
/* tailwind.config.js */
content: [
  './src/**/*.{js,jsx,ts,tsx}',
  // Specify files with Tailwind classes
],
```

## 7. JavaScript Optimization

### Minification

```bash
# Vite automatically minifies in production
npm run build

# Verify with: ls -lh dist/assets/
# Should see .min.js files
```

### Tree Shaking

```typescript
// ✅ Remove unused exports
export { formatCurrency, formatBytes };

// ❌ Don't export entire modules
export * from './formatting';
```

### Async/Await vs Promises

```typescript
// Both compiled to same, but async is clearer
async function loadData() {
  try {
    const data = await fetchAPI();
    return data;
  } catch (error) {
    console.error(error);
  }
}
```

## 8. Metrics Polling Optimization

### Adaptive Polling

```typescript
// Reduce polling when tab not focused
useEffect(() => {
  const handleVisibilityChange = () => {
    if (document.hidden) {
      stopPolling(); // Background tab
    } else {
      startPolling(30000); // Active tab
    }
  };
  
  document.addEventListener('visibilitychange', handleVisibilityChange);
  return () => {
    document.removeEventListener('visibilitychange', handleVisibilityChange);
  };
}, []);
```

### Configurable Polling Intervals

```typescript
const POLLING_INTERVALS = {
  metrics: 30000,      // 30 seconds
  health: 60000,       // 60 seconds
  alerts: 60000,       // 60 seconds
  usage: 120000,       // 2 minutes
};

// Users can configure via settings
<select onChange={(e) => setMetricsInterval(e.target.value)}>
  <option value="10000">Fast (10s)</option>
  <option value="30000" selected>Normal (30s)</option>
  <option value="60000">Slow (60s)</option>
</select>
```

## 9. Memory Optimization

### Cleanup Event Listeners

```typescript
useEffect(() => {
  const handleResize = () => {
    // Handle resize
  };
  
  window.addEventListener('resize', handleResize);
  
  // ✅ Cleanup
  return () => {
    window.removeEventListener('resize', handleResize);
  };
}, []);
```

### Clear Timers

```typescript
useEffect(() => {
  const interval = setInterval(() => {
    refreshData();
  }, 30000);
  
  // ✅ Cleanup
  return () => clearInterval(interval);
}, []);
```

### Limit Cache Size

```typescript
class CachedService {
  private cache = new Map();
  private maxCacheSize = 100;
  
  set(key: string, value: any) {
    if (this.cache.size >= this.maxCacheSize) {
      // Remove oldest item
      const oldestKey = this.cache.keys().next().value;
      this.cache.delete(oldestKey);
    }
    this.cache.set(key, value);
  }
}
```

## 10. Production Builds

### Build Optimization

```bash
# Analyze build output
npm run build

# Production bundle should be < 300KB gzipped
# Check with:
find dist -name '*.js.gz' -exec du -h {} \;
```

### Build Script

```json
{
  "scripts": {
    "build": "vite build",
    "build:analyze": "vite build --analyze",
    "build:preview": "vite build && vite preview",
    "build:report": "vite build && npm run analyze"
  }
}
```

### Environment Configuration

```typescript
// Automatically optimize based on build type
const isProduction = import.meta.env.PROD;

if (isProduction) {
  // Disable debug logging
  console.log = () => {};
  
  // Disable source maps
  // (configured in vite.config.ts)
  
  // Increase cache TTL
  CACHE_TTL = 600000; // 10 min instead of 1 min
}
```

## 11. Performance Monitoring

### Measure Core Web Vitals

```typescript
// utils/metrics.ts
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

export const reportMetrics = () => {
  getCLS(console.log); // Cumulative Layout Shift
  getFID(console.log); // First Input Delay
  getFCP(console.log); // First Contentful Paint
  getLCP(console.log); // Largest Contentful Paint
  getTTFB(console.log); // Time to First Byte
};

// Call from App.tsx
useEffect(() => {
  reportMetrics();
}, []);
```

### Track Slow Operations

```typescript
export const trackOperation = (name: string) => {
  const start = performance.now();
  
  return () => {
    const duration = performance.now() - start;
    if (duration > 200) {
      // Log slow operation
      console.warn(`Slow operation: ${name} took ${duration}ms`);
      
      // Send to metrics service
      metricsService.recordSlowOp(name, duration);
    }
  };
};

// Usage
const stopTimer = trackOperation('data-fetch');
await fetchData();
stopTimer();
```

### Browser Performance API

```typescript
// Use browser's built-in timing
useEffect(() => {
  // After render
  setTimeout(() => {
    const perfData = performance.getEntriesByType('navigation')[0];
    console.log('Page load time:', perfData.loadEventEnd - perfData.fetchStart);
    console.log('DOM ready:', perfData.domContentLoadedEventEnd - perfData.fetchStart);
  }, 0);
}, []);
```

## 12. Specific Component Optimizations

### AdminConsole Optimization

```typescript
// Separate KPIs and detailed data
const KPIs = memo(() => { /* ... */ }); // Cached, rarely changes
const TenantTable = memo(() => { /* ... */ }); // Paginated, only loads 50

// Conditional rendering
{showDetails && <DetailedAnalytics />} // Lazy load
```

### BillingDashboard Optimization

```typescript
// Preload invoices only when tab opened
<Tab onSelect={() => setInvoiceTab(true)}>
  Invoices
  {invoiceTab && <InvoicesList />}
</Tab>
```

### ObservabilityDashboard Optimization

```typescript
// Use smaller time windows for charts
const [timeRange, setTimeRange] = useState('24h'); // Not 90d

// Aggregate metrics on backend
// Send totals, not individual points
```

## 13. Deployment Optimization

### Vercel Deployment

```bash
# Automatically optimizes:
# - Edge caching
# - Automatic code splitting
# - Image optimization
# - Serverless functions

npm install -g vercel
vercel deploy
```

### Docker Deployment

```dockerfile
# Multi-stage build to reduce image size
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 14. Monitoring in Production

### Error Tracking

```typescript
// Sentry integration
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: process.env.REACT_APP_SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: 0.1,
});
```

### Analytics

```typescript
// Track key user actions
trackEvent('dashboard_load', {
  duration: loadTime,
  components: componentsLoaded,
});

trackEvent('api_call', {
  endpoint: '/metrics',
  status: 200,
  duration: responseTime,
});
```

---

## Performance Checklist

- [ ] Bundle size < 300KB gzipped
- [ ] First load < 2.5s (LCP)
- [ ] Dashboard interactive < 3.5s (TTI)
- [ ] API responses < 200ms (p95)
- [ ] No layout shifts (CLS < 0.1)
- [ ] Code splitting by route
- [ ] Images optimized (WebP + lazy load)
- [ ] Unused code removed (tree-shaking)
- [ ] Event listeners cleaned up
- [ ] Timers/intervals cleared
- [ ] Large lists paginated or virtualized
- [ ] API calls parallelized
- [ ] Response caching enabled
- [ ] Polling intervals configurable
- [ ] Memory monitoring in place
- [ ] Error tracking enabled
- [ ] Analytics configured

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Status**: Production Ready
