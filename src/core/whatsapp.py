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
        
        # Use whatsapp:// protocol for speed (if app is installed)
        # Fallback to https://api.whatsapp.com/send which is slightly faster than wa.me
        url = f"whatsapp://send?phone={clean_phone}"
        
        try:
            webbrowser.open(url)
        except:
            # Fallback if protocol fails
            fallback_url = f"https://api.whatsapp.com/send?phone={clean_phone}"
            webbrowser.open(fallback_url)
            
        return True

    def send_with_message(self, phone: str, customer_name: str, invoice_no: str, total_amount: float):
        """
        Opens WhatsApp chat with a pre-filled invoice message.
        PDF should already be copied to clipboard — user pastes after.
        """
        clean_phone = "".join(filter(str.isdigit, phone))
        
        delivery_fee = 10.00
        final_total = total_amount + delivery_fee
        
        message = (
            f"Hello {customer_name},\n\n"
            f"Your invoice {invoice_no} is ready.\n"
            f"Subtotal: ${total_amount:,.2f}\n"
            f"Delivery Fee: ${delivery_fee:,.2f}\n"
            f"Total Amount: ${final_total:,.2f}\n\n"
            f"_NOTE: If you have paid beforehand or are self-collecting, please deduct the $10.00 delivery fee from the total amount._\n\n"
            f"*Payment via PayNow:*\n"
            f"PayNow No: 87610607\n"
            f"Name: Watie\n\n"
            f"After payment, please send the receipt to +65 89093836\n"
            f"For any other enquiries, contact the same number.\n\n"
            f"Thank you for your purchase!"
        )
        encoded_message = urllib.parse.quote(message)
        
        # Use whatsapp:// protocol for speed
        url = f"whatsapp://send?phone={clean_phone}&text={encoded_message}"
        
        try:
            webbrowser.open(url)
        except:
            # Fallback
            fallback_url = f"https://api.whatsapp.com/send?phone={clean_phone}&text={encoded_message}"
            webbrowser.open(fallback_url)
            
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
