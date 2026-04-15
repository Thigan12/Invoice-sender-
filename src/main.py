import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))

    return os.path.join(base_path, relative_path)

# Fix DPI Awareness issues on Windows
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
if sys.platform == 'win32':
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

from src.database.connection import init_db
from src.ui.main_window import MainWindow

def load_stylesheet(app):
    # Use resource_path to find the QSS file even when bundled
    qss_path = resource_path(os.path.join("ui", "styles", "main.qss"))
    if os.path.exists(qss_path):
        with open(qss_path, "r") as f:
            app.setStyleSheet(f.read())
    else:
        print(f"Warning: Stylesheet not found at {qss_path}")

def main():
    # Initialize DB Layer
    init_db()
    
    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app = QApplication(sys.argv)
    
    # Load aesthetics
    load_stylesheet(app)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

