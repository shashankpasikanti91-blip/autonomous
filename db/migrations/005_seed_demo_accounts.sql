-- =============================================================================
-- Demo Accounts Seed Data for Emergentic AI Platform
-- Run: psql -d srp_os -f db/migrations/005_seed_demo_accounts.sql
-- =============================================================================

-- =============================================================================
-- Demo Users (fake accounts for demo purposes)
-- =============================================================================

-- Admin user
INSERT INTO core_users (id, email, role)
VALUES ('00000000-0000-0000-0000-000000000001', 'admin@demo.com', 'admin')
ON CONFLICT (email) DO UPDATE SET role = 'admin';

-- Demo owner user
INSERT INTO core_users (id, email, role)
VALUES ('00000000-0000-0000-0000-000000000002', 'owner@demo.com', 'owner')
ON CONFLICT (email) DO NOTHING;

-- HR Manager
INSERT INTO core_users (id, email, role)
VALUES ('00000000-0000-0000-0000-000000000003', 'hr@demo.com', 'manager')
ON CONFLICT (email) DO NOTHING;

-- Finance Manager
INSERT INTO core_users (id, email, role)
VALUES ('00000000-0000-0000-0000-000000000004', 'finance@demo.com', 'manager')
ON CONFLICT (email) DO NOTHING;

-- Sales Rep
INSERT INTO core_users (id, email, role)
VALUES ('00000000-0000-0000-0000-000000000005', 'sales@demo.com', 'user')
ON CONFLICT (email) DO NOTHING;

-- Developer
INSERT INTO core_users (id, email, role)
VALUES ('00000000-0000-0000-0000-000000000006', 'dev@demo.com', 'user')
ON CONFLICT (email) DO NOTHING;

-- Recruiter
INSERT INTO core_users (id, email, role)
VALUES ('00000000-0000-0000-0000-000000000007', 'recruiter@demo.com', 'user')
ON CONFLICT (email) DO NOTHING;

-- Operations
INSERT INTO core_users (id, email, role)
VALUES ('00000000-0000-0000-0000-000000000008', 'ops@demo.com', 'user')
ON CONFLICT (email) DO NOTHING;

-- =============================================================================
-- Demo Organizations
-- =============================================================================

-- Tech company
INSERT INTO organizations (id, owner_id, name, slug, custom_domain, country, industry)
VALUES (
    '00000000-0000-0000-0000-000000000010',
    '00000000-0000-0000-0000-000000000001',
    'Emergentic AI Demo',
    'emergentic-demo',
    NULL,
    'US',
    'it_company'
) ON CONFLICT (slug) DO NOTHING;

-- Healthcare org
INSERT INTO organizations (id, owner_id, name, slug, custom_domain, country, industry)
VALUES (
    '00000000-0000-0000-0000-000000000011',
    '00000000-0000-0000-0000-000000000002',
    'MediCare Hospital',
    'medicare-hospital',
    NULL,
    'US',
    'hospital'
) ON CONFLICT (slug) DO NOTHING;

-- School
INSERT INTO organizations (id, owner_id, name, slug, custom_domain, country, industry)
VALUES (
    '00000000-0000-0000-0000-000000000012',
    '00000000-0000-0000-0000-000000000002',
    'Bright Future Academy',
    'bright-future',
    NULL,
    'UK',
    'school'
) ON CONFLICT (slug) DO NOTHING;

-- Recruitment agency
INSERT INTO organizations (id, owner_id, name, slug, custom_domain, country, industry)
VALUES (
    '00000000-0000-0000-0000-000000000013',
    '00000000-0000-0000-0000-000000000007',
    'TalentHub Recruiting',
    'talenthub',
    NULL,
    'AE',
    'recruitment'
) ON CONFLICT (slug) DO NOTHING;

-- Payroll/Finance company
INSERT INTO organizations (id, owner_id, name, slug, custom_domain, country, industry)
VALUES (
    '00000000-0000-0000-0000-000000000014',
    '00000000-0000-0000-0000-000000000004',
    'PayRight Financial Services',
    'payright',
    NULL,
    'MY',
    'payroll_finance'
) ON CONFLICT (slug) DO NOTHING;

