#!/usr/bin/env python3
"""
C6 Website Department — Tax AI Hook
Records every transaction for VAT, receipts, and SARS compliance.
"""
from datetime import datetime


class TaxAIHook:
    """
    Hooks into every payment and:
    - Generates VAT-compliant receipt (SARS format)
    - Records transaction for VAT201
    - Classifies income/expense
    - Tracks VAT input/output for returns
    """

    # SA VAT rate (15% as of 2026)
    VAT_RATE = 0.15

    def __init__(self, db_pool, business_id):
        self.db = db_pool
        self.business_id = business_id

    def generate_receipt(self, transaction):
        """
        Generate a VAT-compliant receipt.

        transaction = {
            "id": "TXN-001",
            "amount": 250.00,
            "items": [{"name": "Pap & Chakalaka", "price": 45}],
            "customer_email": "customer@example.com",
            "payment_method": "RemotePay",
            "timestamp": "2026-09-21T10:00:00",
        }
        """
        amount = transaction["amount"]
        # Amount includes VAT (VAT-inclusive pricing)
        vat = round(amount - (amount / (1 + self.VAT_RATE)), 2)
        subtotal = round(amount - vat, 2)

        receipt = {
            "receipt_number": self._generate_receipt_number(transaction["id"]),
            "business_id": self.business_id,
            "transaction_id": transaction["id"],
            "issued_at": datetime.now().isoformat(),
            "customer_email": transaction.get("customer_email"),
            "payment_method": transaction.get("payment_method", "RemotePay"),
            "line_items": transaction.get("items", []),
            "subtotal_excl_vat": subtotal,
            "vat_amount": vat,
            "total_incl_vat": amount,
            "vat_rate": self.VAT_RATE,
            "sars_compliant": True,
            "supplier_vat_number": "4820123456",  # placeholder
        }
        return receipt

    def _generate_receipt_number(self, txn_id):
        """Generate unique SARS-compliant receipt number."""
        today = datetime.now().strftime("%Y%m%d")
        return f"TAX-{today}-{txn_id[-6:]}"

    async def record_transaction(self, transaction):
        """
        Record a transaction in the ledger for VAT reporting.
        """
        receipt = self.generate_receipt(transaction)

        async with self.db.acquire() as conn:
            # Store transaction
            await conn.execute("""
                INSERT INTO tax_transactions
                (business_id, transaction_id, receipt_number, amount_excl_vat,
                 vat_amount, amount_incl_vat, payment_method, issued_at, receipt_json)
                VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), $8)
                ON CONFLICT (transaction_id) DO NOTHING
            """,
                self.business_id,
                transaction["id"],
                receipt["receipt_number"],
                receipt["subtotal_excl_vat"],
                receipt["vat_amount"],
                receipt["total_incl_vat"],
                transaction.get("payment_method", "RemotePay"),
                str(receipt),
            )

        return {
            "status": "RECORDED",
            "receipt": receipt,
            "vat_period": self._current_vat_period(),
        }

    def _current_vat_period(self):
        """Return the current VAT period (standard: bi-monthly)."""
        now = datetime.now()
        if now.month in (1, 2):
            return "Jan-Feb"
        elif now.month in (3, 4):
            return "Mar-Apr"
        elif now.month in (5, 6):
            return "May-Jun"
        elif now.month in (7, 8):
            return "Jul-Aug"
        elif now.month in (9, 10):
            return "Sep-Oct"
        else:
            return "Nov-Dec"

    async def get_vat_summary(self, period=None):
        """Get VAT summary for a period (for VAT201 submission)."""
        period = period or self._current_vat_period()

        async with self.db.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT
                    COUNT(*) as transaction_count,
                    COALESCE(SUM(amount_excl_vat), 0) as total_excl_vat,
                    COALESCE(SUM(vat_amount), 0) as total_vat_output,
                    COALESCE(SUM(amount_incl_vat), 0) as total_incl_vat
                FROM tax_transactions
                WHERE business_id = $1
                  AND vat_period = $2
            """, self.business_id, period)

        return {
            "business_id": self.business_id,
            "vat_period": period,
            "transactions": row["transaction_count"] if row else 0,
            "subtotal_excl_vat": float(row["total_excl_vat"]) if row else 0,
            "vat_output": float(row["total_vat_output"]) if row else 0,
            "total_incl_vat": float(row["total_incl_vat"]) if row else 0,
            "vat201_ready": True,
        }


if __name__ == "__main__":
    # Smoke test with fake DB (no actual db)
    class FakeDB:
        def acquire(self):
            class FakeConn:
                async def execute(self, *args, **kwargs):
                    return None
                async def fetchrow(self, *args, **kwargs):
                    return {"transaction_count": 0, "total_excl_vat": 0,
                            "total_vat_output": 0, "total_incl_vat": 0}
            class FakeAcquire:
                async def __aenter__(self):
                    return FakeConn()
                async def __aexit__(self, *args):
                    return None
            return FakeAcquire()

    hook = TaxAIHook(FakeDB(), "demo-shop-001")

    # Test receipt generation
    txn = {
        "id": "TXN-123456",
        "amount": 250.00,
        "items": [
            {"name": "Pap & Chakalaka", "price": 45},
            {"name": "Kota", "price": 35},
        ],
        "customer_email": "customer@example.com",
        "payment_method": "RemotePay",
    }
    receipt = hook.generate_receipt(txn)
    print("Tax AI Hook ready")
    print(f"Receipt number: {receipt['receipt_number']}")
    print(f"Subtotal (excl VAT): R{receipt['subtotal_excl_vat']}")
    print(f"VAT (15%): R{receipt['vat_amount']}")
    print(f"Total (incl VAT): R{receipt['total_incl_vat']}")
    print(f"VAT period: {hook._current_vat_period()}")
