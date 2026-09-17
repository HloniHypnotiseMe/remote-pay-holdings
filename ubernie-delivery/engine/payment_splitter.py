#!/usr/bin/env python3
"""
Ubernie Payment Splitter
Splits customer payment between shop, rider, and Ubernie.
Uses RemotePay for all money movement.
"""
from datetime import datetime


class PaymentSplitter:
    def __init__(self, remotepay_client):
        self.remotepay = remotepay_client

        # Configurable split rates
        self.rates = {
            "ubernie_platform_fee": 0.15,   # 15%
            "rider_share": 0.85,             # 85% of delivery fee
        }

    def split_order(self, order_amount, delivery_fee):
        """
        Split a customer payment.

        Example:
        - Order: R200 (food)
        - Delivery: R30
        - Total charged: R230
        """
        total = order_amount + delivery_fee

        # RemotePay fee (2.9% + R2)
        remotepay_fee = (total * 0.029) + 2.0
        net = total - remotepay_fee

        # Delivery split
        ubernie_delivery_fee = delivery_fee * self.rates["ubernie_platform_fee"]
        rider_earnings = delivery_fee * self.rates["rider_share"]

        # Shop gets the order amount (minus RemotePay share of order)
        shop_share = order_amount - (order_amount * 0.029)

        return {
            "total_charged": round(total, 2),
            "remotepay_fee": round(remotepay_fee, 2),
            "shop_receives": round(shop_share, 2),
            "rider_receives": round(rider_earnings, 2),
            "ubernie_receives": round(ubernie_delivery_fee, 2),
            "rider_payment_scheduled": "same-day",
            "shop_payment_scheduled": "T+2",
        }

    async def process_delivery_payment(self, order_id, order_amount,
                                       delivery_fee, shop_account,
                                       rider_account):
        """Execute the split payment."""
        split = self.split_order(order_amount, delivery_fee)

        # Charge customer
        charge = await self.remotepay.charge(
            order_id=order_id,
            amount=split["total_charged"],
        )

        if not charge["success"]:
            return {"error": "Payment failed", "details": charge}

        # Pay shop (T+2)
        shop_payout = await self.remotepay.schedule_payout(
            account=shop_account,
            amount=split["shop_receives"],
            schedule="T+2",
        )

        # Pay rider (same-day)
        rider_payout = await self.remotepay.schedule_payout(
            account=rider_account,
            amount=split["rider_receives"],
            schedule="same-day",
        )

        return {
            "order_id": order_id,
            "split": split,
            "shop_payout_id": shop_payout["id"],
            "rider_payout_id": rider_payout["id"],
            "status": "COMPLETED",
            "timestamp": datetime.now().isoformat(),
        }


if __name__ == "__main__":
    print("Payment Splitter ready")
