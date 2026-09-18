"""
OOP Module: Attendance Tracker & Timekeeping Engine
Proposal Mapping: Attendance Tracker Module
Key Classes: AttendanceLog, TimeTracker
"""

from typing import Optional, List, Tuple
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from django.utils import timezone
from core.models import AttendanceRecord, EmployeeProfile, AuditLog
from core.oop_classes.employee_manager import Employee


class AttendanceLog:
    """
    Domain Entity representing an attendance event or daily record.
    Encapsulates date, timestamps, computed duration, status badges, and penalties.
    """
    def __init__(self, record: AttendanceRecord):
        self._record = record
        self.id = record.id
        self.employee_id = record.employee.employee_id
        self.employee_name = record.employee.full_name
        self.department = record.employee.department.name if record.employee.department else "Unassigned"
        self.date = record.date
        self.time_in = record.time_in
        self.time_out = record.time_out
        self.status = record.status
        self.late_minutes = record.late_minutes
        self.overtime_hours = float(record.overtime_hours)
        self.total_hours = float(record.total_hours)
        self.ip_address = record.ip_address
        self.notes = record.notes
        self.created_at = record.created_at

    @property
    def formatted_date(self) -> str:
        return self.date.strftime("%b %d, %Y (%a)")

    @property
    def formatted_time_in(self) -> str:
        return self.time_in.strftime("%I:%M:%S %p") if self.time_in else "--:--:--"

    @property
    def formatted_time_out(self) -> str:
        return self.time_out.strftime("%I:%M:%S %p") if self.time_out else "--:--:--"

    @property
    def status_badge_class(self) -> str:
        """Helper for frontend CSS badge rendering"""
        mapping = {
            'PRESENT': 'badge-success',
            'LATE': 'badge-warning',
            'HALF_DAY': 'badge-info',
            'ABSENT': 'badge-danger',
            'ON_LEAVE': 'badge-secondary',
        }
        return mapping.get(self.status, 'badge-light')

    @property
    def is_clocked_in(self) -> bool:
        return self.time_in is not None and self.time_out is None

    @property
    def is_clocked_out(self) -> bool:
        return self.time_out is not None

    def get_raw_record(self) -> AttendanceRecord:
        return self._record

    def __str__(self):
        return f"{self.employee_name} [{self.date}] In: {self.formatted_time_in} | Out: {self.formatted_time_out} | {self.status}"


