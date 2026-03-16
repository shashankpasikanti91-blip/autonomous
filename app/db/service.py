"""
Database service layer — SRP Autonomous OS.

Provides high-level CRUD operations for all foundation tables.
All methods enforce multi-tenant isolation via organization_id.

Usage
-----
    from app.db.service import db_service
    from app.db.database import SessionLocal

    with SessionLocal() as db:
        app = db_service.create_app(db, org_id="...", name="Visa Tracker", description="...")
        log = db_service.log_execution(db, app_id=app.id, action="app_created", status="success")
"""
from __future__ import annotations

import logging
import re
import uuid
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .models import App, AppSchema, AppRecord, CountryRule, ExecutionLog, CoreUser, Organization

logger = logging.getLogger(__name__)

# Fixed demo org/user UUIDs used during local development (seeded in 001_init.sql)
DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"
DEMO_ORG_ID  = "00000000-0000-0000-0000-000000000010"

# ── Module → icon / table mapping for blueprint building ─────────────────────
_MODULE_META: Dict[str, Dict[str, str]] = {
    # ── payroll ──────────────────────────────────────────────────────────────
    "employee_management":  {"icon": "👥", "table": "employees",         "label": "Employees"},
    "attendance_tracking":  {"icon": "📅", "table": "attendance",        "label": "Attendance"},
    "salary_configuration": {"icon": "💰", "table": "salary_components", "label": "Salary Config"},
    "payroll_run_engine":   {"icon": "▶️", "table": "payroll_runs",      "label": "Payroll Runs"},
    "payslip_generator":    {"icon": "🧾", "table": "payslips",          "label": "Payslips"},
    "tax_calculator":       {"icon": "📋", "table": "tax_rules",         "label": "Tax Rules"},
    # ── invoice ───────────────────────────────────────────────────────────────
    "customer_management":  {"icon": "🏢", "table": "clients",           "label": "Customers"},
    "product_catalogue":    {"icon": "📦", "table": "products",          "label": "Products"},
    "invoice_builder":      {"icon": "🧾", "table": "invoices",          "label": "Invoices"},
    "tax_engine":           {"icon": "📋", "table": "tax_rules",         "label": "Tax Engine"},
    "payment_tracker":      {"icon": "💳", "table": "payments",          "label": "Payments"},
    "pdf_generator":        {"icon": "📄", "table": None,                "label": "PDF Generator"},
    "email_dispatcher":     {"icon": "📧", "table": None,                "label": "Email Dispatcher"},
    # ── crm ───────────────────────────────────────────────────────────────────
    "lead_capture":         {"icon": "🎯", "table": "leads",             "label": "Leads"},
    "deal_pipeline":        {"icon": "🔀", "table": "deals",             "label": "Deals"},
    "activity_log":         {"icon": "📝", "table": "activities",        "label": "Activities"},
    "contact_management":   {"icon": "👤", "table": "contacts",          "label": "Contacts"},
    "email_integration":    {"icon": "📧", "table": None,                "label": "Email"},
    "sales_forecasting":    {"icon": "📈", "table": None,                "label": "Forecasting"},
    # ── shared ────────────────────────────────────────────────────────────────
    "reports_dashboard":    {"icon": "📊", "table": None,                "label": "Reports"},
}

_SUMMARY_CARD_DEFAULTS: Dict[str, List[Dict[str, str]]] = {
    "payroll": [
        {"label": "Total Employees", "icon": "👥", "color": "blue"},
        {"label": "Last Payroll Run", "icon": "▶️", "color": "green"},
        {"label": "Pending Payslips", "icon": "🧾", "color": "orange"},
    ],
    "invoice": [
        {"label": "Total Invoices", "icon": "🧾", "color": "blue"},
        {"label": "Outstanding",    "icon": "💰", "color": "orange"},
        {"label": "Paid This Month","icon": "✅", "color": "green"},
    ],
    "crm": [
        {"label": "Active Leads",   "icon": "🎯", "color": "blue"},
        {"label": "Open Deals",     "icon": "🔀", "color": "purple"},
        {"label": "Won This Month", "icon": "🏆", "color": "green"},
    ],
}


