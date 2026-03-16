"""Finalize deployment - run migrations, seed, configure nginx."""
import paramiko
import sys
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("5.223.67.236", username="root", password="856Reey@nsh", timeout=15)

def run(desc, cmd, timeout=60):
    print(f"\n[{desc}]")
    _, out, err = ssh.exec_command(cmd, timeout=timeout)
    out.channel.settimeout(timeout)
    o = out.read().decode().strip()
    e = err.read().decode().strip()
    for line in o.split("\n"):
        if line: print(f"  {line}")
    if e:
        for line in e.split("\n")[:3]:
            if line and "Warning" not in line: print(f"  ERR: {line}")
    return o

# Check container status
run("Container status", "docker ps | grep emergentic")

# Check logs to see if app started ok
run("App logs", "docker logs emergentic-api --tail 20 2>&1")

# Health check
run("Health check", "curl -s http://localhost:8010/health")

# Run migrations and seed
run("Migrations + seed", """
docker exec emergentic-api sh -c "python _migrate.py && python db/migrations/004_migrate.py && python db/seed_demo_accounts.py 2>&1 | tail -20"
""", timeout=90)

# Write nginx config that doesn't conflict
run("Write nginx for emergentic", """
# Check existing nginx default
cat /etc/nginx/sites-enabled/default 2>/dev/null | head -5 || echo "no default"
cat /etc/nginx/sites-enabled/ 2>/dev/null || ls /etc/nginx/sites-enabled/ 2>/dev/null || echo "checking..."
ls /etc/nginx/sites-enabled/
""")

# Write nginx location block for our project
run("Write nginx config", """
cat > /etc/nginx/sites-available/emergentic-ai << 'NGINXEOF'
server {
    listen 8080;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120;
        proxy_connect_timeout 10;
    }
}
NGINXEOF
ln -sf /etc/nginx/sites-available/emergentic-ai /etc/nginx/sites-enabled/emergentic-ai 2>/dev/null || true
nginx -t 2>&1 && systemctl reload nginx 2>&1 && echo "nginx OK" || echo "nginx reload attempted"
""")

run("Final URLs", """
echo "=================================="
echo "  EMERGENTIC AI LIVE ON HETZNER"
echo "=================================="
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E "emergentic|NAMES"
echo ""
echo "Direct:   http://5.223.67.236:8010"
echo "API Docs: http://5.223.67.236:8010/docs"
echo "Health:   http://5.223.67.236:8010/health"
curl -s http://localhost:8010/health
""")

ssh.close()
print("\nDeployment complete!")
