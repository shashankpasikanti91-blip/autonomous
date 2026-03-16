# Phase 8 UI Platform - Troubleshooting Guide

Complete troubleshooting reference for the SRP Autonomous OS UI Platform.

## Common Issues & Solutions

### 🔴 Authentication Issues

#### Issue: "401 Unauthorized" error on login

**Symptoms**: Login fails with 401 status, token not stored

**Causes**:
- Phase 7 backend not running
- Wrong API URL configured
- Invalid credentials
- Backend database connection issue

**Solutions**:

1. **Verify backend is running**
   ```bash
   # Check if Phase 7 is running on port 8000
   curl http://localhost:8000/platform/health
   
   # Should return 200 with health status
   ```

2. **Check .env configuration**
   ```env
   REACT_APP_API_URL=http://localhost:8000
   ```

3. **Verify credentials**
   - Use admin account from Phase 7 setup
   - Ensure tenant exists in backend
   - Check password complexity (8+ chars, upper, lower, digit, symbol)

4. **Check backend logs**
   ```bash
   # Terminal where Phase 7 is running
   # Look for "POST /platform/ui/login" errors
   ```

5. **Clear browser cache**
   ```javascript
   localStorage.clear();
   sessionStorage.clear();
   // Then reload page
   ```

#### Issue: Token expires immediately

**Symptoms**: Logged in, but redirected to login after page refresh

**Causes**:
- Token TTL too short
- Token not saved to localStorage
- useAuth not initializing on mount

**Solutions**:

1. **Check token storage**
   ```javascript
   // Browser DevTools Console
   localStorage.getItem('auth_token')
   localStorage.getItem('tenant_id')
   ```

2. **Verify token is valid**
   ```javascript
   // In browser console
   const token = localStorage.getItem('auth_token');
   console.log('Token:', token?.substring(0, 20) + '...');
   ```

3. **Check backend token TTL**
   - Ensure `expires_in` is > 0 (typically 3600 seconds)
   - Verify refresh token implementation

4. **Force re-initialize**
   ```bash
   # Hard refresh browser
   Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
   ```

#### Issue: "Invalid token" on protected routes

**Symptoms**: See "Unauthorized" message on dashboard pages

**Causes**:
- Token corrupted or malformed
- Tenant ID mismatch
- X-Tenant-ID header not sent
- Auth header not formatted correctly

**Solutions**:

1. **Check request headers in DevTools**
   - Network tab → any API request
   - Headers section → Look for:
     ```
     Authorization: Bearer eyJ...
     X-Tenant-ID: tenant_123
     ```

2. **Verify AuthService.getAuthHeaders()**
   ```typescript
   // In hooks/useAuth.tsx or services/auth.ts
   const headers = {
     'Authorization': `Bearer ${token}`,
     'X-Tenant-ID': tenantId,
   };
   // Both should be set
   ```

