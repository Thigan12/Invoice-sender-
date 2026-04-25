"""Template editor page for customizing invoice, PDF, and WhatsApp message content."""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QLineEdit, QTextEdit, QFrame, QScrollArea,
                               QDoubleSpinBox, QMessageBox, QSizePolicy)
from PySide6.QtCore import Qt
from src.core.template_data import get_template, save_template


class TemplateView(QWidget):
    """Page for editing invoice template — business info, payment, messages."""

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_template()

    def setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("background: #0f172a;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: #0f172a; }")

        content = QWidget()
        content.setStyleSheet("background: #0f172a;")

        main = QHBoxLayout(content)
        main.setContentsMargins(30, 30, 30, 30)
        main.setSpacing(24)

        # ── LEFT: Form Fields ──
        left = QVBoxLayout()
        left.setSpacing(16)

        # Header
        title = QLabel("Invoice Template")
        title.setStyleSheet("font-size: 32px; font-weight: 800; color: #f8fafc; background: transparent;")
        sub = QLabel("Customize your invoice, PDF, and WhatsApp message content.")
        sub.setStyleSheet("color: #94a3b8; font-size: 14px; background: transparent;")
        left.addWidget(title)
        left.addWidget(sub)
        left.addSpacing(8)

        # ── Section: Business Info ──
        left.addWidget(self._section_label("Business Information"))

        self.inp_business_name = self._add_field(left, "Business Name", "Your company or personal name")
        self.inp_business_phone = self._add_field(left, "Business Phone", "+65 89093836")
        self.inp_business_address = self._add_field(left, "Business Address (optional)", "Your business address")

        left.addSpacing(8)

        # ── Section: Payment ──
        left.addWidget(self._section_label("Payment Details"))

        self.inp_payment_method = self._add_field(left, "Payment Method", "PayNow / Bank Transfer / Cash")
        self.inp_payment_number = self._add_field(left, "Payment Number", "87610607")
        self.inp_payment_name = self._add_field(left, "Payment Account Name", "Watie")
        self.inp_receipt_contact = self._add_field(left, "Send Receipt To (Phone)", "+65 89093836")

        left.addSpacing(8)

        # ── Section: Delivery ──
        left.addWidget(self._section_label("Delivery"))

        fee_row = QHBoxLayout()
        fee_label = QLabel("Delivery Fee ($)")
        fee_label.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600; background: transparent;")
        self.inp_delivery_fee = QDoubleSpinBox()
        self.inp_delivery_fee.setRange(0, 9999)
        self.inp_delivery_fee.setDecimals(2)
        self.inp_delivery_fee.setValue(10.00)
        self.inp_delivery_fee.setFixedWidth(120)
        self.inp_delivery_fee.setStyleSheet("""
            QDoubleSpinBox {
                background: rgba(30, 41, 59, 0.8);
                border: 1px solid rgba(99, 102, 241, 0.2);
                border-radius: 8px;
                color: #e2e8f0;
                padding: 8px 12px;
                font-size: 13px;
            }
        """)
        self.inp_delivery_fee.valueChanged.connect(self._update_preview)
        fee_row.addWidget(fee_label)
        fee_row.addWidget(self.inp_delivery_fee)
        fee_row.addStretch()
        left.addLayout(fee_row)

        self.inp_self_collect = self._add_field(left, "Self-Collect / Prepaid Note",
            "If you have paid beforehand or are self-collecting, please deduct the ${fee} delivery fee...")

        left.addSpacing(8)

        # ── Section: Messages ──
        left.addWidget(self._section_label("Messages"))

        self.inp_closing = self._add_field(left, "Closing Message", "Thank you for your purchase!")
        self.inp_footer = self._add_field(left, "PDF Footer Text", "Software by Thigan Pvt Ltd")
        self.inp_enquiry = self._add_field(left, "Enquiry Line", "For any other enquiries, contact the same number.")

        left.addSpacing(16)

        # Save Button
        btn_row = QHBoxLayout()
        btn_save = QPushButton("Save Template")
        btn_save.setFixedSize(160, 44)
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #22c55e, stop:1 #16a34a);
                border: none; border-radius: 10px;
                color: white; font-weight: 700; font-size: 14px;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4ade80, stop:1 #22c55e); }
        """)
        btn_save.clicked.connect(self._save)

        btn_reset = QPushButton("Reset to Defaults")
        btn_reset.setFixedSize(160, 44)
        btn_reset.setCursor(Qt.PointingHandCursor)
        btn_reset.setStyleSheet("""
            QPushButton {
                background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.25);
                border-radius: 10px; color: #f87171; font-weight: 700; font-size: 13px;
            }
            QPushButton:hover { background: rgba(239, 68, 68, 0.2); color: white; }
        """)
        btn_reset.clicked.connect(self._reset)

        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_reset)
        btn_row.addStretch()
        left.addLayout(btn_row)
        left.addStretch()

        # ── RIGHT: Live WhatsApp Preview ──
        right = QVBoxLayout()
        right.setSpacing(12)

        preview_title = QLabel("WhatsApp Message Preview")
        preview_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #e2e8f0; background: transparent;")
        right.addWidget(preview_title)

        preview_frame = QFrame()
        preview_frame.setStyleSheet("""
            QFrame {
                background: #1a2332;
                border: 1px solid rgba(99, 102, 241, 0.15);
                border-radius: 14px;
            }
        """)
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(16, 16, 16, 16)

        # WhatsApp-style bubble
        self.preview_text = QLabel()
        self.preview_text.setWordWrap(True)
        self.preview_text.setStyleSheet("""
            QLabel {
                background: #0b5e3b;
                color: #e2e8f0;
                border-radius: 12px;
                padding: 16px;
                font-size: 12px;
                line-height: 1.5;
            }
        """)
        self.preview_text.setTextFormat(Qt.PlainText)
        preview_layout.addWidget(self.preview_text)
        preview_layout.addStretch()

        right.addWidget(preview_frame, 1)

        # PDF note
        pdf_note = QLabel("The same details are used in the PDF invoice.")
        pdf_note.setStyleSheet("color: #64748b; font-size: 11px; font-style: italic; background: transparent;")
        right.addWidget(pdf_note)

        # Layout
        left_widget = QWidget()
        left_widget.setLayout(left)
        left_widget.setStyleSheet("background: transparent;")

        right_widget = QWidget()
        right_widget.setLayout(right)
        right_widget.setFixedWidth(360)
        right_widget.setStyleSheet("background: transparent;")

        main.addWidget(left_widget, 1)
        main.addWidget(right_widget)

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _section_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("""
            font-size: 15px; font-weight: 700; color: #a5b4fc;
            padding-top: 4px; padding-bottom: 2px; background: transparent;
            border-bottom: 1px solid rgba(99, 102, 241, 0.15);
        """)
        return lbl

    def _add_field(self, layout, label_text, placeholder=""):
        lbl = QLabel(label_text)
        lbl.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600; background: transparent;")
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setFixedHeight(40)
        inp.setStyleSheet("""
            QLineEdit {
                background: rgba(30, 41, 59, 0.8);
                border: 1px solid rgba(99, 102, 241, 0.2);
                border-radius: 8px;
                color: #e2e8f0;
                padding: 0 14px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #6366f1;
                background: rgba(30, 41, 59, 1.0);
            }
        """)
        inp.textChanged.connect(self._update_preview)
        layout.addWidget(lbl)
        layout.addWidget(inp)
        return inp

    def load_template(self):
        """Load saved template into the form fields."""
        t = get_template()
        self.inp_business_name.setText(t.get("business_name", ""))
        self.inp_business_phone.setText(t.get("business_phone", ""))
        self.inp_business_address.setText(t.get("business_address", ""))
        self.inp_payment_method.setText(t.get("payment_method", ""))
        self.inp_payment_number.setText(t.get("payment_number", ""))
        self.inp_payment_name.setText(t.get("payment_name", ""))
        self.inp_receipt_contact.setText(t.get("receipt_contact", ""))
        self.inp_delivery_fee.setValue(float(t.get("delivery_fee", 10.0)))
        self.inp_self_collect.setText(t.get("self_collect_note", ""))
        self.inp_closing.setText(t.get("closing_message", ""))
        self.inp_footer.setText(t.get("footer_text", ""))
        self.inp_enquiry.setText(t.get("enquiry_text", ""))
        self._update_preview()

    def _get_form_data(self):
        return {
            "business_name": self.inp_business_name.text().strip(),
            "business_phone": self.inp_business_phone.text().strip(),
            "business_address": self.inp_business_address.text().strip(),
            "payment_method": self.inp_payment_method.text().strip(),
            "payment_number": self.inp_payment_number.text().strip(),
            "payment_name": self.inp_payment_name.text().strip(),
            "receipt_contact": self.inp_receipt_contact.text().strip(),
            "delivery_fee": self.inp_delivery_fee.value(),
            "self_collect_note": self.inp_self_collect.text().strip(),
            "closing_message": self.inp_closing.text().strip(),
            "footer_text": self.inp_footer.text().strip(),
            "enquiry_text": self.inp_enquiry.text().strip(),
        }

    def _update_preview(self):
        t = self._get_form_data()
        fee = t["delivery_fee"]
        note = t["self_collect_note"].replace("${fee}", f"${fee:.2f}")

        msg = (
            f"Hello [Customer Name],\n\n"
            f"Your invoice [INV-XXXXX] is ready.\n\n"
            f"Items:\n"
            f"  - Sample Item — $15.00\n"
            f"  - Another Item — $10.00\n\n"
            f"Subtotal: $25.00\n"
            f"Delivery Fee: ${fee:.2f}\n"
            f"Total Amount: ${25.00 + fee:.2f}\n\n"
        )
        if note:
            msg += f"NOTE: {note}\n\n"

        if t["payment_method"]:
            msg += f"*Payment via {t['payment_method']}:*\n"
        if t["payment_number"]:
            msg += f"{t['payment_method']} No: {t['payment_number']}\n"
        if t["payment_name"]:
            msg += f"Name: {t['payment_name']}\n\n"

        if t["receipt_contact"]:
            msg += f"After payment, please send the receipt to {t['receipt_contact']}\n"
        if t["enquiry_text"]:
            msg += f"{t['enquiry_text']}\n\n"
        if t["closing_message"]:
            msg += t["closing_message"]

        self.preview_text.setText(msg)

    def _save(self):
        data = self._get_form_data()
        save_template(data)
        QMessageBox.information(self, "Saved", "Template saved successfully!\n\nAll new invoices, PDFs, and WhatsApp messages will use these settings.")

    def _reset(self):
        from src.core.template_data import DEFAULT_TEMPLATE
        for key, val in DEFAULT_TEMPLATE.items():
            pass  # Will reload from defaults
        save_template(dict(DEFAULT_TEMPLATE))
        self.load_template()
        QMessageBox.information(self, "Reset", "Template reset to default values.")
