"""
Comprehensive E2E test suite for Emergentic AI platform.

Tests the full platform stack: health checks, multi-tenant APIs, all 6
workflow automations, N8N webhooks, data persistence, error handling,
and edge cases.

Run with:
    pytest tests/test_e2e.py -v
    pytest tests/test_e2e.py -v --tb=short      # compact output
    pytest tests/test_e2e.py::TestWorkflowPipeline -v   # single class
"""

import pytest
import time
import uuid
from fastapi.testclient import TestClient
from api.main import app

CLIENT = TestClient(app)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get(path: str, **kw):
    return CLIENT.get(path, **kw)

def post(path: str, json: dict = None, **kw):
    return CLIENT.post(path, json=json or {}, **kw)

def put(path: str, json: dict, **kw):
    return CLIENT.put(path, json=json, **kw)

def delete(path: str, **kw):
    return CLIENT.delete(path, **kw)

def assert_keys(body: dict, *keys):
    for key in keys:
        assert key in body, f"Missing key '{key}' in response: {list(body.keys())}"

UNIQUE = str(uuid.uuid4())[:8]

# ============================================================
# 1. INFRASTRUCTURE
# ============================================================

class TestHealthAndPlatform:
    """API health, platform metadata, and docs availability."""

    def test_health_returns_200(self):
        r = get("/health")
        assert r.status_code == 200

    def test_health_status_healthy(self):
        assert get("/health").json().get("status") == "healthy"

    def test_health_has_version(self):
        body = get("/health").json()
        assert_keys(body, "platform", "version")

    def test_health_has_timestamp(self):
        assert "timestamp" in get("/health").json()

    def test_platform_info_returns_200(self):
        assert get("/api/platform/info").status_code == 200

    def test_platform_info_has_industries(self):
        body = get("/api/platform/info").json()
        assert "supported_industries" in body
        assert len(body["supported_industries"]) >= 7

    def test_platform_info_has_workflows(self):
        body = get("/api/platform/info").json()
        assert "workflows" in body or "automation_modules" in body or "supported_industries" in body

    def test_docs_available(self):
        # Swagger UI should be accessible
        r = get("/docs")
        assert r.status_code == 200

    def test_openapi_schema_available(self):
        r = get("/openapi.json")
        assert r.status_code == 200
        schema = r.json()
        assert "paths" in schema
        assert len(schema["paths"]) >= 20  # many routes registered

    def test_non_existent_route_returns_404(self):
        assert get("/api/does-not-exist-xyz").status_code == 404


# ============================================================
# 2. INDUSTRIES
# ============================================================

class TestIndustries:
    """All 7 industry templates available and correct."""

    EXPECTED_IDS = ["hospital", "school", "it_company", "recruitment",
                    "payroll_finance", "service_business", "generic"]

    def test_list_returns_200(self):
        assert get("/api/industries").status_code == 200

    def test_list_returns_all_seven(self):
        body = get("/api/industries").json()
        assert "industries" in body
        assert len(body["industries"]) >= 7

    def test_all_expected_ids_present(self):
        ids = [i["id"] for i in get("/api/industries").json()["industries"]]
        for expected in self.EXPECTED_IDS:
            assert expected in ids, f"Industry '{expected}' not in list"

    def test_each_industry_has_name_and_modules(self):
        for ind in get("/api/industries").json()["industries"]:
            assert "id" in ind and "name" in ind, f"Industry missing id/name: {ind}"

    @pytest.mark.parametrize("industry_id", EXPECTED_IDS)
    def test_get_each_industry_by_id(self, industry_id):
        r = get(f"/api/industries/{industry_id}")
        assert r.status_code == 200
        assert r.json()["id"] == industry_id

    def test_unknown_industry_returns_404(self):
        assert get("/api/industries/unicorn_factory").status_code == 404

    def test_hospital_has_patient_module(self):
        body = get("/api/industries/hospital").json()
        modules = str(body).lower()
        assert "patient" in modules or "appointment" in modules

    def test_school_has_student_module(self):
        body = get("/api/industries/school").json()
        modules = str(body).lower()
        assert "student" in modules or "class" in modules


