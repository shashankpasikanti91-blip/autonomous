#!/bin/bash
# ============================================================================
# HR Autonomous OS - Database Migration Runner
# ============================================================================
# Purpose: Apply all migrations to isolated HR PostgreSQL instance
# Database: hr_multitenant on localhost:5544
# ===========================================================================

set -e

# Configuration
export DB_HOST="${1:-localhost}"
export DB_PORT="${2:-5544}"
export DB_USER="${3:-hr_app}"
export DB_PASSWORD="${4:-hr_secure_password_change_me}"
export DB_NAME="${5:-hr_multitenant}"

export PGPASSWORD="${DB_PASSWORD}"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MIGRATIONS_DIR="${SCRIPT_DIR}/../db/migrations"

echo "============================================================================"
echo "HR AUTONOMOUS OS - DATABASE MIGRATIONS"
echo "============================================================================"
echo ""
echo "Target Database:"
echo "  Host: ${DB_HOST}"
echo "  Port: ${DB_PORT}"
echo "  Database: ${DB_NAME}"
echo "  User: ${DB_USER}"
echo ""

# Test connection
echo "Testing database connection..."
if psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c "SELECT 1;" &> /dev/null; then
    echo "✓ Database connection successful"
else
    echo "✗ ERROR: Cannot connect to database"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Ensure PostgreSQL container is running: docker ps | grep hr-postgres"
    echo "  2. Verify connection settings are correct"
    echo "  3. Check database logs: docker logs hr-postgres"
    exit 1
fi

echo ""
echo "Applying migrations..."
echo ""

# Apply each migration
MIGRATIONS=(
    "001_init.sql"
    "002_add_modules_column.sql"
    "003_apps_extended_columns.sql"
    "004_add_org_slug_domain.sql"
)

for migration in "${MIGRATIONS[@]}"; do
    MIGRATION_FILE="${MIGRATIONS_DIR}/${migration}"
    
    if [ ! -f "${MIGRATION_FILE}" ]; then
        echo "✗ ERROR: Migration file not found: ${MIGRATION_FILE}"
        exit 1
    fi
    
    echo "Applying: ${migration}..."
    psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -f "${MIGRATION_FILE}" > /dev/null
    echo "  ✓ ${migration} applied"
done

echo ""
echo "============================================================================"
echo "✓ ALL MIGRATIONS APPLIED SUCCESSFULLY"
echo "============================================================================"
echo ""

# Verify schema
echo "Verifying schema..."
echo ""

psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" <<EOF
-- Check organizations table
\echo "Organizations table:"
\d+ organizations

-- Check for slug and custom_domain columns
\echo ""
\echo "Key columns:"
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'organizations' 
  AND column_name IN ('slug', 'custom_domain');
EOF

echo ""
echo "✓ Database is ready for deployment!"
echo ""
