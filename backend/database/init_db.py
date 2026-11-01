"""
CarePlus Hospital - Database Initialization Utility
Creates the database schema and populates seed data for MySQL (or SQLite fallback).
Usage:
    python init_db.py          (Default: tries MySQL, falls back to SQLite if MySQL is unavailable)
    python init_db.py --mysql  (Forces MySQL setup)
    python init_db.py --sqlite (Initializes standalone SQLite database for instant evaluation)
"""
import sys
import os
import pymysql
import sqlite3
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Ensure app directory is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import Config

def init_mysql():
    """Initializes MySQL database using schema.sql and seed_data.sql."""
    print(f"Connecting to MySQL server at {Config.DB_HOST}:{Config.DB_PORT} as '{Config.DB_USER}'...")
    try:
        conn = pymysql.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            port=Config.DB_PORT,
            charset='utf8mb4'
        )
        with conn.cursor() as cursor:
            print(f"Creating database '{Config.DB_NAME}' if not exists...")
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            cursor.execute(f"USE {Config.DB_NAME};")
            
            schema_file = os.path.join(os.path.dirname(__file__), 'schema.sql')
            seed_file = os.path.join(os.path.dirname(__file__), 'seed_data.sql')
            
            print("Executing schema.sql...")
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
                # Split queries by semicolon
                statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
                for stmt in statements:
                    cursor.execute(stmt)

            print("Executing seed_data.sql...")
            with open(seed_file, 'r', encoding='utf-8') as f:
                seed_sql = f.read()
                statements = [stmt.strip() for stmt in seed_sql.split(';') if stmt.strip()]
                for stmt in statements:
                    cursor.execute(stmt)
                    
            conn.commit()
        conn.close()
        print("\nSUCCESS: MySQL database initialized and seeded successfully!")
        return True
    except Exception as e:
        print(f"\n[MySQL Error]: {e}")
        return False

