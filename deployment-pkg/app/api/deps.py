"""
Common API dependencies.

- resolve_org: maps incoming request to an Organization using tenant slug or
  custom domain, falling back to explicit org_id if provided.
"""
from typing import Optional

from fastapi import Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.service import db_service
from app.db.models import Organization


def resolve_org(
    request: Request,
    db: Session = Depends(get_db),
    org_id: Optional[str] = Query(default=None, description="Organization ID (optional if tenant slug/domain is set)"),
) -> Organization:
    """Resolve the organization for the request.

    Priority:
    1) Explicit org_id query parameter.
    2) Tenant slug from subdomain (set by TenantMiddleware).
    3) Custom domain mapping.
    """
    # 1) Explicit org_id
    if org_id:
        org = db_service.get_organization(db, org_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        return org

    # 2) Tenant slug from middleware / header
    tenant_slug = getattr(request.state, "tenant_slug", None) or request.headers.get("X-Tenant-Slug")
    if tenant_slug:
        org = db_service.get_organization_by_slug(db, tenant_slug)
        if org:
            return org

    # 3) Custom domain binding
    host = getattr(request.state, "host", None) or request.headers.get("host", "").split(":")[0].lower()
    if host:
        org = db_service.get_organization_by_domain(db, host)
        if org:
            return org

    raise HTTPException(status_code=400, detail="Unable to resolve tenant organization")
