# seed_data_generator.py
import sqlite3
import random
import os
from datetime import datetime, timedelta

DEFAULT_DB_PATH = os.path.join("database", "support.db")
DEFAULT_SCHEMA_PATH = os.path.join("database", "schema.sql")

def main():
    # Set seed for deterministic generation
    random.seed(42)

    db_path = os.getenv("SQLITE_DB_PATH", DEFAULT_DB_PATH)
    schema_path = os.getenv("SQLITE_SCHEMA_PATH", DEFAULT_SCHEMA_PATH)

    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Read and execute schema
    print(f"Reading schema: {schema_path}")
    with open(schema_path, "r") as f:
        schema_sql = f.read()
        
    # Clean up existing tables to prevent stale records from previous seeding runs
    for table in ["tickets", "payments", "subscriptions", "products", "customers", "feedback_logs"]:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
        
    cursor.executescript(schema_sql)
    print("Database schema initialized.")

    # 2. Seed Products (3 items)
    products_data = [
        ("prod_basic", "Basic Plan", 10.0, "monthly"),
        ("prod_pro", "Pro Plan", 20.0, "monthly"),
        ("prod_enterprise", "Enterprise Plan", 200.0, "annual")
    ]
    cursor.executemany(
        "INSERT OR REPLACE INTO products (product_id, name, price, billing_cycle) VALUES (?, ?, ?, ?)",
        products_data
    )
    print(f"Seeded {len(products_data)} products.")

    # 3. Seed Customers, Subscriptions, Payments & Tickets (logical unified generation)
    first_names = ["Alice", "Bob", "Charlie", "David", "Emma", "Frank", "Grace", "Henry", "Ivy", "Jack", 
                   "Karen", "Leo", "Mia", "Nathan", "Olivia", "Peter", "Quinn", "Rachel", "Sam", "Taylor",
                   "Sarah", "John", "James", "Emily", "Michael", "Jessica", "Thomas", "Lisa", "William", "Ashley"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Garcia", "Rodriguez", "Wilson",
                  "Martinez", "Anderson", "Taylor", "Thomas", "Hernandez", "Moore", "Martin", "Jackson", "Thompson", "White",
                  "Harris", "Clark", "Lewis", "Robinson", "Walker", "Young", "Allen", "King", "Wright", "Scott"]

    customers = []
    subscriptions = []
    payments = []
    tickets = []

    sub_count = 1
    pay_count = 1
    tkt_count = 1

    # Use the current execution date as the reference "now" date
    now_ref = datetime.now()

    ticket_templates = [
        ("Cannot reset password", "I tried to reset my password using the settings menu, but I'm not getting the reset email.", "low"),
        ("Invoice inquiry", "I noticed double charges on my credit card statement for last month. Can you please check?", "medium"),
        ("Upgrade to Pro Plan issue", "I want to upgrade my workspace to the Pro plan. How will the proration be calculated? I keep getting a card rejection error.", "medium"),
        ("Slack integration failing", "The Slack bot isn't posting task updates in our subscribed channel. We verified authorization but nothing happens.", "high"),
        ("Page load error", "I am getting a loading error on my Gantt chart view. I tried clearing browser cache but it didn't help. The screen is blank.", "high"),
        ("Refund request", "I purchased an annual subscription 5 days ago, but our project scope changed. I would like to cancel and request a full refund.", "high"),
        ("API Rate limits reached", "We are receiving HTTP 429 errors from our external sync script. Can we raise our rate limit?", "medium"),
        ("CSV import failure", "My CSV task import fails at column mapping. It says 'Invalid headers structure' but headers match template.", "low"),
        ("How to create boards", "I'm a new user and need help creating a private team board. Can you provide instructions?", "low"),
        ("WebSocket disconnect warnings", "We frequently see the 'Disconnected from server' WebSocket alert on Chrome. Is there an outage?", "medium")
    ]

    for i in range(1, 101):
        cust_id = f"cust_{i:03d}"
        if i == 10:
            first, last = "John", "Smith"
            name = "John Smith"
        elif i == 20:
            first, last = "John", "Smith"
            name = "John Smith"
        elif i == 30:
            first, last = "Emma", "Davis"
            name = "Emma Davis"
        elif i == 40:
            first, last = "Emma", "Davis"
            name = "Emma Davis"
        else:
            first = random.choice(first_names)
            last = random.choice(last_names)
            name = f"{first} {last}"
            
        email = f"{first.lower()}.{last.lower()}.{i}@example.com"
        phone = f"555-{random.randint(100, 999):03d}-{random.randint(1000, 9999):04d}"
        
        # Decide product
        prod = random.choice(products_data)
        prod_id = prod[0]
        price = prod[2]
        billing = prod[3]
        
        # Decide subscription status
        status_rand = random.random()
        if status_rand < 0.75:
            status = "active"
        elif status_rand < 0.90:
            status = "cancelled"
        else:
            status = "expired"

        # Generate subscription dates relative to current local execution time
        if status == "active":
            cancel_at_period_end = 1 if random.random() < 0.15 else 0
            if billing == "monthly":
                # Started within the last month, ends in future
                start_dt = now_ref - timedelta(days=random.randint(1, 28))
                end_dt = start_dt + timedelta(days=30)
            else:
                # Annual started within the last year, ends in future
                start_dt = now_ref - timedelta(days=random.randint(10, 340))
                end_dt = start_dt + timedelta(days=365)
        elif status == "cancelled":
            cancel_at_period_end = 1
            if billing == "monthly":
                # Ended in the past
                end_dt = now_ref - timedelta(days=random.randint(5, 180))
                start_dt = end_dt - timedelta(days=30)
            else:
                end_dt = now_ref - timedelta(days=random.randint(30, 300))
                start_dt = end_dt - timedelta(days=365)
        else: # expired
            cancel_at_period_end = 0
            if billing == "monthly":
                # Ended in the past
                end_dt = now_ref - timedelta(days=random.randint(5, 180))
                start_dt = end_dt - timedelta(days=30)
            else:
                end_dt = now_ref - timedelta(days=random.randint(30, 300))
                start_dt = end_dt - timedelta(days=365)

        # Generate previous billing periods (renewals) for active monthly subscribers to simulate billing history
        history_cycles = []
        if status == "active" and billing == "monthly" and random.random() < 0.80:
            num_cycles = random.randint(1, 4)
            for c in range(1, num_cycles + 1):
                cycle_start = start_dt - timedelta(days=30 * c)
                cycle_end = cycle_start + timedelta(days=30)
                history_cycles.append((cycle_start, cycle_end))

        # Find the oldest start date to determine logical customer signup date
        oldest_start = start_dt
        if history_cycles:
            oldest_start = history_cycles[-1][0]
            
        created_dt = oldest_start - timedelta(days=random.randint(1, 5))
        created_at_str = created_dt.strftime("%Y-%m-%d %H:%M:%S")

        # Add customer
        customers.append((cust_id, name, email, phone, created_at_str))

        # Add historical cycles to subscriptions and payments
        for cycle_start, cycle_end in history_cycles:
            hist_sub_id = f"sub_{sub_count:03d}"
            subscriptions.append((
                hist_sub_id, cust_id, prod_id, "expired",
                cycle_start.strftime("%Y-%m-%d %H:%M:%S"),
                cycle_end.strftime("%Y-%m-%d %H:%M:%S"),
                0
            ))
            sub_count += 1
            
            # Historical success payment
            pay_id = f"pay_{pay_count:03d}"
            pay_status = "success"
            method = random.choice(["credit_card", "paypal", "bank_transfer"])
            pay_dt = cycle_start + timedelta(minutes=random.randint(1, 15))
            payments.append((pay_id, cust_id, price, pay_status, method, pay_dt.strftime("%Y-%m-%d %H:%M:%S")))
            pay_count += 1

        # Add main subscription
        main_sub_id = f"sub_{sub_count:03d}"
        subscriptions.append((
            main_sub_id, cust_id, prod_id, status,
            start_dt.strftime("%Y-%m-%d %H:%M:%S"),
            end_dt.strftime("%Y-%m-%d %H:%M:%S"),
            cancel_at_period_end
        ))
        sub_count += 1

        # Add main payment
        pay_id = f"pay_{pay_count:03d}"
        pay_status = "success" if status in ["active", "expired"] or random.random() < 0.85 else "failed"
        if status == "cancelled" and random.random() < 0.20:
            pay_status = "refunded"
        method = random.choice(["credit_card", "paypal", "bank_transfer"])
        pay_dt = start_dt + timedelta(minutes=random.randint(1, 15))
        payments.append((pay_id, cust_id, price, pay_status, method, pay_dt.strftime("%Y-%m-%d %H:%M:%S")))
        pay_count += 1

        # Seed 1 to 3 tickets for each customer (bounded between signup date and reference execution time)
        num_tickets = random.randint(1, 3)
        for _ in range(num_tickets):
            template = random.choice(ticket_templates)
            tkt_id = f"TKT-{tkt_count:03d}"
            title = template[0]
            description = template[1]
            priority = template[2]
            
            # Random status
            t_rand = random.random()
            if t_rand < 0.70:
                tkt_status = "resolved"
            elif t_rand < 0.85:
                tkt_status = "open"
            elif t_rand < 0.95:
                tkt_status = "in_progress"
            else:
                tkt_status = "closed"
                
            days_range = (now_ref - created_dt).days
            if days_range <= 0:
                days_range = 1
            tkt_dt = created_dt + timedelta(days=random.randint(0, days_range), minutes=random.randint(1, 1440))
            if tkt_dt > now_ref:
                tkt_dt = now_ref - timedelta(minutes=random.randint(1, 60))
                
            tickets.append((tkt_id, cust_id, title, tkt_status, priority, description, tkt_dt.strftime("%Y-%m-%d %H:%M:%S")))
            tkt_count += 1

    # Insert into Database
    cursor.executemany(
        "INSERT OR REPLACE INTO customers (customer_id, name, email, phone, created_at) VALUES (?, ?, ?, ?, ?)",
        customers
    )
    print(f"Seeded {len(customers)} customers.")

    cursor.executemany(
        "INSERT OR REPLACE INTO subscriptions (subscription_id, customer_id, product_id, status, start_date, end_date, cancel_at_period_end) VALUES (?, ?, ?, ?, ?, ?, ?)",
        subscriptions
    )
    print(f"Seeded {len(subscriptions)} subscriptions.")

    cursor.executemany(
        "INSERT OR REPLACE INTO payments (payment_id, customer_id, amount, status, payment_method, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        payments
    )
    print(f"Seeded {len(payments)} payments.")

    cursor.executemany(
        "INSERT OR REPLACE INTO tickets (ticket_id, customer_id, title, status, priority, description, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        tickets
    )
    print(f"Seeded {len(tickets)} tickets.")

    conn.commit()
    conn.close()
    print("Database seeding completed successfully with consistent dates.")

if __name__ == "__main__":
    main()
