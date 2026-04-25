import sqlite3
import os
import threading
from src.utils.paths import get_db_path

# ── Persistent connection pool (one per thread) ──
_local = threading.local()

def get_connection():
    """Returns a reusable connection to the SQLite database.
    Keeps one persistent connection per thread to avoid
    the overhead of opening/closing on every query.
    """
    conn = getattr(_local, 'conn', None)
    db_path = get_db_path()

    # Reuse existing connection if it's still valid and pointing to the same DB
    if conn is not None:
        try:
            conn.execute("SELECT 1")
            # Check if the DB path is still the same
            if getattr(_local, 'db_path', None) == db_path:
                return conn
            else:
                # DB path changed, close old and open new
                conn.close()
        except Exception:
            pass  # Connection is broken, create a new one

    conn = sqlite3.connect(db_path, timeout=20)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging for better concurrency
    conn.execute("PRAGMA synchronous = NORMAL")  # Faster writes, still safe
    _local.conn = conn
    _local.db_path = db_path
    return conn

def close_connection():
    """Explicitly close the persistent connection (call on app exit)."""
    conn = getattr(_local, 'conn', None)
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass
        _local.conn = None

def init_db():
    """Initializes the database with a robust relational schema."""
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Customers Table (Changed to allow multiple people with no phone)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        address TEXT,
        last_invoice_date DATETIME,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(name, phone)
    )
    ''')
    
    # Migration: add address column if it doesn't exist (for existing DBs)
    try:
        cursor.execute("ALTER TABLE customers ADD COLUMN address TEXT")
        conn.commit()
        print("Migration: added 'address' column to customers table.")
    except Exception:
        pass  # Column already exists — safe to ignore
    
    # 2. Master Products (for Fuzzy Matching learning)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS master_products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        standard_name TEXT UNIQUE NOT NULL,
        default_price REAL DEFAULT 0.0
    )
    ''')
    
    # 3. Invoices Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT UNIQUE NOT NULL,
        customer_id INTEGER,
        issue_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        total_amount REAL DEFAULT 0.0,
        pdf_path TEXT,
        status TEXT NOT NULL DEFAULT 'Draft',
        FOREIGN KEY (customer_id) REFERENCES customers(id)
    )
    ''')
    
    # 4. Invoice Items (Line items for the PDF)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER,
        description TEXT NOT NULL,
        quantity INTEGER DEFAULT 1,
        unit_price REAL DEFAULT 0.0,
        subtotal REAL DEFAULT 0.0,
        FOREIGN KEY (invoice_id) REFERENCES invoices(id)
    )
    ''')
    
    # 5. Import Logs (For Dashboard history)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS import_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT NOT NULL,
        import_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        customer_count INTEGER DEFAULT 0,
        invoice_count INTEGER DEFAULT 0,
        total_value REAL DEFAULT 0.0,
        invoice_ids TEXT
    )
    ''')
    
    conn.commit()
    
    # 5. Performance Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cust_name_phone ON customers(name, phone)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_inv_cust_id ON invoices(customer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_item_inv_id ON invoice_items(invoice_id)")
    
    conn.commit()
    print(f"Database schema initialized at {db_path}")

if __name__ == "__main__":
    init_db()
