#!/usr/bin/env python3
"""
C6 Website Department — Deployer
Takes rendered site files and deploys them to a live subdomain.
"""
import asyncio
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
try:
    import asyncpg
except ImportError:
    asyncpg = None


class SiteDeployer:
    """
    Deployment pipeline:
    1. Copy rendered files to nginx web root
    2. Create nginx config for subdomain
    3. Provision SSL via Let's Encrypt
    4. Reload nginx
    5. Update DNS (Cloudflare API)
    6. Health check
    """

    def __init__(self, db_pool, config):
        self.db = db_pool
        self.config = config
        self.web_root = Path(config.get("web_root", "/var/www/c6-sites"))
        self.nginx_sites = Path(config.get("nginx_sites", "/etc/nginx/sites-available"))
        self.nginx_enabled = Path(config.get("nginx_enabled", "/etc/nginx/sites-enabled"))
        self.base_domain = config.get("base_domain", "c6.remotepay.co.za")
        self.cloudflare_token = config.get("cloudflare_token")
        self.cloudflare_zone = config.get("cloudflare_zone")

    async def deploy(self, business_id, rendered_dir, custom_domain=None):
        """Deploy a site end-to-end."""
        subdomain = self._slugify(business_id)
        domain = custom_domain or f"{subdomain}.{self.base_domain}"

        deployment = {
            "business_id": business_id,
            "domain": domain,
            "started_at": datetime.now().isoformat(),
            "steps": [],
        }

        try:
            target_dir = self.web_root / subdomain
            await self._copy_files(rendered_dir, target_dir)
            deployment["steps"].append({"step": "copy_files", "status": "OK"})

            await self._set_permissions(target_dir)
            deployment["steps"].append({"step": "permissions", "status": "OK"})

            await self._create_nginx_config(subdomain, domain, target_dir)
            deployment["steps"].append({"step": "nginx_config", "status": "OK"})

            await self._enable_site(subdomain)
            deployment["steps"].append({"step": "enable_site", "status": "OK"})

            test = await self._test_nginx()
            if not test["ok"]:
                raise Exception(f"Nginx config test failed: {test['error']}")
            deployment["steps"].append({"step": "nginx_test", "status": "OK"})

            await self._reload_nginx()
            deployment["steps"].append({"step": "nginx_reload", "status": "OK"})

            if custom_domain:
                ssl_result = await self._provision_ssl(domain, target_dir)
                deployment["steps"].append({"step": "ssl", "status": ssl_result["status"]})

            if custom_domain and self.cloudflare_token:
                dns_result = await self._update_dns(custom_domain, subdomain)
                deployment["steps"].append({"step": "dns", "status": dns_result["status"]})

            healthy = await self._health_check(domain)
            deployment["steps"].append({"step": "health_check", "status": "OK" if healthy else "FAIL"})

            deployment["status"] = "DEPLOYED" if healthy else "HEALTH_CHECK_FAILED"
            deployment["url"] = f"https://{domain}"
            deployment["completed_at"] = datetime.now().isoformat()

            await self._save_deployment(deployment)
            return deployment

        except Exception as e:
            deployment["status"] = "FAILED"
            deployment["error"] = str(e)
            deployment["completed_at"] = datetime.now().isoformat()
            await self._save_deployment(deployment)
            return deployment

    async def _copy_files(self, source, target):
        target.mkdir(parents=True, exist_ok=True)
        if Path(source).exists():
            proc = await asyncio.create_subprocess_exec(
                "rsync", "-av", "--delete",
                f"{source}/", f"{target}/",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

    async def _set_permissions(self, target_dir):
        await self._run_cmd(["chown", "-R", "www-data:www-data", str(target_dir)])
        await self._run_cmd(["chmod", "-R", "755", str(target_dir)])

    async def _create_nginx_config(self, subdomain, domain, target_dir):
        config = f"""# C6 Auto-generated config for {subdomain}
server {{
    listen 80;
    listen [::]:80;
    server_name {domain};
    root {target_dir};
    index index.html;
    gzip on;
    location / {{ try_files $uri $uri/ $uri.html /index.html; }}
    location /api/ {{
        proxy_pass http://127.0.0.1:8500;
        proxy_set_header Host $host;
    }}
    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {{
        expires 30d;
        add_header Cache-Control "public, immutable";
    }}
}}
"""
        config_path = self.nginx_sites / f"{subdomain}.conf"
        config_path.write_text(config)

    async def _enable_site(self, subdomain):
        source = self.nginx_sites / f"{subdomain}.conf"
        target = self.nginx_enabled / f"{subdomain}.conf"
        if target.exists() or target.is_symlink():
            target.unlink()
        target.symlink_to(source)

    async def _test_nginx(self):
        result = await self._run_cmd(["nginx", "-t"])
        return {"ok": result["returncode"] == 0, "error": result["stderr"]}

    async def _reload_nginx(self):
        await self._run_cmd(["systemctl", "reload", "nginx"])

    async def _provision_ssl(self, domain, webroot):
        result = await self._run_cmd([
            "certbot", "certonly", "--nginx", "-d", domain,
            "--non-interactive", "--agree-tos",
            "--email", "admin@remotepay.co.za",
        ])
        return {"status": "OK" if result["returncode"] == 0 else "FAILED",
                "error": result["stderr"]}

    async def _update_dns(self, custom_domain, subdomain):
        import aiohttp
        url = f"https://api.cloudflare.com/client/v4/zones/{self.cloudflare_zone}/dns_records"
        headers = {
            "Authorization": f"Bearer {self.cloudflare_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "type": "CNAME",
            "name": custom_domain,
            "content": f"{subdomain}.{self.base_domain}",
            "ttl": 1,
            "proxied": True,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                data = await resp.json()
                return {"status": "OK" if data.get("success") else "FAILED", "data": data}

    async def _health_check(self, domain):
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://{domain}", timeout=10) as resp:
                    return resp.status == 200
        except Exception:
            return False

    async def _save_deployment(self, deployment):
        import json
        async with self.db.acquire() as conn:
            await conn.execute("""
                INSERT INTO deployments
                (business_id, domain, status, url, steps, deployed_at)
                VALUES ($1, $2, $3, $4, $5, NOW())
                ON CONFLICT (business_id) DO UPDATE
                SET domain = $2, status = $3, url = $4, steps = $5, deployed_at = NOW()
            """, deployment["business_id"], deployment["domain"],
                deployment["status"], deployment.get("url"),
                json.dumps(deployment["steps"]))

    async def _run_cmd(self, cmd):
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        return {
            "returncode": proc.returncode,
            "stdout": stdout.decode(),
            "stderr": stderr.decode(),
        }

    def _slugify(self, text):
        import re
        return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


if __name__ == "__main__":
    print("Site Deployer ready")
