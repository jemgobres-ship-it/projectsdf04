from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import time, datetime, timedelta
from decimal import Decimal


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def employee_count(self):
        return self.employees.count()


class EmployeeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    employee_id = models.CharField(max_length=30, unique=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    job_title = models.CharField(max_length=100, default='Staff')
    contact_number = models.CharField(max_length=20, blank=True, default='')
    hire_date = models.DateField(default=timezone.localdate)
    shift_start = models.TimeField(default=time(8, 0))   # 8:00 AM standard
    shift_end = models.TimeField(default=time(17, 0))    # 5:00 PM standard
    grace_period_minutes = models.IntegerField(default=15)  # 15 minutes grace period
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['employee_id']

    def __str__(self):
        return f"[{self.employee_id}] {self.user.get_full_name() or self.user.username}"

    @property
    def full_name(self):
        name = self.user.get_full_name()
        return name if name else self.user.username

    @property
    def is_admin(self):
        return self.user.is_staff or self.user.is_superuser


class AttendanceRecord(models.Model):
    STATUS_CHOICES = [
        ('PRESENT', 'Present (On-Time)'),
        ('LATE', 'Late Arrival'),
        ('HALF_DAY', 'Half Day'),
        ('ABSENT', 'Absent'),
        ('ON_LEAVE', 'On Leave'),
    ]

    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=timezone.localdate, db_index=True)
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PRESENT')
    late_minutes = models.IntegerField(default=0)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-time_in']
        constraints = [
            models.UniqueConstraint(fields=['employee', 'date'], name='unique_employee_daily_attendance')
        ]

    def __str__(self):
        return f"{self.employee.employee_id} - {self.date} ({self.status})"

    def calculate_hours_and_overtime(self):
        """Helper to calculate total hours worked and overtime against shift_end"""
        if not self.time_in or not self.time_out:
            return

        dummy_date = datetime(2000, 1, 1)
        dt_in = datetime.combine(dummy_date, self.time_in)
        dt_out = datetime.combine(dummy_date, self.time_out)

        if dt_out < dt_in:
            dt_out += timedelta(days=1)

        if dt_out > dt_in:
            duration = dt_out - dt_in
            hours = Decimal(str(round(duration.total_seconds() / 3600.0, 2)))
            # Subtract 1 hour for standard lunch break if worked > 5 hours
            net_hours = max(Decimal('0.00'), hours - Decimal('1.00')) if hours >= Decimal('5.00') else hours
            self.total_hours = net_hours

            # Calculate overtime if clocked out after shift_end
            shift_end_dt = datetime.combine(dummy_date, self.employee.shift_end)
            if self.employee.shift_end < self.employee.shift_start:
                shift_end_dt += timedelta(days=1)

            if dt_out > shift_end_dt:
                ot_duration = dt_out - shift_end_dt
                ot_hrs = Decimal(str(round(ot_duration.total_seconds() / 3600.0, 2)))
                self.overtime_hours = max(Decimal('0.00'), ot_hrs)
            else:
                self.overtime_hours = Decimal('0.00')


class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=60)
    details = models.TextField()
    ip_address = models.CharField(max_length=45, blank=True, default='')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        user_str = self.user.username if self.user else 'System'
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {user_str}: {self.action}"
