#!/usr/bin/env python3
"""
C6 Website Department — Shop Intake
Collects everything needed to build a shop's website.
"""
import sys
import os
from datetime import datetime
from pathlib import Path

# Make sure we can import from builder/ and hosting/ regardless of cwd
_HERE = Path(__file__).parent
_WEB = _HERE.parent
sys.path.insert(0, str(_WEB / "builder"))
sys.path.insert(0, str(_WEB / "hosting"))


class ShopIntake:
    """
    Intake flow:
    1. Shop owner fills form (or we scrape what we can)
    2. AI fills gaps (taglines, categories, story)
    3. Shop uploads logo + product photos
    4. Site generated in 60 seconds
    5. Shop reviews and approves
    6. Deployed to subdomain
    """

    REQUIRED_FIELDS = [
        "business_name",
        "owner_name",
        "email",
        "phone",
        "address",
        "industry",
    ]

    def __init__(self, db_pool=None):
        self.db = db_pool

    async def start_intake(self, business_id, business_data=None):
        """Start intake for a business (may come from Ubernie scrape)."""
        business = business_data or {}
        return {
            "business_id": business_id,
            "prefilled": {
                "business_name": business.get("name"),
                "address": business.get("address"),
                "phone": business.get("phone"),
                "email": business.get("email"),
                "industry": business.get("industry"),
            },
            "missing": self._get_missing_fields(business),
            "intake_url": f"https://c6.remotepay.co.za/intake/{business_id}",
        }

    async def submit_intake(self, business_id, data):
        """Shop submits intake form."""
        missing = [f for f in self.REQUIRED_FIELDS if not data.get(f)]
        if missing:
            return {"error": "Missing required fields", "missing": missing}

        enriched = await self._enrich_with_ai(data)
        return await self._generate_site(business_id, enriched)

    async def _enrich_with_ai(self, data):
        """Fill gaps (taglines, story) with sensible defaults."""
        enriched = dict(data)

        if not enriched.get("tagline"):
            enriched["tagline"] = self._ai_tagline(data)

        if not enriched.get("story"):
            enriched["story"] = self._ai_story(data)

        if not enriched.get("categories"):
            enriched["categories"] = ["Featured", "Popular", "New"]

        return enriched

    def _ai_tagline(self, data):
        industry = (data.get("industry") or "business").lower()
        taglines = {
            "restaurant": "Authentic flavors, delivered fresh",
            "retail": "Quality products, unbeatable prices",
            "pharmacy": "Your health, our priority",
            "salon": "Look good, feel great",
            "services": "Reliable service, every time",
        }
        return taglines.get(industry, f"Welcome to {data['business_name']}")

    def _ai_story(self, data):
        return f"{data['business_name']} has been proudly serving the community."

    async def _generate_site(self, business_id, enriched_data):
        """Run the full pipeline: generate config -> render HTML."""
        from site_generator import SiteGenerator
        from site_renderer import SiteRenderer

        shop_data = {
            "id": business_id,
            "name": enriched_data["business_name"],
            "industry": enriched_data.get("industry", "retail"),
            "address": enriched_data["address"],
            "phone": enriched_data.get("phone"),
            "email": enriched_data.get("email"),
            "tagline": enriched_data.get("tagline"),
            "story": enriched_data.get("story"),
            "menu_items": enriched_data.get("menu_items", []),
            "products": enriched_data.get("products", []),
            "services": enriched_data.get("services", []),
            "remotepay_merchant_id": f"rp_{business_id}",
            "ubernie_shop_id": business_id,
        }

        generator = SiteGenerator(shop_data)
        config = generator.generate()

        # Windows-safe output dir under user's temp
        output_dir = Path(os.environ.get("TEMP", "/tmp")) / "c6-sites" / business_id
        renderer = SiteRenderer(config, output_dir)
        result = renderer.render()

        return {
            "business_id": business_id,
            "status": "SITE_GENERATED",
            "preview_url": f"https://preview.c6.remotepay.co.za/{business_id}",
            "rendered_to": result["rendered_to"],
            "files": result["files"],
            "next_step": "Shop reviews and approves",
        }

    def _get_missing_fields(self, business):
        return [f for f in self.REQUIRED_FIELDS if not business.get(f)]


if __name__ == "__main__":
    import asyncio

    async def smoke_test():
        intake = ShopIntake()

        # Simulate a scraped business from Ubernie
        scraped = {
            "name": "Mama Thandi's Kitchen",
            "address": "123 Vilakazi St, Soweto",
            "phone": "+27110000000",
            "email": "hello@mamathandi.co.za",
            "industry": "restaurant",
        }

        print("Shop Intake ready")
        print()

        # Step 1: start intake
        started = await intake.start_intake("demo-001", scraped)
        print(f"Started intake: {started['business_id']}")
        print(f"Missing fields: {started['missing']}")
        print()

        # Step 2: submit intake (with the missing owner_name filled in)
        submitted = await intake.submit_intake("demo-001", {
            "business_name": scraped["name"],
            "owner_name": "Thandi Mokoena",
            "email": scraped["email"],
            "phone": scraped["phone"],
            "address": scraped["address"],
            "industry": scraped["industry"],
        })
        print(f"Status: {submitted['status']}")
        print(f"Rendered to: {submitted['rendered_to']}")
        print(f"Files: {submitted['files']}")

    asyncio.run(smoke_test())
