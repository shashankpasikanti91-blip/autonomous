-- =============================================================================
-- SRP Autonomous OS — Foundation Schema
-- Migration: 001_foundation
-- Applied to: Supabase (PostgreSQL)
-- =============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. CORE TABLES
-- ─────────────────────────────────────────────────────────────────────────────

-- core_users: one row per authenticated user
create table if not exists core_users (
  id          uuid primary key default gen_random_uuid(),
  email       text unique not null,
  role        text not null default 'owner',
  created_at  timestamptz not null default now()
);

-- organizations: multi-tenant root
create table if not exists organizations (
  id          uuid primary key default gen_random_uuid(),
  owner_id    uuid not null references core_users(id) on delete cascade,
  name        text not null,
  country     text,
  industry    text,
  created_at  timestamptz not null default now()
);

-- apps: one app per organisation task
create table if not exists apps (
  id              uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  name            text not null,
  description     text,
  status          text not null default 'active',
  created_at      timestamptz not null default now()
);

-- app_schemas: versioned JSON schema produced by the planner
create table if not exists app_schemas (
  id          uuid primary key default gen_random_uuid(),
  app_id      uuid not null references apps(id) on delete cascade,
  schema_json jsonb,
  version     integer not null default 1,
  created_at  timestamptz not null default now()
);

-- app_records: real data submitted through the app
create table if not exists app_records (
  id          uuid primary key default gen_random_uuid(),
  app_id      uuid not null references apps(id) on delete cascade,
  record_json jsonb,
  created_at  timestamptz not null default now()
);

-- country_rules: database-driven business rules per country/industry
create table if not exists country_rules (
  id          uuid primary key default gen_random_uuid(),
  country     text,
  industry    text,
  rule_type   text,
  rule_json   jsonb,
  created_at  timestamptz not null default now()
);

-- execution_logs: immutable audit trail of every action
create table if not exists execution_logs (
  id            uuid primary key default gen_random_uuid(),
  app_id        uuid not null references apps(id) on delete cascade,
  action        text not null,
  status        text not null,
  response_json jsonb,
  created_at    timestamptz not null default now()
);

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. INDEXES
-- ─────────────────────────────────────────────────────────────────────────────

create index if not exists idx_organizations_owner      on organizations(owner_id);
create index if not exists idx_apps_organization        on apps(organization_id);
create index if not exists idx_app_schemas_app          on app_schemas(app_id);
create index if not exists idx_app_records_app          on app_records(app_id);
create index if not exists idx_execution_logs_app       on execution_logs(app_id);
create index if not exists idx_execution_logs_created   on execution_logs(created_at desc);
create index if not exists idx_country_rules_country    on country_rules(country, industry);

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. ROW LEVEL SECURITY
-- ─────────────────────────────────────────────────────────────────────────────

alter table core_users        enable row level security;
alter table organizations     enable row level security;
alter table apps              enable row level security;
alter table app_schemas       enable row level security;
alter table app_records       enable row level security;
alter table country_rules     enable row level security;
alter table execution_logs    enable row level security;

-- ── core_users: each user can only read/update their own row ─────────────────

create policy "users: own row only"
  on core_users
  for all
  using (auth.uid() = id);

-- ── organizations: owner can do everything; members can read ─────────────────

create policy "orgs: owner full access"
  on organizations
  for all
  using (owner_id = auth.uid());

-- ── apps: accessible only through owning organization ────────────────────────

create policy "apps: org owner access"
  on apps
  for all
  using (
    organization_id in (
      select id from organizations where owner_id = auth.uid()
    )
  );

-- ── app_schemas: same isolation as apps ──────────────────────────────────────

create policy "app_schemas: via org ownership"
  on app_schemas
  for all
  using (
    app_id in (
      select a.id from apps a
      join organizations o on o.id = a.organization_id
      where o.owner_id = auth.uid()
    )
  );

-- ── app_records: same isolation as apps ──────────────────────────────────────

create policy "app_records: via org ownership"
  on app_records
  for all
  using (
    app_id in (
      select a.id from apps a
      join organizations o on o.id = a.organization_id
      where o.owner_id = auth.uid()
    )
  );

-- ── execution_logs: read-only through org ownership (append-only via service role) ──

create policy "execution_logs: read via org ownership"
  on execution_logs
  for select
  using (
    app_id in (
      select a.id from apps a
      join organizations o on o.id = a.organization_id
      where o.owner_id = auth.uid()
    )
  );

-- ── country_rules: readable by any authenticated user ────────────────────────

create policy "country_rules: public read"
  on country_rules
  for select
  using (auth.role() = 'authenticated');

-- country_rules: write restricted to service role only (no user policy needed,
-- service role bypasses RLS by default)

-- ─────────────────────────────────────────────────────────────────────────────
-- 4. SEED — sample country rules
-- ─────────────────────────────────────────────────────────────────────────────

insert into country_rules (country, industry, rule_type, rule_json) values
('MY', 'general', 'tax', '{"gst_rate": 0.06, "currency": "MYR", "fiscal_year_start": "01-01"}'),
('IN', 'general', 'tax', '{"gst_rate": 0.18, "currency": "INR", "fiscal_year_start": "04-01"}'),
('AU', 'general', 'tax', '{"gst_rate": 0.10, "currency": "AUD", "fiscal_year_start": "07-01"}'),
('MY', 'hr',      'leave', '{"annual_leave_days": 12, "sick_leave_days": 14, "public_holidays": 11}'),
('IN', 'hr',      'leave', '{"annual_leave_days": 15, "sick_leave_days": 12, "public_holidays": 15}'),
('AU', 'hr',      'leave', '{"annual_leave_days": 20, "sick_leave_days": 10, "public_holidays":  9}')
on conflict do nothing;
