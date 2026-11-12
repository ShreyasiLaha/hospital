"""
CarePlus Hospital - Doctor Workspace Blueprint Implementation
Handles doctor queue management, weekly schedule configuration, and prescription generation.
"""
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.db import query_db, execute_db
from app.utils.decorators import role_required
from app.utils.helpers import log_audit, format_time_hhmm, create_notification, paginate_query

doctor_bp = Blueprint('doctor', __name__, url_prefix='/doctor')

def get_current_doctor_id():
    """Helper to retrieve or verify doctor ID associated with logged-in doctor user."""
    if 'doctor_id' in session:
        return session['doctor_id']
    doctor = query_db("SELECT id FROM doctors WHERE user_id = %s", (session['user_id'],), one=True)
    if doctor:
        session['doctor_id'] = doctor['id']
        return doctor['id']
    return None

def calculate_age(born_date):
    """Calculates age in years from date of birth."""
    if not born_date:
        return 'N/A'
    if isinstance(born_date, str):
        try:
            born_date = datetime.strptime(born_date, '%Y-%m-%d').date()
        except Exception:
            return 'N/A'
    today = date.today()
    return today.year - born_date.year - ((today.month, today.day) < (born_date.month, born_date.day))

@doctor_bp.route('/dashboard')
@role_required('doctor')
def dashboard():
    """Doctor command center with today's queue, consultation metrics, and active patients."""
    doctor_id = get_current_doctor_id()
    today_str = datetime.now().strftime('%Y-%m-%d')

    # Metrics
    today_count = query_db("""
        SELECT COUNT(*) as cnt FROM appointments 
        WHERE doctor_id = %s AND appointment_date = %s AND UPPER(status) NOT IN ('CANCELLED', 'REJECTED')
    """, (doctor_id, today_str), one=True)['cnt']

    waiting_queue_count = query_db("""
        SELECT COUNT(*) as cnt FROM appointments 
        WHERE doctor_id = %s AND appointment_date = %s AND status IN ('Pending', 'Confirmed', 'PENDING', 'CONFIRMED')
    """, (doctor_id, today_str), one=True)['cnt']

    completed_today_count = query_db("""
        SELECT COUNT(*) as cnt FROM appointments 
        WHERE doctor_id = %s AND appointment_date = %s AND status IN ('Completed', 'COMPLETED')
    """, (doctor_id, today_str), one=True)['cnt']

    total_patients_count = query_db("""
        SELECT COUNT(DISTINCT patient_id) as cnt FROM appointments 
        WHERE doctor_id = %s AND status IN ('Completed', 'COMPLETED')
    """, (doctor_id,), one=True)['cnt']

    # Today's Queue List
    today_appointments = query_db("""
        SELECT a.*, u.full_name as patient_name, u.phone as patient_phone, 
               p.gender, p.date_of_birth, p.blood_group, p.medical_history_summary
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN users u ON p.user_id = u.id
        WHERE a.doctor_id = %s AND a.appointment_date = %s AND UPPER(a.status) NOT IN ('CANCELLED', 'REJECTED')
        ORDER BY a.token_number ASC
    """, (doctor_id, today_str))

    for appt in today_appointments:
        appt['age'] = calculate_age(appt.get('date_of_birth'))

    return render_template('doctor/dashboard.html',
                           today_count=today_count,
                           waiting_queue_count=waiting_queue_count,
                           completed_today_count=completed_today_count,
                           total_patients_count=total_patients_count,
                           today_appointments=today_appointments)

