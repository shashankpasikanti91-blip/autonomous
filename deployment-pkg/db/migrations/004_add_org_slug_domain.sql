-- =============================================================================
-- Migration 004: Add organization slug and custom domain bindings
-- ----------------------------------------------------------------------------
-- Adds tenant-friendly identifiers to organizations so hosts/subdomains can be
-- resolved safely without sharing with other projects.
-- =============================================================================

-- Slug: short, URL-safe tenant identifier used for subdomains
ALTER TABLE organizations
    ADD COLUMN IF NOT EXISTS slug TEXT UNIQUE;

-- Custom domain: optional full host (e.g., hr.acme.com) per tenant
ALTER TABLE organizations
    ADD COLUMN IF NOT EXISTS custom_domain TEXT UNIQUE;

-- Backfill existing rows with deterministic slug if missing
UPDATE organizations
SET slug = COALESCE(slug, lower(replace(name, ' ', '-'))) || '-tenant'
WHERE slug IS NULL;

-- Ensure slug is NOT NULL after backfill
ALTER TABLE organizations
    ALTER COLUMN slug SET NOT NULL;

-- Indexes for fast lookup
CREATE INDEX IF NOT EXISTS idx_organizations_slug ON organizations(slug);
CREATE INDEX IF NOT EXISTS idx_organizations_custom_domain ON organizations(custom_domain);
