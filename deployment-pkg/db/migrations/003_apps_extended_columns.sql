-- =============================================================================
-- Migration 003: Extend apps table with template and architecture columns
--
-- Adds three new columns to apps.  All use ADD COLUMN IF NOT EXISTS so this
-- script is safe to run multiple times and will not fail if a column was
-- already added by a previous migration (e.g. modules via 002).
--
-- No existing columns are removed or altered.
-- =============================================================================

-- modules: JSON array of module names populated when a business template is
--          applied (payroll, invoice, crm, etc.).  NULL if no template used.
ALTER TABLE apps
    ADD COLUMN IF NOT EXISTS modules JSONB DEFAULT NULL;

-- app_type: short label identifying the kind of app
--           e.g. 'payroll' | 'invoice' | 'crm' | 'custom'
ALTER TABLE apps
    ADD COLUMN IF NOT EXISTS app_type TEXT DEFAULT NULL;

-- architecture_summary: free-text or AI-generated description of how the app
--                       is structured (tables, modules, integrations).
ALTER TABLE apps
    ADD COLUMN IF NOT EXISTS architecture_summary TEXT DEFAULT NULL;

-- Optional: add comments for documentation inside Postgres
COMMENT ON COLUMN apps.modules IS
    'JSON array of module names; populated automatically when a business template is detected.';

COMMENT ON COLUMN apps.app_type IS
    'Short label for the application category, e.g. payroll, invoice, crm, custom.';

COMMENT ON COLUMN apps.architecture_summary IS
    'Human-readable or AI-generated description of the application architecture.';