@doctor_bp.route('/appointments')
@role_required('doctor')
def appointments():
    """Complete consultation history for this doctor."""
    doctor_id = get_current_doctor_id()
    filter_status = request.args.get('status', '')
    search_q = request.args.get('q', '').strip()
    page = request.args.get('page', 1)

    where_clause = "WHERE a.doctor_id = %s"
    params = [doctor_id]

    if filter_status:
        where_clause += " AND a.status = %s"
        params.append(filter_status)

    if search_q:
        where_clause += " AND (u.full_name LIKE %s OR a.appointment_number LIKE %s)"
        params.extend([f"%{search_q}%", f"%{search_q}%"])

    sql = f"""
        SELECT a.*, u.full_name as patient_name, u.phone as patient_phone, 
               p.gender, p.date_of_birth, p.blood_group, dept.name as department_name
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN users u ON p.user_id = u.id
        JOIN departments dept ON a.department_id = dept.id
        {where_clause}
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
    """
    count_sql = f"""
        SELECT COUNT(*) as cnt
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN users u ON p.user_id = u.id
        {where_clause}
    """

    paginated = paginate_query(sql, count_sql, tuple(params), page=page, per_page=15)
    for appt in paginated['items']:
        appt['age'] = calculate_age(appt.get('date_of_birth'))

    return render_template('doctor/appointments.html', 
                           appointments=paginated['items'],
                           pagination=paginated,
                           current_filter=filter_status, 
                           search_query=search_q)

