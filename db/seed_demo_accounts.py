"""
Seed demo/fake accounts into the database using SQLAlchemy.

Usage:
    cd "emergentic AI"
    python db/seed_demo_accounts.py

Creates 8 users, 6 organizations, 6 apps, sample records, and demo data.
"""
import sys
import os
import uuid

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from db.database import SessionLocal, init_db
from db.models import CoreUser, Organization, App, AppSchema, AppRecord, CountryRule, ExecutionLog


# Fixed UUIDs for demo data
DEMO_USERS = [
    {"id": "00000000-0000-0000-0000-000000000001", "email": "admin@demo.com", "role": "admin"},
    {"id": "00000000-0000-0000-0000-000000000002", "email": "owner@demo.com", "role": "owner"},
    {"id": "00000000-0000-0000-0000-000000000003", "email": "hr@demo.com", "role": "manager"},
    {"id": "00000000-0000-0000-0000-000000000004", "email": "finance@demo.com", "role": "manager"},
    {"id": "00000000-0000-0000-0000-000000000005", "email": "sales@demo.com", "role": "user"},
    {"id": "00000000-0000-0000-0000-000000000006", "email": "dev@demo.com", "role": "user"},
    {"id": "00000000-0000-0000-0000-000000000007", "email": "recruiter@demo.com", "role": "user"},
    {"id": "00000000-0000-0000-0000-000000000008", "email": "ops@demo.com", "role": "user"},
]

DEMO_ORGS = [
    {"id": "00000000-0000-0000-0000-000000000010", "owner_id": "00000000-0000-0000-0000-000000000001",
     "name": "Emergentic AI Demo", "slug": "emergentic-demo", "country": "US", "industry": "it_company"},
    {"id": "00000000-0000-0000-0000-000000000011", "owner_id": "00000000-0000-0000-0000-000000000002",
     "name": "MediCare Hospital", "slug": "medicare-hospital", "country": "US", "industry": "hospital"},
    {"id": "00000000-0000-0000-0000-000000000012", "owner_id": "00000000-0000-0000-0000-000000000002",
     "name": "Bright Future Academy", "slug": "bright-future", "country": "UK", "industry": "school"},
    {"id": "00000000-0000-0000-0000-000000000013", "owner_id": "00000000-0000-0000-0000-000000000007",
     "name": "TalentHub Recruiting", "slug": "talenthub", "country": "AE", "industry": "recruitment"},
    {"id": "00000000-0000-0000-0000-000000000014", "owner_id": "00000000-0000-0000-0000-000000000004",
     "name": "PayRight Financial Services", "slug": "payright", "country": "MY", "industry": "payroll_finance"},
    {"id": "00000000-0000-0000-0000-000000000015", "owner_id": "00000000-0000-0000-0000-000000000005",
     "name": "ServicePro Solutions", "slug": "servicepro", "country": "AU", "industry": "service_business"},
]

DEMO_APPS = [
    {"id": "00000000-0000-0000-0000-000000000100", "organization_id": "00000000-0000-0000-0000-000000000010",
     "name": "Payroll Manager", "description": "Automated payroll processing with tax calculation",
     "app_type": "payroll", "modules": ["employee_management", "attendance_tracking", "salary_configuration",
                                         "payroll_run_engine", "payslip_generator", "tax_calculator"]},
    {"id": "00000000-0000-0000-0000-000000000101", "organization_id": "00000000-0000-0000-0000-000000000010",
     "name": "Sales CRM", "description": "Customer relationship management and deal tracking",
     "app_type": "crm", "modules": ["lead_capture", "deal_pipeline", "activity_log",
                                     "contact_management", "email_integration", "sales_forecasting"]},
    {"id": "00000000-0000-0000-0000-000000000102", "organization_id": "00000000-0000-0000-0000-000000000015",
     "name": "Invoice Generator", "description": "Professional invoice creation and payment tracking",
     "app_type": "invoice", "modules": ["customer_management", "product_catalogue", "invoice_builder",
                                         "tax_engine", "payment_tracker", "pdf_generator", "email_dispatcher"]},
    {"id": "00000000-0000-0000-0000-000000000103", "organization_id": "00000000-0000-0000-0000-000000000011",
     "name": "Patient Records", "description": "Electronic health records management system",
     "app_type": "custom", "modules": ["patient_intake", "medical_records", "appointment_scheduler", "prescription_tracker"]},
    {"id": "00000000-0000-0000-0000-000000000104", "organization_id": "00000000-0000-0000-0000-000000000012",
     "name": "Student Management", "description": "Student enrollment and academic tracking",
     "app_type": "custom", "modules": ["student_enrollment", "class_management", "attendance", "grade_book", "fee_collection"]},
    {"id": "00000000-0000-0000-0000-000000000105", "organization_id": "00000000-0000-0000-0000-000000000013",
     "name": "Talent Pipeline", "description": "End-to-end recruitment workflow automation",
     "app_type": "custom", "modules": ["job_postings", "candidate_tracker", "interview_scheduler", "offer_management", "onboarding"]},
]

