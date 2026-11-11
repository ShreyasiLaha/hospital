"""
CarePlus Hospital - Administrator Blueprint Implementation
Provides executive analytics, staff & doctor CRUD, departments, doctor schedules, and CSV reports.
"""
import io
import csv
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, Response
from werkzeug.security import generate_password_hash
from app.db import query_db, execute_db
from app.utils.decorators import role_required
from app.utils.helpers import log_audit

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@role_required('admin')
def dashboard():
    """Executive administration dashboard with operational metrics, revenue, and audit trails."""
    today_str = datetime.now().strftime('%Y-%m-%d')

    # Metrics
    total_patients = query_db("SELECT COUNT(*) as cnt FROM patients", one=True)['cnt']
    active_doctors = query_db("SELECT COUNT(*) as cnt FROM doctors d JOIN users u ON d.user_id = u.id WHERE u.is_active = 1", one=True)['cnt']
    total_bookings = query_db("SELECT COUNT(*) as cnt FROM appointments", one=True)['cnt']
    
    rev_row = query_db("SELECT COALESCE(SUM(payable_amount), 0) as total FROM bills WHERE payment_status = 'PAID'", one=True)
    total_revenue = float(rev_row['total']) if rev_row else 0.0

    today_bookings = query_db("SELECT COUNT(*) as cnt FROM appointments WHERE appointment_date = %s", (today_str,), one=True)['cnt']

    # Status Breakdown
    confirmed_count = query_db("SELECT COUNT(*) as cnt FROM appointments WHERE status IN ('Confirmed', 'CONFIRMED')", one=True)['cnt']
    completed_count = query_db("SELECT COUNT(*) as cnt FROM appointments WHERE status IN ('Completed', 'COMPLETED')", one=True)['cnt']
    cancelled_count = query_db("SELECT COUNT(*) as cnt FROM appointments WHERE status IN ('Cancelled', 'CANCELLED')", one=True)['cnt']

    # Recent Activity Logs
    recent_logs = query_db("""
        SELECT l.*, u.full_name as user_name, u.role as user_role 
        FROM activity_logs l 
        LEFT JOIN users u ON l.user_id = u.id 
        ORDER BY l.created_at DESC 
        LIMIT 8
    """)

    # Department breakdown
    dept_stats = query_db("""
        SELECT dept.name, COUNT(DISTINCT d.id) as doctor_count, COUNT(DISTINCT a.id) as appt_count
        FROM departments dept
        LEFT JOIN doctors d ON dept.id = d.department_id
        LEFT JOIN appointments a ON dept.id = a.department_id
        GROUP BY dept.id, dept.name
        ORDER BY appt_count DESC
    """)

    return render_template('admin/dashboard.html',
                           total_patients=total_patients,
                           active_doctors=active_doctors,
                           total_bookings=total_bookings,
                           total_revenue=total_revenue,
                           today_bookings=today_bookings,
                           confirmed_count=confirmed_count,
                           completed_count=completed_count,
                           cancelled_count=cancelled_count,
                           recent_logs=recent_logs,
                           dept_stats=dept_stats)