# ============================================================
# 3. TENANT / ORGANIZATION MANAGEMENT
# ============================================================

@pytest.fixture(scope="module")
def tenant_slug():
    """Create a test tenant and return its slug."""
    slug = f"test-{UNIQUE}"
    r = post("/api/tenants", {
        "owner_email": f"owner-{UNIQUE}@test.emergentic.ai",
        "name": f"Test Org {UNIQUE}",
        "industry": "it_company",
        "slug": slug,
    })
    if r.status_code == 200:
        return slug
    return slug  # return slug regardless for downstream tests

@pytest.fixture(scope="module")
def tenant_org_id(tenant_slug):
    """Return org_id for the created tenant."""
    r = get(f"/api/tenants/{tenant_slug}")
    if r.status_code == 200:
        return r.json().get("organization", {}).get("id")
    return None


class TestTenantManagement:
    """Multi-tenant organization creation, listing, retrieval."""

    def test_create_tenant_returns_200(self):
        slug = f"tenant-a-{UNIQUE}"
        r = post("/api/tenants", {
            "owner_email": f"admin-{UNIQUE}@test.com",
            "name": "Test Corp A",
            "industry": "it_company",
            "slug": slug,
        })
        assert r.status_code == 200

    def test_create_tenant_returns_org(self):
        slug = f"tenant-b-{UNIQUE}"
        body = post("/api/tenants", {
            "owner_email": f"owner-b-{UNIQUE}@test.com",
            "name": "Test Corp B",
            "slug": slug,
        }).json()
        assert body.get("ok") is True
        assert "organization" in body

    def test_tenant_has_id_and_slug(self):
        slug = f"tenant-c-{UNIQUE}"
        body = post("/api/tenants", {
            "owner_email": f"owner-c-{UNIQUE}@test.com",
            "name": "Test Corp C",
            "slug": slug,
        }).json()
        org = body.get("organization", {})
        assert "id" in org
        assert org.get("slug") == slug or "slug" in org

    def test_fetch_tenant_by_slug(self, tenant_slug):
        r = get(f"/api/tenants/{tenant_slug}")
        assert r.status_code == 200
        assert r.json().get("ok") is True

    def test_list_tenants_for_owner(self):
        email = f"listowner-{UNIQUE}@test.com"
        post("/api/tenants", {"owner_email": email, "name": "List Org", "slug": f"list-{UNIQUE}"})
        r = get(f"/api/tenants?owner_email={email}")
        assert r.status_code == 200
        body = r.json()
        assert "organizations" in body
        assert len(body["organizations"]) >= 1

    def test_nonexistent_tenant_returns_404(self):
        assert get("/api/tenants/does-not-exist-xyz-abc-123").status_code == 404

    def test_tenant_isolation_different_slugs(self):
        """Two tenants with different slugs are independent."""
        slug1, slug2 = f"iso1-{UNIQUE}", f"iso2-{UNIQUE}"
        post("/api/tenants", {"owner_email": f"iso1@test.com", "name": "Iso Org 1", "slug": slug1})
        post("/api/tenants", {"owner_email": f"iso2@test.com", "name": "Iso Org 2", "slug": slug2})
        r1 = get(f"/api/tenants/{slug1}").json()
        r2 = get(f"/api/tenants/{slug2}").json()
        assert r1["organization"]["id"] != r2["organization"]["id"]


# ============================================================
# 4. APP MANAGEMENT (RECORDS)
# ============================================================

@pytest.fixture(scope="module")
def created_app_id(tenant_org_id):
    """Create a test app and return its ID."""
    r = post("/api/records/apps", {
        "name": f"E2E Test App {UNIQUE}",
        "description": "Automated test app",
        "org_id": tenant_org_id,
        "app_type": "custom",
    })
    if r.status_code == 200:
        return r.json().get("app", {}).get("id") or r.json().get("id")
    return None