DEMO_RECORDS = [
    # Payroll employees
    {"app_id": "00000000-0000-0000-0000-000000000100", "record_json": {
        "type": "employee", "name": "Ahmad Al-Hassan", "email": "ahmad@company.com",
        "department": "Engineering", "position": "Senior Developer", "salary": 8500, "status": "active"}},
    {"app_id": "00000000-0000-0000-0000-000000000100", "record_json": {
        "type": "employee", "name": "Sarah Johnson", "email": "sarah@company.com",
        "department": "Marketing", "position": "Marketing Lead", "salary": 7200, "status": "active"}},
    {"app_id": "00000000-0000-0000-0000-000000000100", "record_json": {
        "type": "employee", "name": "James Chen", "email": "james@company.com",
        "department": "Engineering", "position": "DevOps Engineer", "salary": 9000, "status": "active"}},
    {"app_id": "00000000-0000-0000-0000-000000000100", "record_json": {
        "type": "employee", "name": "Maria Garcia", "email": "maria@company.com",
        "department": "Finance", "position": "Financial Analyst", "salary": 7800, "status": "active"}},
    {"app_id": "00000000-0000-0000-0000-000000000100", "record_json": {
        "type": "employee", "name": "David Kim", "email": "david@company.com",
        "department": "Sales", "position": "Account Executive", "salary": 6500, "status": "active"}},
    # CRM leads
    {"app_id": "00000000-0000-0000-0000-000000000101", "record_json": {
        "type": "lead", "name": "TechStart Inc", "contact": "m.rashid@techstart.com",
        "source": "website", "budget": 50000, "status": "qualified", "score": 0.85}},
    {"app_id": "00000000-0000-0000-0000-000000000101", "record_json": {
        "type": "lead", "name": "GlobalTech Solutions", "contact": "info@globaltech.com",
        "source": "referral", "budget": 120000, "status": "negotiation", "score": 0.92}},
    {"app_id": "00000000-0000-0000-0000-000000000101", "record_json": {
        "type": "lead", "name": "InnovateCo", "contact": "sales@innovateco.com",
        "source": "conference", "budget": 35000, "status": "new", "score": 0.60}},
    # Invoices
    {"app_id": "00000000-0000-0000-0000-000000000102", "record_json": {
        "type": "invoice", "invoice_number": "INV-2026-001", "client": "Acme Corp",
        "amount": 4500.00, "status": "paid", "due_date": "2026-02-28"}},
    {"app_id": "00000000-0000-0000-0000-000000000102", "record_json": {
        "type": "invoice", "invoice_number": "INV-2026-002", "client": "Beta Industries",
        "amount": 12750.00, "status": "pending", "due_date": "2026-03-31"}},
    {"app_id": "00000000-0000-0000-0000-000000000102", "record_json": {
        "type": "invoice", "invoice_number": "INV-2026-003", "client": "Gamma Solutions",
        "amount": 8900.00, "status": "overdue", "due_date": "2026-01-15"}},
]


