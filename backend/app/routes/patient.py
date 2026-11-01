"""
CarePlus Hospital - Patient Portal Blueprint Implementation
Handles appointment booking, cancellation, prescription views, and billing statements.
"""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.db import query_db, execute_db
from app.utils.decorators import role_required
from app.utils.helpers import generate_appointment_number, generate_invoice_number, log_audit

patient_bp = Blueprint('patient', __name__, url_prefix='/patient')

def get_current_patient_id():
    """Helper to retrieve or verify patient ID associated with the logged-in user."""
    if 'patient_id' in session:
        return session['patient_id']
    patient = query_db("SELECT id FROM patients WHERE user_id = %s", (session['user_id'],), one=True)
    if patient:
        session['patient_id'] = patient['id']
        return patient['id']
    return None

@patient_bp.route('/dashboard')
@role_required('patient')
def dashboard():
    """Patient summary dashboard with upcoming appointments and metrics."""
    patient_id = get_current_patient_id()
    today_str = datetime.now().strftime('%Y-%m-%d')

    # 1. Metrics counters
    upcoming_count = query_db("""
        SELECT COUNT(*) as cnt FROM appointments 
        WHERE patient_id = %s AND status IN ('PENDING', 'CONFIRMED') AND appointment_date >= %s
    """, (patient_id, today_str), one=True)['cnt']

    completed_count = query_db("""
        SELECT COUNT(*) as cnt FROM appointments 
        WHERE patient_id = %s AND status = 'COMPLETED'
    """, (patient_id,), one=True)['cnt']

    prescription_count = query_db("""
        SELECT COUNT(*) as cnt FROM prescriptions 
        WHERE patient_id = %s
    """, (patient_id,), one=True)['cnt']

    unpaid_bills_count = query_db("""
        SELECT COUNT(*) as cnt FROM bills 
        WHERE patient_id = %s AND payment_status = 'UNPAID'
    """, (patient_id,), one=True)['cnt']

    # 2. Next Upcoming Appointment
    next_appointment = query_db("""
        SELECT a.*, u.full_name as doctor_name, d.specialization, d.room_number, dept.name as department_name
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users u ON d.user_id = u.id
        JOIN departments dept ON a.department_id = dept.id
        WHERE a.patient_id = %s AND a.status IN ('PENDING', 'CONFIRMED') AND a.appointment_date >= %s
        ORDER BY a.appointment_date ASC, a.appointment_time ASC
        LIMIT 1
    """, (patient_id, today_str), one=True)

    return render_template('patient/dashboard.html',
                           upcoming_count=upcoming_count,
                           completed_count=completed_count,
                           prescription_count=prescription_count,
                           unpaid_bills_count=unpaid_bills_count,
                           next_appointment=next_appointment)

@patient_bp.route('/book-appointment', methods=['GET', 'POST'])
@role_required('patient')
def book_appointment():
    """Handles appointment booking flow with dynamic slot selection."""
    patient_id = get_current_patient_id()

    if request.method == 'POST':
        department_id = request.form.get('department_id')
        doctor_id = request.form.get('doctor_id')
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')
        symptoms = request.form.get('symptoms', '').strip()

        if not (department_id and doctor_id and appointment_date and appointment_time):
            flash('Please select department, doctor, date, and an available time slot.', 'warning')
            return redirect(url_for('patient.book_appointment'))

        # Check for double-booking conflict
        conflict = query_db("""
            SELECT id FROM appointments 
            WHERE doctor_id = %s AND appointment_date = %s AND appointment_time = %s AND status != 'CANCELLED'
        """, (doctor_id, appointment_date, appointment_time), one=True)

        if conflict:
            flash('The selected time slot was just booked by another patient. Please choose another slot.', 'danger')
            return redirect(url_for('patient.book_appointment'))

        try:
            # Generate unique identifiers
            appointment_num = generate_appointment_number()
            invoice_num = generate_invoice_number()

            # Calculate next token number for this doctor on this day
            token_row = query_db("""
                SELECT COALESCE(MAX(token_number), 0) + 1 as next_token 
                FROM appointments 
                WHERE doctor_id = %s AND appointment_date = %s
            """, (doctor_id, appointment_date), one=True)
            token_number = token_row['next_token'] if token_row else 1

            # Fetch doctor fee
            doctor = query_db("SELECT consultation_fee FROM doctors WHERE id = %s", (doctor_id,), one=True)
            fee = float(doctor['consultation_fee']) if doctor else 500.00

            # Insert Appointment
            appt_id = execute_db("""
                INSERT INTO appointments (
                    appointment_number, patient_id, doctor_id, department_id, 
                    appointment_date, appointment_time, token_number, status, symptoms, booked_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'CONFIRMED', %s, 'PATIENT')
            """, (appointment_num, patient_id, doctor_id, department_id, 
                  appointment_date, appointment_time, token_number, symptoms))

            # Auto-generate Bill record
            execute_db("""
                INSERT INTO bills (
                    invoice_number, appointment_id, patient_id, consultation_fee, 
                    additional_charges, total_amount, discount, payable_amount, payment_status, payment_method
                ) VALUES (%s, %s, %s, %s, 0.00, %s, 0.00, %s, 'UNPAID', 'CASH')
            """, (invoice_num, appt_id, patient_id, fee, fee, fee))

            log_audit(session['user_id'], 'BOOK_APPOINTMENT', f"Booked appointment {appointment_num} with Token #{token_number}")
            flash(f"Appointment successfully confirmed! Your Token number is #{token_number:02d} ({appointment_num}).", 'success')
            return redirect(url_for('patient.my_appointments'))

        except Exception as e:
            flash(f"Error booking appointment: {e}", 'danger')
            return redirect(url_for('patient.book_appointment'))

    departments = query_db("SELECT id, name FROM departments WHERE is_active = 1 ORDER BY name ASC")
    return render_template('patient/book_appointment.html', departments=departments)

