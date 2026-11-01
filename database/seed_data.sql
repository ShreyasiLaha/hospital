-- ====================================================================
-- CarePlus Hospital Management System (HAMS)
-- Database Name: hospital_db
-- Seed Demonstration Data for All 4 Roles & 9 Core Tables
--
-- Demonstration Credentials:
-- Admin:        admin@careplus.com      / Admin@123
-- Receptionist: reception@careplus.com  / Reception@123
-- Receptionist: reception2@careplus.com / Reception@123
-- Doctor:       dr.chen@careplus.com    / Doctor@123
-- Doctor:       dr.watson@careplus.com  / Doctor@123
-- Doctor:       dr.kumar@careplus.com   / Doctor@123
-- Patient:      alex@patient.com        / Patient@123
-- Patient:      maria@patient.com       / Patient@123
-- Patient:      john@patient.com        / Patient@123
-- ====================================================================

USE hospital_db;

-- --------------------------------------------------------------------
-- 1. Seed Departments (Fictional Clinical Specialties)
-- --------------------------------------------------------------------
INSERT INTO departments (id, name, description, icon_class, is_active) VALUES
(1, 'Cardiology', 'Heart health, cardiovascular diagnostics, ECG, and hypertension care.', 'bi-heart-pulse', TRUE),
(2, 'Neurology', 'Brain, nerve, migraine, stroke rehabilitation, and spinal therapy.', 'bi-activity', TRUE),
(3, 'Pediatrics', 'Comprehensive infant healthcare, developmental pediatrics, and immunization.', 'bi-person-heart', TRUE),
(4, 'Orthopedics', 'Bones, joints, arthritis treatment, ligaments, and sports injury recovery.', 'bi-bandaid', TRUE),
(5, 'Dermatology', 'Skin, hair, eczema, allergy diagnostics, and cosmetic dermatology.', 'bi-emoji-smile', TRUE),
(6, 'General Medicine', 'Primary outpatient care, seasonal fever, diagnostic health checkups, and wellness.', 'bi-clipboard2-pulse', TRUE)
ON DUPLICATE KEY UPDATE name=VALUES(name), description=VALUES(description);