3. **Test token validation endpoint**
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        http://localhost:8000/platform/ui/auth/validate
   ```

---

### 🟡 API Integration Issues

#### Issue: "Failed to fetch" errors

**Symptoms**: Network requests fail with CORS or connection errors

**Causes**:
- Backend not accessible
- CORS not configured
- Firewall blocking connection
- Wrong API URL

**Solutions**:

1. **Test backend connectivity**
   ```bash
   # Terminal
   curl http://localhost:8000/platform/health
   
   # Should return 200
   ```

2. **Check CORS headers**
   ```bash
   curl -I http://localhost:8000/platform/ui/login
   
   # Look for:
   # Access-Control-Allow-Origin: http://localhost:3000
   # Access-Control-Allow-Methods: POST, GET, OPTIONS
   ```

3. **Verify API URL in .env**
   ```env
   REACT_APP_API_URL=http://localhost:8000
   # No trailing slash
   ```

4. **Check firewall/network**
   ```bash
   # Check if port 8000 is open
   netstat -an | grep 8000
   
   # macOS/Linux
   lsof -i :8000
   ```

#### Issue: "Request timeout" or slow responses

**Symptoms**: API calls hang for 30+ seconds then fail

**Causes**:
- Backend overloaded
- Database slow queries
- Network latency
- Metrics polling interval too frequent

**Solutions**:

1. **Check backend health**
   ```bash
   curl http://localhost:8000/platform/health
   # Should respond < 100ms
   ```

2. **Monitor backend load**
   - Check CPU/memory usage
   - Look for slow database queries
   - Check active connection count

3. **Reduce polling interval**
   ```typescript
   // In components using metrics
   const metrics = useMetrics({ pollInterval: 60000 }); // 60s instead of 30s
   ```

4. **Enable request tracing in DevTools**
   - Network tab → Preserve log
   - Watch timing for each request
   - Identify slow endpoints

#### Issue: 404 errors on certain endpoints

**Symptoms**: "Not found" errors for apps, metrics, or billing endpoints

**Causes**:
- Route not implemented in Phase 7
- Wrong API path
- Resource ID incorrect
- URL encoding issue

**Solutions**:

1. **Verify endpoint URL**
   ```typescript
   // In services/*.ts
   const url = `${API_BASE_URL}/platform/tenants/${tenantId}/apps`;
   console.log('URL:', url); // Check in DevTools console
   ```

2. **Check Phase 7 API documentation**
   - Verify endpoint exists
   - Check path parameters match
   - Confirm tenant ID format

3. **Test endpoint directly**
   ```bash
   TENANT_ID="tenant_123"
   TOKEN="your_token"
   
   curl -H "Authorization: Bearer $TOKEN" \
        -H "X-Tenant-ID: $TENANT_ID" \
        http://localhost:8000/platform/tenants/$TENANT_ID/apps
   ```

4. **Check URL encoding**
   ```javascript
   // Ensure IDs are properly formatted
   const appId = 'app_123'; // Good
   const appId = 'app 123'; // Bad - should be URL encoded
   ```

---

### 🔵 Component & Rendering Issues

#### Issue: Blank dashboard with no data

**Symptoms**: Page loads but shows empty state or loading spinner indefinitely

**Causes**:
- API call not triggered
- Data not returned from backend
- Component state not updated
- Error swallowed silently

**Solutions**:

1. **Check React DevTools**
   - Redux/DevTools extension
   - Check component props and state
   - Verify data is loaded

2. **Enable debug logging**
   ```typescript
   // In component
   useEffect(() => {
     console.log('Component mounted');
     fetchData();
   }, []);
   
   const fetchData = async () => {
     try {
       console.log('Fetching data...');
       const data = await service.getData();
       console.log('Data received:', data);
       setData(data);
     } catch (error) {
       console.error('Error fetching data:', error);
     }
   };
   ```

3. **Check Network tab**
   - API request sent?
   - Response status 200?
   - Response body has data?

4. **Verify service implementation**
   ```typescript
   // In services/
   // Ensure service returns data, not wrapped
   return response.data; // ✅
   return response;      // ❌
   ```

5. **Check error boundaries**
   - Are errors being caught?
   - Error states defined?
   - Fallback UI displayed?

#### Issue: Styling not applied (dark mode not working)

**Symptoms**: Components show light theme or wrong colors

**Causes**:
- Tailwind CSS not compiled
- Dark mode not enabled
- CSS class not applied
- Theme provider missing

**Solutions**:

1. **Verify Tailwind configuration**
   ```javascript
   // tailwind.config.js
   module.exports = {
     darkMode: 'class', // ✅
     // darkMode: false, // ❌
   };
   ```

2. **Check dark class on HTML**
   ```javascript
   // In browser console
   document.documentElement.classList.contains('dark')
   // Should return true
   ```

3. **Rebuild Tailwind CSS**
   ```bash
   npm run build
   # Ensure styles/globals.css is compiled
   ```

4. **Clear browser cache**
   ```bash
   npm run dev
   # vs Code: Ctrl+Shift+P → "Clear workspace state"
   ```

5. **Verify class names**
   ```jsx
   // ✅ GOOD
   <div className="dark:bg-gray-900">Content</div>
   
   // ❌ BAD
   <div className="bg-gray-900"> <!-- Missing dark: prefix -->
   ```

#### Issue: Modal/Overlay not showing or stuck

**Symptoms**: Modal doesn't appear, or appears but can't close

**Causes**:
- isOpen state not set correctly
- Modal component not in DOM
- z-index too low
- Close handler not working

**Solutions**:

1. **Check modal state**
   ```typescript
   // In React DevTools
   // Inspect component state
   // isOpen should be 'true' when visible
   ```

2. **Verify modal implementation**
   ```jsx
   // Uses portal to move modal outside document flow
   return createPortal(
     <div className="fixed inset-0 z-50">
       {/* Modal content */}
     </div>,
     document.body
   );
   ```

3. **Check z-index**
   ```css
   /* In globals.css */
   modal: z-50 (base layer)
   overlay: z-40 (behind modal)
   ```

4. **Test close handler**
   ```jsx
   <button onClick={() => setIsOpen(false)}>Close</button>
   // onClick directly updates state without async
   ```

---

### 🟢 Performance Issues

#### Issue: Dashboard loads slowly (> 1s)

**Symptoms**: Page takes 3+ seconds to display content

**Causes**:
- Multiple API calls not parallelized
- Large bundle size
- Inefficient re-renders
- Unoptimized images

**Solutions**:

1. **Check bundle size**
   ```bash
   npm run build
   # Look at dist/ size
   npm install -g npm-check-bundlesize
   npm-check-bundlesize
   ```

2. **Enable code splitting**
   ```typescript
   // In App.tsx
   const AdminConsole = lazy(() => import('./pages/AdminConsole'));
   
   <Suspense fallback={<Loading />}>
     <AdminConsole />
   </Suspense>
   ```

3. **Parallelize API calls**
   ```typescript
   // ✅ GOOD - Parallel
   const [tenant, metrics] = await Promise.all([
     tenantService.getTenant(),
     metricsService.getTenantMetrics(),
   ]);
   
   // ❌ SLOW - Sequential
   const tenant = await tenantService.getTenant();
   const metrics = await metricsService.getTenantMetrics();
   ```

4. **Enable caching**
   ```typescript
   // In services/metrics.ts
   const CACHE_TTL = 60000; // 60 seconds
   const cache = new Map();
   
   export const getTenantMetrics = async () => {
     const cached = cache.get('metrics');
     if (cached && Date.now() - cached.time < CACHE_TTL) {
       return cached.data;
     }
     // ... fetch from API
   };
   ```

5. **Use React DevTools Profiler**
   - DevTools → Profiler tab
   - Record interaction
   - Identify slow components
   - Check re-render count

#### Issue: High memory usage or memory leaks

**Symptoms**: Browser slows down over time, "Out of memory" errors

**Causes**:
- Event listeners not cleaned up
- Intervals/timeouts not cleared
- Context subscriptions not unsubscribed
- Large data kept in state

**Solutions**:

1. **Check cleanup in useEffect**
   ```typescript
   useEffect(() => {
     const interval = setInterval(() => {
       // polling code
     }, 30000);
     
     // ✅ Cleanup
     return () => clearInterval(interval);
   }, []);
   ```

2. **Check event listeners**
   ```typescript
   useEffect(() => {
     const handler = () => { /* ... */ };
     window.addEventListener('resize', handler);
     
     // ✅ Cleanup
     return () => {
       window.removeEventListener('resize', handler);
     };
   }, []);
   ```

3. **Monitor memory in DevTools**
   - DevTools → Memory tab
   - Take heap snapshot
   - Compare snapshots over time
   - Look for retained objects

4. **Avoid large data in state**
   ```typescript
   // ❌ Problematic
   const [allMetrics, setAllMetrics] = useState([]);
   // Stores 1000s of metric objects
   
   // ✅ Better
   const [metrics, setMetrics] = useState(latestMetrics);
   // Store only latest, paginate rest
   ```

---

### 🟣 Permission & RBAC Issues

#### Issue: "Permission denied" on allowed operations

**Symptoms**: User can't deploy apps or see sections they should have access to

**Causes**:
- Role not assigned correctly
- Permission cache stale
- Backend RBAC not synced
- Role hierarchy incorrect

**Solutions**:

1. **Verify user role in backend**
   ```bash
   curl -H "Authorization: Bearer $TOKEN" \
        http://localhost:8000/platform/ui/me
   
   # Check "role" field
   # Should be: admin, manager, developer, user, or viewer
   ```

2. **Check permission cache**
   ```typescript
   // In usePermission hook
   useEffect(() => {
     // Force refresh permissions from API
     checkPermissions();
   }, [userId]);
   ```

3. **Verify role-permission mapping**
   ```typescript
   // In utils/constants.ts
   const ROLE_PERMISSIONS = {
     admin: ['*'],
     manager: ['apps:read', 'apps:write', 'users:read'],
     // Check your role has required permission
   };
   ```

4. **Test permission endpoint**
   ```bash
   curl -X POST \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"permission":"apps:deploy"}' \
        http://localhost:8000/platform/users/me/permissions/check
   ```

5. **Refresh permissions**
   ```typescript
   // In component
   const { refreshPermissions } = usePermission();
   
   // After role change in backend
   useEffect(() => {
     refreshPermissions();
   }, [userId]);
   ```

#### Issue: Role-based UI not showing/hiding correctly

**Symptoms**: Buttons visible when they shouldn't be

**Causes**:
- usePermission returning stale data
- Wrong permission string
- Condition logic incorrect

**Solutions**:

1. **Check permission string**
   ```typescript
   // ✅ Correct format
   const { can } = usePermission();
   can('apps:deploy') // uses string from ROLE_PERMISSIONS
   
   // ❌ Incorrect
   can('deploy') // or can('APPS_DEPLOY')
   ```

2. **Debug permission check**
   ```typescript
   const { can, permissions } = usePermission();
   
   useEffect(() => {
     console.log('Current permissions:', permissions);
     console.log('Can deploy:', can('apps:deploy'));
   }, [permissions]);
   ```

3. **Verify conditional rendering**
   ```jsx
   // ✅ GOOD
   {can('apps:deploy') && (
     <button onClick={deployApp}>Deploy</button>
   )}
   
   // ❌ BAD
   <button onClick={deployApp} disabled={!can('apps:deploy')}>
     Deploy
   </button>
   // Button always visible, just disabled
   ```

---

### 🔴 Data Issues

#### Issue: Stale data displayed

**Symptoms**: Change doesn't reflect immediately, "old" data shows

**Causes**:
- Cache not invalidated
- Component not re-rendering
- API call not triggered
- Polling interval too long

**Solutions**:

1. **Invalidate cache on mutation**
   ```typescript
   // In AppService
   async deployApp(appId) {
     const response = await this.api.post(`/apps/${appId}/deploy`);
     // Clear cache
     appCache.delete(appId);
     return response;
   }
   ```

2. **Force component re-render**
   ```typescript
   const [, forceUpdate] = useState();
   
   const refresh = () => {
     fetchData();
     forceUpdate({}); // Force re-render
   };
   ```

3. **Query invalidation pattern**
   ```typescript
   // After mutation, refetch data
   const { mutate, isLoading } = useMutation(deployApp, {
     onSuccess: () => {
       queryClient.invalidateQueries(['apps']);
     },
   });
   ```

4. **Shorter polling interval after action**
   ```typescript
   // When user deploys app
   const { startPolling } = useMetrics();
   
   const handleDeploy = async () => {
     await deployApp();
     // Poll every 5 seconds for 1 minute
     startPolling(5000);
     setTimeout(() => startPolling(30000), 60000);
   };
   ```

#### Issue: Incorrect calculations or aggregations

**Symptoms**: Wrong totals, percentages off, cost calculations wrong

**Causes**:
- Math error in formatting
- Backend doesn't match UI expectations
- Rounding issues
- Null/undefined values in calculations

**Solutions**:

1. **Check formatting function**
   ```typescript
   // In utils/formatting.ts
   export const formatCurrency = (amount, currency = 'USD') => {
     return new Intl.NumberFormat('en-US', {
       style: 'currency',
       currency,
     }).format(amount);
   };
   ```

2. **Verify API response structure**
   ```bash
   curl http://localhost:8000/platform/tenants/tenant_123/metrics
   
   # Check response matches expected shape
   # Look for null/undefined values
   ```

3. **Add type guards**
   ```typescript
   const totalCost = metrics?.total_cost ?? 0;
   const percentage = total > 0 ? (used / total) * 100 : 0;
   ```

4. **Test calculations**
   ```typescript
   describe('Cost calculations', () => {
     it('calculates percentage correctly', () => {
       const result = (50 / 100) * 100;
       expect(result).toBe(50);
     });
   });
   ```

---

## Debugging Tools

### Browser DevTools

#### Console
```javascript
// Check localStorage
localStorage.getItem('auth_token')