-- Service business
INSERT INTO organizations (id, owner_id, name, slug, custom_domain, country, industry)
VALUES (
    '00000000-0000-0000-0000-000000000015',
    '00000000-0000-0000-0000-000000000005',
    'ServicePro Solutions',
    'servicepro',
    NULL,
    'AU',
    'service_business'
) ON CONFLICT (slug) DO NOTHING;

-- =============================================================================
-- Demo Apps
-- =============================================================================

-- Payroll App for Emergentic Demo
INSERT INTO apps (id, organization_id, name, description, status, app_type, modules)
VALUES (
    '00000000-0000-0000-0000-000000000100',
    '00000000-0000-0000-0000-000000000010',
    'Payroll Manager',
    'Automated payroll processing with tax calculation',
    'active',
    'payroll',
    '["employee_management","attendance_tracking","salary_configuration","payroll_run_engine","payslip_generator","tax_calculator"]'::jsonb
) ON CONFLICT DO NOTHING;

-- CRM App for Emergentic Demo
INSERT INTO apps (id, organization_id, name, description, status, app_type, modules)
VALUES (
    '00000000-0000-0000-0000-000000000101',
    '00000000-0000-0000-0000-000000000010',
    'Sales CRM',
    'Customer relationship management and deal tracking',
    'active',
    'crm',
    '["lead_capture","deal_pipeline","activity_log","contact_management","email_integration","sales_forecasting"]'::jsonb
) ON CONFLICT DO NOTHING;

-- Invoice App for ServicePro
INSERT INTO apps (id, organization_id, name, description, status, app_type, modules)
VALUES (
    '00000000-0000-0000-0000-000000000102',
    '00000000-0000-0000-0000-000000000015',
    'Invoice Generator',
    'Professional invoice creation and payment tracking',
    'active',
    'invoice',
    '["customer_management","product_catalogue","invoice_builder","tax_engine","payment_tracker","pdf_generator","email_dispatcher"]'::jsonb
) ON CONFLICT DO NOTHING;

-- Patient Management for MediCare
INSERT INTO apps (id, organization_id, name, description, status, app_type, modules)
VALUES (
    '00000000-0000-0000-0000-000000000103',
    '00000000-0000-0000-0000-000000000011',
    'Patient Records',
    'Electronic health records management system',
    'active',
    'custom',
    '["patient_intake","medical_records","appointment_scheduler","prescription_tracker"]'::jsonb
) ON CONFLICT DO NOTHING;

-- Student System for Bright Future
INSERT INTO apps (id, organization_id, name, description, status, app_type, modules)
VALUES (
    '00000000-0000-0000-0000-000000000104',
    '00000000-0000-0000-0000-000000000012',
    'Student Management',
    'Student enrollment and academic tracking',
    'active',
    'custom',
    '["student_enrollment","class_management","attendance","grade_book","fee_collection"]'::jsonb
) ON CONFLICT DO NOTHING;

-- Recruitment App for TalentHub
INSERT INTO apps (id, organization_id, name, description, status, app_type, modules)
VALUES (
    '00000000-0000-0000-0000-000000000105',
    '00000000-0000-0000-0000-000000000013',
    'Talent Pipeline',
    'End-to-end recruitment workflow automation',
    'active',
    'custom',
    '["job_postings","candidate_tracker","interview_scheduler","offer_management","onboarding"]'::jsonb
) ON CONFLICT DO NOTHING;

-- =============================================================================
-- Demo App Schemas
-- =============================================================================

INSERT INTO app_schemas (id, app_id, schema_json, version)
VALUES (
    '00000000-0000-0000-0000-000000000200',
    '00000000-0000-0000-0000-000000000100',
    '{
        "tables": {
            "employees": {"columns": ["id", "name", "email", "department", "position", "salary", "status"]},
            "payroll_runs": {"columns": ["id", "period_start", "period_end", "run_date", "status", "total_gross", "total_net"]},
            "payslips": {"columns": ["id", "employee_id", "payroll_run_id", "gross", "net", "deductions"]}
        }
    }'::jsonb,
    1
) ON CONFLICT DO NOTHING;