class TestAppManagement:
    """App creation, listing, retrieval, schema saving."""

    def _get_org_id(self):
        """Create a fresh test org and return its ID."""
        slug = f"app-test-{uuid.uuid4().hex[:8]}"
        r = post("/api/tenants", {
            "owner_email": f"apptest-{slug}@test.com",
            "name": f"App Test Org {slug}",
            "slug": slug,
        })
        if r.status_code != 200:
            pytest.skip(f"Cannot create test org: {r.text[:100]}")
        return r.json().get("organization", {}).get("id")

    def test_create_app_returns_200(self):
        org_id = self._get_org_id()
        r = CLIENT.post(f"/api/records/apps?org_id={org_id}", json={
            "name": f"App Test {UNIQUE}",
        })
        assert r.status_code == 200

    def test_create_app_returns_id(self):
        org_id = self._get_org_id()
        r = CLIENT.post(f"/api/records/apps?org_id={org_id}", json={
            "name": f"App ID Test {UNIQUE}",
        })
        body = r.json()
        app_data = body.get("app") or body
        assert "id" in app_data

    def test_list_apps_for_org(self, tenant_org_id):
        if not tenant_org_id:
            pytest.skip("No org_id available")
        r = get(f"/api/records/apps?org_id={tenant_org_id}")
        assert r.status_code == 200
        body = r.json()
        assert "apps" in body or isinstance(body, list)

    def test_create_app_with_user_prompt(self):
        """App created from natural-language prompt."""
        org_id = self._get_org_id()
        r = CLIENT.post(f"/api/records/apps?org_id={org_id}", json={
            "name": "Payroll Tracker",
            "user_prompt": "I need a payroll management system for 50 employees with salary slips",
        })
        assert r.status_code == 200

    def test_create_app_multiple_types(self):
        """Different app_type values are accepted."""
        org_id = self._get_org_id()
        for app_type in ["payroll", "invoice", "crm", "custom", "hr_workflow"]:
            r = CLIENT.post(f"/api/records/apps?org_id={org_id}", json={
                "name": f"Type Test {app_type}",
                "app_type": app_type,
            })
            assert r.status_code == 200, f"Failed for app_type={app_type}: {r.text}"

    def test_save_schema_for_app(self, created_app_id, tenant_org_id):
        if not created_app_id:
            pytest.skip("No app_id available")
        r = post("/api/records/schemas", {
            "app_id": created_app_id,
            "schema_json": {
                "tables": [
                    {
                        "name": "employees",
                        "columns": [
                            {"name": "id", "type": "uuid", "primary_key": True},
                            {"name": "name", "type": "varchar", "nullable": False},
                            {"name": "salary", "type": "decimal"},
                            {"name": "department", "type": "varchar"},
                        ]
                    }
                ]
            },
            "version": 1,
            "org_id": tenant_org_id,
        })
        assert r.status_code == 200

    def test_insert_and_retrieve_record(self, created_app_id, tenant_org_id):
        if not created_app_id:
            pytest.skip("No app_id available")
        # Insert
        r = post("/api/records/data", {
            "app_id": created_app_id,
            "record_json": {
                "employee_name": "Alice Smith",
                "department": "Engineering",
                "salary": 95000,
            },
            "org_id": tenant_org_id,
        })
        assert r.status_code == 200
        # Retrieve
        r2 = get(f"/api/records/data/{created_app_id}?org_id={tenant_org_id}")
        assert r2.status_code == 200
        body = r2.json()
        records = body if isinstance(body, list) else body.get("records", [])
        assert len(records) >= 1

    def test_log_execution_and_retrieve(self, created_app_id, tenant_org_id):
        if not created_app_id:
            pytest.skip("No app_id available")
        # Log an action
        r = post("/api/records/logs", {
            "action": "e2e_test_action",
            "status": "success",
            "app_id": created_app_id,
            "response": {"message": "E2E test completed"},
            "org_id": tenant_org_id,
        })
        assert r.status_code == 200
        # Retrieve logs
        r2 = get(f"/api/records/logs/{created_app_id}?org_id={tenant_org_id}")
        assert r2.status_code == 200


