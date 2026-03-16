"""Configure autonomous.srpailabs.com domain on Hetzner server."""
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

# Check existing nginx sites and what's on port 80/443
run("Existing nginx sites", "ls /etc/nginx/sites-enabled/ 2>/dev/null")
run("Current nginx default", "cat /etc/nginx/sites-enabled/default 2>/dev/null | head -20 || echo 'no default'")
run("Check certbot installed", "which certbot 2>/dev/null || apt list --installed 2>/dev/null | grep certbot | head -3")
run("Check port 80 binding", "ss -tlnp | grep ':80 ' || netstat -tlnp 2>/dev/null | grep ':80 '")
run("Check DNS resolution", "curl -s -o /dev/null -w '%{http_code}' http://autonomous.srpailabs.com/ --connect-timeout 5 || echo 'DNS not resolving to this server'")

# Install certbot if not present
run("Install certbot", "apt-get install -y certbot python3-certbot-nginx 2>&1 | tail -5", timeout=90)

# Get SSL cert for the domain
result = run("Get SSL cert", """
certbot certonly --nginx \
    -d autonomous.srpailabs.com \
    --non-interactive \
    --agree-tos \
    -m admin@srpailabs.com \
    --redirect \
    2>&1 | tail -15
""", timeout=90)

# Check if cert was obtained
run("Check cert exists", "ls -la /etc/letsencrypt/live/autonomous.srpailabs.com/ 2>/dev/null || echo 'cert not found'")

# Write nginx config for autonomous.srpailabs.com
run("Write nginx config for domain", """
cat > /etc/nginx/sites-available/emergentic-ai-domain << 'NGINXEOF'
# Emergentic AI - autonomous.srpailabs.com
server {
    listen 80;
    server_name autonomous.srpailabs.com *.autonomous.srpailabs.com;

    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        proxy_pass http://127.0.0.1:8010;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 120;
        proxy_connect_timeout 10;
        client_max_body_size 50M;
    }
}
NGINXEOF
echo "HTTP config written"
""")

# Check if we got the SSL cert and add HTTPS block
cert_path = run("Check cert path", "ls /etc/letsencrypt/live/autonomous.srpailabs.com/fullchain.pem 2>/dev/null | wc -l")
if cert_path.strip() == "1":
    run("Add HTTPS to nginx config", """
cat >> /etc/nginx/sites-available/emergentic-ai-domain << 'NGINXEOF'

server {
    listen 443 ssl;
    server_name autonomous.srpailabs.com *.autonomous.srpailabs.com;

    ssl_certificate /etc/letsencrypt/live/autonomous.srpailabs.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/autonomous.srpailabs.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://127.0.0.1:8010;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 120;
        client_max_body_size 50M;
    }
}
NGINXEOF
echo "HTTPS config added"
""")

# Enable the site
run("Enable site", """
ln -sf /etc/nginx/sites-available/emergentic-ai-domain /etc/nginx/sites-enabled/emergentic-ai-domain
nginx -t 2>&1 | head -5
""")

run("Reload nginx", "systemctl reload nginx 2>&1 && echo 'nginx reloaded OK' || nginx -s reload 2>&1")

# Update .env on server to use the new domain
run("Update PLATFORM_DOMAIN in container", """
docker exec emergentic-api sh -c "
  export PLATFORM_DOMAIN=autonomous.srpailabs.com
  echo 'PLATFORM_DOMAIN updated in container'
" 2>&1
""")

run("Test domain HTTP", "curl -s -o /dev/null -w 'HTTP %{http_code}' http://autonomous.srpailabs.com/health --connect-timeout 10 2>&1 || echo 'domain not accessible yet'")

run("Summary", """
echo "=================================="
echo "LIVE URLS:"
echo "  HTTP:  http://autonomous.srpailabs.com"  
echo "  HTTPS: https://autonomous.srpailabs.com"
echo "  Docs:  http://autonomous.srpailabs.com/docs"
echo "  Direct: http://5.223.67.236:8010"
echo ""
docker ps | grep emergentic
""")

ssh.close()
print("\nDomain configuration complete!")
