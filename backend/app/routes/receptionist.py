"""
CarePlus Hospital - Receptionist Desk Blueprint Implementation
Handles walk-in registrations, patient check-ins, queue management, and cashier billing.
"""
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
from app.db import query_db, execute_db
from app.utils.decorators import role_required
from app.utils.helpers import generate_appointment_number, generate_invoice_number, log_audit

receptionist_bp = Blueprint('receptionist', __name__, url_prefix='/receptionist')

@receptionist_bp.route('/dashboard')
@role_required('receptionist')
def dashboard():
    """Front desk summary showing today's arrivals, lounge queue, and cashier collections."""
    today_str = datetime.now().strftime('%Y-%m-%d')
    today_day = datetime.now().strftime('%A')

    # Metrics
    checkins_count = query_db("""
        SELECT COUNT(*) as cnt FROM appointments 
        WHERE appointment_date = %s AND status != 'CANCELLED'
    """, (today_str,), one=True)['cnt']

    waiting_lounge_count = query_db("""
        SELECT COUNT(*) as cnt FROM appointments 
        WHERE appointment_date = %s AND status = 'CONFIRMED'
    """, (today_str,), one=True)['cnt']

    active_doctors_count = query_db("""
        SELECT COUNT(DISTINCT doctor_id) as cnt FROM doctor_schedules 
        WHERE day_of_week = %s AND is_available = 1
    """, (today_day,), one=True)['cnt']

    # Total cashier collections
    collections_row = query_db("""
        SELECT COALESCE(SUM(payable_amount), 0) as total FROM bills 
        WHERE payment_status = 'PAID'
    """, one=True)
    today_collections = float(collections_row['total']) if collections_row else 0.0

    # Live Waiting Queue
    live_queue = query_db("""
        SELECT a.*, u.full_name as patient_name, u.phone as patient_phone, 
               doc_u.full_name as doctor_name, dept.name as department_name,
               b.id as bill_id, b.payment_status as bill_payment_status, b.payable_amount as bill_amount
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN users u ON p.user_id = u.id
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users doc_u ON d.user_id = doc_u.id
        JOIN departments dept ON a.department_id = dept.id
        LEFT JOIN bills b ON a.id = b.appointment_id
        WHERE a.appointment_date = %s AND a.status != 'CANCELLED'
        ORDER BY a.token_number ASC
    """, (today_str,))

    return render_template('receptionist/dashboard.html',
                           checkins_count=checkins_count,
                           waiting_lounge_count=waiting_lounge_count,
                           active_doctors_count=active_doctors_count,
                           today_collections=today_collections,
                           live_queue=live_queue)

