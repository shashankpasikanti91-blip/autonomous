"""Fix nginx conflict - replace old autonomous config with ours."""
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

# Check what the old autonomous config is
run("Old autonomous config", "cat /etc/nginx/sites-available/autonomous 2>/dev/null || cat /etc/nginx/sites-enabled/autonomous 2>/dev/null")

# Remove the conflicting old autonomous site
run("Remove old autonomous site", """
rm -f /etc/nginx/sites-enabled/autonomous
rm -f /etc/nginx/sites-enabled/emergentic-ai
echo "Removed old configs"
""")

# Write clean combined config
run("Write final nginx config", r"""
cat > /etc/nginx/sites-available/autonomous.srpailabs.com << 'NGINXEOF'
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name autonomous.srpailabs.com *.autonomous.srpailabs.com;
    return 301 https://$host$request_uri;
}

# HTTPS — main platform
server {
    listen 443 ssl;
    server_name autonomous.srpailabs.com *.autonomous.srpailabs.com;

    ssl_certificate /etc/letsencrypt/live/autonomous.srpailabs.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/autonomous.srpailabs.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;

    # Security headers
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    location / {
        proxy_pass http://127.0.0.1:8010;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 120;
        proxy_connect_timeout 10;
        client_max_body_size 50M;
    }
}
NGINXEOF
echo "Config written"
""")

run("Enable clean config", """
ln -sf /etc/nginx/sites-available/autonomous.srpailabs.com /etc/nginx/sites-enabled/autonomous.srpailabs.com
nginx -t 2>&1
""")

run("Reload nginx", "systemctl reload nginx && echo 'OK'")

# Test
run("Test HTTPS", "curl -sk https://autonomous.srpailabs.com/health")
run("Test HTTP redirect", "curl -s -o /dev/null -w 'HTTP %{http_code}' http://autonomous.srpailabs.com/health")

run("Final status", """
echo ""
echo "✅ EMERGENTIC AI — LIVE"
echo ""
echo "  https://autonomous.srpailabs.com        ← Main URL"
echo "  https://autonomous.srpailabs.com/docs   ← API Docs"
echo "  https://autonomous.srpailabs.com/health ← Health Check"
echo "  http://5.223.67.236:8010               ← Direct"
echo ""
nginx -t 2>&1 | head -2
""")

ssh.close()
