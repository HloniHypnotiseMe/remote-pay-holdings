#!/usr/bin/env python3
"""
C6 Website Department — RemotePay Integration
Generates embeddable payment buttons, checkout pages, and payment links.
"""
from datetime import datetime
import hmac
import hashlib
import json
import base64


class RemotePayEmbed:
    """
    Provides:
    - Payment button (one-line embed)
    - Full checkout link (for cart)
    - Payment links (for invoices/WhatsApp)
    - Subscription buttons (for SaaS)
    - Webhook verification + handlers
    """

    def __init__(self, config):
        self.merchant_id = config["merchant_id"]
        self.api_key = config["api_key"]
        self.api_secret = config["api_secret"]
        self.base_url = config.get("base_url", "https://api.remotepay.co.za")
        self.webhook_secret = config.get("webhook_secret", "")

    def generate_button(self, amount, reference, description="Payment"):
        """One-line payment button embed."""
        return (
            f'<script src="https://cdn.remotepay.co.za/button.js" '
            f'data-merchant="{self.merchant_id}" '
            f'data-amount="{amount}" '
            f'data-reference="{reference}" '
            f'data-description="{description}" '
            f'data-theme="green"></script>'
        )

    def generate_checkout_link(self, order):
        """Hosted checkout link for a cart/order."""
        payload = {
            "merchant_id": self.merchant_id,
            "amount": order["total"],
            "reference": order["order_id"],
            "items": order.get("items", []),
            "customer": order.get("customer", {}),
            "delivery": order.get("delivery", {}),
            "callback_url": order.get("callback_url"),
            "timestamp": datetime.now().isoformat(),
        }
        signature = self._sign(payload)
        encoded = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).decode()
        return f"{self.base_url}/checkout/{encoded}?sig={signature}"

    def generate_payment_link(self, amount, reference,
                              description="", expires_in_hours=24):
        """Shareable payment link (WhatsApp, email, SMS)."""
        payload = {
            "merchant_id": self.merchant_id,
            "amount": amount,
            "reference": reference,
            "description": description,
            "expires_at": datetime.now().timestamp() + expires_in_hours * 3600,
        }
        signature = self._sign(payload)
        encoded = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).decode()
        return f"{self.base_url}/pay/{encoded}?sig={signature}"

    def generate_subscription_button(self, plan_id, amount, interval="monthly"):
        """Subscription signup button for C6 SaaS plans."""
        return (
            f'<script src="https://cdn.remotepay.co.za/subscribe.js" '
            f'data-merchant="{self.merchant_id}" '
            f'data-plan="{plan_id}" '
            f'data-amount="{amount}" '
            f'data-interval="{interval}" '
            f'data-button-text="Subscribe - R{amount}/{interval}"></script>'
        )

    def _sign(self, payload):
        """HMAC-SHA256 signature."""
        message = json.dumps(payload, sort_keys=True).encode()
        return hmac.new(
            self.api_secret.encode(),
            message,
            hashlib.sha256,
        ).hexdigest()

    def verify_webhook(self, body, signature):
        """Verify incoming webhook signature."""
        expected = hmac.new(
            self.webhook_secret.encode(),
            body.encode() if isinstance(body, str) else body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    async def handle_payment_webhook(self, payload, db_pool):
        """Handle payment confirmation webhook."""
        event = payload.get("event")
        data = payload.get("data", {})

        if event == "payment.success":
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE orders
                    SET status = 'PAID', paid_at = NOW(), payment_id = $2
                    WHERE order_id = $1
                """, data["reference"], data["payment_id"])
            return {"status": "OK", "event": event}

        elif event == "payment.failed":
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE orders
                    SET status = 'PAYMENT_FAILED'
                    WHERE order_id = $1
                """, data["reference"])
            return {"status": "OK", "event": event}

        elif event == "subscription.created":
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO subscriptions
                    (business_id, plan_id, status, started_at)
                    VALUES ($1, $2, 'ACTIVE', NOW())
                """, data["business_id"], data["plan_id"])
            return {"status": "OK", "event": event}

        return {"status": "IGNORED", "event": event}


if __name__ == "__main__":
    embed = RemotePayEmbed({
        "merchant_id": "demo_merchant",
        "api_key": "demo_key",
        "api_secret": "demo_secret",
        "webhook_secret": "demo_webhook",
    })

    print("RemotePay Embed ready")
    print()
    print("Sample button:")
    print(embed.generate_button(250.00, "ORDER-001", "Lunch order"))
    print()
    print("Sample payment link:")
    print(embed.generate_payment_link(150.00, "INV-042", "Invoice payment"))
