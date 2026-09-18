import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from datetime import datetime
import os

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def style_heading(p, text, level=1, space_before=14, space_after=6):
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.bold = True
    if level == 1:
        run.font.size = Pt(18)
        run.font.color.rgb = RGBColor(30, 58, 138) # Deep Navy
    elif level == 2:
        run.font.size = Pt(14)
        run.font.color.rgb = RGBColor(37, 99, 235) # Royal Blue
    elif level == 3:
        run.font.size = Pt(12)
        run.font.color.rgb = RGBColor(15, 23, 42)  # Slate
    return run

def create_document():
    doc = docx.Document()

    # Set page margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Set Base Normal Style
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(51, 65, 85) # Slate text
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(4)

    # ==========================================
    # COVER / HEADER TITLE BLOCK
    # ==========================================
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.paragraph_format.space_before = Pt(20)
    title_p.paragraph_format.space_after = Pt(4)
    run_title = title_p.add_run("ENHANCING WEB-GUI APPLICATION:\nEMPLOYEES ATTENDANCE MANAGEMENT SYSTEM")
    run_title.font.name = 'Calibri'
    run_title.font.size = Pt(22)
    run_title.bold = True
    run_title.font.color.rgb = RGBColor(30, 58, 138)

    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_p.paragraph_format.space_after = Pt(16)
    run_sub = sub_p.add_run("System Documentation, Technical Architecture, & User Demonstration Manual")
    run_sub.font.size = Pt(13)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(100, 116, 139)

    # Metadata Box Table
    meta_table = doc.add_table(rows=5, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.autofit = False

    metadata = [
        ("Subject Code & Title:", "SDF04 – Object-Oriented Programming (Python & Database)"),
        ("Course, Year & Section:", "BSIT 3rd Year – LFCA311M177"),
        ("Prepared By (Student):", "Gobres, John Emmanuel R."),
        ("Instructor / Evaluator:", "Prof. JESSA EVANGELISTA"),
        ("Software Frameworks:", "Python 3.12 | Django 5.1 | SQLite & MySQL 8.0 | Pandas | ReportLab"),
    ]

    for i, (label, val) in enumerate(metadata):
        c1, c2 = meta_table.rows[i].cells
        c1.width = Inches(2.2)
        c2.width = Inches(4.3)
        set_cell_background(c1, "F1F5F9")
        set_cell_background(c2, "F8FAFC")
        set_cell_margins(c1, top=70, bottom=70, left=120, right=120)
        set_cell_margins(c2, top=70, bottom=70, left=120, right=120)

        p1 = c1.paragraphs[0]
        p1.paragraph_format.space_after = Pt(0)
        r1 = p1.add_run(label)
        r1.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = RGBColor(30, 58, 138)

        p2 = c2.paragraphs[0]
        p2.paragraph_format.space_after = Pt(0)
        r2 = p2.add_run(val)
        r2.font.size = Pt(10)
        r2.font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # ==========================================
    # 1. EXECUTIVE SUMMARY & OBJECTIVES
    # ==========================================
    style_heading(doc.add_paragraph(), "1. Project Overview & System Objectives", level=1)
    
    p = doc.add_paragraph(
        "The Employees Attendance Management System (AttendTrack) is an enterprise-grade Web-GUI application developed in Python using the Django framework. Designed specifically to satisfy the rigorous academic competencies of SDF04 (Object-Oriented Programming with Database), this system eliminates vulnerabilities inherent in manual paper logbooks and time fraud (such as 'buddy punching')."
    )
    p = doc.add_paragraph(
        "The system delivers an automated, tamper-evident digital timekeeping terminal, dynamic grace period tardiness evaluation, overtime tracking, workforce turn-out analytics, staff records administration (CRUD), and generation of official Daily Time Record (DTR) documents in CSV (via Pandas) and PDF (via ReportLab)."
    )

    # ==========================================
    # 2. SDF04 OBJECT-ORIENTED PROGRAMMING (OOP) ARCHITECTURE
    # ==========================================
    style_heading(doc.add_paragraph(), "2. SDF04 Object-Oriented Programming (OOP) Architecture", level=1)

    doc.add_paragraph(
        "To strictly comply with the academic syllabus of SDF04, this project decouples database persistence from presentation by implementing a dedicated OOP Domain Entity and Service Layer located in 'core/oop_classes/':"
    )

    oop_table = doc.add_table(rows=6, cols=3)
    oop_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    oop_table.autofit = False

    headers = ["Proposal Module", "OOP Classes Implemented", "OOP Principles & Architectural Responsibilities"]
    col_widths = [Inches(1.6), Inches(2.0), Inches(2.9)]

    for j, h in enumerate(headers):
        cell = oop_table.rows[0].cells[j]
        cell.width = col_widths[j]
        set_cell_background(cell, "1E3A8A")
        set_cell_margins(cell, top=100, bottom=100, left=100, right=100)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h)
        r.bold = True
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(255, 255, 255)

    oop_rows = [
        ("Login / Authentication", "User\nAuthManager", "Encapsulation & RBAC: Encapsulates user session, resolves Admin vs Staff roles, enforces secure login authentication, and logs login/logout security audit events."),
        ("Attendance Tracker", "AttendanceLog\nTimeTracker", "State Machine & Business Logic: Computes tardiness minutes beyond shift grace period, calculates net hours and overtime, and prevents double Time-In punches."),
        ("Records Management", "Employee\nEmployeeManager", "CRUD & Transaction Integrity: Atomic creation of user credentials and profile records (@transaction.atomic), profile updates, shifts, and safe deletion."),
        ("Dashboard Overview", "Dashboard\nDashboardController", "View-Model & Data Aggregation: Calculates real-time workforce KPIs (turnout rate, present, late, absent), and prepares department attendance summaries."),
        ("Reports & Exports", "Report\nReportGenerator", "Integration & Data Transformation: Leverages Pandas for structured CSV generation and ReportLab for official Philippine DTR PDF document rendering."),
    ]

    for i, row in enumerate(oop_rows, start=1):
        for j, text in enumerate(row):
            cell = oop_table.rows[i].cells[j]
            cell.width = col_widths[j]
            bg = "FFFFFF" if i % 2 != 0 else "F8FAFC"
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(text)
            r.font.size = Pt(9.5)
            if j == 1:
                r.bold = True
                r.font.color.rgb = RGBColor(37, 99, 235)

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # ==========================================
    # 3. COMPLETE CONFIGURATION & SETUP GUIDE
    # ==========================================
    style_heading(doc.add_paragraph(), "3. Configuration & Step-by-Step Setup Guide", level=1)

    style_heading(doc.add_paragraph(), "3.1 Environment Requirements", level=2)
    doc.add_paragraph("Ensure the target workstation has Python 3.10, 3.11, or 3.12 installed with pip configured in the System PATH.")

    style_heading(doc.add_paragraph(), "3.2 Creating and Activating Python Virtual Environment", level=2)
    p = doc.add_paragraph("Open Windows PowerShell or Command Prompt, navigate to the inner project directory, and run:")
    p = doc.add_paragraph()
    r = p.add_run("cd C:\\Users\\Admin\\Downloads\\EmployeeAtt\\EmployeeAtt\npython -m venv venv\n.\\venv\\Scripts\\Activate.ps1")
    r.font.name = 'Consolas'
    r.font.size = Pt(9.5)
    r.font.color.rgb = RGBColor(30, 41, 59)
    p.paragraph_format.left_indent = Inches(0.4)

    style_heading(doc.add_paragraph(), "3.3 Installing Dependencies", level=2)
    p = doc.add_paragraph("Install all production and academic dependencies via pip:")
    p = doc.add_paragraph()
    r = p.add_run("pip install -r requirements.txt")
    r.font.name = 'Consolas'
    r.font.size = Pt(9.5)
    r.font.color.rgb = RGBColor(30, 41, 59)
    p.paragraph_format.left_indent = Inches(0.4)

    style_heading(doc.add_paragraph(), "3.4 Dual Database Configuration (.env)", level=2)
    doc.add_paragraph(
        "The application is engineered with a Dual Database Architecture configured via the '.env' file:"
    )
    doc.add_paragraph("• Mode 1: SQLite (Default Zero-Config): Requires zero database server installation. Instant demo readiness.\n  Setting: USE_MYSQL=False")
    doc.add_paragraph("• Mode 2: MySQL Server 8.0 / XAMPP: Production and academic proposal compliant.\n  Setting: USE_MYSQL=True with DB credentials (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT).")

    style_heading(doc.add_paragraph(), "3.5 Running Database Migrations", level=2)
    p = doc.add_paragraph("Initialize all database schemas and tables:")
    p = doc.add_paragraph()
    r = p.add_run("python manage.py makemigrations\npython manage.py migrate")
    r.font.name = 'Consolas'
    r.font.size = Pt(9.5)
    p.paragraph_format.left_indent = Inches(0.4)

    style_heading(doc.add_paragraph(), "3.6 Seeding Initial Test Accounts & Attendance History", level=2)
    p = doc.add_paragraph("Execute the automated database seeder to establish departments, users, and 14 days of historical logs:")
    p = doc.add_paragraph()
    r = p.add_run("python seed_data.py")
    r.font.name = 'Consolas'
    r.font.size = Pt(9.5)
    p.paragraph_format.left_indent = Inches(0.4)

    # ==========================================
    # 4. HOW TO RUN & ACCESS THE APPLICATION
    # ==========================================
    style_heading(doc.add_paragraph(), "4. How to Run & Access the System", level=1)

    style_heading(doc.add_paragraph(), "4.1 Starting the Development Web Server", level=2)
    p = doc.add_paragraph("Launch the local web server by executing:")
    p = doc.add_paragraph()
    r = p.add_run("python manage.py runserver 8000")
    r.font.name = 'Consolas'
    r.font.size = Pt(9.5)
    r.bold = True
    p.paragraph_format.left_indent = Inches(0.4)

    p = doc.add_paragraph("Open any web browser and navigate to: http://127.0.0.1:8000")

    style_heading(doc.add_paragraph(), "4.2 Pre-Configured Accounts for Professor Evaluation", level=2)

    acc_table = doc.add_table(rows=6, cols=4)
    acc_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    acc_table.autofit = False

    acc_headers = ["Assigned Role", "Username", "Password", "System Privileges & Shift Schedule"]
    acc_col_w = [Inches(1.5), Inches(1.5), Inches(1.3), Inches(2.2)]

    for j, h in enumerate(acc_headers):
        cell = acc_table.rows[0].cells[j]
        cell.width = acc_col_w[j]
        set_cell_background(cell, "1E3A8A")
        set_cell_margins(cell, top=80, bottom=80, left=80, right=80)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h)
        r.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(255, 255, 255)

    acc_data = [
        ("HR Administrator", "admin", "admin123", "Full Executive Dashboard, Employee CRUD, System Logs, DTR Reports"),
        ("Senior Developer", "juan.delacruz", "password123", "Employee Portal, Shift: 8:00 AM - 5:00 PM, Time Clock"),
        ("HR Specialist", "maria.santos", "password123", "Employee Portal, Shift: 8:00 AM - 5:00 PM, Time Clock"),
        ("Finance Analyst", "mark.reyes", "password123", "Employee Portal, Shift: 8:30 AM - 5:30 PM, Time Clock"),
        ("Operations Staff", "anna.dizon", "password123", "Employee Portal, Shift: 9:00 AM - 6:00 PM, Time Clock"),
    ]

    for i, row in enumerate(acc_data, start=1):
        for j, text in enumerate(row):
            cell = acc_table.rows[i].cells[j]
            cell.width = acc_col_w[j]
            bg = "FFFFFF" if i % 2 != 0 else "F8FAFC"
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(text)
            r.font.size = Pt(9)
            if j == 1:
                r.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(10)
    p_note = doc.add_paragraph()
    r_note = p_note.add_run("Defense Convenience Feature: ")
    r_note.bold = True
    p_note.add_run("The login interface includes 1-click credential autofill buttons ('Admin: admin' and 'Staff: juan.delacruz') to enable frictionless demonstration without manual typing.")

    # ==========================================
    # 5. DETAILED MODULE WALKTHROUGH
    # ==========================================
    style_heading(doc.add_paragraph(), "5. Detailed System Modules & User Walkthrough", level=1)

    modules = [
        ("5.1 Time Clock Terminal (Biometric Web Simulation)",
         "Accessible via the top navigation 'Clock In / Out'. Features a real-time ticking digital clock synchronized to Asia/Manila standard time. Employees click 'RECORD TIME IN' to log arrival. The TimeTracker engine checks arrival against shift_start + grace_period_minutes. If late, minutes of tardiness are computed and status becomes LATE; otherwise PRESENT. Clicking 'RECORD TIME OUT' computes total working hours (less standard 1-hour lunch break for >5 hours worked) and overtime beyond shift_end. Double-entry punches are strictly blocked."),

        ("5.2 Executive HR Dashboard",
         "When logged in as Administrator, the central dashboard computes real-time workforce KPIs: Total Enrolled Employees, Present (On-Time), Late Arrivals, and Unaccounted/Absent. It features an attendance turnout percentage progress bar, live recent activity stream with direct manual adjustment buttons, and a department-by-department turnout breakdown."),

        ("5.3 Employee Self-Service Dashboard",
         "When logged in as standard staff, the dashboard transforms to display personal monthly metrics: Days Present, Days Late, Total Hours Rendered, Overtime Accumulated, shift schedule, today's punch state, and personal attendance history with status badges."),

        ("5.4 Employee Records Management (CRUD)",
         "Accessible only to Administrators. Enables adding new employees with automatic Django User account generation and shift assignment (Shift Start, Shift End, Grace Period). Supports keyword search by ID, name, username, or role, department filtering, profile edits, and safe deletion with audit tracking."),

        ("5.5 Master Attendance Log & Manual Adjustments",
         "A filterable master log enabling searching by Date Range, Department, and Status. Administrators can perform manual adjustments (correcting punch times or status) with mandatory justification notes recorded into the security audit trail."),

        ("5.6 Official Reports & Daily Time Record (DTR) Exports",
         "Enables downloading official attendance reports:\n• CSV Export (via Pandas): Generates structured comma-separated files suitable for Excel analysis.\n• PDF DTR (via ReportLab): Produces print-ready official Daily Time Records formatted with employee metadata, scheduled shifts, daily timestamps, monthly totals, and supervisor signature lines matching Philippine corporate standards."),

        ("5.7 Security Audit Trail",
         "Tamper-evident log documenting user logins, logouts, timekeeping punches, manual adjustments (with before-and-after values), and employee profile creations/updates, complete with timestamps and IP addresses.")
    ]

    for title, desc in modules:
        style_heading(doc.add_paragraph(), title, level=2)
        doc.add_paragraph(desc)

    # ==========================================
    # 6. AUTOMATED OOP VERIFICATION & TEST SUITE
    # ==========================================
    style_heading(doc.add_paragraph(), "6. Automated OOP Verification & Testing Guide", level=1)

    doc.add_paragraph(
        "The project includes an automated test suite in 'core/tests.py' specifically written to prove compliance with OOP architecture requirements. To run tests:"
    )

    p = doc.add_paragraph()
    r = p.add_run("python manage.py test core")
    r.font.name = 'Consolas'
    r.font.size = Pt(9.5)
    r.bold = True
    p.paragraph_format.left_indent = Inches(0.4)

    doc.add_paragraph("The automated test suite verifies 9 distinct capabilities:")
    tests_list = [
        "1. test_01_user_and_auth_manager_encapsulation: Validates domain User entity and RBAC permissions.",
        "2. test_02_employee_manager_crud: Tests atomic employee creation, duplicate ID blocking, and updates.",
        "3. test_03_time_tracker_on_time_and_late_detection: Verifies grace period handling and double punch prevention.",
        "4. test_04_time_tracker_late_calculation: Tests exact tardiness minute calculation.",
        "5. test_05_dashboard_controller_kpis: Verifies workforce turnout rate calculation.",
        "6. test_06_report_generator_pandas_and_reportlab: Verifies CSV byte generation and ReportLab PDF compilation.",
        "7. test_07_employee_dashboard_controller: Verifies personal view-model integrity.",
        "8. test_08_employee_manager_search: Tests keyword search queries using Django Q objects.",
        "9. test_09_overnight_shift_calculation: Verifies duration calculations for shifts crossing midnight."
    ]
    for t in tests_list:
        doc.add_paragraph(f"• {t}")

    # ==========================================
    # 7. DEPLOYMENT & DEFENSE PRESENTATION TIPS
    # ==========================================
    style_heading(doc.add_paragraph(), "7. Defense Presentation & Evaluation Tips for Prof. Evangelista", level=1)

    tips = [
        ("Step 1: Introduction", "Explain the project problem statement: eliminating time theft and buddy punching in manual logbooks using a timestamped OOP Web-GUI architecture."),
        ("Step 2: OOP Architecture Highlight", "Show the 'core/oop_classes/' folder to demonstrate how business logic is separated from Django views into User, AuthManager, Employee, EmployeeManager, TimeTracker, DashboardController, and ReportGenerator."),
        ("Step 3: Live Time Clock Punch", "Log in as juan.delacruz (click the quick button), go to 'Clock In / Out', show the live ticking clock, and punch Time-In."),
        ("Step 4: Admin Analytics & Turnout", "Log out and log in as admin. Show the executive dashboard updating turnout percentages and department turnout live."),
        ("Step 5: PDF DTR Generation", "Navigate to 'Reports & DTR (PDF/CSV)', filter for an employee, and click 'Download DTR (ReportLab PDF)' to show the official printed DTR with signatures."),
        ("Step 6: Security Audit Trail", "Navigate to 'Security Audit Trail' to show that every punch and login has been recorded with timestamps and IP addresses."),
        ("Step 7: Automated Test Execution", "Open the terminal and run 'python manage.py test core' to show all 9 automated tests passing with OK status.")
    ]

    for step_title, step_desc in tips:
        p = doc.add_paragraph()
        r = p.add_run(f"• {step_title}: ")
        r.bold = True
        r.font.color.rgb = RGBColor(30, 58, 138)
        p.add_run(step_desc)

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PROJECT_DOCUMENTATION.docx")
    doc.save(output_path)
    print(f"[+] Successfully generated {output_path}")

if __name__ == '__main__':
    create_document()