-- --------------------------------------------------------------------
-- 2. Seed Users (Covering all 4 Roles: admin, doctor, receptionist, patient)
-- --------------------------------------------------------------------
INSERT INTO users (id, full_name, email, password_hash, role, phone, is_active) VALUES
(1, 'Hospital Administrator', 'admin@careplus.com', 'scrypt:32768:8:1$ZdXstTG5dQ3MiDJx$5ddd65c85cd7df3a3540a20255da0039da878d2f46dc3298668b1549e362ffd97254d4d6c7ce1990ef74eccdab89949ea274754585eb8d90eb7de6af38fb8fff', 'admin', '+1 800-555-0199', TRUE),
(2, 'Sarah Jenkins', 'reception@careplus.com', 'scrypt:32768:8:1$oQZStGY3be8RCFkj$a149be6a5321db72eedbdcb238400635b3d920820ff8106d153ff4ab7b71cf180151d6b4fe7c45940fa15edd021732f69692c46402956a005b3ff4579d9c2393', 'receptionist', '+1 800-555-0102', TRUE),
(3, 'David Miller', 'reception2@careplus.com', 'scrypt:32768:8:1$oQZStGY3be8RCFkj$a149be6a5321db72eedbdcb238400635b3d920820ff8106d153ff4ab7b71cf180151d6b4fe7c45940fa15edd021732f69692c46402956a005b3ff4579d9c2393', 'receptionist', '+1 800-555-0103', TRUE),
(4, 'Dr. Robert Chen, MD', 'dr.chen@careplus.com', 'scrypt:32768:8:1$D6DNEdAb9myt1Dec$e6235a4b3ba4dff947541c863e34bdcbac2643c8f654de146c5492cba6a84c34428f35ad4fd531def86cf18ccfb9157255fbf42e207a1898c65093ecb8ada1ed', 'doctor', '+1 800-555-0144', TRUE),
(5, 'Dr. Emily Watson, MBBS', 'dr.watson@careplus.com', 'scrypt:32768:8:1$D6DNEdAb9myt1Dec$e6235a4b3ba4dff947541c863e34bdcbac2643c8f654de146c5492cba6a84c34428f35ad4fd531def86cf18ccfb9157255fbf42e207a1898c65093ecb8ada1ed', 'doctor', '+1 800-555-0177', TRUE),
(6, 'Dr. Rajesh Kumar, MS', 'dr.kumar@careplus.com', 'scrypt:32768:8:1$D6DNEdAb9myt1Dec$e6235a4b3ba4dff947541c863e34bdcbac2643c8f654de146c5492cba6a84c34428f35ad4fd531def86cf18ccfb9157255fbf42e207a1898c65093ecb8ada1ed', 'doctor', '+1 800-555-0188', TRUE),
(7, 'Alex Morgan', 'alex@patient.com', 'scrypt:32768:8:1$O4u9FHIiKaOBrs9z$a312d6a28034cd9df9aa19ac8c60a26520c455ed9f0dcd8f50d09f700f5499377c409a2424512d759ce1e5dba45b8a90f3cd373470e9173c27408a119444d3fb', 'patient', '+1 555-019-2834', TRUE),
(8, 'Maria Garcia', 'maria@patient.com', 'scrypt:32768:8:1$O4u9FHIiKaOBrs9z$a312d6a28034cd9df9aa19ac8c60a26520c455ed9f0dcd8f50d09f700f5499377c409a2424512d759ce1e5dba45b8a90f3cd373470e9173c27408a119444d3fb', 'patient', '+1 555-018-7711', TRUE),
(9, 'John Doe', 'john@patient.com', 'scrypt:32768:8:1$O4u9FHIiKaOBrs9z$a312d6a28034cd9df9aa19ac8c60a26520c455ed9f0dcd8f50d09f700f5499377c409a2424512d759ce1e5dba45b8a90f3cd373470e9173c27408a119444d3fb', 'patient', '+1 555-017-3322', TRUE)
ON DUPLICATE KEY UPDATE full_name=VALUES(full_name), phone=VALUES(phone);

-- --------------------------------------------------------------------
-- 3. Seed Receptionists (Front Desk Staff Profiles)
-- --------------------------------------------------------------------
INSERT INTO receptionists (id, user_id, desk_number, shift, qualification) VALUES
(1, 2, 'Front Desk - Main Wing A', 'Morning', 'B.Sc Healthcare Administration'),
(2, 3, 'Front Desk - OPD Wing B', 'Evening', 'Diploma in Hospital Front Office Management')
ON DUPLICATE KEY UPDATE desk_number=VALUES(desk_number), shift=VALUES(shift);

-- --------------------------------------------------------------------
-- 4. Seed Doctors (Clinical Specialist Profiles)
-- --------------------------------------------------------------------
INSERT INTO doctors (id, user_id, department_id, qualification, specialization, consultation_fee, room_number, experience_years, bio) VALUES
(1, 4, 1, 'MD - Cardiology, FACC', 'Interventional Cardiologist', 750.00, 'Room 101 - Wing A', 12, 'Over 12 years of clinical expertise in coronary interventions, hypertension therapy, and preventative cardiology.'),
(2, 5, 3, 'MBBS, MD - Pediatrics', 'Senior Pediatrician & Neonatologist', 500.00, 'Room 204 - Wing B', 8, 'Dedicated pediatrician specialized in neonatal intensive care, child nutrition, and preventative vaccination programs.'),
(3, 6, 4, 'MS - Orthopedics, MCh', 'Orthopedic & Joint Replacement Surgeon', 650.00, 'Room 305 - Wing C', 15, 'Expert surgeon focusing on minimally invasive arthroscopic surgery, sports trauma management, and total joint replacement.')
ON DUPLICATE KEY UPDATE consultation_fee=VALUES(consultation_fee), room_number=VALUES(room_number);

