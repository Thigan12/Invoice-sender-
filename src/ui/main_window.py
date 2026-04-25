from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                               QLabel, QLineEdit, QPushButton, QScrollArea, QFrame, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QStackedWidget,
                               QMessageBox, QSplitter, QApplication, QGraphicsDropShadowEffect,
                               QDialog, QSpinBox, QComboBox, QSizePolicy, QStatusBar)
from PySide6.QtCore import Qt, QMimeData, QUrl, QTimer, QSize
from PySide6.QtGui import QColor, QFont
import os
import time
try:
    import pyautogui
except ImportError:
    pyautogui = None
from src.ui.widgets.customer_card import CustomerCard
from src.ui.views.import_view import ImportView
from src.ui.views.customer_details_view import CustomerDetailsView
from src.ui.views.dashboard_view import DashboardView
from src.ui.views.all_customers_view import AllCustomersView
from src.ui.views.delivery_view import DeliveryView
from src.ui.views.template_view import TemplateView
from src.core.pdf_engine import PDFEngine
from src.core.whatsapp import WhatsAppBridge
from src.database.repository import DataRepository

# ---- Premium Button Styles ----
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
    QPushButton:pressed { background: #4338ca; }
    QPushButton:disabled { background: #334155; color: #64748b; }
"""

BTN_SUCCESS = """
    QPushButton { 
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #22c55e, stop:1 #16a34a);
        border: none;
        border-radius: 8px; 
        padding: 8px 18px; 
        font-size: 12px; 
        font-weight: 700;
        color: #ffffff;
    }
    QPushButton:hover { 
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #4ade80, stop:1 #22c55e);
    }
    QPushButton:pressed { background: #15803d; }
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
    QPushButton:pressed { background: rgba(99, 102, 241, 0.3); }
    QPushButton:disabled { color: #475569; border-color: rgba(71, 85, 105, 0.2); }
"""

BTN_DANGER = """
    QPushButton { 
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 8px; 
        padding: 8px 16px; 
        font-size: 12px; 
        font-weight: 700;
        color: #f87171;
    }
    QPushButton:hover { 
        background: rgba(239, 68, 68, 0.25);
        border-color: #ef4444;
        color: #fca5a5;
    }
"""

BTN_SHARE_WA = """
    QPushButton { 
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #25d366, stop:1 #128c7e);
        border: none;
        border-radius: 8px; 
        padding: 8px 18px; 
        font-size: 12px; 
        font-weight: 700;
        color: #ffffff;
    }
    QPushButton:hover { 
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #34eb7a, stop:1 #25d366);
    }
    QPushButton:pressed { background: #128c7e; }
    QPushButton:disabled { background: #334155; color: #64748b; }
"""


class InvoiceCustomerPopup(QDialog):
    """Popup showing customer's invoice items with action buttons and status."""
    action_performed = None  # Will be set per-instance

    def __init__(self, parent, name, phone, invoice, items, pdf_engine, whatsapp_bridge):
        super().__init__(parent)
        self.name = name
        self.phone = phone
        self.invoice = invoice  # (id, inv_number, total, status, cust_name, pdf_path)
        self.items = items
        self.pdf_engine = pdf_engine
        self.whatsapp_bridge = whatsapp_bridge
        self.did_action = False

        self.setWindowTitle(f"Invoice - {name}")
        self.setMinimumSize(750, 580)
        self.resize(820, 620)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0f172a, stop:1 #1e293b);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(16)

        # ---- Header with customer info + status ----
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
        header_layout.setContentsMargins(20, 18, 20, 18)

        # Avatar
        avatar = QLabel(name[0].upper() if name else "?")
        avatar.setFixedSize(50, 50)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6366f1, stop:1 #8b5cf6);
                border-radius: 25px;
                font-size: 22px;
                font-weight: 800;
                color: white;
            }
        """)

        info_col = QVBoxLayout()
        info_col.setSpacing(3)
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("font-size: 20px; font-weight: 800; color: #f8fafc; background: transparent;")
        phone_lbl = QLabel(phone if phone and phone.strip() else "No phone number")
        phone_lbl.setStyleSheet("font-size: 12px; color: #94a3b8; background: transparent;")
        info_col.addWidget(name_lbl)
        info_col.addWidget(phone_lbl)

        # Status badge
        status = invoice[3] if invoice else "Draft"
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

        status_badge = QLabel(status)
        status_badge.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                padding: 6px 16px;
                border-radius: 8px;
                background: {badge_bg};
                color: {badge_color};
                border: 1px solid {badge_border};
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
        """)

        # Total
        total_val = invoice[2] if invoice else 0.0
        total_lbl = QLabel(f"${total_val:,.2f}")
        total_lbl.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: 800;
                color: #4ade80;
                background: transparent;
            }
        """)

        header_layout.addWidget(avatar)
        header_layout.addSpacing(14)
        header_layout.addLayout(info_col)
        header_layout.addStretch()
        header_layout.addWidget(status_badge)
        header_layout.addSpacing(16)
        header_layout.addWidget(total_lbl)

        layout.addWidget(header_frame)

        # ---- Invoice Number ----
        if invoice:
            inv_lbl = QLabel(f"Invoice: {invoice[1]}")
            inv_lbl.setStyleSheet("font-size: 12px; color: #64748b; background: transparent;")
            layout.addWidget(inv_lbl)

        # ---- Items Table ----
        items_label = QLabel("Purchased Items")
        items_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #e2e8f0; background: transparent;")
        layout.addWidget(items_label)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Item Name", "Qty", "Unit Price", "Subtotal"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(42)
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
                padding: 10px 14px; 
                border-bottom: 1px solid rgba(99, 102, 241, 0.08);
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
            }
        """)

        for i, (desc, qty, price, sub) in enumerate(items):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(desc))
            qty_item = QTableWidgetItem(str(int(qty)) if qty else "1")
            qty_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 1, qty_item)
            price_item = QTableWidgetItem(f"${price:,.2f}")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, 2, price_item)
            sub_item = QTableWidgetItem(f"${sub:,.2f}")
            sub_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            sub_item.setForeground(QColor("#a5b4fc"))
            self.table.setItem(i, 3, sub_item)

        layout.addWidget(self.table)

        # ---- Total Bar ----
        total_bar = QFrame()
        total_bar.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(99, 102, 241, 0.1), stop:1 rgba(30, 41, 59, 0.5));
                border: 1px solid rgba(99, 102, 241, 0.2);
                border-radius: 10px;
            }
        """)
        total_bar_layout = QHBoxLayout(total_bar)
        total_bar_layout.setContentsMargins(18, 12, 18, 12)
        total_text = QLabel("Total Amount")
        total_text.setStyleSheet("font-size: 14px; font-weight: 600; color: #94a3b8; background: transparent;")
        total_amount = QLabel(f"${total_val:,.2f}")
        total_amount.setStyleSheet("font-size: 26px; font-weight: 800; color: #a5b4fc; background: transparent;")
        total_bar_layout.addWidget(total_text)
        total_bar_layout.addStretch()
        total_bar_layout.addWidget(total_amount)
        layout.addWidget(total_bar)

        # ---- Action Buttons ----
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(10)

        self.btn_gen_pdf = QPushButton("Generate PDF")
        self.btn_gen_pdf.setFixedHeight(42)
        self.btn_gen_pdf.setStyleSheet(BTN_PRIMARY)
        self.btn_gen_pdf.clicked.connect(self._on_gen_pdf)

        self.btn_share_wa = QPushButton("Share WA")
        self.btn_share_wa.setFixedHeight(42)
        self.btn_share_wa.setStyleSheet(BTN_SHARE_WA)
        self.btn_share_wa.setToolTip("Generate PDF, copy to clipboard, and open WhatsApp chat")
        self.btn_share_wa.clicked.connect(self._on_share_wa)

        self.btn_send_wa = QPushButton("Send WA")
        self.btn_send_wa.setFixedHeight(42)
        self.btn_send_wa.setStyleSheet(BTN_SUCCESS)
        self.btn_send_wa.setToolTip("Auto-paste & send PDF via WhatsApp")
        self.btn_send_wa.clicked.connect(self._on_send_wa)

        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setFixedHeight(42)
        self.btn_delete.setStyleSheet(BTN_DANGER)
        self.btn_delete.clicked.connect(self._on_delete)

        btn_close = QPushButton("Close")
        btn_close.setFixedHeight(42)
        btn_close.setStyleSheet(BTN_GHOST)
        btn_close.clicked.connect(self.accept)

        btn_bar.addWidget(self.btn_gen_pdf)
        btn_bar.addWidget(self.btn_share_wa)
        btn_bar.addWidget(self.btn_send_wa)
        btn_bar.addWidget(self.btn_delete)
        btn_bar.addStretch()
        btn_bar.addWidget(btn_close)
        layout.addLayout(btn_bar)

        # Disable buttons if no invoice
        if not invoice:
            self.btn_gen_pdf.setEnabled(False)
            self.btn_share_wa.setEnabled(False)
            self.btn_send_wa.setEnabled(False)
            self.btn_delete.setEnabled(False)

    def _on_gen_pdf(self):
        """Generate PDF for this customer's invoice."""
        if not self.invoice:
            return
        try:
            pdf_path = self.pdf_engine.generate(
                customer_name=self.name,
                invoice_number=self.invoice[1],
                items=self.items,
                total_amount=self.invoice[2]
            )
            DataRepository.update_invoice_pdf(self.invoice[0], pdf_path)
            self.did_action = True
            QMessageBox.information(self, "Success", f"PDF generated for {self.name}.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate PDF: {str(e)}")

    def _on_share_wa(self):
        """Share WhatsApp — manual flow: generate PDF, copy to clipboard, open WA chat."""
        if not self.invoice:
            return
        phone = self.phone
        if not phone or phone.strip() == "" or phone == "None":
            phone = DataRepository.find_phone_by_name(self.name)
        if not phone:
            QMessageBox.warning(self, "No Phone", f"No phone number found for {self.name}.")
            return

        # Step 1: Ensure PDF exists (auto-generate if needed)
        pdf_path = self.invoice[5] if len(self.invoice) > 5 else None
        if not pdf_path or not os.path.exists(pdf_path):
            try:
                pdf_path = self.pdf_engine.generate(
                    customer_name=self.name,
                    invoice_number=self.invoice[1],
                    items=self.items,
                    total_amount=self.invoice[2]
                )
                DataRepository.update_invoice_pdf(self.invoice[0], pdf_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to generate PDF: {str(e)}")
                return

        # Step 2: Copy PDF to clipboard
        try:
            mime_data = QMimeData()
            mime_data.setUrls([QUrl.fromLocalFile(os.path.abspath(pdf_path))])
            QApplication.clipboard().setMimeData(mime_data)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to copy PDF: {str(e)}")
            return

        # Step 3: Open WhatsApp chat with invoice message
        try:
            self.whatsapp_bridge.send_with_message(
                phone=phone, customer_name=self.name,
                invoice_no=self.invoice[1], total_amount=self.invoice[2])
            DataRepository.update_invoice_status(self.invoice[0], "Sent")
            self.did_action = True
            QMessageBox.information(self, "Share WhatsApp",
                f"PDF generated and copied to clipboard.\n\n"
                f"WhatsApp chat opened for {self.name}.\n"
                f"Just paste (Ctrl+V) and send!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open WhatsApp: {str(e)}")

    def _on_send_wa(self):
        """Send WhatsApp for this customer (automated paste & send)."""
        if not self.invoice:
            return
        phone = self.phone
        if not phone or phone.strip() == "" or phone == "None":
            phone = DataRepository.find_phone_by_name(self.name)
        if not phone:
            QMessageBox.warning(self, "No Phone", f"No phone number found for {self.name}.")
            return

        pdf_path = self.invoice[5] if len(self.invoice) > 5 else None
        if not pdf_path or not os.path.exists(pdf_path):
            reply = QMessageBox.question(self, "Generate PDF?",
                f"No PDF found. Generate it first?",
                QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self._on_gen_pdf()
                # Re-fetch invoice to get updated pdf_path
                inv, _ = DataRepository.get_latest_invoice_by_details(self.name, self.phone)
                if inv:
                    pdf_path = inv[5]
            else:
                return

        if not pdf_path or not os.path.exists(pdf_path):
            return

        try:
            mime_data = QMimeData()
            mime_data.setUrls([QUrl.fromLocalFile(os.path.abspath(pdf_path))])
            QApplication.clipboard().setMimeData(mime_data)

            success = self.whatsapp_bridge.send_with_message(
                phone=phone, customer_name=self.name,
                invoice_no=self.invoice[1], total_amount=self.invoice[2])
            if success:
                DataRepository.update_invoice_status(self.invoice[0], "Sent")
                self.did_action = True
                QMessageBox.information(self, "Sent", f"WhatsApp opened for {self.name}. PDF copied to clipboard.")
                self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed: {str(e)}")

    def _on_delete(self):
        """Delete this customer's invoice."""
        reply = QMessageBox.question(self, "Delete?",
            f"Delete {self.name} and all their invoice history?\n\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                DataRepository.delete_customer_by_details(self.name, self.phone)
                self.did_action = True
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete: {str(e)}")


class SettingsDialog(QDialog):
    """Window size & UI customisation dialog."""
    def __init__(self, parent):
        super().__init__(parent)
        self.main_win = parent
        self.setWindowTitle("App Settings")
        self.setMinimumWidth(420)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0f172a, stop:1 #1e293b);
            }
            QLabel { color: #e2e8f0; background: transparent; }
            QSpinBox, QComboBox {
                background: rgba(15,23,42,0.9);
                color: #e2e8f0;
                border: 1px solid rgba(99,102,241,0.35);
                border-radius: 7px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background: rgba(99,102,241,0.15);
                border-radius: 4px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background: #1e293b;
                color: #e2e8f0;
                selection-background-color: rgba(99,102,241,0.35);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        # ---- Title ----
        title = QLabel("⚙  App Customisation")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #a5b4fc;")
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: rgba(99,102,241,0.2);")
        layout.addWidget(sep)

        # ---- Window Size Presets ----
        preset_lbl = QLabel("Window Size Preset")
        preset_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #94a3b8;")
        layout.addWidget(preset_lbl)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Custom",
            "Compact  (1024 × 700)",
            "Default  (1250 × 850)",
            "Large    (1440 × 900)",
            "Full HD  (1920 × 1080)",
            "Maximise Window",
        ])
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        layout.addWidget(self.preset_combo)

        # ---- Custom Size ----
        custom_lbl = QLabel("Custom Window Size")
        custom_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #94a3b8;")
        layout.addWidget(custom_lbl)

        size_row = QHBoxLayout()
        size_row.setSpacing(10)

        w_lbl = QLabel("Width:")
        self.spin_w = QSpinBox()
        self.spin_w.setRange(800, 3840)
        self.spin_w.setSingleStep(50)
        self.spin_w.setValue(parent.width())
        self.spin_w.setSuffix(" px")

        h_lbl = QLabel("Height:")
        self.spin_h = QSpinBox()
        self.spin_h.setRange(600, 2160)
        self.spin_h.setSingleStep(50)
        self.spin_h.setValue(parent.height())
        self.spin_h.setSuffix(" px")

        size_row.addWidget(w_lbl)
        size_row.addWidget(self.spin_w)
        size_row.addSpacing(8)
        size_row.addWidget(h_lbl)
        size_row.addWidget(self.spin_h)
        layout.addLayout(size_row)

        # ---- Sidebar Width ----
        side_lbl = QLabel("Sidebar Width")
        side_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #94a3b8;")
        layout.addWidget(side_lbl)

        side_row = QHBoxLayout()
        side_row.setSpacing(10)
        sw_lbl = QLabel("Width:")
        self.spin_sw = QSpinBox()
        self.spin_sw.setRange(200, 600)
        self.spin_sw.setSingleStep(10)
        # Read current sidebar width
        try:
            self.spin_sw.setValue(parent.sidebar.width() or 330)
        except Exception:
            self.spin_sw.setValue(330)
        self.spin_sw.setSuffix(" px")
        side_row.addWidget(sw_lbl)
        side_row.addWidget(self.spin_sw)
        side_row.addStretch()
        layout.addLayout(side_row)

        sep_mid = QFrame()
        sep_mid.setFrameShape(QFrame.HLine)
        sep_mid.setStyleSheet("color: rgba(99,102,241,0.2);")
        layout.addWidget(sep_mid)

        # ---- Database Location ----
        db_lbl = QLabel("Database Location")
        db_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #94a3b8;")
        layout.addWidget(db_lbl)

        db_desc = QLabel("Point to a shared folder to use the same database on multiple computers.")
        db_desc.setStyleSheet("font-size: 11px; color: #64748b;")
        db_desc.setWordWrap(True)
        layout.addWidget(db_desc)

        from src.utils.paths import get_db_path
        self.lbl_db_path = QLabel(get_db_path())
        self.lbl_db_path.setWordWrap(True)
        self.lbl_db_path.setStyleSheet("""
            font-size: 11px;
            color: #a5b4fc;
            background: rgba(15,23,42,0.6);
            border: 1px solid rgba(99,102,241,0.15);
            border-radius: 6px;
            padding: 8px 10px;
        """)
        layout.addWidget(self.lbl_db_path)

        db_btn_row = QHBoxLayout()
        db_btn_row.setSpacing(8)

        btn_browse_db = QPushButton("Browse")
        btn_browse_db.setFixedHeight(34)
        btn_browse_db.setStyleSheet(BTN_GHOST)
        btn_browse_db.clicked.connect(self._browse_db)

        btn_reset_db = QPushButton("Reset to Default")
        btn_reset_db.setFixedHeight(34)
        btn_reset_db.setStyleSheet(BTN_GHOST)
        btn_reset_db.clicked.connect(self._reset_db_path)

        db_btn_row.addWidget(btn_browse_db)
        db_btn_row.addWidget(btn_reset_db)
        db_btn_row.addStretch()
        layout.addLayout(db_btn_row)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("color: rgba(99,102,241,0.2);")
        layout.addWidget(sep2)

        # ---- Apply / Close ----
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_apply = QPushButton("Apply")
        btn_apply.setFixedHeight(40)
        btn_apply.setStyleSheet(BTN_PRIMARY)
        btn_apply.clicked.connect(self._apply)

        btn_reset = QPushButton("Reset Defaults")
        btn_reset.setFixedHeight(40)
        btn_reset.setStyleSheet(BTN_GHOST)
        btn_reset.clicked.connect(self._reset)

        btn_close = QPushButton("Close")
        btn_close.setFixedHeight(40)
        btn_close.setStyleSheet(BTN_GHOST)
        btn_close.clicked.connect(self.accept)

        btn_row.addWidget(btn_apply)
        btn_row.addWidget(btn_reset)
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def _on_preset_changed(self, idx):
        presets = [
            None,
            (1024, 700),
            (1250, 850),
            (1440, 900),
            (1920, 1080),
            None,  # Maximise
        ]
        p = presets[idx]
        if p:
            self.spin_w.setValue(p[0])
            self.spin_h.setValue(p[1])

    def _apply(self):
        idx = self.preset_combo.currentIndex()
        if idx == 5:  # Maximise
            self.main_win.showMaximized()
        else:
            w = self.spin_w.value()
            h = self.spin_h.value()
            self.main_win.resize(w, h)
            self.main_win.showNormal()

        # Apply sidebar width via splitter
        sw = self.spin_sw.value()
        try:
            if hasattr(self.main_win, 'invoice_splitter'):
                total = self.main_win.invoice_splitter.width()
                self.main_win.invoice_splitter.setSizes([sw, total - sw])
        except Exception:
            pass

        self.main_win.statusBar().showMessage(
            f"Window resized to {self.main_win.width()} × {self.main_win.height()}  |  Sidebar: {sw}px",
            3000
        )

    def _reset(self):
        self.spin_w.setValue(1250)
        self.spin_h.setValue(850)
        self.spin_sw.setValue(330)
        self.preset_combo.setCurrentIndex(2)
        self._apply()

    def _browse_db(self):
        from PySide6.QtWidgets import QFileDialog
        from src.utils.paths import set_db_directory, get_db_path
        from src.database.connection import init_db

        folder = QFileDialog.getExistingDirectory(
            self, "Select Database Folder", "",
            QFileDialog.ShowDirsOnly)
        if not folder:
            return

        set_db_directory(folder)
        new_path = get_db_path()
        self.lbl_db_path.setText(new_path)

        # Initialize schema at new location (creates tables if DB doesn't exist)
        init_db()

        QMessageBox.information(self, "Database Updated",
            f"Database location changed to:\n\n{new_path}\n\n"
            "Please restart the application for all views to reload.")

    def _reset_db_path(self):
        from src.utils.paths import set_db_directory, get_db_path

        set_db_directory("")
        default_path = get_db_path()
        self.lbl_db_path.setText(default_path)

        QMessageBox.information(self, "Database Reset",
            f"Database location reset to default:\n\n{default_path}\n\n"
            "Please restart the application for all views to reload.")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AutoBillr Pro")
        self.resize(1250, 850)
        self.setMinimumSize(800, 600)

        # Set Window Icon
        from src.utils.paths import get_base_dir
        logo_path = os.path.join(get_base_dir(), "assets", "icons", "logo.png")
        if os.path.exists(logo_path):
            from PySide6.QtGui import QIcon
            self.setWindowIcon(QIcon(logo_path))

        # Status bar for non-intrusive notifications
        self._status_bar = QStatusBar()
        self._status_bar.setStyleSheet("""
            QStatusBar {
                background: rgba(15,23,42,0.95);
                color: #a5b4fc;
                font-size: 12px;
                border-top: 1px solid rgba(99,102,241,0.15);
                padding: 2px 10px;
            }
        """)
        self.setStatusBar(self._status_bar)
        
        self.pdf_engine = PDFEngine()
        self.whatsapp_bridge = WhatsAppBridge()
        self.current_phone = None
        self.current_invoice_id = None
        self.current_invoice_number = None
        self.current_total = 0.0
        self.current_pdf_path = None
        self.wa_all_stopped = False
        self.current_session_invoice_ids = []  # Tracks IDs from the latest import session
        
        # Central Widget
        self.central_widget = QWidget()
        self.central_widget.setObjectName("centralWidget")
        self.setCentralWidget(self.central_widget)
        # Main Layout
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 1. NAVIGATION RAIL (Far Left)
        self.setup_nav_rail()
        self.main_layout.addWidget(self.nav_rail)

        # 2. Main Stacked Widget
        self.content_area = QStackedWidget()
        self.content_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.content_area.setStyleSheet("background: #0f172a; border: none;")
        self.main_layout.addWidget(self.content_area, 1)

        # --- Dashboard View (Index 0) ---
        self.dashboard_view = DashboardView()
        self.dashboard_view.startImportRequested.connect(lambda: self.switch_page(2))
        self.dashboard_view.viewInvoicesRequested.connect(self.on_dashboard_import_selected)
        self.dashboard_view.editImportRequested.connect(self.on_edit_import)
        self.content_area.addWidget(self.dashboard_view)

        # --- Invoices View (Index 1) ---
        self.setup_invoice_container()
        self.content_area.addWidget(self.invoice_container)

        # --- Import View (Index 2) ---
        self.import_view = ImportView()
        self.import_view.data_imported.connect(self.on_dashboard_import_selected)
        self.content_area.addWidget(self.import_view)

        # --- Customer Details View (Index 3) ---
        self.customer_view = CustomerDetailsView()
        self.customer_view.customer_updated.connect(self.refresh_customer_list)
        self.content_area.addWidget(self.customer_view)

        # --- All Customers / Details View (Index 4) ---
        self.all_customers_view = AllCustomersView()
        self.content_area.addWidget(self.all_customers_view)

        # --- Delivery View (Index 5) ---
        self.delivery_view = DeliveryView()
        self.content_area.addWidget(self.delivery_view)

        # --- Template View (Index 6) ---
        self.template_view = TemplateView()
        self.content_area.addWidget(self.template_view)

        # Start on Dashboard
        self.switch_page(0)

    def setup_nav_rail(self):
        self.nav_rail = QFrame()
        self.nav_rail.setFixedWidth(220)
        self.nav_rail.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0f172a, stop:1 #1e293b);
                border-right: 1px solid rgba(99, 102, 241, 0.12);
            }
            QPushButton {
                background: transparent;
                border: none;
                color: #64748b;
                font-size: 13px;
                font-weight: 700;
                padding: 14px 25px;
                text-align: left;
                border-radius: 0px;
            }
            QPushButton:hover {
                color: #a5b4fc;
                background: rgba(99, 102, 241, 0.06);
            }
            QPushButton[active="true"] {
                color: #818cf8;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(99, 102, 241, 0.15), stop:1 transparent);
                border-left: 3px solid #6366f1;
                padding-left: 22px;
            }
        """)
        
        rail_layout = QVBoxLayout(self.nav_rail)
        rail_layout.setContentsMargins(0, 0, 0, 20)
        rail_layout.setSpacing(4)

        # ---- LOGO SECTION ----
        logo_frame = QFrame()
        logo_frame.setStyleSheet("""
            QFrame {
                background: transparent;
                border-bottom: 1px solid rgba(99, 102, 241, 0.1);
                padding-bottom: 0px;
            }
        """)
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(20, 24, 20, 18)
        logo_layout.setSpacing(6)

        # Logo row (now centered and larger)
        logo_row = QHBoxLayout()
        logo_row.setAlignment(Qt.AlignCenter)

        logo_icon = QLabel()
        
        from src.utils.paths import get_base_dir
        logo_path = os.path.join(get_base_dir(), "assets", "icons", "logo.png")
        
        if os.path.exists(logo_path):
            from PySide6.QtGui import QPixmap
            # Maximum width for sidebar is 220, so 160-180 is good
            pixmap = QPixmap(logo_path).scaled(160, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_icon.setPixmap(pixmap)
            logo_icon.setFixedSize(160, 80) # Adjust height as needed for horizontal logo
            logo_icon.setStyleSheet("background: transparent; border: none;")
        else:
            logo_icon.setText("AB")
            logo_icon.setFixedSize(60, 60)
            logo_icon.setAlignment(Qt.AlignCenter)
            logo_icon.setStyleSheet("""
                QLabel {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #6366f1, stop:1 #8b5cf6);
                    border-radius: 15px;
                    font-size: 24px;
                    font-weight: 900;
                    color: white;
                }
            """)

        logo_row.addWidget(logo_icon)
        logo_layout.addLayout(logo_row)

        logo_sub = QLabel("Invoice Management System")
        logo_sub.setAlignment(Qt.AlignCenter)
        logo_sub.setStyleSheet("""
            font-size: 11px;
            color: #475569;
            background: transparent;
            margin-top: 4px;
        """)
        logo_layout.addWidget(logo_sub)

        rail_layout.addWidget(logo_frame)
        rail_layout.addSpacing(12)

        # ---- NAV SECTION LABEL ----
        nav_label = QLabel("  MENU")
        nav_label.setStyleSheet("""
            font-size: 10px;
            font-weight: 700;
            color: #334155;
            letter-spacing: 2px;
            padding: 4px 20px;
            background: transparent;
        """)
        rail_layout.addWidget(nav_label)
        rail_layout.addSpacing(4)

        self.nav_btns = []
        nav_data = [
            ("Dashboard", 0),
            ("Invoices", 1),
            ("Import", 2),
            ("Customers", 3),
            ("Details", 4),
            ("Delivery", 5),
            ("Template", 6)
        ]

        for label, idx in nav_data:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, i=idx: self.switch_page(i))
            rail_layout.addWidget(btn)
            self.nav_btns.append(btn)

        rail_layout.addStretch()

        # ---- SETTINGS BUTTON ----
        settings_sep = QFrame()
        settings_sep.setFrameShape(QFrame.HLine)
        settings_sep.setStyleSheet("color: rgba(99,102,241,0.12); margin: 0 16px;")
        rail_layout.addWidget(settings_sep)

        btn_settings = QPushButton("⚙  Settings")
        btn_settings.setToolTip("Customise window size, sidebar width, and UI")
        btn_settings.clicked.connect(self.open_settings)
        btn_settings.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #64748b;
                font-size: 12px;
                font-weight: 700;
                padding: 12px 25px;
                text-align: left;
                border-radius: 0px;
            }
            QPushButton:hover {
                color: #a5b4fc;
                background: rgba(99, 102, 241, 0.06);
            }
        """)
        rail_layout.addWidget(btn_settings)

        # ---- FOOTER ----
        footer_box = QVBoxLayout()
        footer_box.setSpacing(2)
        footer_box.setContentsMargins(0, 4, 0, 8)

        footer_ver = QLabel("v2.0 — Professional")
        footer_ver.setAlignment(Qt.AlignCenter)
        footer_ver.setStyleSheet("font-size: 10px; color: #334155; background: transparent;")

        footer_credit = QLabel("Created by R.Thigan")
        footer_credit.setAlignment(Qt.AlignCenter)
        footer_credit.setStyleSheet("font-size: 13px; color: #6366f1; font-weight: 800; background: transparent;")

        footer_box.addWidget(footer_ver)
        footer_box.addWidget(footer_credit)
        rail_layout.addLayout(footer_box)

    def switch_page(self, index, reset_invoices=True):
        self.content_area.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_btns):
            btn.setProperty("active", i == index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
        if index == 0:
            self.dashboard_view.refresh_data()
        elif index == 1:
            if reset_invoices:
                self.reset_invoice_view()
            # Always refresh the customer list when navigating to Invoices
            self.refresh_customer_list()
        elif index == 4:
            self.all_customers_view.refresh_data()
        elif index == 5:
            self.delivery_view.refresh_imports()

    def reset_invoice_view(self):
        """Clears the entire invoice page to a 'fresh' state (does NOT delete any data)."""
        # Reset the customer header
        self.lbl_active_customer.setText("Select a Customer")

        # Reset all internal state variables
        self.current_phone = None
        self.current_invoice_id = None
        self.current_invoice_number = None
        self.current_total = 0.0
        self.current_pdf_path = None
        self.current_session_invoice_ids = [] # Clear the session tracking

        # Clear the invoice items table
        self.table.setRowCount(0)

        # Reset the total display
        self.lbl_total.setText("$0.00")

        # Clear the search box
        self.search_input.clear()

        # Hide the WA stop button if it was visible
        self.btn_stop_wa.setVisible(False)

        # Hide the invoice detail panel and let sidebar fill full width
        self.invoice_view.setVisible(False)

        # Remove all customer cards from the sidebar (visual clear only, no DB delete)
        while self.customer_list_layout.count():
            item = self.customer_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def setup_invoice_container(self):
        """Combines the customer sidebar and the actual invoice editor with a draggable splitter."""
        self.invoice_container = QWidget()
        self.invoice_container_layout = QHBoxLayout(self.invoice_container)
        self.invoice_container_layout.setContentsMargins(0, 0, 0, 0)
        self.invoice_container_layout.setSpacing(0)

        # Draggable splitter between sidebar and invoice view
        self.invoice_splitter = QSplitter(Qt.Horizontal)
        self.invoice_splitter.setHandleWidth(5)
        self.invoice_splitter.setStyleSheet("""
            QSplitter::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent, stop:0.4 rgba(99,102,241,0.35), stop:0.6 rgba(99,102,241,0.35), stop:1 transparent);
                min-width: 5px;
                max-width: 5px;
            }
            QSplitter::handle:horizontal:hover {
                background: rgba(99,102,241,0.6);
            }
        """)

        # Sidebar (Customer List)
        self.setup_sidebar()
        self.invoice_splitter.addWidget(self.sidebar)

        # Invoice View (Editor) — hidden until a customer is selected
        self.setup_invoice_view()
        self.invoice_splitter.addWidget(self.invoice_view)
        self.invoice_view.setVisible(False)

        # Set initial proportions (sidebar:invoice = 1:2)
        self.invoice_splitter.setSizes([330, 660])
        self.invoice_splitter.setStretchFactor(0, 1)
        self.invoice_splitter.setStretchFactor(1, 2)

        self.invoice_container_layout.addWidget(self.invoice_splitter)

    def setup_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setMinimumWidth(200)
        self.sidebar.setStyleSheet("""
            QFrame#sidebar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e293b, stop:1 #0f172a);
                border-right: 1px solid rgba(99, 102, 241, 0.2);
            }
        """)
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(16, 22, 16, 22)
        sidebar_layout.setSpacing(0)
        
        # Brand
        brand_label = QLabel("InvoicePro")
        brand_label.setStyleSheet("""
            font-size: 22px; 
            font-weight: 800; 
            color: #a5b4fc; 
            padding-bottom: 4px;
            background: transparent;
        """)
        sidebar_layout.addWidget(brand_label)
        
        sub_brand = QLabel("Professional Invoice Manager")
        sub_brand.setStyleSheet("font-size: 11px; color: #64748b; padding-bottom: 14px; background: transparent;")
        sidebar_layout.addWidget(sub_brand)
        
        # Action Buttons Row
        btns_layout = QHBoxLayout()
        btns_layout.setSpacing(6)
        
        self.btn_gen_all_side = QPushButton("Gen All")
        self.btn_gen_all_side.setFixedHeight(34)
        self.btn_gen_all_side.setStyleSheet(BTN_GHOST)
        self.btn_gen_all_side.clicked.connect(self.on_generate_all)
        
        self.btn_wa_all_side = QPushButton("WA All")
        self.btn_wa_all_side.setFixedHeight(34)
        self.btn_wa_all_side.setStyleSheet(BTN_SUCCESS)
        self.btn_wa_all_side.clicked.connect(self.on_send_whatsapp_all)

        self.btn_new_import = QPushButton("Import")
        self.btn_new_import.setFixedHeight(34)
        self.btn_new_import.setStyleSheet(BTN_PRIMARY)
        self.btn_new_import.clicked.connect(lambda: self.switch_page(2))
        
        self.btn_clean_side = QPushButton("Clean")
        self.btn_clean_side.setFixedHeight(34)
        self.btn_clean_side.setStyleSheet(BTN_GHOST)
        self.btn_clean_side.setToolTip("Clear current invoice view")
        self.btn_clean_side.clicked.connect(self.reset_invoice_view)

        btns_layout.addWidget(self.btn_gen_all_side)
        btns_layout.addWidget(self.btn_wa_all_side)
        btns_layout.addWidget(self.btn_new_import)
        btns_layout.addWidget(self.btn_clean_side)
        sidebar_layout.addLayout(btns_layout)
        
        sidebar_layout.addSpacing(16)
        
        # Search Box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search customers...")
        self.search_input.setFixedHeight(42)
        self.search_input.setStyleSheet("""
            QLineEdit { 
                padding: 8px 14px; 
                border-radius: 10px; 
                border: 1px solid rgba(99, 102, 241, 0.25); 
                background: rgba(15, 23, 42, 0.8); 
                color: #e2e8f0; 
                font-size: 13px; 
            }
            QLineEdit:focus {
                border: 1px solid #6366f1;
                background: rgba(15, 23, 42, 1.0);
            }
        """)
        self.search_input.textChanged.connect(self.refresh_customer_list)
        sidebar_layout.addWidget(self.search_input)
        
        sidebar_layout.addSpacing(10)
        
        # Customer List Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        self.customer_list_container = QWidget()
        self.customer_list_container.setStyleSheet("background: transparent;")
        self.customer_list_layout = QVBoxLayout(self.customer_list_container)
        self.customer_list_layout.setAlignment(Qt.AlignTop)
        self.customer_list_layout.setSpacing(8)
        self.customer_list_layout.setContentsMargins(0, 5, 0, 0)
        
        self.scroll_area.setWidget(self.customer_list_container)
        sidebar_layout.addWidget(self.scroll_area)
        
        self.refresh_customer_list()

    def setup_invoice_view(self):
        self.invoice_view = QWidget()
        self.invoice_view.setStyleSheet("background: #0f172a;")
        invoice_layout = QVBoxLayout(self.invoice_view)
        invoice_layout.setContentsMargins(25, 20, 25, 20)
        invoice_layout.setSpacing(15)
        
        # ---- Top Bar ----
        top_bar = QHBoxLayout()
        
        # Customer name label
        self.lbl_active_customer = QLabel("Select a Customer")
        self.lbl_active_customer.setStyleSheet("""
            font-size: 26px; 
            font-weight: 800; 
            color: #e2e8f0;
            background: transparent;
        """)

        # Copy name button
        self.btn_copy_name = QPushButton("Copy")
        self.btn_copy_name.setFixedSize(52, 28)
        self.btn_copy_name.setCursor(Qt.PointingHandCursor)
        self.btn_copy_name.setToolTip("Copy customer name to clipboard")
        self.btn_copy_name.setStyleSheet("""
            QPushButton {
                background: rgba(99, 102, 241, 0.1);
                border: 1px solid rgba(99, 102, 241, 0.25);
                border-radius: 6px;
                color: #a5b4fc;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: rgba(99, 102, 241, 0.25);
                color: #e0e7ff;
                border-color: #6366f1;
            }
        """)
        self.btn_copy_name.clicked.connect(self._copy_customer_name)
        
        top_bar.addWidget(self.lbl_active_customer)
        top_bar.addSpacing(8)
        top_bar.addWidget(self.btn_copy_name)
        top_bar.addStretch()
        invoice_layout.addLayout(top_bar)
        
        # ---- Action Buttons Bar ----
        action_bar = QWidget()
        action_bar.setStyleSheet("""
            QWidget {
                background: rgba(30, 41, 59, 0.5); 
                border: 1px solid rgba(99, 102, 241, 0.15); 
                border-radius: 12px;
            }
        """)
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(16, 12, 16, 12)
        action_layout.setSpacing(10)
        
        self.btn_preview = QPushButton("Preview")
        self.btn_preview.setStyleSheet(BTN_GHOST)
        self.btn_preview.clicked.connect(self.on_preview)
        
        self.btn_pdf = QPushButton("Generate PDF")
        self.btn_pdf.setStyleSheet(BTN_PRIMARY)
        self.btn_pdf.clicked.connect(self.on_generate_pdf)
        
        self.btn_view = QPushButton("View Saved PDF")
        self.btn_view.setStyleSheet(BTN_GHOST)
        self.btn_view.clicked.connect(self.on_view_saved_pdf)
        
        self.btn_share_wa = QPushButton("Share WA")
        self.btn_share_wa.setStyleSheet(BTN_SHARE_WA)
        self.btn_share_wa.setToolTip("Generate PDF, copy to clipboard, and open WhatsApp chat")
        self.btn_share_wa.clicked.connect(self.on_share_whatsapp)

        self.btn_whatsapp = QPushButton("Send WA")
        self.btn_whatsapp.setStyleSheet(BTN_SUCCESS)
        self.btn_whatsapp.setToolTip("Auto-paste & send PDF via WhatsApp")
        self.btn_whatsapp.clicked.connect(self.on_send_whatsapp)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color: rgba(99, 102, 241, 0.2); background: transparent;")
        sep.setFixedWidth(2)
        
        self.btn_pdf_all = QPushButton("Gen All PDFs")
        self.btn_pdf_all.setStyleSheet(BTN_GHOST)
        self.btn_pdf_all.clicked.connect(self.on_generate_all)
        
        self.btn_whatsapp_all = QPushButton("WA All")
        self.btn_whatsapp_all.setStyleSheet(BTN_GHOST)
        self.btn_whatsapp_all.clicked.connect(self.on_send_whatsapp_all)
        
        self.btn_stop_wa = QPushButton("Stop")
        self.btn_stop_wa.setStyleSheet(BTN_DANGER)
        self.btn_stop_wa.setVisible(False)
        self.btn_stop_wa.clicked.connect(self.on_stop_whatsapp_all)

        self.btn_clean_main = QPushButton("Clean Table")
        self.btn_clean_main.setStyleSheet(BTN_GHOST)
        self.btn_clean_main.setToolTip("Clear the current display only (does NOT delete data)")
        self.btn_clean_main.clicked.connect(self.reset_invoice_view)
        
        action_layout.addWidget(self.btn_clean_main)
        action_layout.addWidget(self.btn_preview)
        action_layout.addWidget(self.btn_pdf)
        action_layout.addWidget(self.btn_view)
        action_layout.addWidget(self.btn_share_wa)
        action_layout.addWidget(self.btn_whatsapp)
        action_layout.addWidget(sep)
        action_layout.addWidget(self.btn_pdf_all)
        action_layout.addWidget(self.btn_whatsapp_all)
        action_layout.addWidget(self.btn_stop_wa)
        action_layout.addStretch()
        
        invoice_layout.addWidget(action_bar)
        
        # ---- Invoice Table ----
        self.table = QTableWidget(0, 3)
        self.table.verticalHeader().setDefaultSectionSize(50) # Increased height
        self.table.setHorizontalHeaderLabels(["Item Name", "Price", "Subtotal"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setStyleSheet("""
            QTableWidget { 
                background-color: rgba(15, 23, 42, 0.6);
                alternate-background-color: rgba(30, 41, 59, 0.4);
                color: #e2e8f0; 
                border: 1px solid rgba(99, 102, 241, 0.15);
                border-radius: 12px;
                font-size: 13px;
                gridline-color: transparent;
            }
            QTableWidget::item { 
                padding: 12px 14px; 
                border-bottom: 1px solid rgba(99, 102, 241, 0.08);
            }
            QTableWidget::item:selected {
                background-color: rgba(99, 102, 241, 0.2);
                color: #e0e7ff;
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
                letter-spacing: 1px;
            }
        """)
        invoice_layout.addWidget(self.table)
        
        # ---- Total Section ----
        total_bar = QWidget()
        total_bar.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(99, 102, 241, 0.1), stop:1 rgba(30, 41, 59, 0.5));
                border: 1px solid rgba(99, 102, 241, 0.2);
                border-radius: 12px;
            }
        """)
        total_layout = QHBoxLayout(total_bar)
        total_layout.setContentsMargins(20, 16, 20, 16)
        
        total_label = QLabel("Total Amount")
        total_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #94a3b8; background: transparent;")
        
        self.lbl_total = QLabel("$0.00")
        self.lbl_total.setStyleSheet("""
            font-size: 32px; 
            font-weight: 800; 
            color: #a5b4fc;
            background: transparent;
        """)
        
        total_layout.addWidget(total_label)
        total_layout.addStretch()
        total_layout.addWidget(self.lbl_total)
        
        invoice_layout.addWidget(total_bar)
        
        # ---- PDF Save Location Note ----
        pdf_note = QLabel(f"PDFs are saved to: {os.path.abspath(self.pdf_engine.output_dir)}")
        pdf_note.setStyleSheet("font-size: 11px; color: #64748b; padding-top: 4px; background: transparent;")
        pdf_note.setWordWrap(True)
        invoice_layout.addWidget(pdf_note)
        
        self.content_area.addWidget(self.invoice_view)

    def refresh_customer_list(self):
        self.sidebar.setUpdatesEnabled(False)
        # Clear existing
        while self.customer_list_layout.count():
            item = self.customer_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            
        search_term = self.search_input.text().strip()

        # If no session IDs and no search, show prompt
        if not self.current_session_invoice_ids and not search_term:
            empty_lbl = QLabel("Search for a customer or import data")
            empty_lbl.setStyleSheet("color: #64748b; font-style: italic; padding: 30px 10px; background: transparent;")
            empty_lbl.setAlignment(Qt.AlignCenter)
            self.customer_list_layout.addWidget(empty_lbl)
            self.sidebar.setUpdatesEnabled(True)
            return

        # Fetch based on session IDs if they exist and no search is active
        if self.current_session_invoice_ids and not search_term:
            customers = DataRepository.get_customers_summary_by_ids(self.current_session_invoice_ids)
        else:
            # If searching, we search all (or we could restrict to session, but usually search is global)
            customers = DataRepository.get_all_customers_summary(search_term if search_term else None)
        
        if not customers:
            empty_lbl = QLabel("No customers found")
            empty_lbl.setStyleSheet("color: #64748b; font-style: italic; padding: 30px 10px; background: transparent;")
            empty_lbl.setAlignment(Qt.AlignCenter)
            self.customer_list_layout.addWidget(empty_lbl)
            self.sidebar.setUpdatesEnabled(True)
            return

        for name, phone, item_count, total, status in customers:
            p_str = str(phone) if phone is not None else ""
            card = CustomerCard(name, item_count or 0, total or 0.0, p_str, status or "Draft")
            card.clicked.connect(self.on_customer_selected)
            card.sendWhatsAppRequested.connect(self.on_card_send_whatsapp)
            card.shareWhatsAppRequested.connect(self.on_card_share_whatsapp)
            card.copyBillRequested.connect(self.on_card_copy_bill)
            card.generatePdfRequested.connect(self.on_card_generate_pdf)
            card.deleteRequested.connect(self.on_card_delete)
            self.customer_list_layout.addWidget(card)
            
        self.sidebar.setUpdatesEnabled(True)

    def on_card_copy_bill(self, name, phone):
        """Handle Copy Bill button — copies full invoice text to clipboard silently."""
        if not phone or phone.strip() == "" or phone == "None":
            phone = DataRepository.find_phone_by_name(name)

        invoice, items = DataRepository.get_latest_invoice_by_details(name, phone)
        
        if not invoice:
            QMessageBox.warning(self, "No Invoice", f"No invoice found for <b>{name}</b>.")
            return

        # Build the full bill text with all item details using the dynamic template
        bill_text = self.whatsapp_bridge.get_invoice_message(
            customer_name=name,
            invoice_no=invoice[1],
            total_amount=invoice[2],
            items=items
        )

        QApplication.clipboard().setText(bill_text)
        # Show a brief, non-intrusive status bar message instead of a popup
        self.statusBar().showMessage(f"✓  Bill copied for {name} — press Ctrl+V to paste", 3500)

    def on_card_share_whatsapp(self, name, phone):
        """Handle Share WA button from the customer card in sidebar.
        Generates PDF, copies to clipboard, opens WhatsApp chat — user sends manually."""
        if not phone or phone.strip() == "" or phone == "None":
            phone = DataRepository.find_phone_by_name(name)
        
        if not phone:
            QMessageBox.warning(self, "No Phone Number", 
                f"No phone number found for <b>{name}</b>.<br><br>"
                "Please add it in the <b>Details</b> section first.")
            return

        invoice, items = DataRepository.get_latest_invoice_by_details(name, phone)
        
        if not invoice:
            QMessageBox.warning(self, "No Invoice", f"No invoice found for <b>{name}</b>.")
            return
        
        # Step 1: Ensure PDF exists (auto-generate if needed)
        pdf_path = invoice[5] if invoice and len(invoice) > 5 else None
        if not pdf_path or not os.path.exists(pdf_path):
            try:
                pdf_path = self.pdf_engine.generate(
                    customer_name=name,
                    invoice_number=invoice[1],
                    items=items,
                    total_amount=invoice[2]
                )
                DataRepository.update_invoice_pdf(invoice[0], pdf_path)
                self.refresh_customer_list()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to generate PDF: {str(e)}")
                return

        # Step 2: Copy PDF to clipboard
        try:
            mime_data = QMimeData()
            mime_data.setUrls([QUrl.fromLocalFile(os.path.abspath(pdf_path))])
            QApplication.clipboard().setMimeData(mime_data)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to copy PDF: {str(e)}")
            return

        # Step 3: Open WhatsApp chat with invoice message (no automation)
        try:
            self.whatsapp_bridge.send_with_message(
                phone=phone, customer_name=name,
                invoice_no=invoice[1], total_amount=invoice[2])
            DataRepository.update_invoice_status(invoice[0], "Sent")
            self.refresh_customer_list()
            
            QMessageBox.information(self, "Share WhatsApp",
                f"PDF generated and copied to clipboard for <b>{name}</b>.<br><br>"
                f"WhatsApp chat is now open.<br>"
                f"Just paste (Ctrl+V) and send!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open WhatsApp: {str(e)}")

    def on_card_send_whatsapp(self, name, phone):
        """Handle Send WhatsApp button from the customer card in sidebar.
        Sends the generated PDF — not text."""
        if not phone or phone.strip() == "" or phone == "None":
            phone = DataRepository.find_phone_by_name(name)
        
        if not phone:
            QMessageBox.warning(self, "No Phone Number", 
                f"No phone number found for <b>{name}</b>.<br><br>"
                "Please add it in the <b>Details</b> section first.")
            return

        invoice, items = DataRepository.get_latest_invoice_by_details(name, phone)
        
        if not invoice:
            QMessageBox.warning(self, "No Invoice", f"No invoice found for <b>{name}</b>.")
            return
        
        pdf_path = invoice[5] if invoice and len(invoice) > 5 else None
        
        if not pdf_path or not os.path.exists(pdf_path):
            # Auto-generate the PDF first
            reply = QMessageBox.question(self, "Generate PDF?", 
                f"No PDF found for <b>{name}</b>.<br><br>"
                "Would you like to generate it now?",
                QMessageBox.Yes | QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                try:
                    pdf_path = self.pdf_engine.generate(
                        customer_name=name,
                        invoice_number=invoice[1],
                        items=items,
                        total_amount=invoice[2]
                    )
                    DataRepository.update_invoice_pdf(invoice[0], pdf_path)
                    self.refresh_customer_list()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to generate PDF: {str(e)}")
                    return
            else:
                return

        try:
            # Copy PDF to Clipboard for pasting
            mime_data = QMimeData()
            mime_data.setUrls([QUrl.fromLocalFile(os.path.abspath(pdf_path))])
            QApplication.clipboard().setMimeData(mime_data)

            # Open WhatsApp chat with invoice message
            success = self.whatsapp_bridge.send_with_message(
                phone=phone, customer_name=name,
                invoice_no=invoice[1], total_amount=invoice[2]
            )
            
            if success:
                DataRepository.update_invoice_status(invoice[0], "Sent")
                # Automated Paste & Send for single card click
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("WhatsApp Automation")
                msg_box.setText(f"WhatsApp chat opened for <b>{name}</b>.<br><br>"
                                "Invoice PDF copied to clipboard.<br><br>"
                                "<b>Automation:</b> I will automatically paste (Ctrl+V) and send (Enter) in 5 seconds.<br>"
                                "DO NOT touch your keyboard or mouse.")
                msg_box.setIcon(QMessageBox.Information)
                msg_box.setStandardButtons(QMessageBox.Ok)
                msg_box.show()
                
                if pyautogui:
                    # Optimized: Reduced wait from 5s to 3s for faster flow
                    QTimer.singleShot(3000, lambda: self.automate_paste_and_send(is_batch=False))
                
                # Auto-close the message box after 3 seconds
                QTimer.singleShot(3000, msg_box.accept)
                
                self.refresh_customer_list()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open WhatsApp: {str(e)}")

    def on_card_generate_pdf(self, name, phone):
        """Handle Gen PDF button from the customer card in sidebar."""
        invoice, items = DataRepository.get_latest_invoice_by_details(name, phone)
        
        if not invoice:
            QMessageBox.warning(self, "No Invoice", f"No invoice found for <b>{name}</b>.")
            return

        try:
            pdf_path = self.pdf_engine.generate(
                customer_name=name,
                invoice_number=invoice[1],
                items=items,
                total_amount=invoice[2]
            )
            DataRepository.update_invoice_pdf(invoice[0], pdf_path)
            
            # Show a small non-blocking message or status change
            self.refresh_customer_list()
            QMessageBox.information(self, "Success", f"PDF generated for <b>{name}</b>.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate PDF: {str(e)}")

    def on_card_delete(self, name, phone):
        """Handle Delete button from the customer card in sidebar."""
        reply = QMessageBox.question(self, "Delete Contact?", 
            f"Are you sure you want to delete <b>{name}</b> and ALL their invoice history?<br><br>"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                DataRepository.delete_customer_by_details(name, phone)
                self.refresh_customer_list()
                if self.lbl_active_customer.text() == name:
                    self.lbl_active_customer.setText("Select a Customer")
                    self.table.setRowCount(0)
                    self.lbl_total.setText("$0.00")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete customer: {str(e)}")

    def on_customer_selected(self, name, phone):
        self.switch_page(1, reset_invoices=False) # Go to invoices but DON'T clear the view
        self.lbl_active_customer.setText(name)
        self.current_phone = phone

        # Show the invoice detail panel
        self.invoice_view.setVisible(True)
        
        invoice, items = DataRepository.get_latest_invoice_by_details(name, phone)
        
        if invoice:
            self.current_invoice_id = invoice[0]
            self.current_invoice_number = invoice[1]
            self.current_total = invoice[2]
            self.current_pdf_path = invoice[5] # Store existing PDF path
            
            self.lbl_total.setText(f"${self.current_total:,.2f}")
            
            self.table.setRowCount(0)
            for i, (desc, qty, price, sub) in enumerate(items):
                self.table.insertRow(i)
                self.table.setItem(i, 0, QTableWidgetItem(desc))
                self.table.setItem(i, 1, QTableWidgetItem(f"${price:.2f}"))
                self.table.setItem(i, 2, QTableWidgetItem(f"${sub:.2f}"))
            
            # Highlight the active card manually
            for i in range(self.customer_list_layout.count()):
                widget = self.customer_list_layout.itemAt(i).widget()
                if isinstance(widget, CustomerCard):
                    widget.set_active(widget.name == name)
        else:
            self.table.setRowCount(0)
            self.lbl_total.setText("$0.00")
            self.current_invoice_id = None
            self.current_pdf_path = None

    def _copy_customer_name(self):
        """Copy the active customer name to clipboard."""
        name = self.lbl_active_customer.text()
        if name and name != "Select a Customer":
            QApplication.clipboard().setText(name)
            self.statusBar().showMessage(f"Copied: {name}", 2000)

    def on_preview(self):
        if not self.current_invoice_id:
            QMessageBox.warning(self, "Error", "No invoice selected for preview.")
            return
        
        try:
            invoice, items = DataRepository.get_latest_invoice_by_details(
                self.lbl_active_customer.text(), self.current_phone)
            
            if not invoice:
                QMessageBox.warning(self, "Error", "Could not retrieve invoice details for preview.")
                return

            temp_pdf_path = self.pdf_engine.generate(
                customer_name=self.lbl_active_customer.text(),
                invoice_number=invoice[1],
                items=items,
                total_amount=invoice[2],
                is_preview=True
            )
            
            if temp_pdf_path and os.path.exists(temp_pdf_path):
                os.startfile(os.path.abspath(temp_pdf_path))
            else:
                QMessageBox.critical(self, "Error", "Failed to generate preview PDF.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to preview invoice: {str(e)}")

    def on_generate_pdf(self):
        if not self.current_invoice_id:
            QMessageBox.warning(self, "Error", "No invoice selected.")
            return
            
        try:
            invoice, items = DataRepository.get_latest_invoice_by_details(
                self.lbl_active_customer.text(), self.current_phone)
            
            if not invoice:
                QMessageBox.warning(self, "Error", "Could not find invoice records for this customer.")
                return

            pdf_path = self.pdf_engine.generate(
                customer_name=self.lbl_active_customer.text(),
                invoice_number=invoice[1],
                items=items,
                total_amount=invoice[2]
            )
            
            DataRepository.update_invoice_pdf(invoice[0], pdf_path)
            
            QMessageBox.information(self, "PDF Generated", 
                f"Invoice PDF generated successfully!<br><br>"
                f"Saved to:<br><code>{pdf_path}</code>")
            
            if os.path.exists(pdf_path):
                os.startfile(os.path.abspath(pdf_path))
            
            self.refresh_customer_list()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate PDF: {str(e)}")

    def on_view_saved_pdf(self):
        """Opens the already generated PDF for the current invoice."""
        if not self.current_invoice_id:
            QMessageBox.warning(self, "Error", "No customer selected.")
            return

        # Re-fetch latest to get fresh PDF path
        invoice, _ = DataRepository.get_latest_invoice_by_details(
            self.lbl_active_customer.text(), self.current_phone)
            
        if not invoice or not invoice[5]:
            QMessageBox.warning(self, "No PDF", "No PDF has been generated for this invoice yet.")
            return

        pdf_path = invoice[5]
        if os.path.exists(pdf_path):
            os.startfile(os.path.abspath(pdf_path))
        else:
            QMessageBox.critical(self, "File Not Found", f"The PDF file could not be found at:\n{pdf_path}")

    def on_share_whatsapp(self):
        """Share WhatsApp — manual flow for the currently selected invoice.
        Generates PDF, copies to clipboard, opens WhatsApp chat."""
        customer_name = self.lbl_active_customer.text()
        phone = self.current_phone
        
        if not self.current_invoice_id:
            QMessageBox.warning(self, "Error", "No invoice selected.")
            return

        if not phone or phone.strip() == "" or phone == "None":
            phone = DataRepository.find_phone_by_name(customer_name)
            self.current_phone = phone
            
        if not phone:
            QMessageBox.warning(self, "No Phone Number", 
                f"No phone number found for <b>{customer_name}</b>.<br><br>"
                "Please add it via the <b>Details</b> section.")
            return

        # Get PDF Path for this invoice
        invoice, items = DataRepository.get_latest_invoice_by_details(customer_name, phone)
        pdf_path = invoice[5] if invoice and len(invoice) > 5 else None

        # Auto-generate if no PDF exists
        if not pdf_path or not os.path.exists(pdf_path):
            try:
                pdf_path = self.pdf_engine.generate(
                    customer_name=customer_name,
                    invoice_number=invoice[1],
                    items=items,
                    total_amount=invoice[2]
                )
                DataRepository.update_invoice_pdf(invoice[0], pdf_path)
                self.refresh_customer_list()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to generate PDF: {str(e)}")
                return

        try:
            # Copy PDF to Clipboard
            mime_data = QMimeData()
            mime_data.setUrls([QUrl.fromLocalFile(os.path.abspath(pdf_path))])
            QApplication.clipboard().setMimeData(mime_data)

            # Open WhatsApp chat with invoice message (no automation)
            self.whatsapp_bridge.send_with_message(
                phone=phone, customer_name=customer_name,
                invoice_no=invoice[1], total_amount=invoice[2])
            DataRepository.update_invoice_status(self.current_invoice_id, "Sent")
            self.refresh_customer_list()
            
            QMessageBox.information(self, "Share WhatsApp",
                f"PDF generated and copied to clipboard for <b>{customer_name}</b>.<br><br>"
                f"WhatsApp chat is now open.<br>"
                f"Just paste (Ctrl+V) and send!")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to share via WhatsApp: {str(e)}")

    def on_send_whatsapp(self):
        """Send the generated PDF via WhatsApp for the currently selected invoice."""
        customer_name = self.lbl_active_customer.text()
        phone = self.current_phone
        
        if not self.current_invoice_id:
            QMessageBox.warning(self, "Error", "No invoice selected.")
            return

        # Find phone if missing
        if not phone or phone.strip() == "" or phone == "None":
            phone = DataRepository.find_phone_by_name(customer_name)
            self.current_phone = phone
            
        if not phone:
            QMessageBox.warning(self, "No Phone Number", 
                f"No phone number found for <b>{customer_name}</b>.<br><br>"
                "Please add it via the <b>Details</b> section.")
            return

        # Get PDF Path for this invoice
        invoice, items = DataRepository.get_latest_invoice_by_details(customer_name, phone)
        pdf_path = invoice[5] if invoice and len(invoice) > 5 else None

        if not pdf_path or not os.path.exists(pdf_path):
            # Auto-generate
            reply = QMessageBox.question(self, "Generate PDF First?", 
                "No PDF exists yet for this invoice.<br><br>"
                "Generate it now and send via WhatsApp?",
                QMessageBox.Yes | QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                try:
                    pdf_path = self.pdf_engine.generate(
                        customer_name=customer_name,
                        invoice_number=invoice[1],
                        items=items,
                        total_amount=invoice[2]
                    )
                    DataRepository.update_invoice_pdf(invoice[0], pdf_path)
                    self.refresh_customer_list()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to generate PDF: {str(e)}")
                    return
            else:
                return

        try:
            # Copy PDF to Clipboard
            mime_data = QMimeData()
            mime_data.setUrls([QUrl.fromLocalFile(os.path.abspath(pdf_path))])
            QApplication.clipboard().setMimeData(mime_data)

            # Open WhatsApp chat with invoice message
            success = self.whatsapp_bridge.send_with_message(
                phone=phone, customer_name=customer_name,
                invoice_no=invoice[1], total_amount=invoice[2]
            )
            
            if success:
                DataRepository.update_invoice_status(self.current_invoice_id, "Sent")
                # Automated Paste & Send for single button click
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("WhatsApp Automation")
                msg_box.setText(f"WhatsApp chat opened for <b>{customer_name}</b>.<br><br>"
                                "Invoice PDF copied to clipboard.<br><br>"
                                "<b>Automation:</b> I will automatically paste (Ctrl+V) and send (Enter) in 5 seconds.<br>"
                                "DO NOT touch your keyboard or mouse.")
                msg_box.setIcon(QMessageBox.Information)
                msg_box.setStandardButtons(QMessageBox.Ok)
                msg_box.show()

                if pyautogui:
                    # Optimized: Reduced wait from 5s to 3s
                    QTimer.singleShot(3000, lambda: self.automate_paste_and_send(is_batch=False))
                
                # Auto-close the message box after 3 seconds
                QTimer.singleShot(3000, msg_box.accept)
                
                self.refresh_customer_list()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open WhatsApp: {str(e)}")

    def on_generate_all(self):
        """Generate PDFs for invoices in the CURRENT session."""
        if not self.current_session_invoice_ids:
            # If no specific session, fall back to all pending? User says "only selected files".
            # Let's show a message.
            QMessageBox.warning(self, "No Active Session", "Please import some data first to generate invoices.")
            return

        pending = DataRepository.get_pending_invoices_by_ids(self.current_session_invoice_ids)
        if not pending:
            QMessageBox.information(self, "Gen All", "No pending invoices to generate. All done!")
            return
            
        count = 0
        for item in pending:
            inv = item['invoice']
            lines = item['items']
            
            pdf_path = self.pdf_engine.generate(
                customer_name=inv[4],
                invoice_number=inv[1],
                items=lines,
                total_amount=inv[2]
            )
            DataRepository.update_invoice_pdf(inv[0], pdf_path)
            count += 1
        
        save_dir = os.path.abspath(self.pdf_engine.output_dir)
        QMessageBox.information(self, "All PDFs Generated", 
            f"Generated <b>{count}</b> PDF invoices.<br><br>"
            f"All saved and logged to database.<br>"
            f"Location: <code>{save_dir}</code>")
        self.refresh_customer_list()

    def on_send_whatsapp_all(self):
        """Send invoices via WhatsApp for the CURRENT session."""
        if not self.current_session_invoice_ids:
            QMessageBox.warning(self, "No Active Session", "Please import some data first to send WhatsApp messages.")
            return
            
        self.send_queue = DataRepository.get_pending_invoices_by_ids(self.current_session_invoice_ids)
        
        if not self.send_queue:
            QMessageBox.information(self, "WA All", "No pending invoices to send. All done!")
            return

        msg = (f"This will open <b>{len(self.send_queue)}</b> WhatsApp chats.<br><br>"
               "<b>Missing PDFs will be generated automatically.</b><br><br>"
               "<b>DO NOT touch your keyboard/mouse during this process.</b><br>"
               "Each chat now gets ~3 seconds to load before auto-paste.<br><br>"
               "Click 'Stop' at any time to cancel.")
        
        reply = QMessageBox.question(self, "Start Automation?", msg, QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.wa_all_stopped = False
            self.btn_stop_wa.setVisible(True)
            self.btn_whatsapp_all.setEnabled(False)
            self.btn_wa_all_side.setEnabled(False) # Disable sidebar button too
            self.process_next_in_queue()

    def on_stop_whatsapp_all(self):
        """Stop the WA All automation."""
        self.wa_all_stopped = True
        self.send_queue = []
        self.btn_stop_wa.setVisible(False)
        self.btn_whatsapp_all.setEnabled(True)
        self.btn_wa_all_side.setEnabled(True) # Re-enable sidebar button
        QMessageBox.information(self, "Stopped", "WhatsApp automation has been stopped.")
        self.refresh_customer_list()

    def process_next_in_queue(self):
        if self.wa_all_stopped:
            return
        
        if not self.send_queue:
            self.btn_stop_wa.setVisible(False)
            self.btn_whatsapp_all.setEnabled(True)
            self.btn_wa_all_side.setEnabled(True)
            QMessageBox.information(self, "Complete", "All WhatsApp messages have been processed!")
            self.refresh_customer_list()
            return
            
        item = self.send_queue.pop(0)
        inv = item['invoice']
        lines = item['items']
        
        pdf_path = inv[6] # inv[6] is pdf_path in the get_all_pending_invoices SELECT
        
        # Auto-generate if missing
        if not pdf_path or not os.path.exists(pdf_path):
            try:
                pdf_path = self.pdf_engine.generate(
                    customer_name=inv[4],
                    invoice_number=inv[1],
                    items=lines,
                    total_amount=inv[2]
                )
                DataRepository.update_invoice_pdf(inv[0], pdf_path)
            except Exception as e:
                print(f"Error auto-generating PDF for {inv[4]}: {e}")
                QTimer.singleShot(100, self.process_next_in_queue)
                return

        # Copy PDF to clipboard
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile(os.path.abspath(pdf_path))])
        QApplication.clipboard().setMimeData(mime_data)
        
        # Open WhatsApp chat with invoice message
        self.whatsapp_bridge.send_with_message(
            phone=inv[5],
            customer_name=inv[4],
            invoice_no=inv[1],
            total_amount=inv[2]
        )
        
        # Mark as sent
        DataRepository.update_invoice_status(inv[0], "Sent")
        
        # Wait for browser and paste - Reduced wait to 2.5s for initial chat load
        if pyautogui:
            QTimer.singleShot(2500, lambda: self.automate_paste_and_send(is_batch=True))
        else:
            QTimer.singleShot(2000, self.process_next_in_queue)

    def automate_paste_and_send(self, is_batch=True):
        """Asynchronous automation to prevent UI lag."""
        if (is_batch and self.wa_all_stopped) or not pyautogui:
            return

        # We use a chain of QTimer calls to avoid time.sleep (which blocks the UI)
        def step1_paste():
            if is_batch and self.wa_all_stopped: return
            pyautogui.hotkey('ctrl', 'v')
            # Wait for PDF to load in WA (usually fast, 1s is plenty)
            QTimer.singleShot(1000, step2_enter)

        def step2_enter():
            if is_batch and self.wa_all_stopped: return
            pyautogui.press('enter')
            # Second enter handles the "Send" button in WA Desktop/Web
            QTimer.singleShot(500, step3_confirm_send)

        def step3_confirm_send():
            if is_batch and self.wa_all_stopped: return
            pyautogui.press('enter')
            
            # Step 4: After cooldown, move to next
            if is_batch:
                QTimer.singleShot(1500, self.process_next_in_queue)

        # Initial focus delay
        QTimer.singleShot(500, step1_paste)

    def on_dashboard_import_selected(self, invoice_ids):
        """Called when a user clicks an old import on the dashboard."""
        self.current_session_invoice_ids = invoice_ids
        self.search_input.clear()
        self.refresh_customer_list()
        self.switch_page(1, reset_invoices=False)

    def on_edit_import(self, import_id, file_name):
        """Open the Edit Import dialog for a specific import."""
        from src.ui.dialogs.edit_import_dialog import EditImportDialog
        dlg = EditImportDialog(self, import_id, file_name)
        dlg.import_updated.connect(self.dashboard_view.refresh_data)
        dlg.exec()

    def open_settings(self):
        """Open the App Settings / Customisation dialog."""
        dlg = SettingsDialog(self)
        dlg.exec_()
