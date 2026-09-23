"""Adapter for publishing Tax Secretarial evidence to C6 SaaS Core.

The domain remains usable without the platform endpoint; however, customer-facing
claims must not be promoted to VERIFIED/LIVE unless the C6 evidence service
accepts the record.
"""
from __future__ import annotations

import json
import os
from typing import Any
from urllib.request import Request, urlopen

from core.contracts import EvidenceItem

STATUS_MAP = {
    "CALCULATED": "WORKS",
    "UNVERIFIED": "EXISTS",
    "VERIFIED": "VERIFIED",
    "LIVE": "LIVE",
    "GAP": "GAP",
}


def build_evidence_contract(
    *,
    tenant_id: str,
    entity: str,
    capability: str,
    evidence: EvidenceItem,
) -> dict[str, Any]:
    return {
        "tenant_id": tenant_id,
        "product_id": "tax_secretarial",
        "capability": capability,
        "claim": evidence.claim,
        "status": STATUS_MAP.get(evidence.status.upper(), "GAP"),
        "evidence_type": "document_evidence",
        "source": evidence.source,
        "evidence": {
            "evidence_id": evidence.evidence_id,
            "entity": entity,
            "notes": evidence.notes,
            "domain_status": evidence.status,
        },
    }


def publish_evidence(
    *,
    tenant_id: str,
    entity: str,
    capability: str,
    evidence: EvidenceItem,
) -> dict[str, Any]:
    url = os.getenv("C6_EVIDENCE_API_URL")
    if not url:
        return {
            "published": False,
            "status": "GAP",
            "reason": "C6_EVIDENCE_API_URL is not configured",
        }

    payload = build_evidence_contract(
        tenant_id=tenant_id,
        entity=entity,
        capability=capability,
        evidence=evidence,
    )
    request = Request(
        url.rstrip("/") + "/api/v1/evidence",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=5) as response:
            accepted = json.loads(response.read().decode("utf-8"))
        return {            "published": True,            "status": accepted["status"],            "record": accepted,            "evidence_id": accepted["id"],        }
    except Exception as exc:
        return {
            "published": False,
            "status": "GAP",
            "reason": f"C6 evidence service unavailable: {exc.__class__.__name__}",
        }