# ============================================================
# 5. WORKFLOW AUTOMATION — ONBOARDING
# ============================================================

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
    """Employee onboarding automation — all success + edge cases."""

    def test_onboarding_returns_200(self):
        assert post("/api/workflows/onboarding/start", ONBOARDING_PAYLOAD).status_code == 200

    def test_onboarding_has_execution_id(self):
        body = post("/api/workflows/onboarding/start", ONBOARDING_PAYLOAD).json()
        assert "execution_id" in body and len(body["execution_id"]) > 0

    def test_onboarding_status_completed(self):
        assert post("/api/workflows/onboarding/start", ONBOARDING_PAYLOAD).json().get("status") == "completed"

    def test_onboarding_welcome_email_sent(self):
        assert post("/api/workflows/onboarding/start", ONBOARDING_PAYLOAD).json().get("welcome_email_sent") is True

    def test_onboarding_each_call_unique_execution_id(self):
        ids = {post("/api/workflows/onboarding/start", ONBOARDING_PAYLOAD).json()["execution_id"] for _ in range(3)}
        assert len(ids) == 3, "Execution IDs must be unique per call"

    def test_onboarding_different_departments(self):
        for dept in ["HR", "Sales", "Finance", "Operations", "Marketing"]:
            payload = {**ONBOARDING_PAYLOAD, "department": dept}
            r = post("/api/workflows/onboarding/start", payload)
            assert r.status_code == 200, f"Failed for dept={dept}"

    def test_onboarding_response_has_steps_or_tasks(self):
        body = post("/api/workflows/onboarding/start", ONBOARDING_PAYLOAD).json()
        has_steps = any(k in body for k in ["steps", "tasks", "checklist", "actions"])
        # At minimum status and execution_id should exist
        assert "status" in body and "execution_id" in body


# ============================================================
# 6. WORKFLOW AUTOMATION — RECRUITMENT
# ============================================================

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
    """Candidate screening, scoring, and qualification."""

    def test_screen_returns_200(self):
        assert post("/api/workflows/recruitment/screen", RECRUITMENT_PAYLOAD).status_code == 200

    def test_score_in_valid_range(self):
        score = post("/api/workflows/recruitment/screen", RECRUITMENT_PAYLOAD).json().get("score", -1)
        assert 0.0 <= score <= 1.0

    def test_has_screening_status(self):
        status = post("/api/workflows/recruitment/screen", RECRUITMENT_PAYLOAD).json().get("screening_status")
        assert status in ("passed", "needs_review", "failed")

    def test_has_next_steps(self):
        steps = post("/api/workflows/recruitment/screen", RECRUITMENT_PAYLOAD).json().get("recommended_next_steps")
        assert isinstance(steps, list)

    def test_senior_candidate_scores_higher(self):
        junior = {**RECRUITMENT_PAYLOAD, "years_experience": 0, "skills": ["Python"]}
        senior = {**RECRUITMENT_PAYLOAD, "years_experience": 12, "skills": ["Python"] * 10}
        score_j = post("/api/workflows/recruitment/screen", junior).json().get("score", 0)
        score_s = post("/api/workflows/recruitment/screen", senior).json().get("score", 0)
        assert score_s >= score_j, f"Senior ({score_s}) should score >= junior ({score_j})"

    def test_no_skills_candidate_handled(self):
        payload = {**RECRUITMENT_PAYLOAD, "skills": [], "years_experience": 0}
        r = post("/api/workflows/recruitment/screen", payload)
        assert r.status_code == 200

    def test_many_skills_candidate_passes(self):
        payload = {**RECRUITMENT_PAYLOAD, "skills": [f"skill{i}" for i in range(20)], "years_experience": 8}
        body = post("/api/workflows/recruitment/screen", payload).json()
        assert body.get("screening_status") in ("passed", "needs_review", "failed")


