"""
Business App Templates for SRP Autonomous OS.

Defines structured templates for common business applications.
Each template includes SQL table definitions, module names, description,
and logic hooks.

DO NOT modify existing orchestrator logic. This file is additive only.
"""

from typing import Optional


# ---------------------------------------------------------------------------
# Template definitions
# ---------------------------------------------------------------------------

PAYROLL_TEMPLATE = {
    "name": "payroll",
    "description": (
        "Full-featured payroll management system covering employee records, "
        "attendance tracking, salary components, payroll run cycles, and payslip generation."
    ),
    "tables": [
        """CREATE TABLE IF NOT EXISTS employees (
    id          SERIAL PRIMARY KEY,
    first_name  VARCHAR(100) NOT NULL,
    last_name   VARCHAR(100) NOT NULL,
    email       VARCHAR(255) UNIQUE NOT NULL,
    department  VARCHAR(100),
    position    VARCHAR(100),
    hire_date   DATE NOT NULL,
    status      VARCHAR(20) DEFAULT 'active',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
        """CREATE TABLE IF NOT EXISTS attendance (
    id            SERIAL PRIMARY KEY,
    employee_id   INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    date          DATE NOT NULL,
    check_in      TIME,
    check_out     TIME,
    hours_worked  NUMERIC(5, 2),
    status        VARCHAR(20) DEFAULT 'present',
    notes         TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (employee_id, date)
);""",
        """CREATE TABLE IF NOT EXISTS salary_components (
    id            SERIAL PRIMARY KEY,
    employee_id   INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    component     VARCHAR(100) NOT NULL,
    component_type VARCHAR(20) NOT NULL CHECK (component_type IN ('earning', 'deduction')),
    amount        NUMERIC(12, 2) NOT NULL DEFAULT 0,
    is_percentage BOOLEAN DEFAULT FALSE,
    effective_from DATE NOT NULL,
    effective_to   DATE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
        """CREATE TABLE IF NOT EXISTS payroll_runs (
    id            SERIAL PRIMARY KEY,
    period_start  DATE NOT NULL,
    period_end    DATE NOT NULL,
    run_date      DATE NOT NULL DEFAULT CURRENT_DATE,
    status        VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'processing', 'completed', 'cancelled')),
    total_gross   NUMERIC(14, 2) DEFAULT 0,
    total_net     NUMERIC(14, 2) DEFAULT 0,
    total_deductions NUMERIC(14, 2) DEFAULT 0,
    processed_by  VARCHAR(255),
    notes         TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
        """CREATE TABLE IF NOT EXISTS payslips (
    id               SERIAL PRIMARY KEY,
    payroll_run_id   INTEGER NOT NULL REFERENCES payroll_runs(id) ON DELETE CASCADE,
    employee_id      INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    gross_salary     NUMERIC(12, 2) NOT NULL DEFAULT 0,
    total_deductions NUMERIC(12, 2) NOT NULL DEFAULT 0,
    net_salary       NUMERIC(12, 2) NOT NULL DEFAULT 0,
    breakdown        JSONB,
    issued_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (payroll_run_id, employee_id)
);""",
    ],
    "modules": [
        "employee_management",
        "attendance_tracking",
        "salary_configuration",
        "payroll_run_engine",
        "payslip_generator",
        "tax_calculator",
        "reports_dashboard",
    ],
    "logic_hooks": [
        "on_payroll_run_complete",
        "on_payslip_generated",
        "on_employee_status_change",
        "on_attendance_submitted",
    ],
}


INVOICE_TEMPLATE = {
    "name": "invoice",
    "description": (
        "End-to-end invoicing system with customer management, product catalogue, "
        "invoice creation, line-item tracking, and payment status monitoring."
    ),
    "tables": [
        """CREATE TABLE IF NOT EXISTS customers (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(255) NOT NULL,
    email         VARCHAR(255) UNIQUE,
    phone         VARCHAR(50),
    address       TEXT,
    city          VARCHAR(100),
    country       VARCHAR(100),
    tax_id        VARCHAR(100),
    status        VARCHAR(20) DEFAULT 'active',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
        """CREATE TABLE IF NOT EXISTS products (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(255) NOT NULL,
    description   TEXT,
    sku           VARCHAR(100) UNIQUE,
    unit_price    NUMERIC(12, 2) NOT NULL DEFAULT 0,
    tax_rate      NUMERIC(5, 2) DEFAULT 0,
    unit          VARCHAR(50) DEFAULT 'unit',
    status        VARCHAR(20) DEFAULT 'active',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
        """CREATE TABLE IF NOT EXISTS invoices (
    id             SERIAL PRIMARY KEY,
    invoice_number VARCHAR(100) UNIQUE NOT NULL,
    customer_id    INTEGER NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    issue_date     DATE NOT NULL DEFAULT CURRENT_DATE,
    due_date       DATE,
    status         VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'sent', 'paid', 'overdue', 'cancelled')),
    subtotal       NUMERIC(14, 2) DEFAULT 0,
    tax_total      NUMERIC(14, 2) DEFAULT 0,
    discount       NUMERIC(14, 2) DEFAULT 0,
    total          NUMERIC(14, 2) DEFAULT 0,
    notes          TEXT,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
        """CREATE TABLE IF NOT EXISTS invoice_items (
    id           SERIAL PRIMARY KEY,
    invoice_id   INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    product_id   INTEGER REFERENCES products(id) ON DELETE SET NULL,
    description  TEXT NOT NULL,
    quantity     NUMERIC(10, 3) NOT NULL DEFAULT 1,
    unit_price   NUMERIC(12, 2) NOT NULL DEFAULT 0,
    tax_rate     NUMERIC(5, 2) DEFAULT 0,
    line_total   NUMERIC(14, 2) NOT NULL DEFAULT 0,
    sort_order   INTEGER DEFAULT 0
);""",
    ],
    "modules": [
        "customer_management",
        "product_catalogue",
        "invoice_builder",
        "tax_engine",
        "payment_tracker",
        "pdf_generator",
        "email_dispatcher",
        "reports_dashboard",
    ],
    "logic_hooks": [
        "on_invoice_sent",
        "on_invoice_paid",
        "on_invoice_overdue",
        "on_customer_created",
    ],
}


CRM_TEMPLATE = {
    "name": "crm",
    "description": (
        "Customer Relationship Management system with lead capture, deal pipeline, "
        "activity logging, and contact management."
    ),
    "tables": [
        """CREATE TABLE IF NOT EXISTS leads (
    id            SERIAL PRIMARY KEY,
    first_name    VARCHAR(100),
    last_name     VARCHAR(100),
    email         VARCHAR(255),
    phone         VARCHAR(50),
    company       VARCHAR(255),
    source        VARCHAR(100),
    status        VARCHAR(30) DEFAULT 'new' CHECK (status IN ('new', 'contacted', 'qualified', 'converted', 'lost')),
    assigned_to   VARCHAR(255),
    notes         TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
        """CREATE TABLE IF NOT EXISTS deals (
    id            SERIAL PRIMARY KEY,
    title         VARCHAR(255) NOT NULL,
    lead_id       INTEGER REFERENCES leads(id) ON DELETE SET NULL,
    contact_id    INTEGER,
    stage         VARCHAR(50) DEFAULT 'prospecting',
    value         NUMERIC(14, 2) DEFAULT 0,
    currency      VARCHAR(10) DEFAULT 'USD',
    probability   NUMERIC(5, 2) DEFAULT 0,
    expected_close DATE,
    status        VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'won', 'lost')),
    assigned_to   VARCHAR(255),
    notes         TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
        """CREATE TABLE IF NOT EXISTS activities (
    id            SERIAL PRIMARY KEY,
    activity_type VARCHAR(50) NOT NULL CHECK (activity_type IN ('call', 'email', 'meeting', 'task', 'note')),
    subject       VARCHAR(255) NOT NULL,
    description   TEXT,
    deal_id       INTEGER REFERENCES deals(id) ON DELETE CASCADE,
    lead_id       INTEGER REFERENCES leads(id) ON DELETE CASCADE,
    contact_id    INTEGER,
    due_date      TIMESTAMP,
    completed_at  TIMESTAMP,
    status        VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'cancelled')),
    assigned_to   VARCHAR(255),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
        """CREATE TABLE IF NOT EXISTS contacts (
    id            SERIAL PRIMARY KEY,
    first_name    VARCHAR(100) NOT NULL,
    last_name     VARCHAR(100),
    email         VARCHAR(255) UNIQUE,
    phone         VARCHAR(50),
    company       VARCHAR(255),
    job_title     VARCHAR(100),
    lead_id       INTEGER REFERENCES leads(id) ON DELETE SET NULL,
    tags          TEXT[],
    notes         TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
    ],
    "modules": [
        "lead_capture",
        "deal_pipeline",
        "activity_log",
        "contact_management",
        "email_integration",
        "sales_forecasting",
        "reports_dashboard",
    ],
    "logic_hooks": [
        "on_lead_created",
        "on_lead_converted",
        "on_deal_stage_changed",
        "on_deal_won",
        "on_deal_lost",
        "on_activity_completed",
    ],
}


# ---------------------------------------------------------------------------
# Hospital / Healthcare Template
# ---------------------------------------------------------------------------

HOSPITAL_TEMPLATE = {
    "name": "hospital",
    "description": (
        "Patient management, appointment scheduling, staff roster, and billing "
        "for hospitals, clinics, and healthcare providers."
    ),
    "tables": [
        """CREATE TABLE IF NOT EXISTS patients (
    id            SERIAL PRIMARY KEY,
    first_name    VARCHAR(100) NOT NULL,
    last_name     VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    gender        VARCHAR(20),
    email         VARCHAR(255),
    phone         VARCHAR(50),
    address       TEXT,
    blood_group   VARCHAR(10),
    allergies     TEXT,
    status        VARCHAR(20) DEFAULT 'active',
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
        """CREATE TABLE IF NOT EXISTS appointments (
    id             SERIAL PRIMARY KEY,
    patient_id     INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_name    VARCHAR(100) NOT NULL,
    department     VARCHAR(100),
    appointment_at TIMESTAMP NOT NULL,
    duration_mins  INTEGER DEFAULT 30,
    reason         TEXT,
    status         VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled','confirmed','completed','cancelled','no_show')),
    notes          TEXT,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
        """CREATE TABLE IF NOT EXISTS medical_records (
    id           SERIAL PRIMARY KEY,
    patient_id   INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    visit_date   DATE NOT NULL DEFAULT CURRENT_DATE,
    diagnosis    TEXT,
    treatment    TEXT,
    prescription TEXT,
    doctor_name  VARCHAR(100),
    follow_up    DATE,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
        """CREATE TABLE IF NOT EXISTS staff_roster (
    id           SERIAL PRIMARY KEY,
    staff_name   VARCHAR(100) NOT NULL,
    role         VARCHAR(100) NOT NULL,
    department   VARCHAR(100),
    shift_start  TIME,
    shift_end    TIME,
    shift_date   DATE NOT NULL,
    status       VARCHAR(20) DEFAULT 'scheduled',
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
    ],
    "modules": [
        "patient_management",
        "appointment_scheduling",
        "medical_records",
        "staff_roster",
        "payroll_run_engine",
        "invoice_builder",
        "reports_dashboard",
    ],
    "logic_hooks": [
        "on_appointment_confirmed",
        "on_appointment_completed",
        "on_patient_registered",
        "on_staff_shift_changed",
    ],
}

# ---------------------------------------------------------------------------
# School / Education Template
# ---------------------------------------------------------------------------

SCHOOL_TEMPLATE = {
    "name": "school",
    "description": (
        "Student enrollment, class management, fee collection, attendance, "
        "and reporting for schools, colleges, and training institutes."
    ),
    "tables": [
        """CREATE TABLE IF NOT EXISTS students (
    id            SERIAL PRIMARY KEY,
    first_name    VARCHAR(100) NOT NULL,
    last_name     VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    gender        VARCHAR(20),
    email         VARCHAR(255),
    phone         VARCHAR(50),
    parent_name   VARCHAR(100),
    parent_phone  VARCHAR(50),
    class_name    VARCHAR(50),
    enrollment_no VARCHAR(100) UNIQUE,
    status        VARCHAR(20) DEFAULT 'active',
    enrolled_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
        """CREATE TABLE IF NOT EXISTS classes (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    grade        VARCHAR(20),
    section      VARCHAR(20),
    teacher_name VARCHAR(100),
    room         VARCHAR(50),
    capacity     INTEGER DEFAULT 30,
    academic_year VARCHAR(20),
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
        """CREATE TABLE IF NOT EXISTS student_attendance (
    id           SERIAL PRIMARY KEY,
    student_id   INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    class_id     INTEGER REFERENCES classes(id) ON DELETE SET NULL,
    date         DATE NOT NULL,
    status       VARCHAR(20) DEFAULT 'present' CHECK (status IN ('present','absent','late','excused')),
    notes        TEXT,
    UNIQUE (student_id, date)
);""",
        """CREATE TABLE IF NOT EXISTS fee_payments (
    id            SERIAL PRIMARY KEY,
    student_id    INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    fee_type      VARCHAR(100) NOT NULL,
    amount        NUMERIC(12, 2) NOT NULL,
    due_date      DATE NOT NULL,
    paid_date     DATE,
    status        VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending','paid','overdue','waived')),
    payment_method VARCHAR(50),
    notes         TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
    ],
    "modules": [
        "student_management",
        "class_management",
        "attendance_tracking",
        "fee_collection",
        "reports_dashboard",
    ],
    "logic_hooks": [
        "on_student_enrolled",
        "on_fee_paid",
        "on_fee_overdue",
        "on_attendance_submitted",
    ],
}

# ---------------------------------------------------------------------------
# IT / Software Company Template
# ---------------------------------------------------------------------------

IT_COMPANY_TEMPLATE = {
    "name": "it_company",
    "description": (
        "Project tracking, client billing, technical recruitment, HR operations, "
        "and CRM for IT firms and software companies."
    ),
    "tables": [
        """CREATE TABLE IF NOT EXISTS projects (
    id             SERIAL PRIMARY KEY,
    name           VARCHAR(255) NOT NULL,
    client_name    VARCHAR(255),
    project_type   VARCHAR(100),
    status         VARCHAR(30) DEFAULT 'active' CHECK (status IN ('active','on_hold','completed','cancelled')),
    start_date     DATE,
    end_date       DATE,
    budget         NUMERIC(14, 2) DEFAULT 0,
    billed_amount  NUMERIC(14, 2) DEFAULT 0,
    tech_stack     TEXT[],
    lead_dev       VARCHAR(100),
    notes          TEXT,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
        """CREATE TABLE IF NOT EXISTS project_tasks (
    id           SERIAL PRIMARY KEY,
    project_id   INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title        VARCHAR(255) NOT NULL,
    description  TEXT,
    assignee     VARCHAR(100),
    priority     VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low','medium','high','critical')),
    status       VARCHAR(30) DEFAULT 'todo' CHECK (status IN ('todo','in_progress','review','done')),
    due_date     DATE,
    estimated_hours NUMERIC(6, 2) DEFAULT 0,
    logged_hours    NUMERIC(6, 2) DEFAULT 0,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
        """CREATE TABLE IF NOT EXISTS timesheets (
    id           SERIAL PRIMARY KEY,
    employee_id  INTEGER,
    project_id   INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    task_id      INTEGER REFERENCES project_tasks(id) ON DELETE SET NULL,
    work_date    DATE NOT NULL,
    hours_worked NUMERIC(5, 2) NOT NULL,
    description  TEXT,
    billable     BOOLEAN DEFAULT TRUE,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
    ],
    "modules": [
        "project_management",
        "task_tracker",
        "timesheet_logging",
        "lead_capture",
        "deal_pipeline",
        "invoice_builder",
        "reports_dashboard",
    ],
    "logic_hooks": [
        "on_project_created",
        "on_project_completed",
        "on_task_status_changed",
        "on_timesheet_submitted",
    ],
}

# ---------------------------------------------------------------------------
# HR / Recruitment Agency Template
# ---------------------------------------------------------------------------

HR_RECRUITMENT_TEMPLATE = {
    "name": "hr_recruitment",
    "description": (
        "Candidate pipeline, client CRM, placement tracking, and commission "
        "management for recruitment and HR agencies."
    ),
    "tables": [
        """CREATE TABLE IF NOT EXISTS candidates (
    id              SERIAL PRIMARY KEY,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(255) UNIQUE,
    phone           VARCHAR(50),
    current_role    VARCHAR(100),
    years_exp       INTEGER DEFAULT 0,
    skills          TEXT[],
    expected_salary NUMERIC(14, 2),
    cv_url          TEXT,
    status          VARCHAR(30) DEFAULT 'available' CHECK (status IN ('available','interviewing','placed','on_hold','not_available')),
    source          VARCHAR(100),
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
        """CREATE TABLE IF NOT EXISTS job_openings (
    id              SERIAL PRIMARY KEY,
    title           VARCHAR(255) NOT NULL,
    client_name     VARCHAR(255) NOT NULL,
    location        VARCHAR(100),
    job_type        VARCHAR(50) DEFAULT 'permanent',
    salary_min      NUMERIC(14, 2),
    salary_max      NUMERIC(14, 2),
    skills_required TEXT[],
    description     TEXT,
    status          VARCHAR(30) DEFAULT 'open' CHECK (status IN ('open','filled','cancelled','on_hold')),
    deadline        DATE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
        """CREATE TABLE IF NOT EXISTS placements (
    id              SERIAL PRIMARY KEY,
    candidate_id    INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    job_id          INTEGER REFERENCES job_openings(id) ON DELETE SET NULL,
    client_name     VARCHAR(255),
    start_date      DATE,
    placement_fee   NUMERIC(14, 2) DEFAULT 0,
    commission_rate NUMERIC(5, 2) DEFAULT 10.0,
    commission_paid BOOLEAN DEFAULT FALSE,
    status          VARCHAR(30) DEFAULT 'active' CHECK (status IN ('active','completed','cancelled')),
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
    ],
    "modules": [
        "candidate_management",
        "job_openings",
        "placement_tracker",
        "contact_management",
        "deal_pipeline",
        "activity_log",
        "reports_dashboard",
    ],
    "logic_hooks": [
        "on_candidate_placed",
        "on_job_filled",
        "on_commission_due",
        "on_cv_submitted",
    ],
}

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_TEMPLATE_REGISTRY: dict[str, dict] = {
    "payroll": PAYROLL_TEMPLATE,
    "invoice": INVOICE_TEMPLATE,
    "crm": CRM_TEMPLATE,
    "hospital": HOSPITAL_TEMPLATE,
    "school": SCHOOL_TEMPLATE,
    "it_company": IT_COMPANY_TEMPLATE,
    "hr_recruitment": HR_RECRUITMENT_TEMPLATE,
}

# Keywords mapped to template names (order matters for specificity)
_KEYWORD_MAP: list[tuple[str, Optional[str]]] = [
    # Payroll
    ("payroll", "payroll"),
    ("salary", "payroll"),
    ("payslip", "payroll"),
    # School / Education (before 'employee' to avoid matching 'employee' on school prompts)
    ("student", "school"),
    ("school", "school"),
    ("education", "school"),
    ("college", "school"),
    ("tuition", "school"),
    ("fee collection", "school"),
    # Hospital
    ("hospital", "hospital"),
    ("patient", "hospital"),
    ("clinic", "hospital"),
    ("healthcare", "hospital"),
    ("appointment", "hospital"),
    ("medical", "hospital"),
    # IT / Software
    ("project management", "it_company"),
    ("timesheet", "it_company"),
    ("software company", "it_company"),
    ("it company", "it_company"),
    ("sprint", "it_company"),
    # HR / Recruitment
    ("candidate", "hr_recruitment"),
    ("recruitment", "hr_recruitment"),
    ("placement", "hr_recruitment"),
    ("staffing", "hr_recruitment"),
    ("job opening", "hr_recruitment"),
    # Generic payroll / employee (after more specific keywords)
    ("employee", "payroll"),
    ("attendance", "payroll"),
    # Invoice / Finance
    ("invoice", "invoice"),
    ("billing", "invoice"),
    ("receipt", "invoice"),
    ("quotation", "invoice"),
    ("quote", "invoice"),
    # CRM / Sales
    ("crm", "crm"),
    ("lead", "crm"),
    ("deal", "crm"),
    ("pipeline", "crm"),
    ("contact", "crm"),
    ("sales", "crm"),
    # Reserved — future templates
    ("inventory", None),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_template_by_prompt(prompt: str) -> Optional[dict]:
    """
    Detect business-app keywords in *prompt* and return the matching template.

    Parameters
    ----------
    prompt : str
        Free-text description or instruction from which the desired template
        should be inferred.

    Returns
    -------
    dict | None
        A copy of the matching template dictionary, or ``None`` if no
        template could be matched (including the 'inventory' keyword which
        is reserved for a future template).

    Examples
    --------
    >>> tpl = get_template_by_prompt("build me a payroll system")
    >>> tpl["name"]
    'payroll'

    >>> get_template_by_prompt("I need an inventory tracker")
    # returns None — inventory template not yet implemented

    >>> get_template_by_prompt("something completely different")
    # returns None
    """
    normalised = prompt.lower()

    for keyword, template_name in _KEYWORD_MAP:
        if keyword in normalised:
            if template_name is None:
                # Keyword recognised but template not yet available
                return None
            return dict(_TEMPLATE_REGISTRY[template_name])

    return None


def list_templates() -> list[str]:
    """Return the names of all registered templates."""
    return list(_TEMPLATE_REGISTRY.keys())


def get_template_by_name(name: str) -> Optional[dict]:
    """
    Retrieve a template directly by its canonical name.

    Parameters
    ----------
    name : str
        One of 'payroll', 'invoice', or 'crm'.

    Returns
    -------
    dict | None
        A copy of the template dictionary, or ``None`` if the name is not
        registered.
    """
    template = _TEMPLATE_REGISTRY.get(name.lower())
    return dict(template) if template else None
