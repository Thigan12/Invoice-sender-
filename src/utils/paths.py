import os
import sys
import json

# ── In-memory config cache ──
_config_cache = None

def get_base_dir():
    """Returns the directory containing static assets (logo, styles).
    In a bundle, this is the temp directory (_MEIPASS).
    """
    if getattr(sys, 'frozen', False):
        return getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_external_base_dir():
    """Returns the directory where the EXE is located (for database/config)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return get_base_dir()

def get_data_dir():
    """Returns the path to the data directory, ensuring it exists.
    Always creates it next to the EXE for persistence.
    """
    data_dir = os.path.join(get_external_base_dir(), "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def get_config_path():
    """Returns the path to the config.json file."""
    return os.path.join(get_data_dir(), "config.json")

def load_config():
    """Load the config file. Uses in-memory cache after first read."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache
    path = get_config_path()
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                _config_cache = json.load(f)
                return _config_cache
        except Exception:
            _config_cache = {}
            return _config_cache
    _config_cache = {}
    return _config_cache

def save_config(config):
    """Save config dict to config.json and update cache."""
    global _config_cache
    path = get_config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    _config_cache = config

def invalidate_config_cache():
    """Force config to be re-read from disk on next load_config() call."""
    global _config_cache
    _config_cache = None

# ── Cached DB path ──
_db_path_cache = None

def get_db_path():
    """Returns the path to the SQLite database file.
    Checks config.json for a custom database directory first.
    Result is cached after first call.
    """
    global _db_path_cache
    if _db_path_cache is not None:
        return _db_path_cache
    
    config = load_config()
    custom_dir = config.get("db_directory", "").strip()
    
    if custom_dir and os.path.isdir(custom_dir):
        _db_path_cache = os.path.join(custom_dir, "invoices.db")
    else:
        _db_path_cache = os.path.join(get_data_dir(), "invoices.db")
    return _db_path_cache

def set_db_directory(directory):
    """Set a custom database directory in config.json."""
    global _db_path_cache
    config = load_config()
    config["db_directory"] = directory
    save_config(config)
    _db_path_cache = None  # Invalidate so next get_db_path() re-evaluates

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
