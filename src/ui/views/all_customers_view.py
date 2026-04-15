from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QScrollArea, QFrame, QDialog, QTableWidget,
                               QTableWidgetItem, QHeaderView, QLineEdit, QGridLayout,
                               QGraphicsDropShadowEffect, QSizePolicy)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from src.database.repository import DataRepository
from src.ui.dialogs.import_customers_dialog import ImportCustomersDialog


# ============================================================
#  CUSTOMER DETAIL POPUP — Full-screen premium dialog
# ============================================================
class CustomerDetailPopup(QDialog):
    """Big popup showing all items a customer has purchased with totals."""

    def __init__(self, parent, name, phone):
        super().__init__(parent)
        self.setWindowTitle(f"Customer Details - {name}")
        self.setMinimumSize(750, 600)
        self.resize(850, 650)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0f172a, stop:1 #1e293b);
                border-radius: 16px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        # ---- Header ----
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(99, 102, 241, 0.15), stop:1 rgba(139, 92, 246, 0.08));
                border: 1px solid rgba(99, 102, 241, 0.2);
                border-radius: 16px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(24, 20, 24, 20)

        # Avatar circle
        avatar = QLabel(name[0].upper() if name else "?")
        avatar.setFixedSize(56, 56)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6366f1, stop:1 #8b5cf6);
                border-radius: 28px;
                font-size: 24px;
                font-weight: 800;
                color: white;
            }
        """)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("font-size: 22px; font-weight: 800; color: #f8fafc; background: transparent;")

        phone_text = phone if phone and phone.strip() else "No phone number"
        phone_lbl = QLabel(phone_text)
        phone_lbl.setStyleSheet("font-size: 13px; color: #94a3b8; background: transparent;")

        info_layout.addWidget(name_lbl)
        info_layout.addWidget(phone_lbl)

        header_layout.addWidget(avatar)
        header_layout.addSpacing(16)
        header_layout.addLayout(info_layout)
        header_layout.addStretch()

        # Grand Total badge
        invoices_data, grand_total = DataRepository.get_customer_full_details(name, phone)

        total_badge = QLabel(f"${grand_total:,.2f}")
        total_badge.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(34, 197, 94, 0.15), stop:1 rgba(16, 185, 129, 0.1));
                border: 1px solid rgba(34, 197, 94, 0.3);
                border-radius: 12px;
                padding: 10px 20px;
                font-size: 26px;
                font-weight: 800;
                color: #4ade80;
            }
        """)
        header_layout.addWidget(total_badge)

        layout.addWidget(header_frame)

        # ---- Summary Stats ----
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)

        total_invoices = len(invoices_data)
        total_items = sum(len(inv['items']) for inv in invoices_data)
        statuses = [inv['invoice'][3] for inv in invoices_data]
        sent_count = statuses.count('Sent')

        stats_data = [
            ("Total Invoices", str(total_invoices), "#a5b4fc", "rgba(99, 102, 241, 0.1)", "rgba(99, 102, 241, 0.2)"),
            ("Total Items", str(total_items), "#38bdf8", "rgba(56, 189, 248, 0.1)", "rgba(56, 189, 248, 0.2)"),
            ("Sent", str(sent_count), "#4ade80", "rgba(34, 197, 94, 0.1)", "rgba(34, 197, 94, 0.2)"),
            ("Pending", str(total_invoices - sent_count), "#fbbf24", "rgba(251, 191, 36, 0.1)", "rgba(251, 191, 36, 0.2)"),
        ]

        for title, value, color, bg, border_color in stats_data:
            stat_frame = QFrame()
            stat_frame.setStyleSheet(f"""
                QFrame {{
                    background: {bg};
                    border: 1px solid {border_color};
                    border-radius: 10px;
                    min-width: 120px;
                }}
            """)
            stat_layout = QVBoxLayout(stat_frame)
            stat_layout.setContentsMargins(14, 12, 14, 12)
            stat_layout.setSpacing(2)

            stat_title = QLabel(title)
            stat_title.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 600; text-transform: uppercase; background: transparent;")

            stat_value = QLabel(value)
            stat_value.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: 800; background: transparent;")

            stat_layout.addWidget(stat_title)
            stat_layout.addWidget(stat_value)
            stats_row.addWidget(stat_frame)

        layout.addLayout(stats_row)

        # ---- Items Table Label ----
        items_label = QLabel("Purchased Items")
        items_label.setStyleSheet("font-size: 16px; font-weight: 700; color: #e2e8f0; background: transparent; margin-top: 4px;")
        layout.addWidget(items_label)

        # ---- Items Table ----
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Item Name", "Qty", "Unit Price", "Subtotal"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setDefaultSectionSize(44)
        table.setStyleSheet("""
            QTableWidget { 
                background-color: rgba(15, 23, 42, 0.6);
                alternate-background-color: rgba(30, 41, 59, 0.4);
                color: #e2e8f0; 
                border: 1px solid rgba(99, 102, 241, 0.15);
                border-radius: 12px;
                font-size: 13px;
            }
            QTableWidget::item { 
                padding: 10px 14px; 
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
                padding: 12px 14px; 
                border: none;
                border-bottom: 2px solid rgba(99, 102, 241, 0.3);
                text-transform: uppercase;
                letter-spacing: 1px;
            }
        """)

        row_idx = 0
        for inv_data in invoices_data:
            for desc, qty, price, sub in inv_data['items']:
                table.insertRow(row_idx)
                table.setItem(row_idx, 0, QTableWidgetItem(desc))
                
                qty_item = QTableWidgetItem(str(int(qty)) if qty else "1")
                qty_item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row_idx, 1, qty_item)
                
                price_item = QTableWidgetItem(f"${price:,.2f}")
                price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table.setItem(row_idx, 2, price_item)
                
                sub_item = QTableWidgetItem(f"${sub:,.2f}")
                sub_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                sub_item.setForeground(QColor("#a5b4fc"))
                table.setItem(row_idx, 3, sub_item)
                row_idx += 1

        layout.addWidget(table)

        # ---- Bottom: Grand Total Bar ----
        total_bar = QFrame()
        total_bar.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(99, 102, 241, 0.12), stop:1 rgba(139, 92, 246, 0.08));
                border: 1px solid rgba(99, 102, 241, 0.25);
                border-radius: 12px;
            }
        """)
        total_bar_layout = QHBoxLayout(total_bar)
        total_bar_layout.setContentsMargins(20, 14, 20, 14)

        total_text = QLabel("Grand Total")
        total_text.setStyleSheet("font-size: 15px; font-weight: 600; color: #94a3b8; background: transparent;")
        
        total_amount = QLabel(f"${grand_total:,.2f}")
        total_amount.setStyleSheet("font-size: 28px; font-weight: 800; color: #a5b4fc; background: transparent;")

        total_bar_layout.addWidget(total_text)
        total_bar_layout.addStretch()
        total_bar_layout.addWidget(total_amount)

        layout.addWidget(total_bar)

        # ---- Close Button ----
        btn_close = QPushButton("Close")
        btn_close.setFixedHeight(44)
        btn_close.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6366f1, stop:1 #4f46e5);
                border: none;
                border-radius: 10px;
                color: white;
                font-weight: 700;
                font-size: 14px;
                padding: 8px 40px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #818cf8, stop:1 #6366f1);
            }
        """)
        btn_close.clicked.connect(self.accept)

        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_layout.addWidget(btn_close)
        layout.addLayout(close_layout)