-- --------------------------------------------------------------------
-- 5. Seed Patients (Demographics, Blood Groups & Emergency Contacts)
-- --------------------------------------------------------------------
INSERT INTO patients (id, user_id, date_of_birth, gender, blood_group, address, emergency_contact_name, emergency_contact_phone, medical_history_summary) VALUES
(1, 7, '1995-04-12', 'Male', 'O+', '42 Elm Street, Springfield, IL', 'Clara Morgan', '+1 555-019-9988', 'Mild seasonal asthma; no known penicillin or drug allergies.'),
(2, 8, '1988-08-25', 'Female', 'A+', '108 Pine Hill Road, Springfield, IL', 'Carlos Garcia', '+1 555-018-7711', 'History of mild essential hypertension under maintenance lifestyle therapy.'),
(3, 9, '1979-11-03', 'Male', 'B+', '77 Oak Boulevard, Springfield, IL', 'Susan Doe', '+1 555-017-3322', 'Type 2 Diabetes Mellitus managed with oral hypoglycemics; non-smoker.')
ON DUPLICATE KEY UPDATE address=VALUES(address), emergency_contact_name=VALUES(emergency_contact_name);

-- --------------------------------------------------------------------
-- 6. Seed Doctor Schedules (Consultation Days & Roster Hours)
-- --------------------------------------------------------------------
INSERT INTO doctor_schedules (id, doctor_id, day_of_week, start_time, end_time, slot_duration_minutes, max_patients, is_available) VALUES
(1, 1, 'Monday', '09:00:00', '13:00:00', 30, 8, TRUE),
(2, 1, 'Wednesday', '09:00:00', '13:00:00', 30, 8, TRUE),
(3, 1, 'Friday', '09:00:00', '13:00:00', 30, 8, TRUE),
(4, 2, 'Tuesday', '10:00:00', '14:00:00', 30, 8, TRUE),
(5, 2, 'Thursday', '10:00:00', '14:00:00', 30, 8, TRUE),
(6, 2, 'Saturday', '09:00:00', '13:00:00', 30, 8, TRUE),
(7, 3, 'Monday', '14:00:00', '18:00:00', 30, 8, TRUE),
(8, 3, 'Wednesday', '14:00:00', '18:00:00', 30, 8, TRUE),
(9, 3, 'Friday', '14:00:00', '18:00:00', 30, 8, TRUE)
ON DUPLICATE KEY UPDATE start_time=VALUES(start_time), end_time=VALUES(end_time);

-- --------------------------------------------------------------------
-- 7. Seed Appointments (Covering All 5 Statuses & Double Booking Prevention)
-- Statuses: Pending, Confirmed, Completed, Cancelled, Rejected
-- --------------------------------------------------------------------
INSERT INTO appointments (id, appointment_number, patient_id, doctor_id, department_id, appointment_date, appointment_time, token_number, status, symptoms, booked_by, rejection_reason) VALUES
(1, 'APT-2026-0001', 1, 1, 1, '2026-11-06', '09:30:00', 1, 'Pending', 'Intermittent chest tightness and palpitation during exercise.', 'PATIENT', NULL),
(2, 'APT-2026-0002', 2, 2, 3, '2026-11-05', '10:30:00', 2, 'Confirmed', 'Child persistent nocturnal dry cough and recurrent fever.', 'PATIENT', NULL),
(3, 'APT-2026-0003', 3, 1, 1, '2026-10-28', '11:00:00', 1, 'Completed', 'Routine annual cardiac checkup and stress test review.', 'RECEPTIONIST', NULL),
(4, 'APT-2026-0004', 1, 2, 3, '2026-10-20', '11:30:00', 3, 'Cancelled', 'General checkup - patient requested schedule postponement.', 'PATIENT', NULL),
(5, 'APT-2026-0005', 2, 3, 4, '2026-11-02', '15:00:00', 4, 'Rejected', 'Left knee strain after marathon run.', 'RECEPTIONIST', 'Doctor attending urgent orthopedic trauma surgery.')
ON DUPLICATE KEY UPDATE status=VALUES(status), symptoms=VALUES(symptoms);

