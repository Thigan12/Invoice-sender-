import sqlite3
import os

DB_PATH = os.path.join(os.getcwd(), "data", "invoices.db")

def check_db():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM customers")
    cust_count = cursor.fetchone()[0]
    print(f"Total Customers: {cust_count}")
    
    cursor.execute("SELECT name, phone FROM customers LIMIT 10")
    print("Latest 10 customers:")
    for row in cursor.fetchall():
        print(f"- {row[0]} ({row[1]})")
        
    cursor.execute("SELECT COUNT(*) FROM invoices")
    inv_count = cursor.fetchone()[0]
    print(f"Total Invoices: {inv_count}")
    
    conn.close()

if __name__ == "__main__":
    check_db()
