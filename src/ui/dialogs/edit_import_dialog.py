from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                               QMessageBox, QFileDialog, QFrame, QApplication)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
import pandas as pd
import datetime
import random

from src.database.repository import DataRepository
from src.utils.excel_parser import ExcelParser
from src.core.processor import ProductProcessor


# ---- Styles ----
BTN_PRIMARY = """
    QPushButton { 
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #6366f1, stop:1 #4f46e5);
        border: none; border-radius: 8px; padding: 10px 22px; 
        font-size: 13px; font-weight: 700; color: #ffffff;
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
        border: none; border-radius: 8px; padding: 10px 22px; 
        font-size: 13px; font-weight: 700; color: #ffffff;
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
        border-radius: 8px; padding: 8px 16px; 
        font-size: 12px; font-weight: 600; color: #a5b4fc;
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
        border-radius: 8px; padding: 10px 22px; 
        font-size: 13px; font-weight: 700; color: #f87171;
    }
    QPushButton:hover { 
        background: rgba(239, 68, 68, 0.2); 
        color: #ffffff; border-color: #ef4444; 
    }
    QPushButton:disabled { background: #334155; color: #64748b; border-color: transparent; }
"""

BTN_WARNING = """
    QPushButton { 
        background: rgba(251, 191, 36, 0.1);
        border: 1px solid rgba(251, 191, 36, 0.25);
        border-radius: 8px; padding: 10px 22px; 
        font-size: 13px; font-weight: 700; color: #fbbf24;
    }
    QPushButton:hover { 
        background: rgba(251, 191, 36, 0.2); 
        color: #ffffff; border-color: #fbbf24; 
    }
"""