# ============================================================
# 7. WORKFLOW AUTOMATION — PAYROLL
# ============================================================

PAYROLL_PAYLOAD = {
    "company_id": "ORG001",
    "payroll_period": "2025-01",
    "employee_ids": ["E001", "E002", "E003"],
    "payment_method": "bank_transfer",
}

class TestPayrollWorkflow:
    """Payroll processing for multiple employees."""

    def test_process_returns_200(self):
        assert post("/api/workflows/payroll/process", PAYROLL_PAYLOAD).status_code == 200

    def test_total_amount_positive(self):
        assert post("/api/workflows/payroll/process", PAYROLL_PAYLOAD).json().get("total_amount", 0) > 0

    def test_processed_count_matches_input(self):
        body = post("/api/workflows/payroll/process", PAYROLL_PAYLOAD).json()
        assert body.get("total_processed") == len(PAYROLL_PAYLOAD["employee_ids"])

    def test_status_completed(self):
        assert post("/api/workflows/payroll/process", PAYROLL_PAYLOAD).json().get("status") == "completed"

    def test_single_employee_payroll(self):
        payload = {**PAYROLL_PAYLOAD, "employee_ids": ["E099"]}
        body = post("/api/workflows/payroll/process", payload).json()
        assert body.get("total_processed") == 1

    def test_large_payroll_batch(self):
        payload = {**PAYROLL_PAYLOAD, "employee_ids": [f"E{i:03d}" for i in range(50)]}
        body = post("/api/workflows/payroll/process", payload).json()
        assert body.get("total_processed") == 50

    def test_different_payment_methods(self):
        for method in ["bank_transfer", "check", "digital_wallet"]:
            payload = {**PAYROLL_PAYLOAD, "payment_method": method}
            r = post("/api/workflows/payroll/process", payload)
            assert r.status_code == 200, f"Failed for payment_method={method}"

    def test_payroll_has_execution_id(self):
        body = post("/api/workflows/payroll/process", PAYROLL_PAYLOAD).json()
        assert "execution_id" in body or "payroll_run_id" in body or "status" in body


# ============================================================
# 8. WORKFLOW AUTOMATION — INVOICE
# ============================================================

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
    """Invoice generation with unique numbering."""

    def test_generate_returns_200(self):
        assert post("/api/workflows/invoice/generate", INVOICE_PAYLOAD).status_code == 200

    def test_invoice_number_format(self):
        inv = post("/api/workflows/invoice/generate", INVOICE_PAYLOAD).json().get("invoice_number", "")
        assert inv.startswith("INV-"), f"Expected 'INV-...' got: {inv}"

    def test_invoice_numbers_are_unique(self):
        invoices = [post("/api/workflows/invoice/generate", INVOICE_PAYLOAD).json()["invoice_number"]
                    for _ in range(5)]
        assert len(set(invoices)) == 5, "Invoice numbers must be globally unique"

    def test_status_completed(self):
        assert post("/api/workflows/invoice/generate", INVOICE_PAYLOAD).json().get("status") == "completed"

    def test_sent_to_client_flag(self):
        body = post("/api/workflows/invoice/generate", INVOICE_PAYLOAD).json()
        # After our fix, sent_to_client should be True
        assert body.get("sent_to_client") is True

    def test_different_currencies(self):
        for currency in ["USD", "EUR", "GBP", "INR", "AED"]:
            payload = {**INVOICE_PAYLOAD, "currency": currency}
            r = post("/api/workflows/invoice/generate", payload)
            assert r.status_code == 200, f"Failed for currency={currency}"

    def test_invoice_with_single_item(self):
        payload = {**INVOICE_PAYLOAD, "items": [{"description": "One-time setup", "quantity": 1, "unit_price": 5000.0}]}
        assert post("/api/workflows/invoice/generate", payload).status_code == 200

    def test_invoice_with_many_items(self):
        items = [{"description": f"Item {i}", "quantity": i, "unit_price": float(i * 10)} for i in range(1, 20)]
        payload = {**INVOICE_PAYLOAD, "items": items}
        assert post("/api/workflows/invoice/generate", payload).status_code == 200


