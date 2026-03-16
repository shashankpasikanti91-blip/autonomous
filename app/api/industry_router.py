"""
Industry API endpoints.

GET  /api/industries           — list all supported industries
GET  /api/industries/{id}      — get config for a specific industry
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from industry.config import get_industry_config, list_industries, IndustryType

router = APIRouter(prefix="/api/industries", tags=["Industries"])


@router.get("", summary="List all supported industries")
def get_industries() -> Dict[str, Any]:
    """Return every industry the platform supports, with its default workflows and modules."""
    return {
        "industries": list_industries(),
        "total": len(list_industries()),
    }


@router.get("/{industry_id}", summary="Get configuration for a specific industry")
def get_industry(industry_id: str) -> Dict[str, Any]:
    """
    Return the configuration for a single industry.

    Valid IDs: hospital, school, it_company, recruitment, payroll_finance,
               service_business, generic
    """
    valid_ids = [i.value for i in IndustryType]
    if industry_id not in valid_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Industry '{industry_id}' not found. Valid options: {valid_ids}",
        )
    cfg = get_industry_config(industry_id)
    return {
        "id": cfg.industry.value,
        "name": cfg.display_name,
        "icon": cfg.icon,
        "description": cfg.description,
        "default_workflows": cfg.default_workflows,
        "default_modules": cfg.default_modules,
        "supported_integrations": cfg.supported_integrations,
        "country_compliance_required": cfg.country_compliance_required,
        "tags": cfg.tags,
    }
