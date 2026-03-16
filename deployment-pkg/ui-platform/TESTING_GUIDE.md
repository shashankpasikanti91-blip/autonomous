# Phase 8 UI Platform - Testing Guide

Comprehensive testing strategy and examples for the SRP Autonomous OS UI Platform.

## Testing Stack

- **Framework**: Vitest (faster than Jest, optimized for modern tooling)
- **Component Testing**: React Testing Library (semantic queries)
- **API Mocking**: MSW (Mock Service Worker)
- **E2E Testing**: Playwright (recommended, not included)
- **Coverage Target**: 80% lines, functions, branches, statements

## Test Structure

```
src/
├── __tests__/
│   ├── setup.ts              # Test environment setup
│   ├── utils/
│   │   ├── formatting.test.ts
│   │   └── validation.test.ts
│   ├── services/
│   │   ├── auth.test.ts
│   │   ├── tenant.test.ts
│   │   └── apps.test.ts
│   ├── hooks/
│   │   ├── useAuth.test.tsx
│   │   └── useMetrics.test.tsx
│   ├── components/
│   │   └── UIComponents.test.tsx
│   └── pages/
│       └── AdminConsole.test.tsx
```

## Running Tests

```bash
# Run all tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm run test src/__tests__/utils/formatting.test.ts

# Run tests matching pattern
npm run test --grep "formatCurrency"
```

## Test Configuration

**vitest.config.ts** includes:
- jsdom environment for DOM/React testing
- Path aliases matching tsconfig
- Coverage thresholds
- setupFiles for mocks

**package.json scripts**:
```json
{
  "test": "vitest run",
  "test:watch": "vitest watch",
  "test:coverage": "vitest run --coverage"
}
```

## Unit Tests - Utilities

### Formatting Tests ([src/__tests__/utils/formatting.test.ts](./src/__tests__/utils/formatting.test.ts))

```typescript
import { describe, it, expect } from 'vitest';
import * as formatting from '../../utils/formatting';

describe('Formatting Utilities', () => {
  describe('formatCurrency', () => {
    it('formats USD currency correctly', () => {
      expect(formatting.formatCurrency(1234.56, 'USD')).toBe('$1,234.56');
    });
  });
});
```

**Coverage**: All 13 formatting functions with edge cases

### Validation Tests ([src/__tests__/utils/validation.test.ts](./src/__tests__/utils/validation.test.ts))

```typescript
describe('isValidEmail', () => {
  it('validates correct email addresses', () => {
    expect(validation.isValidEmail('user@example.com')).toBe(true);
  });

  it('rejects invalid email addresses', () => {
    expect(validation.isValidEmail('notanemail')).toBe(false);
  });
});
```

**Coverage**: All 15+ validation functions with positive/negative cases

## Unit Tests - Services

### Auth Service Tests