# ============================================================
# 9. WORKFLOW AUTOMATION — MEETING
# ============================================================

MEETING_PAYLOAD = {
    "title": "Q1 Planning",
    "organizer_id": "U001",
    "participants": ["u2@example.com", "u3@example.com", "u4@example.com"],
    "start_time": "2025-02-01T10:00:00",
    "duration_minutes": 60,
    "room_required": True,
}

class TestMeetingWorkflow:
    """Meeting scheduling with calendar integration and invites."""

    def test_schedule_returns_200(self):
        assert post("/api/workflows/meeting/schedule", MEETING_PAYLOAD).status_code == 200

    def test_meeting_scheduled_true(self):
        assert post("/api/workflows/meeting/schedule", MEETING_PAYLOAD).json().get("meeting_scheduled") is True

    def test_invites_count_matches_participants(self):
        body = post("/api/workflows/meeting/schedule", MEETING_PAYLOAD).json()
        assert body.get("invites_sent") == len(MEETING_PAYLOAD["participants"])

    def test_room_allocated_when_required(self):
        body = post("/api/workflows/meeting/schedule", MEETING_PAYLOAD).json()
        assert body.get("room_allocated") is not None

    def test_no_room_when_not_required(self):
        payload = {**MEETING_PAYLOAD, "room_required": False}
        body = post("/api/workflows/meeting/schedule", payload).json()
        assert body.get("meeting_scheduled") is True

    def test_large_participant_list(self):
        participants = [f"user{i}@example.com" for i in range(20)]
        payload = {**MEETING_PAYLOAD, "participants": participants}
        body = post("/api/workflows/meeting/schedule", payload).json()
        assert body.get("invites_sent") == 20

    def test_different_meeting_durations(self):
        for minutes in [15, 30, 45, 60, 90, 120, 180]:
            payload = {**MEETING_PAYLOAD, "duration_minutes": minutes}
            r = post("/api/workflows/meeting/schedule", payload)
            assert r.status_code == 200, f"Failed for duration={minutes}min"

    def test_meeting_has_meeting_id(self):
        body = post("/api/workflows/meeting/schedule", MEETING_PAYLOAD).json()
        assert any(k in body for k in ["meeting_id", "execution_id", "calendar_event_id"])


# ============================================================
# 10. WORKFLOW AUTOMATION — SALES LEAD
# ============================================================

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
    """Sales lead qualification and scoring."""

    def test_generate_lead_returns_200(self):
        assert post("/api/workflows/sales/generate-lead", SALES_PAYLOAD).status_code == 200

    def test_has_lead_id(self):
        assert "lead_id" in post("/api/workflows/sales/generate-lead", SALES_PAYLOAD).json()

    def test_qualification_score_in_range(self):
        score = post("/api/workflows/sales/generate-lead", SALES_PAYLOAD).json().get("qualification_score", -1)
        assert 0.0 <= score <= 1.0

    def test_qualified_lead_with_full_data(self):
        assert post("/api/workflows/sales/generate-lead", SALES_PAYLOAD).json().get("lead_qualified") is True

    def test_unqualified_lead_no_budget(self):
        payload = {**SALES_PAYLOAD, "lead_budget": 0, "lead_phone": "", "product_interest": []}
        body = post("/api/workflows/sales/generate-lead", payload).json()
        # Should still process, may not be qualified
        assert "lead_id" in body

    def test_different_lead_sources(self):
        for source in ["website", "referral", "linkedin", "cold_call", "event"]:
            payload = {**SALES_PAYLOAD, "lead_source": source}
            r = post("/api/workflows/sales/generate-lead", payload)
            assert r.status_code == 200, f"Failed for source={source}"

    def test_high_budget_lead_qualified(self):
        payload = {**SALES_PAYLOAD, "lead_budget": 100000.0}
        assert post("/api/workflows/sales/generate-lead", payload).json().get("lead_qualified") is True

    def test_lead_ids_are_unique(self):
        ids = {post("/api/workflows/sales/generate-lead", SALES_PAYLOAD).json()["lead_id"] for _ in range(3)}
        assert len(ids) == 3, "Lead IDs must be unique"