@receptionist_bp.route('/walkin-booking', methods=['GET', 'POST'])
@role_required('receptionist')
def walkin_booking():
    """Rapid booking interface for walk-in patients arriving at the clinic."""
    today_str = datetime.now().strftime('%Y-%m-%d')
    current_time_str = datetime.now().strftime('%H:%M')

    if request.method == 'POST':
        patient_name = request.form.get('patient_name', '').strip()
        phone = request.form.get('phone', '').strip()
        gender = request.form.get('gender', 'Male').strip()
        dob = request.form.get('dob', '1990-01-01').strip()
        blood_group = request.form.get('blood_group', 'O+').strip()
        department_id = request.form.get('department_id')
        doctor_id = request.form.get('doctor_id')
        symptoms = request.form.get('symptoms', 'Walk-in consultation').strip()

        if not (patient_name and phone and department_id and doctor_id):
            flash('Please complete all required fields.', 'warning')
            return redirect(url_for('receptionist.walkin_booking'))

        try:
            # 1. Lookup or create patient
            patient_user = query_db("SELECT id FROM users WHERE phone = %s", (phone,), one=True)
            if patient_user:
                user_id = patient_user['id']
                patient_rec = query_db("SELECT id FROM patients WHERE user_id = %s", (user_id,), one=True)
                patient_id = patient_rec['id'] if patient_rec else None
            else:
                # Auto-generate temporary patient account
                temp_email = f"walkin_{phone.replace(' ', '').replace('+', '')}@careplus.com"
                pw_hash = generate_password_hash("Careplus@123")
                user_id = execute_db("""
                    INSERT INTO users (full_name, email, password_hash, role, phone) 
                    VALUES (%s, %s, %s, 'patient', %s)
                """, (patient_name, temp_email, pw_hash, phone))

                patient_id = execute_db("""
                    INSERT INTO patients (user_id, date_of_birth, gender, blood_group, address) 
                    VALUES (%s, %s, %s, %s, 'Walk-in Patient (Front Desk)')
                """, (user_id, dob, gender, blood_group))

            # 2. Next token number for doctor today
            token_row = query_db("""
                SELECT COALESCE(MAX(token_number), 0) + 1 as next_token 
                FROM appointments 
                WHERE doctor_id = %s AND appointment_date = %s
            """, (doctor_id, today_str), one=True)
            token_number = token_row['next_token'] if token_row else 1

            # 3. Create appointment (marked CONFIRMED right away)
            appt_num = generate_appointment_number()
            invoice_num = generate_invoice_number()

            doctor = query_db("SELECT consultation_fee FROM doctors WHERE id = %s", (doctor_id,), one=True)
            fee = float(doctor['consultation_fee']) if doctor else 500.00

            appt_id = execute_db("""
                INSERT INTO appointments (
                    appointment_number, patient_id, doctor_id, department_id, 
                    appointment_date, appointment_time, token_number, status, symptoms, booked_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'CONFIRMED', %s, 'RECEPTIONIST')
            """, (appt_num, patient_id, doctor_id, department_id, today_str, current_time_str, token_number, symptoms))

            # 4. Create Bill
            execute_db("""
                INSERT INTO bills (
                    invoice_number, appointment_id, patient_id, consultation_fee, 
                    additional_charges, total_amount, discount, payable_amount, payment_status, payment_method, generated_by_user_id
                ) VALUES (%s, %s, %s, %s, 0.00, %s, 0.00, %s, 'UNPAID', 'CASH', %s)
            """, (invoice_num, appt_id, patient_id, fee, fee, fee, session.get('user_id')))

            log_audit(session['user_id'], 'WALKIN_BOOKING', f"Walk-in appointment {appt_num} issued Token #{token_number}")
            flash(f"Walk-in patient {patient_name} registered successfully! Assigned Token #{token_number:02d} ({appt_num}).", 'success')
            return redirect(url_for('receptionist.queue'))

        except Exception as e:
            flash(f"Error registering walk-in booking: {e}", 'danger')
            return redirect(url_for('receptionist.walkin_booking'))

    departments = query_db("SELECT id, name FROM departments WHERE is_active = 1 ORDER BY name ASC")
    doctors = query_db("""
        SELECT d.id, u.full_name, d.specialization, dept.name as department_name, d.consultation_fee 
        FROM doctors d
        JOIN users u ON d.user_id = u.id
        JOIN departments dept ON d.department_id = dept.id
        WHERE u.is_active = 1
        ORDER BY dept.name ASC, u.full_name ASC
    """)

    return render_template('receptionist/walkin_booking.html', departments=departments, doctors=doctors)

@receptionist_bp.route('/queue')
@role_required('receptionist')
def queue():
    """Live patient check-in queue desk with status transitions."""
    today_str = datetime.now().strftime('%Y-%m-%d')
    doctor_filter = request.args.get('doctor_id', '')

    sql = """
        SELECT a.*, u.full_name as patient_name, u.phone as patient_phone, 
               p.gender, p.blood_group,
               doc_u.full_name as doctor_name, dept.name as department_name,
               b.id as bill_id, b.payment_status as bill_payment_status, b.payable_amount as bill_amount
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN users u ON p.user_id = u.id
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users doc_u ON d.user_id = doc_u.id
        JOIN departments dept ON a.department_id = dept.id
        LEFT JOIN bills b ON a.id = b.appointment_id
        WHERE a.appointment_date = %s
    """
    params = [today_str]
    if doctor_filter:
        sql += " AND a.doctor_id = %s"
        params.append(doctor_filter)

    sql += " ORDER BY a.token_number ASC"
    appointments = query_db(sql, tuple(params))

    doctors = query_db("SELECT d.id, u.full_name FROM doctors d JOIN users u ON d.user_id = u.id WHERE u.is_active = 1")
    return render_template('receptionist/queue.html', appointments=appointments, doctors=doctors, doctor_filter=doctor_filter)

