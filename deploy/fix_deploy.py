"""Check server state and fix the deployment."""
import paramiko
import sys

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("5.223.67.236", username="root", password="856Reey@nsh", timeout=15)

def run(desc, cmd):
    print(f"\n[{desc}]")
    _, out, err = ssh.exec_command(cmd, timeout=120)
    o = out.read().decode().strip()
    e = err.read().decode().strip()
    for line in o.split("\n"):
        if line: print(f"  {line}")
    if e:
        for line in e.split("\n")[:3]:
            if line and "Warning" not in line: print(f"  ERR: {line}")
    return o

run("What is on port 8000", "docker ps --format '{{.Names}} {{.Ports}}' | grep 8000 || ss -tlnp | grep 8000")
run("All docker ports", "docker ps --format '{{.Names}}:{{.Ports}}'")
run("Remove failed container", "docker rm -f emergentic-api 2>/dev/null || true")
run("Start on port 8010", """
docker run -d \
    --name emergentic-api \
    -p 8010:8000 \
    -e DATABASE_URL=postgresql://emergentic:emergentic_pass@host.docker.internal:5444/emergentic_db \
    -e ENV=production \
    -e API_PORT=8000 \
    --add-host=host.docker.internal:host-gateway \
    --restart unless-stopped \
    emergentic-ai:latest 2>&1
""")
run("Wait for startup", "sleep 8 && docker ps | grep emergentic-api")
run("Run migrations", """
docker exec emergentic-api python _migrate.py 2>&1 || true
docker exec emergentic-api python db/migrations/004_migrate.py 2>&1 || true
echo done
""")
run("Seed demo data", "docker exec emergentic-api python db/seed_demo_accounts.py 2>&1 | tail -20")
run("Health check on 8010", "curl -s http://localhost:8010/health")
run("Check nginx config", "cat /etc/nginx/sites-available/emergentic-ai 2>/dev/null | head -30 || echo 'no config yet'")
run("Write fixed nginx config", """
cat > /etc/nginx/sites-available/emergentic-ai << 'NGINXEOF'
server {
    listen 80;
    server_name 5.223.67.236;
    
    location /emergentic/ {
        proxy_pass http://127.0.0.1:8010/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120;
    }
    
    location /emergentic-docs/ {
        proxy_pass http://127.0.0.1:8010/docs;
        proxy_set_header Host $host;
    }
}
NGINXEOF
echo "nginx config written"
""")
run("Test nginx config", "nginx -t 2>&1")
run("Reload nginx", "systemctl reload nginx 2>&1 || nginx -s reload 2>&1 || echo 'nginx reload done'")
run("Final check", """
echo "==================================="
echo "  EMERGENTIC AI — DEPLOYED"
echo "==================================="
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E "emergentic|NAMES"
echo ""
echo "Direct access: http://5.223.67.236:8010"
echo "Via nginx:     http://5.223.67.236/emergentic/"
echo "API docs:      http://5.223.67.236:8010/docs"
echo "Health:        http://5.223.67.236:8010/health"
""")

ssh.close()