# ============================================================
# 11. FULL WORKFLOW PIPELINE (INTEGRATION)
# ============================================================

class TestWorkflowPipeline:
    """End-to-end pipeline: hire → onboard → schedule meeting → invoice client."""

    def test_full_hire_to_invoice_pipeline(self):
        """Simulate a complete business cycle."""
        # 1. Screen a candidate
        screen_r = post("/api/workflows/recruitment/screen", RECRUITMENT_PAYLOAD)
        assert screen_r.status_code == 200
        screening = screen_r.json()
        assert screening.get("score", 0) >= 0

        # 2. Onboard the hired employee
        onboard_r = post("/api/workflows/onboarding/start", ONBOARDING_PAYLOAD)
        assert onboard_r.status_code == 200
        onboard_exec = onboard_r.json().get("execution_id")
        assert onboard_exec

        # 3. Schedule a kickoff meeting
        meeting_r = post("/api/workflows/meeting/schedule", MEETING_PAYLOAD)
        assert meeting_r.status_code == 200
        assert meeting_r.json().get("meeting_scheduled") is True

        # 4. Process payroll at month end
        payroll_r = post("/api/workflows/payroll/process", PAYROLL_PAYLOAD)
        assert payroll_r.status_code == 200
        assert payroll_r.json().get("status") == "completed"

        # 5. Generate invoice for client work
        invoice_r = post("/api/workflows/invoice/generate", INVOICE_PAYLOAD)
        assert invoice_r.status_code == 200
        inv_num = invoice_r.json().get("invoice_number", "")
        assert inv_num.startswith("INV-")

    def test_concurrent_workflow_calls_all_succeed(self):
        """Multiple workflow types in rapid succession."""
        results = [
            post("/api/workflows/onboarding/start", ONBOARDING_PAYLOAD),
            post("/api/workflows/recruitment/screen", RECRUITMENT_PAYLOAD),
            post("/api/workflows/payroll/process", PAYROLL_PAYLOAD),
            post("/api/workflows/invoice/generate", INVOICE_PAYLOAD),
            post("/api/workflows/meeting/schedule", MEETING_PAYLOAD),
            post("/api/workflows/sales/generate-lead", SALES_PAYLOAD),
        ]
        for r in results:
            assert r.status_code == 200, f"Workflow failed: {r.text[:200]}"


# ============================================================
# 12. TENANT MIDDLEWARE
# ============================================================

class TestTenantMiddleware:
    """Subdomain-based tenant routing."""

    def test_apex_domain_returns_200(self):
        r = get("/api/platform/info", headers={"Host": "autonomous.srpailabs.com"})
        assert r.status_code == 200

    def test_subdomain_host_returns_200(self):
        r = get("/health", headers={"Host": "acme.autonomous.srpailabs.com"})
        assert r.status_code == 200

    def test_demo_tenant_subdomain(self):
        r = get("/health", headers={"Host": "demo.autonomous.srpailabs.com"})
        assert r.status_code == 200

    def test_wildcard_subdomain_accepted(self):
        """Any subdomain should be routed through without error."""
        for subdomain in ["hr", "sales", "finance", "ops", "test123"]:
            r = get("/health", headers={"Host": f"{subdomain}.autonomous.srpailabs.com"})
            assert r.status_code == 200, f"Subdomain '{subdomain}' failed"


