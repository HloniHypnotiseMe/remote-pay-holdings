#!/usr/bin/env python3
"""
RemotePay POS Bridge
Connects physical cash registers to RemotePay + C6 Tax AI.

Supported POS systems:
- Yoco (via API)
- iKhokha (via API)
- GAAP (via API)
- Pilot (via API)
- Loyverse (via API)
- Shopify POS (via API)

Uses nango (Category 9) for integration management.
"""
import requests
import json
from datetime import datetime


class POSBridge:
    """
    Reference: nango (Category 9: Directory & Marketplace)
    nango handles OAuth + API tokens for all POS providers.
    """

    POS_PROVIDERS = {
        "yoco": {
            "api_base": "https://api.yoco.com/v1",
            "auth_type": "bearer",
            "docs": "https://developer.yoco.com/",
        },
        "ikhokha": {
            "api_base": "https://api.ikhokha.com/v1",
            "auth_type": "api_key",
        },
        "gaap": {
            "api_base": "https://api.gaap.co.za/v2",
            "auth_type": "oauth2",
        },
        "loyverse": {
            "api_base": "https://api.loyverse.com/v1.0",
            "auth_type": "bearer",
        },
        "shopify_pos": {
            "api_base": "https://{shop}.myshopify.com/admin/api/2026-01",
            "auth_type": "oauth2",
        },
    }

    def __init__(self, tenant_id, nango_connection_id):
        self.tenant_id = tenant_id
        self.nango_connection_id = nango_connection_id

    def connect_pos(self, provider_name):
        """
        Initiate OAuth flow for POS provider.
        Uses nango for token management.
        Reference: nango (Category 9)
        """
        if provider_name not in self.POS_PROVIDERS:
            raise ValueError(f"Unsupported POS: {provider_name}")

        # nango handles the OAuth dance
        # Reference: nango (Category 9: Directory & Marketplace)
        oauth_url = f"https://api.nango.dev/oauth/connect/{provider_name}"

        return {
            "redirect_url": oauth_url,
            "tenant_id": self.tenant_id,
            "provider": provider_name,
        }

    def sync_transactions(self, provider_name, since_date):
        """
        Pull transactions from POS and record in RemotePay.

        Flow:
        1. Fetch transactions from POS API
        2. Normalise format
        3. Push to RemotePay transaction ledger
        4. C6 Tax AI agent picks them up for VAT tracking
        """
        provider = self.POS_PROVIDERS[provider_name]

        # Step 1: Fetch from POS (via nango)
        pos_transactions = self._fetch_from_pos(provider_name, since_date)

        # Step 2: Normalise
        normalised = [
            self._normalise(t, provider_name) for t in pos_transactions
        ]

        # Step 3: Push to RemotePay
        for txn in normalised:
            self._record_in_remotepay(txn)

        # Step 4: Notify C6 Tax AI
        self._notify_tax_agent(normalised)

        return {
            "synced_count": len(normalised),
            "provider": provider_name,
            "since": since_date,
        }

    def _fetch_from_pos(self, provider, since_date):
        """Fetch via nango proxy (nango handles all POS APIs uniformly)."""
        # Reference: nango (Category 9)
        r = requests.get(
            f"https://api.nango.dev/proxy/{provider}/transactions",
            params={"since": since_date},
            headers={"Connection-Id": self.nango_connection_id},
        )
        return r.json().get("transactions", [])

    def _normalise(self, txn, provider):
        """Convert POS-specific format to RemotePay standard."""
        return {
            "source": provider,
            "external_id": txn.get("id"),
            "amount": txn.get("amount", 0),
            "currency": "ZAR",
            "vat_amount": txn.get("amount", 0) * 0.15,  # 15% VAT (SA)
            "timestamp": txn.get("created_at"),
            "payment_method": txn.get("payment_method", "card"),
            "tenant_id": self.tenant_id,
        }

    def _record_in_remotepay(self, txn):
        """Push transaction to RemotePay ledger."""
        requests.post(
            "http://localhost:8000/api/ledger/record",
            json=txn,
            headers={"X-Tenant-Id": self.tenant_id},
        )

    def _notify_tax_agent(self, transactions):
        """Notify C6 Tax AI agent for VAT tracking."""
        requests.post(
            "http://localhost:8500/api/{}/tax/ingest".format(self.tenant_id),
            json={"transactions": transactions, "type": "pos_sync"},
        )


if __name__ == "__main__":
    bridge = POSBridge(
        tenant_id="test_tenant_001",
        nango_connection_id="nango_conn_xyz"
    )
    print(json.dumps(bridge.connect_pos("yoco"), indent=2))
