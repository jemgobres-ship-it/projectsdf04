# Enhancing Web-GUI Application: Employees Attendance Management System (AttendTrack)
## Complete Technical Documentation, Architecture, Setup & Presentation Manual

---

### Academic Information Block
* **Subject Code & Title:** SDF04 – Object-Oriented Programming (Python & Database)
* **Course, Year & Section:** BSIT 3rd Year – LFCA311M177
* **Prepared By (Student):** Gobres, John Emmanuel R.
* **Instructor / Evaluator:** Prof. JESSA EVANGELISTA
* **Technologies Used:** Python 3.12, Django 5.1, SQLite / MySQL 8.0, Pandas 3.x, ReportLab 5.x, HTML5, CSS3, JavaScript

---

## 1. Executive Summary & Problem Statement

Manual attendance logging via paper logbooks poses severe operational and security liabilities for organizations:
1. **Time Theft & "Buddy Punching":** Employees can clock in on behalf of late or absent colleagues.
2. **Computational Errors:** Calculating tardiness, grace period exemptions, and overtime hours manually is labor-intensive and prone to human error.
3. **Lack of Auditability:** Manual records lack verifiable digital timestamps, IP logging, and tamper detection.

The **AttendTrack** application provides a secure, modern **Web-GUI Employee Attendance Management System** developed in **Python** using **Django**. It enforces real-time digital timekeeping, automated grace period calculations, executive analytics, and formal **Daily Time Record (DTR)** report generation in both **CSV** (via Pandas) and **PDF** (via ReportLab).

---

## 2. SDF04 Object-Oriented Programming (OOP) Architecture

To comply with the academic rigor of **SDF04**, the application decouples data presentation and raw database queries from business logic by introducing a dedicated **OOP Domain & Service Layer** in `core/oop_classes/`:

```
core/oop_classes/
├── auth_manager.py          --> User (Domain Entity), AuthManager (Service Class)
├── time_tracker.py          --> AttendanceLog (Domain Entity), TimeTracker (Service Class)
├── employee_manager.py      --> Employee (Domain Entity), EmployeeManager (Service Class)
├── dashboard_controller.py  --> Dashboard (Domain Entity), DashboardController (Service Class)
└── report_generator.py      --> Report (Domain Entity), ReportGenerator (Service Class)
```

### OOP Implementation Matrix

| Module / Feature | OOP Classes Implemented | OOP Principles & Responsibilities |
|---|---|---|
| **Login / Authentication** | `User`, `AuthManager` | **Encapsulation & RBAC:** Encapsulates user session, resolves Admin vs Staff roles, enforces secure login authentication, and logs login/logout security audit events. |
| **Attendance Tracker** | `AttendanceLog`, `TimeTracker` | **State Machine & Business Logic:** Computes tardiness minutes beyond shift grace period, calculates net hours and overtime, and prevents double Time-In punches. |
| **Records Management** | `Employee`, `EmployeeManager` | **CRUD & Transaction Integrity:** Atomic creation of user credentials and profile records (`@transaction.atomic`), profile updates, shifts, and safe deletion. |
| **Dashboard Overview** | `Dashboard`, `DashboardController` | **View-Model & Data Aggregation:** Calculates real-time workforce KPIs (turnout rate, present, late, absent), and prepares department attendance summaries. |
| **Reports & Exports** | `Report`, `ReportGenerator` | **Integration & Data Transformation:** Leverages Pandas for structured CSV generation and ReportLab for official Philippine DTR PDF document rendering. |

---

## 3. System Requirements & Tech Stack

* **Operating System:** Windows 10/11, macOS, or Ubuntu/Debian Linux
* **Python Runtime:** Python 3.10 to 3.12
* **Web Framework:** Django 5.x
* **Data Processing:** Pandas (CSV generation)
* **PDF Rendering:** ReportLab (Official Philippine DTR layout)
* **Dual Database Architecture:**
  - **SQLite (Default):** Zero-configuration local database for grading and presentation.
  - **MySQL 8.0 / MariaDB:** Production/lab database connecting via PyMySQL and mysql-connector-python.

---

## 4. Step-by-Step Setup & Installation Guide

### Step 1: Open Terminal and Navigate to Directory
```powershell
cd C:\Users\Admin\Downloads\EmployeeAtt\EmployeeAtt
```