```typescript
// src/__tests__/services/auth.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { authService } from '../../services';
import * as constants from '../../utils/constants';

describe('AuthService', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  describe('login', () => {
    it('stores token and tenant ID on successful login', async () => {
      const mockResponse = {
        status: 'success',
        data: {
          user: { user_id: '123', email: 'user@example.com' },
          tenant: { tenant_id: 'tenant_123' },
          token: {
            access_token: 'eyJhbGc...',
            token_type: 'Bearer',
            expires_in: 3600,
          },
        },
      };

      vi.spyOn(global, 'fetch').mockResolvedValueOnce(
        new Response(JSON.stringify(mockResponse), { status: 200 })
      );

      const result = await authService.login({
        email: 'user@example.com',
        password: 'SecurePass123!',
      });

      expect(result.token.access_token).toBe('eyJhbGc...');
      expect(localStorage.getItem(constants.STORAGE_KEYS.AUTH_TOKEN)).toBe('eyJhbGc...');
      expect(localStorage.getItem(constants.STORAGE_KEYS.TENANT_ID)).toBe('tenant_123');
    });

    it('throws error on invalid credentials', async () => {
      vi.spyOn(global, 'fetch').mockResolvedValueOnce(
        new Response(JSON.stringify({
          status: 'error',
          error: { code: 'UNAUTHORIZED', message: 'Invalid credentials' },
        }), { status: 401 })
      );

      expect(async () => {
        await authService.login({
          email: 'user@example.com',
          password: 'wrong_password',
        });
      }).rejects.toThrow();
    });
  });

  describe('validateToken', () => {
    it('returns user data on valid token', async () => {
      const mockUser = { user_id: '123', email: 'user@example.com', role: 'admin' };

      vi.spyOn(global, 'fetch').mockResolvedValueOnce(
        new Response(JSON.stringify({
          status: 'success',
          data: mockUser,
        }), { status: 200 })
      );

      const result = await authService.validateToken('valid_token');
      expect(result).toEqual(mockUser);
    });

    it('returns null on invalid token', async () => {
      vi.spyOn(global, 'fetch').mockResolvedValueOnce(
        new Response(JSON.stringify({
          status: 'error',
          error: { code: 'UNAUTHORIZED' },
        }), { status: 401 })
      );

      expect(async () => {
        await authService.validateToken('invalid_token');
      }).rejects.toThrow();
    });
  });

  describe('getAuthHeaders', () => {
    it('includes Bearer token and X-Tenant-ID', () => {
      authService.setToken('test_token');
      authService.setTenantId('tenant_123');

      const headers = authService.getAuthHeaders();
      expect(headers.Authorization).toBe('Bearer test_token');
      expect(headers['X-Tenant-ID']).toBe('tenant_123');
    });
  });
});
```

## Component Tests

### UI Components Test

```typescript
// src/__tests__/components/UIComponents.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Button, Card, Stat, Loading, ErrorAlert } from '../../components/common/UIComponents';

describe('UI Components', () => {
  describe('Button', () => {
    it('renders button with label', () => {
      render(<Button>Click me</Button>);
      expect(screen.getByRole('button')).toHaveTextContent('Click me');
    });

    it('applies variant styles', () => {
      const { rerender } = render(<Button variant="primary">Primary</Button>);
      let button = screen.getByRole('button');
      expect(button).toHaveClass('bg-blue-600');

      rerender(<Button variant="secondary">Secondary</Button>);
      button = screen.getByRole('button');
      expect(button).toHaveClass('bg-gray-600');

      rerender(<Button variant="danger">Danger</Button>);
      button = screen.getByRole('button');
      expect(button).toHaveClass('bg-red-600');
    });

    it('shows loading state', () => {
      render(<Button loading>Loading</Button>);
      expect(screen.getByRole('button')).toBeDisabled();
      expect(screen.getByTestId('loader')).toBeInTheDocument();
    });
  });

  describe('Card', () => {
    it('renders card with title and content', () => {
      render(
        <Card title="Test Card">
          <div>Content</div>
        </Card>
      );

      expect(screen.getByText('Test Card')).toBeInTheDocument();
      expect(screen.getByText('Content')).toBeInTheDocument();
    });

    it('renders description if provided', () => {
      render(
        <Card title="Card" description="This is a description">
          <div>Content</div>
        </Card>
      );

      expect(screen.getByText('This is a description')).toBeInTheDocument();
    });
  });

  describe('Stat', () => {
    it('displays label, value, and unit', () => {
      render(<Stat label="Revenue" value={1234.56} unit="USD" />);

      expect(screen.getByText('Revenue')).toBeInTheDocument();
      expect(screen.getByText('1234.56')).toBeInTheDocument();
      expect(screen.getByText('USD')).toBeInTheDocument();
    });

    it('displays trend indicator', () => {
      render(<Stat label="Growth" value={100} trend="up" trendValue="15%" />);

      expect(screen.getByText('15%')).toBeInTheDocument();
      expect(screen.getByTestId('trend-icon')).toBeInTheDocument();
    });
  });

  describe('ErrorAlert', () => {
    it('displays error message', () => {
      render(<ErrorAlert title="Error" message="Something went wrong" />);

      expect(screen.getByText('Error')).toBeInTheDocument();
      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    });

    it('calls onDismiss when close button clicked', () => {
      const onDismiss = vi.fn();
      render(
        <ErrorAlert
          title="Error"
          message="Error message"
          onDismiss={onDismiss}
        />
      );

      screen.getByRole('button').click();
      expect(onDismiss).toHaveBeenCalled();
    });
  });
});
```

