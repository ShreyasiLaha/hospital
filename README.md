# CarePlus Hospital — Hospital Appointment Management System (HAMS)

An enterprise-standard, full-stack Hospital Appointment Management System built with **HTML5, CSS3, JavaScript, Bootstrap 5, Python Flask, and MySQL**.

The codebase is organized into **2 dedicated layers**:
1. **`backend/`**: Python Flask controllers, Blueprints, database connection pool, security decorators, and schema scripts.
2. **`frontend/`**: Presentation layer containing all HTML5 Jinja2 templates, Bootstrap 5 views, CSS design tokens, dynamic JavaScript scripts, and SVG logos.

---

## 📁 2-Folder Clean Architecture

```text
hospital/
│
├── backend/                              # ================= BACKEND LAYER =================
│   ├── app/
│   │   ├── __init__.py                   # Application Factory (binds frontend templates & static)
│   │   ├── db.py                         # PyMySQL connection pool & query helpers
│   │   ├── routes/
│   │   │   ├── auth.py                   # Unified login, patient sign-up, session logout
│   │   │   ├── patient.py                # Patient portal routes (booking, appointments, Rx, bills)
│   │   │   ├── doctor.py                 # Doctor workspace routes (queue, timetable, prescriptions)
│   │   │   ├── receptionist.py           # Receptionist desk routes (walk-ins, queue, cashier billing)
│   │   │   ├── admin.py                  # Admin executive analytics, user CRUD, reports
│   │   │   └── api.py                    # Asynchronous JSON endpoints (slots, doctors)
│   │   └── utils/
│   │       ├── decorators.py             # @role_required, @login_required RBAC guards
│   │       └── helpers.py                # Token generators, invoice IDs, currency formatters
│   │
│   ├── database/
│   │   ├── schema.sql                    # Full relational schema (10 InnoDB tables with FK constraints)
│   │   ├── seed_data.sql                 # Demo accounts, departments, and sample doctors
│   │   ├── init_db.py                    # Database initialization & setup script
│   │   └── careplus_hospital.db          # Offline SQLite database fallback
│   │
│   ├── tests/
│   │   └── test_flow.py                  # Automated 7-step end-to-end integration test suite
│   ├── config.py                         # Central environment configuration
│   ├── requirements.txt                  # Python dependencies
│   ├── .env.example                      # Environment variables template
│   └── run.py                            # Backend server runner (can be run directly inside backend/)
│
├── frontend/                             # ================ FRONTEND LAYER =================
│   ├── static/
│   │   ├── css/
│   │   │   ├── main.css                  # Core CSS variables, medical color tokens, status badges
│   │   │   └── dashboard.css             # Sidebar layout, metric cards, table aesthetics
│   │   ├── js/
│   │   │   ├── main.js                   # Toast alerts, modals, confirmation popups
│   │   │   ├── booking.js                # Dynamic slot calculation and validation
│   │   │   └── prescription.js           # Dynamic medication item row builder
│   │   └── img/
│   │       └── logo.svg                  # CarePlus Hospital vector brand logo
│   │
│   └── templates/
│       ├── base.html                     # Master layout with Bootstrap 5 CDN & Bootstrap Icons
│       ├── dashboard_base.html           # Reusable dashboard layout with role-aware sidebar
│       ├── index.html                    # Public hospital homepage with role quick-links
│       ├── components/
│       │   ├── navbar.html               # Role-aware navigation header
│       │   ├── sidebar.html              # Dynamic sidebar navigation tailored to each actor
│       │   ├── footer.html               # Standard clinical footer
│       │   └── flash_messages.html       # Animated status message banners
│       ├── auth/
│       │   ├── login.html                # Unified login screen with quick test credentials
│       │   ├── register.html             # Patient registration portal
│       │   └── change_password.html      # Password change screen
│       ├── patient/
│       │   ├── dashboard.html            # Patient summary metrics & upcoming visit
│       │   ├── book_appointment.html     # Multi-step booking engine (Dept -> Doctor -> Slot)
│       │   ├── my_appointments.html      # Booking history & status tracker
│       │   ├── prescriptions.html        # Prescription vault
│       │   └── bills.html                # Invoices and payment receipts
│       ├── doctor/
│       │   ├── dashboard.html            # Doctor command center & today's queue
│       │   ├── appointments.html         # Consultation roster
│       │   ├── schedule.html             # Weekly working hours configuration
│       │   └── write_prescription.html   # Clinical Rx pad with dynamic drug rows
│       ├── receptionist/
│       │   ├── dashboard.html            # Front-desk summary & waiting room
│       │   ├── walkin_booking.html       # Walk-in patient instant booking
│       │   ├── queue.html                # Live token check-in manager
│       │   └── billing.html              # Cashier invoicing and payment desk
│       ├── admin/
│       │   ├── dashboard.html            # Executive analytics & metrics
│       │   ├── manage_users.html         # Doctor and receptionist CRUD
│       │   ├── manage_departments.html   # Medical specialties configuration
│       │   ├── manage_schedules.html     # Doctor duty roster oversight
│       │   └── reports.html              # CSV/PDF reporting & analytics export
│       └── errors/
│           ├── 404.html                  # Custom Page Not Found
│           └── 500.html                  # Custom Server Error
│
├── run.py                                # Convenient unified root runner
└── README.md                             # Documentation & Setup Guide
```

---

## ⚙️ How to Run the Application

You can start the server in either of two ways:

### Option A: From the Project Root (Unified)
```powershell
python run.py
```

### Option B: From the `backend/` Folder
```powershell
cd backend
python run.py
```

Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

---

## 🔑 Quick Demo Credentials

| Role | Email | Password | Primary Functions |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@careplus.com` | `Admin@123` | Analytics, Staff CRUD, Departments, CSV Exports |
| **Doctor** | `dr.chen@careplus.com` | `Doctor@123` | Patient Queue, Timetable Config, Prescription Builder |
| **Receptionist** | `reception@careplus.com` | `Reception@123` | Walk-in Registration, Token Queue, Cashier Billing |
| **Patient** | `alex@patient.com` | `Patient@123` | Dynamic Slot Booking, Prescriptions, Invoices |

---

## 🧪 Run Automated Tests
```powershell
python backend/tests/test_flow.py
```
