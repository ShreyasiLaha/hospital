"""
CarePlus Hospital - Authentication & Role-Based Access Control (RBAC) Decorators
Protects routes against unauthenticated access and cross-role privilege escalation.
"""
from functools import wraps
from flask import session, flash, redirect, url_for, request

def login_required(f):
    """Ensures user is logged in before accessing protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    """
    Ensures the logged-in user belongs to one of the specified roles.
    Example: @role_required('admin') or @role_required('doctor', 'receptionist')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            user_role = session.get('role')
            if user_role not in allowed_roles:
                flash('Access denied: You do not have permission to view this resource.', 'danger')
                # Redirect user to their appropriate dashboard
                dashboard_map = {
                    'admin': 'admin.dashboard',
                    'doctor': 'doctor.dashboard',
                    'receptionist': 'receptionist.dashboard',
                    'patient': 'patient.dashboard'
                }
                return redirect(url_for(dashboard_map.get(user_role, 'auth.login')))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
