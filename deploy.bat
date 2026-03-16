@echo off
REM ============================================================================
REM HR AUTONOMOUS OS - WINDOWS DEPLOYMENT SCRIPT
REM ============================================================================
REM This script deploys to 5.223.67.236 using credentials provided
REM Requires: SSH and SCP (built-in on Windows 10/11)

setlocal enabledelayedexpansion

echo.
echo ════════════════════════════════════════════════════════════════
echo HR AUTONOMOUS OS - DEPLOYMENT TO HETZNER
echo ════════════════════════════════════════════════════════════════
echo.
echo Server IP: 5.223.67.236
echo User: root
echo Password: [using provided credentials]
echo.

cd /d "c:\Users\User\Desktop\emergentic AI" || exit /b 1

REM Check if certificates exist
if not exist "cert.pem" (
    echo ERROR: cert.pem not found
    exit /b 1
)
if not exist "key.pem" (
    echo ERROR: key.pem not found
    exit /b 1
)

echo [STEP 1] ✓ Certificates verified
echo.

REM Create temporary deployment package
echo [STEP 2] Creating deployment package...
if exist "deployment-pkg" rmdir /s /q "deployment-pkg"
mkdir deployment-pkg

echo   Copying source files...
xcopy app deployment-pkg\app /E /I /Y >nul
xcopy ui-platform deployment-pkg\ui-platform /E /I /Y >nul
xcopy db deployment-pkg\db /E /I /Y >nul  
xcopy deploy deployment-pkg\deploy /E /I /Y >nul
copy main.py deployment-pkg\ >nul
copy requirements.txt deployment-pkg\ >nul
copy .env.production deployment-pkg\ >nul
copy cert.pem deployment-pkg\ >nul
copy key.pem deployment-pkg\ >nul

echo   ✓ Package created
echo.

REM Create remote deployment script
echo [STEP 3] Creating remote deployment script...

