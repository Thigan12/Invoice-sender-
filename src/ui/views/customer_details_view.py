from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                                QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                                QHeaderView, QMessageBox, QDialog, QFormLayout,
                                QFileDialog, QRadioButton, QButtonGroup,
                                QGroupBox, QApplication)
from PySide6.QtCore import Qt, Signal
from src.database.repository import DataRepository

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
    QPushButton:disabled { color: #475569; border-color: rgba(71, 85, 105, 0.2); }
"""

BTN_PRIMARY = """
    QPushButton { 
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #6366f1, stop:1 #4f46e5);
        border: none;
        border-radius: 8px; 
        padding: 8px 18px; 
        font-size: 12px; 
        font-weight: 700;
        color: #ffffff;
    }
    QPushButton:hover { 
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #818cf8, stop:1 #6366f1);
    }
"""

BTN_DANGER = """
    QPushButton { 
        background: rgba(239, 68, 68, 0.1); 
        border: 1px solid rgba(239, 68, 68, 0.2); 
        border-radius: 8px; 
        padding: 8px 18px; 
        font-size: 12px; 
        font-weight: 700;
        color: #f87171;
    }
    QPushButton:hover { 
        background: rgba(239, 68, 68, 0.2); 
        color: #ffffff; 
        border-color: #ef4444; 
    }
"""

BTN_IMPORT = """
    QPushButton {
        background: rgba(56, 189, 248, 0.1);
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 12px;
        font-weight: 700;
        color: #38bdf8;
    }
    QPushButton:hover {
        background: rgba(56, 189, 248, 0.2);
        color: #ffffff;
        border-color: #0ea5e9;
    }
"""

BTN_EXPORT = """
    QPushButton {
        background: rgba(34, 197, 94, 0.1);
        border: 1px solid rgba(34, 197, 94, 0.25);
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 12px;
        font-weight: 700;
        color: #4ade80;
    }
    QPushButton:hover {
        background: rgba(34, 197, 94, 0.2);
        color: #ffffff;
        border-color: #22c55e;
    }
"""


class CustomerEditDialog(QDialog):
    def __init__(self, parent=None, name="", phone="", address=""):
        super().__init__(parent)
        self.setWindowTitle("Edit Customer")
        self.setFixedWidth(440)
        self.setStyleSheet("""
            QDialog { 
                background-color: #1e293b; 
                color: #e2e8f0;
                border-radius: 12px;
            }
        """)
        
        layout = QFormLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)
        
        title = QLabel("Edit Customer Details")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #a5b4fc; padding-bottom: 8px;")
        layout.addRow(title)
        
        field_style = """
            QLineEdit {
                background-color: #0f172a;
                border: 1px solid rgba(99, 102, 241, 0.3);
                border-radius: 8px;
                padding: 10px 12px;
                color: #e2e8f0;
                font-size: 13px;
            }
            QLineEdit:focus { border-color: #6366f1; }
        """

        lbl_name = QLabel("Name:")
        lbl_name.setStyleSheet("color: #94a3b8; font-weight: 600;")
        self.name_input = QLineEdit(name)
        self.name_input.setStyleSheet(field_style)
        
        lbl_phone = QLabel("Phone / Mobile:")
        lbl_phone.setStyleSheet("color: #94a3b8; font-weight: 600;")
        self.phone_input = QLineEdit(phone)
        self.phone_input.setStyleSheet(field_style)

        lbl_address = QLabel("Address:")
        lbl_address.setStyleSheet("color: #94a3b8; font-weight: 600;")
        self.address_input = QLineEdit(address or "")
        self.address_input.setPlaceholderText("Optional — street, city, postcode…")
        self.address_input.setStyleSheet(field_style)
        
        layout.addRow(lbl_name, self.name_input)
        layout.addRow(lbl_phone, self.phone_input)
        layout.addRow(lbl_address, self.address_input)
        
        btns = QHBoxLayout()
        btns.setSpacing(10)
        self.btn_save = QPushButton("Save")
        self.btn_save.setStyleSheet(BTN_PRIMARY)
        self.btn_save.setFixedHeight(38)
        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet(BTN_GHOST)
        self.btn_cancel.setFixedHeight(38)
        self.btn_cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_save)
        layout.addRow(btns)

    def get_data(self):
        return (
            self.name_input.text().strip(),
            self.phone_input.text().strip(),
            self.address_input.text().strip()
        )


class CustomerDetailsView(QWidget):
    customer_updated = Signal()

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 35, 40, 35)
        layout.setSpacing(20)
        self.setStyleSheet("background: #0f172a;")

        # Header
        header_layout = QHBoxLayout()
        header = QLabel("Manage Customers")
        header.setStyleSheet("""
            font-size: 26px; 
            font-weight: 800; 
            color: #e2e8f0;
            background: transparent;
        """)
        
        self.btn_add = QPushButton("➕  Add New")
        self.btn_add.setFixedHeight(38)
        self.btn_add.setStyleSheet(BTN_PRIMARY)
        self.btn_add.clicked.connect(self.on_add_new)

        self.btn_import = QPushButton("📥  Import")
        self.btn_import.setFixedHeight(38)
        self.btn_import.setToolTip("Import customers from Excel or PDF")
        self.btn_import.setStyleSheet(BTN_IMPORT)
        self.btn_import.clicked.connect(self._on_import)

        self.btn_export = QPushButton("📤  Export")
        self.btn_export.setFixedHeight(38)
        self.btn_export.setToolTip("Export customer list to Excel or PDF")
        self.btn_export.setStyleSheet(BTN_EXPORT)
        self.btn_export.clicked.connect(self._on_export)

        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_import)
        header_layout.addWidget(self.btn_export)
        header_layout.addWidget(self.btn_add)
        layout.addLayout(header_layout)

        # ── Selection toolbar (Select All + Delete Selected) ──
        sel_bar = QHBoxLayout()
        sel_bar.setSpacing(10)

        self.btn_select_all = QPushButton("☑  Select All")
        self.btn_select_all.setFixedHeight(34)
        self.btn_select_all.setStyleSheet("""
            QPushButton {
                background: rgba(99,102,241,0.1);
                border: 1px solid rgba(99,102,241,0.25);
                border-radius: 7px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 700;
                color: #a5b4fc;
            }
            QPushButton:hover {
                background: rgba(99,102,241,0.2);
                color: #e0e7ff;
                border-color: #6366f1;
            }
        """)
        self.btn_select_all.clicked.connect(self._on_select_all_toggle)
        self._all_selected = False

        self.btn_delete_selected = QPushButton("🗑  Delete Selected (0)")
        self.btn_delete_selected.setFixedHeight(34)
        self.btn_delete_selected.setEnabled(False)
        self.btn_delete_selected.setStyleSheet("""
            QPushButton {
                background: rgba(239,68,68,0.1);
                border: 1px solid rgba(239,68,68,0.2);
                border-radius: 7px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 700;
                color: #f87171;
            }
            QPushButton:hover {
                background: rgba(239,68,68,0.2);
                color: #ffffff;
                border-color: #ef4444;
            }
            QPushButton:disabled {
                background: rgba(30,41,59,0.3);
                border-color: rgba(71,85,105,0.2);
                color: #475569;
            }
        """)
        self.btn_delete_selected.clicked.connect(self._on_delete_selected)

        sel_bar.addWidget(self.btn_select_all)
        sel_bar.addWidget(self.btn_delete_selected)
        sel_bar.addStretch()
        layout.addLayout(sel_bar)

        # ── Table — 5 cols: ☑ | Name | Phone | Address | Actions ──
        self.table = QTableWidget(0, 5)
        self.table.verticalHeader().setDefaultSectionSize(56)
        self.table.setHorizontalHeaderLabels(["", "Name", "Phone", "Address", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 40)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
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
                padding: 12px; 
                border-bottom: 1px solid rgba(99, 102, 241, 0.08);
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

    def _checked_count(self):
        """Returns the number of checked rows."""
        count = 0
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.Checked:
                count += 1
        return count

    def _update_delete_btn(self):
        n = self._checked_count()
        self.btn_delete_selected.setText(f"🗑  Delete Selected ({n})")
        self.btn_delete_selected.setEnabled(n > 0)

    def refresh_data(self):
        # Disconnect itemChanged while building to avoid spurious callbacks
        try:
            self.table.itemChanged.disconnect()
        except RuntimeError:
            pass

        self.table.setUpdatesEnabled(False)  # freeze repaints for speed
        customers = DataRepository.get_all_master_customers()
        self.table.setRowCount(0)
        self._all_selected = False
        self.btn_select_all.setText("☑  Select All")

        for i, (cid, name, phone, address) in enumerate(customers):
            self.table.insertRow(i)

            # Col 0 — Checkbox
            chk_item = QTableWidgetItem()
            chk_item.setCheckState(Qt.Unchecked)
            chk_item.setData(Qt.UserRole, cid)   # store customer id
            chk_item.setTextAlignment(Qt.AlignCenter)
            chk_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            self.table.setItem(i, 0, chk_item)

            # Col 1 — Name
            name_item = QTableWidgetItem(name)
            name_item.setForeground(Qt.white)
            name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(i, 1, name_item)

            # Col 2 — Phone
            phone_item = QTableWidgetItem(phone or "—")
            phone_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(i, 2, phone_item)

            # Col 3 — Address
            addr_item = QTableWidgetItem(address or "—")
            addr_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(i, 3, addr_item)

            # Col 4 — Action buttons
            btn_box = QWidget()
            btn_box.setStyleSheet("background: transparent;")
            btn_layout = QHBoxLayout(btn_box)
            btn_layout.setContentsMargins(8, 0, 8, 0)
            btn_layout.setSpacing(8)
            btn_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

            btn_edit = QPushButton("Edit")
            btn_edit.setStyleSheet(BTN_GHOST)
            btn_edit.setFixedHeight(30)
            btn_edit.setFixedWidth(70)
            btn_edit.clicked.connect(lambda checked, c=cid, n=name, p=phone, a=address: self.on_edit(c, n, p, a))

            btn_del = QPushButton("Delete")
            btn_del.setStyleSheet(BTN_DANGER)
            btn_del.setFixedHeight(30)
            btn_del.setFixedWidth(70)
            btn_del.clicked.connect(lambda checked, c=cid, n=name: self.on_delete(c, n))

            btn_layout.addWidget(btn_edit)
            btn_layout.addWidget(btn_del)
            self.table.setCellWidget(i, 4, btn_box)

        # Reconnect itemChanged and re-enable painting
        self.table.itemChanged.connect(self._on_item_changed)
        self.table.setUpdatesEnabled(True)
        self._update_delete_btn()

    def _on_item_changed(self, item):
        if item and item.column() == 0:
            self._update_delete_btn()

    def _on_select_all_toggle(self):
        self._all_selected = not self._all_selected
        state = Qt.Checked if self._all_selected else Qt.Unchecked
        self.btn_select_all.setText("☐  Deselect All" if self._all_selected else "☑  Select All")
        try:
            self.table.itemChanged.disconnect()
        except RuntimeError:
            pass
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(state)
        self.table.itemChanged.connect(self._on_item_changed)
        self._update_delete_btn()

    def _on_delete_selected(self):
        # Collect selected customer IDs and names
        selected = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.Checked:
                cid  = item.data(Qt.UserRole)
                name = self.table.item(row, 1).text() if self.table.item(row, 1) else str(cid)
                selected.append((cid, name))

        if not selected:
            return

        n = len(selected)
        reply = QMessageBox.question(
            self, "Confirm Bulk Delete",
            f"Are you sure you want to delete <b>{n} customer{'s' if n > 1 else ''}</b>?<br><br>"
            "Their historical invoices will be preserved in the database.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        errors = []
        for cid, name in selected:
            try:
                DataRepository.delete_customer_by_id(cid)
            except Exception as e:
                errors.append(f"{name}: {e}")

        if errors:
            QMessageBox.warning(self, "Partial Delete",
                f"Some customers could not be deleted:\n\n" + "\n".join(errors))
        else:
            QMessageBox.information(self, "Done",
                f"✔ Deleted <b>{n}</b> customer{'s' if n > 1 else ''} successfully.")

        self.refresh_data()
        self.customer_updated.emit()

    # ── Format Picker ──────────────────────────────────────────────────────
    def _format_picker(self, title):
        """
        Shows a small dialog asking 'Excel or PDF?'.
        Returns 'excel', 'pdf', or None if cancelled.
        """
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setFixedSize(300, 160)
        dlg.setStyleSheet("""
            QDialog { background: #1e293b; }
            QLabel  { color: #e2e8f0; font-size: 13px; background: transparent; }
            QRadioButton { color: #e2e8f0; font-size: 13px; background: transparent; spacing: 8px; }
            QRadioButton::indicator { width: 16px; height: 16px; }
            QRadioButton::indicator:checked { background: #6366f1; border-radius: 8px; border: 2px solid #818cf8; }
            QRadioButton::indicator:unchecked { background: #334155; border-radius: 8px; border: 2px solid #475569; }
        """)

        vbox = QVBoxLayout(dlg)
        vbox.setContentsMargins(24, 20, 24, 20)
        vbox.setSpacing(14)

        lbl = QLabel("Choose file format:")
        lbl.setStyleSheet("font-weight: 700; color: #a5b4fc; font-size: 14px; background: transparent;")
        vbox.addWidget(lbl)

        rb_excel = QRadioButton("📊  Excel (.xlsx)")
        rb_excel.setChecked(True)
        rb_pdf   = QRadioButton("📄  PDF (.pdf)")
        vbox.addWidget(rb_excel)
        vbox.addWidget(rb_pdf)

        btn_row = QHBoxLayout()
        btn_ok = QPushButton("Continue")
        btn_ok.setFixedHeight(34)
        btn_ok.setStyleSheet(BTN_PRIMARY)
        btn_ok.clicked.connect(dlg.accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedHeight(34)
        btn_cancel.setStyleSheet(BTN_GHOST)
        btn_cancel.clicked.connect(dlg.reject)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        vbox.addLayout(btn_row)

        if dlg.exec_() == QDialog.Accepted:
            return 'excel' if rb_excel.isChecked() else 'pdf'
        return None

    # ── Import ─────────────────────────────────────────────────────────────
    def _on_import(self):
        fmt = self._format_picker("Import Customers")
        if fmt is None:
            return

        if fmt == 'excel':
            path, _ = QFileDialog.getOpenFileName(
                self, "Select Excel File", "",
                "Excel Files (*.xlsx *.xls)"
            )
            if not path:
                return
            records, error = self._parse_excel(path)
        else:
            path, _ = QFileDialog.getOpenFileName(
                self, "Select PDF File", "",
                "PDF Files (*.pdf)"
            )
            if not path:
                return
            records, error = self._parse_pdf(path)

        if error:
            QMessageBox.critical(self, "Import Error", f"Could not read file:\n\n{error}")
            return
        if not records:
            QMessageBox.warning(self, "No Data", "No valid customer rows found in the file.")
            return

        try:
            added, updated, skipped = DataRepository.import_customers_bulk(records)
            QMessageBox.information(
                self, "Import Complete",
                f"<b>{added}</b> new customer{'s' if added != 1 else ''} added<br>"
                f"<b>{updated}</b> existing updated (address)<br>"
                f"<b>{skipped}</b> row{'s' if skipped != 1 else ''} skipped"
            )
            self.refresh_data()
            self.customer_updated.emit()
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))

    def _parse_excel(self, path):
        try:
            import pandas as pd
            df = pd.read_excel(path, dtype=str)
            df.columns = [str(c).strip() for c in df.columns]

            def _detect(cols, candidates):
                for col in cols:
                    c = col.lower().replace(' ', '').replace('_', '')
                    for k in candidates:
                        if k in c:
                            return col
                return None

            name_col  = _detect(df.columns, ['name','customername','customer','nama','fullname']) or (df.columns[0] if len(df.columns) > 0 else None)
            phone_col = _detect(df.columns, ['phone','mobile','contact','hp','tel','number','no']) or (df.columns[1] if len(df.columns) > 1 else None)
            addr_col  = _detect(df.columns, ['address','addr','alamat','location','street']) or (df.columns[2] if len(df.columns) > 2 else None)

            records = []
            for _, row in df.iterrows():
                def _val(col):
                    if not col: return ''
                    v = str(row.get(col, '')).strip()
                    return '' if v.lower() in ('nan','none','null') else v
                name = _val(name_col)
                if name:
                    records.append({'name': name, 'phone': _val(phone_col), 'address': _val(addr_col)})

            if not records:
                return [], "No valid rows found. Ensure the file has a Name column."
            return records, None
        except ImportError:
            return [], "pandas/openpyxl not installed. Run: pip install pandas openpyxl"
        except Exception as e:
            return [], str(e)

    def _parse_pdf(self, path):
        try:
            import pdfplumber, re
            records = []
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            if not table: continue
                            header = [str(c or '').strip().lower() for c in table[0]]
                            ni = next((i for i,h in enumerate(header) if any(k in h for k in ['name','nama','customer'])), 0)
                            pi = next((i for i,h in enumerate(header) if any(k in h for k in ['phone','mobile','no','tel','hp','contact'])), 1)
                            ai = next((i for i,h in enumerate(header) if any(k in h for k in ['address','addr','alamat','location'])), 2)
                            start = 1 if any(k in header[0] for k in ['name','nama','customer']) else 0
                            for r in table[start:]:
                                if not r: continue
                                def _cell(i):
                                    v = str(r[i] or '').strip() if i < len(r) else ''
                                    return '' if v.lower() in ('nan','none') else v
                                name = _cell(ni)
                                if name:
                                    records.append({'name': name, 'phone': _cell(pi), 'address': _cell(ai)})
                    else:
                        text = page.extract_text() or ''
                        for line in text.split('\n'):
                            parts = [p.strip() for p in re.split(r'\t|  +', line.strip()) if p.strip()]
                            if len(parts) >= 2 and parts[0].lower() not in ('name','customer','nama'):
                                records.append({'name': parts[0], 'phone': parts[1] if len(parts)>1 else '', 'address': parts[2] if len(parts)>2 else ''})
            if not records:
                return [], "No rows could be extracted. PDF must have a table or 3-column text rows."
            return records, None
        except ImportError:
            return [], "pdfplumber not installed. Run: pip install pdfplumber"
        except Exception as e:
            return [], str(e)

    # ── Export ─────────────────────────────────────────────────────────────
    def _on_export(self):
        fmt = self._format_picker("Export Customers")
        if fmt is None:
            return

        customers = DataRepository.get_all_master_customers()  # id, name, phone, address
        if not customers:
            QMessageBox.warning(self, "No Data", "There are no customers to export.")
            return

        if fmt == 'excel':
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Excel File", "customers.xlsx",
                "Excel Files (*.xlsx)"
            )
            if path:
                self._do_excel_export(customers, path)
        else:
            path, _ = QFileDialog.getSaveFileName(
                self, "Save PDF File", "customers.pdf",
                "PDF Files (*.pdf)"
            )
            if path:
                self._do_pdf_export(customers, path)

    def _do_excel_export(self, customers, path):
        try:
            import pandas as pd
            data = [
                {'Name': c[1], 'Phone': c[2] or '', 'Address': c[3] or ''}
                for c in customers
            ]
            df = pd.DataFrame(data)
            with pd.ExcelWriter(path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Customers')
                ws = writer.sheets['Customers']
                # Auto-width columns
                for col in ws.columns:
                    max_len = max(len(str(cell.value or '')) for cell in col)
                    ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 60)
            QMessageBox.information(self, "Export Complete",
                f"✔ Exported <b>{len(customers)}</b> customers to:<br><br>{path}")
        except ImportError:
            QMessageBox.critical(self, "Error", "pandas/openpyxl not installed.\nRun: pip install pandas openpyxl")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def _do_pdf_export(self, customers, path):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import mm

            doc = SimpleDocTemplate(path, pagesize=A4,
                                    leftMargin=15*mm, rightMargin=15*mm,
                                    topMargin=20*mm, bottomMargin=20*mm)
            styles = getSampleStyleSheet()
            elements = []

            # Title
            title_style = ParagraphStyle('title', fontSize=18, fontName='Helvetica-Bold',
                                         textColor=colors.HexColor('#1e293b'), spaceAfter=6)
            elements.append(Paragraph("Customer List", title_style))

            sub_style = ParagraphStyle('sub', fontSize=9, fontName='Helvetica',
                                       textColor=colors.HexColor('#64748b'), spaceAfter=14)
            from datetime import datetime
            elements.append(Paragraph(f"Exported: {datetime.now().strftime('%d %b %Y %H:%M')}  |  Total: {len(customers)} customers", sub_style))

            # Table data
            header_row = ['#', 'Name', 'Phone', 'Address']
            table_data = [header_row]
            for idx, c in enumerate(customers, 1):
                table_data.append([str(idx), c[1] or '', c[2] or '', c[3] or ''])

            col_widths = [10*mm, 55*mm, 40*mm, 75*mm]
            tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
            tbl.setStyle(TableStyle([
                # Header
                ('BACKGROUND',  (0,0), (-1,0), colors.HexColor('#4f46e5')),
                ('TEXTCOLOR',   (0,0), (-1,0), colors.white),
                ('FONTNAME',    (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE',    (0,0), (-1,0), 9),
                ('ALIGN',       (0,0), (-1,0), 'CENTER'),
                ('BOTTOMPADDING', (0,0), (-1,0), 8),
                ('TOPPADDING',  (0,0), (-1,0), 8),
                # Data rows
                ('FONTNAME',    (0,1), (-1,-1), 'Helvetica'),
                ('FONTSIZE',    (0,1), (-1,-1), 8),
                ('TEXTCOLOR',   (0,1), (-1,-1), colors.HexColor('#1e293b')),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f1f5f9')]),
                ('ALIGN',       (0,1), (0,-1), 'CENTER'),
                ('TOPPADDING',  (0,1), (-1,-1), 7),
                ('BOTTOMPADDING', (0,1), (-1,-1), 7),
                # Grid
                ('LINEBELOW',   (0,0), (-1,0), 1, colors.HexColor('#4f46e5')),
                ('LINEBELOW',   (0,1), (-1,-1), 0.3, colors.HexColor('#e2e8f0')),
                ('BOX',         (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ]))
            elements.append(tbl)
            doc.build(elements)

            QMessageBox.information(self, "Export Complete",
                f"✔ Exported <b>{len(customers)}</b> customers to:<br><br>{path}")
        except ImportError:
            QMessageBox.critical(self, "Error", "reportlab not installed.\nRun: pip install reportlab")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def on_save_inline(self, cust_id, row_idx):
        """Allows direct saving if table was edited (future proofing) or just confirms."""
        name = self.table.item(row_idx, 0).text().strip()
        phone = self.table.item(row_idx, 1).text().strip()
        
        if not name:
            QMessageBox.warning(self, "Error", "Name cannot be empty.")
            return
            
        DataRepository.update_customer_info(cust_id, name, phone)
        QMessageBox.information(self, "Success", "Customer details saved.")
        self.customer_updated.emit()
        self.refresh_data()

    def on_add_new(self):
        dialog = CustomerEditDialog(self, "", "", "")
        dialog.setWindowTitle("Add New Customer")
        if dialog.exec_() == QDialog.Accepted:
            new_name, new_phone, new_address = dialog.get_data()
            if not new_name:
                QMessageBox.warning(self, "Error", "Name cannot be empty.")
                return
            
            DataRepository.upsert_customer(new_name, new_phone, new_address or None)
            self.refresh_data()
            self.customer_updated.emit()
            QMessageBox.information(self, "Success", f"Customer <b>{new_name}</b> added successfully.")

    def on_edit(self, cust_id, old_name, old_phone, old_address=None):
        dialog = CustomerEditDialog(self, old_name, old_phone or "", old_address or "")
        if dialog.exec_() == QDialog.Accepted:
            new_name, new_phone, new_address = dialog.get_data()
            if not new_name:
                QMessageBox.warning(self, "Error", "Name cannot be empty.")
                return
                
            DataRepository.update_customer_info(cust_id, new_name, new_phone, new_address or None)
            self.refresh_data()
            self.customer_updated.emit()
            QMessageBox.information(self, "Success", "Customer details updated.")

    def on_delete(self, cust_id, name):
        reply = QMessageBox.question(self, "Confirm Delete", 
                                   f"Are you sure you want to remove <b>{name}</b> from the master list?<br><br>"
                                   "This will delete the customer record, but their historical invoices will be preserved in the database.",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                DataRepository.delete_customer_by_id(cust_id)
                self.refresh_data()
                self.customer_updated.emit()
                QMessageBox.information(self, "Deleted", f"Customer <b>{name}</b> and all their data has been removed.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete customer: {str(e)}")
