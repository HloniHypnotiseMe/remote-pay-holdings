#!/usr/bin/env python3
"""
C6 Website Department — Site Renderer
Renders generated site config into deployable HTML/CSS/JS.
"""
from pathlib import Path


class SiteRenderer:
    def __init__(self, site_config, output_dir):
        self.site = site_config
        self.output = Path(output_dir)
        self.output.mkdir(parents=True, exist_ok=True)

    def render(self):
        """Render all pages."""
        self._render_index()
        for page_name in ("menu", "shop", "products", "services", "about", "contact"):
            page = self.site["pages"].get(page_name)
            if page:
                self._render_simple_page(page_name, page)
        self._render_checkout()
        self._render_assets()
        self._render_delivery_widget()
        return {"rendered_to": str(self.output),
                "files": [str(p.name) for p in self.output.glob("*.html")]}

    def _render_index(self):
        home = self.site["pages"].get("home", {})
        hero = home.get("hero", {})
        config = self.site["config"]

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config['site_name']} — {config['tagline']}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="/assets/remotepay.js"></script>
    <script src="/assets/ubernie-delivery.js"></script>
    <script src="/assets/cart.js"></script>
    <style>
        :root {{ --primary: {config['primary_color']}; }}
        .btn-primary {{ background: var(--primary); color: white; }}
        .btn-primary:hover {{ opacity: 0.9; }}
    </style>
</head>
<body class="bg-gray-50">
    <nav class="bg-white shadow-sm sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
            <h1 class="text-2xl font-bold" style="color: var(--primary);">{config['site_name']}</h1>
            <div class="flex gap-6 items-center">
                <a href="index.html" class="hover:opacity-70">Home</a>
                <a href="menu.html" class="hover:opacity-70">Menu</a>
                <a href="about.html" class="hover:opacity-70">About</a>
                <a contact.html" class="hover:opacity-70">Contact</a>
                <button onclick="openCart()" class="btn-primary px-4 py-2 rounded-lg">
                    Cart <span id="cart-count">0</span>
                </button>
            </div>
        </div>
    </nav>

    <section class="py-20 px-4" style="background: linear-gradient(135deg, {config['primary_color']}22, transparent);">
        <div class="max-w-4xl mx-auto text-center">
            <h2 class="text-5xl font-bold mb-4">{hero.get('headline', config['site_name'])}</h2>
            <p class="text-xl text-gray-600 mb-8">{hero.get('subheadline', '')}</p>
            <a href="menu.html" class="btn-primary px-8 py-4 rounded-lg text-lg font-bold inline-block">
                {hero.get('cta', 'Order Now')}
            </a>
        </div>
    </section>

    <section class="py-16 px-4 bg-white">
        <div class="max-w-7xl mx-auto">
            <h3 class="text-3xl font-bold mb-8 text-center">Featured</h3>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="bg-gray-50 rounded-xl p-6 text-center">
                    <p class="text-gray-500">Products will appear here once added.</p>
                </div>
            </div>
        </div>
    </section>

    <section class="py-16 px-4" style="background: var(--primary); color: white;">
        <div class="max-w-4xl mx-auto text-center">
            <h3 class="text-3xl font-bold mb-4">🛵 Delivery Available</h3>
            <p class="text-lg mb-6">Get it delivered to your door in 30-45 minutes.</p>
            <button onclick="openDeliveryWidget()" class="bg-white text-gray-900 px-8 py-3 rounded-lg font-bold">
                Check Delivery
            </button>
        </div>
    </section>

    <footer class="bg-gray-900 text-white py-12 px-4">
        <div class="max-w-7xl mx-auto text-center">
            <p>{config['site_name']}</p>
            <p class="text-sm text-gray-400 mt-2">
                {config['contact'].get('phone', '')} · {config['contact'].get('email', '')}
            </p>
            <p class="text-xs text-gray-500 mt-4">Powered by RemotePay · C6 SaaS</p>
        </div>
    </footer>

    <div id="cart-modal" class="hidden fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
        <div class="bg-white rounded-2xl p-8 max-w-md w-full mx-4">
            <h3 class="text-2xl font-bold mb-4">Your Cart</h3>
            <div id="cart-items"></div>
            <div class="mt-6 flex justify-between font-bold text-lg">
                <span>Total</span>
                <span id="cart-total">R0.00</span>
            </div>
            <button onclick="checkout()" class="btn-primary w-full py-4 rounded-lg mt-4 font-bold">
                Checkout with RemotePay
            </button>
            <button onclick="closeCart()" class="w-full py-2 mt-2 text-gray-500">Close</button>
        </div>
    </div>
