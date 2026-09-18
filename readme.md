# Enhancing Web-GUI Application: Employees Attendance Management

**Subject Code:** SDF04 – Object-Oriented Programming (Python & Database)  
**Course & Section:** BSIT 3rd Year LFCA311M177  
**Prepared By:** Gobres, John Emmanuel R.  
**Instructor:** Prof. JESSA EVANGELISTA  

---

## 🌟 1. Project Overview & System Architecture

This project is a modern, responsive **Web-GUI Employee Attendance Management System** developed in **Python** using **Django**. It overcomes the vulnerabilities of manual logbooks and time fraud (such as "buddy punching") by providing an intuitive, timestamped interface for attendance logging, automated tardiness and overtime computation, administrative workforce analytics, and official **Daily Time Record (DTR)** report generation in **PDF** and **CSV**.

### SDF04 Object-Oriented Programming (OOP) Architecture

To comply with the academic rigor of **SDF04**, the application decouples the database presentation from business logic by introducing a dedicated **OOP Domain & Service Layer** in `core/oop_classes/`:

| Module / Feature | OOP Classes Implemented | OOP Principles & Responsibilities |
|---|---|---|
| **Login / Authentication** | [`User`](file:///c:/Users/reynaldo.mimis/Documents/GitHub/EmployeeAtt/core/oop_classes/auth_manager.py), [`AuthManager`](file:///c:/Users/reynaldo.mimis/Documents/GitHub/EmployeeAtt/core/oop_classes/auth_manager.py) | **Encapsulation & RBAC:** Manages authentication state, protects session data, enforces role separation between Admin and Staff, and maintains tamper-evident audit logs. |
| **Attendance Tracker** | [`AttendanceLog`](file:///c:/Users/reynaldo.mimis/Documents/GitHub/EmployeeAtt/core/oop_classes/time_tracker.py), [`TimeTracker`](file:///c:/Users/reynaldo.mimis/Documents/GitHub/EmployeeAtt/core/oop_classes/time_tracker.py) | **Business Logic & State Machine:** Enforces timekeeping rules, detects late arrival past the shift grace period, calculates overtime, and prevents double Time-In entries. |
| **Records Management** | [`Employee`](file:///c:/Users/reynaldo.mimis/Documents/GitHub/EmployeeAtt/core/oop_classes/employee_manager.py), [`EmployeeManager`](file:///c:/Users/reynaldo.mimis/Documents/GitHub/EmployeeAtt/core/oop_classes/employee_manager.py) | **CRUD Operations & Transactions:** Encapsulates atomic user creation, updates shift schedules, and validates department assignments. |
| **Dashboard Overview** | [`Dashboard`](file:///c:/Users/reynaldo.mimis/Documents/GitHub/EmployeeAtt/core/oop_classes/dashboard_controller.py), [`DashboardController`](file:///c:/Users/reynaldo.mimis/Documents/GitHub/EmployeeAtt/core/oop_classes/dashboard_controller.py) | **Aggregation & View-Model:** Computes workforce KPIs (Present, Late, Absent rates) and prepares department turnout summaries. |
| **Reports & Exports** | [`Report`](file:///c:/Users/reynaldo.mimis/Documents/GitHub/EmployeeAtt/core/oop_classes/report_generator.py), [`ReportGenerator`](file:///c:/Users/reynaldo.mimis/Documents/GitHub/EmployeeAtt/core/oop_classes/report_generator.py) | **Data Processing & Rendering:** Integrates **Pandas** for structured CSV formatting and **ReportLab** for formal DTR PDF rendering. |

---

## 🚀 2. Quickstart Guide (Running Locally)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Database Setup & Migrations
The system is pre-configured with a **dual database architecture**:
- **SQLite (Default for Local Zero-Config Running):** No MySQL setup needed to demo immediately!
- **MySQL (Production / Lab):** Set `USE_MYSQL=True` in `.env` and specify your MySQL credentials.

Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 3: Populate Sample Data
Run the included database seeder to generate departments, employee profiles, and 14 days of realistic attendance history:
```bash
python seed_data.py
```

### Step 4: Run the Development Server
```bash
python manage.py runserver 8000
```
Open your browser and navigate to: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🔑 3. Pre-Seeded Accounts for Testing & Defense Demo

| Role | Username | Password | Notes |
|---|---|---|---|
| **HR Administrator** | `admin` | `admin123` | Full CRUD privileges, system KPIs, audit logs, DTR reports |
| **Senior Staff** | `juan.delacruz` | `password123` | Senior Dev (IT), Shift: 08:00 AM - 05:00 PM |
| **HR Specialist** | `maria.santos` | `password123` | Staff (HR), Shift: 08:00 AM - 05:00 PM |
| **Finance Analyst** | `mark.reyes` | `password123` | Staff (FIN), Shift: 08:30 AM - 05:30 PM |
| **Operations Staff** | `anna.dizon` | `password123` | Staff (OPS), Shift: 09:00 AM - 06:00 PM |

*(Note: The login page includes convenient 1-click credential autofill buttons for defense convenience!)*

---

## 🧪 4. Automated OOP Verification & Testing

Execute the test suite to verify the OOP classes:
```bash
python manage.py test core
```

---

## 🌐 5. Deployment Guide (Paid Hosting & Custom Domain)

As specified in the proposal *(“Domain & Hosting setup required; bawal free hosting & domain”)*:

1. **Environment Configuration (`.env`):**
   - Set `DEBUG=False`
   - Set `ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com`
   - Set `USE_MYSQL=True` with your hosting provider's MySQL credentials:
     ```env
     DB_NAME=your_cpanel_db
     DB_USER=your_cpanel_user
     DB_PASSWORD=your_cpanel_password
     DB_HOST=localhost
     DB_PORT=3306
     ```
2. **Static Files:**
   - Run `python manage.py collectstatic`
3. **WSGI / Web Server:**
   - Compatible with **Gunicorn** / **uWSGI** under **Nginx** (on Ubuntu/Debian VPS) or **Passenger WSGI** (on cPanel / Namecheap / Hostinger / PythonAnywhere).
