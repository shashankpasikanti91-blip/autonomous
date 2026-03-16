"""
Tenant resolution middleware for multi-tenant SaaS.

Extracts tenant slug from the HTTP Host / subdomain and attaches it to
request.state so any downstream handler can identify which tenant is making
the request.

Supported patterns
------------------
- autonomous.srpailabs.com          → tenant_slug = None  (platform/admin)
- acme.autonomous.srpailabs.com     → tenant_slug = "acme"
- localhost / 127.0.0.1             → tenant_slug = None  (local dev)
- Any other host                    → tenant_slug = None  (safe fallback)
"""

from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


class TenantMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware that resolves the current tenant from the request host.

    Sets ``request.state.tenant_slug`` (str | None) on every request.
    """

    def __init__(self, app: ASGIApp, platform_domain: str = "autonomous.srpailabs.com") -> None:
        super().__init__(app)
        self.platform_domain = platform_domain.lower()

    async def dispatch(self, request: Request, call_next) -> Response:
        host = request.headers.get("host", "").split(":")[0].lower()
        request.state.tenant_slug = self._extract_tenant(host)
        request.state.host = host
        response = await call_next(request)
        # Expose tenant info in response headers (useful for debugging)
        if request.state.tenant_slug:
            response.headers["X-Tenant"] = request.state.tenant_slug
        return response

    def _extract_tenant(self, host: str) -> Optional[str]:
        """Return the subdomain portion of the host, or None for the root domain."""
        # Local development — no tenant
        if host in ("localhost", "127.0.0.1", "0.0.0.0"):
            return None

        # Exact platform domain — no tenant (admin/platform area)
        if host == self.platform_domain:
            return None

        # subdomain.platform_domain → tenant is the subdomain
        suffix = f".{self.platform_domain}"
        if host.endswith(suffix):
            subdomain = host[: -len(suffix)]
            # Ignore common non-tenant subdomains
            if subdomain and subdomain not in ("www", "api", "static", "cdn", "mail"):
                return subdomain

        return None
