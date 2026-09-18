"""
Unit & Integration Tests for SDF04 OOP Architecture
Verifies:
1. User & AuthManager encapsulation & RBAC
2. Employee & EmployeeManager CRUD operations & atomic transactions
3. AttendanceLog & TimeTracker timekeeping rules (on-time, late detection, double-entry blocking)
4. Dashboard & DashboardController KPI computations
5. Report & ReportGenerator Pandas CSV and ReportLab PDF exports
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User as DjangoUser
from datetime import date, time, datetime, timedelta
from decimal import Decimal

from core.models import Department, EmployeeProfile, AttendanceRecord, AuditLog
from core.oop_classes.auth_manager import User, AuthManager
from core.oop_classes.employee_manager import Employee, EmployeeManager
from core.oop_classes.time_tracker import AttendanceLog, TimeTracker
from core.oop_classes.dashboard_controller import DashboardController
from core.oop_classes.report_generator import ReportGenerator


class SDF04OOPTestSuite(TestCase):
    def setUp(self):
        # Create department
        self.dept = Department.objects.create(name="Engineering", code="ENG")

        # Create Admin
        self.admin_user = DjangoUser.objects.create_superuser(
            username="test_admin", email="admin@test.com", password="adminpassword"
        )
        self.admin_profile = EmployeeProfile.objects.create(
            user=self.admin_user,
            employee_id="ADM-001",
            department=self.dept,
            shift_start=time(8, 0),
            shift_end=time(17, 0),
        )

        # Create Regular Employee
        self.emp_user = DjangoUser.objects.create_user(
            username="test_staff", email="staff@test.com", password="staffpassword",
            first_name="Pedro", last_name="Penduko"
        )
        self.emp_profile = EmployeeProfile.objects.create(
            user=self.emp_user,
            employee_id="EMP-999",
            department=self.dept,
            job_title="Junior QA",
            shift_start=time(8, 0),
            shift_end=time(17, 0),
            grace_period_minutes=15,
        )

    def test_01_user_and_auth_manager_encapsulation(self):
        """Test OOP Encapsulation of User entity and AuthManager role resolution"""
        domain_admin = User(self.admin_user)
        domain_staff = User(self.emp_user)

        self.assertTrue(domain_admin.is_admin)
        self.assertFalse(domain_admin.is_employee)

        self.assertFalse(domain_staff.is_admin)
        self.assertTrue(domain_staff.is_employee)
        self.assertEqual(domain_staff.full_name, "Pedro Penduko")

    def test_02_employee_manager_crud(self):
        """Test EmployeeManager CRUD operations and validation"""
        payload = {
            'username': 'new_hire',
            'password': 'password123',
            'employee_id': 'EMP-101',
            'first_name': 'Clara',
            'last_name': 'Reyes',
            'email': 'clara@test.com',
            'department_id': self.dept.id,
            'job_title': 'Junior Dev',
            'shift_start': time(8, 0),
            'shift_end': time(17, 0),
            'grace_period_minutes': 15,
        }
        success, new_emp = EmployeeManager.create_employee(payload, actor_user=self.admin_user)
        self.assertTrue(success)
        self.assertEqual(new_emp.employee_id, 'EMP-101')

        # Test duplicate username rejection
        dup_user_success, dup_user_msg = EmployeeManager.create_employee(payload, actor_user=self.admin_user)
        self.assertFalse(dup_user_success)
        self.assertIn("already taken", dup_user_msg)

        # Test duplicate employee_id rejection (with different username)
        dup_id_payload = payload.copy()
        dup_id_payload['username'] = 'another_username'
        dup_id_success, dup_id_msg = EmployeeManager.create_employee(dup_id_payload, actor_user=self.admin_user)
        self.assertFalse(dup_id_success)
        self.assertIn("already registered", dup_id_msg)

        # Test update
        upd_success, updated_emp = EmployeeManager.update_employee(
            new_emp.id, {'job_title': 'Mid-level Dev'}, actor_user=self.admin_user
        )
        self.assertTrue(upd_success)
        self.assertEqual(updated_emp.job_title, 'Mid-level Dev')

    def test_03_time_tracker_on_time_and_late_detection(self):
        """Test TimeTracker logic: grace period, tardiness, and double-entry prevention"""
        test_date = date(2026, 9, 15)

        # 1. On-time clock in (within 8:00 AM + 15 min grace = 8:15 AM)
        success, msg, log = TimeTracker.record_time_in(
            self.emp_profile,
            check_time=time(8, 10),
            check_date=test_date,
            ip_address="127.0.0.1"
        )
        self.assertTrue(success)
        self.assertEqual(log.status, 'PRESENT')
        self.assertEqual(log.late_minutes, 0)

        # 2. Prevent duplicate clock in on the same date
        dup_success, dup_msg, _ = TimeTracker.record_time_in(
            self.emp_profile,
            check_time=time(8, 20),
            check_date=test_date,
            ip_address="127.0.0.1"
        )
        self.assertFalse(dup_success)
        self.assertIn("already clocked in", dup_msg)

        # 3. Clock out and calculate hours
        out_success, out_msg, out_log = TimeTracker.record_time_out(
            self.emp_profile,
            check_time=time(17, 30),
            check_date=test_date,
            ip_address="127.0.0.1"
        )
        self.assertTrue(out_success)
        self.assertGreater(out_log.total_hours, 0)
        self.assertGreater(out_log.overtime_hours, 0)

    def test_04_time_tracker_late_calculation(self):
        """Test accurate calculation of tardiness minutes past grace period"""
        late_date = date(2026, 9, 16)
        # Shift start is 8:00 AM. Clocking in at 8:35 AM -> 35 minutes late
        success, msg, log = TimeTracker.record_time_in(
            self.emp_profile,
            check_time=time(8, 35),
            check_date=late_date,
            ip_address="127.0.0.1"
        )
        self.assertTrue(success)
        self.assertEqual(log.status, 'LATE')
        self.assertEqual(log.late_minutes, 35)

    def test_05_dashboard_controller_kpis(self):
        """Test DashboardController aggregation of metrics"""
        dash = DashboardController.get_admin_dashboard(target_date=date.today())
        self.assertIsNotNone(dash)
        self.assertGreaterEqual(dash.total_employees, 2)
        self.assertIsInstance(dash.attendance_rate, float)

    def test_06_report_generator_pandas_and_reportlab(self):
        """Test ReportGenerator CSV and PDF generation using pandas & reportlab"""
        # Create a sample record
        AttendanceRecord.objects.create(
            employee=self.emp_profile,
            date=date(2026, 9, 10),
            time_in=time(8, 0),
            time_out=time(17, 0),
            status='PRESENT',
            total_hours=Decimal('8.00'),
            overtime_hours=Decimal('0.00')
        )

        qs = AttendanceRecord.objects.filter(employee=self.emp_profile)

        # Pandas CSV Export
        csv_bytes = ReportGenerator.generate_csv_report(qs)
        self.assertIsInstance(csv_bytes, bytes)
        self.assertIn(b"EMP-999", csv_bytes)

        # ReportLab PDF Export
        pdf_bytes = ReportGenerator.generate_pdf_dtr(
            queryset=qs,
            report_title="Test DTR Report",
            employee_profile=self.emp_profile
        )
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b'%PDF-'))

    def test_07_employee_dashboard_controller(self):
        """Verify employee dashboard does not crash on recent_logs comprehension"""
        data = DashboardController.get_employee_dashboard(self.emp_profile)
        self.assertIsNotNone(data)
        self.assertEqual(data['employee'], self.emp_profile)
        self.assertIsInstance(data['recent_logs'], list)

    def test_08_employee_manager_search(self):
        """Verify employee search handles Q query without NameError"""
        results = EmployeeManager.search_employees(query="Pedro")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].employee_id, "EMP-999")

    def test_09_overnight_shift_calculation(self):
        """Verify hours and overtime calculation for shifts crossing midnight"""
        rec = AttendanceRecord.objects.create(
            employee=self.emp_profile,
            date=date(2026, 9, 20),
            time_in=time(22, 0),
            time_out=time(6, 0),
            status='PRESENT'
        )
        rec.calculate_hours_and_overtime()
        rec.save()
        self.assertGreater(rec.total_hours, Decimal('0.00'))
        # 8 hours worked - 1 hour lunch = 7.00 hours
        self.assertEqual(rec.total_hours, Decimal('7.00'))
