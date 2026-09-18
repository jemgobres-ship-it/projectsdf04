from django import forms
from django.contrib.auth.models import User
from core.models import EmployeeProfile, Department, AttendanceRecord
from datetime import time, date


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your username', 'autofocus': True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'})
    )


class EmployeeCreateForm(forms.Form):
    employee_id = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. EMP-2026-001'})
    )
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Juan'})
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Dela Cruz'})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'e.g. juan@company.com'})
    )
    username = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. juan.delacruz'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Temporary Password'})
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    job_title = forms.CharField(
        max_length=100,
        initial='Staff',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. IT Specialist'})
    )
    contact_number = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 09171234567'})
    )
    shift_start = forms.TimeField(
        initial=time(8, 0),
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    shift_end = forms.TimeField(
        initial=time(17, 0),
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    grace_period_minutes = forms.IntegerField(
        initial=15,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 60})
    )
    hire_date = forms.DateField(
        initial=date.today,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(f"Username '{username}' is already taken.")
        return username

    def clean_employee_id(self):
        emp_id = self.cleaned_data['employee_id'].strip()
        if EmployeeProfile.objects.filter(employee_id=emp_id).exists():
            raise forms.ValidationError(f"Employee ID '{emp_id}' already exists.")
        return emp_id


class EmployeeUpdateForm(forms.Form):
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    job_title = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    contact_number = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    shift_start = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    shift_end = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    grace_period_minutes = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 60})
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank to keep current password'})
    )


class AttendanceAdjustmentForm(forms.Form):
    time_in = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    time_out = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    status = forms.ChoiceField(
        choices=AttendanceRecord.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Reason for adjustment (Mandatory for audit trail)'})
    )


class ReportFilterForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        empty_label="All Departments",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + AttendanceRecord.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
