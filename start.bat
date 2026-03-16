@echo off
REM ============================================================================
REM EMERGENTIC AI — ONE-CLICK LOCAL START
REM ============================================================================
REM Installs deps, seeds demo data, runs tests, starts backend + frontend
REM ============================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ================================================================
echo   EMERGENTIC AI — Starting Local Development
echo ================================================================
echo.

REM ── Step 1: Check Python ─────────────────────────────────────────
echo [1/7] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Python not found. Install from https://python.org
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo   %%i
echo.

REM ── Step 2: Install Python dependencies ──────────────────────────
echo [2/7] Installing Python dependencies...
python -m pip install -r requirements.txt --quiet 2>nul
if errorlevel 1 (
    echo   WARNING: Some packages may have failed to install
) else (
    echo   OK - Dependencies installed
)
echo.

REM ── Step 3: Check PostgreSQL ────────────────────────────────────
echo [3/7] Checking PostgreSQL...
python -c "from sqlalchemy import create_engine, text; e=create_engine('postgresql://postgres:postgres@localhost:5432/srp_os'); c=e.connect(); c.execute(text('SELECT 1')); c.close(); print('  OK - PostgreSQL connected')" 2>nul
if errorlevel 1 (
    echo   WARNING: PostgreSQL not reachable at localhost:5432
    echo   Trying Docker...
    docker-compose up -d postgres 2>nul
    if errorlevel 1 (
        echo   NOTE: Database unavailable. App will start in mock mode.
    ) else (
        echo   OK - PostgreSQL started via Docker
        timeout /t 5 /nobreak >nul
    )
)
echo.

REM ── Step 4: Initialize database tables ──────────────────────────
echo [4/7] Initializing database...
python -c "import sys; sys.path.insert(0,'app'); from db.database import init_db; init_db(); print('  OK - Tables created')" 2>nul
if errorlevel 1 (
    echo   SKIP - Database init skipped (will retry on startup)
)
echo.

REM ── Step 5: Seed demo accounts ──────────────────────────────────
echo [5/7] Seeding demo accounts...
python db\seed_demo_accounts.py 2>nul
if errorlevel 1 (
    echo   SKIP - Seeding skipped (database may not be available)
)
echo.

REM ── Step 6: Run tests ────────────────────────────────────────────
echo [6/7] Running tests...
python -m pytest tests\ -v --tb=short -q 2>nul
if errorlevel 1 (
    echo   NOTE: Some tests may have failed (check output above)
) else (
    echo   OK - All tests passed
)
echo.

REM ── Step 7: Start backend ────────────────────────────────────────
echo [7/7] Starting backend server...
echo.
echo ================================================================
echo   Backend: http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo   Health: http://localhost:8000/health
echo ================================================================
echo.
echo   Demo accounts:
echo     admin@demo.com    (admin)
echo     owner@demo.com    (owner)
echo     hr@demo.com       (manager)
echo     finance@demo.com  (manager)
echo     sales@demo.com    (user)
echo.
echo   Press Ctrl+C to stop the server
echo ================================================================
echo.

python main.py

pause
endlocal
