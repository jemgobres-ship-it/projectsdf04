from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, date

from core.models import EmployeeProfile, Department, AttendanceRecord, AuditLog
from core.forms import (
    LoginForm, EmployeeCreateForm, EmployeeUpdateForm,
    AttendanceAdjustmentForm, ReportFilterForm
)
from core.oop_classes.auth_manager import AuthManager
from core.oop_classes.employee_manager import EmployeeManager
from core.oop_classes.time_tracker import TimeTracker
from core.oop_classes.dashboard_controller import DashboardController
from core.oop_classes.report_generator import ReportGenerator


def get_client_ip(request):
    """Helper to extract user client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip


# ==========================================
# 1. Authentication Views (AuthManager)
# ==========================================

def login_view(request):
    """User Login View delegating to AuthManager"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            ip_addr = get_client_ip(request)

            success, result = AuthManager.authenticate_user(request, username, password, ip_addr)
            if success:
                messages.success(request, f"Welcome back, {result.full_name}!")
                return redirect('dashboard')
            else:
                messages.error(request, result)
    else:
        form = LoginForm()

    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    """User Logout View delegating to AuthManager"""
    ip_addr = get_client_ip(request)
    AuthManager.logout_user(request, ip_addr)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


# ==========================================
# 2. Dashboard Views (DashboardController)
# ==========================================

@login_required
def dashboard_view(request):
    """
    Central Dashboard Router:
    - Admins/HR -> Admin Analytics & Company KPIs
    - Regular Employees -> Personal Clock & Attendance History
    """
    current_user = AuthManager.get_current_user(request)

    if current_user.is_admin:
        dashboard_data = DashboardController.get_admin_dashboard()
        return render(request, 'dashboard/admin_dashboard.html', {
            'dashboard': dashboard_data,
            'current_user': current_user
        })
    else:
        employee_profile = current_user.profile
        if not employee_profile:
            messages.warning(request, "No employee profile linked to your user account. Please contact Administrator.")
            return render(request, 'dashboard/no_profile.html')

        emp_data = DashboardController.get_employee_dashboard(employee_profile)
        return render(request, 'dashboard/employee_dashboard.html', {
            'data': emp_data,
            'current_user': current_user
        })


# ==========================================
# 3. Attendance Tracking Views (TimeTracker)
# ==========================================

@login_required
def clock_terminal_view(request):
    """
    Real-time interactive timekeeping screen.
    Employees can click 'Time In' or 'Time Out' with live clock feedback.
    """
    current_user = AuthManager.get_current_user(request)
    profile = current_user.profile

    if not profile:
        messages.error(request, "Employee profile required to clock in/out.")
        return redirect('dashboard')

    today_log = TimeTracker.get_today_log(profile)

    if request.method == 'POST':
        action = request.POST.get('action')
        ip_addr = get_client_ip(request)

        if action == 'time_in':
            success, msg, log = TimeTracker.record_time_in(profile, ip_address=ip_addr)
            if success:
                messages.success(request, msg)
            else:
                messages.warning(request, msg)
        elif action == 'time_out':
            success, msg, log = TimeTracker.record_time_out(profile, ip_address=ip_addr)
            if success:
                messages.success(request, msg)
            else:
                messages.warning(request, msg)

        return redirect('clock_terminal')

    return render(request, 'attendance/clock.html', {
        'profile': profile,
        'today_log': today_log,
        'current_time': timezone.localtime(),
        'current_user': current_user
    })


@login_required
def attendance_logs_view(request):
    """
    Attendance Master Log:
    - Admins see entire company with filters
    - Employees see only their personal history
    """
    current_user = AuthManager.get_current_user(request)

    # Date range filters from GET parameters
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    dept_id_str = request.GET.get('department')
    status = request.GET.get('status')

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
    dept_id = int(dept_id_str) if dept_id_str and dept_id_str.isdigit() else None

    if current_user.is_admin:
        logs = TimeTracker.get_all_logs(start_date=start_date, end_date=end_date, department_id=dept_id, status=status)
        departments = Department.objects.all()
        return render(request, 'attendance/log_list.html', {
            'logs': logs,
            'departments': departments,
            'start_date': start_date_str or '',
            'end_date': end_date_str or '',
            'selected_dept': dept_id,
            'selected_status': status or '',
            'current_user': current_user,
            'is_admin': True,
        })
    else:
        profile = current_user.profile
        logs = TimeTracker.get_logs_for_employee(profile, start_date=start_date, end_date=end_date)
        return render(request, 'attendance/log_list.html', {
            'logs': logs,
            'start_date': start_date_str or '',
            'end_date': end_date_str or '',
            'current_user': current_user,
            'is_admin': False,
        })


