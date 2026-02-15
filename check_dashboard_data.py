import sqlite3
import sys
import os

# Add project root to sys.path
current_dir = os.getcwd()
sys.path.insert(0, current_dir)

from src.database.repository import DataRepository
from src.database.connection import init_db

def check():
    print(f"Python version: {sys.version}")
    print(f"SQLite version: {sqlite3.sqlite_version}")
    
    try:
        init_db()
        print("Database initialized.")
        
        stats = DataRepository.get_dashboard_stats()
        print(f"Dashboard Stats: {stats}")
        
        imports = DataRepository.get_recent_imports()
        print(f"Recent Imports: {imports}")
        
    except Exception as e:
        print(f"Error during check: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check()
