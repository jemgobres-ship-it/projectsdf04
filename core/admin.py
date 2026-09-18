from django.contrib import admin
from core.models import Department, EmployeeProfile, AttendanceRecord, AuditLog


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'employee_count', 'created_at')
    search_fields = ('name', 'code')


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'full_name', 'department', 'job_title', 'shift_start', 'shift_end', 'is_active')
    list_filter = ('department', 'is_active')
    search_fields = ('employee_id', 'user__first_name', 'user__last_name', 'user__username', 'job_title')


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'time_in', 'time_out', 'status', 'late_minutes', 'total_hours', 'overtime_hours')
    list_filter = ('status', 'date', 'employee__department')
    search_fields = ('employee__employee_id', 'employee__user__first_name', 'employee__user__last_name')
    date_hierarchy = 'date'


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'details', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('action', 'details', 'user__username')
    readonly_fields = ('timestamp', 'user', 'action', 'details', 'ip_address')
