import webbrowser
import urllib.parse
import os
from src.core.template_data import get_template


class WhatsAppBridge:
    def __init__(self):
        pass

    def send_invoice_pdf(self, phone: str, customer_name: str):
        """Opens a WhatsApp chat with the customer so the user can paste the PDF."""
        clean_phone = "".join(filter(str.isdigit, phone))
        url = f"whatsapp://send?phone={clean_phone}"
        try:
            webbrowser.open(url)
        except:
            fallback_url = f"https://api.whatsapp.com/send?phone={clean_phone}"
            webbrowser.open(fallback_url)
        return True

    def get_invoice_message(self, customer_name: str, invoice_no: str, 
                            total_amount: float, items=None):
        """Builds the full invoice message string using the saved template."""
        t = get_template()

        delivery_fee = float(t.get("delivery_fee", 10.0))
        final_total = total_amount + delivery_fee

        # Build message from template
        msg = f"Hello {customer_name},\n\n"
        msg += f"Your invoice {invoice_no} is ready.\n"

        # Items list (if provided)
        if items:
            msg += "\nItems:\n"
            for desc, qty, price, subtotal in items:
                msg += f"  - {desc} — ${subtotal:.2f}\n"
            msg += "\n"

        msg += f"Subtotal: ${total_amount:,.2f}\n"
        msg += f"Delivery Fee: ${delivery_fee:,.2f}\n"
        msg += f"Total Amount: ${final_total:,.2f}\n\n"

        # Self-collect note
        note = t.get("self_collect_note", "").strip()
        if note:
            note = note.replace("${fee}", f"${delivery_fee:.2f}")
            msg += f"_NOTE: {note}_\n\n"

        # Payment info
        method = t.get("payment_method", "").strip()
        number = t.get("payment_number", "").strip()
        name = t.get("payment_name", "").strip()
        if method:
            msg += f"*Payment via {method}:*\n"
        if number:
            msg += f"{method} No: {number}\n"
        if name:
            msg += f"Name: {name}\n\n"

        # Receipt contact
        receipt = t.get("receipt_contact", "").strip()
        if receipt:
            msg += f"After payment, please send the receipt to {receipt}\n"

        # Enquiry
        enquiry = t.get("enquiry_text", "").strip()
        if enquiry:
            msg += f"{enquiry}\n\n"

        # Closing
        closing = t.get("closing_message", "").strip()
        if closing:
            msg += closing
        
        return msg

    def send_with_message(self, phone: str, customer_name: str, invoice_no: str, 
                          total_amount: float, items=None):
        """Opens WhatsApp chat with a pre-filled invoice message using the saved template."""
        clean_phone = "".join(filter(str.isdigit, phone))
        
        msg = self.get_invoice_message(customer_name, invoice_no, total_amount, items)

        encoded_message = urllib.parse.quote(msg)
        url = f"whatsapp://send?phone={clean_phone}&text={encoded_message}"

        try:
            webbrowser.open(url)
        except:
            fallback_url = f"https://api.whatsapp.com/send?phone={clean_phone}&text={encoded_message}"
            webbrowser.open(fallback_url)

        return True

    def send_invoice_message(self, phone: str, customer_name: str, total_amount: float, invoice_no: str):
        """Legacy method — kept for backward compatibility."""
        clean_phone = "".join(filter(str.isdigit, phone))
        message = f"Hi {customer_name}, please find your invoice {invoice_no} attached. Thank you!"
        encoded_message = urllib.parse.quote(message)
        url = f"https://wa.me/{clean_phone}?text={encoded_message}"
        webbrowser.open(url)
        return True