@receptionist_bp.route('/check-in/<int:appointment_id>', methods=['POST'])
@role_required('receptionist')
def check_in(appointment_id):
    """Marks patient as checked-in."""
    execute_db("UPDATE appointments SET status = 'CONFIRMED' WHERE id = %s", (appointment_id,))
    flash('Patient checked-in successfully and added to doctor queue.', 'success')
    return redirect(url_for('receptionist.queue'))

@receptionist_bp.route('/billing', methods=['GET', 'POST'])
@role_required('receptionist')
def billing():
    """Cashier interface for calculating fees, discounts, and recording payments."""
    if request.method == 'POST':
        bill_id = request.form.get('bill_id')
        consultation_fee = float(request.form.get('consultation_fee', 0) or 0)
        additional_charges = float(request.form.get('additional_charges', 0) or 0)
        discount = float(request.form.get('discount', 0) or 0)
        payment_method = request.form.get('payment_method', 'CASH')

        total = consultation_fee + additional_charges
        payable = max(0.0, total - discount)

        try:
            execute_db("""
                UPDATE bills 
                SET consultation_fee = %s, additional_charges = %s, discount = %s, 
                    total_amount = %s, payable_amount = %s, payment_status = 'PAID', 
                    payment_method = %s, paid_at = CURRENT_TIMESTAMP, generated_by_user_id = %s
                WHERE id = %s
            """, (consultation_fee, additional_charges, discount, total, payable, payment_method, session['user_id'], bill_id))

            bill = query_db("SELECT invoice_number FROM bills WHERE id = %s", (bill_id,), one=True)
            inv_code = bill['invoice_number'] if bill else ''
            log_audit(session['user_id'], 'COLLECT_PAYMENT', f"Collected payment of ${payable:.2f} for Invoice {inv_code}")
            flash(f"Payment of ${payable:.2f} recorded successfully for {inv_code} via {payment_method}!", 'success')
            return redirect(url_for('receptionist.billing'))
        except Exception as e:
            flash(f"Error processing payment: {e}", 'danger')

    # Query unpaid and recent bills
    unpaid_bills = query_db("""
        SELECT b.*, a.appointment_number, a.token_number, u.full_name as patient_name, u.phone as patient_phone,
               doc_u.full_name as doctor_name, dept.name as department_name
        FROM bills b
        JOIN appointments a ON b.appointment_id = a.id
        JOIN patients p ON b.patient_id = p.id
        JOIN users u ON p.user_id = u.id
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users doc_u ON d.user_id = doc_u.id
        JOIN departments dept ON a.department_id = dept.id
        WHERE b.payment_status = 'UNPAID'
        ORDER BY b.created_at DESC
    """)

    recent_paid_bills = query_db("""
        SELECT b.*, u.full_name as patient_name, doc_u.full_name as doctor_name
        FROM bills b
        JOIN patients p ON b.patient_id = p.id
        JOIN users u ON p.user_id = u.id
        JOIN appointments a ON b.appointment_id = a.id
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users doc_u ON d.user_id = doc_u.id
        WHERE b.payment_status = 'PAID'
        ORDER BY b.paid_at DESC
        LIMIT 10
    """)

    return render_template('receptionist/billing.html', unpaid_bills=unpaid_bills, recent_paid_bills=recent_paid_bills)
