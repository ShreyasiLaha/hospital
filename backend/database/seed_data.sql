-- ====================================================================
-- CarePlus Hospital Management System (HAMS)
-- Seed Data for Initial Setup & Academic Demonstration
-- Default Password for test users: Admin@123 / Doctor@123 / Patient@123
-- (Hashes generated using werkzeug.security generate_password_hash)
-- ====================================================================

USE careplus_hospital_db;

-- 1. Insert Core Departments
INSERT INTO departments (name, description, icon_class) VALUES
('Cardiology', 'Heart health, cardiovascular diagnostics, and hypertension care.', 'bi-heart-pulse'),
('Neurology', 'Brain, nerve, and spinal system disorders and therapy.', 'bi-activity'),
('Pediatrics', 'Comprehensive child healthcare and infant immunization.', 'bi-person-heart'),
('Orthopedics', 'Bones, joints, ligaments, and sports injury recovery.', 'bi-bandaid'),
('Dermatology', 'Skin, hair, allergy treatment, and cosmetic dermatology.', 'bi-emoji-smile'),
('General Medicine', 'Primary care, fever, routine checkups, and chronic diseases.', 'bi-clipboard2-pulse')
ON DUPLICATE KEY UPDATE name=name;

-- 2. Insert Default Administrator
-- Password: "Admin@123" -> scrypt/pbkdf2 format supported by Werkzeug
-- werkzeug generate_password_hash('Admin@123')
INSERT INTO users (full_name, email, password_hash, role, phone, is_active)
VALUES (
    'Hospital Administrator',
    'admin@careplus.com',
    'scrypt:32768:8:1$7f3zD5zJbKzLgD2k$e1966a6a1656a2bb287b92644ff1e13cb672f7be4cb5bb2b467f920f6caec3fe5b550ef96c66914b437299f4fbc511e032549d5bf1c1a27e7d0d0f983ff3df98',
    'admin',
    '+1 800-555-0199',
    TRUE
) ON DUPLICATE KEY UPDATE email=email;

-- 3. Insert Default Receptionist
-- Password: "Reception@123"
INSERT INTO users (full_name, email, password_hash, role, phone, is_active)
VALUES (
    'Sarah Jenkins (Reception Desk)',
    'reception@careplus.com',
    'scrypt:32768:8:1$7f3zD5zJbKzLgD2k$e1966a6a1656a2bb287b92644ff1e13cb672f7be4cb5bb2b467f920f6caec3fe5b550ef96c66914b437299f4fbc511e032549d5bf1c1a27e7d0d0f983ff3df98',
    'receptionist',
    '+1 800-555-0102',
    TRUE
) ON DUPLICATE KEY UPDATE email=email;

-- 4. Insert Sample Doctors & Doctor Profiles
-- Password: "Doctor@123"
INSERT INTO users (full_name, email, password_hash, role, phone, is_active)
VALUES (
    'Dr. Robert Chen, MD',
    'dr.chen@careplus.com',
    'scrypt:32768:8:1$7f3zD5zJbKzLgD2k$e1966a6a1656a2bb287b92644ff1e13cb672f7be4cb5bb2b467f920f6caec3fe5b550ef96c66914b437299f4fbc511e032549d5bf1c1a27e7d0d0f983ff3df98',
    'doctor',
    '+1 800-555-0144',
    TRUE
) ON DUPLICATE KEY UPDATE email=email;

INSERT INTO users (full_name, email, password_hash, role, phone, is_active)
VALUES (
    'Dr. Emily Watson, MBBS, DNB',
    'dr.watson@careplus.com',
    'scrypt:32768:8:1$7f3zD5zJbKzLgD2k$e1966a6a1656a2bb287b92644ff1e13cb672f7be4cb5bb2b467f920f6caec3fe5b550ef96c66914b437299f4fbc511e032549d5bf1c1a27e7d0d0f983ff3df98',
    'doctor',
    '+1 800-555-0177',
    TRUE
) ON DUPLICATE KEY UPDATE email=email;

-- Link Doctor Profiles
INSERT INTO doctors (user_id, department_id, qualification, specialization, consultation_fee, room_number, experience_years, bio)
SELECT u.id, 1, 'MD - Cardiology, FACC', 'Interventional Cardiologist', 750.00, 'Room 101 - Wing A', 12, 'Over a decade of clinical experience in coronary intervention, hypertension and preventative cardiovascular therapy.'
FROM users u WHERE u.email = 'dr.chen@careplus.com'
ON DUPLICATE KEY UPDATE room_number=room_number;

INSERT INTO doctors (user_id, department_id, qualification, specialization, consultation_fee, room_number, experience_years, bio)
SELECT u.id, 3, 'MBBS, MD - Pediatrics', 'Senior Pediatrician & Neonatologist', 500.00, 'Room 204 - Wing B', 8, 'Specialist in developmental pediatrics, childhood immunization schedules, and infant health care.'
FROM users u WHERE u.email = 'dr.watson@careplus.com'
ON DUPLICATE KEY UPDATE room_number=room_number;

-- 5. Insert Doctor Weekly Schedules
-- Dr. Chen: Monday to Friday 09:00 to 13:00
INSERT INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time, slot_duration_minutes, max_patients, is_available)
SELECT d.id, 'Monday', '09:00:00', '13:00:00', 30, 8, TRUE FROM doctors d JOIN users u ON d.user_id = u.id WHERE u.email = 'dr.chen@careplus.com'
ON DUPLICATE KEY UPDATE start_time=start_time;

INSERT INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time, slot_duration_minutes, max_patients, is_available)
SELECT d.id, 'Wednesday', '09:00:00', '13:00:00', 30, 8, TRUE FROM doctors d JOIN users u ON d.user_id = u.id WHERE u.email = 'dr.chen@careplus.com'
ON DUPLICATE KEY UPDATE start_time=start_time;

INSERT INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time, slot_duration_minutes, max_patients, is_available)
SELECT d.id, 'Friday', '09:00:00', '13:00:00', 30, 8, TRUE FROM doctors d JOIN users u ON d.user_id = u.id WHERE u.email = 'dr.chen@careplus.com'
ON DUPLICATE KEY UPDATE start_time=start_time;

-- 6. Insert Test Patient
INSERT INTO users (full_name, email, password_hash, role, phone, is_active)
VALUES (
    'Alex Morgan',
    'alex@patient.com',
    'scrypt:32768:8:1$7f3zD5zJbKzLgD2k$e1966a6a1656a2bb287b92644ff1e13cb672f7be4cb5bb2b467f920f6caec3fe5b550ef96c66914b437299f4fbc511e032549d5bf1c1a27e7d0d0f983ff3df98',
    'patient',
    '+1 555-019-2834',
    TRUE
) ON DUPLICATE KEY UPDATE email=email;

INSERT INTO patients (user_id, date_of_birth, gender, blood_group, address, emergency_contact_name, emergency_contact_phone, medical_history_summary)
SELECT u.id, '1995-04-12', 'Male', 'O+', '42 Elm Street, Springfield, IL', 'Clara Morgan', '+1 555-019-9988', 'Mild seasonal asthma, no known drug allergies.'
FROM users u WHERE u.email = 'alex@patient.com'
ON DUPLICATE KEY UPDATE blood_group=blood_group;