# ============================================================
#  CUSTOMER CARD for the grid
# ============================================================
class AllCustomerCard(QFrame):
    """A clickable card for each customer in the details grid."""
    clicked = Signal(str, str)  # name, phone

    def __init__(self, name, phone, item_count, total_amount, status, address=None):
        super().__init__()
        self.name = name
        self.phone = phone or ""
        self.setObjectName("AllCustomerCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(140)
        self.setMaximumHeight(185)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Dynamic border/accent based on status
        if status == "Sent":
            accent = "#4ade80"
            accent_bg = "rgba(34, 197, 94, 0.08)"
            border_color = "rgba(34, 197, 94, 0.25)"
            badge_bg = "rgba(34, 197, 94, 0.15)"
        elif status == "Generated":
            accent = "#a5b4fc"
            accent_bg = "rgba(99, 102, 241, 0.08)"
            border_color = "rgba(99, 102, 241, 0.25)"
            badge_bg = "rgba(99, 102, 241, 0.15)"
        else:
            accent = "#fbbf24"
            accent_bg = "rgba(251, 191, 36, 0.06)"
            border_color = "rgba(251, 191, 36, 0.2)"
            badge_bg = "rgba(251, 191, 36, 0.15)"

        self.default_style = f"""
            QFrame#AllCustomerCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(30, 41, 59, 0.85), stop:1 {accent_bg});
                border: 1px solid {border_color};
                border-radius: 14px;
            }}
        """
        self.hover_style = f"""
            QFrame#AllCustomerCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(49, 46, 129, 0.35), stop:1 rgba(30, 41, 59, 0.9));
                border: 2px solid {accent};
                border-radius: 14px;
            }}
        """
        self.setStyleSheet(self.default_style)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # Row 1: Avatar + Name + Status
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        avatar = QLabel(name[0].upper() if name else "?")
        avatar.setFixedSize(38, 38)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6366f1, stop:1 #8b5cf6);
                border-radius: 19px;
                font-size: 16px;
                font-weight: 800;
                color: white;
            }}
        """)

        name_lbl = QLabel(name if name and name.strip() else "Unknown")
        name_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #f1f5f9; background: transparent;")
        name_lbl.setWordWrap(True)

        status_badge = QLabel(status or "Draft")
        status_badge.setStyleSheet(f"""
            QLabel {{
                font-size: 10px;
                padding: 3px 10px;
                border-radius: 8px;
                background: {badge_bg};
                color: {accent};
                border: 1px solid {border_color};
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
        """)

        top_row.addWidget(avatar)
        top_row.addWidget(name_lbl, 1)
        top_row.addWidget(status_badge)
        layout.addLayout(top_row)

        # Row 2: Phone
        if phone and phone.strip():
            phone_lbl = QLabel(f"📞  {phone}")
            phone_lbl.setStyleSheet("font-size: 12px; color: #64748b; background: transparent; padding-left: 48px;")
            layout.addWidget(phone_lbl)

        # Row 3: Address (new)
        if address and str(address).strip() and str(address).strip().lower() not in ('nan', 'none', ''):
            addr_lbl = QLabel(f"📍  {str(address).strip()}")
            addr_lbl.setStyleSheet("font-size: 11px; color: #475569; background: transparent; padding-left: 48px;")
            addr_lbl.setWordWrap(True)
            layout.addWidget(addr_lbl)

        # Row 4: Items count + Total
        bottom_row = QHBoxLayout()

        items_lbl = QLabel(f"{item_count} items")
        items_lbl.setStyleSheet("font-size: 12px; color: #94a3b8; font-weight: 600; background: transparent;")

        total_lbl = QLabel(f"${total_amount:,.2f}")
        total_lbl.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {accent}; background: transparent;")

        bottom_row.addWidget(items_lbl)
        bottom_row.addStretch()
        bottom_row.addWidget(total_lbl)
        layout.addLayout(bottom_row)

        layout.addStretch()

    def enterEvent(self, event):
        self.setStyleSheet(self.hover_style)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self.default_style)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.name, self.phone)
        super().mousePressEvent(event)


# ============================================================
#  ALL CUSTOMERS VIEW — Separate page with grid of customers
# ============================================================
class AllCustomersView(QWidget):
    """Page showing all customers in a grid. Click to open detail popup."""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 28, 30, 28)
        layout.setSpacing(20)
        self.setStyleSheet("background: #0f172a;")

        # ---- Header ----
        header_layout = QHBoxLayout()
        
        welcome = QVBoxLayout()
        welcome.setSpacing(4)

        title = QLabel("All Customers")
        title.setStyleSheet("font-size: 28px; font-weight: 800; color: #f8fafc; background: transparent;")

        subtitle = QLabel("Click any customer to view their purchase details and invoices")
        subtitle.setStyleSheet("color: #64748b; font-size: 13px; background: transparent;")
        
        welcome.addWidget(title)
        welcome.addWidget(subtitle)
        
        header_layout.addLayout(welcome)
        header_layout.addStretch()

        # ── Import Customers Button ──
        self.btn_import_customers = QPushButton("📥  Import Customers")
        self.btn_import_customers.setFixedHeight(44)
        self.btn_import_customers.setCursor(Qt.PointingHandCursor)
        self.btn_import_customers.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6366f1, stop:1 #4f46e5);
                border: none;
                border-radius: 10px;
                padding: 10px 22px;
                font-size: 13px;
                font-weight: 700;
                color: #ffffff;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #818cf8, stop:1 #6366f1);
            }
        """)
        self.btn_import_customers.clicked.connect(self._on_import_customers)
        header_layout.addWidget(self.btn_import_customers)

        layout.addLayout(header_layout)

        # ---- Search Bar ----
        search_frame = QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background: rgba(30, 41, 59, 0.5);
                border: 1px solid rgba(99, 102, 241, 0.15);
                border-radius: 12px;
            }
        """)
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(16, 8, 16, 8)

        search_label = QLabel("Search:")
        search_label.setStyleSheet("font-size: 13px; color: #94a3b8; font-weight: 600; background: transparent;")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search customers by name or phone...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #e2e8f0;
                font-size: 14px;
                padding: 8px 4px;
            }
        """)
        self.search_input.textChanged.connect(self.refresh_data)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addWidget(search_frame)

        # ---- Customer Count ----
        self.count_label = QLabel("0 customers")
        self.count_label.setStyleSheet("color: #64748b; font-size: 12px; font-weight: 600; background: transparent;")
        layout.addWidget(self.count_label)

        # ---- Scrollable Customer Grid ----
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setContentsMargins(0, 4, 0, 4)

        self.scroll_area.setWidget(self.grid_container)
        layout.addWidget(self.scroll_area)

    def refresh_data(self):
        try:
            # Clear existing cards
            self.setUpdatesEnabled(False)  # freeze painting for speed
            while self.grid_layout.count():
                item = self.grid_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            search_term = self.search_input.text().strip() if hasattr(self, 'search_input') else ""
            customers = DataRepository.get_all_customers_summary(search_term if search_term else None)

            if not customers:
                # Empty state
                empty_frame = QFrame()
                empty_frame.setStyleSheet("""
                    QFrame {
                        background: rgba(30, 41, 59, 0.3);
                        border: 2px dashed rgba(99, 102, 241, 0.2);
                        border-radius: 16px;
                        min-height: 200px;
                    }
                """)
                empty_layout = QVBoxLayout(empty_frame)
                empty_layout.setAlignment(Qt.AlignCenter)

                empty_text = QLabel("No customers yet")
                empty_text.setStyleSheet("font-size: 18px; font-weight: 700; color: #64748b; background: transparent;")
                empty_text.setAlignment(Qt.AlignCenter)

                empty_sub = QLabel("Import invoice data to see your customers here")
                empty_sub.setStyleSheet("font-size: 13px; color: #475569; background: transparent;")
                empty_sub.setAlignment(Qt.AlignCenter)

                empty_layout.addWidget(empty_text)
                empty_layout.addWidget(empty_sub)
                self.grid_layout.addWidget(empty_frame, 0, 0, 1, 3)
                self.count_label.setText("0 customers")
                self.setUpdatesEnabled(True)
                return

            self.count_label.setText(f"{len(customers)} customer{'s' if len(customers) != 1 else ''}")

            # Create grid of cards — 3 columns
            # Row now: name, phone, address, item_count, total_amount, status
            cols = 3
            for idx, row in enumerate(customers):
                name       = row[0]
                phone      = row[1]
                address    = row[2]  # ← comes direct from SQL, no extra query
                item_count = row[3]
                total      = row[4]
                status     = row[5]
                p_str = str(phone) if phone is not None else ""
                card = AllCustomerCard(
                    name=name,
                    phone=p_str,
                    item_count=item_count or 0,
                    total_amount=total or 0.0,
                    status=status or "Draft",
                    address=address
                )
                card.clicked.connect(self.on_customer_card_clicked)
                row_pos = idx // cols
                col_pos = idx % cols
                self.grid_layout.addWidget(card, row_pos, col_pos)

            # Fill remaining cells in last row for alignment
            remainder = len(customers) % cols
            if remainder:
                last_row = len(customers) // cols
                for fill_col in range(remainder, cols):
                    spacer = QWidget()
                    spacer.setStyleSheet("background: transparent;")
                    self.grid_layout.addWidget(spacer, last_row, fill_col)

        except Exception as e:
            print(f"Error refreshing all customers: {e}")
            err_lbl = QLabel(f"Error loading customers: {str(e)}")
            err_lbl.setStyleSheet("color: #f87171; font-style: italic; background: transparent; padding: 20px;")
            self.grid_layout.addWidget(err_lbl, 0, 0)
        finally:
            self.setUpdatesEnabled(True)  # always re-enable painting

    def on_customer_card_clicked(self, name, phone):
        """Open the big popup with full customer purchase details."""
        popup = CustomerDetailPopup(self, name, phone)
        popup.exec_()

    def _on_import_customers(self):
        """Open the Import Customers dialog."""
        dialog = ImportCustomersDialog(self)
        dialog.customers_imported.connect(self.refresh_data)
        dialog.exec_()