def seed():
    """Seed the database with demo data."""
    print("=" * 60)
    print("  Seeding Demo Accounts")
    print("=" * 60)

    # Ensure tables exist
    print("\n[1/6] Creating database tables...")
    try:
        init_db()
        print("  ✓ Tables created/verified")
    except Exception as e:
        print(f"  ⚠ Table creation warning: {e}")

    db = SessionLocal()
    try:
        # Seed users
        print("\n[2/6] Creating demo users...")
        for u in DEMO_USERS:
            obj = db.get(CoreUser, u["id"])
            if not obj:
                db.add(CoreUser(id=u["id"], email=u["email"], role=u["role"]))
                print(f"  + {u['email']} ({u['role']})")
            else:
                print(f"  - {u['email']} already exists")
        db.commit()

        # Seed organizations
        print("\n[3/6] Creating demo organizations...")
        for o in DEMO_ORGS:
            obj = db.get(Organization, o["id"])
            if not obj:
                db.add(Organization(
                    id=o["id"], owner_id=o["owner_id"], name=o["name"],
                    slug=o["slug"], country=o["country"], industry=o["industry"]
                ))
                print(f"  + {o['name']} ({o['slug']})")
            else:
                print(f"  - {o['name']} already exists")
        db.commit()

        # Seed apps
        print("\n[4/6] Creating demo apps...")
        for a in DEMO_APPS:
            obj = db.get(App, a["id"])
            if not obj:
                db.add(App(
                    id=a["id"], organization_id=a["organization_id"],
                    name=a["name"], description=a["description"],
                    app_type=a["app_type"], modules=a["modules"], status="active"
                ))
                print(f"  + {a['name']} ({a['app_type']})")
            else:
                print(f"  - {a['name']} already exists")
        db.commit()

        # Seed records (always add — they have auto-generated IDs)
        print("\n[5/6] Creating demo data records...")
        existing_count = db.query(AppRecord).filter(
            AppRecord.app_id == "00000000-0000-0000-0000-000000000100"
        ).count()
        if existing_count == 0:
            count = 0
            for r in DEMO_RECORDS:
                rec = AppRecord(app_id=r["app_id"], record_json=r["record_json"])
                db.add(rec)
                count += 1
            db.commit()
            print(f"  + {count} records created")
        else:
            print(f"  - records already exist ({existing_count} found)")

        # Seed execution logs (always add — auto-generated IDs)
        print("\n[6/6] Creating execution logs...")
        existing_logs = db.query(ExecutionLog).filter(
            ExecutionLog.app_id == "00000000-0000-0000-0000-000000000100"
        ).count()
        if existing_logs == 0:
            logs = [
                {"app_id": "00000000-0000-0000-0000-000000000100", "action": "app_created", "status": "success",
                 "response_json": {"message": "Payroll Manager app initialized"}},
                {"app_id": "00000000-0000-0000-0000-000000000100", "action": "payroll_run", "status": "success",
                 "response_json": {"period": "2026-02", "employees_processed": 5, "total_gross": 39000, "total_net": 31200}},
                {"app_id": "00000000-0000-0000-0000-000000000101", "action": "app_created", "status": "success",
                 "response_json": {"message": "Sales CRM app initialized"}},
                {"app_id": "00000000-0000-0000-0000-000000000101", "action": "lead_created", "status": "success",
                 "response_json": {"lead_name": "TechStart Inc", "score": 0.85}},
                {"app_id": "00000000-0000-0000-0000-000000000102", "action": "invoice_generated", "status": "success",
                 "response_json": {"invoice_number": "INV-2026-001", "amount": 4500.00}},
            ]
            for log in logs:
                db.add(ExecutionLog(**log))
            db.commit()
            print(f"  + {len(logs)} execution logs created")
        else:
            print(f"  - execution logs already exist ({existing_logs} found)")

        print("\n" + "=" * 60)
        print("  ✓ DEMO DATA SEEDED SUCCESSFULLY")
        print("=" * 60)
        print("\nDemo login credentials:")
        print("  admin@demo.com  (admin)")
        print("  owner@demo.com  (owner)")
        print("  hr@demo.com     (manager)")
        print("  finance@demo.com (manager)")
        print("  sales@demo.com  (user)")
        print("  dev@demo.com    (user)")
        print("  recruiter@demo.com (user)")
        print("  ops@demo.com    (user)")
        print(f"\nDemo organizations: {len(DEMO_ORGS)}")
        print(f"Demo apps: {len(DEMO_APPS)}")
        print(f"Demo data records: {len(DEMO_RECORDS)}")

    except Exception as e:
        db.rollback()
        print(f"\n✗ Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
