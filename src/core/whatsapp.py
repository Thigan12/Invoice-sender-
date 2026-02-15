import webbrowser
import urllib.parse
import os

class WhatsAppBridge:
    def __init__(self):
        pass

    def send_invoice_pdf(self, phone: str, customer_name: str):
        """
        Opens a WhatsApp chat with the customer so the user can paste the PDF.
        The PDF is copied to clipboard before calling this — user just Ctrl+V's.
        No text message is pre-filled — the PDF IS the invoice.
        """
        # Standardize phone number: keep only digits
        clean_phone = "".join(filter(str.isdigit, phone))
        
        # Open WhatsApp chat with the customer (no pre-filled text)
        url = f"https://wa.me/{clean_phone}"
        
        webbrowser.open(url)
        return True

    def send_invoice_message(self, phone: str, customer_name: str, total_amount: float, invoice_no: str):
        """
        Legacy method — kept for backward compatibility.
        Opens WhatsApp with a short message. PDF should already be copied to clipboard.
        """
        clean_phone = "".join(filter(str.isdigit, phone))
        
        # Short message informing about the attached invoice
        message = f"Hi {customer_name}, please find your invoice {invoice_no} attached. Thank you!"
        encoded_message = urllib.parse.quote(message)
        
        url = f"https://wa.me/{clean_phone}?text={encoded_message}"
        
        webbrowser.open(url)
        return True