@login_required
def adjust_attendance_view(request, record_id):
    """Admin Adjustment View with mandatory audit logging"""
    if not AuthManager.has_admin_access(request):
        return HttpResponseForbidden("Admin access required.")

    record = get_object_or_404(AttendanceRecord, id=record_id)

    if request.method == 'POST':
        form = AttendanceAdjustmentForm(request.POST)
        if form.is_valid():
            t_in = form.cleaned_data['time_in']
            t_out = form.cleaned_data['time_out']
            status = form.cleaned_data['status']
            notes = form.cleaned_data['notes']

            success, msg = TimeTracker.admin_adjust_record(
                record_id=record.id,
                time_in=t_in,
                time_out=t_out,
                status=status,
                notes=notes,
                admin_user=request.user
            )
            if success:
                messages.success(request, msg)
                return redirect('attendance_logs')
            else:
                messages.error(request, msg)
    else:
        form = AttendanceAdjustmentForm(initial={
            'time_in': record.time_in,
            'time_out': record.time_out,
            'status': record.status,
            'notes': record.notes
        })

    return render(request, 'attendance/adjust_record.html', {
        'form': form,
        'record': record
    })


# ==========================================
# 4. Employee Records Management (EmployeeManager)
# ==========================================

@login_required
def employee_list_view(request):
    """Lists all employees with search and department filtering"""
    if not AuthManager.has_admin_access(request):
        return HttpResponseForbidden("Admin access required.")

    search_query = request.GET.get('q', '').strip()
    dept_id = request.GET.get('department')
    dept_id_int = int(dept_id) if dept_id and dept_id.isdigit() else None

    if search_query or dept_id_int:
        employees = EmployeeManager.search_employees(search_query, dept_id_int)
    else:
        employees = EmployeeManager.get_all_employees()

    departments = Department.objects.all()

    return render(request, 'employees/list.html', {
        'employees': employees,
        'departments': departments,
        'query': search_query,
        'selected_dept': dept_id_int
    })


@login_required
def employee_create_view(request):
    """Creates a new Employee and user account"""
    if not AuthManager.has_admin_access(request):
        return HttpResponseForbidden("Admin access required.")

    if request.method == 'POST':
        form = EmployeeCreateForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            dept = data.get('department')
            payload = {
                'username': data['username'],
                'password': data['password'],
                'employee_id': data['employee_id'],
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'email': data.get('email', ''),
                'department_id': dept.id if dept else None,
                'job_title': data['job_title'],
                'contact_number': data.get('contact_number', ''),
                'shift_start': data['shift_start'],
                'shift_end': data['shift_end'],
                'grace_period_minutes': data['grace_period_minutes'],
                'hire_date': data['hire_date'],
            }

            success, result = EmployeeManager.create_employee(payload, actor_user=request.user)
            if success:
                messages.success(request, f"Employee {result.full_name} ({result.employee_id}) created successfully!")
                return redirect('employee_list')
            else:
                messages.error(request, result)
    else:
        form = EmployeeCreateForm()

    return render(request, 'employees/form.html', {
        'form': form,
        'is_edit': False
    })


@login_required
def employee_update_view(request, profile_id):
    """Updates an existing employee's details"""
    if not AuthManager.has_admin_access(request):
        return HttpResponseForbidden("Admin access required.")

    profile = get_object_or_404(EmployeeProfile, id=profile_id)

    if request.method == 'POST':
        form = EmployeeUpdateForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            dept = data.get('department')
            payload = {
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'email': data.get('email', ''),
                'department_id': dept.id if dept else None,
                'job_title': data['job_title'],
                'contact_number': data.get('contact_number', ''),
                'shift_start': data['shift_start'],
                'shift_end': data['shift_end'],
                'grace_period_minutes': data['grace_period_minutes'],
                'is_active': data['is_active'],
            }
            if data.get('password'):
                payload['password'] = data['password']

            success, result = EmployeeManager.update_employee(profile.id, payload, actor_user=request.user)
            if success:
                messages.success(request, f"Employee {result.full_name} updated successfully!")
                return redirect('employee_list')
            else:
                messages.error(request, result)
    else:
        form = EmployeeUpdateForm(initial={
            'first_name': profile.user.first_name,
            'last_name': profile.user.last_name,
            'email': profile.user.email,
            'department': profile.department,
            'job_title': profile.job_title,
            'contact_number': profile.contact_number,
            'shift_start': profile.shift_start,
            'shift_end': profile.shift_end,
            'grace_period_minutes': profile.grace_period_minutes,
            'is_active': profile.is_active,
        })

    return render(request, 'employees/form.html', {
        'form': form,
        'profile': profile,
        'is_edit': True
    })


