"""Apply migration 004 – add slug and custom_domain to organizations."""
import sys, os
import psycopg2

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/srp_os")

STMTS = [
    "ALTER TABLE organizations ADD COLUMN IF NOT EXISTS slug TEXT UNIQUE",
    "ALTER TABLE organizations ADD COLUMN IF NOT EXISTS custom_domain TEXT UNIQUE",
]
BACKFILL = "UPDATE organizations SET slug = lower(replace(name, ' ', '-')) || '-tenant' WHERE slug IS NULL"

try:
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()
    for stmt in STMTS:
        cur.execute(stmt)
        col = stmt.split("EXISTS")[1].strip().split()[0]
        print(f"  [OK] Added column '{col}' (or already existed)")
    cur.execute(BACKFILL)
    print("  [OK] Slugs backfilled")
    conn.close()
    print("\nMigration 004 applied successfully.")
except Exception as e:
    print(f"  [ERR] {e}")
    sys.exit(1)
