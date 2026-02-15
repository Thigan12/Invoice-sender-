import sqlite3
import os

DB_PATH = "data/invoices.db"

def fix_db():
    if not os.path.exists(DB_PATH):
        print("DB not found at", DB_PATH)
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if invoice_ids exists
        cursor.execute("PRAGMA table_info(import_logs)")
        cols = [c[1] for c in cursor.fetchall()]
        if "invoice_ids" not in cols:
            print("Adding invoice_ids column to import_logs...")
            cursor.execute("ALTER TABLE import_logs ADD COLUMN invoice_ids TEXT")
            conn.commit()
            print("Done")
        else:
            print("Column already exists")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_db()