def init_sqlite():
    """Initializes an SQLite database for seamless offline academic demonstration."""
    db_path = os.path.join(os.path.dirname(__file__), 'careplus_hospital.db')
    print(f"Initializing SQLite database at: {db_path}...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.executescript("""
    PRAGMA foreign_keys = ON;

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

    CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        icon_class TEXT DEFAULT 'bi-heart-pulse',
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

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
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS doctor_schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_id INTEGER NOT NULL,
        day_of_week TEXT CHECK(day_of_week IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')) NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        slot_duration_minutes INTEGER DEFAULT 20,
        max_patients INTEGER DEFAULT 20,
        is_available INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE,
        UNIQUE (doctor_id, day_of_week)
    );

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
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_number TEXT NOT NULL UNIQUE,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        department_id INTEGER NOT NULL,
        appointment_date TEXT NOT NULL,
        appointment_time TEXT NOT NULL,
        token_number INTEGER NOT NULL,
        status TEXT CHECK(status IN ('PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED', 'NO_SHOW')) DEFAULT 'PENDING',
        symptoms TEXT,
        booked_by TEXT CHECK(booked_by IN ('PATIENT', 'RECEPTIONIST', 'ADMIN')) DEFAULT 'PATIENT',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
        FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE RESTRICT,
        FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS prescriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_id INTEGER NOT NULL UNIQUE,
        doctor_id INTEGER NOT NULL,
        patient_id INTEGER NOT NULL,
        diagnosis TEXT NOT NULL,
        advice_notes TEXT,
        follow_up_date TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
        FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE,
        FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
        FOREIGN KEY (generated_by_user_id) REFERENCES users(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        details TEXT,
        ip_address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """)

    # Seed core data
    pw_admin = generate_password_hash("Admin@123")
    pw_doctor = generate_password_hash("Doctor@123")
    pw_reception = generate_password_hash("Reception@123")
    pw_patient = generate_password_hash("Patient@123")

    # Departments
    departments = [
        ('Cardiology', 'Heart health, cardiovascular diagnostics, and hypertension care.', 'bi-heart-pulse'),
        ('Neurology', 'Brain, nerve, and spinal system disorders and therapy.', 'bi-activity'),
        ('Pediatrics', 'Comprehensive child healthcare and infant immunization.', 'bi-person-heart'),
        ('Orthopedics', 'Bones, joints, ligaments, and sports injury recovery.', 'bi-bandaid'),
        ('Dermatology', 'Skin, hair, allergy treatment, and cosmetic dermatology.', 'bi-emoji-smile'),
        ('General Medicine', 'Primary care, fever, routine checkups, and chronic diseases.', 'bi-clipboard2-pulse')
    ]
    cursor.executemany("INSERT OR IGNORE INTO departments (name, description, icon_class) VALUES (?, ?, ?)", departments)

    # Users
    users = [
        ('Hospital Administrator', 'admin@careplus.com', pw_admin, 'admin', '+1 800-555-0199'),
        ('Sarah Jenkins (Reception Desk)', 'reception@careplus.com', pw_reception, 'receptionist', '+1 800-555-0102'),
        ('Dr. Robert Chen, MD', 'dr.chen@careplus.com', pw_doctor, 'doctor', '+1 800-555-0144'),
        ('Dr. Emily Watson, MBBS', 'dr.watson@careplus.com', pw_doctor, 'doctor', '+1 800-555-0177'),
        ('Alex Morgan', 'alex@patient.com', pw_patient, 'patient', '+1 555-019-2834')
    ]
    for u in users:
        cursor.execute("INSERT OR IGNORE INTO users (full_name, email, password_hash, role, phone) VALUES (?, ?, ?, ?, ?)", u)

    conn.commit()

    # Link Doctors
    cursor.execute("SELECT id FROM users WHERE email='dr.chen@careplus.com'")
    chen_uid = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM departments WHERE name='Cardiology'")
    cardio_id = cursor.fetchone()[0]
    cursor.execute("""
        INSERT OR IGNORE INTO doctors (user_id, department_id, qualification, specialization, consultation_fee, room_number, experience_years, bio)
        VALUES (?, ?, 'MD - Cardiology, FACC', 'Interventional Cardiologist', 750.00, 'Room 101 - Wing A', 12, 'Over a decade of clinical experience in coronary intervention, hypertension and preventative cardiovascular therapy.')
    """, (chen_uid, cardio_id))

    cursor.execute("SELECT id FROM users WHERE email='dr.watson@careplus.com'")
    watson_uid = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM departments WHERE name='Pediatrics'")
    pedia_id = cursor.fetchone()[0]
    cursor.execute("""
        INSERT OR IGNORE INTO doctors (user_id, department_id, qualification, specialization, consultation_fee, room_number, experience_years, bio)
        VALUES (?, ?, 'MBBS, MD - Pediatrics', 'Senior Pediatrician & Neonatologist', 500.00, 'Room 204 - Wing B', 8, 'Specialist in developmental pediatrics, childhood immunization schedules, and infant health care.')
    """, (watson_uid, pedia_id))

    # Link Patient Profile
    cursor.execute("SELECT id FROM users WHERE email='alex@patient.com'")
    alex_uid = cursor.fetchone()[0]
    cursor.execute("""
        INSERT OR IGNORE INTO patients (user_id, date_of_birth, gender, blood_group, address, emergency_contact_name, emergency_contact_phone, medical_history_summary)
        VALUES (?, '1995-04-12', 'Male', 'O+', '42 Elm Street, Springfield, IL', 'Clara Morgan', '+1 555-019-9988', 'Mild seasonal asthma, no known drug allergies.')
    """, (alex_uid,))

    # Insert Doctor Schedules
    cursor.execute("SELECT id FROM doctors WHERE user_id=?", (chen_uid,))
    chen_doc_id = cursor.fetchone()[0]
    schedules = [
        (chen_doc_id, 'Monday', '09:00', '13:00', 30, 8),
        (chen_doc_id, 'Wednesday', '09:00', '13:00', 30, 8),
        (chen_doc_id, 'Friday', '09:00', '13:00', 30, 8)
    ]
    cursor.executemany("INSERT OR IGNORE INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time, slot_duration_minutes, max_patients) VALUES (?, ?, ?, ?, ?, ?)", schedules)

    conn.commit()
    conn.close()
    print("SUCCESS: SQLite database initialized and seeded successfully!\n")
    return True

if __name__ == '__main__':
    args = sys.argv[1:]
    if '--mysql' in args:
        init_mysql()
    elif '--sqlite' in args:
        init_sqlite()
    else:
        # Default smart strategy: Attempt MySQL first; if unavailable, auto-initialize SQLite
        print("CarePlus DB Initializer: Checking MySQL availability...")
        if not init_mysql():
            print("\nMySQL is not running locally. Initializing local database fallback for instant development/testing...")
            init_sqlite()
