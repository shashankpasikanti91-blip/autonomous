"""Fix DB networking, run migrations, seed, configure nginx."""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("5.223.67.236", username="root", password="856Reey@nsh", timeout=15)

def run(desc, cmd, timeout=30):
    print(f"\n[{desc}]")
    _, out, err = ssh.exec_command(cmd, timeout=timeout)
    out.channel.settimeout(timeout)
    try:
        o = out.read().decode().strip()
    except Exception:
        o = "(timeout - command still running)"
    try:
        e = err.read().decode().strip()
    except Exception:
        e = ""
    for line in o.split("\n"):
        if line: print(f"  {line}")
    if e:
        for line in e.split("\n")[:2]:
            if line and "Warning" not in line: print(f"  ERR: {line}")
    return o

# Get the emergentic-postgres container IP
pg_ip = run("Get postgres IP", "docker inspect emergentic-postgres --format '{{.NetworkSettings.IPAddress}}'")
pg_ip = pg_ip.strip()
print(f"  -> Postgres IP: {pg_ip}")

# Recreate app container with correct DB URL using container IP
run("Stop old app container", "docker stop emergentic-api && docker rm emergentic-api")

run("Start app with correct DB URL", f"""
docker run -d \
    --name emergentic-api \
    -p 8010:8000 \
    -e DATABASE_URL=postgresql://emergentic:emergentic_pass@{pg_ip}:5432/emergentic_db \
    -e ENV=production \
    -e API_PORT=8000 \
    --restart unless-stopped \
    emergentic-ai:latest 2>&1
""")

run("Wait 15s for startup", "sleep 15 && docker ps | grep emergentic-api")
run("App logs", "docker logs emergentic-api --tail 10 2>&1")
run("Health check", "curl -s http://localhost:8010/health")

# Run migrations (each separately to avoid timeout)
run("Migration 003", f"docker exec emergentic-api python _migrate.py 2>&1", timeout=30)
run("Migration 004", f"docker exec emergentic-api python db/migrations/004_migrate.py 2>&1", timeout=30)

# Seed in background
run("Start seed in background", "docker exec -d emergentic-api python db/seed_demo_accounts.py")
run("Wait for seed", "sleep 10 && echo done")
run("Check seed logs", "docker logs emergentic-api --tail 5 2>&1")

# Nginx - use a non-SSL server block on port 8080 to avoid SSL conflicts
run("Write nginx config", """
cat > /etc/nginx/sites-available/emergentic-ai << 'EOF'
server {
    listen 8080;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120;
    }
}
EOF
echo "nginx config written"
""")

run("Enable nginx site", """
ln -sf /etc/nginx/sites-available/emergentic-ai /etc/nginx/sites-enabled/emergentic-ai
nginx -t 2>&1 | head -3
systemctl reload nginx 2>&1 | head -3 || nginx -s reload 2>&1 | head -3
echo "nginx reloaded"
""")

run("Final health checks", """
echo "=== EMERGENTIC AI ON HETZNER ==="
curl -s http://localhost:8010/health
echo ""
curl -s http://localhost:8080/health
echo ""
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E "emergentic|NAMES"
echo ""
echo "URLs:"
echo "  http://5.223.67.236:8010       (direct)"
echo "  http://5.223.67.236:8010/docs  (API docs)"
echo "  http://5.223.67.236:8080       (via nginx)"
""")

ssh.close()
print("\n✅ Deployment finalized!")
