"""
Import Customers Dialog
=======================
Allows uploading an Excel (.xlsx/.xls) or PDF file containing:
  - Customer Name
  - Mobile Number (Phone)
  - Address

Shows a live preview and saves to the customers table.
"""

import os
import re
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFrame, QWidget, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

from src.database.repository import DataRepository


# ─── Style constants ──────────────────────────────────────────────────────────
BTN_PRIMARY = """
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #6366f1, stop:1 #4f46e5);
        border: none; border-radius: 8px;
        padding: 10px 22px; font-size: 13px; font-weight: 700; color: #ffffff;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #818cf8, stop:1 #6366f1);
    }
    QPushButton:disabled { background: #334155; color: #64748b; }
"""

BTN_SUCCESS = """
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #22c55e, stop:1 #16a34a);
        border: none; border-radius: 8px;
        padding: 10px 22px; font-size: 13px; font-weight: 700; color: #ffffff;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #4ade80, stop:1 #22c55e);
    }
    QPushButton:disabled { background: #334155; color: #64748b; }
"""

BTN_GHOST = """
    QPushButton {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 8px; padding: 10px 18px;
        font-size: 13px; font-weight: 600; color: #a5b4fc;
    }
    QPushButton:hover {
        background: rgba(99, 102, 241, 0.15);
        border-color: #6366f1; color: #e0e7ff;
    }
"""

BTN_DANGER = """
    QPushButton {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.2);
        border-radius: 8px; padding: 10px 18px;
        font-size: 13px; font-weight: 600; color: #f87171;
    }
    QPushButton:hover {
        background: rgba(239, 68, 68, 0.2); color: #ffffff;
        border-color: #ef4444;
    }
    QPushButton:disabled { background: #334155; color: #64748b; border-color: transparent; }
"""

TABLE_STYLE = """
    QTableWidget {
        background-color: rgba(15, 23, 42, 0.8);
        alternate-background-color: rgba(30, 41, 59, 0.5);
        color: #e2e8f0;
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: 10px;
        font-size: 13px;
        gridline-color: rgba(99, 102, 241, 0.08);
    }
    QTableWidget::item { padding: 10px 14px; }
    QTableWidget::item:selected { background-color: rgba(99, 102, 241, 0.25); }
    QHeaderView::section {
        background: rgba(30, 41, 59, 0.95);
        color: #a5b4fc; font-weight: 700; font-size: 11px;
        padding: 12px 14px; border: none;
        border-bottom: 2px solid rgba(99, 102, 241, 0.3);
    }
    QScrollBar:vertical {
        background: rgba(15, 23, 42, 0.5); width: 8px; border-radius: 4px;
    }
    QScrollBar::handle:vertical {
        background: rgba(99, 102, 241, 0.4); border-radius: 4px; min-height: 20px;
    }
"""


def _normalize(val):
    """Convert a cell value to a clean string, or '' if empty/null."""
    if val is None:
        return ''
    s = str(val).strip()
    return '' if s.lower() in ('nan', 'none', 'null') else s


def _detect_column(columns, candidates):
    """Case-insensitive fuzzy column name detector."""
    for col in columns:
        col_lower = col.lower().replace(' ', '').replace('_', '')
        for cand in candidates:
            if cand in col_lower:
                return col
    return None


def _parse_excel(file_path):
    """
    Parse an Excel file and return (list_of_dicts, error_string).
    Each dict: {'name': ..., 'phone': ..., 'address': ...}
    """
    try:
        import pandas as pd
        df = pd.read_excel(file_path, dtype=str)
        df.columns = [str(c).strip() for c in df.columns]

        # Auto-detect columns
        name_col   = _detect_column(df.columns, ['name', 'customername', 'customer', 'nama', 'fullname'])
        phone_col  = _detect_column(df.columns, ['phone', 'mobile', 'contact', 'handphone', 'no', 'number', 'tel', 'hp'])
        addr_col   = _detect_column(df.columns, ['address', 'addr', 'alamat', 'location', 'street', 'city'])

        if not name_col:
            # Fallback: first column is name
            name_col = df.columns[0] if len(df.columns) > 0 else None
        if not phone_col and len(df.columns) > 1:
            phone_col = df.columns[1]
        if not addr_col and len(df.columns) > 2:
            addr_col = df.columns[2]

        records = []
        for _, row in df.iterrows():
            name    = _normalize(row.get(name_col, '')) if name_col else ''
            phone   = _normalize(row.get(phone_col, '')) if phone_col else ''
            address = _normalize(row.get(addr_col, ''))  if addr_col  else ''
            if name:
                records.append({'name': name, 'phone': phone, 'address': address})

        if not records:
            return [], "No valid rows found. Make sure the file has a 'Name' column."
        return records, None

    except ImportError:
        return [], "pandas / openpyxl not installed. Run: pip install pandas openpyxl"
    except Exception as e:
        return [], str(e)


