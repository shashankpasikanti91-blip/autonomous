"""
Tenant (organization) management endpoints.

- POST /api/tenants         — create tenant/org with slug/domain
- GET  /api/tenants         — list tenants for an owner email (simple filter)
- GET  /api/tenants/{slug}  — fetch tenant by slug
"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.service import db_service
from app.db.models import Organization

router = APIRouter(prefix="/api/tenants", tags=["Tenants"])


class CreateTenantRequest(BaseModel):
    owner_email: str = Field(..., description="Owner email; created if missing")
    name: str = Field(..., description="Organization display name")
    country: Optional[str] = None
    industry: Optional[str] = None
    slug: Optional[str] = Field(None, description="URL-safe slug (subdomain)")
    custom_domain: Optional[str] = Field(None, description="Optional custom domain host")


@router.post("", summary="Create a new tenant/organization")
def create_tenant(body: CreateTenantRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    try:
        owner = db_service.get_or_create_user(db, email=body.owner_email)
        org = db_service.create_organization(
            db,
            owner_id=str(owner.id),
            name=body.name,
            country=body.country,
            industry=body.industry,
            slug=body.slug,
            custom_domain=body.custom_domain,
        )
        return {"ok": True, "organization": org.to_dict()}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("", summary="List organizations for an owner")
def list_tenants(
    owner_email: str = Query(..., description="Owner email to filter"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    owner = db_service.get_or_create_user(db, email=owner_email)
    orgs = db_service.list_organizations_for_user(db, user_id=str(owner.id))
    return {"ok": True, "organizations": [o.to_dict() for o in orgs]}


@router.get("/{slug}", summary="Fetch tenant by slug")
def get_tenant(slug: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    org = db_service.get_organization_by_slug(db, slug)
    if not org:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"ok": True, "organization": org.to_dict()}
