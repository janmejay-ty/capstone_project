-- schema.sql
-- ResolveDesk Support Database Schema

CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    billing_cycle TEXT NOT NULL -- 'monthly' or 'annual'
);

CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    status TEXT NOT NULL, -- 'active', 'cancelled', 'expired'
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    cancel_at_period_end INTEGER NOT NULL DEFAULT 0, -- 0 for False, 1 for True
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    amount REAL NOT NULL,
    status TEXT NOT NULL, -- 'success', 'failed', 'refunded'
    payment_method TEXT NOT NULL, -- 'credit_card', 'paypal', 'bank_transfer'
    created_at TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS tickets (
    ticket_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL, -- 'open', 'in_progress', 'resolved', 'closed'
    priority TEXT NOT NULL, -- 'low', 'medium', 'high'
    description TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
