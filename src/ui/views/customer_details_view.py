from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                                QLabel, QLineEdit, QTableWidget, QTableWidgetItem, 
                                QHeaderView, QMessageBox, QDialog, QFormLayout)
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


class CustomerEditDialog(QDialog):
    def __init__(self, parent=None, name="", phone=""):
        super().__init__(parent)
        self.setWindowTitle("Edit Customer")
        self.setFixedWidth(400)
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
        
        lbl_name = QLabel("Name:")
        lbl_name.setStyleSheet("color: #94a3b8; font-weight: 600;")
        self.name_input = QLineEdit(name)
        self.name_input.setStyleSheet("""
            QLineEdit {
                background-color: #0f172a;
                border: 1px solid rgba(99, 102, 241, 0.3);
                border-radius: 8px;
                padding: 10px 12px;
                color: #e2e8f0;
                font-size: 13px;
            }
            QLineEdit:focus { border-color: #6366f1; }
        """)
        
        lbl_phone = QLabel("Phone:")
        lbl_phone.setStyleSheet("color: #94a3b8; font-weight: 600;")
        self.phone_input = QLineEdit(phone)
        self.phone_input.setStyleSheet("""
            QLineEdit {
                background-color: #0f172a;
                border: 1px solid rgba(99, 102, 241, 0.3);
                border-radius: 8px;
                padding: 10px 12px;
                color: #e2e8f0;
                font-size: 13px;
            }
            QLineEdit:focus { border-color: #6366f1; }
        """)
        
        layout.addRow(lbl_name, self.name_input)
        layout.addRow(lbl_phone, self.phone_input)
        
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
        return self.name_input.text().strip(), self.phone_input.text().strip()


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
        
        self.btn_add = QPushButton("Add New Customer")
        self.btn_add.setFixedHeight(38)
        self.btn_add.setStyleSheet(BTN_PRIMARY)
        self.btn_add.clicked.connect(self.on_add_new)

        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_add)
        layout.addLayout(header_layout)

        # Table
        self.table = QTableWidget(0, 3)
        self.table.verticalHeader().setDefaultSectionSize(52) # Increased height
        self.table.setHorizontalHeaderLabels(["Name", "Phone", "Action"])
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

    def refresh_data(self):
        customers = DataRepository.get_all_master_customers()
        self.table.setRowCount(0)
        
        for i, (cid, name, phone) in enumerate(customers):
            self.table.insertRow(i)
            
            name_item = QTableWidgetItem(name)
            name_item.setForeground(Qt.white)
            self.table.setItem(i, 0, name_item)
            
            phone_item = QTableWidgetItem(phone or "—")
            self.table.setItem(i, 1, phone_item)
            
            # Action: Edit button only
            btn_box = QWidget()
            btn_box.setStyleSheet("background: transparent;")
            btn_layout = QHBoxLayout(btn_box)
            btn_layout.setContentsMargins(8, 4, 8, 4)
            btn_layout.setSpacing(6)
            
            btn_edit = QPushButton("Edit")
            btn_edit.setStyleSheet(BTN_GHOST)
            btn_edit.setFixedHeight(30)
            btn_edit.clicked.connect(lambda checked, c=cid, n=name, p=phone: self.on_edit(c, n, p))
            
            btn_layout.addWidget(btn_edit)
            btn_layout.addStretch()
            self.table.setCellWidget(i, 2, btn_box)

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
        dialog = CustomerEditDialog(self, "", "")
        dialog.setWindowTitle("Add New Customer")
        if dialog.exec_() == QDialog.Accepted:
            new_name, new_phone = dialog.get_data()
            if not new_name:
                QMessageBox.warning(self, "Error", "Name cannot be empty.")
                return
            
            DataRepository.upsert_customer(new_name, new_phone)
            self.refresh_data()
            self.customer_updated.emit()
            QMessageBox.information(self, "Success", f"Customer <b>{new_name}</b> added and saved locally.")

    def on_edit(self, cust_id, old_name, old_phone):
        dialog = CustomerEditDialog(self, old_name, old_phone or "")
        if dialog.exec_() == QDialog.Accepted:
            new_name, new_phone = dialog.get_data()
            if not new_name:
                QMessageBox.warning(self, "Error", "Name cannot be empty.")
                return
                
            DataRepository.update_customer_info(cust_id, new_name, new_phone)
            self.refresh_data()
            self.customer_updated.emit()
            QMessageBox.information(self, "Success", "Customer details updated.")
