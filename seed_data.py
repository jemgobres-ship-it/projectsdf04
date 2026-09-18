"""
Database Seeder Script for Employee Attendance Management System (SDF04).
Pre-populates:
1. Departments (IT, HR, Finance, Operations)
2. Admin User ('admin' / 'admin123')
3. Sample Staff Users ('juan.delacruz', 'maria.santos', 'mark.reyes', 'anna.dizon')
4. 14 Days of realistic attendance records (On-time, Late, Overtime, Absent)
"""

import os
import django
from datetime import date, time, datetime, timedelta
from decimal import Decimal
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'employee_attendance.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Department, EmployeeProfile, AttendanceRecord, AuditLog


def seed_database():
    print("[*] Starting Database Seeding for SDF04 Project...")

    # 1. Create Departments
    departments_data = [
        {'name': 'Information Technology', 'code': 'IT', 'description': 'Software development, infrastructure, and technical support.'},
        {'name': 'Human Resources', 'code': 'HR', 'description': 'Talent acquisition, employee relations, and payroll/attendance oversight.'},
        {'name': 'Accounting & Finance', 'code': 'FIN', 'description': 'Financial reporting, budget planning, and auditing.'},
        {'name': 'Operations & Logistics', 'code': 'OPS', 'description': 'Daily office operations, inventory, and logistics management.'},
    ]

    dept_objs = {}
    for d in departments_data:
        dept, created = Department.objects.get_or_create(
            code=d['code'],
            defaults={'name': d['name'], 'description': d['description']}
        )
        dept_objs[d['code']] = dept
        print(f"  - Department: {dept.name} ({'Created' if created else 'Exists'})")

    # 2. Create Admin User
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@company.com',
            'first_name': 'System',
            'last_name': 'Administrator',
            'is_staff': True,
            'is_superuser': True,
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()

    admin_profile, _ = EmployeeProfile.objects.get_or_create(
        user=admin_user,
        defaults={
            'employee_id': 'EMP-ADMIN-001',
            'department': dept_objs['HR'],
            'job_title': 'HR Director & System Admin',
            'contact_number': '09170000001',
            'shift_start': time(8, 0),
            'shift_end': time(17, 0),
            'grace_period_minutes': 15,
            'hire_date': date(2023, 1, 15),
            'is_active': True,
        }
    )
    print(f"  - Admin User: admin / admin123 ({'Created' if created else 'Exists'})")

    # 3. Create Sample Staff Users
    staff_data = [
        {
            'username': 'juan.delacruz',
            'first_name': 'Juan',
            'last_name': 'Dela Cruz',
            'email': 'juan.delacruz@company.com',
            'emp_id': 'EMP-2026-001',
            'dept': 'IT',
            'title': 'Senior Software Engineer',
            'contact': '09171234567',
            'shift_start': time(8, 0),
            'shift_end': time(17, 0),
        },
        {
            'username': 'maria.santos',
            'first_name': 'Maria',
            'last_name': 'Santos',
            'email': 'maria.santos@company.com',
            'emp_id': 'EMP-2026-002',
            'dept': 'HR',
            'title': 'HR Specialist',
            'contact': '09189876543',
            'shift_start': time(8, 0),
            'shift_end': time(17, 0),
        },
        {
            'username': 'mark.reyes',
            'first_name': 'Mark',
            'last_name': 'Reyes',
            'email': 'mark.reyes@company.com',
            'emp_id': 'EMP-2026-003',
            'dept': 'FIN',
            'title': 'Financial Analyst',
            'contact': '09195551234',
            'shift_start': time(8, 30),
            'shift_end': time(17, 30),
        },
        {
            'username': 'anna.dizon',
            'first_name': 'Anna',
            'last_name': 'Dizon',
            'email': 'anna.dizon@company.com',
            'emp_id': 'EMP-2026-004',
            'dept': 'OPS',
            'title': 'Operations Coordinator',
            'contact': '09204445678',
            'shift_start': time(9, 0),
            'shift_end': time(18, 0),
        },
    ]

    staff_profiles = []
    for s in staff_data:
        u, u_created = User.objects.get_or_create(
            username=s['username'],
            defaults={
                'first_name': s['first_name'],
                'last_name': s['last_name'],
                'email': s['email'],
                'is_staff': False,
                'is_superuser': False,
            }
        )
        if u_created:
            u.set_password('password123')
            u.save()

        p, p_created = EmployeeProfile.objects.get_or_create(
            user=u,
            defaults={
                'employee_id': s['emp_id'],
                'department': dept_objs[s['dept']],
                'job_title': s['title'],
                'contact_number': s['contact'],
                'shift_start': s['shift_start'],
                'shift_end': s['shift_end'],
                'grace_period_minutes': 15,
                'hire_date': date(2024, 3, 1),
                'is_active': True,
            }
        )
        staff_profiles.append(p)
        print(f"  - Staff: {s['username']} / password123 [ID: {s['emp_id']}]")

    # 4. Generate 14 days of realistic attendance history (weekdays only)
    today = date.today()
    created_logs = 0

    all_profiles = [admin_profile] + staff_profiles

    for days_back in range(14, -1, -1):
        target_date = today - timedelta(days=days_back)
        # Skip Sundays
        if target_date.weekday() == 6:
            continue

        for profile in all_profiles:
            # Check if record already exists
            if AttendanceRecord.objects.filter(employee=profile, date=target_date).exists():
                continue

            # Randomize attendance scenario for realism
            rand_roll = random.random()

            # Today: leave one clocked-in without clock-out, others completed
            if target_date == today:
                if profile.user.username == 'juan.delacruz':
                    # Juan clocked in on time today
                    t_in = time(7, 55, 0)
                    AttendanceRecord.objects.create(
                        employee=profile,
                        date=target_date,
                        time_in=t_in,
                        status='PRESENT',
                        late_minutes=0,
                        ip_address='127.0.0.1',
                        notes='Active session today.'
                    )
                    created_logs += 1
                elif profile.user.username == 'maria.santos':
                    # Maria clocked in late today
                    t_in = time(8, 28, 0)
                    AttendanceRecord.objects.create(
                        employee=profile,
                        date=target_date,
                        time_in=t_in,
                        status='LATE',
                        late_minutes=28,
                        ip_address='127.0.0.1',
                        notes='Traffic along Commonwealth Ave.'
                    )
                    created_logs += 1
                continue

            # Historical days
            if rand_roll < 0.70:
                # On-time attendance
                in_min = random.randint(45, 58)
                t_in = time(profile.shift_start.hour - 1 if profile.shift_start.minute == 0 else profile.shift_start.hour, in_min)
                out_min = random.randint(5, 30)
                t_out = time(profile.shift_end.hour, out_min)
                status = 'PRESENT'
                late_mins = 0
            elif rand_roll < 0.90:
                # Late arrival
                late_mins = random.randint(18, 45)
                late_dt = datetime.combine(datetime(2000,1,1), profile.shift_start) + timedelta(minutes=late_mins)
                t_in = late_dt.time()
                t_out = time(profile.shift_end.hour, random.randint(15, 45))
                status = 'LATE'
            else:
                # Half-day or leave
                t_in = time(profile.shift_start.hour, random.randint(0, 10))
                t_out = time(12, 0)
                status = 'HALF_DAY'
                late_mins = 0

            rec = AttendanceRecord(
                employee=profile,
                date=target_date,
                time_in=t_in,
                time_out=t_out,
                status=status,
                late_minutes=late_mins,
                ip_address='192.168.1.10'
            )
            rec.calculate_hours_and_overtime()
            rec.save()
            created_logs += 1

    # Record initial audit entry
    AuditLog.objects.create(
        user=admin_user,
        action="DATABASE_SEED",
        details="Initial system seeder executed with default accounts and 14 days of realistic logs."
    )

    print(f"\n[+] Seeding complete! Generated {created_logs} attendance records.")
    print("--------------------------------------------------")
    print("[*] Login Credentials for Testing & Presentation:")
    print("  Administrator : Username = admin           | Password = admin123")
    print("  Staff Member  : Username = juan.delacruz   | Password = password123")
    print("  Staff Member  : Username = maria.santos    | Password = password123")
    print("--------------------------------------------------")


if __name__ == '__main__':
    seed_database()