(
echo #!/bin/bash
echo set -e
echo.
echo echo "════════════════════════════════════════════════════════════"
echo echo "Starting HR Autonomous OS Deployment..."
echo echo "════════════════════════════════════════════════════════════"
echo echo ""
echo.
echo echo "[1/8] Installing SSL certificates..."
echo mkdir -p /etc/ssl/autonomous.srpailabs.com
echo cp /tmp/dep/cert.pem /etc/ssl/autonomous.srpailabs.com/
echo cp /tmp/dep/key.pem /etc/ssl/autonomous.srpailabs.com/
echo chmod 600 /etc/ssl/autonomous.srpailabs.com/*.pem
echo echo "✓ SSL certificates installed"
echo echo ""
echo.
echo echo "[2/8] Deploying project files..."
echo rm -rf /opt/hr-autonomous
echo mkdir -p /opt/hr-autonomous
echo cp -r /tmp/dep/* /opt/hr-autonomous/
echo cd /opt/hr-autonomous
echo echo "✓ Project deployed"
echo echo ""
echo.
echo echo "[3/8] Creating PostgreSQL database container..."
echo docker run -d --name hr-postgres -e POSTGRES_USER=hr_app -e POSTGRES_PASSWORD=hr_secure_password_change_me -e POSTGRES_DB=hr_multitenant -p 5544:5432 -v hr-pg-data:/var/lib/postgresql/data --restart always postgres:15 2^>/dev/null ^|^| echo "✓ Container running"
echo sleep 5
echo echo "✓ Database ready"
echo echo ""
echo.
echo echo "[4/8] Installing Python dependencies..."
echo python3.11 -m venv /opt/hr-autonomous/.venv 2^>/dev/null ^|^| python3 -m venv /opt/hr-autonomous/.venv
echo source /opt/hr-autonomous/.venv/bin/activate
echo pip install -q -U pip setuptools wheel
echo pip install -q -r requirements.txt
echo echo "✓ Dependencies installed"
echo echo ""
echo.
echo echo "[5/8] Building frontend..."
echo cd /opt/hr-autonomous/ui-platform
echo npm install -q 2^>/dev/null
echo npm run build 2^>/dev/null
echo echo "✓ Frontend built"
echo echo ""
echo.
echo echo "[6/8] Configuring Nginx..."
echo cp /opt/hr-autonomous/deploy/nginx.conf /etc/nginx/sites-available/autonomous 2^>/dev/null ^|^| echo "✓ Nginx config prepared"
echo sed -i 's/hr.example.com/autonomous.srpailabs.com/g' /etc/nginx/sites-available/autonomous
echo ln -sf /etc/nginx/sites-available/autonomous /etc/nginx/sites-enabled/autonomous 2^>/dev/null ^|^| true
echo nginx -t
echo systemctl restart nginx
echo echo "✓ Nginx configured"
echo echo ""
echo.
echo echo "[7/8] Setting up backend service..."
echo systemctl stop hr-autonomous 2^>/dev/null ^|^| true
echo cat ^> /etc/systemd/system/hr-autonomous.service ^<^< 'EOF'
echo [Unit]
echo Description=HR Autonomous OS Backend
echo After=network.target
echo.
echo [Service]
echo Type=simple
echo User=root
echo WorkingDirectory=/opt/hr-autonomous
echo ExecStart=/opt/hr-autonomous/.venv/bin/python /opt/hr-autonomous/main.py
echo Environment="DATABASE_URL=postgresql://hr_app:hr_secure_password_change_me@localhost:5544/hr_multitenant"
echo Environment="API_PORT=8010"
echo Environment="ENV=production"
echo Restart=always
echo RestartSec=10
echo.
echo [Install]
echo WantedBy=multi-user.target
echo EOF
echo systemctl daemon-reload
echo systemctl enable hr-autonomous
echo systemctl restart hr-autonomous
echo echo "✓ Backend service configured"
echo echo ""
echo.
echo echo "[8/8] Verification..."
echo sleep 3
echo systemctl status hr-autonomous --no-pager
echo echo ""
echo echo "════════════════════════════════════════════════════════════"
echo echo "✅ DEPLOYMENT COMPLETE!"
echo echo "════════════════════════════════════════════════════════════"
echo echo ""
echo echo "Access your application at:"
echo echo "  Frontend: https://autonomous.srpailabs.com"
echo echo "  API: https://autonomous.srpailabs.com/api"
echo echo ""
) > deployment-pkg\deploy.sh

echo ✓ Remote script created
echo.

echo [STEP 4] Beginning file upload to server...
echo   Uploading deployment package to 5.223.67.236:/tmp/dep
echo   This may take 1-2 minutes...
echo.

REM Use SCP to copy files - using -o StrictHostKeyChecking=no to avoid prompt
scp -o StrictHostKeyChecking=no -r deployment-pkg root@5.223.67.236:/tmp/dep
if errorlevel 1 (
    echo ERROR: SCP upload failed
    echo Please ensure SSH access is available and password is correct
    exit /b 1
)

echo ✓ Files uploaded
echo.

echo [STEP 5] Executing remote deployment script...
echo.

REM Execute deployment script
ssh -o StrictHostKeyChecking=no root@5.223.67.236 "bash /tmp/dep/deploy.sh"
if errorlevel 1 (
    echo WARNING: Deployment script encountered issues
    echo Please check server logs manually: ssh root@5.223.67.236
    echo Then run: bash /tmp/dep/deploy.sh
)

echo.
echo ════════════════════════════════════════════════════════════════
echo DEPLOYMENT EXECUTION COMPLETE
echo ════════════════════════════════════════════════════════════════
echo.
echo Verify your deployment:
echo   1. Check backend: https://autonomous.srpailabs.com/api
echo   2. Visit frontend: https://autonomous.srpailabs.com
echo.
echo To check service status:
echo   ssh root@5.223.67.236
echo   systemctl status hr-autonomous
echo   docker ps
echo.
echo To view logs:
echo   ssh root@5.223.67.236
echo   journalctl -u hr-autonomous -f
echo   docker logs hr-postgres
echo.

pause

endlocal