// Check tenant context
window.__TENANT_ID__ // if exposed

// Monitor API calls
fetch('http://localhost:8000/platform/health').then(r => r.json())
```

#### Network Tab
1. Open DevTools → Network tab
2. Reload page or trigger action
3. Watch for requests
4. Check status codes (should be 2xx)
5. Inspect request/response bodies

**Common Status Codes**:
- 200: Success
- 201: Created
- 400: Bad request (check payload)
- 401: Unauthorized (check token)
- 403: Forbidden (check permissions)
- 404: Not found (check URL)
- 500: Server error (check backend logs)

#### React DevTools
1. Install [React DevTools](https://chrome.google.com/webstore) extension
2. Open DevTools → Components tab
3. Inspect component tree
4. Check props, hooks, state
5. Edit state for testing

#### Performance
1. DevTools → Performance tab
2. Click record
3. Interact with page
4. Stop recording
5. Analyze flame chart
6. Identify slow functions

### VS Code Debugging

#### Setup launch config (.vscode/launch.json)
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "chrome",
      "request": "launch",
      "name": "Launch Chrome",
      "url": "http://localhost:3000",
      "webRoot": "${workspaceFolder}/src"
    }
  ]
}
```

#### Debug tests
```bash
npm run test -- --inspect-brk
# Open chrome://inspect in Chrome
```

