import sys
import os

# Fix DPI Awareness issues on Windows before importing PySide6
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

# Fix ModuleNotFoundError by adding current project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PySide6.QtWidgets import QApplication
from src.database.connection import init_db
from src.ui.main_window import MainWindow

def load_stylesheet(app):
    qss_path = os.path.join(os.path.dirname(__file__), "ui", "styles", "main.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r") as f:
            app.setStyleSheet(f.read())

def main():
    # Initialize DB Layer
    init_db()
    
    app = QApplication(sys.argv)
    
    # Load aesthetics
    load_stylesheet(app)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