@patient_bp.route('/my-appointments')
@role_required('patient')
def my_appointments():
    """Lists past and upcoming appointments for logged-in patient."""
    patient_id = get_current_patient_id()
    appointments = query_db("""
        SELECT a.*, u.full_name as doctor_name, d.qualification, d.specialization, d.room_number, dept.name as department_name
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users u ON d.user_id = u.id
        JOIN departments dept ON a.department_id = dept.id
        WHERE a.patient_id = %s
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
    """, (patient_id,))

    return render_template('patient/my_appointments.html', appointments=appointments)

@patient_bp.route('/cancel-appointment/<int:appointment_id>', methods=['POST'])
@role_required('patient')
def cancel_appointment(appointment_id):
    """Allows patient to cancel a pending or confirmed appointment."""
    patient_id = get_current_patient_id()
    appt = query_db("SELECT * FROM appointments WHERE id = %s AND patient_id = %s", (appointment_id, patient_id), one=True)

    if not appt:
        flash("Appointment not found or unauthorized.", "danger")
        return redirect(url_for('patient.my_appointments'))

    if appt['status'] in ('COMPLETED', 'CANCELLED'):
        flash(f"Cannot cancel appointment with status '{appt['status']}'.", "warning")
        return redirect(url_for('patient.my_appointments'))

    execute_db("UPDATE appointments SET status = 'CANCELLED' WHERE id = %s", (appointment_id,))
    log_audit(session['user_id'], 'CANCEL_APPOINTMENT', f"Cancelled appointment {appt['appointment_number']}")
    flash(f"Appointment {appt['appointment_number']} has been successfully cancelled.", "info")
    return redirect(url_for('patient.my_appointments'))

@patient_bp.route('/prescriptions')
@role_required('patient')
def prescriptions():
    """Displays medical prescriptions with medication items."""
    patient_id = get_current_patient_id()
    rx_list = query_db("""
        SELECT p.*, a.appointment_number, a.appointment_date, u.full_name as doctor_name, d.specialization, dept.name as department_name
        FROM prescriptions p
        JOIN appointments a ON p.appointment_id = a.id
        JOIN doctors d ON p.doctor_id = d.id
        JOIN users u ON d.user_id = u.id
        JOIN departments dept ON d.department_id = dept.id
        WHERE p.patient_id = %s
        ORDER BY p.created_at DESC
    """, (patient_id,))

    # Attach medication items to each prescription
    for rx in rx_list:
        items = query_db("SELECT * FROM prescription_items WHERE prescription_id = %s", (rx['id'],))
        rx['items'] = items

    return render_template('patient/prescriptions.html', prescriptions=rx_list)

@patient_bp.route('/bills')
@role_required('patient')
def bills():
    """Displays patient billing history and receipts."""
    patient_id = get_current_patient_id()
    bill_list = query_db("""
        SELECT b.*, a.appointment_number, a.appointment_date, u.full_name as doctor_name, dept.name as department_name
        FROM bills b
        JOIN appointments a ON b.appointment_id = a.id
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users u ON d.user_id = u.id
        JOIN departments dept ON a.department_id = dept.id
        WHERE b.patient_id = %s
        ORDER BY b.created_at DESC
    """, (patient_id,))

    return render_template('patient/bills.html', bills=bill_list)
