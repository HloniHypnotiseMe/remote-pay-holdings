#!/usr/bin/env python3
"""
Ubernie Delivery Matching Engine
Connects delivery jobs to available riders.
"""
from datetime import datetime
import math


class DeliveryMatcher:
    def __init__(self, db_pool):
        self.db = db_pool

    async def create_delivery_job(self, order_id, shop, customer):
        """Create a delivery job from a customer order."""
        return {
            "order_id": order_id,
            "shop_id": shop["id"],
            "pickup": {
                "address": shop["address"],
                "lat": shop["latitude"],
                "lng": shop["longitude"],
            },
            "dropoff": {
                "address": customer["address"],
                "lat": customer["latitude"],
                "lng": customer["longitude"],
            },
            "status": "PENDING",
            "created_at": datetime.now().isoformat(),
        }

    async def find_best_rider(self, job):
        """Find the best rider using scoring algorithm."""
        riders = await self._get_available_riders(job["pickup"]["lat"],
                                                  job["pickup"]["lng"])

        scored = []
        for rider in riders:
            score = self._score_rider(rider, job)
            scored.append({"rider": rider, "score": score})

        scored.sort(key=lambda x: x["score"], reverse=True)

        if not scored:
            return {"error": "No riders available"}

        return {
            "job_id": job["order_id"],
            "assigned_rider": scored[0]["rider"],
            "score": scored[0]["score"],
            "alternatives": scored[1:3],
        }

    def _score_rider(self, rider, job):
        """
        Score a rider for a job (0-100).
        Factors: distance, rating, current load, acceptance rate.
        """
        # Distance factor (max 40 pts)
        distance = self._haversine(
            rider["lat"], rider["lng"],
            job["pickup"]["lat"], job["pickup"]["lng"]
        )
        distance_score = max(0, 40 - (distance * 4))  # 10km = 0 pts

        # Rating factor (max 20 pts)
        rating_score = (rider["rating"] / 5.0) * 20

        # Load factor (max 20 pts) — fewer current jobs = better
        load_score = max(0, 20 - (rider["current_jobs"] * 5))

        # Acceptance rate (max 20 pts)
        acceptance_score = rider["acceptance_rate"] * 20

        return distance_score + rating_score + load_score + acceptance_score

    async def _get_available_riders(self, lat, lng):
        """Get riders within 10km of pickup."""
        async with self.db.acquire() as conn:
            rows = await conn.fetch("""
                SELECT r.id, r.name, r.lat, r.lng, r.rating,
                       r.current_jobs, r.acceptance_rate
                FROM riders r
                WHERE r.status = 'AVAILABLE'
                AND (
                    6371 * acos(
                        cos(radians($1)) * cos(radians(r.lat))
                        * cos(radians(r.lng) - radians($2))
                        + sin(radians($1)) * sin(radians(r.lat))
                    )
                ) < 10
            """, lat, lng)
        return [dict(r) for r in rows]

    def _haversine(self, lat1, lng1, lat2, lng2):
        """Distance in km between two coordinates."""
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = (math.sin(dlat/2)**2
             + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
             * math.sin(dlng/2)**2)
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


if __name__ == "__main__":
    print("Delivery Matcher ready")