def _slugify(name: str) -> str:
    """Create a URL-safe slug for organization domains."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return slug or uuid.uuid4().hex[:8]


def _build_blueprint(app_name: str, template: dict) -> dict:
    """Convert a business template dict into a UI blueprint for TemplateRenderer."""
    template_name: str = template["name"]
    modules: list = template.get("modules", [])

    sidebar = []
    for mod in modules:
        meta = _MODULE_META.get(mod)
        if meta:
            item: Dict[str, Any] = {
                "id":    mod,
                "label": meta["label"],
                "icon":  meta["icon"],
                "type":  "crud" if meta["table"] else "action",
            }
            if meta["table"]:
                item["table"] = meta["table"]
            else:
                item["description"] = meta["label"]
            sidebar.append(item)
        else:
            # Fallback: derive label from module name
            sidebar.append({
                "id":    mod,
                "label": mod.replace("_", " ").replace("-", " ").title(),
                "icon":  "⚙️",
                "type":  "crud",
                "table": mod,
            })

    summary_cards = [
        {"label": card["label"], "value": "0", "icon": card["icon"], "color": card["color"]}
        for card in _SUMMARY_CARD_DEFAULTS.get(template_name, [])
    ]

    return {
        "title":         app_name,
        "description":   f"Managed {template_name.title()} application",
        "sidebar":       sidebar,
        "summary_cards": summary_cards,
    }


class DatabaseService:
    """Typed service layer for all foundation tables."""

    # -------------------------------------------------------------------------
    # core_users
    # -------------------------------------------------------------------------
    def get_or_create_user(self, db: Session, email: str, role: str = "owner") -> CoreUser:
        user = db.query(CoreUser).filter(CoreUser.email == email).first()
        if user:
            return user
        user = CoreUser(email=email, role=role)
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("Created user: %s", email)
        return user

    # -------------------------------------------------------------------------
    # organizations
    # -------------------------------------------------------------------------
    def create_organization(
        self,
        db: Session,
        owner_id: str,
        name: str,
        country: Optional[str] = None,
        industry: Optional[str] = None,
        slug: Optional[str] = None,
        custom_domain: Optional[str] = None,
    ) -> Organization:
        slug_value = slug or _slugify(name)
        existing = db.query(Organization).filter(Organization.slug == slug_value).first()
        if existing:
            raise ValueError(f"Slug '{slug_value}' already exists")
        if custom_domain:
            clash = db.query(Organization).filter(Organization.custom_domain == custom_domain).first()
            if clash:
                raise ValueError(f"Domain '{custom_domain}' already mapped")

        org = Organization(
            owner_id=owner_id,
            name=name,
            country=country,
            industry=industry,
            slug=slug_value,
            custom_domain=custom_domain,
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        logger.info("Created organization '%s' (%s)", name, org.slug)
        return org

    def get_organization(self, db: Session, org_id: str) -> Optional[Organization]:
        return db.query(Organization).filter(Organization.id == org_id).first()

    def get_organization_by_slug(self, db: Session, slug: str) -> Optional[Organization]:
        return db.query(Organization).filter(Organization.slug == slug).first()

    def get_organization_by_domain(self, db: Session, host: str) -> Optional[Organization]:
        return db.query(Organization).filter(Organization.custom_domain == host).first()

    def list_organizations_for_user(self, db: Session, user_id: str) -> List[Organization]:
        return (
            db.query(Organization)
            .filter(Organization.owner_id == user_id)
            .order_by(Organization.created_at.desc())
            .all()
        )

    # -------------------------------------------------------------------------
    # apps
    # -------------------------------------------------------------------------
    def create_app(
        self,
        db: Session,
        org_id: str,
        name: str,
        description: Optional[str] = None,
        status: str = "active",
        user_prompt: Optional[str] = None,
        app_type: Optional[str] = None,
        architecture_summary: Optional[str] = None,
    ) -> App:
        # ── Template detection ──────────────────────────────────────────────
        detected_modules: Optional[list] = None
        detected_blueprint: Optional[dict] = None
        template: Optional[dict] = None   # always defined before use
        if user_prompt:
            try:
                from backend.templates.business_templates import get_template_by_prompt
                template = get_template_by_prompt(user_prompt)
            except ImportError:
                logger.warning("business_templates module not found; skipping template detection.")
                template = None

            if template:
                # Override app_type from the detected template
                app_type = template["name"]
                print(f"[Template Detection] Detected template: '{app_type}' for prompt: \"{user_prompt}\"")
                logger.info(
                    "Business template '%s' detected for app '%s'; provisioning tables.",
                    template["name"], name,
                )
                for ddl in template["tables"]:
                    try:
                        db.execute(text(ddl))
                        db.commit()
                    except Exception as tbl_err:
                        db.rollback()
                        logger.warning(
                            "Skipped table (already exists or error): %s", tbl_err
                        )
                detected_modules = template["modules"]
                detected_blueprint = _build_blueprint(name, template)
            else:
                print(f"[Template Detection] No template matched for prompt: \"{user_prompt}\". Using custom.")
        else:
            print("[Template Detection] No user_prompt supplied. Using custom app.")

        # Ensure app_type always has a value
        if not app_type:
            app_type = "custom"

        # ── Auto-generate architecture_summary if not supplied ───────────────
        if architecture_summary is None:
            if template and detected_modules:
                # Build a human-readable, bullet-pointed summary for template apps
                module_bullets = "\n".join(
                    f"  - {m.replace('_', ' ').replace('-', ' ').title()}"
                    for m in detected_modules
                )
                template_label = template["name"].upper()
                architecture_summary = (
                    f"This {template_label} app includes:\n"
                    f"- PostgreSQL database\n"
                    f"- Structured business modules:\n"
                    f"{module_bullets}\n"
                    f"- REST API endpoints\n"
                    f"- Run tracking\n"
                    f"- Execution logs"
                )
            else:
                architecture_summary = (
                    "This custom app includes:\n"
                    "- REST API endpoints\n"
                    "- Run tracking\n"
                    "- Execution logs"
                )

        # ── Persist the app row ─────────────────────────────────────────────
        app = App(
            organization_id=org_id,
            name=name,
            description=description,
            status=status,
            modules=detected_modules,
            app_type=app_type,
            blueprint=detected_blueprint,
            architecture_summary=architecture_summary,
        )
        db.add(app)
        db.commit()
        db.refresh(app)
        logger.info("Created app '%s' (id=%s) in org %s", name, app.id, org_id)

        # ── Audit log ───────────────────────────────────────────────────────
        log_response: Dict[str, Any] = {
            "app_id": str(app.id),
            "name": name,
            "org_id": org_id,
        }
        if detected_modules is not None:
            log_response["template_modules"] = detected_modules

        self.log_execution(
            db,
            app_id=str(app.id),
            action="app_created",
            status="success",
            response=log_response,
        )
        return app

    def get_app(self, db: Session, app_id: str, org_id: str) -> Optional[App]:
        """Fetch app — enforces org isolation."""
        return (
            db.query(App)
            .filter(App.id == app_id, App.organization_id == org_id)
            .first()
        )

    def list_apps(self, db: Session, org_id: str) -> List[App]:
        """List all apps belonging to an organisation."""
        return db.query(App).filter(App.organization_id == org_id).order_by(App.created_at.desc()).all()

    def update_app_status(self, db: Session, app_id: str, org_id: str, status: str) -> Optional[App]:
        app = self.get_app(db, app_id, org_id)
        if not app:
            return None
        setattr(app, "status", status)  # setattr avoids Pylance Column[str] false-positive
        db.commit()
        db.refresh(app)
        return app

    def delete_app(self, db: Session, app_id: str, org_id: str) -> bool:
        app = self.get_app(db, app_id, org_id)
        if not app:
            return False
        db.delete(app)
        db.commit()
        return True

    # -------------------------------------------------------------------------
    # app_schemas
    # -------------------------------------------------------------------------
    def save_schema(
        self,
        db: Session,
        app_id: str,
        org_id: str,
        schema_json: Dict[str, Any],
        version: int = 1,
    ) -> Optional[AppSchema]:
        # Verify app belongs to org
        app = self.get_app(db, app_id, org_id)
        if not app:
            logger.warning("save_schema: app %s not found in org %s", app_id, org_id)
            return None

        schema = AppSchema(app_id=app_id, schema_json=schema_json, version=version)
        db.add(schema)
        db.commit()
        db.refresh(schema)
        logger.info("Saved schema v%s for app %s", version, app_id)
        self.log_execution(
            db,
            app_id=app_id,
            action="schema_saved",
            status="success",
            response={"schema_id": str(schema.id), "version": version},
        )
        return schema

    def get_latest_schema(self, db: Session, app_id: str, org_id: str) -> Optional[AppSchema]:
        app = self.get_app(db, app_id, org_id)
        if not app:
            return None
        return (
            db.query(AppSchema)
            .filter(AppSchema.app_id == app_id)
            .order_by(AppSchema.version.desc())
            .first()
        )

    # -------------------------------------------------------------------------
    # app_records
    # -------------------------------------------------------------------------
    def insert_record(
        self,
        db: Session,
        app_id: str,
        org_id: str,
        record_json: Dict[str, Any],
    ) -> Optional[AppRecord]:
        app = self.get_app(db, app_id, org_id)
        if not app:
            logger.warning("insert_record: app %s not found in org %s", app_id, org_id)
            return None

        record = AppRecord(app_id=app_id, record_json=record_json)
        db.add(record)
        db.commit()
        db.refresh(record)
        logger.info("Inserted record %s for app %s", record.id, app_id)
        self.log_execution(
            db,
            app_id=app_id,
            action="record_inserted",
            status="success",
            response={"record_id": str(record.id)},
        )
        return record

    def list_records(
        self,
        db: Session,
        app_id: str,
        org_id: str,
        limit: int = 100,
    ) -> List[AppRecord]:
        app = self.get_app(db, app_id, org_id)
        if not app:
            return []
        return (
            db.query(AppRecord)
            .filter(AppRecord.app_id == app_id)
            .order_by(AppRecord.created_at.desc())
            .limit(limit)
            .all()
        )

    # -------------------------------------------------------------------------
    # country_rules
    # -------------------------------------------------------------------------
    def get_rules(
        self,
        db: Session,
        country: str,
        industry: Optional[str] = None,
    ) -> List[CountryRule]:
        q = db.query(CountryRule).filter(CountryRule.country == country)
        if industry:
            q = q.filter(CountryRule.industry == industry)
        return q.order_by(CountryRule.rule_type).all()

    # -------------------------------------------------------------------------
    # execution_logs
    # -------------------------------------------------------------------------
    def log_execution(
        self,
        db: Session,
        action: str,
        status: str = "success",
        app_id: Optional[str] = None,
        response: Optional[Dict[str, Any]] = None,
    ) -> ExecutionLog:
        log = ExecutionLog(
            app_id=app_id,
            action=action,
            status=status,
            response_json=response or {},
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    def list_logs(
        self,
        db: Session,
        app_id: str,
        org_id: str,
        limit: int = 100,
    ) -> List[ExecutionLog]:
        app = self.get_app(db, app_id, org_id)
        if not app:
            return []
        return (
            db.query(ExecutionLog)
            .filter(ExecutionLog.app_id == app_id)
            .order_by(ExecutionLog.created_at.desc())
            .limit(limit)
            .all()
        )


# Module-level singleton
db_service = DatabaseService()
