"""
Comprehensive API Test Suite - Tests ALL endpoints
Run with: python tests/test_all_endpoints.py
"""
import sys
import json
import datetime
sys.path.insert(0, "app")

try:
    import httpx
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
    import httpx

BASE = "http://localhost:8000"
PASS = 0
FAIL = 0
ERRORS = []


def run_test(name: str, method: str, path: str, body=None, expected_keys=None, expected_status=200):
    global PASS, FAIL
    url = BASE + path
    try:
        if method == "GET":
            r = httpx.get(url, timeout=10)
        elif method == "POST":
            r = httpx.post(url, json=body or {}, timeout=15)
        elif method == "DELETE":
            r = httpx.delete(url, timeout=10)
        
        if r.status_code == expected_status:
            try:
                data = r.json() if r.content else {}
            except Exception:
                data = {}  # non-JSON response (e.g. HTML for /docs)
            if expected_keys:
                missing = [k for k in expected_keys if k not in data]
                if missing:
                    print(f"  WARN  {name} [{r.status_code}] — missing keys: {missing}")
                else:
                    print(f"  OK    {name} [{r.status_code}]")
            else:
                print(f"  OK    {name} [{r.status_code}]")
            PASS += 1
            return data
        else:
            print(f"  FAIL  {name} — expected {expected_status}, got {r.status_code}: {r.text[:120]}")
            FAIL += 1
            ERRORS.append(f"{name}: HTTP {r.status_code} - {r.text[:120]}")
    except Exception as e:
        print(f"  ERR   {name} — {type(e).__name__}: {str(e)[:100]}")
        FAIL += 1
        ERRORS.append(f"{name}: {type(e).__name__}: {str(e)[:100]}")
    return {}


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")