class TimeTracker:
    """
    Core Timekeeping Engine & Business Logic Controller.
    Implements business rules: Tardiness detection, Overtime calculation,
    Double-entry prevention, and State transitions (Time In -> Time Out).
    """

    @classmethod
    def get_today_log(cls, employee_profile: EmployeeProfile, target_date: Optional[date] = None) -> Optional[AttendanceLog]:
        """Checks if a log already exists for the given date"""
        check_date = target_date or timezone.localdate()
        record = AttendanceRecord.objects.filter(employee=employee_profile, date=check_date).first()
        return AttendanceLog(record) if record else None

    @classmethod
    def record_time_in(cls, employee_profile: EmployeeProfile, check_time: Optional[time] = None,
                       check_date: Optional[date] = None, ip_address: str = '') -> Tuple[bool, str, Optional[AttendanceLog]]:
        """
        Processes a Time-In punch for an employee.
        Business Rules:
        1. Only one Time-In per calendar day is allowed.
        2. Compares timestamp against shift_start + grace_period_minutes.
        3. If after grace period, calculates late_minutes and marks status as 'LATE'.
        4. Otherwise marks status as 'PRESENT'.
        """
        now = timezone.localtime()
        log_date = check_date or now.date()
        log_time = check_time or now.time()

        # Check existing record
        existing = AttendanceRecord.objects.filter(employee=employee_profile, date=log_date).first()
        if existing and existing.time_in:
            return False, f"You have already clocked in today at {existing.time_in.strftime('%I:%M %p')}.", AttendanceLog(existing)

        # Calculate tardiness
        shift_start = employee_profile.shift_start
        grace_mins = employee_profile.grace_period_minutes

        # Convert to datetime on a dummy day to compare minutes accurately
        dummy = datetime(2000, 1, 1)
        shift_dt = datetime.combine(dummy, shift_start)
        actual_dt = datetime.combine(dummy, log_time)
        grace_limit_dt = shift_dt + timedelta(minutes=grace_mins)

        status = 'PRESENT'
        late_minutes = 0

        if actual_dt > grace_limit_dt:
            status = 'LATE'
            diff = actual_dt - shift_dt
            late_minutes = int(diff.total_seconds() // 60)

        # Create or update record
        record, created = AttendanceRecord.objects.get_or_create(
            employee=employee_profile,
            date=log_date,
            defaults={
                'time_in': log_time,
                'status': status,
                'late_minutes': late_minutes,
                'ip_address': ip_address,
            }
        )

        if not created and not record.time_in:
            record.time_in = log_time
            record.status = status
            record.late_minutes = late_minutes
            record.ip_address = ip_address
            record.save()

        # Log audit trail
        AuditLog.objects.create(
            user=employee_profile.user,
            action="TIME_IN",
            details=f"Employee {employee_profile.employee_id} clocked in at {log_time.strftime('%H:%M:%S')} (Status: {status}, Late: {late_minutes}m)",
            ip_address=ip_address
        )

        msg = f"Time-In successfully recorded at {log_time.strftime('%I:%M:%S %p')}!"
        if status == 'LATE':
            msg += f" (Late by {late_minutes} minutes)"

        return True, msg, AttendanceLog(record)

    @classmethod
    def record_time_out(cls, employee_profile: EmployeeProfile, check_time: Optional[time] = None,
                        check_date: Optional[date] = None, ip_address: str = '') -> Tuple[bool, str, Optional[AttendanceLog]]:
        """
        Processes a Time-Out punch for an employee.
        Business Rules:
        1. Must have clocked in first.
        2. Cannot clock out twice if already recorded.
        3. Computes total working hours and overtime.
        """
        now = timezone.localtime()
        log_date = check_date or now.date()
        log_time = check_time or now.time()

        record = AttendanceRecord.objects.filter(employee=employee_profile, date=log_date).first()

        if not record or not record.time_in:
            return False, "You cannot Clock Out because no Time-In record was found for today.", None

        if record.time_out:
            return False, f"You have already clocked out today at {record.time_out.strftime('%I:%M %p')}.", AttendanceLog(record)

        # Set time out and compute hours
        record.time_out = log_time
        record.calculate_hours_and_overtime()
        record.save()

        # Log audit trail
        AuditLog.objects.create(
            user=employee_profile.user,
            action="TIME_OUT",
            details=f"Employee {employee_profile.employee_id} clocked out at {log_time.strftime('%H:%M:%S')} (Total: {record.total_hours}h, OT: {record.overtime_hours}h)",
            ip_address=ip_address
        )

        msg = f"Time-Out successfully recorded at {log_time.strftime('%I:%M:%S %p')}. Total Hours: {record.total_hours} hrs."
        if record.overtime_hours > 0:
            msg += f" (Overtime: {record.overtime_hours} hrs)"

        return True, msg, AttendanceLog(record)

    @classmethod
    def get_logs_for_employee(cls, employee_profile: EmployeeProfile, start_date: Optional[date] = None,
                              end_date: Optional[date] = None) -> List[AttendanceLog]:
        """Fetches attendance records for a specific employee within date range"""
        qs = AttendanceRecord.objects.filter(employee=employee_profile)
        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)
        return [AttendanceLog(r) for r in qs.order_by('-date')]

    @classmethod
    def get_all_logs(cls, start_date: Optional[date] = None, end_date: Optional[date] = None,
                     department_id: Optional[int] = None, status: Optional[str] = None) -> List[AttendanceLog]:
        """Fetches all company attendance records with multi-criteria filtering"""
        qs = AttendanceRecord.objects.select_related('employee__user', 'employee__department')
        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)
        if department_id:
            qs = qs.filter(employee__department_id=department_id)
        if status:
            qs = qs.filter(status=status)
        return [AttendanceLog(r) for r in qs.order_by('-date', '-time_in')]

    @classmethod
    def admin_adjust_record(cls, record_id: int, time_in: Optional[time], time_out: Optional[time],
                            status: str, notes: str, admin_user) -> Tuple[bool, str]:
        """Admin correction mechanism with mandatory audit logging"""
        try:
            record = AttendanceRecord.objects.select_related('employee__user').get(id=record_id)
        except AttendanceRecord.DoesNotExist:
            return False, "Attendance record not found."

        old_details = f"In: {record.time_in}, Out: {record.time_out}, Status: {record.status}"

        record.time_in = time_in
        record.time_out = time_out
        record.status = status
        record.notes = notes
        record.calculate_hours_and_overtime()
        record.save()

        new_details = f"In: {record.time_in}, Out: {record.time_out}, Status: {record.status}, Notes: {notes}"

        AuditLog.objects.create(
            user=admin_user,
            action="MANUAL_ATTENDANCE_ADJUSTMENT",
            details=f"Admin {admin_user.username} adjusted record for {record.employee.employee_id} on {record.date}. Before: [{old_details}] -> After: [{new_details}]"
        )

        return True, "Attendance record successfully updated."