### Logging Strategy

```typescript
// Create logger utility
// src/utils/logger.ts
export const logger = {
  info: (message: string, data?: any) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`[INFO] ${message}`, data);
    }
  },
  
  error: (message: string, error?: Error) => {
    console.error(`[ERROR] ${message}`, error);
  },
  
  debug: (message: string, data?: any) => {
    if (process.env.DEBUG === 'true') {
      console.debug(`[DEBUG] ${message}`, data);
    }
  },
};

// Usage
logger.info('User logged in', { userId: '123' });
logger.error('Failed to deploy app', error);
```

---

## Reporting Issues

### Issue Report Template

```markdown
## Title
Brief description of the issue

## Environment
- OS: Windows/Mac/Linux
- Browser: Chrome/Firefox/Safari
- Node version: 18.x
- npm version: 9.x

## Steps to Reproduce
1. Click X
2. Enter Y
3. Observe Z

## Expected Behavior
Should show/do X

## Actual Behavior
Shows/does Y

## Screenshots
[Attach image if applicable]

## Console Errors
```
Paste full error message
```

## Network Log
[Attach HAR file from DevTools]

## Additional Context
Any other information
```

### Useful Information to Include

- **Error message**: Full text from console
- **Network tab**: Response status and body
- **DevTools state**: Component props/state
- **Backend logs**: Server-side errors
- **Recent changes**: What changed before issue appeared
- **Reproducibility**: Always happens? Sometimes?

---

## Getting Help

1. **Check this guide** first (search keywords)
2. **Search GitHub issues** for similar problems
3. **Read API documentation** (API_REFERENCE.md)
4. **Check setup guide** (SETUP_GUIDE.md)
5. **Enable debug logging** and collect evidence
6. **File issue** with template above

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Status**: Production Ready
