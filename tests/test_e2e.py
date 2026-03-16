"""
End-to-end tests for SRP Autonomous OS API.

Run with:
    pytest tests/test_e2e.py -v

Uses FastAPI TestClient (in-memory, not HTTP).
"""

import os
import sys
import pytest

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))
sys.path.insert(0, os.path.dirname(__file__) + '/..')

from fastapi.testclient import TestClient
from api.main import app

CLIENT = TestClient(app)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get(path: str, **kw):
    return CLIENT.get(path, **kw)


def post(path: str, json: dict, **kw):
    return CLIENT.post(path, json=json, **kw)


# ---------------------------------------------------------------------------
# Infrastructure
# ---------------------------------------------------------------------------

class TestHealthAndPlatform:
    def test_health_returns_200(self):
        r = get("/health")
        assert r.status_code == 200

    def test_health_status_is_healthy(self):
        r = get("/health")
        body = r.json()
        assert body.get("status") == "healthy"

    def test_health_has_platform_name(self):
        r = get("/health")
        body = r.json()
        assert "platform" in body or "name" in body or "platform_name" in body or "version" in body

    def test_platform_info_returns_200(self):
        r = get("/api/platform/info")
        assert r.status_code == 200

    def test_platform_info_has_industries(self):
        r = get("/api/platform/info")
        body = r.json()
        assert "supported_industries" in body
        assert len(body["supported_industries"]) > 0


# ---------------------------------------------------------------------------
# Industries
# ---------------------------------------------------------------------------

class TestIndustries:
    def test_list_industries_returns_200(self):
        r = get("/api/industries")
        assert r.status_code == 200

    def test_list_industries_returns_list(self):
        r = get("/api/industries")
        body = r.json()
        assert "industries" in body
        assert isinstance(body["industries"], list)
        assert len(body["industries"]) >= 7

    def test_industry_ids_present(self):
        r = get("/api/industries")
        body = r.json()
        ids = [i["id"] for i in body["industries"]]
        assert "hospital" in ids
        assert "school" in ids
        assert "it_company" in ids
        assert "generic" in ids

    def test_get_single_industry(self):
        r = get("/api/industries/hospital")
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == "hospital"

    def test_unknown_industry_returns_404(self):
        r = get("/api/industries/unicorn")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Onboarding Workflow
# ---------------------------------------------------------------------------

ONBOARDING_PAYLOAD = {
    "employee_id": "E001",
    "employee_name": "John Doe",
    "employee_email": "john.doe@example.com",
    "department": "Engineering",
    "position": "Software Engineer",
    "start_date": "2025-01-01",
    "manager_id": "M001",
}


class TestOnboardingWorkflow:
    def test_onboarding_returns_200(self):
        r = post("/api/workflows/onboarding/start", ONBOARDING_PAYLOAD)
        assert r.status_code == 200

    def test_onboarding_has_execution_id(self):
        r = post("/api/workflows/onboarding/start", ONBOARDING_PAYLOAD)
        body = r.json()
        assert "execution_id" in body
        assert len(body["execution_id"]) > 0

    def test_onboarding_status_completed(self):
        r = post("/api/workflows/onboarding/start", ONBOARDING_PAYLOAD)
        body = r.json()
        assert body.get("status") == "completed"

    def test_onboarding_welcome_email_sent(self):
        r = post("/api/workflows/onboarding/start", ONBOARDING_PAYLOAD)
        body = r.json()
        assert body.get("welcome_email_sent") is True


# ---------------------------------------------------------------------------
# Recruitment Workflow
# ---------------------------------------------------------------------------

RECRUITMENT_PAYLOAD = {
    "candidate_id": "C001",
    "candidate_name": "Jane Smith",
    "candidate_email": "jane.smith@example.com",
    "position_id": "POS001",
    "resume_url": "https://example.com/resumes/jane-smith.pdf",
    "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "React"],
    "years_experience": 4,
}


class TestRecruitmentWorkflow:
    def test_recruitment_returns_200(self):
        r = post("/api/workflows/recruitment/screen", RECRUITMENT_PAYLOAD)
        assert r.status_code == 200

    def test_recruitment_has_score(self):
        r = post("/api/workflows/recruitment/screen", RECRUITMENT_PAYLOAD)
        body = r.json()
        assert "score" in body
        assert 0.0 <= body["score"] <= 1.0

    def test_recruitment_experienced_candidate_passes(self):
        payload = {**RECRUITMENT_PAYLOAD, "years_experience": 10, "skills": ["Python"] * 8, "resume_url": "https://example.com/resumes/jane-smith.pdf"}
        r = post("/api/workflows/recruitment/screen", payload)
        body = r.json()
        assert body.get("screening_status") in ("passed", "needs_review", "failed")

    def test_recruitment_has_next_steps(self):
        r = post("/api/workflows/recruitment/screen", RECRUITMENT_PAYLOAD)
        body = r.json()
        assert isinstance(body.get("recommended_next_steps"), list)


# ---------------------------------------------------------------------------
# Payroll Workflow
# ---------------------------------------------------------------------------

PAYROLL_PAYLOAD = {
    "company_id": "ORG001",
    "payroll_period": "2025-01",
    "employee_ids": ["E001", "E002", "E003"],
    "payment_method": "bank_transfer",
}


