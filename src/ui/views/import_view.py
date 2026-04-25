from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QFileDialog, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QMessageBox, QApplication)
from PySide6.QtCore import Qt, Signal
import pandas as pd
from src.utils.excel_parser import ExcelParser
from src.core.processor import ProductProcessor

BTN_PRIMARY = """
    QPushButton { 
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #6366f1, stop:1 #4f46e5);
        border: none;
        border-radius: 8px; 
        padding: 10px 22px; 
        font-size: 13px; 
        font-weight: 700;
        color: #ffffff;
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
        border: none;
        border-radius: 8px; 
        padding: 10px 22px; 
        font-size: 13px; 
        font-weight: 700;
        color: #ffffff;
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
        border-radius: 8px; 
        padding: 8px 16px; 
        font-size: 12px; 
        font-weight: 600;
        color: #a5b4fc;
    }
    QPushButton:hover { 
        background: rgba(99, 102, 241, 0.15);
        border-color: #6366f1;
        color: #e0e7ff;
    }
"""

BTN_DANGER = """
    QPushButton { 
        background: rgba(239, 68, 68, 0.1); 
        border: 1px solid rgba(239, 68, 68, 0.2); 
        border-radius: 8px; 
        padding: 10px 22px; 
        font-size: 13px; 
        font-weight: 700;
        color: #f87171;
    }
    QPushButton:hover { 
        background: rgba(239, 68, 68, 0.2); 
        color: #ffffff; 
        border-color: #ef4444; 
    }
    QPushButton:disabled { background: #334155; color: #64748b; border-color: transparent; }
"""


