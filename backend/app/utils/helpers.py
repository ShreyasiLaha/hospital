"""
CarePlus Hospital - Helper Utilities
Contains helper functions for token formatting, unique code generation, and logging.
"""
import random
import string
import math
import re
from datetime import datetime
from app.db import execute_db, query_db
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

def paginate_query(base_query, count_query, params=(), page=1, per_page=10):
    """
    Executes a paginated query returning items and pagination metadata.
    """
    try:
        page_num = max(1, int(page or 1))
    except (ValueError, TypeError):
        page_num = 1

    try:
        limit = max(1, min(100, int(per_page or 10)))
    except (ValueError, TypeError):
        limit = 10

    total_row = query_db(count_query, params, one=True)
    total_count = total_row['cnt'] if total_row and 'cnt' in total_row else 0
    total_pages = max(1, math.ceil(total_count / limit))
    if page_num > total_pages and total_count > 0:
        page_num = total_pages

    offset = (page_num - 1) * limit
    paginated_sql = f"{base_query} LIMIT {limit} OFFSET {offset}"
    items = query_db(paginated_sql, params)

    return {
        'items': items,
        'page': page_num,
        'per_page': limit,
        'total_count': total_count,
        'total_pages': total_pages,
        'has_prev': page_num > 1,
        'has_next': page_num < total_pages,
        'prev_page': page_num - 1 if page_num > 1 else None,
        'next_page': page_num + 1 if page_num < total_pages else None
    }

def generate_reset_token(email):
    """Generates a cryptographically secure, time-limited password reset token."""
    from itsdangerous import URLSafeTimedSerializer
    try:
        from flask import current_app
        secret_key = current_app.config.get('SECRET_KEY', 'careplus_hospital_super_secret_key_2026')
    except Exception:
        secret_key = 'careplus_hospital_super_secret_key_2026'
    serializer = URLSafeTimedSerializer(secret_key)
    return serializer.dumps(email, salt='careplus-password-reset-salt')

def verify_reset_token(token, max_age_seconds=3600):
    """
    Verifies a password reset token.
    Returns the associated email if valid and not expired, else None.
    """
    from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
    try:
        from flask import current_app
        secret_key = current_app.config.get('SECRET_KEY', 'careplus_hospital_super_secret_key_2026')
    except Exception:
        secret_key = 'careplus_hospital_super_secret_key_2026'
    serializer = URLSafeTimedSerializer(secret_key)
    try:
        email = serializer.loads(token, salt='careplus-password-reset-salt', max_age=max_age_seconds)
        return email
    except (BadSignature, SignatureExpired, Exception):
        return None

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

def validate_email_format(email):
    """Validates email format using standard regex."""
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))

def validate_phone_format(phone):
    """Checks that phone contains at least 7 digits."""
    if not phone or not isinstance(phone, str):
        return False
    digits = re.sub(r'\D', '', phone)
    return len(digits) >= 7

def validate_positive_amount(val, default=0.0):
    """Safely parses float and guarantees non-negative number."""
    try:
        f = float(val)
        return max(0.0, f)
    except (ValueError, TypeError):
        return max(0.0, float(default))




