#!/usr/bin/env python3
"""
C6 Web Department — FastAPI Server
HTTP layer for the site generation pipeline.
"""
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# --- Make sibling packages importable ---
_HERE = Path(__file__).parent
_WEB = _HERE.parent
sys.path.insert(0, str(_WEB / "builder"))
sys.path.insert(0, str(_WEB / "onboarding"))
sys.path.insert(0, str(_WEB / "integration"))

from shop_intake import ShopIntake
from remotepay_embed import RemotePayEmbed
from taxai_hook import TaxAIHook

# --- App setup ---
app = FastAPI(title="C6 Web Department", version="0.1.0")

# Where generated sites live (Windows-safe)
SITES_ROOT = Path(os.environ.get("TEMP", "/tmp")) / "c6-sites"
SITES_ROOT.mkdir(parents=True, exist_ok=True)


# --- Request models ---
class ShopIntakeRequest(BaseModel):
    business_id: str
    business_name: str
    owner_name: str
    email: str
    phone: str
    address: str
    industry: str
    tagline: Optional[str] = None
    story: Optional[str] = None


class PaymentLinkRequest(BaseModel):
    amount: float
    reference: str
    description: str = ""


# --- Routes ---

@app.get("/")
async def root():
    return {
        "service": "C6 Web Department",
        "version": "0.1.0",
        "status": "running",
        "endpoints": [
            "POST /api/intake              - create a shop site",
            "GET  /api/sites               - list all generated sites",
            "GET  /sites/{business_id}/    - serve a generated site",
            "POST /api/remotepay/link      - generate a payment link",
            "GET  /api/taxai/period        - current VAT period",
        ],
    }


@app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.now().isoformat()}


@app.post("/api/intake")
async def create_site(req: ShopIntakeRequest):
    """Run the full pipeline: intake -> generate -> render."""
    intake = ShopIntake()
    data = {
        "business_name": req.business_name,
        "owner_name": req.owner_name,
        "email": req.email,
        "phone": req.phone,
        "address": req.address,
        "industry": req.industry,
        "tagline": req.tagline,
        "story": req.story,
    }
    result = await intake.submit_intake(req.business_id, data)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    return result


@app.get("/api/sites")
async def list_sites():
    """List all generated sites."""
    if not SITES_ROOT.exists():
        return {"sites": []}
    sites = []
    for d in SITES_ROOT.iterdir():
        if d.is_dir():
            files = [f.name for f in d.glob("*.html")]
            sites.append({
                "business_id": d.name,
                "path": str(d),
                "html_files": files,
                "url": f"/sites/{d.name}/",
            })
    return {"count": len(sites), "sites": sites}


@app.get("/sites/{business_id}/", response_class=HTMLResponse)
async def serve_site_index(business_id: str):
    """Serve the generated index.html for a shop."""
    index = SITES_ROOT / business_id / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail=f"Site '{business_id}' not found. Create it via POST /api/intake")
    return index.read_text(encoding="utf-8")


@app.get("/sites/{business_id}/{page}", response_class=HTMLResponse)
async def serve_site_page(business_id: str, page: str):
    """Serve a specific page (menu.html, contact.html, etc.)."""
    if not page.endswith(".html"):
        page = f"{page}.html"
    target = SITES_ROOT / business_id / page
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"Page '{page}' not found")
    return target.read_text(encoding="utf-8")


@app.post("/api/remotepay/link")
async def make_payment_link(req: PaymentLinkRequest):
    """Generate a RemotePay payment link for an order."""
    embed = RemotePayEmbed({
        "merchant_id": "demo_merchant",
        "api_key": "demo_key",
        "api_secret": "demo_secret",
        "webhook_secret": "demo_webhook",
    })
    link = embed.generate_payment_link(req.amount, req.reference, req.description)
    return {"status": "ok", "link": link}


@app.get("/api/taxai/period")
async def current_vat_period():
    """Get the current VAT period."""
    hook = TaxAIHook(db_pool=None, business_id="system")
    return {"vat_period": hook._current_vat_period(),
            "vat_rate": hook.VAT_RATE}


# --- Mount static assets (if any exist) ---
# Uncomment when we add a real dashboard folder
# app.mount("/static", StaticFiles(directory=_HERE / "static"), name="static")


if __name__ == "__main__":
    import uvicorn
    print("C6 Web Department Server")
    print("=" * 40)
    print(f"Sites root: {SITES_ROOT}")
    print(f"Docs:  http://localhost:8000/docs")
    print(f"Root:  http://localhost:8000/")
    print("=" * 40)
    uvicorn.run(app, host="127.0.0.1", port=8000)