## Hook Tests

### useAuth Hook Test

```typescript
// src/__tests__/hooks/useAuth.test.tsx
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../../hooks/useAuth';
import React from 'react';

describe('useAuth', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('initializes with no user', () => {
    const wrapper = ({ children }: any) => React.createElement(AuthProvider, {}, children);
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.isLoading).toBe(true);
  });

  it('loads user from stored token', async () => {
    localStorage.setItem('auth_token', 'valid_token');

    const wrapper = ({ children }: any) => React.createElement(AuthProvider, {}, children);
    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).not.toBeNull();
  });

  it('logs in user', async () => {
    const wrapper = ({ children }: any) => React.createElement(AuthProvider, {}, children);
    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.login('user@example.com', 'SecurePass123!', 'tenant_123');
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).not.toBeNull();
    expect(localStorage.getItem('auth_token')).not.toBeNull();
  });

  it('logs out user', async () => {
    localStorage.setItem('auth_token', 'valid_token');

    const wrapper = ({ children }: any) => React.createElement(AuthProvider, {}, children);
    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      result.current.logout();
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(localStorage.getItem('auth_token')).toBeNull();
  });
});
```

## Integration Tests

### Dashboard Integration Test

```typescript
// src/__tests__/pages/AdminConsole.test.tsx
import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../hooks/useAuth';
import { TenantProvider } from '../../hooks/useTenant';
import AdminConsole from '../../pages/AdminConsole';

function renderWithProviders(component: React.ReactElement) {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <TenantProvider>
          {component}
        </TenantProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

describe('AdminConsole', () => {
  beforeEach(() => {
    localStorage.setItem('auth_token', 'admin_token');
    localStorage.setItem('tenant_id', 'admin_tenant');
  });

  it('renders platform KPIs', async () => {
    renderWithProviders(<AdminConsole />);

    await waitFor(() => {
      expect(screen.getByText(/Active Tenants/i)).toBeInTheDocument();
      expect(screen.getByText(/Monthly Revenue/i)).toBeInTheDocument();
      expect(screen.getByText(/Active Executions/i)).toBeInTheDocument();
    });
  });

  it('displays platform health status', async () => {
    renderWithProviders(<AdminConsole />);

    await waitFor(() => {
      expect(screen.getByText(/Platform Health/i)).toBeInTheDocument();
      expect(screen.getByText(/Uptime/i)).toBeInTheDocument();
    });
  });

  it('shows tenant registry table', async () => {
    renderWithProviders(<AdminConsole />);

    await waitFor(() => {
      expect(screen.getByText(/Tenant Registry/i)).toBeInTheDocument();
    });
  });
});
```

## API Mocking Strategy

### Setup MSW (Mock Service Worker)

```bash
npm install --save-dev msw
```

Create `src/__tests__/mocks/handlers.ts`:

```typescript
import { http, HttpResponse } from 'msw';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const handlers = [
  // Auth endpoints
  http.post(`${API_URL}/platform/ui/login`, () => {
    return HttpResponse.json({
      status: 'success',
      data: {
        user: { user_id: '123', email: 'user@example.com', role: 'admin' },
        tenant: { tenant_id: 'tenant_123', organization_name: 'Test Org' },
        token: { access_token: 'mock_token', token_type: 'Bearer', expires_in: 3600 },
      },
    });
  }),

  // Tenant endpoints
  http.get(`${API_URL}/platform/ui/tenant`, () => {
    return HttpResponse.json({
      status: 'success',
      data: {
        tenant_id: 'tenant_123',
        organization_name: 'Test Org',
        status: 'active',
        subscription_plan: 'professional',
      },
    });
  }),

  // Apps endpoints
  http.get(`${API_URL}/platform/ui/apps`, () => {
    return HttpResponse.json({
      status: 'success',
      data: {
        items: [
          {
            app_id: 'app_123',
            name: 'Test App',
            version: '1.0.0',
            status: 'deployed',
          },
        ],
        total: 1,
      },
    });
  }),
];
```