class EditImportDialog(QDialog):
    """Dialog for editing an existing import — add, remove, edit rows, or merge from a new Excel file."""
    import_updated = Signal()  # Emitted when data is saved so dashboard can refresh

    def __init__(self, parent, import_id, file_name):
        super().__init__(parent)
        self.import_id = import_id
        self.file_name = file_name
        self.processor = ProductProcessor()
        self.setWindowTitle(f"Edit Import — {file_name}")
        self.setMinimumSize(950, 650)
        self.resize(1050, 720)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0f172a, stop:1 #1e293b);
            }
        """)
        self._build_ui()
        self._load_existing_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(16)

        # ── Header ──
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(99, 102, 241, 0.12), stop:1 rgba(139, 92, 246, 0.06));
                border: 1px solid rgba(99, 102, 241, 0.2);
                border-radius: 14px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 16, 20, 16)

        icon_lbl = QLabel("✏️")
        icon_lbl.setStyleSheet("font-size: 28px; background: transparent;")

        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        title_lbl = QLabel(f"Editing: {self.file_name}")
        title_lbl.setStyleSheet("font-size: 20px; font-weight: 800; color: #f8fafc; background: transparent;")
        desc_lbl = QLabel("Edit rows, add new entries, merge from another Excel, or remove items.")
        desc_lbl.setStyleSheet("font-size: 12px; color: #94a3b8; background: transparent;")
        info_col.addWidget(title_lbl)
        info_col.addWidget(desc_lbl)

        self.lbl_stats = QLabel("")
        self.lbl_stats.setStyleSheet("""
            font-size: 13px; font-weight: 700; color: #a5b4fc; 
            background: rgba(99, 102, 241, 0.1); 
            border: 1px solid rgba(99, 102, 241, 0.2); 
            border-radius: 8px; padding: 8px 14px;
        """)

        header_layout.addWidget(icon_lbl)
        header_layout.addSpacing(10)
        header_layout.addLayout(info_col)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_stats)
        layout.addWidget(header_frame)

        # ── Action Buttons Row ──
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_add_row = QPushButton("➕ Add Row")
        self.btn_add_row.setFixedHeight(42)
        self.btn_add_row.setStyleSheet(BTN_GHOST)
        self.btn_add_row.clicked.connect(self._add_empty_row)

        self.btn_delete_row = QPushButton("🗑 Delete Selected")
        self.btn_delete_row.setFixedHeight(42)
        self.btn_delete_row.setStyleSheet(BTN_DANGER)
        self.btn_delete_row.clicked.connect(self._delete_selected_rows)

        self.btn_merge_excel = QPushButton("📂 Merge from Excel")
        self.btn_merge_excel.setFixedHeight(42)
        self.btn_merge_excel.setStyleSheet(BTN_WARNING)
        self.btn_merge_excel.setToolTip("Import additional rows from another Excel file")
        self.btn_merge_excel.clicked.connect(self._merge_from_excel)

        self.btn_paste = QPushButton("📋 Paste from Excel")
        self.btn_paste.setFixedHeight(42)
        self.btn_paste.setStyleSheet(BTN_GHOST)
        self.btn_paste.setToolTip("Paste rows copied from Excel (Name, Phone, Product, Price)")
        self.btn_paste.clicked.connect(self._paste_from_clipboard)

        btn_layout.addWidget(self.btn_add_row)
        btn_layout.addWidget(self.btn_delete_row)
        btn_layout.addWidget(self.btn_merge_excel)
        btn_layout.addWidget(self.btn_paste)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # ── Editable Table ──
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Customer Name", "Phone", "Product", "Price"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(True)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setStyleSheet("""
            QTableWidget { 
                background-color: rgba(15, 23, 42, 0.6);
                alternate-background-color: rgba(30, 41, 59, 0.4);
                color: #e2e8f0; 
                border: 1px solid rgba(99, 102, 241, 0.15);
                border-radius: 12px;
                font-size: 13px;
            }
            QTableWidget::item { 
                padding: 10px 12px; 
                border-bottom: 1px solid rgba(99, 102, 241, 0.08);
            }
            QTableWidget::item:selected {
                background-color: rgba(99, 102, 241, 0.25);
            }
            QHeaderView::section { 
                background: rgba(30, 41, 59, 0.95);
                color: #a5b4fc; 
                font-weight: 700;
                font-size: 11px;
                padding: 14px 12px; 
                border: none;
                border-bottom: 2px solid rgba(99, 102, 241, 0.3);
                text-transform: uppercase;
            }
            QTableWidget QLineEdit {
                background: rgba(15, 23, 42, 0.8);
                color: #e2e8f0;
                border: 1px solid rgba(99, 102, 241, 0.3);
                border-radius: 4px;
                padding: 4px 8px;
            }
        """)
        self.table.cellChanged.connect(self._on_cell_changed)
        layout.addWidget(self.table)

        # ── Status + Save Row ──
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(12)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #94a3b8; font-size: 12px; background: transparent;")

        self.btn_save = QPushButton("💾  Save Changes")
        self.btn_save.setFixedHeight(46)
        self.btn_save.setFixedWidth(200)
        self.btn_save.setStyleSheet(BTN_SUCCESS)
        self.btn_save.clicked.connect(self._on_save)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedHeight(46)
        btn_cancel.setStyleSheet(BTN_GHOST)
        btn_cancel.clicked.connect(self.reject)

        bottom_layout.addWidget(self.lbl_status)
        bottom_layout.addStretch()
        bottom_layout.addWidget(btn_cancel)
        bottom_layout.addWidget(self.btn_save)
        layout.addLayout(bottom_layout)

    def _load_existing_data(self):
        """Load the current import data from database into the table."""
        rows = DataRepository.get_import_invoice_details(self.import_id)
        self.table.blockSignals(True)
        self.table.setRowCount(0)

        for name, phone, product, price, item_id, inv_id in rows:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(name or '')))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(phone or '')))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(product or '')))
            self.table.setItem(row_idx, 3, QTableWidgetItem(f"{price}" if price else "0"))

        self.table.blockSignals(False)
        self._update_stats()

    def _update_stats(self):
        """Update the stats label with row count and total."""
        row_count = self.table.rowCount()
        total = 0.0
        customers = set()
        for i in range(row_count):
            name_item = self.table.item(i, 0)
            price_item = self.table.item(i, 3)
            if name_item and name_item.text().strip():
                customers.add(name_item.text().strip().lower())
            if price_item:
                try:
                    total += float(price_item.text().replace('$', '').replace(',', ''))
                except ValueError:
                    pass
        self.lbl_stats.setText(f"{len(customers)} Customers  |  {row_count} Items  |  ${total:,.2f}")

    def _on_cell_changed(self, row, col):
        """Handle cell edits — apply fuzzy matching on product column."""
        if col == 2:  # Product column
            item = self.table.item(row, col)
            if item:
                product_val = item.text().strip()
                if product_val:
                    match, is_fuzzy = self.processor.find_match(product_val)
                    if is_fuzzy and match != product_val:
                        self.table.blockSignals(True)
                        item.setText(match)
                        item.setBackground(QColor(251, 191, 36, 40))
                        item.setToolTip(f"Auto-corrected from: {product_val}")
                        self.table.blockSignals(False)
        self._update_stats()

    def _add_empty_row(self):
        """Add a blank row at the bottom of the table."""
        row_idx = self.table.rowCount()
        self.table.insertRow(row_idx)
        self.table.setItem(row_idx, 0, QTableWidgetItem(""))
        self.table.setItem(row_idx, 1, QTableWidgetItem(""))
        self.table.setItem(row_idx, 2, QTableWidgetItem(""))
        self.table.setItem(row_idx, 3, QTableWidgetItem("0"))
        self.table.scrollToBottom()
        self.table.editItem(self.table.item(row_idx, 0))
        self._update_stats()

    def _delete_selected_rows(self):
        """Delete currently selected rows."""
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.information(self, "No Selection", "Select one or more rows to delete.")
            return

        reply = QMessageBox.question(
            self, "Delete Rows?",
            f"Delete {len(selected)} selected row(s)?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # Delete from bottom to top to preserve indices
            for idx in sorted(selected, key=lambda x: x.row(), reverse=True):
                self.table.removeRow(idx.row())
            self._update_stats()

    def _merge_from_excel(self):
        """Import rows from another Excel file and append them to the table."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel File to Merge", "", "Excel Files (*.xlsx *.xls)"
        )
        if not file_path:
            return

        df, error = ExcelParser.parse_invoice_data(file_path)
        if error:
            QMessageBox.critical(self, "Import Error", f"Failed to read file:\n\n{error}")
            return
        if df.empty:
            QMessageBox.warning(self, "No Data", "The selected file contains no valid rows.")
            return

        self._append_dataframe(df)
        self.lbl_status.setText(f"Merged {len(df)} rows from {file_path.split('/')[-1]}")

    def _paste_from_clipboard(self):
        """Read tab-separated data from clipboard and append to table."""
        clipboard = QApplication.clipboard()
        text = clipboard.text()

        if not text or not text.strip():
            QMessageBox.warning(self, "Empty Clipboard",
                "Nothing found in clipboard.\n\n"
                "Copy rows from Excel first (columns: Name, Phone, Product, Price).")
            return

        try:
            lines = text.strip().split('\n')
            rows = []

            for line in lines:
                parts = line.strip().split('\t')
                if not parts or all(p.strip() == '' for p in parts):
                    continue

                if len(parts) >= 4:
                    name = parts[0].strip().title()
                    phone = parts[1].strip()
                    product = parts[2].strip()
                    price_str = parts[3].strip()
                elif len(parts) == 3:
                    name = parts[0].strip().title()
                    phone = ''
                    product = parts[1].strip()
                    price_str = parts[2].strip()
                else:
                    continue

                if name.lower() in ('name', 'customer name', 'customer', 'nama'):
                    continue

                price_str = price_str.replace('$', '').replace(',', '').replace('RM', '').replace('rm', '').strip()
                try:
                    price = float(price_str)
                except ValueError:
                    price = 0.0

                rows.append({
                    'Customer Name': name,
                    'Phone': phone,
                    'Product': product,
                    'Price': price
                })

            if not rows:
                QMessageBox.warning(self, "No Valid Data",
                    "Could not parse any valid rows from clipboard.")
                return

            df = pd.DataFrame(rows)
            self._append_dataframe(df)
            self.lbl_status.setText(f"Pasted {len(rows)} rows from clipboard")

        except Exception as e:
            QMessageBox.critical(self, "Paste Error", f"Failed to parse clipboard data:\n\n{str(e)}")

    def _append_dataframe(self, df):
        """Append rows from a DataFrame to the table."""
        self.table.blockSignals(True)
        for _, row in df.iterrows():
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)

            name = str(row.get('Customer Name', '')).strip()
            phone = str(row.get('Phone', '')).strip()
            if phone.lower() in ('nan', 'none'):
                phone = ''

            product = str(row.get('Product', '')).strip()
            # Apply fuzzy matching
            match, is_fuzzy = self.processor.find_match(product)
            prod_item = QTableWidgetItem(match)
            if is_fuzzy and match != product:
                prod_item.setBackground(QColor(251, 191, 36, 40))
                prod_item.setToolTip(f"Auto-corrected from: {product}")

            price = row.get('Price', 0)
            try:
                price = float(price)
            except (ValueError, TypeError):
                price = 0.0

            self.table.setItem(row_idx, 0, QTableWidgetItem(name))
            self.table.setItem(row_idx, 1, QTableWidgetItem(phone))
            self.table.setItem(row_idx, 2, prod_item)
            self.table.setItem(row_idx, 3, QTableWidgetItem(f"{price}"))

        self.table.blockSignals(False)
        self._update_stats()

    def _on_save(self):
        """Save all changes: delete old invoices, re-create from current table data."""
        # 1. Validate — at least one row with a name
        row_count = self.table.rowCount()
        if row_count == 0:
            QMessageBox.warning(self, "No Data", "Cannot save — the table is empty.")
            return

        valid_rows = []
        for i in range(row_count):
            name_item = self.table.item(i, 0)
            name = name_item.text().strip() if name_item else ""
            if not name:
                continue

            phone_item = self.table.item(i, 1)
            phone = phone_item.text().strip() if phone_item else ""

            prod_item = self.table.item(i, 2)
            product = prod_item.text().strip() if prod_item else "Item"
            if not product:
                product = "Item"

            price_item = self.table.item(i, 3)
            price_str = price_item.text().strip() if price_item else "0"
            price_str = price_str.replace('$', '').replace(',', '')
            try:
                price = float(price_str)
            except ValueError:
                price = 0.0

            valid_rows.append({
                'Customer Name': name.title(),
                'Phone': phone,
                'Product': product,
                'Price': price
            })

        if not valid_rows:
            QMessageBox.warning(self, "No Valid Data",
                "All rows are empty or have no customer name.")
            return

        # 2. Confirm
        reply = QMessageBox.question(
            self, "Save Changes?",
            f"This will replace all invoices from this import with the current {len(valid_rows)} items.\n\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply != QMessageBox.Yes:
            return

        try:
            # 3. Delete old invoices for this import
            DataRepository.clear_import_invoices(self.import_id)

            # 4. Re-create invoices from current table data
            df = pd.DataFrame(valid_rows)
            df['Customer Name'] = df['Customer Name'].astype(str).str.strip().str.title()
            df['Phone'] = df['Phone'].astype(str).str.strip()

            grouped = df.groupby(['Customer Name', 'Phone'])
            total_saved = 0
            grand_total = 0
            new_invoice_ids = []

            for (name, phone), group in grouped:
                final_phone = phone
                if not phone or phone.lower() == 'nan' or phone == 'None' or phone.strip() == '':
                    found_phone = DataRepository.find_phone_by_name(name)
                    if found_phone:
                        final_phone = found_phone

                customer_id = DataRepository.upsert_customer(name, final_phone)
                invoice_items = []
                total_amount = 0

                for _, row in group.iterrows():
                    prod_name = str(row['Product'])
                    corrected_name, _ = self.processor.find_match(prod_name)
                    price = float(row['Price'])

                    invoice_items.append({'name': corrected_name, 'qty': 1, 'price': price})
                    total_amount += price

                ts = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                rand = random.randint(1000, 9999)
                inv_no = f"INV-{ts}-{customer_id}-{rand}"

                invoice_id = DataRepository.save_invoice(customer_id, inv_no, total_amount, invoice_items)
                new_invoice_ids.append(invoice_id)
                total_saved += 1
                grand_total += total_amount

            # 5. Update the import log
            DataRepository.update_import_log(
                self.import_id,
                len(grouped),
                total_saved,
                grand_total,
                new_invoice_ids
            )

            QMessageBox.information(self, "Saved",
                f"Updated import with {total_saved} invoices for {len(grouped)} customers.\n"
                f"Total: ${grand_total:,.2f}")

            self.import_updated.emit()
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save changes:\n\n{str(e)}")
