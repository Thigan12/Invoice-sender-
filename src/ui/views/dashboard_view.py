from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QScrollArea, QFrame)
from PySide6.QtCore import Qt, Signal
import datetime
from src.database.repository import DataRepository

class StatCard(QFrame):
    def __init__(self, title, value, icon_text, color):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(30, 41, 59, 0.7), stop:1 rgba(15, 23, 42, 0.9));
                border: 1px solid rgba(99, 102, 241, 0.15);
                border-radius: 16px;
                min-width: 200px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #94a3b8; font-size: 13px; font-weight: 600; text-transform: uppercase;")
        
        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: 800; margin-top: 4px;")
        
        layout.addWidget(lbl_title)
        layout.addWidget(self.lbl_value)
        layout.addStretch()

class ImportHistoryCard(QFrame):
    clicked = Signal(list) # Emits the invoice_ids for this import

    def __init__(self, file_name, date_str, cust_count, inv_count, total_val, invoice_ids_str):
        super().__init__()
        self.invoice_ids = [int(i) for i in invoice_ids_str.split(',')] if invoice_ids_str else []
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
            QFrame:hover {
                border-color: rgba(99, 102, 241, 0.4);
                background: rgba(30, 41, 59, 0.6);
            }
        """)
        self.setCursor(Qt.PointingHandCursor)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        
        info = QVBoxLayout()
        name_lbl = QLabel(file_name)
        name_lbl.setStyleSheet("color: #e2e8f0; font-weight: 700; font-size: 15px;")
        date_lbl = QLabel(formatted_date)
        date_lbl.setStyleSheet("color: #64748b; font-size: 12px;")
        info.addWidget(name_lbl)
        info.addWidget(date_lbl)
        
        stats = QHBoxLayout()
        safe_val = total_val if total_val is not None else 0.0
        stats_lbl = QLabel(f"{cust_count} Customers  |  {inv_count} Invoices  |  ${safe_val:,.2f}")
        stats_lbl.setStyleSheet("color: #a5b4fc; font-size: 13px;")
        
        layout.addLayout(info)
        layout.addStretch()
        layout.addWidget(stats_lbl)

    def mousePressEvent(self, event):
        self.clicked.emit(self.invoice_ids)
        super().mousePressEvent(event)

class DashboardView(QWidget):
    startImportRequested = Signal()
    viewInvoicesRequested = Signal(list) # Pass list of IDs to filter

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        self.setStyleSheet("background: #0f172a;")

        # Welcome Header
        header_layout = QHBoxLayout()
        welcome = QVBoxLayout()
        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 32px; font-weight: 800; color: #f8fafc;")
        subtitle = QLabel("Overview of your invoice activity and imports.")
        subtitle.setStyleSheet("color: #94a3b8; font-size: 14px;")
        welcome.addWidget(title)
        welcome.addWidget(subtitle)
        
        btn_import = QPushButton("New Import")
        btn_import.setFixedSize(140, 45)
        btn_import.setStyleSheet("""
            QPushButton {
                background: #6366f1;
                border-radius: 10px;
                color: white;
                font-weight: 700;
                font-size: 13px;
            }
            QPushButton:hover { background: #4f46e5; }
        """)
        btn_import.clicked.connect(lambda: self.startImportRequested.emit())
        
        header_layout.addLayout(welcome)
        header_layout.addStretch()
        header_layout.addWidget(btn_import)
        layout.addLayout(header_layout)

        # Quick Stats Row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)
        
        self.card_revenue = StatCard("Total Revenue", "$0.00", "money", "#4ade80")
        self.card_total = StatCard("Total Invoices", "0", "file-text", "#a5b4fc")
        self.card_pending = StatCard("Invoices Pending", "0", "clock", "#fbbf24")
        self.card_customers = StatCard("Active Customers", "0", "user", "#38bdf8")
        
        stats_layout.addWidget(self.card_revenue)
        stats_layout.addWidget(self.card_total)
        stats_layout.addWidget(self.card_pending)
        stats_layout.addWidget(self.card_customers)
        layout.addLayout(stats_layout)

        # Recent Activity Section
        activity_label = QLabel("Recent Excel Imports")
        activity_label.setStyleSheet("font-size: 20px; font-weight: 700; color: #f8fafc; margin-top: 10px;")
        layout.addWidget(activity_label)
        
        self.history_area = QScrollArea()
        self.history_area.setWidgetResizable(True)
        self.history_area.setStyleSheet("background: transparent; border: none;")
        self.history_content = QWidget()
        self.history_content.setStyleSheet("background: transparent;")
        self.history_layout = QVBoxLayout(self.history_content)
        self.history_layout.setSpacing(12)
        self.history_layout.setAlignment(Qt.AlignTop)
        self.history_area.setWidget(self.history_content)
        
        layout.addWidget(self.history_area)

    def refresh_data(self):
        try:
            # 1. Update Cards
            stats = DataRepository.get_dashboard_stats()
            self.card_revenue.lbl_value.setText(f"${stats['revenue']:,.2f}")
            self.card_total.lbl_value.setText(str(stats['total_invoices']))
            self.card_pending.lbl_value.setText(str(stats['pending']))
            self.card_customers.lbl_value.setText(str(stats['customers']))
            
            # 2. Update History
            while self.history_layout.count():
                item = self.history_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                    
            imports = DataRepository.get_recent_imports()
            if not imports:
                no_data = QLabel("No import history yet. Click 'New Import' to get started.")
                no_data.setStyleSheet("color: #64748b; font-style: italic; padding: 40px; border: 1px dashed rgba(99,102,241,0.2); border-radius: 12px;")
                no_data.setAlignment(Qt.AlignCenter)
                self.history_layout.addWidget(no_data)
            else:
                for fname, date, c_cnt, i_cnt, val, ids_str in imports:
                    card = ImportHistoryCard(fname, date, c_cnt, i_cnt, val, ids_str)
                    card.clicked.connect(self.viewInvoicesRequested.emit)
                    self.history_layout.addWidget(card)
        except Exception as e:
            print(f"Error refreshing dashboard: {e}")
            err_lbl = QLabel(f"Dashboard error: {str(e)}")
            err_lbl.setStyleSheet("color: #f87171; font-style: italic;")
            self.history_layout.addWidget(err_lbl)
