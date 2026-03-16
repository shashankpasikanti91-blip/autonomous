-- =============================================================================
-- SRP Autonomous OS — Foundation Schema
-- Local PostgreSQL migration — run once to initialise the database.
-- =============================================================================

-- Enable pgcrypto for gen_random_uuid() on older Postgres versions
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =============================================================================
-- core_users
-- =============================================================================
CREATE TABLE IF NOT EXISTS core_users (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    email       TEXT        UNIQUE NOT NULL,
    role        TEXT        NOT NULL DEFAULT 'owner',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- organizations
-- =============================================================================
CREATE TABLE IF NOT EXISTS organizations (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id    UUID        NOT NULL REFERENCES core_users(id) ON DELETE CASCADE,
    name        TEXT        NOT NULL,
    country     TEXT,
    industry    TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- apps
-- =============================================================================
CREATE TABLE IF NOT EXISTS apps (
    id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id  UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name             TEXT        NOT NULL,
    description      TEXT,
    status           TEXT        NOT NULL DEFAULT 'active',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- app_schemas
-- =============================================================================
CREATE TABLE IF NOT EXISTS app_schemas (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    app_id      UUID        NOT NULL REFERENCES apps(id) ON DELETE CASCADE,
    schema_json JSONB,
    version     INTEGER     NOT NULL DEFAULT 1,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- app_records  (real user data rows — one per form submission / record created)
-- =============================================================================
CREATE TABLE IF NOT EXISTS app_records (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    app_id      UUID        NOT NULL REFERENCES apps(id) ON DELETE CASCADE,
    record_json JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- country_rules  (database-driven compliance / tax / legal rules per country)
-- =============================================================================
CREATE TABLE IF NOT EXISTS country_rules (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    country     TEXT        NOT NULL,
    industry    TEXT,
    rule_type   TEXT        NOT NULL,
    rule_json   JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- execution_logs  (immutable audit trail — every backend action is logged here)
-- =============================================================================
CREATE TABLE IF NOT EXISTS execution_logs (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    app_id        UUID        REFERENCES apps(id) ON DELETE CASCADE,
    action        TEXT        NOT NULL,
    status        TEXT        NOT NULL DEFAULT 'success',
    response_json JSONB,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- Indexes for multi-tenant query performance
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_apps_organization_id      ON apps(organization_id);
CREATE INDEX IF NOT EXISTS idx_app_schemas_app_id        ON app_schemas(app_id);
CREATE INDEX IF NOT EXISTS idx_app_records_app_id        ON app_records(app_id);
CREATE INDEX IF NOT EXISTS idx_execution_logs_app_id     ON execution_logs(app_id);
CREATE INDEX IF NOT EXISTS idx_country_rules_country     ON country_rules(country);
CREATE INDEX IF NOT EXISTS idx_organizations_owner_id    ON organizations(owner_id);

-- =============================================================================
-- Seed: default demo organisation (used during local development)
-- =============================================================================
INSERT INTO core_users (id, email, role)
VALUES ('00000000-0000-0000-0000-000000000001', 'demo@srpos.local', 'owner')
ON CONFLICT (email) DO NOTHING;

INSERT INTO organizations (id, owner_id, name, country, industry)
VALUES (
    '00000000-0000-0000-0000-000000000010',
    '00000000-0000-0000-0000-000000000001',
    'SRP Demo Organisation',
    'MY',
    'Recruitment & Immigration'
)
ON CONFLICT DO NOTHING;
