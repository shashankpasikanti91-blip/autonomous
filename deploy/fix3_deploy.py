"""Connect app to postgres via docker network and run migrations/seed."""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("5.223.67.236", username="root", password="856Reey@nsh", timeout=15)

def run(desc, cmd, timeout=45):
    print(f"\n[{desc}]")
    _, out, err = ssh.exec_command(cmd, timeout=timeout)
    out.channel.settimeout(timeout)
    try: o = out.read().decode().strip()
    except: o = "(timeout)"
    try: e = err.read().decode().strip()
    except: e = ""
    for line in o.split("\n"):
        if line: print(f"  {line}")
    return o

# Create a shared network for emergentic containers
run("Create network", "docker network create emergentic-net 2>/dev/null || echo 'network exists'")
run("Connect postgres to network", "docker network connect emergentic-net emergentic-postgres 2>/dev/null || echo 'already connected'")

# Recreate app container on the same network
run("Stop old container", "docker stop emergentic-api && docker rm emergentic-api")
run("Start app on emergentic-net", """
docker run -d \
    --name emergentic-api \
    --network emergentic-net \
    -p 8010:8000 \
    -e DATABASE_URL=postgresql://emergentic:emergentic_pass@emergentic-postgres:5432/emergentic_db \
    -e ENV=production \
    -e API_PORT=8000 \
    --restart unless-stopped \
    emergentic-ai:latest 2>&1
""")
run("Wait for startup", "sleep 15 && echo ready")
run("App logs", "docker logs emergentic-api --tail 8 2>&1")
run("Health check", "curl -s http://localhost:8010/health")

# Now migrations and seed should work
run("Migration 003", "docker exec emergentic-api python _migrate.py 2>&1")
run("Migration 004", "docker exec emergentic-api python db/migrations/004_migrate.py 2>&1")
run("Seed demo accounts", "docker exec emergentic-api python db/seed_demo_accounts.py 2>&1 | tail -25", timeout=60)

run("Final status", """
echo "=================================="
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E "emergentic|NAMES"
echo ""
curl -s http://localhost:8010/health
echo ""
echo "Live at: http://5.223.67.236:8010"
echo "Docs:    http://5.223.67.236:8010/docs"
echo "Nginx:   http://5.223.67.236:8080"
""")

ssh.close()
print("\n✅ Done!")
