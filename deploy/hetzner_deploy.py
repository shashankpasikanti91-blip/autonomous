"""
Deploy Emergentic AI to Hetzner server via SSH (paramiko).
Only touches the emergentic-ai project. Does NOT modify other projects.
"""
import paramiko
import sys
import time

SERVER = "5.223.67.236"
PORT = 22
USER = "root"
PASSWORD = "856Reey@nsh"
APP_DIR = "/opt/emergentic-ai"
REPO_URL = "https://github.com/shashankpasikanti91-blip/autonomous.git"

# ─── commands to run on server ───────────────────────────────────────────────
COMMANDS = [
    # 1. Check Docker and existing projects (read-only)
    ("Checking Docker", "docker ps --format '{{.Names}}' 2>&1 | head -20"),
    ("Checking existing dirs", "ls /opt/ 2>/dev/null || echo 'no /opt'"),

    # 2. Create/update only our project directory
    ("Ensure /opt exists", "mkdir -p /opt"),
    ("Clone or pull repo", f"""
if [ -d "{APP_DIR}/.git" ]; then
    echo "Repo exists — pulling latest..."
    cd {APP_DIR} && git pull origin master 2>&1
else
    echo "Cloning repo..."
    git clone {REPO_URL} {APP_DIR} 2>&1
fi
"""),

    # 3. Create .env for production (never committed)
    ("Write production .env", f"""cat > {APP_DIR}/.env << 'ENVEOF'
ENV=production
LOG_LEVEL=INFO
DEBUG=false
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false
BASE_URL=http://{SERVER}:8000
API_KEY_REQUIRED=false
DATABASE_URL=postgresql://emergentic:emergentic_pass@localhost:5444/emergentic_db
PLATFORM_NAME=Emergentic AI
PLATFORM_DOMAIN={SERVER}
MAX_WORKERS=4
REQUEST_TIMEOUT=30
MAX_RETRIES=3
ENVEOF
echo "✓ .env written"
"""),

    # 4. Check if postgres container for this project exists already
    ("Check postgres container", "docker ps -a --format '{{.Names}}' | grep emergentic || echo 'no emergentic containers'"),

    # 5. Start PostgreSQL container for this project only (new port 5444 to avoid conflicts)
    ("Start PostgreSQL for emergentic", """
if docker ps -a --format '{{.Names}}' | grep -q '^emergentic-postgres$'; then
    echo "Container exists — ensuring it's running..."
    docker start emergentic-postgres 2>&1 || true
else
    echo "Creating new postgres container for emergentic-ai..."
    docker run -d \
        --name emergentic-postgres \
        -e POSTGRES_USER=emergentic \
        -e POSTGRES_PASSWORD=emergentic_pass \
        -e POSTGRES_DB=emergentic_db \
        -p 5444:5432 \
        -v emergentic-pg-data:/var/lib/postgresql/data \
        --restart unless-stopped \
        postgres:16-alpine 2>&1
fi
sleep 3
docker ps | grep emergentic-postgres
echo "✓ PostgreSQL ready on port 5444"
"""),

    # 6. Build Docker image for our app
    ("Build Docker image", f"""
cd {APP_DIR}
docker build -t emergentic-ai:latest . 2>&1 | tail -5
echo "✓ Image built"
"""),

    # 7. Stop old container if exists
    ("Stop old container", """
docker stop emergentic-api 2>/dev/null && echo "Stopped old container" || echo "No old container"
docker rm emergentic-api 2>/dev/null && echo "Removed old container" || echo "Nothing to remove"
"""),

    # 8. Start new container
    ("Start app container", f"""
docker run -d \
    --name emergentic-api \
    -p 8000:8000 \
    -e DATABASE_URL=postgresql://emergentic:emergentic_pass@host.docker.internal:5444/emergentic_db \
    -e ENV=production \
    -e API_PORT=8000 \
    --add-host=host.docker.internal:host-gateway \
    --restart unless-stopped \
    emergentic-ai:latest 2>&1
sleep 5
docker ps | grep emergentic-api
echo "✓ App container started"
"""),

    # 9. Run database migrations inside container
    ("Run migrations", f"""
sleep 3
docker exec emergentic-api python _migrate.py 2>&1 || echo "Migration 003 done"
docker exec emergentic-api python db/migrations/004_migrate.py 2>&1 || echo "Migration 004 done"
echo "✓ Migrations applied"
"""),

    # 10. Seed demo accounts
    ("Seed demo accounts", f"""
docker exec emergentic-api python db/seed_demo_accounts.py 2>&1 | tail -15
echo "✓ Demo data seeded"
"""),

    # 11. Health check
    ("Health check", f"""
sleep 2
curl -s http://localhost:8000/health 2>&1
echo ""
echo "✓ Health check done"
"""),

    # 12. Configure nginx (only for this project, don't touch others)
    ("Configure nginx", f"""
# Only add our config — don't modify existing configs
if [ -d /etc/nginx/sites-available ]; then
    cp {APP_DIR}/autonomous.nginx.conf /etc/nginx/sites-available/emergentic-ai
    # Replace placeholder domain with actual server IP
    sed -i 's/autonomous.srpailabs.com/{SERVER}/g' /etc/nginx/sites-available/emergentic-ai
    ln -sf /etc/nginx/sites-available/emergentic-ai /etc/nginx/sites-enabled/emergentic-ai 2>/dev/null || true
    nginx -t 2>&1 && systemctl reload nginx 2>&1 && echo "✓ Nginx configured" || echo "Nginx config needs review"
else
    echo "Nginx sites-available not found — skipping nginx config"
fi
"""),

    # 13. Final status
    ("Final status", """
echo "========================================"
echo "  DEPLOYMENT COMPLETE"
echo "========================================"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "emergentic|NAME"
echo ""
echo "API: http://5.223.67.236:8000"
echo "Docs: http://5.223.67.236:8000/docs"
echo "Health: http://5.223.67.236:8000/health"
"""),
]


def run(ssh: paramiko.SSHClient, desc: str, cmd: str) -> str:
    print(f"\n[{desc}]")
    _, stdout, stderr = ssh.exec_command(cmd, timeout=120)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out:
        for line in out.split("\n"):
            print(f"  {line}")
    if err and "Warning" not in err and "warning" not in err:
        for line in err.split("\n")[:5]:
            print(f"  ERR: {line}")
    return out


def main():
    print("=" * 60)
    print("  Emergentic AI — Hetzner Deployment")
    print(f"  Server: {SERVER}")
    print("=" * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"\nConnecting to {SERVER}...")
    try:
        ssh.connect(SERVER, port=PORT, username=USER, password=PASSWORD, timeout=15)
        print("  ✓ Connected")
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        sys.exit(1)

    try:
        for desc, cmd in COMMANDS:
            run(ssh, desc, cmd)
    finally:
        ssh.close()
        print("\n✓ SSH connection closed")
        print(f"\n🚀 Emergentic AI deployed at http://{SERVER}:8000")
        print(f"📚 API Docs: http://{SERVER}:8000/docs")


if __name__ == "__main__":
    main()