@login_required
def employee_delete_view(request, profile_id):
    """Deletes an employee record"""
    if not AuthManager.has_admin_access(request):
        return HttpResponseForbidden("Admin access required.")

    profile = get_object_or_404(EmployeeProfile, id=profile_id)

    if request.method == 'POST':
        success, msg = EmployeeManager.delete_employee(profile.id, actor_user=request.user)
        if success:
            messages.success(request, msg)
        else:
            messages.error(request, msg)
        return redirect('employee_list')

    return render(request, 'employees/confirm_delete.html', {'profile': profile})


# ==========================================
# 5. Reports & Exports (ReportGenerator - Pandas & ReportLab)
# ==========================================

@login_required
def reports_index_view(request):
    """Report Generation & Preview Center"""
    current_user = AuthManager.get_current_user(request)
    form = ReportFilterForm(request.GET or None)

    start_date = form.cleaned_data.get('start_date') if form.is_valid() else None
    end_date = form.cleaned_data.get('end_date') if form.is_valid() else None
    department = form.cleaned_data.get('department') if form.is_valid() else None
    status = form.cleaned_data.get('status') if form.is_valid() else None

    # Base query
    if current_user.is_admin:
        qs = AttendanceRecord.objects.select_related('employee__user', 'employee__department').all()
        if department:
            qs = qs.filter(employee__department=department)
    else:
        qs = AttendanceRecord.objects.select_related('employee__user', 'employee__department').filter(
            employee=current_user.profile
        )

    if start_date:
        qs = qs.filter(date__gte=start_date)
    if end_date:
        qs = qs.filter(date__lte=end_date)
    if status:
        qs = qs.filter(status=status)

    qs = qs.order_by('-date')

    # Summary calculations
    total_hours_sum = sum(float(r.total_hours) for r in qs)
    total_late_sum = sum(r.late_minutes for r in qs)
    total_ot_sum = sum(float(r.overtime_hours) for r in qs)

    return render(request, 'reports/index.html', {
        'form': form,
        'records': qs[:50],  # Preview limit
        'total_count': qs.count(),
        'total_hours': round(total_hours_sum, 2),
        'total_late': total_late_sum,
        'total_ot': round(total_ot_sum, 2),
        'is_admin': current_user.is_admin
    })


@login_required
def export_csv_view(request):
    """Exports filtered attendance to CSV using Pandas"""
    current_user = AuthManager.get_current_user(request)
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    dept_id = request.GET.get('department')
    status = request.GET.get('status')

    qs = AttendanceRecord.objects.select_related('employee__user', 'employee__department').all()

    if not current_user.is_admin:
        qs = qs.filter(employee=current_user.profile)
    elif dept_id and dept_id.isdigit():
        qs = qs.filter(employee__department_id=int(dept_id))

    if start_date_str:
        qs = qs.filter(date__gte=datetime.strptime(start_date_str, '%Y-%m-%d').date())
    if end_date_str:
        qs = qs.filter(date__lte=datetime.strptime(end_date_str, '%Y-%m-%d').date())
    if status:
        qs = qs.filter(status=status)

    csv_data = ReportGenerator.generate_csv_report(qs.order_by('-date'))

    response = HttpResponse(csv_data, content_type='text/csv')
    filename = f"Attendance_Report_{timezone.localdate().strftime('%Y%m%d')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def export_pdf_dtr_view(request):
    """Exports official PDF Daily Time Record (DTR) using ReportLab"""
    current_user = AuthManager.get_current_user(request)
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    emp_id_param = request.GET.get('employee_id')

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None

    employee_profile = None

    if current_user.is_admin:
        if emp_id_param and emp_id_param.isdigit():
            employee_profile = EmployeeProfile.objects.filter(id=int(emp_id_param)).first()
            qs = AttendanceRecord.objects.filter(employee=employee_profile)
        else:
            qs = AttendanceRecord.objects.select_related('employee__user', 'employee__department').all()
    else:
        employee_profile = current_user.profile
        qs = AttendanceRecord.objects.filter(employee=employee_profile)

    if start_date:
        qs = qs.filter(date__gte=start_date)
    if end_date:
        qs = qs.filter(date__lte=end_date)

    pdf_bytes = ReportGenerator.generate_pdf_dtr(
        queryset=qs.order_by('date'),
        report_title="Daily Time Record (DTR)",
        start_date=start_date,
        end_date=end_date,
        employee_profile=employee_profile
    )

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    target_name = employee_profile.employee_id if employee_profile else "Company_DTR"
    filename = f"DTR_{target_name}_{timezone.localdate().strftime('%Y%m%d')}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


@login_required
def audit_logs_view(request):
    """View system audit logs for administrative security verification"""
    if not AuthManager.has_admin_access(request):
        return HttpResponseForbidden("Admin access required.")

    logs = AuditLog.objects.select_related('user').all()[:100]
    return render(request, 'dashboard/audit_logs.html', {'logs': logs})
