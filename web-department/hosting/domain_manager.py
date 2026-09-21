#!/usr/bin/env python3
"""C6 Website Department — Domain Manager"""
from datetime import datetime
import dns.resolver


class DomainManager:
    def __init__(self, db_pool, config):
        self.db = db_pool
        self.base_domain = config["base_domain"]
        self.cloudflare_token = config.get("cloudflare_token")
        self.cloudflare_zone = config.get("cloudflare_zone")

    def get_subdomain(self, business_id):
        slug = self._slugify(business_id)
        return f"{slug}.{self.base_domain}"

    async def connect_custom_domain(self, business_id, custom_domain):
        verification = await self._verify_ownership(custom_domain, business_id)
        if not verification["verified"]:
            return {"status": "PENDING_VERIFICATION", "instructions": verification["instructions"]}
        dns_result = await self._create_dns_record(custom_domain, business_id)
        ssl_result = await self._provision_ssl(custom_domain)
        await self._update_nginx(custom_domain, business_id)
        return {"status": "CONNECTED", "domain": custom_domain,
                "ssl": ssl_result["status"], "dns": dns_result["status"]}

    async def _verify_ownership(self, domain, business_id):
        txt_record = f"_c6-verify.{domain}"
        expected = f"c6-verify={business_id}"
        try:
            answers = dns.resolver.resolve(txt_record, 'TXT')
            for rdata in answers:
                if expected in str(rdata):
                    return {"verified": True}
        except Exception:
            pass
        return {"verified": False,
                "instructions": f"Add TXT record: {txt_record} = {expected}"}

    async def _create_dns_record(self, custom_domain, business_id):
        import aiohttp
        subdomain = self._slugify(business_id)
        url = f"https://api.cloudflare.com/client/v4/zones/{self.cloudflare_zone}/dns_records"
        headers = {"Authorization": f"Bearer {self.cloudflare_token}",
                   "Content-Type": "application/json"}
        payload = {"type": "CNAME", "name": custom_domain,
                   "content": f"{subdomain}.{self.base_domain}",
                   "ttl": 1, "proxied": True}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                data = await resp.json()
                return {"status": "OK" if data.get("success") else "FAILED"}

    async def _provision_ssl(self, domain):
        import asyncio
        proc = await asyncio.create_subprocess_exec(
            "certbot", "certonly", "--nginx", "-d", domain,
            "--non-interactive", "--agree-tos",
            "--email", "admin@remotepay.co.za",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await proc.communicate()
        return {"status": "OK" if proc.returncode == 0 else "FAILED"}

    async def _update_nginx(self, custom_domain, business_id):
        import asyncio
        subdomain = self._slugify(business_id)
        config_path = f"/etc/nginx/sites-available/{subdomain}.conf"
        try:
            with open(config_path) as f:
                config = f.read()
            if custom_domain not in config:
                config = config.replace(
                    f"server_name {subdomain}.{self.base_domain};",
                    f"server_name {subdomain}.{self.base_domain} {custom_domain};")
                with open(config_path, "w") as f:
                    f.write(config)
            proc = await asyncio.create_subprocess_exec(
                "systemctl", "reload", "nginx",
                stdout=asyncio.subprocess.PIPE)
            await proc.communicate()
        except FileNotFoundError:
            pass

    def _slugify(self, text):
        import re
        return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


if __name__ == "__main__":
    print("Domain Manager ready")
