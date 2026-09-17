#!/usr/bin/env python3
"""
Ubernie Delivery Waitlist Engine
Aggregates shop demand for delivery zones.
"""
from datetime import datetime, timedelta
from pathlib import Path
import json
import asyncpg


class DeliveryWaitlist:
    def __init__(self, db_pool):
        self.db = db_pool
        self.thresholds = {
            "min_shops": 15,
            "min_riders": 3,
            "min_daily_orders": 50,  # Estimated from shop data
        }

    async def add_shop(self, business_id, area, industry, estimated_orders):
        """Add a shop to the delivery waitlist."""
        async with self.db.acquire() as conn:
            await conn.execute("""
                INSERT INTO delivery_waitlist
                (business_id, area, industry, estimated_daily_orders, status)
                VALUES ($1, $2, $3, $4, 'WAITING')
                ON CONFLICT (business_id) DO UPDATE
                SET area = $2, estimated_daily_orders = $4
            """, business_id, area, industry, estimated_orders)

        return await self.check_zone_readiness(area)

    async def check_zone_readiness(self, area):
        """Check if a zone is ready to activate."""
        async with self.db.acquire() as conn:
            shops = await conn.fetchrow("""
                SELECT COUNT(*) as count,
                       SUM(estimated_daily_orders) as total_orders
                FROM delivery_waitlist
                WHERE area = $1 AND status = 'WAITING'
            """, area)

            riders = await conn.fetchrow("""
                SELECT COUNT(*) as count
                FROM riders
                WHERE area = $1 AND status = 'AVAILABLE'
            """, area)

        shop_count = shops["count"] or 0
        rider_count = riders["count"] or 0
        order_count = shops["total_orders"] or 0

        ready = (
            shop_count >= self.thresholds["min_shops"]
            and rider_count >= self.thresholds["min_riders"]
        )

        return {
            "area": area,
            "shops": shop_count,
            "riders": rider_count,
            "estimated_orders": order_count,
            "ready_to_activate": ready,
            "progress_pct": round(
                min(shop_count / self.thresholds["min_shops"], 1.0) * 100, 1
            ),
        }

    async def activate_zone(self, area):
        """Activate a delivery zone when thresholds are met."""
        readiness = await self.check_zone_readiness(area)

        if not readiness["ready_to_activate"]:
            return {"error": "Thresholds not met", "readiness": readiness}

        async with self.db.acquire() as conn:
            # Mark zone active
            await conn.execute("""
                INSERT INTO delivery_zones (area, activated_at, status)
                VALUES ($1, NOW(), 'ACTIVE')
                ON CONFLICT (area) DO UPDATE
                SET status = 'ACTIVE', activated_at = NOW()
            """, area)

            # Notify all shops
            shops = await conn.fetch("""
                SELECT b.email, b.name
                FROM delivery_waitlist w
                JOIN businesses b ON b.id = w.business_id
                WHERE w.area = $1 AND w.status = 'WAITING'
            """, area)

        # Trigger n8n webhook for notification sequence
        import requests
        requests.post("http://localhost:5678/webhook/delivery-zone-activated", json={
            "area": area,
            "shops": [dict(s) for s in shops],
        })

        return {
            "status": "ACTIVATED",
            "area": area,
            "shops_notified": len(shops),
        }

    async def get_all_zones_status(self):
        """Get status of all zones."""
        async with self.db.acquire() as conn:
            rows = await conn.fetch("""
                SELECT area,
                       COUNT(*) as shops,
                       SUM(estimated_daily_orders) as orders
                FROM delivery_waitlist
                WHERE status = 'WAITING'
                GROUP BY area
                ORDER BY shops DESC
            """)

        return [dict(r) for r in rows]


if __name__ == "__main__":
    print("Delivery Waitlist Engine ready")