@admin_bp.route('/manage-users', methods=['GET', 'POST'])
@role_required('admin')
def manage_users():
    """CRUD operations for hospital personnel (Doctors, Receptionists, Patients)."""
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        phone = request.form.get('phone', '').strip()
        role = request.form.get('role', '').strip()

        if not (full_name and email and password and phone and role):
            flash('Please complete all mandatory user fields.', 'warning')
            return redirect(url_for('admin.manage_users'))

        # Check existing user
        exists = query_db("SELECT id FROM users WHERE email = %s", (email,), one=True)
        if exists:
            flash(f"User with email '{email}' already exists.", 'danger')
            return redirect(url_for('admin.manage_users'))

        try:
            pw_hash = generate_password_hash(password)
            user_id = execute_db("""
                INSERT INTO users (full_name, email, password_hash, role, phone, is_active)
                VALUES (%s, %s, %s, %s, %s, 1)
            """, (full_name, email, pw_hash, role, phone))

            if role == 'doctor':
                dept_id = request.form.get('department_id')
                qual = request.form.get('qualification', 'MBBS, MD').strip()
                spec = request.form.get('specialization', 'General Specialist').strip()
                fee = float(request.form.get('consultation_fee', 500) or 500)
                room = request.form.get('room_number', 'OPD Room 1').strip()
                exp = int(request.form.get('experience_years', 3) or 3)
                bio = request.form.get('bio', '').strip()

                doc_id = execute_db("""
                    INSERT INTO doctors (user_id, department_id, qualification, specialization, consultation_fee, room_number, experience_years, bio)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (user_id, dept_id, qual, spec, fee, room, exp, bio))

                # Initialize default schedules (Mon, Wed, Fri 09:00 - 13:00)
                for day in ['Monday', 'Wednesday', 'Friday']:
                    execute_db("""
                        INSERT INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time, slot_duration_minutes, is_available)
                        VALUES (%s, %s, '09:00:00', '13:00:00', 30, 1)
                    """, (doc_id, day))

            elif role == 'receptionist':
                execute_db("""
                    INSERT INTO receptionists (user_id, desk_number, shift, qualification)
                    VALUES (%s, 'Front Desk - Main Wing A', 'Morning', 'Front Desk Operations')
                """, (user_id,))

            elif role == 'patient':
                execute_db("""
                    INSERT INTO patients (user_id, date_of_birth, gender, blood_group, address)
                    VALUES (%s, '1990-01-01', 'Other', 'O+', 'Registered via Administration')
                """, (user_id,))

            log_audit(session['user_id'], 'CREATE_USER', f"Created {role} account for {email}")
            flash(f"New {role.capitalize()} '{full_name}' created successfully!", 'success')
            return redirect(url_for('admin.manage_users'))

        except Exception as e:
            flash(f"Error creating user: {e}", 'danger')
            return redirect(url_for('admin.manage_users'))

    role_filter = request.args.get('role', '')
    sql = """
        SELECT u.*, d.specialization, dept.name as department_name, d.room_number, d.consultation_fee
        FROM users u
        LEFT JOIN doctors d ON u.id = d.user_id
        LEFT JOIN departments dept ON d.department_id = dept.id
        WHERE 1=1
    """
    params = []
    if role_filter:
        sql += " AND u.role = %s"
        params.append(role_filter)

    sql += " ORDER BY u.created_at DESC"
    users_list = query_db(sql, tuple(params))
    departments = query_db("SELECT id, name FROM departments WHERE is_active = 1 ORDER BY name ASC")

    return render_template('admin/manage_users.html', users=users_list, departments=departments, current_role=role_filter)

@admin_bp.route('/toggle-user-status/<int:user_id>', methods=['POST'])
@role_required('admin')
def toggle_user_status(user_id):
    """Activates or deactivates a user account."""
    if user_id == session.get('user_id'):
        flash("You cannot deactivate your own administrative account.", "warning")
        return redirect(url_for('admin.manage_users'))

    user = query_db("SELECT id, full_name, is_active FROM users WHERE id = %s", (user_id,), one=True)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('admin.manage_users'))

    new_status = 0 if user['is_active'] else 1
    execute_db("UPDATE users SET is_active = %s WHERE id = %s", (new_status, user_id))
    action_text = "activated" if new_status else "deactivated"
    log_audit(session['user_id'], 'TOGGLE_USER_STATUS', f"User {user['full_name']} was {action_text}.")
    flash(f"User '{user['full_name']}' has been {action_text}.", "info")
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/manage-departments', methods=['GET', 'POST'])
@role_required('admin')
def manage_departments():
    """Clinical departments and specialization categories management."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        icon_class = request.form.get('icon_class', 'bi-heart-pulse').strip()

        if not name:
            flash('Department name is mandatory.', 'warning')
            return redirect(url_for('admin.manage_departments'))

        exists = query_db("SELECT id FROM departments WHERE name = %s", (name,), one=True)
        if exists:
            flash(f"Department '{name}' already exists.", 'danger')
            return redirect(url_for('admin.manage_departments'))

        try:
            execute_db("""
                INSERT INTO departments (name, description, icon_class, is_active)
                VALUES (%s, %s, %s, 1)
            """, (name, description, icon_class))
            log_audit(session['user_id'], 'CREATE_DEPARTMENT', f"Created department '{name}'")
            flash(f"Department '{name}' created successfully!", 'success')
            return redirect(url_for('admin.manage_departments'))
        except Exception as e:
            flash(f"Error creating department: {e}", 'danger')

    departments = query_db("""
        SELECT dept.*, COUNT(d.id) as doctor_count
        FROM departments dept
        LEFT JOIN doctors d ON dept.id = d.department_id
        GROUP BY dept.id, dept.name, dept.description, dept.icon_class, dept.is_active, dept.created_at
        ORDER BY dept.name ASC
    """)

    return render_template('admin/manage_departments.html', departments=departments)