def _parse_pdf(file_path):
    """
    Parse a PDF file and return (list_of_dicts, error_string).
    Tries pdfplumber first, then PyMuPDF (fitz), then pdfminer.
    Expects rows with: Name | Phone | Address (tab or multiple-space separated)
    """
    try:
        import pdfplumber
        records = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                # Try to extract table first
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        if not table:
                            continue
                        # Detect header row
                        header = [str(c).strip().lower() if c else '' for c in table[0]]
                        name_idx  = next((i for i, h in enumerate(header) if any(k in h for k in ['name', 'nama', 'customer'])), 0)
                        phone_idx = next((i for i, h in enumerate(header) if any(k in h for k in ['phone', 'mobile', 'no', 'tel', 'contact', 'hp'])), 1)
                        addr_idx  = next((i for i, h in enumerate(header) if any(k in h for k in ['address', 'addr', 'alamat', 'location'])), 2)
                        
                        start = 1 if any(k in header[0] for k in ['name', 'nama', 'customer']) else 0
                        for r in table[start:]:
                            if not r:
                                continue
                            name    = _normalize(r[name_idx])  if name_idx  < len(r) else ''
                            phone   = _normalize(r[phone_idx]) if phone_idx < len(r) else ''
                            address = _normalize(r[addr_idx])  if addr_idx  < len(r) else ''
                            if name:
                                records.append({'name': name, 'phone': phone, 'address': address})
                else:
                    # Fallback: parse raw text lines
                    text = page.extract_text() or ''
                    for line in text.split('\n'):
                        line = line.strip()
                        if not line:
                            continue
                        # Split by 2+ spaces or tab
                        parts = re.split(r'\t|  +', line)
                        parts = [p.strip() for p in parts if p.strip()]
                        if len(parts) >= 2:
                            name    = parts[0]
                            phone   = parts[1] if len(parts) > 1 else ''
                            address = parts[2] if len(parts) > 2 else ''
                            # Skip obvious headers
                            if name.lower() in ('name', 'customer', 'nama', 'no.'):
                                continue
                            records.append({'name': name, 'phone': phone, 'address': address})

        if not records:
            return [], "No valid rows could be extracted from PDF.\n\nMake sure the PDF has a table or columns: Name | Phone | Address."
        return records, None

    except ImportError:
        # Try fallback with fitz (PyMuPDF)
        try:
            import fitz
            records = []
            doc = fitz.open(file_path)
            for page in doc:
                text = page.get_text()
                for line in text.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    parts = re.split(r'\t|  +', line)
                    parts = [p.strip() for p in parts if p.strip()]
                    if len(parts) >= 2:
                        name  = parts[0]
                        phone = parts[1] if len(parts) > 1 else ''
                        addr  = parts[2] if len(parts) > 2 else ''
                        if name.lower() not in ('name', 'customer', 'nama', 'no.'):
                            records.append({'name': name, 'phone': phone, 'address': addr})
            if not records:
                return [], "No valid rows extracted. Check PDF structure."
            return records, None
        except ImportError:
            return [], (
                "No PDF library found.\n\n"
                "Install one of:\n"
                "  pip install pdfplumber\n"
                "  pip install PyMuPDF"
            )
        except Exception as e:
            return [], str(e)
    except Exception as e:
        return [], str(e)