class ImportView(QWidget):
    data_imported = Signal(list)  # Emits list of invoice IDs from current import

    def __init__(self):
        super().__init__()
        self.processor = ProductProcessor()
        self.setup_ui()
        self.raw_df = None

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 35, 40, 35)
        layout.setSpacing(20)
        self.setStyleSheet("background: #0f172a;")

        # Header with Back Button
        header_layout = QHBoxLayout()
        header = QLabel("Import Invoice Data")
        header.setStyleSheet("""
            font-size: 26px; 
            font-weight: 800; 
            color: #e2e8f0;
            background: transparent;
        """)
        
        header_layout.addWidget(header)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        sub_header = QLabel("Upload an Excel file or paste data from Excel to automatically group items by customer and create invoices.")
        sub_header.setStyleSheet("color: #64748b; font-size: 13px; background: transparent;")
        layout.addWidget(sub_header)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        self.btn_select_file = QPushButton("Select Excel File")
        self.btn_select_file.setFixedHeight(48)
        self.btn_select_file.setStyleSheet(BTN_PRIMARY)
        self.btn_select_file.clicked.connect(self.on_select_file)

        self.btn_paste = QPushButton("Paste from Excel")
        self.btn_paste.setFixedHeight(48)
        self.btn_paste.setStyleSheet(BTN_GHOST)
        self.btn_paste.setToolTip("Copy rows from Excel (Name, Phone, Product, Price) then click here to paste")
        self.btn_paste.clicked.connect(self.on_paste_from_clipboard)
        
        self.btn_process = QPushButton("Process and Save")
        self.btn_process.setFixedHeight(48)
        self.btn_process.setEnabled(False)
        self.btn_process.setStyleSheet(BTN_SUCCESS)
        self.btn_process.clicked.connect(self.on_process_save)

        self.btn_clean = QPushButton("Clean Table")
        self.btn_clean.setFixedHeight(48)
        self.btn_clean.setEnabled(False)
        self.btn_clean.setStyleSheet(BTN_DANGER)
        self.btn_clean.clicked.connect(self.on_clean_table)

        btn_layout.addWidget(self.btn_select_file)
        btn_layout.addWidget(self.btn_paste)
        btn_layout.addWidget(self.btn_process)
        btn_layout.addWidget(self.btn_clean)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Status Label
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #a5b4fc; font-weight: 700; font-size: 13px; background: transparent;")
        layout.addWidget(self.lbl_status)

        # Preview Table
        self.lbl_preview = QLabel("Excel Data Preview")
        self.lbl_preview.setStyleSheet("font-weight: 700; color: #94a3b8; font-size: 14px; background: transparent;")
        layout.addWidget(self.lbl_preview)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Name", "Phone", "Product", "Price"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
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
                background-color: rgba(99, 102, 241, 0.2);
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
        """)
        layout.addWidget(self.table)

    def on_select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel File", "", "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            self.lbl_status.setText("Reading file...")
            self.raw_df, error = ExcelParser.parse_invoice_data(file_path)
            if error:
                QMessageBox.critical(self, "Import Error", f"Failed to read file:\n\n{error}")
                self.lbl_status.setText("")
                self.btn_process.setEnabled(False)
            elif not self.raw_df.empty:
                self.display_data()
                self.lbl_status.setText(f"Found {len(self.raw_df)} items. Ready to process.")
                self.btn_process.setEnabled(True)
                self.btn_clean.setEnabled(True)
                self.last_file_path = file_path
                
                # Archive the file
                try:
                    import shutil
                    import os
                    from datetime import datetime
                    from src.utils.paths import get_import_archive_dir
                    
                    archive_dir = get_import_archive_dir()
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = os.path.basename(file_path)
                    archive_path = os.path.join(archive_dir, f"{timestamp}_{filename}")
                    
                    shutil.copy2(file_path, archive_path)
                    print(f"Excel archived to: {archive_path}")
                except Exception as archive_err:
                    print(f"Warning: Failed to archive excel: {archive_err}")
            else:
                QMessageBox.warning(self, "No Data", "The selected file contains no valid rows.")
                self.lbl_status.setText("")
                self.btn_process.setEnabled(False)
                self.btn_clean.setEnabled(False)

    def on_paste_from_clipboard(self):
        """Reads tab-separated data from clipboard (Excel copy format) and loads it."""
        clipboard = QApplication.clipboard()
        text = clipboard.text()

        if not text or not text.strip():
            QMessageBox.warning(self, "Empty Clipboard", 
                "Nothing found in clipboard.\n\n"
                "Copy rows from Excel first (columns: Name, Phone, Product, Price), then click this button.")
            return

        try:
            lines = text.strip().split('\n')
            rows = []

            for line in lines:
                # Excel copies as tab-separated values
                parts = line.strip().split('\t')
                if not parts or all(p.strip() == '' for p in parts):
                    continue

                # Support 3 columns (Name, Product, Price) or 4 columns (Name, Phone, Product, Price)
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
                    continue  # Skip rows with too few columns

                # Skip header rows — check if this looks like a header
                if name.lower() in ('name', 'customer name', 'customer', 'nama'):
                    continue

                # Parse price — remove currency symbols and commas
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
                    "Could not parse any valid rows from clipboard.\n\n"
                    "Make sure your Excel data has columns:\n"
                    "Name | Phone | Product | Price\n\n"
                    "Or at minimum:\n"
                    "Name | Product | Price")
                return

            self.raw_df = pd.DataFrame(rows)
            self.display_data()
            self.lbl_status.setText(f"Pasted {len(rows)} items from clipboard. Ready to process.")
            self.btn_process.setEnabled(True)
            self.btn_clean.setEnabled(True)
            self.last_file_path = "Clipboard Paste"

        except Exception as e:
            QMessageBox.critical(self, "Paste Error", f"Failed to parse clipboard data:\n\n{str(e)}")

    def on_clean_table(self):
        """Cleans the preview table and resets state."""
        self.table.setRowCount(0)
        self.raw_df = None
        self.lbl_status.setText("")
        self.btn_process.setEnabled(False)
        self.btn_clean.setEnabled(False)

    def display_data(self):
        self.table.setRowCount(0)
        for idx, row in self.raw_df.iterrows():
            self.table.insertRow(idx)
            
            name_item = QTableWidgetItem(str(row.get('Customer Name', '')))
            self.table.setItem(idx, 0, name_item)
            
            phone_item = QTableWidgetItem(str(row.get('Phone', '')))
            self.table.setItem(idx, 1, phone_item)
            
            # Product with Fuzzy Check
            product_val = str(row.get('Product', ''))
            match, is_fuzzy = self.processor.find_match(product_val)
            prod_item = QTableWidgetItem(match)
            if is_fuzzy and match != product_val:
                from PySide6.QtGui import QColor
                prod_item.setBackground(QColor(251, 191, 36, 40))
                prod_item.setToolTip(f"Suggesting: {match}")
            self.table.setItem(idx, 2, prod_item)
            
            price_val = row.get('Price', 0)
            self.table.setItem(idx, 3, QTableWidgetItem(f"{price_val}"))

    def on_process_save(self):
        if self.raw_df is None or self.raw_df.empty:
            return

        from src.database.repository import DataRepository
        import datetime
        import random
        import os
        
        self.lbl_status.setText("Processing & saving to database...")
        self.btn_process.setEnabled(False)
        self.btn_select_file.setEnabled(False)

        try:
            self.raw_df['Customer Name'] = self.raw_df['Customer Name'].astype(str).str.strip().str.title()
            self.raw_df['Phone'] = self.raw_df['Phone'].astype(str).str.strip()
            
            grouped = self.raw_df.groupby(['Customer Name', 'Phone'])
            total_saved = 0
            grand_total = 0
            imported_invoice_ids = []  # Track which invoices were just created
            
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
                
                date_str = datetime.datetime.now().strftime('%d%m%Y')
                rand = random.randint(1000, 9999)
                inv_no = f"INV-{date_str}-{rand}"
                
                invoice_id = DataRepository.save_invoice(customer_id, inv_no, total_amount, invoice_items)
                imported_invoice_ids.append(invoice_id)
                total_saved += 1
                grand_total += total_amount

            # Log the import event for the dashboard
            file_name = os.path.basename(self.last_file_path) if hasattr(self, 'last_file_path') else "Excel Import"
            DataRepository.log_import(file_name, len(grouped), total_saved, grand_total, imported_invoice_ids)

            QMessageBox.information(self, "Import Complete", 
                f"Created <b>{total_saved}</b> invoices for <b>{len(grouped)}</b> customers.")
            self.lbl_status.setText("")
            self.btn_select_file.setEnabled(True)
            self.data_imported.emit(imported_invoice_ids)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save data: {str(e)}")
            self.btn_select_file.setEnabled(True)
            self.lbl_status.setText("Error occurred.")
