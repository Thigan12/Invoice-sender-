import os
import sys

def get_base_dir():
    """Returns the persistent base directory for the application data."""
    if getattr(sys, 'frozen', False):
        # Running as a bundled executable
        # Use the directory where the .exe is located
        return os.path.dirname(sys.executable)
    else:
        # Running in a normal Python environment
        # Use the project root (three levels up from this file: src/utils/paths.py)
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_data_dir():
    """Returns the path to the data directory, ensuring it exists."""
    data_dir = os.path.join(get_base_dir(), "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def get_db_path():
    """Returns the path to the SQLite database file."""
    return os.path.join(get_data_dir(), "invoices.db")

def get_pdf_dir():
    """Returns the path to the directory where PDFs are generated."""
    pdf_dir = os.path.join(get_data_dir(), "generated_pdfs")
    os.makedirs(pdf_dir, exist_ok=True)
    return pdf_dir

def get_import_archive_dir():
    """Returns the path to the directory where imported Excel files are archived."""
    archive_dir = os.path.join(get_data_dir(), "imports")
    os.makedirs(archive_dir, exist_ok=True)
    return archive_dir
