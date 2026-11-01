"""
CarePlus Hospital - Helper Utilities
Contains helper functions for token formatting, unique code generation, and logging.
"""
import random
import string
from datetime import datetime
from app.db import execute_db
from flask import request

def generate_appointment_number():
    """Generates a human-friendly unique appointment identifier e.g. APT-2026-X89K."""
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    year = datetime.now().year
    return f"APT-{year}-{random_str}"

def generate_invoice_number():
    """Generates a unique invoice number e.g. INV-2026-9281."""
    random_str = ''.join(random.choices(string.digits, k=5))
    year = datetime.now().year
    return f"INV-{year}-{random_str}"

def format_currency(amount):
    """Formats decimal into standard currency string ($500.00)."""
    try:
        return f"${float(amount):,.2f}"
    except (ValueError, TypeError):
        return "$0.00"

def log_audit(user_id, action, details):
    """Logs system activity to the audit_logs table."""
    try:
        ip = request.remote_addr if request else '127.0.0.1'
        execute_db(
            "INSERT INTO audit_logs (user_id, action, details, ip_address) VALUES (%s, %s, %s, %s)",
            (user_id, action, details, ip)
        )
    except Exception as e:
        # Avoid crashing app if logging fails
        print(f"[Audit Log Warning] Failed to log action '{action}': {e}")