# ─── Main Dialog ──────────────────────────────────────────────────────────────
class ImportCustomersDialog(QDialog):
    """
    Dialog that lets the user import customers from Excel or PDF.
    Shows a live 3-column preview (Name, Phone, Address).
    On confirm, saves to the customers table.
    """
    customers_imported = Signal()  # Emitted after a successful save

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Customers")
        self.setMinimumSize(860, 620)
        self.resize(960, 700)
        self.setModal(True)
        self._records = []  # list of {'name', 'phone', 'address'}

        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0f172a, stop:1 #1e293b);
            }
        """)
        self._build_ui()

    # ── UI ──────────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        # ── Header ──
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(99,102,241,0.12), stop:1 rgba(139,92,246,0.06));
                border: 1px solid rgba(99,102,241,0.2);
                border-radius: 14px;
            }
        """)
        hdr_layout = QHBoxLayout(header_frame)
        hdr_layout.setContentsMargins(24, 18, 24, 18)

        icon_lbl = QLabel("📥")
        icon_lbl.setStyleSheet("font-size: 32px; background: transparent;")

        txt_layout = QVBoxLayout()
        txt_layout.setSpacing(3)
        title_lbl = QLabel("Import Customers")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 800; color: #f8fafc; background: transparent;")
        sub_lbl = QLabel("Upload an Excel (.xlsx / .xls) or PDF file with Name, Phone & Address columns")
        sub_lbl.setStyleSheet("font-size: 12px; color: #64748b; background: transparent;")
        txt_layout.addWidget(title_lbl)
        txt_layout.addWidget(sub_lbl)

        hdr_layout.addWidget(icon_lbl)
        hdr_layout.addSpacing(12)
        hdr_layout.addLayout(txt_layout)
        hdr_layout.addStretch()
        root.addWidget(header_frame)

        # ── Format hint ──
        hint_frame = QFrame()
        hint_frame.setStyleSheet("""
            QFrame {
                background: rgba(251,191,36,0.06);
                border: 1px solid rgba(251,191,36,0.2);
                border-radius: 10px;
            }
        """)
        hint_layout = QHBoxLayout(hint_frame)
        hint_layout.setContentsMargins(16, 10, 16, 10)
        hint_icon = QLabel("💡")
        hint_icon.setStyleSheet("font-size: 16px; background: transparent;")
        hint_text = QLabel(
            "<b style='color:#fbbf24;'>Expected columns:</b> "
            "<span style='color:#e2e8f0;'>Name &nbsp;|&nbsp; Phone / Mobile &nbsp;|&nbsp; Address</span> — "
            "<span style='color:#94a3b8;'>Column headers are auto-detected. Extra columns are ignored.</span>"
        )
        hint_text.setStyleSheet("color: #94a3b8; font-size: 12px; background: transparent;")
        hint_text.setTextFormat(Qt.RichText)
        hint_layout.addWidget(hint_icon)
        hint_layout.addWidget(hint_text)
        hint_layout.addStretch()
        root.addWidget(hint_frame)

        # ── Action buttons ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_excel = QPushButton("📂  Upload Excel")
        self.btn_excel.setFixedHeight(44)
        self.btn_excel.setStyleSheet(BTN_PRIMARY)
        self.btn_excel.setCursor(Qt.PointingHandCursor)
        self.btn_excel.clicked.connect(self._on_upload_excel)

        self.btn_pdf = QPushButton("📄  Upload PDF")
        self.btn_pdf.setFixedHeight(44)
        self.btn_pdf.setStyleSheet(BTN_GHOST)
        self.btn_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_pdf.clicked.connect(self._on_upload_pdf)

        self.btn_clear = QPushButton("🗑  Clear")
        self.btn_clear.setFixedHeight(44)
        self.btn_clear.setStyleSheet(BTN_DANGER)
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.setEnabled(False)
        self.btn_clear.clicked.connect(self._on_clear)

        self.btn_save = QPushButton("✔  Save Customers")
        self.btn_save.setFixedHeight(44)
        self.btn_save.setStyleSheet(BTN_SUCCESS)
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self._on_save)

        btn_row.addWidget(self.btn_excel)
        btn_row.addWidget(self.btn_pdf)
        btn_row.addWidget(self.btn_clear)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_save)
        root.addLayout(btn_row)

        # ── Status bar ──
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("font-size: 12px; color: #a5b4fc; font-weight: 600; background: transparent;")
        root.addWidget(self.lbl_status)

        # ── Preview table ──
        preview_hdr = QHBoxLayout()
        preview_title = QLabel("Preview")
        preview_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #e2e8f0; background: transparent;")
        self.lbl_count = QLabel("No file loaded")
        self.lbl_count.setStyleSheet("font-size: 12px; color: #64748b; background: transparent;")
        preview_hdr.addWidget(preview_title)
        preview_hdr.addStretch()
        preview_hdr.addWidget(self.lbl_count)
        root.addLayout(preview_hdr)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Name", "Phone / Mobile", "Address"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.verticalHeader().setDefaultSectionSize(40)
        root.addWidget(self.table)

        # ── Bottom close ──
        close_row = QHBoxLayout()
        btn_close = QPushButton("Close")
        btn_close.setFixedHeight(40)
        btn_close.setStyleSheet(BTN_GHOST)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.reject)
        close_row.addStretch()
        close_row.addWidget(btn_close)
        root.addLayout(close_row)

    # ── Handlers ────────────────────────────────────────────────────────────
    def _on_upload_excel(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel File", "",
            "Excel Files (*.xlsx *.xls)"
        )
        if not path:
            return
        fname = os.path.basename(path)
        self.lbl_status.setText(f"Reading {fname}…")
        records, error = _parse_excel(path)
        if error:
            QMessageBox.critical(self, "Excel Error", f"Could not read file:\n\n{error}")
            self.lbl_status.setText("")
            return
        self._load_records(records, f"Excel: {fname}")

    def _on_upload_pdf(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select PDF File", "",
            "PDF Files (*.pdf)"
        )
        if not path:
            return
        fname = os.path.basename(path)
        self.lbl_status.setText(f"Reading {fname}…")
        records, error = _parse_pdf(path)
        if error:
            QMessageBox.critical(self, "PDF Error", f"Could not read file:\n\n{error}")
            self.lbl_status.setText("")
            return
        self._load_records(records, f"PDF: {fname}")

    def _load_records(self, records, source_label):
        self._records = records
        self.table.setRowCount(0)

        for i, rec in enumerate(records):
            self.table.insertRow(i)

            name_item = QTableWidgetItem(rec.get('name', ''))
            name_item.setForeground(QColor('#f1f5f9'))
            self.table.setItem(i, 0, name_item)

            phone_item = QTableWidgetItem(rec.get('phone', ''))
            phone_item.setForeground(QColor('#94a3b8'))
            self.table.setItem(i, 1, phone_item)

            addr = rec.get('address', '')
            addr_item = QTableWidgetItem(addr)
            if not addr:
                addr_item.setForeground(QColor('#475569'))
                addr_item.setText("—")
            else:
                addr_item.setForeground(QColor('#a5b4fc'))
            self.table.setItem(i, 2, addr_item)

        n = len(records)
        self.lbl_count.setText(f"{n} row{'s' if n != 1 else ''} found")
        self.lbl_status.setText(f"✔ Loaded from {source_label}. Review and click 'Save Customers'.")
        self.btn_save.setEnabled(n > 0)
        self.btn_clear.setEnabled(n > 0)

    def _on_clear(self):
        self._records = []
        self.table.setRowCount(0)
        self.lbl_count.setText("No file loaded")
        self.lbl_status.setText("")
        self.btn_save.setEnabled(False)
        self.btn_clear.setEnabled(False)

    def _on_save(self):
        if not self._records:
            return

        # Read from table in case user edited cells manually
        edited_records = []
        for row in range(self.table.rowCount()):
            name_item  = self.table.item(row, 0)
            phone_item = self.table.item(row, 1)
            addr_item  = self.table.item(row, 2)

            name  = name_item.text().strip()  if name_item  else ''
            phone = phone_item.text().strip() if phone_item else ''
            addr  = addr_item.text().strip()  if addr_item  else ''

            if addr == '—':
                addr = ''
            if name:
                edited_records.append({'name': name, 'phone': phone, 'address': addr})

        if not edited_records:
            QMessageBox.warning(self, "Nothing to Save", "No valid rows to import.")
            return

        try:
            added, updated, skipped = DataRepository.import_customers_bulk(edited_records)
            QMessageBox.information(
                self, "Import Complete",
                f"<b style='color:#4ade80;'>✔ Done!</b><br><br>"
                f"<b>{added}</b> new customer{'s' if added != 1 else ''} added<br>"
                f"<b>{updated}</b> existing customer{'s' if updated != 1 else ''} updated (address)<br>"
                f"<b>{skipped}</b> row{'s' if skipped != 1 else ''} skipped (no name)"
            )
            self.customers_imported.emit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save customers:\n\n{str(e)}")
