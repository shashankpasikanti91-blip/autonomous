"""Apply migration 003 – add modules, app_type, architecture_summary, blueprint to apps table."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import psycopg2

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/srp_os")

STMTS = [
    "ALTER TABLE apps ADD COLUMN IF NOT EXISTS modules JSONB DEFAULT NULL",
    "ALTER TABLE apps ADD COLUMN IF NOT EXISTS app_type TEXT DEFAULT NULL",
    "ALTER TABLE apps ADD COLUMN IF NOT EXISTS architecture_summary TEXT DEFAULT NULL",
    "ALTER TABLE apps ADD COLUMN IF NOT EXISTS blueprint JSONB DEFAULT NULL",
]

try:
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()
    for stmt in STMTS:
        cur.execute(stmt)
        col = stmt.split("EXISTS")[1].strip().split()[0]
        print(f"  [OK] Added column '{col}' (or already existed)")
    conn.close()
    print("\nMigration 003 applied successfully.")
except psycopg2.OperationalError as e:
    print(f"  [ERR] Cannot connect to database: {e}")
    sys.exit(1)
except Exception as e:
    print(f"  [ERR] {e}")
    sys.exit(1)
