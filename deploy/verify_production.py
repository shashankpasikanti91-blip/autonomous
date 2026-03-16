"""Add founder account and verify all demo accounts on server."""
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
    for line in o.split("\n"):
        if line: print(f"  {line}")
    return o

# Re-run seed to add founder account
run("Run seed (adds founder)", "docker exec emergentic-api python db/seed_demo_accounts.py 2>&1 | tail -30", timeout=60)

# Test auth endpoint
run("Test auth - founder", "curl -s -X POST 'http://localhost:8010/auth/login?email=founder@emergentic.ai&password=Founder%40123' | python3 -c 'import sys,json; d=json.load(sys.stdin); print(\"OK:\", d.get(\"user_email\", d.get(\"role\",\"?\")))'")
run("Test auth - admin", "curl -s -X POST 'http://localhost:8010/auth/login?email=admin@demo.com&password=Demo%40123' | python3 -c 'import sys,json; d=json.load(sys.stdin); print(\"OK:\", d.get(\"role\",\"?\"))'")

# Test frontend pages
run("Test landing page", "curl -s https://autonomous.srpailabs.com/ | grep -o 'Emergentic AI' | head -1")
run("Test /how-it-works", "curl -s https://autonomous.srpailabs.com/how-it-works | grep -o '<title>\\|index.html\\|Emergentic' | head -1")
run("Test /pricing", "curl -s -o /dev/null -w 'HTTP %{http_code}' https://autonomous.srpailabs.com/pricing")
run("Test /about", "curl -s -o /dev/null -w 'HTTP %{http_code}' https://autonomous.srpailabs.com/about")
run("Test /login", "curl -s -o /dev/null -w 'HTTP %{http_code}' https://autonomous.srpailabs.com/login")
run("Test API still works", "curl -s https://autonomous.srpailabs.com/health | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d[\"status\"], d[\"platform\"])'")
run("Test API docs", "curl -s -o /dev/null -w 'Docs: HTTP %{http_code}' https://autonomous.srpailabs.com/docs")

run("Summary", """
echo ""
echo "============================================"
echo "  EMERGENTIC AI PRODUCTION STATUS"
echo "============================================"
echo ""
echo "  https://autonomous.srpailabs.com          Landing page"
echo "  https://autonomous.srpailabs.com/login    Login (demo accounts)"
echo "  https://autonomous.srpailabs.com/pricing  Pricing tiers"
echo "  https://autonomous.srpailabs.com/about    About us"
echo "  https://autonomous.srpailabs.com/how-it-works  How it works"
echo "  https://autonomous.srpailabs.com/docs     API Documentation"
echo ""
echo "Demo Accounts (password: Demo@123):"
echo "  founder@emergentic.ai  (Founder@123)"
echo "  admin@demo.com         admin"
echo "  owner@demo.com         owner"
echo "  hr@demo.com            manager"
echo "  finance@demo.com       manager"
echo "  sales@demo.com         user"
echo "  dev@demo.com           user"
echo "  recruiter@demo.com     user"
echo "  ops@demo.com           user"
""")

ssh.close()
