@echo off
REM ============================================================================
REM EMERGENTIC AI — Run All Tests
REM ============================================================================
cd /d "%~dp0"

echo.
echo ================================================================
echo   EMERGENTIC AI — Test Suite
echo ================================================================
echo.

python -m pip install pytest httpx --quiet 2>nul

echo Running tests...
echo.
python -m pytest tests\ -v --tb=short
echo.

pause