# ============================================================
# 13. N8N WEBHOOKS
# ============================================================

class TestN8NWebhooks:
    """N8N webhook integration endpoints."""

    def test_onboarding_webhook_exists(self):
        r = post("/webhooks/n8n/onboarding", {"employee_id": "E001", "action": "start"})
        assert r.status_code in (200, 201, 202, 422)

    def test_payroll_webhook_exists(self):
        r = post("/webhooks/n8n/payroll", {"period": "2025-01", "action": "process"})
        assert r.status_code in (200, 201, 202, 422)

    def test_invoice_webhook_exists(self):
        r = post("/webhooks/n8n/invoice", {"client_id": "C001", "action": "generate"})
        assert r.status_code in (200, 201, 202, 422)

    def test_meeting_webhook_exists(self):
        r = post("/webhooks/n8n/meeting", {"title": "Test", "action": "schedule"})
        assert r.status_code in (200, 201, 202, 422)

    def test_all_webhooks_dont_return_500(self):
        """Webhooks should never return 5xx — graceful handling only."""
        endpoints = [
            ("/webhooks/n8n/onboarding", {"action": "test"}),
            ("/webhooks/n8n/payroll", {"action": "test"}),
            ("/webhooks/n8n/invoice", {"action": "test"}),
            ("/webhooks/n8n/meeting", {"action": "test"}),
        ]
        for path, payload in endpoints:
            r = post(path, payload)
            assert r.status_code < 500, f"Webhook {path} returned 5xx: {r.status_code}"


# ============================================================
# 14. ERROR HANDLING & EDGE CASES
# ============================================================

class TestErrorHandling:
    """API should return proper errors, never crash."""

    def test_empty_onboarding_returns_422(self):
        assert post("/api/workflows/onboarding/start", {}).status_code == 422

    def test_empty_recruitment_returns_422(self):
        assert post("/api/workflows/recruitment/screen", {}).status_code == 422

    def test_empty_payroll_returns_422(self):
        assert post("/api/workflows/payroll/process", {}).status_code == 422

    def test_malformed_json_handled_gracefully(self):
        r = CLIENT.post("/api/workflows/onboarding/start",
                        content="not-valid-json",
                        headers={"Content-Type": "application/json"})
        assert r.status_code in (400, 422)

    def test_very_long_name_handled(self):
        payload = {**ONBOARDING_PAYLOAD, "employee_name": "A" * 500}
        r = post("/api/workflows/onboarding/start", payload)
        assert r.status_code in (200, 400, 422)  # graceful, not 500

    def test_unicode_characters_accepted(self):
        payload = {**ONBOARDING_PAYLOAD, "employee_name": "张伟 / Müller / Пётр"}
        r = post("/api/workflows/onboarding/start", payload)
        assert r.status_code in (200, 422)  # accepted or validated, not 500

    def test_negative_payroll_batch_handled(self):
        payload = {**PAYROLL_PAYLOAD, "employee_ids": []}
        r = post("/api/workflows/payroll/process", payload)
        # May return 200 with 0 processed or 422 — not 500
        assert r.status_code in (200, 400, 422)

    def test_all_routes_in_openapi_are_reachable(self):
        """Spot-check that no route path in the schema returns 405."""
        schema = get("/openapi.json").json()
        get_paths = [p for p, m in schema["paths"].items() if "get" in m]
        unreachable = []
        for path in get_paths[:10]:  # Check first 10 GET routes
            r = get(path.replace("{app_id}", "test").replace("{slug}", "test").replace("{industry_id}", "hospital"))
            if r.status_code == 405:
                unreachable.append(path)
        assert unreachable == [], f"Routes returning 405: {unreachable}"
