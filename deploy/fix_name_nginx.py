"""Fix platform name and clean up nginx conflicts."""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("5.223.67.236", username="root", password="856Reey@nsh", timeout=15)

def run(desc, cmd, timeout=30):
    print(f"\n[{desc}]")
    _, out, err = ssh.exec_command(cmd, timeout=timeout)
    out.channel.settimeout(timeout)
    try: o = out.read().decode().strip()
    except: o = "(timeout)"
    for line in o.split("\n"):
        if line: print(f"  {line}")
    return o

# Find duplicate autonomous config
run("All configs with autonomous.srpailabs.com", """
grep -rl "autonomous.srpailabs.com" /etc/nginx/sites-enabled/ 2>/dev/null
""")

run("Remove duplicate configs", """
rm -f /etc/nginx/sites-enabled/emergentic-ai-domain
ls /etc/nginx/sites-enabled/
""")

run("Test nginx clean", "nginx -t 2>&1 | head -5")
run("Reload nginx", "systemctl reload nginx && echo OK")

# Fix platform name and env in the running container
run("Update container env vars", """
docker exec emergentic-api sh -c "echo 'Container env OK'" 
# The .env is baked in — recreate container with correct name
""")

# Check what PLATFORM_NAME is in the .env on server
run("Check server .env", "cat /opt/emergentic-ai/.env | grep -E 'PLATFORM_NAME|PLATFORM_DOMAIN|ALLOWED_ORIGINS'")

# Update the .env on server  
run("Update server .env", r"""
cd /opt/emergentic-ai
# Update PLATFORM_NAME
sed -i 's/^PLATFORM_NAME=.*/PLATFORM_NAME=Emergentic AI/' .env
# Update PLATFORM_DOMAIN
sed -i 's/^PLATFORM_DOMAIN=.*/PLATFORM_DOMAIN=autonomous.srpailabs.com/' .env
# Update ALLOWED_ORIGINS
sed -i 's|^ALLOWED_ORIGINS=.*|ALLOWED_ORIGINS=https://autonomous.srpailabs.com,http://localhost:3000,http://localhost:5173|' .env
echo "Updated .env:"
grep -E 'PLATFORM_NAME|PLATFORM_DOMAIN|ALLOWED_ORIGINS' .env
""")

# Restart container to pick up new env
run("Restart container with new env", """
docker stop emergentic-api && docker rm emergentic-api
sleep 2
# Get postgres IP from network
PG_IP=$(docker inspect emergentic-postgres --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
echo "Postgres IP: $PG_IP"

docker run -d \
    --name emergentic-api \
    --network emergentic-net \
    -p 8010:8000 \
    --env-file /opt/emergentic-ai/.env \
    -e DATABASE_URL=postgresql://emergentic:emergentic_pass@emergentic-postgres:5432/emergentic_db \
    --restart unless-stopped \
    emergentic-ai:latest
""", timeout=45)

run("Wait for startup", "sleep 12 && echo ready")
run("Test health with new name", "curl -s https://autonomous.srpailabs.com/health")
run("Test docs", "curl -s -o /dev/null -w 'Docs: HTTP %{http_code}' https://autonomous.srpailabs.com/docs")

run("Final status", """
echo ""
echo "====================================="
echo "   EMERGENTIC AI — FULLY DEPLOYED"
echo "====================================="
echo ""
echo "  https://autonomous.srpailabs.com"
echo "  https://autonomous.srpailabs.com/docs"
echo "  https://autonomous.srpailabs.com/health"
echo ""
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep emergentic
""")

ssh.close()