### Step 2: Create & Activate Virtual Environment
```powershell
# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (Windows Command Prompt)
venv\Scripts\activate.bat

# Activate (macOS / Linux)
source venv/bin/activate
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Configure Database (`.env`)

#### Option A: SQLite (Default — Fast & Zero-Config)
In `.env`:
```ini
SECRET_KEY=django-insecure-employee-attendance-sdf04-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
USE_MYSQL=False
```

#### Option B: MySQL 8.0 / XAMPP
In `.env`:
```ini
USE_MYSQL=True
DB_NAME=employee_attendance_db
DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306
```

### Step 5: Run Database Migrations
```powershell
python manage.py makemigrations
python manage.py migrate
```

### Step 6: Populate Seed Data (Test Accounts & History)
```powershell
python seed_data.py
```

---

## 5. How to Run & Access the System

### Start Development Server
```powershell
python manage.py runserver 8000
```

Open your web browser and go to:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

### Pre-Configured Accounts for Defense Demo

| Role | Username | Password | Privileges & Shift Schedule |
|---|---|---|---|
| **HR Administrator** | `admin` | `admin123` | Full Executive Dashboard, Employee Directory (CRUD), Audit Trail, PDF/CSV Reports |
| **Senior Developer** | `juan.delacruz` | `password123` | Personal Employee Portal, Time Clock, Shift: 8:00 AM – 5:00 PM |
| **HR Specialist** | `maria.santos` | `password123` | Personal Employee Portal, Time Clock, Shift: 8:00 AM – 5:00 PM |
| **Finance Analyst** | `mark.reyes` | `password123` | Personal Employee Portal, Time Clock, Shift: 8:30 AM – 5:30 PM |
| **Operations Staff** | `anna.dizon` | `password123` | Personal Employee Portal, Time Clock, Shift: 9:00 AM – 6:00 PM |

> **Presentation Convenience:** The login screen provides **1-click credential buttons** (`Admin: admin` and `Staff: juan.delacruz`) so you don't have to type passwords during defense.

---

## 6. Detailed Feature & Module Walkthrough

### 6.1 Interactive Time Clock Terminal
* **Route:** `/clock/`
* **Features:**
  - Live ticking digital clock synchronized to Manila time.
  - One-click **RECORD TIME IN** button.
  - Automated Tardiness Calculation: If arrival > `shift_start + grace_period_minutes`, marks status as `LATE` and records late minutes.
  - One-click **RECORD TIME OUT** button.
  - Automatic Working Duration computation: Deducts 1 hour standard lunch break if duration ≥ 5 hours.
  - Overtime calculation against scheduled `shift_end`.
  - Double punch prevention (blocks multiple Time-In entries on the same date).

### 6.2 Executive HR Dashboard
* **Route:** `/` (when logged in as `admin`)
* **Features:**
  - Real-time KPI Cards: Total Active Employees, Present On-Time, Late Arrivals, Unaccounted/Absent.
  - Dynamic attendance turnout percentage progress bar.
  - Live activity feed with quick links to adjust records.
  - Department turnout summary (e.g. IT, HR, Finance, Operations).

### 6.3 Employee Self-Service Portal
* **Route:** `/` (when logged in as standard staff)
* **Features:**
  - Today's punch status overview.
  - Monthly attendance performance (Days Present, Days Late, Total Hours, Overtime).
  - Personal 10-day history with status badges (`badge-success`, `badge-warning`).
  - Direct 1-click download of personal Daily Time Record (PDF DTR).

### 6.4 Employee Records Management (CRUD)
* **Routes:** `/employees/`, `/employees/create/`, `/employees/<id>/edit/`, `/employees/<id>/delete/`
* **Features:**
  - Employee list with keyword search (ID, name, title) and department filtering.
  - Atomic account creation (`User` and `EmployeeProfile` created together).
  - Shift configuration: Start Time, End Time, Grace Period (mins).
  - Safe deletion with audit log tracking.

### 6.5 Master Attendance Log & Manual Adjustments
* **Routes:** `/attendance/`, `/attendance/<id>/adjust/`
* **Features:**
  - Filter by date range, department, and attendance status.
  - Administrator adjustment form allowing manual time correction.
  - Mandatory audit notes explaining adjustment reasons.

### 6.6 Official Reports & Daily Time Record (DTR)
* **Routes:** `/reports/`, `/reports/export/csv/`, `/reports/export/pdf/`
* **Features:**
  - Filterable report preview with total hours and overtime sums.
  - **Pandas CSV Export:** Clean formatted spreadsheet data.
  - **ReportLab PDF DTR:** Official Philippine DTR layout with metadata header, daily punches, late minutes, totals, and HR/Employee certification signature lines.

### 6.7 Security Audit Trail
* **Route:** `/audit-logs/`
* **Features:**
  - Tamper-evident logging of logins, logouts, time punches, manual adjustments, and profile changes.
  - Stores user, action, event details, and IP address.

---

## 7. Automated OOP Unit Testing

Run the automated test suite to demonstrate code verification to your professor:

```powershell
python manage.py test core
```

### Verified Test Cases:
1. `test_01_user_and_auth_manager_encapsulation`: User domain entity and RBAC.
2. `test_02_employee_manager_crud`: Atomic employee creation and validation.
3. `test_03_time_tracker_on_time_and_late_detection`: Grace period & double punch blocking.
4. `test_04_time_tracker_late_calculation`: Accurate tardiness minutes calculation.
5. `test_05_dashboard_controller_kpis`: Workforce KPI and turnout aggregation.
6. `test_06_report_generator_pandas_and_reportlab`: Pandas CSV and ReportLab PDF DTR exports.
7. `test_07_employee_dashboard_controller`: Employee dashboard view-model integrity.
8. `test_08_employee_manager_search`: Directory search query handling.
9. `test_09_overnight_shift_calculation`: Accurate calculation for overnight shifts.

**Result:** `Ran 9 tests in ~25s — OK`

---

## 8. Presentation Flow Guide for Defense

1. **Problem Statement:** Explain the goal of replacing unreliable manual paper logbooks with an automated, timestamped OOP Web-GUI system.
2. **Codebase Architecture:** Open `core/oop_classes/` in VS Code to highlight the separation of concerns:
   - `auth_manager.py`
   - `employee_manager.py`
   - `time_tracker.py`
   - `dashboard_controller.py`
   - `report_generator.py`
3. **Live Demonstration:**
   - Log in as `juan.delacruz` via 1-click button.
   - Go to **Clock In / Out** and clock in.
   - Show personal dashboard and DTR preview.
   - Log in as `admin`.
   - Show Executive KPIs and department turnout.
   - Generate official **PDF DTR** via ReportLab.
   - Show the **Security Audit Trail**.
4. **Automated Tests:** Run `python manage.py test core` in terminal to prove complete test passage.
