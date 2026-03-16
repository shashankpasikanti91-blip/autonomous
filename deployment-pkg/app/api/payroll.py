"""
Payroll operational endpoints.

POST /api/payroll/{app_id}/generate
    Generates a new payroll run for the given app and month.
    Creates a row in the `payroll_runs` table and returns the run details.
"""

from __future__ import annotations

import calendar
import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import get_db

router = APIRouter(prefix="/api/payroll", tags=["payroll"])


# ─── Request / Response models ────────────────────────────────────────────────

class GeneratePayrollRequest(BaseModel):
    month: Optional[str] = None  # "YYYY-MM"; defaults to current month


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _month_bounds(month: Optional[str]) -> tuple[datetime.date, datetime.date]:
    """Return (period_start, period_end) for a YYYY-MM string, or current month."""
    today = datetime.date.today()
    if month:
        try:
            year, mon = [int(x) for x in month.split("-")]
        except (ValueError, AttributeError):
            raise HTTPException(status_code=422, detail="month must be YYYY-MM")
    else:
        year, mon = today.year, today.month

    period_start = datetime.date(year, mon, 1)
    last_day = calendar.monthrange(year, mon)[1]
    period_end = datetime.date(year, mon, last_day)
    return period_start, period_end


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post(
    "/{app_id}/generate",
    summary="Generate a payroll run for an app",
)
def generate_payroll(
    app_id: str = Path(..., description="The UUID of the payroll app"),
    body: GeneratePayrollRequest = GeneratePayrollRequest(),
    db: Session = Depends(get_db),
):
    """
    Creates a completed payroll run row in `payroll_runs` for the requested
    month (or the current month when omitted).  Returns the new run record.
    """
    period_start, period_end = _month_bounds(body.month)
    today = datetime.date.today()

    month_label = period_start.strftime("%B %Y")  # e.g. "July 2025"

    sql = text(
        """
        INSERT INTO payroll_runs
            (period_start, period_end, run_date, status, notes, created_at, updated_at)
        VALUES
            (:period_start, :period_end, :run_date, 'completed', :notes,
             NOW(), NOW())
        RETURNING id, period_start, period_end, run_date, status, total_gross,
                  total_net, total_deductions, notes, created_at
        """
    )

    try:
        result = db.execute(
            sql,
            {
                "period_start": period_start,
                "period_end": period_end,
                "run_date": today,
                "notes": f"Auto-generated for {month_label}",
            },
        )
        db.commit()
        row = result.fetchone()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))

    import decimal

    def _serial(v):
        if isinstance(v, (datetime.date, datetime.datetime)):
            return v.isoformat()
        if isinstance(v, decimal.Decimal):
            return float(v)
        return v

    cols = list(result.keys())
    run = {k: _serial(v) for k, v in zip(cols, row)}

    return {
        "ok": True,
        "message": f"Payroll generated successfully for {month_label}",
        "month_label": month_label,
        "payroll_run": run,
    }
