# seed_data_generator.py
import os
import sqlite3
import random
from datetime import datetime, timedelta

def main():
    db_dir = r"c:\Users\User\Desktop\python\capstone_project\database"
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "support.db")
    schema_path = os.path.join(db_dir, "schema.sql")

    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Read and execute schema
    print(f"Reading schema: {schema_path}")
    with open(schema_path, "r") as f:
        schema_sql = f.read()
        
    # Clean up existing tables to prevent stale records from previous seeding runs
    for table in ["tickets", "payments", "subscriptions", "products", "customers"]:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
        
    cursor.executescript(schema_sql)
    print("Database schema initialized.")

    # Set deterministic random seed
    random.seed(42)

    # 2. Insert Products
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

    # 3. Seed Customers (~100)
    first_names = ["Alice", "Bob", "Charlie", "David", "Emma", "Frank", "Grace", "Henry", "Ivy", "Jack", 
                   "Karen", "Leo", "Mia", "Nathan", "Olivia", "Peter", "Quinn", "Rachel", "Sam", "Taylor",
                   "Sarah", "John", "James", "Emily", "Michael", "Jessica", "Thomas", "Lisa", "William", "Ashley"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Garcia", "Rodriguez", "Wilson",
                  "Martinez", "Anderson", "Taylor", "Thomas", "Hernandez", "Moore", "Martin", "Jackson", "Thompson", "White",
                  "Harris", "Clark", "Lewis", "Robinson", "Walker", "Young", "Allen", "King", "Wright", "Scott"]

    customers = []
    base_date = datetime(2026, 1, 1)

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
        
        # Random signup date in 2026 to mid 2027
        created_days = random.randint(0, 500)
        created_at = (base_date + timedelta(days=created_days)).strftime("%Y-%m-%d %H:%M:%S")
        
        customers.append((cust_id, name, email, phone, created_at))

    cursor.executemany(
        "INSERT OR REPLACE INTO customers (customer_id, name, email, phone, created_at) VALUES (?, ?, ?, ?, ?)",
        customers
    )
    print(f"Seeded {len(customers)} customers.")

    # 4. Seed Subscriptions (~150)
    # Each customer has at least one subscription, some have multiple over time (expired then new one)
    subscriptions = []
    sub_count = 1

    # First, make sure every customer has at least one subscription
    for cust in customers:
        cust_id, _, _, _, created_at = cust
        sub_id = f"sub_{sub_count:03d}"
        prod = random.choice(products_data)
        prod_id = prod[0]
        
        start_dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S") + timedelta(hours=random.randint(1, 48))
        
        # Decide status
        status_rand = random.random()
        if status_rand < 0.70:
            status = "active"
            cancel_at_period_end = 1 if random.random() < 0.15 else 0
            if prod[3] == "monthly":
                end_dt = start_dt + timedelta(days=30)
            else:
                end_dt = start_dt + timedelta(days=365)
        elif status_rand < 0.90:
            status = "cancelled"
            cancel_at_period_end = 1
            if prod[3] == "monthly":
                end_dt = start_dt + timedelta(days=30)
            else:
                end_dt = start_dt + timedelta(days=365)
        else:
            status = "expired"
            cancel_at_period_end = 0
            if prod[3] == "monthly":
                end_dt = start_dt + timedelta(days=30)
            else:
                end_dt = start_dt + timedelta(days=365)

        subscriptions.append((
            sub_id, cust_id, prod_id, status, 
            start_dt.strftime("%Y-%m-%d %H:%M:%S"), 
            end_dt.strftime("%Y-%m-%d %H:%M:%S"), 
            cancel_at_period_end
        ))
        sub_count += 1

    # Generate additional ~50 historical/expired subscriptions
    active_customers = [c[0] for c in customers]
    for _ in range(50):
        cust_id = random.choice(active_customers)
        sub_id = f"sub_{sub_count:03d}"
        prod = random.choice(products_data)
        prod_id = prod[0]
        
        # Set start date earlier than their current active one
        start_dt = base_date + timedelta(days=random.randint(0, 365))
        end_dt = start_dt + timedelta(days=30)
        status = "expired"
        cancel_at_period_end = 0
        
        subscriptions.append((
            sub_id, cust_id, prod_id, status,
            start_dt.strftime("%Y-%m-%d %H:%M:%S"),
            end_dt.strftime("%Y-%m-%d %H:%M:%S"),
            cancel_at_period_end
        ))
        sub_count += 1

    cursor.executemany(
        "INSERT OR REPLACE INTO subscriptions (subscription_id, customer_id, product_id, status, start_date, end_date, cancel_at_period_end) VALUES (?, ?, ?, ?, ?, ?, ?)",
        subscriptions
    )
    print(f"Seeded {len(subscriptions)} subscriptions.")

    # 5. Seed Payments (~200)
    payments = []
    pay_count = 1
    
    # Generate payments corresponding to subscriptions
    for sub in subscriptions:
        sub_id, cust_id, prod_id, status, start_date_str, _, _ = sub
        start_dt = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S")
        
        # Get product price
        price = 10.0 if prod_id == "prod_basic" else (20.0 if prod_id == "prod_pro" else 200.0)
        
        # Initial payment for the subscription
        pay_id = f"pay_{pay_count:03d}"
        pay_status = "success" if random.random() < 0.95 else ("refunded" if random.random() < 0.6 else "failed")
        method = random.choice(["credit_card", "credit_card", "paypal", "bank_transfer"])
        pay_dt = start_dt + timedelta(minutes=random.randint(1, 15))
        
        payments.append((pay_id, cust_id, price, pay_status, method, pay_dt.strftime("%Y-%m-%d %H:%M:%S")))
        pay_count += 1
        
        # If active and monthly, generate subsequent monthly payments
        if status == "active" and prod_id != "prod_enterprise":
            # Generate 2 additional monthly renewals
            for month in range(1, 3):
                pay_id = f"pay_{pay_count:03d}"
                pay_status = "success" if random.random() < 0.97 else "failed"
                pay_dt = start_dt + timedelta(days=30 * month, minutes=random.randint(1, 15))
                
                # Check if payment date is in future compared to a max seed date
                if pay_dt < datetime(2027, 12, 31):
                    payments.append((pay_id, cust_id, price, pay_status, method, pay_dt.strftime("%Y-%m-%d %H:%M:%S")))
                    pay_count += 1

    # Add extra random failed/duplicate payments to reach target of ~200
    while len(payments) < 200:
        cust_id = random.choice(active_customers)
        pay_id = f"pay_{pay_count:03d}"
        price = random.choice([10.0, 20.0])
        pay_status = "failed" if random.random() < 0.8 else "success"
        method = random.choice(["credit_card", "paypal"])
        pay_dt = base_date + timedelta(days=random.randint(10, 700))
        payments.append((pay_id, cust_id, price, pay_status, method, pay_dt.strftime("%Y-%m-%d %H:%M:%S")))
        pay_count += 1

    cursor.executemany(
        "INSERT OR REPLACE INTO payments (payment_id, customer_id, amount, status, payment_method, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        payments
    )
    print(f"Seeded {len(payments)} payments.")

    # 6. Seed Tickets (~300)
    tickets = []
    tkt_count = 1
    
    # Common categories and details for realistic support cases
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

    for i in range(300):
        cust_id = random.choice(active_customers)
        template = random.choice(ticket_templates)
        
        tkt_id = f"TKT-{tkt_count:03d}"
        title = template[0]
        description = template[1]
        priority = template[2]
        
        # Random status
        status_rand = random.random()
        if status_rand < 0.70:
            status = "resolved"
        elif status_rand < 0.85:
            status = "open"
        elif status_rand < 0.95:
            status = "in_progress"
        else:
            status = "closed"
            
        # Random creation date
        created_days = random.randint(5, 700)
        created_at = (base_date + timedelta(days=created_days)).strftime("%Y-%m-%d %H:%M:%S")
        
        tickets.append((tkt_id, cust_id, title, status, priority, description, created_at))
        tkt_count += 1

    cursor.executemany(
        "INSERT OR REPLACE INTO tickets (ticket_id, customer_id, title, status, priority, description, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        tickets
    )
    print(f"Seeded {len(tickets)} tickets.")

    conn.commit()
    conn.close()
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    main()
