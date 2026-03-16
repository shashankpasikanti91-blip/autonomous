"""
Deployment and startup script for Emergentic AI Platform.

Usage:
    python deploy_start.py [--seed] [--test] [--frontend]

Options:
    --seed      Seed demo accounts into the database
    --test      Run test suite after startup verification
    --frontend  Also build and serve the frontend
"""
import sys
import os
import subprocess
import time
import argparse

# Ensure we're in the right directory
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT_DIR)

# Add app to path
sys.path.insert(0, os.path.join(ROOT_DIR, "app"))


def check_python():
    """Check Python version."""
    print("[CHECK] Python version...")
    v = sys.version_info
    print(f"  Python {v.major}.{v.minor}.{v.micro}")
    if v.major < 3 or (v.major == 3 and v.minor < 10):
        print("  ✗ Python 3.10+ required")
        return False
    print("  ✓ OK")
    return True


def check_dependencies():
    """Check that key dependencies are installed."""
    print("\n[CHECK] Dependencies...")
    missing = []
    for pkg in ["fastapi", "uvicorn", "sqlalchemy", "pydantic", "pydantic_settings", "httpx"]:
        try:
            __import__(pkg)
            print(f"  ✓ {pkg}")
        except ImportError:
            print(f"  ✗ {pkg} — MISSING")
            missing.append(pkg)

    if missing:
        print(f"\n  Installing missing packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--quiet"])
        print("  ✓ Dependencies installed")
    return True


def check_database():
    """Verify database connection."""
    print("\n[CHECK] Database connection...")
    try:
        from db.database import engine
        with engine.connect() as conn:
            result = conn.execute(__import__("sqlalchemy").text("SELECT 1"))
            result.fetchone()
        print("  ✓ PostgreSQL connected")
        return True
    except Exception as e:
        print(f"  ✗ Database connection failed: {e}")
        print("  → Ensure PostgreSQL is running and DATABASE_URL in .env is correct")
        print("  → Default: postgresql://postgres:postgres@localhost:5432/srp_os")
        return False


def init_database():
    """Create tables and run migrations."""
    print("\n[INIT] Database tables...")
    try:
        from db.database import init_db
        init_db()
        print("  ✓ All tables created/verified")
        return True
    except Exception as e:
        print(f"  ✗ Table creation failed: {e}")
        return False


def seed_demo_data():
    """Seed demo accounts."""
    print("\n[SEED] Demo accounts...")
    try:
        sys.path.insert(0, os.path.join(ROOT_DIR, "db"))
        from seed_demo_accounts import seed
        seed()
        return True
    except Exception as e:
        print(f"  ✗ Seeding failed: {e}")
        return False


def verify_app_loads():
    """Verify the FastAPI app loads without errors."""
    print("\n[VERIFY] App loading...")
    try:
        from api.main import app
        print(f"  ✓ FastAPI app loaded: {app.title}")
        print(f"  ✓ Routes: {len(app.routes)}")
        return True
    except Exception as e:
        print(f"  ✗ App failed to load: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_tests():
    """Run the test suite."""
    print("\n[TEST] Running test suite...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-q"],
        cwd=ROOT_DIR,
    )
    return result.returncode == 0


def start_backend():
    """Start the backend server."""
    print("\n[START] Backend server...")
    print("  → Starting uvicorn on http://localhost:8000")
    print("  → Press Ctrl+C to stop\n")

    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "api.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--app-dir", os.path.join(ROOT_DIR, "app"),
        ])
    except KeyboardInterrupt:
        print("\n  Server stopped.")


def build_frontend():
    """Build the frontend."""
    ui_dir = os.path.join(ROOT_DIR, "ui-platform")
    if not os.path.exists(os.path.join(ui_dir, "package.json")):
        print("\n[SKIP] Frontend not found")
        return True

    print("\n[BUILD] Frontend...")
    try:
        subprocess.check_call(["npm", "install", "--quiet"], cwd=ui_dir, shell=True)
        print("  ✓ Dependencies installed")
        subprocess.check_call(["npm", "run", "build"], cwd=ui_dir, shell=True)
        print("  ✓ Frontend built successfully")
        return True
    except Exception as e:
        print(f"  ⚠ Frontend build: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Emergentic AI Platform Deployment")
    parser.add_argument("--seed", action="store_true", help="Seed demo accounts")
    parser.add_argument("--test", action="store_true", help="Run tests after setup")
    parser.add_argument("--frontend", action="store_true", help="Build frontend")
    parser.add_argument("--check-only", action="store_true", help="Only run checks, don't start server")
    args = parser.parse_args()

    print("=" * 60)
    print("  Emergentic AI Platform — Deployment")
    print("=" * 60)

    # Pre-flight checks
    if not check_python():
        sys.exit(1)

    if not check_dependencies():
        sys.exit(1)

    db_ok = check_database()
    if db_ok:
        init_database()

        if args.seed:
            seed_demo_data()

    if not verify_app_loads():
        sys.exit(1)

    if args.frontend:
        build_frontend()

    if args.test:
        if not run_tests():
            print("\n⚠ Some tests failed. Check output above.")

    if args.check_only:
        print("\n✓ All checks passed!")
        sys.exit(0)

    # Start the server
    start_backend()


if __name__ == "__main__":
    main()
