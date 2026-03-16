#!/bin/bash
# HR AUTONOMOUS OS - E2E DEPLOYMENT TEST
# Tests all components and verifies successful deployment

echo "════════════════════════════════════════════════════════════"
echo "HR AUTONOMOUS OS - E2E DEPLOYMENT VERIFICATION"
echo "════════════════════════════════════════════════════════════"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASSED=0
FAILED=0

# Test 1: Check SSL certificates
echo "[TEST 1] SSL Certificates"
if [ -f "/etc/ssl/autonomous.srpailabs.com/cert.pem" ] && [ -f "/etc/ssl/autonomous.srpailabs.com/key.pem" ]; then
    echo -e "${GREEN}✓ PASS${NC} SSL certificates installed"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} SSL certificates NOT found"
    ((FAILED++))
fi
echo ""

# Test 2: Check PostgreSQL Container
echo "[TEST 2] PostgreSQL Database"
if docker ps | grep -q "hr-postgres"; then
    echo -e "${GREEN}✓ PASS${NC} PostgreSQL container running"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} PostgreSQL container NOT running"
    ((FAILED++))
fi
echo ""

# Test 3: Check Database Connection
echo "[TEST 3] Database Connectivity"
export PGPASSWORD="hr_secure_password_change_me"
if psql -h 127.0.0.1 -p 5544 -U hr_app -d hr_multitenant -c "SELECT 1" &>/dev/null; then
    echo -e "${GREEN}✓ PASS${NC} Database accessible"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} Database connection failed"
    ((FAILED++))
fi
unset PGPASSWORD
echo ""

# Test 4: Check Backend Service
echo "[TEST 4] Backend Service"
if systemctl is-active --quiet hr-autonomous; then
    echo -e "${GREEN}✓ PASS${NC} Backend service running"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} Backend service NOT running"
    attempt_restart=1
    ((FAILED++))
fi
echo ""

# Test 5: Check Backend API Port
echo "[TEST 5] Backend API Port (8010)"
if netstat -tuln 2>/dev/null | grep -q ":8010" || ss -tuln 2>/dev/null | grep -q ":8010"; then
    echo -e "${GREEN}✓ PASS${NC} Backend API listening on port 8010"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ WARNING${NC} Port 8010 not yet listening (service may be starting)"
    ((FAILED++))
fi
echo ""

# Test 6: Check Nginx
echo "[TEST 6] Nginx Web Server"
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ PASS${NC} Nginx running"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} Nginx NOT running"
    ((FAILED++))
fi
echo ""

# Test 7: Check Frontend Build
echo "[TEST 7] Frontend Build"
if [ -f "/opt/hr-autonomous/ui-platform/dist/index.html" ]; then
    echo -e "${GREEN}✓ PASS${NC} Frontend build exists"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} Frontend NOT built"
    ((FAILED++))
fi
echo ""

# Test 8: Check Project Files
echo "[TEST 8] Project Deployment"
if [ -d "/opt/hr-autonomous/app" ] && [ -f "/opt/hr-autonomous/main.py" ]; then
    echo -e "${GREEN}✓ PASS${NC} Project files deployed"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} Project files NOT deployed"
    ((FAILED++))
fi
echo ""

# Test 9: Virtual Environment
echo "[TEST 9] Python Virtual Environment"
if [ -d "/opt/hr-autonomous/.venv" ]; then
    echo -e "${GREEN}✓ PASS${NC} Virtual environment configured"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} Virtual environment missing"
    ((FAILED++))
fi
echo ""

# Test 10: Nginx Configuration
echo "[TEST 10] Nginx Configuration"
if nginx -t 2>&1 | grep -q "successful"; then
    echo -e "${GREEN}✓ PASS${NC} Nginx config valid"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ WARNING${NC} Nginx config needs review"
    ((FAILED++))
fi
echo ""

# Summary
echo "════════════════════════════════════════════════════════════"
echo "TEST SUMMARY"
echo "════════════════════════════════════════════════════════════"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED - Deployment Successful!${NC}"
    echo ""
    echo "Your application is ready at:"
    echo "  Frontend: https://autonomous.srpailabs.com"
    echo "  API: https://autonomous.srpailabs.com/api"
    echo ""
    exit 0
else
    echo -e "${YELLOW}⚠️  Some tests failed - Review issues above${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  • Backend logs: journalctl -u hr-autonomous -f"
    echo "  • Nginx logs: tail -f /var/log/nginx/error.log"
    echo "  • Database logs: docker logs hr-postgres"
    echo ""
    exit 1
fi