@admin_bp.route('/manage-schedules', methods=['GET', 'POST'])
@role_required('admin')
def manage_schedules():
    """Administrative roster overview and schedule editor."""
    doctor_filter = request.args.get('doctor_id', '')

    sql = """
        SELECT ds.*, u.full_name as doctor_name, d.specialization, d.room_number, dept.name as department_name
        FROM doctor_schedules ds
        JOIN doctors d ON ds.doctor_id = d.id
        JOIN users u ON d.user_id = u.id
        JOIN departments dept ON d.department_id = dept.id
        WHERE 1=1
    """
    params = []
    if doctor_filter:
        sql += " AND ds.doctor_id = %s"
        params.append(doctor_filter)

    sql += " ORDER BY u.full_name ASC, ds.id ASC"
    schedules = query_db(sql, tuple(params))
    doctors = query_db("SELECT d.id, u.full_name FROM doctors d JOIN users u ON d.user_id = u.id WHERE u.is_active = 1")

    return render_template('admin/manage_schedules.html', schedules=schedules, doctors=doctors, doctor_filter=doctor_filter)

@admin_bp.route('/reports')
@role_required('admin')
def reports():
    """Operational metrics, financial reporting, and downloadable report triggers."""
    monthly_rev = query_db("""
        SELECT strftime('%Y-%m', paid_at) as month, SUM(payable_amount) as total_rev, COUNT(*) as invoice_count
        FROM bills 
        WHERE payment_status = 'PAID' AND paid_at IS NOT NULL
        GROUP BY month
        ORDER BY month DESC
    """)

    dept_performance = query_db("""
        SELECT dept.name, COUNT(a.id) as total_appointments, COALESCE(SUM(b.payable_amount), 0) as total_revenue
        FROM departments dept
        LEFT JOIN appointments a ON dept.id = a.department_id
        LEFT JOIN bills b ON a.id = b.appointment_id AND b.payment_status = 'PAID'
        GROUP BY dept.id, dept.name
        ORDER BY total_revenue DESC
    """)

    return render_template('admin/reports.html', monthly_rev=monthly_rev, dept_performance=dept_performance)

@admin_bp.route('/export-appointments-csv')
@role_required('admin')
def export_appointments_csv():
    """Generates and downloads CSV export of all appointments."""
    appointments = query_db("""
        SELECT a.appointment_number, a.appointment_date, a.appointment_time, a.token_number, a.status, a.booked_by,
               u.full_name as patient_name, u.phone as patient_phone,
               doc_u.full_name as doctor_name, dept.name as department_name
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN users u ON p.user_id = u.id
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users doc_u ON d.user_id = doc_u.id
        JOIN departments dept ON a.department_id = dept.id
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
    """)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Appt Number', 'Date', 'Time', 'Token', 'Status', 'Booked By', 'Patient Name', 'Phone', 'Doctor', 'Department'])

    for row in appointments:
        writer.writerow([
            row['appointment_number'], row['appointment_date'], row['appointment_time'],
            row['token_number'], row['status'], row['booked_by'], row['patient_name'],
            row['patient_phone'], row['doctor_name'], row['department_name']
        ])

    csv_data = output.getvalue()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=careplus_appointments_report.csv"}
    )

@admin_bp.route('/export-revenue-csv')
@role_required('admin')
def export_revenue_csv():
    """Generates and downloads CSV export of billing invoices and payments."""
    bills = query_db("""
        SELECT b.invoice_number, a.appointment_number, b.consultation_fee, b.additional_charges, 
               b.discount, b.payable_amount, b.payment_status, b.payment_method, b.paid_at,
               u.full_name as patient_name, doc_u.full_name as doctor_name
        FROM bills b
        JOIN appointments a ON b.appointment_id = a.id
        JOIN patients p ON b.patient_id = p.id
        JOIN users u ON p.user_id = u.id
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users doc_u ON d.user_id = doc_u.id
        ORDER BY b.created_at DESC
    """)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Invoice Number', 'Appt Code', 'Patient Name', 'Doctor', 'Consultation Fee', 'Additional Charges', 'Discount', 'Payable Amount', 'Payment Status', 'Payment Method', 'Paid At'])

    for b in bills:
        writer.writerow([
            b['invoice_number'], b['appointment_number'], b['patient_name'], b['doctor_name'],
            f"{float(b['consultation_fee'] or 0.0):.2f}",
            f"{float(b['additional_charges'] or 0.0):.2f}",
            f"{float(b['discount'] or 0.0):.2f}",
            f"{float(b['payable_amount'] or 0.0):.2f}",
            b['payment_status'], b['payment_method'], b['paid_at'] or 'N/A'
        ])

    csv_data = output.getvalue()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=careplus_financial_statement.csv"}
    )