-- --------------------------------------------------------------------
-- 8. Seed Notifications (In-App Alerts for Users)
-- --------------------------------------------------------------------
INSERT INTO notifications (id, user_id, title, message, type, is_read) VALUES
(1, 1, 'System Ready', 'CarePlus Hospital Management System (hospital_db) successfully initialized.', 'SYSTEM', TRUE),
(2, 4, 'New Appointment Request', 'Patient Alex Morgan has requested an appointment (APT-2026-0001) for Nov 06.', 'APPOINTMENT', FALSE),
(3, 7, 'Booking Submitted', 'Your appointment APT-2026-0001 with Dr. Robert Chen is currently pending doctor review.', 'APPOINTMENT', FALSE),
(4, 8, 'Appointment Confirmed', 'Your visit APT-2026-0002 with Dr. Emily Watson has been confirmed for Nov 05 at 10:30 AM.', 'APPOINTMENT', TRUE),
(5, 8, 'Appointment Notice', 'Appointment APT-2026-0005 could not be scheduled: Doctor attending urgent trauma surgery.', 'APPOINTMENT', TRUE),
(6, 2, 'Reception Rota Active', 'Morning shift duty commenced at Front Desk Main Wing A.', 'REMINDER', TRUE)
ON DUPLICATE KEY UPDATE title=VALUES(title);

-- --------------------------------------------------------------------
-- 9. Seed Activity Logs (Operational Audit Trail)
-- --------------------------------------------------------------------
INSERT INTO activity_logs (id, user_id, action, details, ip_address) VALUES
(1, 1, 'SYSTEM_INIT', 'Relational database schema hospital_db created with all tables and relationships.', '127.0.0.1'),
(2, 7, 'APPOINTMENT_BOOKED', 'Patient Alex Morgan booked appointment APT-2026-0001 with Dr. Robert Chen.', '127.0.0.1'),
(3, 2, 'APPOINTMENT_CONFIRMED', 'Receptionist confirmed appointment APT-2026-0002 for Maria Garcia.', '127.0.0.1'),
(4, 2, 'APPOINTMENT_REJECTED', 'Appointment APT-2026-0005 rejected: Doctor on emergency trauma duty.', '127.0.0.1'),
(5, 4, 'CONSULTATION_COMPLETED', 'Dr. Robert Chen finalized consultation for appointment APT-2026-0003.', '127.0.0.1')
ON DUPLICATE KEY UPDATE action=VALUES(action);

-- --------------------------------------------------------------------
-- Supporting Data: Prescriptions & Billing Records
-- --------------------------------------------------------------------
INSERT INTO prescriptions (id, appointment_id, doctor_id, patient_id, diagnosis, advice_notes, follow_up_date) VALUES
(1, 3, 1, 3, 'Pre-hypertension with mild sinus bradycardia.', 'Low sodium diet, 30 min daily brisk walking. Continue current medication.', '2026-12-01')
ON DUPLICATE KEY UPDATE diagnosis=VALUES(diagnosis);

INSERT INTO prescription_items (id, prescription_id, medicine_name, dosage, frequency, duration, instructions) VALUES
(1, 1, 'Atorvastatin', '10 mg', 'Once daily at bedtime', '30 days', 'Take with water after dinner'),
(2, 1, 'Metoprolol Succinate', '25 mg', 'Once daily in the morning', '30 days', 'Take after breakfast, monitor pulse')
ON DUPLICATE KEY UPDATE medicine_name=VALUES(medicine_name);

INSERT INTO bills (id, invoice_number, appointment_id, patient_id, consultation_fee, additional_charges, total_amount, discount, payable_amount, payment_status, payment_method, paid_at, generated_by_user_id) VALUES
(1, 'INV-2026-0001', 3, 3, 750.00, 50.00, 800.00, 0.00, 800.00, 'PAID', 'CARD', '2026-10-28 11:45:00', 2),
(2, 'INV-2026-0002', 2, 2, 500.00, 0.00, 500.00, 0.00, 500.00, 'UNPAID', 'ONLINE', NULL, 2)
ON DUPLICATE KEY UPDATE payment_status=VALUES(payment_status);
