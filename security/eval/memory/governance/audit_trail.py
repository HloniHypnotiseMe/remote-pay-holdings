#!/usr/bin/env python3
"""
Immutable Audit Trail
Every agent action logged with full traceability.
Required by King V Principle 10.
"""
import json
import hashlib
from datetime import datetime
from pathlib import Path

AUDIT_DIR = Path("/var/log/c6/audit")
AUDIT_DIR.mkdir(parents=True, exist_ok=True)


class AuditTrail:
    def __init__(self):
        self.current_file = AUDIT_DIR / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"

    def log(self, agent: str, action: str, resource: str,
            allowed: bool, human_override: bool = False,
            payload: dict = None):
        """Write an immutable audit entry."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "action": action,
            "resource": resource,
            "allowed": allowed,
            "human_override": human_override,
            "payload_hash": hashlib.sha256(
                json.dumps(payload or {}).encode()
            ).hexdigest()[:16],
            "chain_hash": self._chain_hash(),
        }

        with open(self.current_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

        return entry

    def _chain_hash(self):
        """Hash of previous entry to create tamper-evident chain."""
        if not self.current_file.exists():
            return "genesis"
        with open(self.current_file, "rb") as f:
            last_line = f.readlines()[-1] if f.readlines() else b""
        return hashlib.sha256(last_line).hexdigest()[:16]


if __name__ == "__main__":
    trail = AuditTrail()
    print(trail.log("c6_auditor", "read:business_data", "lead_123", True))
    print(trail.log("c6_auditor", "export:customer_records", "all", False))
