"""
CarePlus Hospital - Authentication Blueprint Implementation
Handles unified login, patient registration, logout, and password updates with role redirection.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import query_db, execute_db
from app.utils.decorators import login_required
from app.utils.helpers import log_audit, generate_reset_token, verify_reset_token

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Unified login for all 4 roles."""
    if 'user_id' in session:
        role = session.get('role')
        dashboard_map = {
            'admin': 'admin.dashboard',
            'doctor': 'doctor.dashboard',
            'receptionist': 'receptionist.dashboard',
            'patient': 'patient.dashboard'
        }
        return redirect(url_for(dashboard_map.get(role, 'auth.login')))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash('Please enter both email and password.', 'warning')
            return render_template('auth/login.html')

        user = query_db("SELECT * FROM users WHERE email = %s", (email,), one=True)

        if user and check_password_hash(user['password_hash'], password):
            if not user.get('is_active', 1):
                flash('Your account has been deactivated. Please contact the administrator.', 'danger')
                return render_template('auth/login.html')

            # Populate session
            session.clear()
            session['user_id'] = user['id']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            session['email'] = user['email']

            # Attach specific profile IDs
            if user['role'] == 'patient':
                patient = query_db("SELECT id FROM patients WHERE user_id = %s", (user['id'],), one=True)
                if patient:
                    session['patient_id'] = patient['id']
            elif user['role'] == 'doctor':
                doctor = query_db("SELECT id FROM doctors WHERE user_id = %s", (user['id'],), one=True)
                if doctor:
                    session['doctor_id'] = doctor['id']

            log_audit(user['id'], 'LOGIN', f"User {user['email']} ({user['role']}) logged in.")
            flash(f"Welcome back, {user['full_name']}!", 'success')

            # Redirect according to role
            dashboard_map = {
                'admin': 'admin.dashboard',
                'doctor': 'doctor.dashboard',
                'receptionist': 'receptionist.dashboard',
                'patient': 'patient.dashboard'
            }
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for(dashboard_map.get(user['role'], 'index')))

        else:
            flash('Invalid email or password. Please verify your credentials.', 'danger')

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Allows public self-registration for new patients."""
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        phone = request.form.get('phone', '').strip()
        date_of_birth = request.form.get('date_of_birth', '').strip()
        gender = request.form.get('gender', '').strip()
        blood_group = request.form.get('blood_group', 'O+').strip()
        address = request.form.get('address', '').strip()
        emergency_contact_name = request.form.get('emergency_contact_name', '').strip()
        emergency_contact_phone = request.form.get('emergency_contact_phone', '').strip()
        medical_history = request.form.get('medical_history', '').strip()

        if not (full_name and email and password and phone and date_of_birth and gender and address):
            flash('Please fill in all mandatory fields.', 'warning')
            return render_template('auth/register.html')

        # Check existing email
        existing_user = query_db("SELECT id FROM users WHERE email = %s", (email,), one=True)
        if existing_user:
            flash('An account with this email already exists. Please sign in.', 'danger')
            return render_template('auth/register.html')

        try:
            pw_hash = generate_password_hash(password)
            user_id = execute_db(
                "INSERT INTO users (full_name, email, password_hash, role, phone) VALUES (%s, %s, %s, 'patient', %s)",
                (full_name, email, pw_hash, phone)
            )

            execute_db(
                """INSERT INTO patients (user_id, date_of_birth, gender, blood_group, address, 
                   emergency_contact_name, emergency_contact_phone, medical_history_summary) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (user_id, date_of_birth, gender, blood_group, address, 
                 emergency_contact_name, emergency_contact_phone, medical_history)
            )

            log_audit(user_id, 'REGISTER', f"New patient registration for {email}")
            flash('Registration successful! You can now log in with your credentials.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash(f'An error occurred during registration: {e}', 'danger')

    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Logs the user out and clears session state."""
    user_id = session.get('user_id')
    if user_id:
        log_audit(user_id, 'LOGOUT', 'User logged out.')
    session.clear()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Allows authenticated user to change their password."""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not current_password or not new_password or not confirm_password:
            flash('Please complete all password fields.', 'warning')
            return render_template('auth/change_password.html')

        if new_password != confirm_password:
            flash('New password and confirm password do not match.', 'danger')
            return render_template('auth/change_password.html')

        if len(new_password) < 6:
            flash('New password must be at least 6 characters.', 'warning')
            return render_template('auth/change_password.html')

        user = query_db("SELECT * FROM users WHERE id = %s", (session['user_id'],), one=True)
        if not user or not check_password_hash(user['password_hash'], current_password):
            flash('Your current password is incorrect.', 'danger')
            return render_template('auth/change_password.html')

        new_hash = generate_password_hash(new_password)
        execute_db("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, session['user_id']))
        log_audit(session['user_id'], 'CHANGE_PASSWORD', 'User updated password.')
        flash('Password successfully updated!', 'success')

        dashboard_map = {
            'admin': 'admin.dashboard',
            'doctor': 'doctor.dashboard',
            'receptionist': 'receptionist.dashboard',
            'patient': 'patient.dashboard'
        }
        return redirect(url_for(dashboard_map.get(session.get('role'), 'index')))

    return render_template('auth/change_password.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Generates password reset token and link for user recovery."""
    reset_link = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        if not email:
            flash('Please enter your registered email address.', 'warning')
            return render_template('auth/forgot_password.html')

        user = query_db("SELECT id, email, full_name, is_active FROM users WHERE email = %s", (email,), one=True)
        if not user:
            # Prevent email enumeration attacks by showing a generic message
            flash('If an active account exists with that email, a password reset link has been generated.', 'info')
            return render_template('auth/forgot_password.html')

        if not user.get('is_active', 1):
            flash('Your account has been deactivated. Please contact support.', 'danger')
            return render_template('auth/forgot_password.html')

        token = generate_reset_token(user['email'])
        reset_link = url_for('auth.reset_password', token=token, _external=True)
        log_audit(user['id'], 'FORGOT_PASSWORD_REQUEST', f"Password reset requested for {user['email']}")
        flash('Password reset link generated successfully! (Valid for 1 hour)', 'success')

    return render_template('auth/forgot_password.html', reset_link=reset_link)

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Verifies token and sets a new password."""
    email = verify_reset_token(token, max_age_seconds=3600)
    if not email:
        flash('The password reset link is invalid or has expired. Please request a new one.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    user = query_db("SELECT id, email, full_name FROM users WHERE email = %s", (email,), one=True)
    if not user:
        flash('User account not found.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not new_password or not confirm_password:
            flash('Please enter and confirm your new password.', 'warning')
            return render_template('auth/reset_password.html', token=token, email=email)

        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html', token=token, email=email)

        if len(new_password) < 6:
            flash('Password must be at least 6 characters.', 'warning')
            return render_template('auth/reset_password.html', token=token, email=email)

        new_hash = generate_password_hash(new_password)
        execute_db("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, user['id']))
        log_audit(user['id'], 'RESET_PASSWORD_SUCCESS', f"Password reset successfully for {email}")
        flash('Your password has been successfully reset! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token, email=email)

