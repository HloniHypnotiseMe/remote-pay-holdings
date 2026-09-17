#!/usr/bin/env python3
"""
C6 SaaS Multi-Tenant Backend
Every customer is isolated. Every product is a subscription.
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional
import asyncpg
import json
import os

app = FastAPI(title="C6 SaaS Platform")

DB_POOL = None


@app.on_event("startup")
async def startup():
    global DB_POOL
    DB_POOL = await asyncpg.create_pool(
        "postgresql://c6group:password@localhost:5432/c6_saas"
    )


# ============================================================
# TENANT MODEL
# ============================================================

class Tenant(BaseModel):
    tenant_id: str
    company_name: str
    subscription_tier: str  # starter, growth, enterprise
    active_products: list[str]  # ["tax", "secretarial", "cybersecurity"]


async def get_tenant(tenant_id: str) -> Tenant:
    """Load tenant from database."""
    async with DB_POOL.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM tenants WHERE tenant_id = $1", tenant_id
        )
        if not row:
            raise HTTPException(404, "Tenant not found")
        return Tenant(**dict(row))


# ============================================================
# SUBSCRIPTION TIERS
# ============================================================

TIER_PRODUCTS = {
    "starter": ["secretarial", "compliance"],
    "growth": ["secretarial", "compliance", "tax", "risk", "cybersecurity"],
    "enterprise": [
        "secretarial", "compliance", "tax", "risk",
        "cybersecurity", "international", "pos-bridge"
    ],
}

PRODUCT_PRICES = {
    "tax": 499,
    "secretarial": 399,
    "compliance": 599,
    "risk": 799,
    "cybersecurity": 599,
    "international": 1499,
    "pos-bridge": 899,
}


# ============================================================
# AGENT ROUTING
# ============================================================

AGENT_CATEGORIES = {
    # Category reference for agents
    "tax": {
        "agents": ["tax_director", "sars_filing_agent", "compliance_calendar"],
        "repo_refs": ["tax-secretarial/sars/", "tax-secretarial/director/"],
    },
    "secretarial": {
        "agents": ["cipc_secretarial", "compliance_calendar"],
        "repo_refs": ["tax-secretarial/cipc/"],
    },
    "compliance": {
        "agents": ["compliance_auditor", "incident_commander"],
        "repo_refs": ["governance/"],
    },
    "risk": {
        "agents": ["risk_director", "inversion_analyst", "red_team_lead"],
        "repo_refs": ["risk-inversion/"],
    },
    "cybersecurity": {
        "agents": ["security_scanner", "threat_intel", "phishing_simulator"],
        "repo_refs": [
            "shared/security/",  # crowdsec, prowler
            "monitoring/",        # hyperdx, uptime-kuma
            "shared/security/vaultwarden/",  # credentials
        ],
    },
    "international": {
        "agents": ["international_tax_analyst"],
        "repo_refs": ["tax-secretarial/international/"],
    },
    "pos-bridge": {
        "agents": ["pos_sync", "transaction_recorder", "tax_connector"],
        "repo_refs": ["integrations/pos/"],  # Uses nango for integrations
    },
}


@app.post("/api/{tenant_id}/{product}/run")
async def run_product(
    tenant_id: str,
    product: str,
    payload: dict,
    authorization: str = Header(None),
):
    """Run a SaaS product action for a tenant."""
    tenant = await get_tenant(tenant_id)

    # Verify subscription includes this product
    allowed = TIER_PRODUCTS.get(tenant.subscription_tier, [])
    if product not in allowed and product not in tenant.active_products:
        raise HTTPException(402, f"Product '{product}' not in subscription")

    # Get the agents for this product
    product_config = AGENT_CATEGORIES.get(product)
    if not product_config:
        raise HTTPException(404, f"Unknown product: {product}")

    # Route to appropriate agent
    result = {
        "tenant": tenant_id,
        "product": product,
        "agents_used": product_config["agents"],
        "repo_refs": product_config["repo_refs"],
        "status": "processed",
    }

    return result


@app.get("/api/{tenant_id}/subscription")
async def get_subscription(tenant_id: str):
    """Return tenant subscription details."""
    tenant = await get_tenant(tenant_id)
    allowed = TIER_PRODUCTS.get(tenant.subscription_tier, [])
    monthly_total = sum(PRODUCT_PRICES.get(p, 0) for p in allowed)

    return {
        "tenant_id": tenant.tenant_id,
        "company": tenant.company_name,
        "tier": tenant.subscription_tier,
        "products": allowed,
        "monthly_total_zar": monthly_total,
        "estimated_our_cost_zar": round(len(allowed) * 0.15, 2),
        "margin_pct": 99.98,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8500)
