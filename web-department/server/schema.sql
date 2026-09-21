-- C6 Web Department — Database Schema
-- Database: remotepay_holdings
-- All statements are idempotent (IF NOT EXISTS)

-- ============================================================
-- 1. BUSINESSES (directory + shop records)
-- ============================================================
CREATE TABLE IF NOT EXISTS businesses (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    industry        TEXT,
    email           TEXT,
    phone           TEXT,
    address         TEXT,
    latitude        DOUBLE PRECISION,
    longitude       DOUBLE PRECISION,
    tagline         TEXT,
    story           TEXT,
    logo_url        TEXT,
    website_url     TEXT,
    remotepay_merchant_id TEXT,
    ubernie_shop_id TEXT,
    status          TEXT DEFAULT 'ACTIVE',
    scraped_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_businesses_industry ON businesses(industry);
CREATE INDEX IF NOT EXISTS idx_businesses_status ON businesses(status);

-- ============================================================
-- 2. SHOP INTAKES (website onboarding)
-- ============================================================
CREATE TABLE IF NOT EXISTS shop_intakes (
    business_id     TEXT PRIMARY KEY REFERENCES businesses(id) ON DELETE CASCADE,
    data            JSONB NOT NULL,
    site_config     JSONB,
    site_url        TEXT,
    status          TEXT DEFAULT 'SUBMITTED',
    submitted_at    TIMESTAMPTZ DEFAULT NOW(),
    generated_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_shop_intakes_status ON shop_intakes(status);

-- ============================================================
-- 3. DEPLOYMENTS (site hosting records)
-- ============================================================
CREATE TABLE IF NOT EXISTS deployments (
    business_id     TEXT PRIMARY KEY REFERENCES businesses(id) ON DELETE CASCADE,
    domain          TEXT NOT NULL,
    url             TEXT,
    status          TEXT NOT NULL,
    steps           JSONB,
    error           TEXT,
    deployed_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_deployments_status ON deployments(status);

-- ============================================================
-- 4. CUSTOM DOMAINS
-- ============================================================
CREATE TABLE IF NOT EXISTS custom_domains (
    id              SERIAL PRIMARY KEY,
    business_id     TEXT REFERENCES businesses(id) ON DELETE CASCADE,
    domain          TEXT UNIQUE NOT NULL,
    verified        BOOLEAN DEFAULT FALSE,
    ssl_active      BOOLEAN DEFAULT FALSE,
    connected_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 5. CUSTOMERS
-- ============================================================
CREATE TABLE IF NOT EXISTS customers (
    id              SERIAL PRIMARY KEY,
    email           TEXT UNIQUE,
    phone           TEXT,
    name            TEXT,
    address         TEXT,
    latitude        DOUBLE PRECISION,
    longitude       DOUBLE PRECISION,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);

-- ============================================================
-- 6. ORDERS
-- ============================================================
CREATE TABLE IF NOT EXISTS orders (
    order_id        TEXT PRIMARY KEY,
    business_id     TEXT REFERENCES businesses(id),
    customer_id     INTEGER REFERENCES customers(id),
    subtotal        NUMERIC(12,2) NOT NULL,
    delivery_fee    NUMERIC(12,2) DEFAULT 0,
    total           NUMERIC(12,2) NOT NULL,
    status          TEXT DEFAULT 'PENDING',
    payment_method  TEXT DEFAULT 'RemotePay',
    payment_id      TEXT,
    paid_at         TIMESTAMPTZ,
    delivery_option TEXT,
    delivery_address TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orders_business ON orders(business_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at DESC);

-- ============================================================
-- 7. ORDER ITEMS
-- ============================================================
CREATE TABLE IF NOT EXISTS order_items (
    id              SERIAL PRIMARY KEY,
    order_id        TEXT REFERENCES orders(order_id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    price           NUMERIC(12,2) NOT NULL,
    quantity        INTEGER NOT NULL DEFAULT 1
);

-- ============================================================
-- 8. RIDERS (Ubernie owner-drivers)
-- ============================================================
CREATE TABLE IF NOT EXISTS riders (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    phone           TEXT,
    email           TEXT,
    area            TEXT,
    lat             DOUBLE PRECISION,
    lng             DOUBLE PRECISION,
    scooter_model   TEXT DEFAULT 'Zeebee Greenscooter',
    rating          NUMERIC(3,2) DEFAULT 5.00,
    current_jobs    INTEGER DEFAULT 0,
    acceptance_rate NUMERIC(3,2) DEFAULT 1.00,
    status          TEXT DEFAULT 'APPLIED',
    bank_account    TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_riders_status ON riders(status);
CREATE INDEX IF NOT EXISTS idx_riders_area ON riders(area);

-- ============================================================
-- 9. DELIVERY ZONES (waitlist aggregation)
-- ============================================================
CREATE TABLE IF NOT EXISTS delivery_zones (
    id              SERIAL PRIMARY KEY,
    area            TEXT UNIQUE NOT NULL,
    status          TEXT DEFAULT 'WAITING',
    activated_at    TIMESTAMPTZ,
    min_shops       INTEGER DEFAULT 15,
    min_riders      INTEGER DEFAULT 3
);

-- ============================================================
-- 10. DELIVERY WAITLIST (shops waiting for zone activation)
-- ============================================================
CREATE TABLE IF NOT EXISTS delivery_waitlist (
    id              SERIAL PRIMARY KEY,
    business_id     TEXT REFERENCES businesses(id) ON DELETE CASCADE,
    area            TEXT NOT NULL,
    industry        TEXT,
    estimated_daily_orders INTEGER DEFAULT 0,
    status          TEXT DEFAULT 'WAITING',
    waitlist_date   TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (business_id)
);

CREATE INDEX IF NOT EXISTS idx_waitlist_area ON delivery_waitlist(area);
CREATE INDEX IF NOT EXISTS idx_waitlist_status ON delivery_waitlist(status);

-- ============================================================
-- 11. DELIVERY JOBS
-- ============================================================
CREATE TABLE IF NOT EXISTS delivery_jobs (
    id              SERIAL PRIMARY KEY,
    order_id        TEXT REFERENCES orders(order_id) ON DELETE CASCADE,
    shop_id         TEXT REFERENCES businesses(id),
    rider_id        TEXT REFERENCES riders(id),
    pickup_address  TEXT,
    dropoff_address TEXT,
    status          TEXT DEFAULT 'PENDING',
    assigned_at     TIMESTAMPTZ,
    delivered_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON delivery_jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_rider ON delivery_jobs(rider_id);

-- ============================================================
-- 12. TAX TRANSACTIONS (VAT ledger)
-- ============================================================
CREATE TABLE IF NOT EXISTS tax_transactions (
    id              SERIAL PRIMARY KEY,
    business_id     TEXT REFERENCES businesses(id) ON DELETE CASCADE,
    transaction_id  TEXT UNIQUE NOT NULL,
    receipt_number  TEXT NOT NULL,
    amount_excl_vat NUMERIC(12,2) NOT NULL,
    vat_amount      NUMERIC(12,2) NOT NULL,
    amount_incl_vat NUMERIC(12,2) NOT NULL,
    payment_method  TEXT,
    vat_period      TEXT,
    receipt_json    JSONB,
    issued_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tax_business ON tax_transactions(business_id);
CREATE INDEX IF NOT EXISTS idx_tax_period ON tax_transactions(vat_period);

-- ============================================================
-- 13. SUBSCRIPTIONS (C6 SaaS plans)
-- ============================================================
CREATE TABLE IF NOT EXISTS subscriptions (
    id              SERIAL PRIMARY KEY,
    business_id     TEXT REFERENCES businesses(id) ON DELETE CASCADE,
    plan_id         TEXT NOT NULL,
    status          TEXT DEFAULT 'ACTIVE',
    amount          NUMERIC(12,2),
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    cancelled_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_subs_business ON subscriptions(business_id);
CREATE INDEX IF NOT EXISTS idx_subs_status ON subscriptions(status);

-- ============================================================
-- DONE
-- ============================================================