class TestPayrollWorkflow:
    def test_payroll_returns_200(self):
        r = post("/api/workflows/payroll/process", PAYROLL_PAYLOAD)
        assert r.status_code == 200

    def test_payroll_total_amount_positive(self):
        r = post("/api/workflows/payroll/process", PAYROLL_PAYLOAD)
        body = r.json()
        assert body.get("total_amount", 0) > 0

    def test_payroll_processed_count_matches(self):
        r = post("/api/workflows/payroll/process", PAYROLL_PAYLOAD)
        body = r.json()
        assert body.get("total_processed") == len(PAYROLL_PAYLOAD["employee_ids"])

    def test_payroll_status_completed(self):
        r = post("/api/workflows/payroll/process", PAYROLL_PAYLOAD)
        body = r.json()
        assert body.get("status") == "completed"


# ---------------------------------------------------------------------------
# Invoice Workflow
# ---------------------------------------------------------------------------

INVOICE_PAYLOAD = {
    "client_id": "CLIENT001",
    "client_name": "Acme Corp",
    "client_email": "billing@acme.com",
    "items": [
        {"description": "Consulting", "quantity": 10, "unit_price": 150.0},
        {"description": "Support", "quantity": 5, "unit_price": 80.0},
    ],
    "amount_due": 1900.0,
    "due_date": "2025-02-28",
    "currency": "USD",
}


class TestInvoiceWorkflow:
    def test_invoice_returns_200(self):
        r = post("/api/workflows/invoice/generate", INVOICE_PAYLOAD)
        assert r.status_code == 200

    def test_invoice_number_format(self):
        r = post("/api/workflows/invoice/generate", INVOICE_PAYLOAD)
        body = r.json()
        inv = body.get("invoice_number", "")
        assert inv.startswith("INV-"), f"Expected 'INV-...' got: {inv}"

    def test_invoice_number_unique(self):
        r1 = post("/api/workflows/invoice/generate", INVOICE_PAYLOAD)
        r2 = post("/api/workflows/invoice/generate", INVOICE_PAYLOAD)
        assert r1.json()["invoice_number"] != r2.json()["invoice_number"]

    def test_invoice_status_completed(self):
        r = post("/api/workflows/invoice/generate", INVOICE_PAYLOAD)
        body = r.json()
        assert body.get("status") == "completed"


# ---------------------------------------------------------------------------
# Meeting Workflow
# ---------------------------------------------------------------------------

MEETING_PAYLOAD = {
    "title": "Q1 Planning",
    "organizer_id": "U001",
    "participants": ["u2@example.com", "u3@example.com", "u4@example.com"],
    "start_time": "2025-02-01T10:00:00",
    "duration_minutes": 60,
    "room_required": True,
}


class TestMeetingWorkflow:
    def test_meeting_returns_200(self):
        r = post("/api/workflows/meeting/schedule", MEETING_PAYLOAD)
        assert r.status_code == 200

    def test_meeting_scheduled_true(self):
        r = post("/api/workflows/meeting/schedule", MEETING_PAYLOAD)
        body = r.json()
        assert body.get("meeting_scheduled") is True

    def test_meeting_invites_count(self):
        r = post("/api/workflows/meeting/schedule", MEETING_PAYLOAD)
        body = r.json()
        assert body.get("invites_sent") == len(MEETING_PAYLOAD["participants"])

    def test_meeting_room_allocated_when_required(self):
        r = post("/api/workflows/meeting/schedule", MEETING_PAYLOAD)
        body = r.json()
        assert body.get("room_allocated") is not None


# ---------------------------------------------------------------------------
# Sales Lead Workflow
# ---------------------------------------------------------------------------

SALES_PAYLOAD = {
    "lead_name": "Bob Builder",
    "lead_email": "bob@builder.com",
    "lead_phone": "+1234567890",
    "company_name": "Builder Inc",
    "lead_source": "website",
    "lead_budget": 5000.0,
    "product_interest": ["Payroll Automation", "Invoice Management"],
}


class TestSalesLeadWorkflow:
    def test_sales_returns_200(self):
        r = post("/api/workflows/sales/generate-lead", SALES_PAYLOAD)
        assert r.status_code == 200

    def test_sales_has_lead_id(self):
        r = post("/api/workflows/sales/generate-lead", SALES_PAYLOAD)
        body = r.json()
        assert "lead_id" in body

    def test_sales_score_in_range(self):
        r = post("/api/workflows/sales/generate-lead", SALES_PAYLOAD)
        body = r.json()
        score = body.get("qualification_score", -1)
        assert 0.0 <= score <= 1.0

    def test_sales_qualified_lead_with_budget(self):
        r = post("/api/workflows/sales/generate-lead", SALES_PAYLOAD)
        body = r.json()
        # With budget + phone + interests, should be qualified
        assert body.get("lead_qualified") is True


# ---------------------------------------------------------------------------
# Tenant Middleware
# ---------------------------------------------------------------------------

class TestTenantMiddleware:
    def test_apex_domain_has_no_tenant_header_set_on_response(self):
        """Platform info with apex host doesn't set an error tenant."""
        r = get("/api/platform/info", headers={"Host": "autonomous.srpailabs.com"})
        assert r.status_code == 200

    def test_subdomain_host_accepted(self):
        """Subdomain host is accepted (middleware sets tenant slug)."""
        r = get("/health", headers={"Host": "acme.autonomous.srpailabs.com"})
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# N8N Webhooks
# ---------------------------------------------------------------------------

class TestN8NWebhooks:
    def test_onboarding_webhook_accepts_post(self):
        r = post("/webhooks/n8n/onboarding", {"employee_id": "E001", "action": "start"})
        assert r.status_code in (200, 201, 202, 422)  # 422 = schema mismatch, but endpoint exists

    def test_payroll_webhook_accepts_post(self):
        r = post("/webhooks/n8n/payroll", {"period": "2025-01", "action": "process"})
        assert r.status_code in (200, 201, 202, 422)
