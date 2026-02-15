import sqlite3
import os

# Define the database path
DB_PATH = os.path.join(os.getcwd(), "data", "invoices.db")

def migrate():
    if not os.path.exists(DB_PATH):
        print("No database found. Nothing to migrate.")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Starting database migration...")
    
    try:
        # 1. Backup old customers
        cursor.execute("SELECT name, phone, last_invoice_date, created_at FROM customers")
        old_customers = cursor.fetchall()
        
        # 2. Disable foreign keys temporarily
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # 3. Drop old table
        cursor.execute("DROP TABLE customers")
        
        # 4. Create new table with relaxed constraints
        cursor.execute('''
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            last_invoice_date DATETIME,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name, phone)
        )
        ''')
        
        # 5. Restore customers (using INSERT OR IGNORE to be safe)
        for name, phone, last_inv, created in old_customers:
            cursor.execute("""
                INSERT OR IGNORE INTO customers (name, phone, last_invoice_date, created_at) 
                VALUES (?, ?, ?, ?)
            """, (name, phone, last_inv, created))
            
        conn.commit()
        print(f"Migration successful! Restored {len(old_customers)} customers.")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
