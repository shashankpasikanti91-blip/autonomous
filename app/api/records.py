"""
FastAPI router — /api/records
Provides REST endpoints for real database operations.
Called by the frontend orchestrator (replaces Supabase direct calls).

All routes enforce organization isolation via org_id query param.
For production: replace org_id param with JWT-decoded claim.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.service import db_service
from app.api.deps import resolve_org
from app.db.models import Organization

router = APIRouter(prefix="/api/records", tags=["records"])


# ─── Request / Response schemas ───────────────────────────────────────────────

class CreateAppRequest(BaseModel):
    name: str
    description: Optional[str] = None
    org_id: Optional[str] = None
    user_prompt: Optional[str] = None          # triggers business-template detection
    app_type: Optional[str] = None             # e.g. 'payroll', 'invoice', 'crm', 'custom'
    architecture_summary: Optional[str] = None # free-text architecture description


class SaveSchemaRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    app_id: str
    schema_data: Dict[str, Any] = Field(alias="schema_json")
    version: int = 1
    org_id: Optional[str] = None


class InsertRecordRequest(BaseModel):
    app_id: str
    record_json: Dict[str, Any]
    org_id: Optional[str] = None


class LogExecutionRequest(BaseModel):
    action: str
    status: str = "success"
    app_id: Optional[str] = None
    response: Optional[Dict[str, Any]] = None
    org_id: Optional[str] = None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/apps", summary="Create a new app and persist to database")
def create_app(
    body: CreateAppRequest,
    org: Organization = Depends(resolve_org),
    db: Session = Depends(get_db),
):
    """
    Insert a real row into the apps table.
    Returns the new app's id and metadata.
    """
    app = db_service.create_app(
        db,
        org_id=str(org.id),
        name=body.name,
        description=body.description,
        user_prompt=body.user_prompt,
        app_type=body.app_type,
        architecture_summary=body.architecture_summary,
    )
    return {"ok": True, "app": app.to_dict()}


@router.get("/apps", summary="List all apps for an organisation")
def list_apps(
    org: Organization = Depends(resolve_org),
    db: Session = Depends(get_db),
):
    apps = db_service.list_apps(db, org_id=str(org.id))
    return {"ok": True, "apps": [a.to_dict() for a in apps]}


@router.get("/apps/{app_id}", summary="Get a single app")
def get_app(
    app_id: str,
    org: Organization = Depends(resolve_org),
    db: Session = Depends(get_db),
):
    app = db_service.get_app(db, app_id=app_id, org_id=str(org.id))
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    return {"ok": True, "app": app.to_dict()}


@router.post("/schemas", summary="Save structured app schema to database")
def save_schema(
    body: SaveSchemaRequest,
    org: Organization = Depends(resolve_org),
    db: Session = Depends(get_db),
):
    """
    Stores validated JSON schema in app_schemas table.
    """
    schema = db_service.save_schema(
        db,
        app_id=body.app_id,
        org_id=str(org.id),
        schema_json=body.schema_data,
        version=body.version,
    )
    if not schema:
        raise HTTPException(status_code=404, detail="App not found or access denied")
    return {"ok": True, "schema": schema.to_dict()}


@router.post("/data", summary="Insert a real data record into app_records")
def insert_record(
    body: InsertRecordRequest,
    org: Organization = Depends(resolve_org),
    db: Session = Depends(get_db),
):
    """
    Every form submission / data entry writes a real row to app_records.
    """
    record = db_service.insert_record(
        db,
        app_id=body.app_id,
        org_id=str(org.id),
        record_json=body.record_json,
    )
    if not record:
        raise HTTPException(status_code=404, detail="App not found or access denied")
    return {"ok": True, "record": record.to_dict()}


@router.get("/data/{app_id}", summary="List data records for an app")
def list_records(
    app_id: str,
    org: Organization = Depends(resolve_org),
    limit: int = Query(default=100, le=1000),
    db: Session = Depends(get_db),
):
    records = db_service.list_records(db, app_id=app_id, org_id=str(org.id), limit=limit)
    return {"ok": True, "records": [r.to_dict() for r in records]}


@router.post("/logs", summary="Write an immutable execution log entry")
def log_execution(
    body: LogExecutionRequest,
    org: Organization = Depends(resolve_org),
    db: Session = Depends(get_db),
):
    log = db_service.log_execution(
        db,
        action=body.action,
        status=body.status,
        app_id=body.app_id,
        response=body.response,
    )
    return {"ok": True, "log": log.to_dict()}


@router.get("/logs/{app_id}", summary="Fetch execution logs for an app")
def get_logs(
    app_id: str,
    org: Organization = Depends(resolve_org),
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
):
    logs = db_service.list_logs(db, app_id=app_id, org_id=str(org.id), limit=limit)
    return {"ok": True, "logs": [l.to_dict() for l in logs]}


@router.get("/rules", summary="Fetch country compliance rules")
def get_country_rules(
    country: str = Query(...),
    industry: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    rules = db_service.get_rules(db, country=country, industry=industry)
    return {"ok": True, "rules": [r.to_dict() for r in rules]}


# ─── Direct template-table CRUD ───────────────────────────────────────────────
# Whitelisted table names that the frontend may access directly.
# Only these names are accepted — no arbitrary SQL injection possible.
_ALLOWED_TEMPLATE_TABLES: set[str] = {
    # payroll
    "employees", "attendance", "salary_components", "payroll_runs", "payslips",
    # invoice
    "customers", "products", "invoices", "invoice_items",
    # crm
    "leads", "deals", "activities", "contacts",
}


class TableRowInsertRequest(BaseModel):
    row: Dict[str, Any]


@router.get(
    "/table/{table_name}",
    summary="Fetch rows from a template table",
)
def list_template_table_rows(
    table_name: str,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
):
    """
    Return up to *limit* rows from a whitelisted template table.
    Rows are returned newest-first (by id DESC).
    """
    from sqlalchemy import text as _text

    if table_name not in _ALLOWED_TEMPLATE_TABLES:
        raise HTTPException(status_code=400, detail=f"Table '{table_name}' is not allowed.")

    try:
        result = db.execute(
            _text(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT :limit"),
            {"limit": limit},
        )
        cols = list(result.keys())
        rows = [dict(zip(cols, row)) for row in result.fetchall()]
        # Serialise any non-JSON-safe types (dates, decimals, etc.)
        import decimal, datetime
        def _serial(v: Any) -> Any:
            if isinstance(v, (datetime.date, datetime.datetime)):
                return v.isoformat()
            if isinstance(v, decimal.Decimal):
                return float(v)
            return v
        rows = [{k: _serial(v) for k, v in r.items()} for r in rows]
        return {"ok": True, "table": table_name, "columns": cols, "rows": rows}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/table/{table_name}",
    summary="Insert a row into a template table",
)
def insert_template_table_row(
    table_name: str,
    body: TableRowInsertRequest,
    db: Session = Depends(get_db),
):
    """
    Insert one row into a whitelisted template table.
    Pass the column values as a plain dict in ``row``.
    Auto-generated columns (id, created_at, updated_at) are excluded from
    the insert so the database defaults apply.
    """
    from sqlalchemy import text as _text

    if table_name not in _ALLOWED_TEMPLATE_TABLES:
        raise HTTPException(status_code=400, detail=f"Table '{table_name}' is not allowed.")

    # Strip server-managed columns so we never override them
    _skip = {"id", "created_at", "updated_at"}
    row = {k: v for k, v in body.row.items() if k not in _skip and v is not None and v != ""}

    if not row:
        raise HTTPException(status_code=400, detail="No column values provided.")

    cols = ", ".join(row.keys())
    params = ", ".join(f":{k}" for k in row.keys())
    try:
        db.execute(_text(f"INSERT INTO {table_name} ({cols}) VALUES ({params})"), row)
        db.commit()
        return {"ok": True, "table": table_name, "inserted": row}
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
