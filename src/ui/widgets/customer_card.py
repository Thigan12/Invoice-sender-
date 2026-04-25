from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QApplication
from PySide6.QtCore import Qt, Signal

class CustomerCard(QFrame):
    clicked = Signal(str, str)  # name, phone
    sendWhatsAppRequested = Signal(str, str)  # name, phone
    shareWhatsAppRequested = Signal(str, str)  # name, phone — manual share flow
    copyBillRequested = Signal(str, str)  # name, phone — copy bill text to clipboard
    generatePdfRequested = Signal(str, str) # name, phone
    deleteRequested = Signal(str, str) # name, phone

    def __init__(self, name, item_count, total_amount, phone, status="Ready"):
        super().__init__()
        self.name = name
        self.phone = phone
        self.setObjectName("CustomerCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(120)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 12)
        layout.setSpacing(8)

        # Header Row: Name + Status
        header_row = QHBoxLayout()
        self.lbl_name = QLabel(name if name and name.strip() else "Unknown Customer")
        self.lbl_name.setWordWrap(True)
        self.lbl_name.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.lbl_name.setStyleSheet("font-weight: 700; font-size: 14px; color: #e2e8f0; background: transparent;")
        
        # Dynamic status colors
        if status == "Sent":
            badge_bg = "rgba(34, 197, 94, 0.15)"
            badge_color = "#4ade80"
            badge_border = "rgba(34, 197, 94, 0.3)"
        elif status == "Generated":
            badge_bg = "rgba(99, 102, 241, 0.15)"
            badge_color = "#a5b4fc"
            badge_border = "rgba(99, 102, 241, 0.3)"
        else:
            badge_bg = "rgba(251, 191, 36, 0.15)"
            badge_color = "#fbbf24"
            badge_border = "rgba(251, 191, 36, 0.3)"
        
        self.lbl_status = QLabel(status)
        self.lbl_status.setStyleSheet(f"""
            font-size: 10px; 
            padding: 3px 8px; 
            border-radius: 6px; 
            background: {badge_bg}; 
            color: {badge_color}; 
            border: 1px solid {badge_border};
            font-weight: 700;
        """)
        
        # Copy name button
        self.btn_copy_name = QPushButton("Copy")
        self.btn_copy_name.setFixedSize(42, 22)
        self.btn_copy_name.setCursor(Qt.PointingHandCursor)
        self.btn_copy_name.setToolTip("Copy name to clipboard")
        self.btn_copy_name.setStyleSheet("""
            QPushButton {
                background: rgba(99, 102, 241, 0.08);
                border: 1px solid rgba(99, 102, 241, 0.2);
                border-radius: 4px;
                color: #818cf8;
                font-size: 10px;
                font-weight: 700;
                padding: 0;
            }
            QPushButton:hover {
                background: rgba(99, 102, 241, 0.25);
                color: #e0e7ff;
                border-color: #6366f1;
            }
        """)
        self.btn_copy_name.clicked.connect(self._copy_name)

        header_row.addWidget(self.lbl_name)
        header_row.addSpacing(4)
        header_row.addWidget(self.btn_copy_name)
        header_row.addStretch()
        header_row.addWidget(self.lbl_status)
        
        # Details Row: Amount
        self.lbl_details = QLabel(f"${total_amount:,.2f}")
        self.lbl_details.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.lbl_details.setStyleSheet("color: #a5b4fc; font-size: 13px; font-weight: 600; background: transparent;")
        
        # Action Buttons Layout
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(6)

        # 1. Copy Bill Button (copies full invoice text to clipboard)
        self.btn_copy_bill = QPushButton("Copy Bill")
        self.btn_copy_bill.setFixedHeight(30)
        self.btn_copy_bill.setCursor(Qt.PointingHandCursor)
        self.btn_copy_bill.setStyleSheet("""
            QPushButton { 
                background: rgba(99, 102, 241, 0.1); 
                border: 1px solid rgba(99, 102, 241, 0.25); 
                border-radius: 6px; 
                padding: 2px 8px; 
                font-size: 11px; 
                color: #a5b4fc;
                font-weight: 700;
            }
            QPushButton:hover { background: rgba(99, 102, 241, 0.2); color: #e0e7ff; border-color: #6366f1; }
        """)
        self.btn_copy_bill.setToolTip("Copy full invoice text to clipboard")
        self.btn_copy_bill.clicked.connect(lambda: self.copyBillRequested.emit(self.name, self.phone))

        # 2. Share WhatsApp Button (manual: gen PDF → copy → open WA chat)
        self.btn_share_wa = QPushButton("Share WA")
        self.btn_share_wa.setFixedHeight(30)
        self.btn_share_wa.setCursor(Qt.PointingHandCursor)
        self.btn_share_wa.setStyleSheet("""
            QPushButton { 
                background: rgba(37, 211, 102, 0.1); 
                border: 1px solid rgba(37, 211, 102, 0.25); 
                border-radius: 6px; 
                padding: 2px 10px; 
                font-size: 11px; 
                color: #25d366;
                font-weight: 700;
            }
            QPushButton:hover { background: rgba(37, 211, 102, 0.25); color: #ffffff; border-color: #25d366; }
        """)
        self.btn_share_wa.setToolTip("Generate PDF, copy to clipboard, and open WhatsApp chat")
        self.btn_share_wa.clicked.connect(lambda: self.shareWhatsAppRequested.emit(self.name, self.phone))

        # 3. Send WhatsApp Button (automated paste & send)
        self.btn_send = QPushButton("Send WA")
        self.btn_send.setFixedHeight(30)
        self.btn_send.setCursor(Qt.PointingHandCursor)
        self.btn_send.setStyleSheet("""
            QPushButton { 
                background: rgba(34, 197, 94, 0.1); 
                border: 1px solid rgba(34, 197, 94, 0.2); 
                border-radius: 6px; 
                padding: 2px 10px; 
                font-size: 11px; 
                color: #4ade80;
                font-weight: 700;
            }
            QPushButton:hover { background: rgba(34, 197, 94, 0.2); color: #ffffff; border-color: #22c55e; }
        """)
        self.btn_send.setToolTip("Auto-paste & send PDF via WhatsApp")
        self.btn_send.clicked.connect(lambda: self.sendWhatsAppRequested.emit(self.name, self.phone))

        # 4. Delete Button (Small Trash)
        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setFixedHeight(30)
        self.btn_delete.setCursor(Qt.PointingHandCursor)
        self.btn_delete.setStyleSheet("""
            QPushButton { 
                background: rgba(239, 68, 68, 0.1); 
                border: 1px solid rgba(239, 68, 68, 0.2); 
                border-radius: 6px; 
                padding: 2px 8px; 
                font-size: 11px; 
                color: #f87171;
            }
            QPushButton:hover { background: rgba(239, 68, 68, 0.2); color: #ffffff; border-color: #ef4444; }
        """)
        self.btn_delete.clicked.connect(lambda: self.deleteRequested.emit(self.name, self.phone))

        actions_layout.addWidget(self.btn_copy_bill)
        actions_layout.addWidget(self.btn_share_wa)
        actions_layout.addWidget(self.btn_send)
        actions_layout.addWidget(self.btn_delete)

        layout.addLayout(header_row)
        layout.addWidget(self.lbl_details)
        layout.addLayout(actions_layout)

    def _copy_name(self):
        """Copy customer name to clipboard."""
        QApplication.clipboard().setText(self.name)

    def mousePressEvent(self, event):
        # Only emit clicked if we didn't click a button
        if self.childAt(event.pos()) is None or not isinstance(self.childAt(event.pos()), QPushButton):
            if event.button() == Qt.LeftButton:
                self.clicked.emit(self.name, self.phone)
        super().mousePressEvent(event)

    def set_active(self, active):
        if active:
            self.setStyleSheet("""
                QFrame#CustomerCard { 
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(99, 102, 241, 0.2), stop:1 rgba(30, 41, 59, 0.9));
                    border: 2px solid #6366f1; 
                    border-radius: 12px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame#CustomerCard { 
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(30, 41, 59, 0.6), stop:1 rgba(15, 23, 42, 0.8));
                    border: 1px solid rgba(99, 102, 241, 0.15); 
                    border-radius: 12px;
                }
            """)
