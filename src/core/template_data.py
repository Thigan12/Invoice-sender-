"""Template data management for invoice customization."""
from src.utils.paths import load_config, save_config

DEFAULT_TEMPLATE = {
    # Business Info
    "business_name": "Watie",
    "business_phone": "+65 89093836",
    "business_address": "",

    # Payment
    "payment_method": "PayNow",
    "payment_number": "87610607",
    "payment_name": "Watie",
    "receipt_contact": "+65 89093836",

    # Delivery
    "delivery_fee": 10.00,
    "self_collect_note": "If you have paid beforehand or are self-collecting, please deduct the ${fee} delivery fee from the total amount.",

    # Messages
    "closing_message": "Thank you for your purchase!",
    "footer_text": "Software by Thigan Pvt Ltd",
    "enquiry_text": "For any other enquiries, contact the same number.",
}


def get_template():
    """Load template from config, falling back to defaults."""
    config = load_config()
    saved = config.get("invoice_template", {})
    # Merge defaults with saved (saved overrides defaults)
    result = dict(DEFAULT_TEMPLATE)
    result.update(saved)
    return result


def save_template(template_data):
    """Save template data to config.json."""
    config = load_config()
    config["invoice_template"] = template_data
    save_config(config)
