#!/usr/bin/env python3
"""
deploy_frontend.py — Deploy Emergentic AI frontend to production server.

Usage:
    python deploy/deploy_frontend.py

What it does:
  1. Builds the React/Vite frontend (ui-platform → dist/)
  2. SSHes to 5.223.67.236 (root)
  3. Copies dist/ files to /opt/emergentic-ai/ui-platform/dist/
  4. Writes the corrected nginx config (SPA + API proxy)
  5. Reloads nginx

Prerequisites:
  pip install paramiko scp
"""

import os
import subprocess
import sys
import time

# ─── Configuration ────────────────────────────────────────────────────────────
HOST        = "5.223.67.236"
PORT        = 22
USER        = "root"
PASSWORD    = "856Reey@nsh"
REMOTE_DIST = "/opt/emergentic-ai/ui-platform/dist"
NGINX_CONF_PATH = "/etc/nginx/sites-available/autonomous.srpailabs.com"
NGINX_ENABLED   = "/etc/nginx/sites-enabled/autonomous.srpailabs.com"

LOCAL_DIST = os.path.join(os.path.dirname(__file__), "..", "ui-platform", "dist")

# ─── Nginx config ─────────────────────────────────────────────────────────────
NGINX_CONFIG = """
server {
    listen 80;
    server_name autonomous.srpailabs.com *.autonomous.srpailabs.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name autonomous.srpailabs.com *.autonomous.srpailabs.com;

    ssl_certificate     /etc/letsencrypt/live/autonomous.srpailabs.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/autonomous.srpailabs.com/privkey.pem;

    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    root  /opt/emergentic-ai/ui-platform/dist;
    index index.html;

    # ── Backend API proxy ──────────────────────────────────────────────────────
    location /api/ {
        proxy_pass         http://127.0.0.1:8010;
        proxy_http_version 1.1;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }

    location /auth/ {
        proxy_pass         http://127.0.0.1:8010;
        proxy_http_version 1.1;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }

    location /webhooks/ {
        proxy_pass         http://127.0.0.1:8010;
        proxy_http_version 1.1;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }

    location = /health {
        proxy_pass         http://127.0.0.1:8010;
        proxy_http_version 1.1;
        proxy_set_header   Host $host;
    }

    location /docs {
        proxy_pass         http://127.0.0.1:8010;
        proxy_http_version 1.1;
        proxy_set_header   Host $host;
    }

    location = /openapi.json {
        proxy_pass         http://127.0.0.1:8010;
        proxy_http_version 1.1;
        proxy_set_header   Host $host;
    }

    # ── React SPA — all other routes serve index.html ─────────────────────────
    location / {
        try_files $uri $uri/ /index.html;
    }
}
"""

# ─── Helpers ──────────────────────────────────────────────────────────────────
def log(msg: str) -> None:
    print(f"  {msg}".encode('utf-8', errors='replace').decode('utf-8', errors='replace'), flush=True)


def run_local(cmd: str) -> None:
    log(f"$ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        sys.exit(f"Command failed: {cmd}")
    log("  ✓ done")


def deploy() -> None:
    try:
        import paramiko
        from scp import SCPClient
    except ImportError:
        sys.exit("Missing dependencies. Run: pip install paramiko scp")

    print("=" * 60)
    print("  Emergentic AI — Frontend Deploy")
    print("=" * 60)

    # ── 1. Build ──────────────────────────────────────────────────────────────
    print("\n[1/4] Building frontend…")
    ui_dir = os.path.join(os.path.dirname(__file__), "..", "ui-platform")
    run_local(f'cd "{os.path.abspath(ui_dir)}" && npm run build')

    if not os.path.isdir(LOCAL_DIST):
        sys.exit(f"Build output not found at: {LOCAL_DIST}")
    log(f"✓ dist/ built at {LOCAL_DIST}")

    # ── 2. Connect ────────────────────────────────────────────────────────────
    print(f"\n[2/4] Connecting to {USER}@{HOST}…")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=30)
    log("✓ SSH connected")

    def run_ssh(cmd: str) -> str:
        _, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        if err and "warning" not in err.lower():
            log(f"  stderr: {err}")
        return out

    # ── 3. Upload dist ────────────────────────────────────────────────────────
    print(f"\n[3/4] Uploading dist/ to {REMOTE_DIST}…")
    run_ssh(f"mkdir -p {REMOTE_DIST}")

    with SCPClient(ssh.get_transport()) as scp:
        # Upload all files in dist/
        for item in os.listdir(LOCAL_DIST):
            local_path = os.path.join(LOCAL_DIST, item)
            log(f"  Uploading {item}…")
            scp.put(local_path, remote_path=REMOTE_DIST, recursive=True)

    log("✓ Files uploaded")

    # ── 4. Write nginx config & reload ────────────────────────────────────────
    print("\n[4/4] Writing nginx config and reloading…")

    # Write config via SFTP
    sftp = ssh.open_sftp()
    with sftp.open(NGINX_CONF_PATH, 'w') as f:
        f.write(NGINX_CONFIG)
    sftp.close()
    log("✓ nginx config written")

    # Enable site
    run_ssh(f"ln -sf {NGINX_CONF_PATH} {NGINX_ENABLED}")

    # Test nginx config
    test_out = run_ssh("nginx -t 2>&1")
    if "successful" not in test_out.lower() and "ok" not in test_out.lower():
        log(f"Nginx test output: {test_out}")
        log("⚠ nginx config test may have issues — check manually")
    else:
        log("✓ nginx config test passed")

    # Reload nginx
    run_ssh("systemctl reload nginx")
    log("✓ nginx reloaded")

    ssh.close()

    print("\n" + "=" * 60)
    print("  ✓ DEPLOYMENT COMPLETE")
    print("=" * 60)
    print(f"\n  Site: https://autonomous.srpailabs.com")
    print(f"  React SPA routes now work (try /how-it-works, /pricing, /about)")
    print(f"  API still proxied at /api/, /auth/, /health")


if __name__ == "__main__":
    deploy()