</body>
</html>"""

        (self.output / "index.html").write_text(html, encoding="utf-8")

    def _render_simple_page(self, name, config):
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config.get('title', name)} — {self.site['config']['site_name']}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="/assets/cart.js"></script>
    <style>:root {{ --primary: {self.site['config']['primary_color']}; }}
    .btn-primary {{ background: var(--primary); color: white; }}</style>
</head>
<body class="bg-gray-50">
    <nav class="bg-white shadow-sm px-4 py-4">
        <div class="max-w-7xl mx-auto flex justify-between">
            <a href="index.html" class="text-xl font-bold">{self.site['config']['site_name']}</a>
            <a href="index.html" class="text-gray-600">← Back</a>
        </div>
    </nav>
    <main class="max-w-7xl mx-auto px-4 py-12">
        <h1 class="text-4xl font-bold mb-8">{config.get('title', name)}</h1>
        <div class="bg-white rounded-xl p-8 shadow-sm">
            <p class="text-gray-500">Content for {config.get('title', name)} will go here.</p>
        </div>
    </main>
</body>
</html>"""
        (self.output / f"{name}.html").write_text(html, encoding="utf-8")

    def _render_checkout(self):
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Checkout</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="/assets/remotepay.js"></script>
</head>
<body class="bg-gray-50">
    <div class="max-w-2xl mx-auto py-12 px-4">
        <h1 class="text-3xl font-bold mb-8">Checkout</h1>
        <div class="bg-white rounded-xl p-6 shadow-sm mb-6">
            <h3 class="font-bold mb-4">Delivery Options</h3>
            <label class="flex items-center gap-3 p-3 border rounded-lg mb-2">
                <input type="radio" name="delivery" value="ubernie" checked>
                <span>🛵 Ubernie Delivery (30-45 min)</span>
            </label>
            <label class="flex items-center gap-3 p-3 border rounded-lg">
                <input type="radio" name="delivery" value="pickup">
                <span>🏪 Pickup</span>
            </label>
        </div>
        <button onclick="payWithRemotePay()" class="w-full bg-green-600 text-white py-4 rounded-lg font-bold">
            Pay with RemotePay
        </button>
    </div>
</body>
</html>"""
        (self.output / "checkout.html").write_text(html, encoding="utf-8")

    def _render_assets(self):
        assets_dir = self.output / "assets"
        assets_dir.mkdir(exist_ok=True)

        remotepay_js = """// RemotePay Embed
async function payWithRemotePay() {
    const cart = JSON.parse(localStorage.getItem('cart') || '[]');
    const total = cart.reduce((s, i) => s + i.price * i.qty, 0);
    alert('Redirecting to RemotePay checkout... Total: R' + total.toFixed(2));
    // In production: fetch('/api/remotepay/create-payment') and redirect
}
"""
        (assets_dir / "remotepay.js").write_text(remotepay_js, encoding="utf-8")

        cart_js = """// Shopping Cart
let cart = JSON.parse(localStorage.getItem('cart') || '[]');

function addToCart(id, name, price) {
    const existing = cart.find(i => i.id === id);
    if (existing) existing.qty++;
    else cart.push({id, name, price, qty: 1});
    localStorage.setItem('cart', JSON.stringify(cart));
    updateCartCount();
    alert(name + ' added to cart');
}

function updateCartCount() {
    const count = cart.reduce((s, i) => s + i.qty, 0);
    const el = document.getElementById('cart-count');
    if (el) el.textContent = count;
}

function openCart() {
    const modal = document.getElementById('cart-modal');
    if (modal) modal.classList.remove('hidden');
    renderCart();
}

function closeCart() {
    const modal = document.getElementById('cart-modal');
    if (modal) modal.classList.add('hidden');
}

function renderCart() {
    const items = document.getElementById('cart-items');
    const total = document.getElementById('cart-total');
    if (!items) return;
    items.innerHTML = cart.map(i =>
        '<div class="flex justify-between py-2 border-b"><span>' + i.name + ' x' + i.qty + '</span><span>R' + (i.price * i.qty).toFixed(2) + '</span></div>'
    ).join('');
    const sum = cart.reduce((s, i) => s + i.price * i.qty, 0);
    if (total) total.textContent = 'R' + sum.toFixed(2);
}

function checkout() { window.location.href = 'checkout.html'; }
updateCartCount();
"""
        (assets_dir / "cart.js").write_text(cart_js, encoding="utf-8")

    def _render_delivery_widget(self):
        js = """// Ubernie Delivery Widget
function openDeliveryWidget() {
    const area = prompt('Enter your area:');
    if (!area) return;
    alert('Checking delivery for: ' + area + '\\n(In production: fetch from /api/delivery/check)');
}
"""
        (self.output / "assets" / "ubernie-delivery.js").write_text(js, encoding="utf-8")


if __name__ == "__main__":
    from site_generator import SiteGenerator
    import tempfile

    demo_shop = {
        "id": "demo-001",
        "name": "Mama Thandi's Kitchen",
        "industry": "restaurant",
        "address": "123 Vilakazi St, Soweto",
        "phone": "+27110000000",
        "email": "hello@mamathandi.co.za",
        "tagline": "Home-cooked meals, delivered hot",
    }
    gen = SiteGenerator(demo_shop)
    config = gen.generate()

    with tempfile.TemporaryDirectory() as tmpdir:
        renderer = SiteRenderer(config, tmpdir)
        result = renderer.render()
        print("Site Renderer ready")
        print(f"Rendered to: {result['rendered_to']}")
        print(f"Files: {result['files']}")
