from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QScrollArea, QFrame, QTableWidget,
                               QTableWidgetItem, QHeaderView, QMessageBox,
                               QFileDialog, QCheckBox, QSizePolicy)
from PySide6.QtCore import Qt, Signal
import datetime
from src.database.repository import DataRepository


class ImportSelectCard(QFrame):
    """A card representing an import event, with a checkbox for selection."""
    def __init__(self, import_id, file_name, date_str, cust_count, inv_count, total_val):
        super().__init__()
        self.import_id = import_id
        self.checked = False

        try:
            dt = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                dt = datetime.datetime.fromisoformat(date_str)
            except:
                dt = datetime.datetime.now()

        formatted_date = dt.strftime('%b %d, %Y at %H:%M')

        self.setStyleSheet("""
            QFrame {
                background: rgba(30, 41, 59, 0.4);
                border: 1px solid rgba(99, 102, 241, 0.1);
                border-radius: 12px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        # Checkbox
        self.chk = QCheckBox()
        self.chk.setStyleSheet("""
            QCheckBox::indicator {
                width: 20px; height: 20px;
                border-radius: 4px;
                border: 2px solid #475569;
                background: #0f172a;
            }
            QCheckBox::indicator:checked {
                background: #6366f1;
                border-color: #818cf8;
            }
        """)
        self.chk.toggled.connect(self._on_toggle)
        layout.addWidget(self.chk)

        # Date badge
        date_badge = QFrame()
        date_badge.setFixedSize(48, 48)
        date_badge.setStyleSheet("""
            QFrame {
                background: rgba(99, 102, 241, 0.12);
                border: 1px solid rgba(99, 102, 241, 0.2);
                border-radius: 8px;
            }
        """)
        badge_layout = QVBoxLayout(date_badge)
        badge_layout.setContentsMargins(0, 3, 0, 3)
        badge_layout.setSpacing(0)
        badge_layout.setAlignment(Qt.AlignCenter)
        day_lbl = QLabel(dt.strftime('%d'))
        day_lbl.setAlignment(Qt.AlignCenter)
        day_lbl.setStyleSheet("color: #a5b4fc; font-size: 16px; font-weight: 800; background: transparent; border: none;")
        month_lbl = QLabel(dt.strftime('%b'))
        month_lbl.setAlignment(Qt.AlignCenter)
        month_lbl.setStyleSheet("color: #64748b; font-size: 9px; font-weight: 600; text-transform: uppercase; background: transparent; border: none;")
        badge_layout.addWidget(day_lbl)
        badge_layout.addWidget(month_lbl)
        layout.addWidget(date_badge)

        # Info
        info = QVBoxLayout()
        info.setSpacing(2)
        name_lbl = QLabel(file_name)
        name_lbl.setStyleSheet("color: #e2e8f0; font-weight: 700; font-size: 13px; background: transparent;")
        date_lbl = QLabel(formatted_date)
        date_lbl.setStyleSheet("color: #64748b; font-size: 11px; background: transparent;")
        info.addWidget(name_lbl)
        info.addWidget(date_lbl)
        layout.addLayout(info)

        layout.addStretch()

        # Stats
        safe_val = total_val if total_val is not None else 0.0
        stats_lbl = QLabel(f"{cust_count} Customers  |  {inv_count} Invoices  |  ${safe_val:,.2f}")
        stats_lbl.setStyleSheet("color: #a5b4fc; font-size: 12px; background: transparent;")
        layout.addWidget(stats_lbl)

    def _on_toggle(self, checked):
        self.checked = checked
        if checked:
            self.setStyleSheet("""
                QFrame {
                    background: rgba(99, 102, 241, 0.1);
                    border: 1px solid rgba(99, 102, 241, 0.4);
                    border-radius: 12px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background: rgba(30, 41, 59, 0.4);
                    border: 1px solid rgba(99, 102, 241, 0.1);
                    border-radius: 12px;
                }
            """)


class DeliveryView(QWidget):
    """Page for building and exporting delivery lists."""

    def __init__(self):
        super().__init__()
        self._import_cards = []
        self._customer_data = []  # list of (name, phone, address)
        self.setup_ui()
        self.refresh_imports()

    def setup_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("background: #0f172a;")

        # Wrap everything in a scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: #0f172a; }")

        content = QWidget()
        content.setStyleSheet("background: #0f172a;")
        self.main_layout = QVBoxLayout(content)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Delivery List")
        title.setStyleSheet("font-size: 32px; font-weight: 800; color: #f8fafc; background: transparent;")
        subtitle = QLabel("Select imports, review customers, and export delivery list for your driver.")
        subtitle.setStyleSheet("color: #94a3b8; font-size: 14px; background: transparent;")

        header_info = QVBoxLayout()
        header_info.addWidget(title)
        header_info.addWidget(subtitle)
        header_layout.addLayout(header_info)
        header_layout.addStretch()
        self.main_layout.addLayout(header_layout)

        # ── Step 1: Import Selection ──
        self.step1_frame = QFrame()
        self.step1_frame.setStyleSheet("""
            QFrame {
                background: rgba(30, 41, 59, 0.3);
                border: 1px solid rgba(99, 102, 241, 0.1);
                border-radius: 14px;
            }
        """)
        step1_layout = QVBoxLayout(self.step1_frame)
        step1_layout.setContentsMargins(20, 18, 20, 18)
        step1_layout.setSpacing(12)

        step1_header = QHBoxLayout()
        step1_title = QLabel("Step 1: Select Imports")
        step1_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #e2e8f0; background: transparent;")
        step1_header.addWidget(step1_title)
        step1_header.addStretch()

        self.btn_build = QPushButton("Build Delivery List")
        self.btn_build.setFixedSize(170, 38)
        self.btn_build.setCursor(Qt.PointingHandCursor)
        self.btn_build.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6366f1, stop:1 #4f46e5);
                border: none;
                border-radius: 8px;
                color: white;
                font-weight: 700;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #818cf8, stop:1 #6366f1);
            }
        """)
        self.btn_build.clicked.connect(self._on_build_list)
        step1_header.addWidget(self.btn_build)
        step1_layout.addLayout(step1_header)

        # Scroll area for import cards
        self.import_scroll = QScrollArea()
        self.import_scroll.setWidgetResizable(True)
        self.import_scroll.setMinimumHeight(260)
        self.import_scroll.setMaximumHeight(280)
        self.import_scroll.setStyleSheet("background: transparent; border: none;")
        self.import_content = QWidget()
        self.import_content.setStyleSheet("background: transparent;")
        self.import_list_layout = QVBoxLayout(self.import_content)
        self.import_list_layout.setSpacing(8)
        self.import_list_layout.setAlignment(Qt.AlignTop)
        self.import_scroll.setWidget(self.import_content)
        step1_layout.addWidget(self.import_scroll)

        self.main_layout.addWidget(self.step1_frame)

        # ── Step 2: Customer Review Table ──
        self.step2_frame = QFrame()
        self.step2_frame.setStyleSheet("""
            QFrame {
                background: rgba(30, 41, 59, 0.3);
                border: 1px solid rgba(99, 102, 241, 0.1);
                border-radius: 14px;
            }
        """)
        step2_layout = QVBoxLayout(self.step2_frame)
        step2_layout.setContentsMargins(20, 18, 20, 18)
        step2_layout.setSpacing(12)

        step2_header = QHBoxLayout()
        self.step2_title = QLabel("Step 2: Review Delivery List")
        self.step2_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #e2e8f0; background: transparent;")
        step2_header.addWidget(self.step2_title)
        step2_header.addStretch()

        self.btn_select_all = QPushButton("Deselect All")
        self.btn_select_all.setFixedSize(100, 34)
        self.btn_select_all.setCursor(Qt.PointingHandCursor)
        self.btn_select_all.setStyleSheet("""
            QPushButton {
                background: rgba(99, 102, 241, 0.1);
                border: 1px solid rgba(99, 102, 241, 0.25);
                border-radius: 7px;
                font-size: 12px;
                font-weight: 700;
                color: #a5b4fc;
            }
            QPushButton:hover {
                background: rgba(99, 102, 241, 0.2);
                color: #e0e7ff;
                border-color: #6366f1;
            }
        """)
        self.btn_select_all.clicked.connect(self._on_toggle_all)
        self._all_checked = True

        self.btn_export = QPushButton("Export to Excel")
        self.btn_export.setFixedSize(140, 38)
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.setStyleSheet("""
            QPushButton {
                background: rgba(34, 197, 94, 0.1);
                border: 1px solid rgba(34, 197, 94, 0.25);
                border-radius: 8px;
                font-size: 13px;
                font-weight: 700;
                color: #4ade80;
            }
            QPushButton:hover {
                background: rgba(34, 197, 94, 0.2);
                color: #ffffff;
                border-color: #22c55e;
            }
        """)
        self.btn_export.clicked.connect(self._on_export)

        self.btn_clear = QPushButton("Clear List")
        self.btn_clear.setFixedSize(100, 34)
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background: rgba(239, 68, 68, 0.08);
                border: 1px solid rgba(239, 68, 68, 0.2);
                border-radius: 7px;
                font-size: 12px;
                font-weight: 700;
                color: #f87171;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.18);
                color: #ffffff;
                border-color: #ef4444;
            }
        """)
        self.btn_clear.clicked.connect(self._on_clear_list)

        step2_header.addWidget(self.btn_select_all)
        step2_header.addWidget(self.btn_clear)
        step2_header.addWidget(self.btn_export)
        step2_layout.addLayout(step2_header)

        # Customer table — no fixed height, grows with data
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["", "NAME", "PHONE", "ADDRESS"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 40)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.setColumnWidth(2, 160)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(44)
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
                padding: 10px;
                border-bottom: 1px solid rgba(99, 102, 241, 0.08);
            }
            QHeaderView::section {
                background: rgba(30, 41, 59, 0.95);
                color: #a5b4fc;
                font-weight: 700;
                font-size: 11px;
                padding: 12px 10px;
                border: none;
                border-bottom: 2px solid rgba(99, 102, 241, 0.3);
                text-transform: uppercase;
            }
        """)
        self.table.itemChanged.connect(self._on_item_changed)
        step2_layout.addWidget(self.table)

        # Summary label
        self.lbl_summary = QLabel("No delivery list built yet.")
        self.lbl_summary.setStyleSheet("color: #64748b; font-size: 13px; font-style: italic; background: transparent;")
        step2_layout.addWidget(self.lbl_summary)

        self.main_layout.addWidget(self.step2_frame)

        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

    def refresh_imports(self):
        """Reload the import cards list."""
        # Clear existing cards
        while self.import_list_layout.count():
            item = self.import_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._import_cards = []

        imports = DataRepository.get_recent_imports(limit=30)
        if not imports:
            no_data = QLabel("No imports found. Import invoices first.")
            no_data.setStyleSheet("color: #64748b; font-style: italic; padding: 20px; background: transparent;")
            no_data.setAlignment(Qt.AlignCenter)
            self.import_list_layout.addWidget(no_data)
        else:
            for imp_id, fname, date, c_cnt, i_cnt, val, ids_str in imports:
                card = ImportSelectCard(imp_id, fname, date, c_cnt, i_cnt, val)
                self._import_cards.append(card)
                self.import_list_layout.addWidget(card)

    def _on_build_list(self):
        """Build the delivery list from selected imports."""
        selected_ids = [c.import_id for c in self._import_cards if c.checked]
        if not selected_ids:
            QMessageBox.warning(self, "No Selection", "Please select at least one import to build the delivery list.")
            return

        customers = DataRepository.get_customers_by_import_ids(selected_ids)
        self._customer_data = customers

        # Populate the table
        try:
            self.table.itemChanged.disconnect()
        except RuntimeError:
            pass

        self.table.setRowCount(0)
        self._all_checked = True
        self.btn_select_all.setText("Deselect All")

        for i, (name, phone, address) in enumerate(customers):
            self.table.insertRow(i)

            # Checkbox
            chk = QTableWidgetItem()
            chk.setCheckState(Qt.Checked)
            chk.setTextAlignment(Qt.AlignCenter)
            chk.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            self.table.setItem(i, 0, chk)

            # Name
            name_item = QTableWidgetItem(name)
            name_item.setForeground(Qt.white)
            name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(i, 1, name_item)

            # Phone
            phone_item = QTableWidgetItem(phone or "---")
            phone_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(i, 2, phone_item)

            # Address
            addr_item = QTableWidgetItem(address or "---")
            addr_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(i, 3, addr_item)

        self.table.itemChanged.connect(self._on_item_changed)
        self._update_summary()

        # Auto-size table to fit all rows (no internal scrolling)
        row_count = self.table.rowCount()
        header_h = self.table.horizontalHeader().height()
        row_h = self.table.verticalHeader().defaultSectionSize()
        self.table.setMinimumHeight(header_h + row_count * row_h + 4)

    def _on_item_changed(self, item):
        if item and item.column() == 0:
            self._update_summary()

    def _on_toggle_all(self):
        self._all_checked = not self._all_checked
        state = Qt.Checked if self._all_checked else Qt.Unchecked
        self.btn_select_all.setText("Deselect All" if self._all_checked else "Select All")

        try:
            self.table.itemChanged.disconnect()
        except RuntimeError:
            pass

        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(state)

        self.table.itemChanged.connect(self._on_item_changed)
        self._update_summary()

    def _update_summary(self):
        total = self.table.rowCount()
        checked = 0
        for row in range(total):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.Checked:
                checked += 1
        removed = total - checked
        if total == 0:
            self.lbl_summary.setText("No delivery list built yet.")
        else:
            self.lbl_summary.setText(
                f"{checked} customers for delivery  |  {removed} removed (self-collect / no delivery)")
        self.step2_title.setText(f"Step 2: Review Delivery List ({checked}/{total})")

    def _on_clear_list(self):
        """Clear the delivery list table and uncheck all import cards."""
        try:
            self.table.itemChanged.disconnect()
        except RuntimeError:
            pass

        self.table.setRowCount(0)
        self._customer_data = []
        self._all_checked = True
        self.btn_select_all.setText("Select All")
        self.step2_title.setText("Step 2: Review Delivery List")
        self.lbl_summary.setText("No delivery list built yet.")

        # Uncheck all import cards
        for card in self._import_cards:
            card.chk.setChecked(False)

        self.table.itemChanged.connect(self._on_item_changed)

    def _on_export(self):
        """Export checked customers to Excel."""
        rows_to_export = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.Checked:
                name = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
                phone = self.table.item(row, 2).text() if self.table.item(row, 2) else ""
                address = self.table.item(row, 3).text() if self.table.item(row, 3) else ""
                if phone == "---":
                    phone = ""
                if address == "---":
                    address = ""
                rows_to_export.append({"Name": name, "Phone": phone, "Address": address})

        if not rows_to_export:
            QMessageBox.warning(self, "Nothing to Export", "No customers are selected for delivery.")
            return

        today = datetime.date.today().strftime('%Y-%m-%d')
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Delivery List", f"delivery_list_{today}.xlsx",
            "Excel Files (*.xlsx)")
        if not path:
            return

        try:
            import pandas as pd
            df = pd.DataFrame(rows_to_export)
            with pd.ExcelWriter(path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Delivery List')
                ws = writer.sheets['Delivery List']
                # Auto-width columns
                for col in ws.columns:
                    max_len = max(len(str(cell.value or '')) for cell in col)
                    ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 60)
            QMessageBox.information(self, "Export Complete",
                f"Delivery list exported with {len(rows_to_export)} customers.\n\n{path}")
        except ImportError:
            QMessageBox.critical(self, "Error", "pandas/openpyxl not installed.\nRun: pip install pandas openpyxl")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))
