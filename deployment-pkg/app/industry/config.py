"""
Industry abstraction layer.

Provides industry-specific configuration, workflow mapping, default modules,
and supported integrations.  The platform engine is generic — this registry
drives how tenants are pre-configured when they choose their industry.

Supported industries
--------------------
- hospital       — Healthcare / Hospitals
- school         — Schools / Education
- it_company     — IT / Software Companies
- recruitment    — Recruitment / HR Agencies
- payroll_finance — Finance, Payroll & Invoicing
- service_business — General Service Businesses
- generic        — Generic Enterprise (default)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class IndustryType(str, Enum):
    HOSPITAL = "hospital"
    SCHOOL = "school"
    IT_COMPANY = "it_company"
    RECRUITMENT = "recruitment"
    PAYROLL_FINANCE = "payroll_finance"
    SERVICE_BUSINESS = "service_business"
    GENERIC = "generic"


@dataclass
class IndustryConfig:
    industry: IndustryType
    display_name: str
    description: str
    icon: str
    default_workflows: List[str]
    default_modules: List[str]
    supported_integrations: List[str]
    country_compliance_required: bool = False
    tags: List[str] = field(default_factory=list)


INDUSTRY_REGISTRY: Dict[IndustryType, IndustryConfig] = {
    IndustryType.HOSPITAL: IndustryConfig(
        industry=IndustryType.HOSPITAL,
        display_name="Hospital / Healthcare",
        icon="🏥",
        description=(
            "Patient management, staff scheduling, billing, and compliance workflows "
            "for hospitals, clinics, and healthcare providers."
        ),
        default_workflows=["onboarding", "payroll", "invoice", "meeting"],
        default_modules=[
            "employee_management",
            "attendance_tracking",
            "payroll_run_engine",
            "payslip_generator",
            "customer_management",
            "invoice_builder",
            "reports_dashboard",
        ],
        supported_integrations=["email", "calendar", "payroll", "invoice"],
        country_compliance_required=True,
        tags=["healthcare", "medical", "clinic", "hospital"],
    ),
    IndustryType.SCHOOL: IndustryConfig(
        industry=IndustryType.SCHOOL,
        display_name="School / Education",
        icon="🏫",
        description=(
            "Student enrollment, teacher management, fee collection, timetabling, "
            "and reporting for schools, colleges, and training institutes."
        ),
        default_workflows=["onboarding", "invoice", "meeting"],
        default_modules=[
            "employee_management",
            "attendance_tracking",
            "customer_management",
            "invoice_builder",
            "payment_tracker",
            "reports_dashboard",
        ],
        supported_integrations=["email", "calendar", "invoice"],
        tags=["education", "school", "college", "training", "students"],
    ),
    IndustryType.IT_COMPANY: IndustryConfig(
        industry=IndustryType.IT_COMPANY,
        display_name="IT / Software Company",
        icon="💻",
        description=(
            "Project tracking, client billing, technical recruitment, HR operations, "
            "and CRM for IT firms and software companies."
        ),
        default_workflows=["recruitment", "onboarding", "invoice", "sales", "meeting"],
        default_modules=[
            "employee_management",
            "lead_capture",
            "deal_pipeline",
            "invoice_builder",
            "activity_log",
            "reports_dashboard",
        ],
        supported_integrations=["email", "calendar", "crm", "invoice"],
        tags=["it", "software", "technology", "saas", "startup"],
    ),
    IndustryType.RECRUITMENT: IndustryConfig(
        industry=IndustryType.RECRUITMENT,
        display_name="Recruitment / HR Agency",
        icon="🎯",
        description=(
            "Candidate pipeline, client CRM, placement tracking, commission calculation, "
            "and employer branding for recruitment and HR agencies."
        ),
        default_workflows=["recruitment", "onboarding", "sales"],
        default_modules=[
            "lead_capture",
            "deal_pipeline",
            "contact_management",
            "activity_log",
            "employee_management",
            "payroll_run_engine",
            "reports_dashboard",
        ],
        supported_integrations=["email", "calendar", "crm"],
        tags=["recruitment", "staffing", "hr", "talent", "hiring"],
    ),
    IndustryType.PAYROLL_FINANCE: IndustryConfig(
        industry=IndustryType.PAYROLL_FINANCE,
        display_name="Finance / Payroll",
        icon="💰",
        description=(
            "Payroll processing, tax calculation, invoicing, financial reporting, "
            "and compliance for payroll bureaus and finance teams."
        ),
        default_workflows=["payroll", "invoice"],
        default_modules=[
            "employee_management",
            "attendance_tracking",
            "salary_configuration",
            "payroll_run_engine",
            "payslip_generator",
            "tax_calculator",
            "invoice_builder",
            "payment_tracker",
            "reports_dashboard",
        ],
        supported_integrations=["email", "payroll", "invoice"],
        country_compliance_required=True,
        tags=["finance", "payroll", "accounting", "tax", "invoicing"],
    ),
    IndustryType.SERVICE_BUSINESS: IndustryConfig(
        industry=IndustryType.SERVICE_BUSINESS,
        display_name="Service Business",
        icon="🔧",
        description=(
            "Job scheduling, client billing, field staff management, and CRM "
            "for service businesses, agencies, and operations teams."
        ),
        default_workflows=["meeting", "invoice", "sales", "onboarding"],
        default_modules=[
            "customer_management",
            "invoice_builder",
            "deal_pipeline",
            "activity_log",
            "reports_dashboard",
        ],
        supported_integrations=["email", "calendar", "invoice", "crm"],
        tags=["service", "field", "operations", "agency", "consulting"],
    ),
    IndustryType.GENERIC: IndustryConfig(
        industry=IndustryType.GENERIC,
        display_name="General Enterprise",
        icon="🏢",
        description=(
            "Generic business operations with customisable workflows. "
            "Suitable for any organisation not covered by a specific template."
        ),
        default_workflows=["onboarding", "meeting", "invoice"],
        default_modules=[
            "employee_management",
            "reports_dashboard",
        ],
        supported_integrations=["email", "calendar"],
        tags=["general", "enterprise", "custom", "operations"],
    ),
}


def get_industry_config(industry: str) -> IndustryConfig:
    """
    Return IndustryConfig for the given industry string.
    Falls back to GENERIC if the industry is unknown.
    """
    try:
        itype = IndustryType(industry.lower())
    except ValueError:
        itype = IndustryType.GENERIC
    return INDUSTRY_REGISTRY.get(itype, INDUSTRY_REGISTRY[IndustryType.GENERIC])


def list_industries() -> List[Dict]:
    """Return a serialisable list of all supported industries."""
    return [
        {
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
        for cfg in INDUSTRY_REGISTRY.values()
    ]
