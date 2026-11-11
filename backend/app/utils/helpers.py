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

def format_time_hhmm(val):
    """Formats datetime, timedelta, time, or string time into normalized HH:MM."""
    if not val:
        return "09:00"
    if hasattr(val, 'total_seconds'):  # datetime.timedelta
        total_sec = int(val.total_seconds())
        h = (total_sec // 3600) % 24
        m = (total_sec % 3600) // 60
        return f"{h:02d}:{m:02d}"
    if hasattr(val, 'strftime'):  # datetime.datetime or datetime.time
        return val.strftime('%H:%M')
    val_str = str(val).strip()
    parts = val_str.split(':')
    if len(parts) >= 2:
        try:
            return f"{int(parts[0]):02d}:{int(parts[1]):02d}"
        except ValueError:
            pass
    return val_str[:5]

def log_audit(user_id, action, details):
    """Logs system activity to the activity_logs table."""
    try:
        ip = request.remote_addr if request else '127.0.0.1'
        execute_db(
            "INSERT INTO activity_logs (user_id, action, details, ip_address) VALUES (%s, %s, %s, %s)",
            (user_id, action, details, ip)
        )
    except Exception as e:
        # Avoid crashing app if logging fails
        print(f"[Activity Log Warning] Failed to log action '{action}': {e}")

def create_notification(user_id, title, message, notif_type='APPOINTMENT'):
    """Creates an in-app alert in the notifications table for a user."""
    try:
        execute_db(
            "INSERT INTO notifications (user_id, title, message, type, is_read) VALUES (%s, %s, %s, %s, 0)",
            (user_id, title, message, notif_type)
        )
    except Exception as e:
        print(f"[Notification Warning] Failed to send notification to user {user_id}: {e}")

