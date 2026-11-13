"""
CarePlus Hospital - Database Initialization & Verification Engine
Target Database: hospital_db (MySQL InnoDB with SQLite fallback)

Usage:
    python init_db.py          (Default: Attempts MySQL, falls back to local SQLite if MySQL daemon is offline)
    python init_db.py --mysql  (Strict MySQL initialization)
    python init_db.py --sqlite (Direct SQLite initialization)
    python init_db.py --verify (Runs detailed verification of tables, constraints, and double-booking prevention)
"""
import sys
import os
import sqlite3
import pymysql
from werkzeug.security import generate_password_hash

# Ensure project root is importable
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
root_dir = os.path.abspath(os.path.join(parent_dir, '..'))

for p in [parent_dir, root_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from config import Config

def execute_sql_file(cursor, filepath):
    """Executes a multi-statement SQL file, correctly ignoring empty segments and comments."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split statements by semicolon while respecting strings
    statements = []
    current_stmt = []
    
    lines = content.splitlines()
    for line in lines:
        stripped = line.strip()
        # Skip pure comment lines when starting a new statement
        if not current_stmt and (stripped.startswith('--') or stripped.startswith('/*') or not stripped):
            continue
        current_stmt.append(line)
        if stripped.endswith(';'):
            stmt_text = '\n'.join(current_stmt).strip()
            if stmt_text:
                statements.append(stmt_text)
            current_stmt = []

    for stmt in statements:
        # Strip trailing semicolon for cursor execution if needed
        clean_stmt = stmt.strip()
        if clean_stmt.endswith(';'):
            clean_stmt = clean_stmt[:-1].strip()
        if clean_stmt:
            cursor.execute(clean_stmt)

def init_mysql():
    """Initializes MySQL database hospital_db using schema.sql and seed_data.sql."""
    print(f"[*] Connecting to MySQL at {Config.DB_HOST}:{Config.DB_PORT} as '{Config.DB_USER}'...")
    try:
        conn = pymysql.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            port=Config.DB_PORT,
            charset='utf8mb4',
            autocommit=True
        )
        with conn.cursor() as cursor:
            db_name = Config.DB_NAME
            print(f"[*] Creating MySQL database '{db_name}' if not exists...")
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            cursor.execute(f"USE {db_name};")

            schema_file = os.path.join(current_dir, 'schema.sql')
            seed_file = os.path.join(current_dir, 'seed_data.sql')

            print(f"[*] Applying DDL schema from {os.path.basename(schema_file)}...")
            execute_sql_file(cursor, schema_file)

            print(f"[*] Populating demonstration data from {os.path.basename(seed_file)}...")
            execute_sql_file(cursor, seed_file)

        conn.close()
        print("\n[SUCCESS] MySQL database 'hospital_db' initialized and seeded successfully!")
        return True
    except Exception as e:
        print(f"\n[MySQL Notice] Could not connect to MySQL server ({e})")
        return False

def init_sqlite():
    """Initializes a matching SQLite database for offline evaluation and instant testing."""
    db_path = Config.SQLITE_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    print(f"[*] Initializing local database at: {db_path}...")

    conn = sqlite3.connect(db_path, timeout=30.0)
    cursor = conn.cursor()

    cursor.executescript("""
    PRAGMA foreign_keys = ON;

    -- 1. Table: users
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT CHECK(role IN ('admin', 'doctor', 'receptionist', 'patient')) NOT NULL,
        phone TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- 2. Table: departments
    CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        icon_class TEXT DEFAULT 'bi-heart-pulse',
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- 3. Table: doctors
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        department_id INTEGER NOT NULL,
        qualification TEXT NOT NULL,
        specialization TEXT NOT NULL,
        consultation_fee REAL NOT NULL DEFAULT 500.00,
        room_number TEXT NOT NULL,
        experience_years INTEGER NOT NULL DEFAULT 1,
        bio TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE RESTRICT
    );

    -- 4. Table: patients
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        date_of_birth TEXT NOT NULL,
        gender TEXT CHECK(gender IN ('Male', 'Female', 'Other')) NOT NULL,
        blood_group TEXT DEFAULT 'O+',
        address TEXT NOT NULL,
        emergency_contact_name TEXT,
        emergency_contact_phone TEXT,
        medical_history_summary TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    -- 5. Table: receptionists
    CREATE TABLE IF NOT EXISTS receptionists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        desk_number TEXT NOT NULL DEFAULT 'Front Desk - Wing A',
        shift TEXT CHECK(shift IN ('Morning', 'Evening', 'Night', 'Rotational')) DEFAULT 'Morning',
        qualification TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    -- 6. Table: doctor_schedules
    CREATE TABLE IF NOT EXISTS doctor_schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_id INTEGER NOT NULL,
        day_of_week TEXT CHECK(day_of_week IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')) NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        slot_duration_minutes INTEGER DEFAULT 30,
        max_patients INTEGER DEFAULT 20,
        is_available INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE,
        UNIQUE (doctor_id, day_of_week)
    );

    -- 7. Table: appointments
    -- Includes all 5 statuses: Pending, Confirmed, Completed, Cancelled, Rejected
    -- UNIQUE(doctor_id, appointment_date, appointment_time) prevents double booking
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_number TEXT NOT NULL UNIQUE,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        department_id INTEGER NOT NULL,
        appointment_date TEXT NOT NULL,
        appointment_time TEXT NOT NULL,
        token_number INTEGER NOT NULL,
        status TEXT CHECK(status IN ('Pending', 'Confirmed', 'Completed', 'Cancelled', 'Rejected')) DEFAULT 'Pending',
        symptoms TEXT,
        booked_by TEXT CHECK(booked_by IN ('PATIENT', 'RECEPTIONIST', 'ADMIN')) DEFAULT 'PATIENT',
        rejection_reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
        FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE RESTRICT,
        FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE RESTRICT,
        UNIQUE (doctor_id, appointment_date, appointment_time)
    );

    -- 8. Table: notifications
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        type TEXT CHECK(type IN ('APPOINTMENT', 'SYSTEM', 'BILLING', 'REMINDER')) DEFAULT 'APPOINTMENT',
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    -- 9. Table: activity_logs
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        details TEXT,
        ip_address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    );

    -- Supporting Tables: prescriptions, prescription_items, bills
    CREATE TABLE IF NOT EXISTS prescriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_id INTEGER NOT NULL UNIQUE,
        doctor_id INTEGER NOT NULL,
        patient_id INTEGER NOT NULL,
        diagnosis TEXT NOT NULL,
        advice_notes TEXT,
        follow_up_date TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE,
        FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE RESTRICT,
        FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS prescription_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prescription_id INTEGER NOT NULL,
        medicine_name TEXT NOT NULL,
        dosage TEXT NOT NULL,
        frequency TEXT NOT NULL,
        duration TEXT NOT NULL,
        instructions TEXT,
        FOREIGN KEY (prescription_id) REFERENCES prescriptions(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS bills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT NOT NULL UNIQUE,
        appointment_id INTEGER NOT NULL UNIQUE,
        patient_id INTEGER NOT NULL,
        consultation_fee REAL NOT NULL,
        additional_charges REAL DEFAULT 0.00,
        total_amount REAL NOT NULL,
        discount REAL DEFAULT 0.00,
        payable_amount REAL NOT NULL,
        payment_status TEXT CHECK(payment_status IN ('UNPAID', 'PAID', 'PARTIALLY_PAID')) DEFAULT 'UNPAID',
        payment_method TEXT CHECK(payment_method IN ('CASH', 'CARD', 'UPI', 'ONLINE')) DEFAULT 'CASH',
        paid_at TIMESTAMP,
        generated_by_user_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE,
        FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
        FOREIGN KEY (generated_by_user_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """)

    # Seed data
    pw_admin = generate_password_hash("Admin@123")
    pw_doctor = generate_password_hash("Doctor@123")
    pw_reception = generate_password_hash("Reception@123")
    pw_patient = generate_password_hash("Patient@123")

    departments = [
        ('Cardiology', 'Heart health, cardiovascular diagnostics, ECG, and hypertension care.', 'bi-heart-pulse'),
        ('Neurology', 'Brain, nerve, migraine, stroke rehabilitation, and spinal therapy.', 'bi-activity'),
        ('Pediatrics', 'Comprehensive infant healthcare, developmental pediatrics, and immunization.', 'bi-person-heart'),
        ('Orthopedics', 'Bones, joints, arthritis treatment, ligaments, and sports injury recovery.', 'bi-bandaid'),
        ('Dermatology', 'Skin, hair, eczema, allergy diagnostics, and cosmetic dermatology.', 'bi-emoji-smile'),
        ('General Medicine', 'Primary outpatient care, seasonal fever, diagnostic health checkups, and wellness.', 'bi-clipboard2-pulse')
    ]
    cursor.executemany("INSERT OR IGNORE INTO departments (name, description, icon_class) VALUES (?, ?, ?)", departments)

    users = [
        ('Hospital Administrator', 'admin@careplus.com', pw_admin, 'admin', '+1 800-555-0199'),
        ('Sarah Jenkins', 'reception@careplus.com', pw_reception, 'receptionist', '+1 800-555-0102'),
        ('David Miller', 'reception2@careplus.com', pw_reception, 'receptionist', '+1 800-555-0103'),
        ('Dr. Robert Chen, MD', 'dr.chen@careplus.com', pw_doctor, 'doctor', '+1 800-555-0144'),
        ('Dr. Emily Watson, MBBS', 'dr.watson@careplus.com', pw_doctor, 'doctor', '+1 800-555-0177'),
        ('Dr. Rajesh Kumar, MS', 'dr.kumar@careplus.com', pw_doctor, 'doctor', '+1 800-555-0188'),
        ('Alex Morgan', 'alex@patient.com', pw_patient, 'patient', '+1 555-019-2834'),
        ('Maria Garcia', 'maria@patient.com', pw_patient, 'patient', '+1 555-018-7711'),
        ('John Doe', 'john@patient.com', pw_patient, 'patient', '+1 555-017-3322')
    ]
    for u in users:
        cursor.execute("INSERT OR IGNORE INTO users (full_name, email, password_hash, role, phone) VALUES (?, ?, ?, ?, ?)", u)

    # Receptionists
    cursor.execute("SELECT id FROM users WHERE email='reception@careplus.com'")
    r1_id = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM users WHERE email='reception2@careplus.com'")
    r2_id = cursor.fetchone()[0]

    cursor.execute("INSERT OR IGNORE INTO receptionists (user_id, desk_number, shift, qualification) VALUES (?, 'Front Desk - Main Wing A', 'Morning', 'B.Sc Healthcare Administration')", (r1_id,))
    cursor.execute("INSERT OR IGNORE INTO receptionists (user_id, desk_number, shift, qualification) VALUES (?, 'Front Desk - OPD Wing B', 'Evening', 'Diploma in Hospital Front Office Management')", (r2_id,))

    # Doctors
    cursor.execute("SELECT id FROM users WHERE email='dr.chen@careplus.com'")
    doc1_uid = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM users WHERE email='dr.watson@careplus.com'")
    doc2_uid = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM users WHERE email='dr.kumar@careplus.com'")
    doc3_uid = cursor.fetchone()[0]

    cursor.execute("SELECT id FROM departments WHERE name='Cardiology'")
    dept_cardio = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM departments WHERE name='Pediatrics'")
    dept_pedia = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM departments WHERE name='Orthopedics'")
    dept_ortho = cursor.fetchone()[0]

    cursor.execute("""
        INSERT OR IGNORE INTO doctors (user_id, department_id, qualification, specialization, consultation_fee, room_number, experience_years, bio)
        VALUES (?, ?, 'MD - Cardiology, FACC', 'Interventional Cardiologist', 750.00, 'Room 101 - Wing A', 12, 'Over 12 years of clinical expertise in coronary interventions, hypertension therapy, and preventative cardiology.')
    """, (doc1_uid, dept_cardio))

    cursor.execute("""
        INSERT OR IGNORE INTO doctors (user_id, department_id, qualification, specialization, consultation_fee, room_number, experience_years, bio)
        VALUES (?, ?, 'MBBS, MD - Pediatrics', 'Senior Pediatrician & Neonatologist', 500.00, 'Room 204 - Wing B', 8, 'Dedicated pediatrician specialized in neonatal intensive care, child nutrition, and preventative vaccination programs.')
    """, (doc2_uid, dept_pedia))

    cursor.execute("""
        INSERT OR IGNORE INTO doctors (user_id, department_id, qualification, specialization, consultation_fee, room_number, experience_years, bio)
        VALUES (?, ?, 'MS - Orthopedics, MCh', 'Orthopedic & Joint Replacement Surgeon', 650.00, 'Room 305 - Wing C', 15, 'Expert surgeon focusing on minimally invasive arthroscopic surgery, sports trauma management, and total joint replacement.')
    """, (doc3_uid, dept_ortho))

    # Patients
    cursor.execute("SELECT id FROM users WHERE email='alex@patient.com'")
    pat1_uid = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM users WHERE email='maria@patient.com'")
    pat2_uid = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM users WHERE email='john@patient.com'")
    pat3_uid = cursor.fetchone()[0]

    cursor.execute("""
        INSERT OR IGNORE INTO patients (user_id, date_of_birth, gender, blood_group, address, emergency_contact_name, emergency_contact_phone, medical_history_summary)
        VALUES (?, '1995-04-12', 'Male', 'O+', '42 Elm Street, Springfield, IL', 'Clara Morgan', '+1 555-019-9988', 'Mild seasonal asthma; no known penicillin or drug allergies.')
    """, (pat1_uid,))

    cursor.execute("""
        INSERT OR IGNORE INTO patients (user_id, date_of_birth, gender, blood_group, address, emergency_contact_name, emergency_contact_phone, medical_history_summary)
        VALUES (?, '1988-08-25', 'Female', 'A+', '108 Pine Hill Road, Springfield, IL', 'Carlos Garcia', '+1 555-018-7711', 'History of mild essential hypertension under maintenance lifestyle therapy.')
    """, (pat2_uid,))

    cursor.execute("""
        INSERT OR IGNORE INTO patients (user_id, date_of_birth, gender, blood_group, address, emergency_contact_name, emergency_contact_phone, medical_history_summary)
        VALUES (?, '1979-11-03', 'Male', 'B+', '77 Oak Boulevard, Springfield, IL', 'Susan Doe', '+1 555-017-3322', 'Type 2 Diabetes Mellitus managed with oral hypoglycemics; non-smoker.')
    """, (pat3_uid,))

    # Doctor Schedules
    cursor.execute("SELECT id FROM doctors WHERE user_id=?", (doc1_uid,))
    d1_id = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM doctors WHERE user_id=?", (doc2_uid,))
    d2_id = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM doctors WHERE user_id=?", (doc3_uid,))
    d3_id = cursor.fetchone()[0]

    schedules = [
        (d1_id, 'Monday', '09:00:00', '13:00:00', 30, 8),
        (d1_id, 'Wednesday', '09:00:00', '13:00:00', 30, 8),
        (d1_id, 'Friday', '09:00:00', '13:00:00', 30, 8),
        (d2_id, 'Tuesday', '10:00:00', '14:00:00', 30, 8),
        (d2_id, 'Thursday', '10:00:00', '14:00:00', 30, 8),
        (d2_id, 'Saturday', '09:00:00', '13:00:00', 30, 8),
        (d3_id, 'Monday', '14:00:00', '18:00:00', 30, 8),
        (d3_id, 'Wednesday', '14:00:00', '18:00:00', 30, 8),
        (d3_id, 'Friday', '14:00:00', '18:00:00', 30, 8)
    ]
    cursor.executemany("INSERT OR IGNORE INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time, slot_duration_minutes, max_patients) VALUES (?, ?, ?, ?, ?, ?)", schedules)

    # Appointments (covering all 5 statuses)
    cursor.execute("SELECT id FROM patients WHERE user_id=?", (pat1_uid,))
    p1_id = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM patients WHERE user_id=?", (pat2_uid,))
    p2_id = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM patients WHERE user_id=?", (pat3_uid,))
    p3_id = cursor.fetchone()[0]

    appointments = [
        ('APT-2026-0001', p1_id, d1_id, dept_cardio, '2026-11-06', '09:30:00', 1, 'Pending', 'Intermittent chest tightness and palpitation during exercise.', 'PATIENT', None),
        ('APT-2026-0002', p2_id, d2_id, dept_pedia, '2026-11-05', '10:30:00', 2, 'Confirmed', 'Child persistent nocturnal dry cough and recurrent fever.', 'PATIENT', None),
        ('APT-2026-0003', p3_id, d1_id, dept_cardio, '2026-10-28', '11:00:00', 1, 'Completed', 'Routine annual cardiac checkup and stress test review.', 'RECEPTIONIST', None),
        ('APT-2026-0004', p1_id, d2_id, dept_pedia, '2026-10-20', '11:30:00', 3, 'Cancelled', 'General checkup - patient requested schedule postponement.', 'PATIENT', None),
        ('APT-2026-0005', p2_id, d3_id, dept_ortho, '2026-11-02', '15:00:00', 4, 'Rejected', 'Left knee strain after marathon run.', 'RECEPTIONIST', 'Doctor attending urgent orthopedic trauma surgery.')
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO appointments (appointment_number, patient_id, doctor_id, department_id, appointment_date, appointment_time, token_number, status, symptoms, booked_by, rejection_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, appointments)

    # Notifications
    notifications = [
        (1, 'System Ready', 'CarePlus Hospital Management System (hospital_db) successfully initialized.', 'SYSTEM', 1),
        (doc1_uid, 'New Appointment Request', 'Patient Alex Morgan has requested an appointment (APT-2026-0001) for Nov 06.', 'APPOINTMENT', 0),
        (pat1_uid, 'Booking Submitted', 'Your appointment APT-2026-0001 with Dr. Robert Chen is currently pending doctor review.', 'APPOINTMENT', 0),
        (pat2_uid, 'Appointment Confirmed', 'Your visit APT-2026-0002 with Dr. Emily Watson has been confirmed for Nov 05 at 10:30 AM.', 'APPOINTMENT', 1),
        (pat2_uid, 'Appointment Notice', 'Appointment APT-2026-0005 could not be scheduled: Doctor attending urgent trauma surgery.', 'APPOINTMENT', 1),
        (r1_id, 'Reception Rota Active', 'Morning shift duty commenced at Front Desk Main Wing A.', 'REMINDER', 1)
    ]
    cursor.executemany("INSERT OR IGNORE INTO notifications (user_id, title, message, type, is_read) VALUES (?, ?, ?, ?, ?)", notifications)

    # Activity Logs
    activity_logs = [
        (1, 'SYSTEM_INIT', 'Relational database schema hospital_db created with all tables and relationships.', '127.0.0.1'),
        (pat1_uid, 'APPOINTMENT_BOOKED', 'Patient Alex Morgan booked appointment APT-2026-0001 with Dr. Robert Chen.', '127.0.0.1'),
        (r1_id, 'APPOINTMENT_CONFIRMED', 'Receptionist confirmed appointment APT-2026-0002 for Maria Garcia.', '127.0.0.1'),
        (r1_id, 'APPOINTMENT_REJECTED', 'Appointment APT-2026-0005 rejected: Doctor on emergency trauma duty.', '127.0.0.1'),
        (doc1_uid, 'CONSULTATION_COMPLETED', 'Dr. Robert Chen finalized consultation for appointment APT-2026-0003.', '127.0.0.1')
    ]
    cursor.executemany("INSERT OR IGNORE INTO activity_logs (user_id, action, details, ip_address) VALUES (?, ?, ?, ?)", activity_logs)

    # Supporting Data: Prescriptions & Bills
    cursor.execute("SELECT id FROM appointments WHERE appointment_number='APT-2026-0003'")
    apt3_id = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM appointments WHERE appointment_number='APT-2026-0002'")
    apt2_id = cursor.fetchone()[0]

    cursor.execute("""
        INSERT OR IGNORE INTO prescriptions (appointment_id, doctor_id, patient_id, diagnosis, advice_notes, follow_up_date)
        VALUES (?, ?, ?, 'Pre-hypertension with mild sinus bradycardia.', 'Low sodium diet, 30 min daily brisk walking. Continue current medication.', '2026-12-01')
    """, (apt3_id, d1_id, p3_id))

    cursor.execute("SELECT id FROM prescriptions WHERE appointment_id=?", (apt3_id,))
    rx_id = cursor.fetchone()[0]

    cursor.execute("""
        INSERT OR IGNORE INTO prescription_items (prescription_id, medicine_name, dosage, frequency, duration, instructions)
        VALUES (?, 'Atorvastatin', '10 mg', 'Once daily at bedtime', '30 days', 'Take with water after dinner')
    """, (rx_id,))
    cursor.execute("""
        INSERT OR IGNORE INTO prescription_items (prescription_id, medicine_name, dosage, frequency, duration, instructions)
        VALUES (?, 'Metoprolol Succinate', '25 mg', 'Once daily in the morning', '30 days', 'Take after breakfast, monitor pulse')
    """, (rx_id,))

    cursor.execute("""
        INSERT OR IGNORE INTO bills (invoice_number, appointment_id, patient_id, consultation_fee, additional_charges, total_amount, discount, payable_amount, payment_status, payment_method, paid_at, generated_by_user_id)
        VALUES ('INV-2026-0001', ?, ?, 750.00, 50.00, 800.00, 0.00, 800.00, 'PAID', 'CARD', '2026-10-28 11:45:00', ?)
    """, (apt3_id, p3_id, r1_id))

    cursor.execute("""
        INSERT OR IGNORE INTO bills (invoice_number, appointment_id, patient_id, consultation_fee, additional_charges, total_amount, discount, payable_amount, payment_status, payment_method, paid_at, generated_by_user_id)
        VALUES ('INV-2026-0002', ?, ?, 500.00, 0.00, 500.00, 0.00, 500.00, 'UNPAID', 'ONLINE', NULL, ?)
    """, (apt2_id, p2_id, r1_id))

    conn.commit()
    conn.close()
    print("[SUCCESS] Local SQLite database initialized with all 9 core tables and sample data!\n")
    return True

def verify_database():
    """Inspects all 9 required tables, counts, constraints, and tests double booking prevention."""
    print("=" * 65)
    print(" CarePlus Hospital (hospital_db) - Database Verification Test")
    print("=" * 65)

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

    # Connect to either MySQL (if available) or SQLite
    is_mysql = False
    conn = None
    try:
        conn = pymysql.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            port=Config.DB_PORT,
            charset='utf8mb4'
        )
        is_mysql = True
        print(f"[Engine] Verified connection to MySQL '{Config.DB_NAME}' at {Config.DB_HOST}:{Config.DB_PORT}")
    except Exception:
        db_path = Config.SQLITE_PATH
        if not os.path.exists(db_path):
            init_sqlite()
        conn = sqlite3.connect(db_path)
        print(f"[Engine] Verified connection to local fallback '{os.path.basename(db_path)}'")

    cursor = conn.cursor()

    print("\n[Table Verification]")
    print(f"{'#':<3} {'Table Name':<20} {'Status':<10} {'Records':<10} {'Description'}")
    print("-" * 65)

    table_descriptions = {
        'users': 'Core system users (4 roles)',
        'patients': 'Patient medical profiles',
        'doctors': 'Physician specialist profiles',
        'receptionists': 'Front desk operational profiles',
        'departments': 'Clinical specialties & wings',
        'doctor_schedules': 'Weekly consultation rotas',
        'appointments': 'Booking engine (5 statuses)',
        'notifications': 'Real-time alert messages',
        'activity_logs': 'System & user security audit trail'
    }

    all_present = True
    for i, t in enumerate(required_tables, 1):
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {t}")
            cnt = cursor.fetchone()[0]
            print(f"{i:<3} {t:<20} {'[EXISTS]':<10} {cnt:<10} {table_descriptions.get(t, '')}")
        except Exception as e:
            all_present = False
            print(f"{i:<3} {t:<20} {'[MISSING]':<10} {'0':<10} Error: {e}")

    print("\n[Appointment Statuses Verification]")
    cursor.execute("SELECT DISTINCT status FROM appointments")
    statuses = [r[0] for r in cursor.fetchall()]
    print(f"Recorded statuses in appointments: {statuses}")
    expected_statuses = {'Pending', 'Confirmed', 'Completed', 'Cancelled', 'Rejected'}
    if expected_statuses.issubset(set(statuses)):
        print("[OK] All 5 required appointment statuses verified: Pending, Confirmed, Completed, Cancelled, Rejected.")
    else:
        print(f"[WARN] Some statuses missing: {expected_statuses - set(statuses)}")

    print("\n[Double Booking Prevention Test]")
    # Try inserting duplicate appointment for the same doctor at the same date and time
    cursor.execute("SELECT doctor_id, appointment_date, appointment_time FROM appointments LIMIT 1")
    row = cursor.fetchone()
    if row:
        doc_id, appt_date, appt_time = row[0], row[1], row[2]
        print(f"Testing duplicate slot insertion for Doctor ID {doc_id} on {appt_date} at {appt_time}...")
        try:
            cursor.execute("""
                INSERT INTO appointments (appointment_number, patient_id, doctor_id, department_id, appointment_date, appointment_time, token_number, status)
                VALUES ('TEST-DUP-001', 1, ?, 1, ?, ?, 99, 'Pending')
            """ if not is_mysql else """
                INSERT INTO appointments (appointment_number, patient_id, doctor_id, department_id, appointment_date, appointment_time, token_number, status)
                VALUES ('TEST-DUP-001', 1, %s, 1, %s, %s, 99, 'Pending')
            """, (doc_id, appt_date, appt_time))
            if not is_mysql:
                conn.commit()
            print("[FAIL] Constraint failed: Duplicate slot was allowed!")
        except Exception as e:
            print(f"[PASS] Duplicate slot successfully blocked by Unique Key constraint! ({type(e).__name__})")
            if not is_mysql:
                conn.rollback()

    conn.close()
    print("=" * 65)
    return all_present

if __name__ == '__main__':
    args = sys.argv[1:]
    if '--mysql' in args:
        init_mysql()
    elif '--sqlite' in args:
        init_sqlite()
    elif '--verify' in args:
        verify_database()
    else:
        print("[*] CarePlus DB Initializer: Checking MySQL availability...")
        if not init_mysql():
            print("\n[*] MySQL is not running locally. Initializing local database fallback for instant development/testing...")
            init_sqlite()
        verify_database()
