"""
CarePlus Hospital - Comprehensive End-to-End System Test
Validates all 4 roles, security guards, clinical workflows, and reporting.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.db import query_db

app = create_app()

def run_tests():
    print("==================================================")
    print("   CarePlus Hospital - End-to-End System Tests    ")
    print("==================================================")

    # 1. TEST AUTHENTICATION & ROLE-BASED ACCESS CONTROL
    print("\n[1/7] Testing Multi-Role Authentication...")
    test_credentials = [
        ('admin@careplus.com', 'Admin@123', '/admin/dashboard'),
        ('dr.chen@careplus.com', 'Doctor@123', '/doctor/dashboard'),
        ('reception@careplus.com', 'Reception@123', '/receptionist/dashboard'),
        ('alex@patient.com', 'Patient@123', '/patient/dashboard')
    ]
    for email, pw, expected in test_credentials:
        c = app.test_client()
        res = c.post('/auth/login', data={'email': email, 'password': pw})
        assert res.status_code == 302, f"Login failed for {email}"
        assert res.headers.get('Location') == expected, f"Wrong redirect for {email}: {res.headers.get('Location')}"
        print(f"  [OK] {email} successfully authenticated -> {expected}")

    # 2. TEST PATIENT APPOINTMENT BOOKING
    print("\n[2/7] Testing Patient Appointment Booking & Slots...")
    c_patient = app.test_client()
    c_patient.post('/auth/login', data={'email': 'alex@patient.com', 'password': 'Patient@123'})
    
    # Check slots API
    res_slots = c_patient.get('/api/available-slots?doctor_id=1&date=2026-11-09')
    assert res_slots.status_code == 200, "Slots API failed"
    slots_data = res_slots.json
    assert slots_data.get('status') == 'success', "Slot calculation status error"
    print(f"  [OK] Slot API returned {len(slots_data['slots'])} slots for 2026-11-09 (Doctor 1)")

    # Book appointment
    res_book = c_patient.post('/patient/book-appointment', data={
        'department_id': '1',
        'doctor_id': '1',
        'appointment_date': '2026-11-09',
        'appointment_time': '10:00',
        'symptoms': 'Cardiovascular health routine evaluation'
    })
    assert res_book.status_code == 302, "Appointment booking failed"
    
    with app.app_context():
        latest_appt = query_db("SELECT * FROM appointments WHERE appointment_date='2026-11-09' AND doctor_id=1 ORDER BY id DESC LIMIT 1", one=True)
        assert latest_appt is not None, "Appointment not found in database"
        appt_id = latest_appt['id']
        print(f"  [OK] Created Appointment {latest_appt['appointment_number']} (Token #{latest_appt['token_number']})")

    # 3. TEST DOCTOR PRESCRIPTION PAD
    print("\n[3/7] Testing Doctor Consultation & Prescription Builder...")
    c_doctor = app.test_client()
    c_doctor.post('/auth/login', data={'email': 'dr.chen@careplus.com', 'password': 'Doctor@123'})
    
    res_rx = c_doctor.post(f'/doctor/write-prescription/{appt_id}', data={
        'diagnosis': 'Borderline Hypertension - Stage 1',
        'advice_notes': 'Maintain low-sodium diet, 30 min daily cardio exercise, follow up in 1 month.',
        'follow_up_date': '2026-12-09',
        'medicine_name[]': ['Telmisartan', 'Metoprolol Succinate'],
        'dosage[]': ['40 mg', '25 mg'],
        'frequency[]': ['1-0-0 (Morning)', '0-0-1 (Night)'],
        'duration[]': ['30 Days', '30 Days'],
        'instructions[]': ['After breakfast', 'Before sleep']
    })
    assert res_rx.status_code == 302, "Prescription creation failed"

    with app.app_context():
        rx = query_db("SELECT * FROM prescriptions WHERE appointment_id = %s", (appt_id,), one=True)
        assert rx is not None, "Prescription not saved"
        items = query_db("SELECT * FROM prescription_items WHERE prescription_id = %s", (rx['id'],))
        assert len(items) == 2, f"Expected 2 medications, got {len(items)}"
        updated_appt = query_db("SELECT status FROM appointments WHERE id = %s", (appt_id,), one=True)
        assert updated_appt['status'] in ('Completed', 'COMPLETED'), f"Appointment not marked Completed (got {updated_appt['status']})"
        print(f"  [OK] Prescription #{rx['id']} saved with {len(items)} medicines & Appt status marked Completed")

    # 4. TEST RECEPTIONIST WALK-IN BOOKING
    print("\n[4/7] Testing Receptionist Walk-in Patient Booking...")
    c_recep = app.test_client()
    c_recep.post('/auth/login', data={'email': 'reception@careplus.com', 'password': 'Reception@123'})

    res_walkin = c_recep.post('/receptionist/walkin-booking', data={
        'patient_name': 'Sarah Connor',
        'phone': '+1 555-888-9999',
        'gender': 'Female',
        'dob': '1985-03-25',
        'blood_group': 'O-',
        'department_id': '1',
        'doctor_id': '1',
        'symptoms': 'Palpitations and exertion fatigue'
    })
    assert res_walkin.status_code == 302, "Walk-in booking failed"

    with app.app_context():
        walkin = query_db("SELECT * FROM appointments WHERE booked_by='RECEPTIONIST' ORDER BY id DESC LIMIT 1", one=True)
        assert walkin is not None, "Walk-in appointment not recorded"
        walkin_appt_id = walkin['id']
        print(f"  [OK] Walk-in Appointment {walkin['appointment_number']} registered with Token #{walkin['token_number']}")

    # 5. TEST RECEPTIONIST CASHIER BILLING
    print("\n[5/7] Testing Receptionist Cashier Invoicing Desk...")
    with app.app_context():
        bill = query_db("SELECT * FROM bills WHERE appointment_id = %s", (walkin_appt_id,), one=True)
        assert bill is not None, "Bill not created for walk-in"
        bill_id = bill['id']

    res_pay = c_recep.post('/receptionist/billing', data={
        'bill_id': bill_id,
        'consultation_fee': '750.00',
        'additional_charges': '120.00', # ECG & Lipid profile
        'discount': '50.00',
        'payment_method': 'UPI'
    })
    assert res_pay.status_code == 302, "Payment settlement failed"

    with app.app_context():
        b_paid = query_db("SELECT * FROM bills WHERE id = %s", (bill_id,), one=True)
        assert b_paid['payment_status'] == 'PAID', "Bill not marked PAID"
        assert float(b_paid['payable_amount']) == 820.00, f"Expected 820.00, got {b_paid['payable_amount']}"
        print(f"  [OK] Bill {b_paid['invoice_number']} settled for ${b_paid['payable_amount']} via {b_paid['payment_method']}")

    # 6. TEST ADMINISTRATOR MANAGEMENT
    print("\n[6/7] Testing Administrator Department & Staff Creation...")
    c_admin = app.test_client()
    c_admin.post('/auth/login', data={'email': 'admin@careplus.com', 'password': 'Admin@123'})

    # Create new department
    with app.app_context():
        from app.db import execute_db
        execute_db("DELETE FROM departments WHERE name = 'Oncology'")

    res_dept = c_admin.post('/admin/manage-departments', data={
        'name': 'Oncology',
        'description': 'Advanced cancer care, chemotherapy, and tumor therapy.',
        'icon_class': 'bi-radioactive'
    })
    assert res_dept.status_code == 302, "Department creation failed"

    with app.app_context():
        dept_onco = query_db("SELECT * FROM departments WHERE name = 'Oncology'", one=True)
        assert dept_onco is not None, "Oncology department not found"
        print(f"  [OK] Created Department '{dept_onco['name']}' (ID #{dept_onco['id']})")

    # 7. TEST ADMIN CSV EXPORTS
    print("\n[7/7] Testing CSV Report Generation...")
    res_csv_appt = c_admin.get('/admin/export-appointments-csv')
    assert res_csv_appt.status_code == 200, "Appointments CSV export failed"
    assert b"Appt Number,Date,Time" in res_csv_appt.data, "Invalid appointments CSV headers"
    print("  [OK] Appointments CSV export generated successfully")

    res_csv_rev = c_admin.get('/admin/export-revenue-csv')
    assert res_csv_rev.status_code == 200, "Revenue CSV export failed"
    assert b"Invoice Number,Appt Code" in res_csv_rev.data, "Invalid revenue CSV headers"
    print("  [OK] Financial Revenue CSV statement generated successfully")

    print("\n==================================================")
    print("   ALL TESTS PASSED! CAREPLUS SYSTEM VERIFIED!    ")
    print("==================================================")

def test_system_flow():
    """Pytest hook for end-to-end system flow tests."""
    run_tests()

if __name__ == '__main__':
    run_tests()
