#!/usr/bin/env python3
"""
C6 Website Department — Ubernie Delivery Widget
Injects delivery functionality into any generated site.
"""
from datetime import datetime


class UbernieWidget:
    """
    Generates:
    - Floating delivery button
    - Area checker
    - Delivery fee display
    - Waitlist signup fallback (if area not active)
    """

    def __init__(self, config):
        self.shop_id = config["shop_id"]
        self.base_url = config.get("base_url", "https://api.ubernie.co.za")
        self.shop_lat = config.get("lat")
        self.shop_lng = config.get("lng")

    def generate_widget_html(self):
        """Return the full widget HTML + inline JS."""
        return f"""<div id="ubernie-widget" style="
    position: fixed; bottom: 20px; right: 20px; z-index: 1000;
    font-family: system-ui, -apple-system, sans-serif;">
    <button onclick="ubernieOpen()" style="
        background: #16a34a; color: white; border: none;
        padding: 16px 24px; border-radius: 50px; cursor: pointer;
        font-size: 16px; font-weight: bold;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
        🛵 Delivery Available
    </button>
</div>

<div id="ubernie-modal" style="
    display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5);
    z-index: 1001; align-items: center; justify-content: center;">
    <div style="
        background: white; border-radius: 16px; padding: 32px;
        max-width: 400px; width: 90%;">
        <h3 style="margin: 0 0 16px; font-size: 22px;">Check Delivery</h3>
        <input id="ubernie-area" placeholder="Enter your area or address"
            style="width: 100%; padding: 12px; border: 1px solid #ddd;
            border-radius: 8px; font-size: 16px; margin-bottom: 12px;
            box-sizing: border-box;">
        <button onclick="ubernieCheck()" style="
            width: 100%; background: #16a34a; color: white;
            border: none; padding: 14px; border-radius: 8px;
            font-size: 16px; font-weight: bold; cursor: pointer;">
            Check Availability
        </button>
        <div id="ubernie-result" style="margin-top: 16px;"></div>
        <button onclick="ubernieClose()" style="
            width: 100%; background: transparent; color: #666;
            border: none; padding: 12px; margin-top: 8px; cursor: pointer;">
            Close
        </button>
    </div>
</div>

<script>
const UBERNIE_CONFIG = {{
    shop_id: "{self.shop_id}",
    base_url: "{self.base_url}"
}};

function ubernieOpen() {{
    document.getElementById('ubernie-modal').style.display = 'flex';
}}

function ubernieClose() {{
    document.getElementById('ubernie-modal').style.display = 'none';
}}

async function ubernieCheck() {{
    const area = document.getElementById('ubernie-area').value.trim();
    if (!area) return;
    const result = document.getElementById('ubernie-result');
    result.innerHTML = 'Checking...';
    try {{
        const res = await fetch(
            UBERNIE_CONFIG.base_url + '/api/delivery/check?shop_id='
            + UBERNIE_CONFIG.shop_id + '&area=' + encodeURIComponent(area)
        );
        const data = await res.json();
        if (data.available) {{
            result.innerHTML = '<div style="background:#f0fdf4;padding:16px;border-radius:8px;">'
                + '<p style="color:#16a34a;font-weight:bold;margin:0 0 8px;">✅ Delivery available!</p>'
                + '<p style="margin:0;font-size:14px;">Fee: <strong>R' + data.fee
                + '</strong><br>ETA: <strong>' + data.eta_minutes + ' min</strong></p>'
                + '<button onclick="ubernieProceed()" style="width:100%;background:#16a34a;color:white;'
                + 'border:none;padding:12px;border-radius:8px;margin-top:12px;font-weight:bold;cursor:pointer;">'
                + 'Continue to Checkout</button></div>';
        }} else {{
            result.innerHTML = '<div style="background:#fef3c7;padding:16px;border-radius:8px;">'
                + '<p style="color:#92400e;font-weight:bold;margin:0 0 8px;">⏳ Not yet available in ' + area + '</p>'
                + '<p style="margin:0;font-size:14px;">We launch delivery zones when 15 shops sign up. '
                + 'Join the waitlist and we\\'ll notify you.</p></div>';
        }}
    }} catch (err) {{
        result.innerHTML = '<p style="color:red;">Error: ' + err.message + '</p>';
    }}
}}

function ubernieProceed() {{
    window.location.href = '/checkout.html';
}}
</script>"""

    def inject_into_html(self, html_path):
        """Inject widget into an existing HTML file."""
        from pathlib import Path
        p = Path(html_path)
        html = p.read_text(encoding="utf-8")
        widget = self.generate_widget_html()
        if "</body>" in html:
            html = html.replace("</body>", widget + "\n</body>")
        else:
            html += widget
        p.write_text(html, encoding="utf-8")

    async def check_delivery(self, area, db_pool):
        """API: check if delivery is available in area."""
        async with db_pool.acquire() as conn:
            zone = await conn.fetchrow("""
                SELECT * FROM delivery_zones
                WHERE area = $1 AND status = 'ACTIVE'
            """, area)
            if not zone:
                return {"available": False, "reason": "zone_not_active"}
            return {"available": True, "fee": 25, "eta_minutes": 35, "zone": area}


if __name__ == "__main__":
    # Smoke test
    widget = UbernieWidget({
        "shop_id": "demo-shop-001",
        "base_url": "https://api.ubernie.co.za",
    })
    html = widget.generate_widget_html()
    print("Ubernie Widget ready")
    print(f"Generated HTML length: {len(html)} chars")
    print(f"Contains delivery button: {'Delivery Available' in html}")
    print(f"Contains area checker: {'ubernieCheck' in html}")
