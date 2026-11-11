"""
CarePlus Hospital - Internal API Blueprint Implementation
Provides dynamic JSON endpoints for department doctors and available slot calculations.
"""
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from app.db import query_db
from app.utils.helpers import format_time_hhmm

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/doctors-by-department/<int:department_id>')
def get_doctors_by_department(department_id):
    """Returns JSON list of doctors belonging to the selected department."""
    doctors = query_db("""
        SELECT d.id, u.full_name, d.specialization, d.qualification, d.consultation_fee, d.room_number, d.experience_years
        FROM doctors d
        JOIN users u ON d.user_id = u.id
        WHERE d.department_id = %s AND u.is_active = 1
        ORDER BY u.full_name ASC
    """, (department_id,))

    return jsonify({
        'status': 'success',
        'doctors': [
            {
                'id': doc['id'],
                'name': doc['full_name'],
                'specialization': doc['specialization'],
                'qualification': doc['qualification'],
                'fee': float(doc['consultation_fee'] or 0.0),
                'room': doc.get('room_number') or 'General OPD',
                'experience': doc.get('experience_years') or 0
            } for doc in doctors
        ]
    })

@api_bp.route('/available-slots')
def get_available_slots():
    """
    Calculates and returns available time slots for a specified doctor and date.
    Query params: doctor_id, date (YYYY-MM-DD)
    """
    raw_doctor_id = request.args.get('doctor_id')
    raw_date_str = request.args.get('date')

    if not raw_doctor_id or not raw_date_str:
        return jsonify({'status': 'error', 'message': 'Doctor and date parameters are required.', 'slots': []}), 400

    try:
        doctor_id = int(str(raw_doctor_id).strip())
    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'message': 'Invalid doctor ID parameter.', 'slots': []}), 400

    date_str = raw_date_str.strip()
    try:
        booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Invalid date format. Expected YYYY-MM-DD.', 'slots': []}), 400

    # Ensure date is not in past
    today = datetime.now().date()
    if booking_date < today:
        return jsonify({'status': 'error', 'message': 'Cannot book appointments for past dates.', 'slots': []}), 400

    # Determine Day of Week (Monday..Sunday)
    day_name = booking_date.strftime('%A')

    # Query Doctor Schedule for this day
    schedule = query_db("""
        SELECT * FROM doctor_schedules 
        WHERE doctor_id = %s AND day_of_week = %s AND is_available = 1
    """, (doctor_id, day_name), one=True)

    if not schedule:
        return jsonify({
            'status': 'unavailable',
            'message': f'Doctor is not scheduled for consultations on {day_name}s.',
            'slots': []
        })

    start_str = format_time_hhmm(schedule['start_time'])
    end_str = format_time_hhmm(schedule['end_time'])
    slot_minutes = int(schedule.get('slot_duration_minutes', 30) or 30)

    try:
        start_dt = datetime.strptime(start_str, '%H:%M')
        end_dt = datetime.strptime(end_str, '%H:%M')
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Invalid doctor schedule time configuration.', 'slots': []}), 500

    all_slots = []
    curr = start_dt
    while curr < end_dt:
        slot_time_str = curr.strftime('%H:%M')
        all_slots.append(slot_time_str)
        curr += timedelta(minutes=slot_minutes)

    # Query booked appointments for this doctor on this date
    booked_records = query_db("""
        SELECT appointment_time FROM appointments 
        WHERE doctor_id = %s AND appointment_date = %s AND UPPER(status) NOT IN ('CANCELLED', 'REJECTED')
    """, (doctor_id, date_str))

    booked_times = {format_time_hhmm(r['appointment_time']) for r in booked_records}

    # If booking for today, filter out past time slots
    current_time_str = datetime.now().strftime('%H:%M')

    available_slots = []
    for slot in all_slots:
        is_past = (booking_date == today and slot <= current_time_str)
        is_booked = (slot in booked_times)
        available_slots.append({
            'time': slot,
            'display': datetime.strptime(slot, '%H:%M').strftime('%I:%M %p'),
            'is_available': not is_past and not is_booked,
            'reason': 'Booked' if is_booked else ('Past' if is_past else 'Available')
        })

    return jsonify({
        'status': 'success',
        'doctor_id': doctor_id,
        'date': date_str,
        'day': day_name,
        'slots': available_slots
    })