@doctor_bp.route('/schedule', methods=['GET', 'POST'])
@role_required('doctor')
def schedule():
    """Configures doctor's weekly duty days, hours, and slot intervals."""
    doctor_id = get_current_doctor_id()
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    if request.method == 'POST':
        try:
            for day in days_of_week:
                day_lower = day.lower()
                is_available = 1 if request.form.get(f'available_{day_lower}') else 0
                start_time = request.form.get(f'start_{day_lower}', '09:00').strip()
                end_time = request.form.get(f'end_{day_lower}', '13:00').strip()
                slot_duration = int(request.form.get(f'slot_{day_lower}', 30) or 30)

                # Ensure HH:MM:SS format
                if len(start_time) == 5: start_time += ':00'
                if len(end_time) == 5: end_time += ':00'

                # Upsert into doctor_schedules
                existing = query_db("SELECT id FROM doctor_schedules WHERE doctor_id = %s AND day_of_week = %s", 
                                    (doctor_id, day), one=True)
                if existing:
                    execute_db("""
                        UPDATE doctor_schedules 
                        SET start_time = %s, end_time = %s, slot_duration_minutes = %s, is_available = %s
                        WHERE id = %s
                    """, (start_time, end_time, slot_duration, is_available, existing['id']))
                else:
                    execute_db("""
                        INSERT INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time, slot_duration_minutes, is_available)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (doctor_id, day, start_time, end_time, slot_duration, is_available))

            log_audit(session['user_id'], 'UPDATE_SCHEDULE', 'Doctor updated weekly consultation hours.')
            flash('Your weekly consultation schedule has been updated successfully.', 'success')
            return redirect(url_for('doctor.schedule'))
        except Exception as e:
            flash(f"Error saving schedule: {e}", 'danger')

    # Load existing schedules mapped by day
    schedules_raw = query_db("SELECT * FROM doctor_schedules WHERE doctor_id = %s", (doctor_id,))
    schedule_map = {}
    for s in schedules_raw:
        # Standardize time strings to HH:MM
        st = format_time_hhmm(s['start_time'])
        et = format_time_hhmm(s['end_time'])
        schedule_map[s['day_of_week']] = {
            'is_available': bool(s['is_available']),
            'start_time': st,
            'end_time': et,
            'slot_duration': s.get('slot_duration_minutes', 30)
        }

    return render_template('doctor/schedule.html', days_of_week=days_of_week, schedule_map=schedule_map)

@doctor_bp.route('/write-prescription/<int:appointment_id>', methods=['GET', 'POST'])
@role_required('doctor')
def write_prescription(appointment_id):
    """Consultation and multi-drug prescription pad."""
    doctor_id = get_current_doctor_id()

    # Verify appointment belongs to this doctor
    appt = query_db("""
        SELECT a.*, u.full_name as patient_name, u.phone as patient_phone, 
               p.gender, p.date_of_birth, p.blood_group, p.medical_history_summary,
               dept.name as department_name
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN users u ON p.user_id = u.id
        JOIN departments dept ON a.department_id = dept.id
        WHERE a.id = %s AND a.doctor_id = %s
    """, (appointment_id, doctor_id), one=True)

    if not appt:
        flash('Consultation record not found or access unauthorized.', 'danger')
        return redirect(url_for('doctor.dashboard'))

    appt['age'] = calculate_age(appt.get('date_of_birth'))

    # Check for existing prescription
    existing_rx = query_db("SELECT * FROM prescriptions WHERE appointment_id = %s", (appointment_id,), one=True)
    existing_items = []
    if existing_rx:
        existing_items = query_db("SELECT * FROM prescription_items WHERE prescription_id = %s", (existing_rx['id'],))

    if request.method == 'POST':
        diagnosis = request.form.get('diagnosis', '').strip()
        advice_notes = request.form.get('advice_notes', '').strip()
        follow_up_date = request.form.get('follow_up_date', '').strip() or None

        med_names = request.form.getlist('medicine_name[]')
        dosages = request.form.getlist('dosage[]')
        frequencies = request.form.getlist('frequency[]')
        durations = request.form.getlist('duration[]')
        instructions = request.form.getlist('instructions[]')

        if not diagnosis:
            flash('Clinical diagnosis is mandatory.', 'warning')
            return render_template('doctor/write_prescription.html', 
                                   appointment=appt, 
                                   appointment_id=appointment_id,
                                   prescription=existing_rx,
                                   items=existing_items)

        try:
            if existing_rx:
                rx_id = existing_rx['id']
                execute_db("""
                    UPDATE prescriptions 
                    SET diagnosis = %s, advice_notes = %s, follow_up_date = %s
                    WHERE id = %s
                """, (diagnosis, advice_notes, follow_up_date, rx_id))
                execute_db("DELETE FROM prescription_items WHERE prescription_id = %s", (rx_id,))
            else:
                rx_id = execute_db("""
                    INSERT INTO prescriptions (appointment_id, doctor_id, patient_id, diagnosis, advice_notes, follow_up_date)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (appointment_id, doctor_id, appt['patient_id'], diagnosis, advice_notes, follow_up_date))

            # Insert medicine rows
            for i in range(len(med_names)):
                m_name = med_names[i].strip() if i < len(med_names) else ''
                if m_name:
                    m_dose = dosages[i].strip() if i < len(dosages) else ''
                    m_freq = frequencies[i].strip() if i < len(frequencies) else ''
                    m_dur = durations[i].strip() if i < len(durations) else ''
                    m_inst = instructions[i].strip() if i < len(instructions) else ''
                    execute_db("""
                        INSERT INTO prescription_items (prescription_id, medicine_name, dosage, frequency, duration, instructions)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (rx_id, m_name, m_dose, m_freq, m_dur, m_inst))

            # Mark appointment COMPLETED
            execute_db("UPDATE appointments SET status = 'Completed' WHERE id = %s", (appointment_id,))

            # Trigger notification to patient
            pat = query_db("SELECT user_id FROM patients WHERE id = %s", (appt['patient_id'],), one=True)
            if pat:
                create_notification(pat['user_id'], 'Prescription Issued',
                                    f"Dr. {session.get('full_name')} completed your consultation and issued your prescription for appointment {appt['appointment_number']}.", 'APPOINTMENT')

            log_audit(session['user_id'], 'WRITE_PRESCRIPTION', f"Prescription #{rx_id} issued for Appt #{appt['appointment_number']}")
            flash(f"Prescription successfully saved and consultation completed for {appt['patient_name']}!", 'success')
            return redirect(url_for('doctor.dashboard'))

        except Exception as e:
            flash(f"Error saving prescription: {e}", 'danger')

    return render_template('doctor/write_prescription.html', 
                           appointment=appt, 
                           appointment_id=appointment_id,
                           prescription=existing_rx,
                           items=existing_items)
