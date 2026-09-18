"""
OOP Module: Dashboard Analytics & Overview
Proposal Mapping: Dashboard Module
Key Classes: Dashboard, DashboardController
"""

from typing import Dict, Any, List
from datetime import date, datetime
from django.utils import timezone
from django.db.models import Count, Q
from core.models import AttendanceRecord, EmployeeProfile, Department
from core.oop_classes.time_tracker import AttendanceLog, TimeTracker


class Dashboard:
    """
    Domain Entity representing the aggregated state of the Dashboard.
    Encapsulates high-level KPI metrics, attendance percentage, and visualization data.
    """
    def __init__(self, metrics: Dict[str, Any]):
        self.total_employees: int = metrics.get('total_employees', 0)
        self.present_count: int = metrics.get('present_count', 0)
        self.late_count: int = metrics.get('late_count', 0)
        self.absent_count: int = metrics.get('absent_count', 0)
        self.attendance_rate: float = metrics.get('attendance_rate', 0.0)
        self.recent_logs: List[AttendanceLog] = metrics.get('recent_logs', [])
        self.dept_breakdown: List[Dict[str, Any]] = metrics.get('dept_breakdown', [])
        self.today_date: date = metrics.get('today_date', timezone.localdate())

    @property
    def formatted_today(self) -> str:
        return self.today_date.strftime("%A, %B %d, %Y")

    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_employees': self.total_employees,
            'present_count': self.present_count,
            'late_count': self.late_count,
            'absent_count': self.absent_count,
            'attendance_rate': self.attendance_rate,
            'recent_logs': self.recent_logs,
            'dept_breakdown': self.dept_breakdown,
            'formatted_today': self.formatted_today,
        }


class DashboardController:
    """
    Controller/Service Class responsible for aggregating live attendance stats,
    calculating KPI ratios, and preparing view-models for Admin and Employee Dashboards.
    """

    @classmethod
    def get_admin_dashboard(cls, target_date: date = None) -> Dashboard:
        """
        Compiles administrative metrics:
        - Total Active Staff
        - Present Today (on time)
        - Late Today
        - Absent Today (estimated based on active staff without clock-in)
        - Attendance % Rate
        - Recent Live Activity Feed
        - Department Attendance breakdown
        """
        check_date = target_date or timezone.localdate()

        total_active_employees = EmployeeProfile.objects.filter(is_active=True, user__is_active=True).count()

        today_records = AttendanceRecord.objects.filter(date=check_date)
        present_count = today_records.filter(status='PRESENT').count()
        late_count = today_records.filter(status='LATE').count()
        total_clocked_in = present_count + late_count

        # Employees who haven't logged in yet today
        absent_count = max(0, total_active_employees - total_clocked_in)

        # Calculate rate
        attendance_rate = round((total_clocked_in / total_active_employees * 100), 1) if total_active_employees > 0 else 0.0

        # Recent 10 live logs
        recent_records = AttendanceRecord.objects.select_related(
            'employee__user', 'employee__department'
        ).filter(date=check_date).order_by('-updated_at')[:10]
        recent_logs = [AttendanceLog(r) for r in recent_records]

        # Department Breakdown
        dept_breakdown = []
        departments = Department.objects.prefetch_related('employees').all()
        for dept in departments:
            dept_emp_ids = dept.employees.filter(is_active=True).values_list('id', flat=True)
            dept_total = len(dept_emp_ids)
            dept_present = today_records.filter(employee_id__in=dept_emp_ids).count()
            dept_breakdown.append({
                'name': dept.name,
                'code': dept.code,
                'total': dept_total,
                'present': dept_present,
                'rate': round((dept_present / dept_total * 100), 1) if dept_total > 0 else 0.0
            })

        return Dashboard({
            'total_employees': total_active_employees,
            'present_count': present_count,
            'late_count': late_count,
            'absent_count': absent_count,
            'attendance_rate': attendance_rate,
            'recent_logs': recent_logs,
            'dept_breakdown': dept_breakdown,
            'today_date': check_date,
        })

    @classmethod
    def get_employee_dashboard(cls, employee_profile: EmployeeProfile, target_date: date = None) -> Dict[str, Any]:
        """
        Compiles personal metrics for an individual employee:
        - Today's Attendance State (Not Clocked In / Clocked In / Clocked Out)
        - Monthly Summary (Days Present, Days Late, Total Hours Worked)
        - Last 10 days attendance records
        """
        check_date = target_date or timezone.localdate()
        today_log = TimeTracker.get_today_log(employee_profile, check_date)

        # Current month statistics
        first_of_month = check_date.replace(day=1)
        monthly_records = AttendanceRecord.objects.filter(
            employee=employee_profile,
            date__gte=first_of_month,
            date__lte=check_date
        )

        monthly_present = monthly_records.filter(status='PRESENT').count()
        monthly_late = monthly_records.filter(status='LATE').count()
        total_monthly_hours = sum(float(r.total_hours) for r in monthly_records)
        total_monthly_ot = sum(float(r.overtime_hours) for r in monthly_records)

        # Recent 10 attendance records
        recent_personal_records = AttendanceRecord.objects.filter(
            employee=employee_profile
        ).order_by('-date')[:10]
        recent_logs = [AttendanceLog(r) for r in recent_personal_records]

        return {
            'employee': employee_profile,
            'today_log': today_log,
            'today_date': check_date.strftime("%A, %B %d, %Y"),
            'monthly_present': monthly_present,
            'monthly_late': monthly_late,
            'monthly_hours': round(total_monthly_hours, 2),
            'monthly_ot': round(total_monthly_ot, 2),
            'recent_logs': recent_logs,
            'shift_start_display': employee_profile.shift_start.strftime("%I:%M %p"),
            'shift_end_display': employee_profile.shift_end.strftime("%I:%M %p"),
        }
