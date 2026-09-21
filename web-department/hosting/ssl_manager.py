#!/usr/bin/env python3
"""C6 Website Department — SSL Manager"""
from datetime import datetime
import asyncio
import re


class SSLManager:
    def __init__(self, db_pool):
        self.db = db_pool

    async def check_all_certs(self):
        certs = await self._list_certs()
        results = []
        for cert in certs:
            days_left = self._days_until_expiry(cert["expiry"])
            status = "OK" if days_left > 30 else "RENEWAL_NEEDED"
            if days_left <= 30:
                renewed = await self._renew_cert(cert["domain"])
                status = "RENEWED" if renewed else "RENEWAL_FAILED"
            results.append({"domain": cert["domain"], "expiry": cert["expiry"],
                            "days_left": days_left, "status": status})
        return results

    async def _list_certs(self):
        proc = await asyncio.create_subprocess_exec(
            "certbot", "certificates",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, _ = await proc.communicate()
        output = stdout.decode()
        certs = []
        current_domain = None
        for line in output.split("\n"):
            dm = re.search(r"Domains:\s*(.+)", line)
            if dm:
                current_domain = dm.group(1).strip()
            em = re.search(r"Expiry Date:\s*(.+)", line)
            if em and current_domain:
                try:
                    expiry = datetime.strptime(em.group(1).strip().split(" ")[0], "%Y-%m-%d")
                except ValueError:
                    expiry = datetime.now()
                certs.append({"domain": current_domain, "expiry": expiry})
                current_domain = None
        return certs

    def _days_until_expiry(self, expiry):
        return (expiry - datetime.now()).days

    async def _renew_cert(self, domain):
        proc = await asyncio.create_subprocess_exec(
            "certbot", "renew", "--cert-name", domain,
            "--non-interactive",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await proc.communicate()
        if proc.returncode == 0:
            rp = await asyncio.create_subprocess_exec(
                "systemctl", "reload", "nginx",
                stdout=asyncio.subprocess.PIPE)
            await rp.communicate()
            return True
        return False


if __name__ == "__main__":
    print("SSL Manager ready")