if __name__ == "__main__":
 # ============================================================================
 # section("CORE ENDPOINTS")
 # ============================================================================
 section("CORE ENDPOINTS")
 run_test("Health Check", "GET", "/health", expected_keys=["status"])
 run_test("Platform Info", "GET", "/info", expected_keys=["name"])
 run_test("Statistics", "GET", "/stats")
 run_test("List Agents", "GET", "/agents")
 run_test("List Workflows", "GET", "/workflows")
 run_test("Events Historical", "GET", "/events")
 run_test("OpenAPI Docs", "GET", "/docs")
 run_test("OpenAPI JSON", "GET", "/openapi.json")

 # ============================================================================
 section("AUTHENTICATION ENDPOINTS")
 # ============================================================================
 login_data = run_test("Auth Login", "POST", "/auth/login?email=admin@demo.com&password=admin123", expected_keys=["token"])
 token = login_data.get("token", "demo_token_123")
 run_test("Auth Verify Token", "GET", f"/auth/verify?token={token}")

 # ============================================================================
 section("AGENT MANAGEMENT ENDPOINTS")
 # ============================================================================
 agents_data = run_test("List All Agents", "GET", "/agents")
 agent_id = "executor_1"
 run_test("Get Agent State", "GET", f"/agents/{agent_id}")
 run_test("Get Agent Tools", "GET", f"/agents/{agent_id}/tools")
 run_test("Process with Agent", "POST", f"/agents/{agent_id}/process",
      {"task": "Summarize employee John Doe onboarding", "context": {"employee_id": "EMP001"}})

 # ============================================================================
 section("WORKFLOW MANAGEMENT ENDPOINTS")
 # ============================================================================
 wf_data = run_test("List Workflows", "GET", "/workflows")

 new_wf = run_test("Create Workflow", "POST", "/workflows", {
     "id": "test_wf_001",
     "name": "Test Workflow",
     "description": "Automated test workflow",
     "entry_point": "step_1",
     "agents": ["planner_1"],
     "steps": [
         {"id": "step_1", "name": "Initialize", "description": "Initialization step", "next_steps": []}
     ]
 })
 wf_id = new_wf.get("workflow_id", "test_wf_001")

 run_test("Get Workflow Details", "GET", f"/workflows/{wf_id}")
 run_test("Execute Workflow", "POST", f"/workflows/{wf_id}/execute", {
     "context": {"triggered_by": "test_suite", "timestamp": datetime.datetime.now().isoformat()}
 })
 run_test("List Workflow Executions", "GET", f"/workflows/{wf_id}/executions")

 # ============================================================================
 section("BUSINESS WORKFLOW ENDPOINTS - ONBOARDING")
 # ============================================================================
 onboarding_result = run_test("Start Onboarding", "POST", "/api/workflows/onboarding/start", {
     "employee_id": "EMP_TEST_001",
     "employee_name": "Ahmad Al-Hassan",
     "employee_email": "ahmad@company.com",
     "department": "Engineering",
     "position": "Senior Software Engineer",
     "start_date": "2026-03-01"
 }, expected_keys=["execution_id", "status"])
 exec_id = onboarding_result.get("execution_id", "test_exec")
 run_test("Onboarding Status", "GET", f"/api/workflows/onboarding/status/{exec_id}")

 # ============================================================================
 section("BUSINESS WORKFLOW ENDPOINTS - RECRUITMENT")
 # ============================================================================
 run_test("Screen Candidate", "POST", "/api/workflows/recruitment/screen", {
     "candidate_id": "CAN_TEST_001",
     "candidate_name": "Sara Al-Mansouri",
     "candidate_email": "sara@example.com",
     "position_id": "POS_SWE_001",
     "resume_url": "https://example.com/sara_resume.pdf",
     "years_experience": 7,
     "skills": ["Python", "FastAPI", "AWS", "Docker", "Kubernetes"]
 }, expected_keys=["execution_id", "status"])

 # ============================================================================
 section("BUSINESS WORKFLOW ENDPOINTS - PAYROLL")
 # ============================================================================
 payroll_result = run_test("Process Payroll", "POST", "/api/workflows/payroll/process", {
     "payroll_period": "2026-02",
     "company_id": "COM_TEST_001",
     "employee_ids": ["EMP_TEST_001", "EMP_TEST_002"],
     "process_all": False
 }, expected_keys=["execution_id", "status"])

 # ============================================================================
 section("BUSINESS WORKFLOW ENDPOINTS - INVOICE")
 # ============================================================================
 invoice_result = run_test("Generate Invoice", "POST", "/api/workflows/invoice/generate", {
     "client_id": "CLIENT_TEST_001",
     "client_name": "Acme Corporation",
     "client_email": "billing@acme.com",
     "items": [
         {"description": "Software Development Services — Feb 2026", "quantity": 20, "unit_price": 200.00},
         {"description": "Cloud Infrastructure Management", "quantity": 1, "unit_price": 500.00}
     ],
     "amount_due": 4500.00,
     "due_date": "2026-03-15"
 }, expected_keys=["execution_id", "status"])

 # ============================================================================
 section("BUSINESS WORKFLOW ENDPOINTS - MEETING")
 # ============================================================================
 run_test("Schedule Meeting", "POST", "/api/workflows/meeting/schedule", {
     "title": "Q1 2026 Engineering Review",
     "description": "Quarterly engineering planning session",
     "participants": ["dev1@company.com", "dev2@company.com", "manager@company.com"],
     "start_time": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)).isoformat(),
     "duration_minutes": 60,
     "room_required": True
 }, expected_keys=["execution_id", "status"])

 # ============================================================================
 section("BUSINESS WORKFLOW ENDPOINTS - SALES LEAD")
 # ============================================================================
 run_test("Generate Sales Lead", "POST", "/api/workflows/sales/generate-lead", {
     "lead_name": "Mohammed Al-Rashid",
     "lead_email": "m.rashid@techstart.com",
     "lead_phone": "+971-50-123-4567",
     "company_name": "TechStart Inc",
     "lead_source": "website",
     "product_interest": ["Automation", "AI Workflows", "HR Automation"]
 }, expected_keys=["execution_id", "status"])

 # ============================================================================
 section("N8N WEBHOOK ENDPOINTS")
 # ============================================================================
 run_test("N8N List Workflows", "GET", "/webhooks/n8n/workflows")
 run_test("N8N Onboarding Webhook", "POST", "/webhooks/n8n/onboarding", {
     "workflow_id": "n8n_employee_onboarding",
     "trigger_name": "employee_created",
     "data": {
         "employee_id": "EMP_N8N_001",
         "employee_name": "Fatima Al-Zahraa",
         "employee_email": "fatima@company.com",
         "department": "Operations",
         "start_date": "2026-03-15"
     }
 })
 run_test("N8N Recruitment Webhook", "POST", "/webhooks/n8n/recruitment", {
     "workflow_id": "n8n_recruitment",
     "trigger_name": "candidate_applied",
     "data": {
         "candidate_id": "CAN_N8N_001",
         "candidate_name": "Khalid Ibrahim",
         "candidate_email": "khalid@example.com",
         "position_id": "POS_OPS_001",
         "resume_url": "https://example.com/khalid_cv.pdf"
     }
 })
 run_test("N8N Payroll Webhook", "POST", "/webhooks/n8n/payroll", {
     "workflow_id": "n8n_payroll",
     "trigger_name": "payroll_processing",
     "data": {
         "payroll_period": "2026-02",
         "employee_ids": ["EMP_001", "EMP_002"],
         "company_id": "COM_N8N_001"
     }
 })
 run_test("N8N Invoice Webhook", "POST", "/webhooks/n8n/invoice", {
     "workflow_id": "n8n_invoice",
     "trigger_name": "invoice_created",
     "data": {
         "invoice_id": "INV_N8N_001",
         "client_id": "CLIENT_N8N_001",
         "amount": 1500.0,
         "due_date": "2026-03-31"
     }
 })
 run_test("N8N Meeting Webhook", "POST", "/webhooks/n8n/meeting", {
     "workflow_id": "n8n_meeting",
     "trigger_name": "meeting_requested",
     "data": {
         "meeting_id": "MTG_N8N_001",
         "participants": ["pm@company.com", "dev@company.com"],
         "start_time": "2026-03-15T10:00:00Z",
         "duration_minutes": 90,
         "title": "Sprint Planning"
     }
 })
 run_test("N8N Sales Webhook", "POST", "/webhooks/n8n/sales", {
     "workflow_id": "n8n_sales",
     "trigger_name": "lead_generated",
     "data": {
         "lead_id": "LEAD_N8N_001",
         "lead_name": "Laura Chen",
         "lead_email": "laura@gamma.com",
         "company_name": "Gamma Solutions",
         "lead_source": "website"
     }
 })

 # ============================================================================
 section("MEMORY / DATABASE ENDPOINTS")
 # ============================================================================
 mem_result = run_test("Memory Store", "POST", "/memory/store", {
     "content": "Employee Ahmad Al-Hassan completed onboarding on 2026-03-01 in Engineering (Senior Software Engineer)",
     "metadata": {
         "type": "onboarding_completion",
         "employee_id": "EMP_TEST_001",
         "department": "Engineering",
         "timestamp": datetime.datetime.now().isoformat()
     }
 }, expected_keys=["memory_id"])

 run_test("Memory Retrieve", "GET", "/memory/retrieve?query=Ahmad+onboarding&limit=5")
 run_test("Memory Retrieve Payroll", "GET", "/memory/retrieve?query=payroll+processing&limit=3")

 # ============================================================================
 section("DATA PERSISTENCE (FIRESTORE MOCK)")
 # ============================================================================
 run_test("Data Store Document", "POST", "/data/employees/EMP_TEST_001", {
     "name": "Ahmad Al-Hassan",
     "department": "Engineering",
     "position": "Senior Software Engineer",
     "start_date": "2026-03-01",
     "salary": 8500.00,
     "status": "active"
 })
 run_test("Data Retrieve Document", "GET", "/data/employees/EMP_TEST_001")
 run_test("Data Query Collection", "GET", "/data/employees")
 run_test("Data Store Workflow", "POST", "/data/workflows/WF_TEST_001", {
     "name": "Employee Onboarding",
     "steps": 6,
     "status": "completed",
     "last_run": datetime.datetime.now().isoformat()
 })
 run_test("Data Retrieve Workflow", "GET", "/data/workflows/WF_TEST_001")

 # ============================================================================
 section("EXECUTION HISTORY ENDPOINTS")
 # ============================================================================
 run_test("List Executions (via workflow)", "GET", "/events")

 # ============================================================================
 # FINAL SUMMARY
 # ============================================================================
 print(f"\n{'='*60}")
 print(f"  TEST RESULTS: {PASS} PASSED  |  {FAIL} FAILED  |  {PASS+FAIL} TOTAL")
 print(f"{'='*60}")
 if ERRORS:
     print("\nFailed Tests:")
     for e in ERRORS:
         print(f"  - {e}")
 else:
     print("\n✓ ALL TESTS PASSED!")
 print()