INSERT INTO app_schemas (id, app_id, schema_json, version)
VALUES (
    '00000000-0000-0000-0000-000000000201',
    '00000000-0000-0000-0000-000000000101',
    '{
        "tables": {
            "leads": {"columns": ["id", "name", "email", "company", "source", "status", "score"]},
            "deals": {"columns": ["id", "lead_id", "title", "value", "stage", "probability"]},
            "contacts": {"columns": ["id", "name", "email", "phone", "company", "role"]}
        }
    }'::jsonb,
    1
) ON CONFLICT DO NOTHING;

-- =============================================================================
-- Demo App Records (sample data entries)
-- =============================================================================

-- Payroll employee records
INSERT INTO app_records (id, app_id, record_json)
VALUES
    ('00000000-0000-0000-0000-000000000300', '00000000-0000-0000-0000-000000000100',
     '{"type": "employee", "name": "Ahmad Al-Hassan", "email": "ahmad@company.com", "department": "Engineering", "position": "Senior Developer", "salary": 8500, "status": "active"}'::jsonb),
    ('00000000-0000-0000-0000-000000000301', '00000000-0000-0000-0000-000000000100',
     '{"type": "employee", "name": "Sarah Johnson", "email": "sarah@company.com", "department": "Marketing", "position": "Marketing Lead", "salary": 7200, "status": "active"}'::jsonb),
    ('00000000-0000-0000-0000-000000000302', '00000000-0000-0000-0000-000000000100',
     '{"type": "employee", "name": "James Chen", "email": "james@company.com", "department": "Engineering", "position": "DevOps Engineer", "salary": 9000, "status": "active"}'::jsonb),
    ('00000000-0000-0000-0000-000000000303', '00000000-0000-0000-0000-000000000100',
     '{"type": "employee", "name": "Maria Garcia", "email": "maria@company.com", "department": "Finance", "position": "Financial Analyst", "salary": 7800, "status": "active"}'::jsonb),
    ('00000000-0000-0000-0000-000000000304', '00000000-0000-0000-0000-000000000100',
     '{"type": "employee", "name": "David Kim", "email": "david@company.com", "department": "Sales", "position": "Account Executive", "salary": 6500, "status": "active"}'::jsonb)
ON CONFLICT DO NOTHING;

-- CRM lead records
INSERT INTO app_records (id, app_id, record_json)
VALUES
    ('00000000-0000-0000-0000-000000000310', '00000000-0000-0000-0000-000000000101',
     '{"type": "lead", "name": "TechStart Inc", "contact": "m.rashid@techstart.com", "source": "website", "budget": 50000, "status": "qualified", "score": 0.85}'::jsonb),
    ('00000000-0000-0000-0000-000000000311', '00000000-0000-0000-0000-000000000101',
     '{"type": "lead", "name": "GlobalTech Solutions", "contact": "info@globaltech.com", "source": "referral", "budget": 120000, "status": "negotiation", "score": 0.92}'::jsonb),
    ('00000000-0000-0000-0000-000000000312', '00000000-0000-0000-0000-000000000101',
     '{"type": "lead", "name": "InnovateCo", "contact": "sales@innovateco.com", "source": "conference", "budget": 35000, "status": "new", "score": 0.60}'::jsonb)
ON CONFLICT DO NOTHING;

-- Invoice records for ServicePro
INSERT INTO app_records (id, app_id, record_json)
VALUES
    ('00000000-0000-0000-0000-000000000320', '00000000-0000-0000-0000-000000000102',
     '{"type": "invoice", "invoice_number": "INV-2026-001", "client": "Acme Corp", "amount": 4500.00, "status": "paid", "due_date": "2026-02-28"}'::jsonb),
    ('00000000-0000-0000-0000-000000000321', '00000000-0000-0000-0000-000000000102',
     '{"type": "invoice", "invoice_number": "INV-2026-002", "client": "Beta Industries", "amount": 12750.00, "status": "pending", "due_date": "2026-03-31"}'::jsonb),
    ('00000000-0000-0000-0000-000000000322', '00000000-0000-0000-0000-000000000102',
     '{"type": "invoice", "invoice_number": "INV-2026-003", "client": "Gamma Solutions", "amount": 8900.00, "status": "overdue", "due_date": "2026-01-15"}'::jsonb)