Update `src/__tests__/setup.ts` to use MSW:

```typescript
import { setupServer } from 'msw/node';
import { handlers } from './mocks/handlers';

const server = setupServer(...handlers);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

## Coverage Report

Generate coverage report:

```bash
npm run test:coverage
```

Coverage threshold by file type:

| Type | Threshold |
|------|-----------|
| Statements | 80% |
| Branches | 80% |
| Functions | 80% |
| Lines | 80% |

View HTML report:
```bash
open coverage/index.html
```

## Testing Best Practices

### 1. Unit Tests

- Test **one** function/component per describe block
- Use **semantic queries** (getByRole, getByLabelText)
- Avoid testing implementation details
- Cover **happy path** and **error scenarios**

```typescript
✅ GOOD
it('disables button when loading', () => {
  render(<Button loading>Submit</Button>);
  expect(screen.getByRole('button')).toBeDisabled();
});

❌ AVOID
it('has correct className', () => {
  const { container } = render(<Button>Click</Button>);
  expect(container.querySelector('.btn')).toBeDefined();
});
```

### 2. Component Tests

- Test **user interactions**, not internal state
- Mock **expensive operations** (API calls, timers)
- Use **userEvent** for realistic interactions
- Test **accessibility** attributes

```typescript
✅ GOOD
it('submits form when button clicked', async () => {
  const onSubmit = vi.fn();
  render(<Form onSubmit={onSubmit} />);
  
  await userEvent.click(screen.getByRole('button', { name: /submit/i }));
  expect(onSubmit).toHaveBeenCalled();
});
```

### 3. Hook Tests

- Use **renderHook** for isolated testing
- Use **act** for state updates
- Mock **context providers** with wrapper
- Test **side effects** with waitFor

```typescript
✅ GOOD
it('updates metrics on poll interval', async () => {
  vi.useFakeTimers();
  const { result } = renderHook(() => useMetrics());
  
  vi.advanceTimersByTime(30000);
  
  await waitFor(() => {
    expect(result.current.tenantMetrics).not.toBeNull();
  });
});
```

### 4. Async Testing

- Always use **async/await**
- Use **waitFor** for async operations
- Avoid hard-coded delays
- Mock timers for polling

```typescript
✅ GOOD
it('loads data', async () => {
  render(<Dashboard />);
  
  await waitFor(() => {
    expect(screen.getByTestId('data')).toBeInTheDocument();
  });
});

❌ AVOID
setTimeout(() => {
  expect(screen.getByTestId('data')).toBeInTheDocument();
}, 1000);
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - run: npm ci
      
      - run: npm run test
      
      - run: npm run test:coverage
      
      - uses: codecov/codecov-action@v3
        with:
          files: ./coverage/coverage-final.json
```

## Debugging Tests

### Run single test
```bash
npm run test -- formatCurrency.test.ts
```

### Debug in browser
```bash
npm run test -- --inspect-brk formatCurrency.test.ts
```

### Watch mode with UI
```bash
npm run test:watch
```

## Performance Testing

Test performance thresholds:

```typescript
it('renders dashboard in < 1s', async () => {
  const start = performance.now();
  render(<AdminConsole />);
  
  await waitFor(() => {
    expect(screen.getByTestId('dashboard')).toBeInTheDocument();
  });
  
  const duration = performance.now() - start;
  expect(duration).toBeLessThan(1000);
});
```

---

**Testing Version**: 1.0.0  
**Last Updated**: 2024  
**Status**: Production Ready
