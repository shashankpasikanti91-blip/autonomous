-- Migration 002: Add modules column to apps table
-- Stores the list of module names applied from a business template.
-- JSONB allows flexible storage; NULL means no template was applied.

ALTER TABLE apps
    ADD COLUMN IF NOT EXISTS modules JSONB DEFAULT NULL;

COMMENT ON COLUMN apps.modules IS
    'Module list automatically populated when a business template (payroll, invoice, crm) is detected from the user prompt.';