ON CONFLICT DO NOTHING;

-- =============================================================================
-- Demo Country Rules
-- =============================================================================

INSERT INTO country_rules (id, country, industry, rule_type, rule_json)
VALUES
    ('00000000-0000-0000-0000-000000000400', 'US', NULL, 'tax',
     '{"federal_tax_brackets": [{"min": 0, "max": 10275, "rate": 0.10}, {"min": 10276, "max": 41775, "rate": 0.12}, {"min": 41776, "max": 89075, "rate": 0.22}], "social_security_rate": 0.062, "medicare_rate": 0.0145}'::jsonb),
    ('00000000-0000-0000-0000-000000000401', 'UK', NULL, 'tax',
     '{"personal_allowance": 12570, "basic_rate": 0.20, "higher_rate": 0.40, "ni_rate": 0.12}'::jsonb),
    ('00000000-0000-0000-0000-000000000402', 'MY', NULL, 'tax',
     '{"epf_employee_rate": 0.11, "epf_employer_rate": 0.12, "socso_rate": 0.005, "eis_rate": 0.002}'::jsonb),
    ('00000000-0000-0000-0000-000000000403', 'AE', NULL, 'tax',
     '{"vat_rate": 0.05, "corporate_tax_rate": 0.09, "corporate_tax_threshold": 375000}'::jsonb),
    ('00000000-0000-0000-0000-000000000404', 'US', 'hospital', 'compliance',
     '{"hipaa_required": true, "phi_encryption": "AES-256", "audit_log_retention_years": 7}'::jsonb)
ON CONFLICT DO NOTHING;

-- =============================================================================
-- Demo Execution Logs
-- =============================================================================

INSERT INTO execution_logs (id, app_id, action, status, response_json)
VALUES
    ('00000000-0000-0000-0000-000000000500', '00000000-0000-0000-0000-000000000100',
     'app_created', 'success', '{"message": "Payroll Manager app initialized"}'::jsonb),
    ('00000000-0000-0000-0000-000000000501', '00000000-0000-0000-0000-000000000100',
     'payroll_run', 'success', '{"period": "2026-02", "employees_processed": 5, "total_gross": 39000, "total_net": 31200}'::jsonb),
    ('00000000-0000-0000-0000-000000000502', '00000000-0000-0000-0000-000000000101',
     'app_created', 'success', '{"message": "Sales CRM app initialized"}'::jsonb),
    ('00000000-0000-0000-0000-000000000503', '00000000-0000-0000-0000-000000000101',
     'lead_created', 'success', '{"lead_name": "TechStart Inc", "score": 0.85}'::jsonb),
    ('00000000-0000-0000-0000-000000000504', '00000000-0000-0000-0000-000000000102',
     'invoice_generated', 'success', '{"invoice_number": "INV-2026-001", "amount": 4500.00}'::jsonb)
ON CONFLICT DO NOTHING;

-- =============================================================================
-- Summary
-- =============================================================================
-- Created:
--   8 demo users (admin, owner, hr, finance, sales, dev, recruiter, ops)
--   6 demo organizations (IT, Hospital, School, Recruitment, Finance, Service)
--   6 demo apps (Payroll, CRM, Invoice, Patient Records, Student Mgmt, Talent Pipeline)
--   2 app schemas (Payroll, CRM)
--  11 app records (employees, leads, invoices)
--   5 country rules (US, UK, MY, AE tax + US HIPAA compliance)
--   5 execution logs
--
-- Login credentials for demo:
--   admin@demo.com / admin123
--   owner@demo.com / demo123
--   hr@demo.com / demo123
--   finance@demo.com / demo123
--   sales@demo.com / demo123
-- =============================================================================
