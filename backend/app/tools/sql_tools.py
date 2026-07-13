# sql_tools.py
import os
import sqlite3
from pathlib import Path
from langchain_core.tools import tool

# Resolve database path relative to this file's location (portable across machines)
_PROJECT_ROOT = Path(__file__).resolve().parents[3]  # backend/app/tools -> project root
DEFAULT_DB_PATH = str(_PROJECT_ROOT / "database" / "support.db")

def get_db_connection():
    db_path = os.getenv("SQLITE_DB_PATH", DEFAULT_DB_PATH)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def run_select_query(query: str, params: tuple = ()) -> list:
    """Helper function to execute a safe SELECT query and return rows as list of dicts."""
    # Safety check: enforce read-only SELECT
    clean_query = query.strip().upper()
    if not clean_query.startswith("SELECT"):
        raise ValueError("Security Violation: Only SELECT queries are permitted.")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"[SQL ERROR] Query failed: {query} with params {params}. Error: {e}")
        return [{"error": str(e)}]
    finally:
        conn.close()

@tool
def customer_lookup(query: str) -> str:
    """
    Search for customer records in the ResolveDesk database.
    The query can be a customer email, a customer name (partial matching), or a customer_id.
    """
    clean_query = query.strip()
    # Auto-pad numeric queries to match cust_XXX format (e.g. 013 -> cust_013)
    lookup_ids = [clean_query]
    if clean_query.isdigit():
        lookup_ids.append(f"cust_{int(clean_query):03d}")
        
    placeholders = ",".join("?" for _ in lookup_ids)
    sql = f"""
        SELECT customer_id, name, email, phone, created_at 
        FROM customers 
        WHERE customer_id IN ({placeholders}) OR email = ? OR name LIKE ?
    """
    # Try exact match first, then fallback to partial name match
    param_name = f"%{clean_query}%"
    params = tuple(lookup_ids) + (clean_query, param_name)
    results = run_select_query(sql, params)
    
    if not results:
        return f"No customer found matching search query: '{query}'."
    return str(results)

@tool
def subscription_lookup(customer_id: str) -> str:
    """
    Retrieve active, cancelled, or expired subscription details for a customer.
    Must provide the specific customer_id (e.g. 'cust_001').
    """
    sql = """
        SELECT s.subscription_id, s.status, s.start_date, s.end_date, s.cancel_at_period_end, 
               p.name AS product_name, p.price 
        FROM subscriptions s 
        JOIN products p ON s.product_id = p.product_id 
        WHERE s.customer_id = ?
        ORDER BY s.start_date DESC
    """
    results = run_select_query(sql, (customer_id,))
    if not results:
        return f"No subscriptions found for customer_id: '{customer_id}'."
    return str(results)

@tool
def ticket_status(query: str) -> str:
    """
    Look up customer support tickets. 
    The query can be a specific ticket_id (e.g. 'TKT-001') or a customer_id (e.g. 'cust_001').
    """
    sql = """
        SELECT ticket_id, customer_id, title, status, priority, description, created_at 
        FROM tickets 
        WHERE ticket_id = ? OR customer_id = ?
        ORDER BY created_at DESC
    """
    results = run_select_query(sql, (query, query))
    if not results:
        return f"No tickets found matching query: '{query}'."
    return str(results)

@tool
def payment_history(customer_id: str) -> str:
    """
    List billing records, payments, and payment states (success, failed, refunded) for a customer.
    Must provide the specific customer_id (e.g. 'cust_001').
    """
    sql = """
        SELECT payment_id, amount, status, payment_method, created_at 
        FROM payments 
        WHERE customer_id = ? 
        ORDER BY created_at DESC 
        LIMIT 10
    """
    results = run_select_query(sql, (customer_id,))
    if not results:
        return f"No payment history found for customer_id: '{customer_id}'."
    return str(results)

@tool
def get_customer_count() -> str:
    """
    Retrieve the total number of customers registered in the ResolveDesk database.
    """
    sql = "SELECT COUNT(*) as count FROM customers"
    results = run_select_query(sql)
    if not results or "error" in results[0]:
        return "Error retrieving customer count."
    return f"Total customer count: {results[0]['count']}"

@tool
def get_all_customers() -> str:
    """
    Retrieve details (ID, name, email, and phone number) for all registered customers in the database.
    """
    sql = "SELECT customer_id, name, email, phone FROM customers ORDER BY customer_id"
    results = run_select_query(sql)
    if not results:
        return "No customers found in database."
    return str(results)
