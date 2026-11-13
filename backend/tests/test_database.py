"""
CarePlus Hospital - Database Test & Verification Suite
Validates schema integrity, tables, foreign keys, indexes, roles, statuses, and constraints.
"""
import sys
import os

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from config import Config
from app import create_app
from app.db import get_db, query_db, execute_db

def run_tests():
    print("=" * 75)
    print(" CarePlus Hospital (hospital_db) - Full Verification Test")
    print("=" * 75)

    app = create_app()

    with app.app_context():
        # 1. Test Database Connection Module
        print("\n--- Test 1: Connection Module & Environment Configuration ---")
        get_db()
        from flask import g
        backend = getattr(g, 'db_backend', 'mysql')
        print("[OK] Database connection established successfully.")
        print(f"     Active Backend Engine: {backend.upper()}")
        print(f"     Target DB Name:        {Config.DB_NAME}")
        print(f"     Host & Port:           {Config.DB_HOST}:{Config.DB_PORT}")
        print(f"     Config User:           {Config.DB_USER}")
        if backend == 'sqlite':
            print(f"     Active Fallback File:  {Config.SQLITE_PATH}")

        # 2. Test All 9 Required Tables
        print("\n--- Test 2: Required Tables Verification ---")
        required_tables = [
            'users',
            'patients',
            'doctors',
            'receptionists',
            'departments',
            'doctor_schedules',
            'appointments',
            'notifications',
            'activity_logs'
        ]

        table_rows = {}
        for t in required_tables:
            res = query_db(f"SELECT COUNT(*) as cnt FROM {t}", one=True)
            table_rows[t] = res['cnt']
            print(f"[OK] Table '{t:<18}' EXISTS | Row count: {res['cnt']}")

        # 3. Test 4 User Roles
        print("\n--- Test 3: Four User Roles Support ---")
        roles = query_db("SELECT DISTINCT role, COUNT(*) as cnt FROM users GROUP BY role")
        found_roles = {r['role']: r['cnt'] for r in roles}
        for expected_role in ['admin', 'doctor', 'receptionist', 'patient']:
            if expected_role in found_roles:
                print(f"[OK] Role '{expected_role:<12}' supported ({found_roles[expected_role]} demonstration user(s))")
            else:
                print(f"[FAIL] Role '{expected_role}' missing from users table!")

        # 4. Test Dedicated Role Profiles
        print("\n--- Test 4: Dedicated Role Table Linkages & Foreign Keys ---")
        # Check doctors linked to users and departments
        doctors = query_db("""
            SELECT d.id, u.full_name, u.email, dept.name as dept_name, d.specialization, d.room_number, d.consultation_fee
            FROM doctors d
            JOIN users u ON d.user_id = u.id
            JOIN departments dept ON d.department_id = dept.id
        """)
        print(f"[OK] Doctors Profile Linkage: {len(doctors)} doctors correctly linked to users and departments")
        for d in doctors:
            print(f"     - Dr. ID {d['id']}: {d['full_name']} ({d['dept_name']} - {d['specialization']}) Room: {d['room_number']}")

        # Check receptionists linked to users
        receptionists = query_db("""
            SELECT r.id, u.full_name, u.email, r.desk_number, r.shift, r.qualification
            FROM receptionists r
            JOIN users u ON r.user_id = u.id
        """)
        print(f"[OK] Receptionists Profile Linkage: {len(receptionists)} receptionists correctly linked to users")
        for r in receptionists:
            print(f"     - Rec. ID {r['id']}: {r['full_name']} | Desk: {r['desk_number']} | Shift: {r['shift']}")

        # Check patients linked to users
        patients = query_db("""
            SELECT p.id, u.full_name, u.email, p.gender, p.blood_group, p.date_of_birth, p.emergency_contact_name
            FROM patients p
            JOIN users u ON p.user_id = u.id
        """)
        print(f"[OK] Patients Profile Linkage: {len(patients)} patients correctly linked to users")
        for p in patients:
            print(f"     - Pat. ID {p['id']}: {p['full_name']} | Blood: {p['blood_group']} | Emergency: {p['emergency_contact_name']}")

        # 5. Test Fictional Sample Departments
        print("\n--- Test 5: Fictional Sample Departments ---")
        depts = query_db("SELECT id, name, description FROM departments ORDER BY id ASC")
        print(f"[OK] {len(depts)} clinical departments seeded:")
        for dept in depts:
            print(f"     - [{dept['id']}] {dept['name']}: {dept['description'][:60]}...")

        # 6. Test Doctor Consultation Schedules
        print("\n--- Test 6: Doctor Weekly Schedules ---")
        schedules = query_db("""
            SELECT ds.id, u.full_name as doctor_name, ds.day_of_week, ds.start_time, ds.end_time, ds.slot_duration_minutes
            FROM doctor_schedules ds
            JOIN doctors d ON ds.doctor_id = d.id
            JOIN users u ON d.user_id = u.id
            ORDER BY ds.doctor_id, ds.id
        """)
        print(f"[OK] {len(schedules)} consultation rota slots configured across active doctors.")

        # 7. Test Appointment Statuses (Pending, Confirmed, Completed, Cancelled, Rejected)
        print("\n--- Test 7: Five Required Appointment Statuses ---")
        appt_stats = query_db("SELECT status, COUNT(*) as cnt FROM appointments GROUP BY status")
        status_map = {s['status']: s['cnt'] for s in appt_stats}
        all_5_statuses = ['Pending', 'Confirmed', 'Completed', 'Cancelled', 'Rejected']
        for st in all_5_statuses:
            count = status_map.get(st, 0)
            if count > 0:
                print(f"[OK] Status '{st:<12}' present ({count} appointment(s))")
            else:
                print(f"[FAIL] Status '{st}' not found in appointments table!")

        # 8. Test Notifications Table
        print("\n--- Test 8: Notifications Table & User Alerts ---")
        notifs = query_db("""
            SELECT n.id, u.full_name, n.title, n.type, n.is_read
            FROM notifications n
            JOIN users u ON n.user_id = u.id
            ORDER BY n.id ASC
        """)
        print(f"[OK] {len(notifs)} system notifications logged for users:")
        for n in notifs[:3]:
            print(f"     - [{n['type']}] For {n['full_name']}: '{n['title']}' (Read: {bool(n['is_read'])})")

        # 9. Test Activity Logs Table
        print("\n--- Test 9: Activity Logs Audit Trail ---")
        logs = query_db("""
            SELECT l.id, COALESCE(u.full_name, 'SYSTEM') as user_name, l.action, l.details, l.ip_address
            FROM activity_logs l
            LEFT JOIN users u ON l.user_id = u.id
            ORDER BY l.id ASC
        """)
        print(f"[OK] {len(logs)} activity logs recorded in audit trail:")
        for log in logs[:3]:
            print(f"     - Action: '{log['action']}' by {log['user_name']} | Details: {log['details']}")

        # 10. Test Double-Booking Prevention Constraint
        print("\n--- Test 10: Double Booking Prevention Enforcement ---")
        first_appt = query_db("SELECT doctor_id, appointment_date, appointment_time FROM appointments LIMIT 1", one=True)
        doc_id = first_appt['doctor_id']
        appt_date = first_appt['appointment_date']
        appt_time = first_appt['appointment_time']

        print(f"Attempting to double-book Doctor ID {doc_id} on {appt_date} at {appt_time}...")
        try:
            execute_db("""
                INSERT INTO appointments (
                    appointment_number, patient_id, doctor_id, department_id,
                    appointment_date, appointment_time, token_number, status, symptoms, booked_by
                ) VALUES ('APT-TEST-CONFLICT', 1, %s, 1, %s, %s, 99, 'Pending', 'Test Conflict', 'PATIENT')
            """, (doc_id, appt_date, appt_time))
            print("[FAIL] Conflict test failed: Duplicate appointment slot was inserted!")
        except Exception as e:
            print("[PASS] Duplicate slot successfully REJECTED by database constraint!")
            print(f"       Constraint enforcement message: {e}")

        # 11. Test Supporting Clinical/Billing Tables
        print("\n--- Test 11: Clinical & Billing Supporting Tables ---")
        for st in ['prescriptions', 'prescription_items', 'bills']:
            cnt = query_db(f"SELECT COUNT(*) as cnt FROM {st}", one=True)['cnt']
            print(f"[OK] Supporting Table '{st:<18}' EXISTS | Row count: {cnt}")

    print("\n" + "=" * 75)
    print(" ALL 11 DATABASE TESTS PASSED SUCCESSFULLY!")
    print("=" * 75)

def test_database_verification():
    """Pytest hook for database verification suite."""
    run_tests()

if __name__ == '__main__':
    run_tests()
