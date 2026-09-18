"""
OOP Module: Records Management
Proposal Mapping: Records Management Module (CRUD operations)
Key Classes: Employee, EmployeeManager
"""

from typing import List, Optional, Dict, Any
from django.contrib.auth.models import User as DjangoUser
from django.db import transaction, models
from core.models import EmployeeProfile, Department, AuditLog
from datetime import time, date


class Employee:
    """
    Domain Entity representing an Employee.
    Demonstrates OOP Encapsulation of employee properties, shifts, and business rules.
    """
    def __init__(self, profile: EmployeeProfile):
        self._profile = profile
        self.id = profile.id
        self.employee_id = profile.employee_id
        self.user_id = profile.user.id
        self.username = profile.user.username
        self.first_name = profile.user.first_name
        self.last_name = profile.user.last_name
        self.email = profile.user.email
        self.department = profile.department.name if profile.department else "Unassigned"
        self.department_id = profile.department_id
        self.job_title = profile.job_title
        self.contact_number = profile.contact_number
        self.hire_date = profile.hire_date
        self.shift_start = profile.shift_start
        self.shift_end = profile.shift_end
        self.grace_period_minutes = profile.grace_period_minutes
        self.is_active = profile.is_active

    @property
    def full_name(self) -> str:
        name = f"{self.first_name} {self.last_name}".strip()
        return name if name else self.username

    @property
    def shift_display(self) -> str:
        """Formats shift schedule nicely e.g., 08:00 AM - 05:00 PM"""
        start_fmt = self.shift_start.strftime("%I:%M %p") if self.shift_start else "N/A"
        end_fmt = self.shift_end.strftime("%I:%M %p") if self.shift_end else "N/A"
        return f"{start_fmt} - {end_fmt}"

    def get_raw_profile(self) -> EmployeeProfile:
        return self._profile

    def __str__(self):
        return f"[{self.employee_id}] {self.full_name} ({self.job_title})"


class EmployeeManager:
    """
    Service/Manager Class for managing Employee entities and database CRUD operations.
    Encapsulates transaction integrity, data validation, and audit tracking.
    """

    @classmethod
    def get_all_employees(cls, active_only: bool = False) -> List[Employee]:
        """Retrieves list of employees wrapped in domain Employee objects"""
        qs = EmployeeProfile.objects.select_related('user', 'department')
        if active_only:
            qs = qs.filter(is_active=True, user__is_active=True)
        return [Employee(p) for p in qs]

    @classmethod
    def get_employee_by_id(cls, profile_id: int) -> Optional[Employee]:
        """Finds employee by primary key"""
        try:
            profile = EmployeeProfile.objects.select_related('user', 'department').get(id=profile_id)
            return Employee(profile)
        except EmployeeProfile.DoesNotExist:
            return None

    @classmethod
    def get_employee_by_employee_id(cls, emp_id_code: str) -> Optional[Employee]:
        """Finds employee by employee code string e.g., EMP-001"""
        try:
            profile = EmployeeProfile.objects.select_related('user', 'department').get(employee_id=emp_id_code)
            return Employee(profile)
        except EmployeeProfile.DoesNotExist:
            return None

    @classmethod
    def get_employee_by_user(cls, django_user: DjangoUser) -> Optional[Employee]:
        """Finds employee entity corresponding to a Django User"""
        try:
            profile = EmployeeProfile.objects.select_related('user', 'department').get(user=django_user)
            return Employee(profile)
        except EmployeeProfile.DoesNotExist:
            return None

    @classmethod
    @transaction.atomic
    def create_employee(cls, data: Dict[str, Any], actor_user: Optional[DjangoUser] = None) -> tuple[bool, Any]:
        """
        Creates a new User account and associated EmployeeProfile in a single atomic transaction.
        """
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        employee_id = data.get('employee_id', '').strip()
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()

        # Validations
        if not username or not password or not employee_id:
            return False, "Username, password, and Employee ID are required."

        if DjangoUser.objects.filter(username=username).exists():
            return False, f"Username '{username}' is already taken."

        if EmployeeProfile.objects.filter(employee_id=employee_id).exists():
            return False, f"Employee ID '{employee_id}' is already registered."

        # Create Django User
        user = DjangoUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        department_id = data.get('department_id')
        department = None
        if department_id:
            try:
                department = Department.objects.get(id=department_id)
            except Department.DoesNotExist:
                pass

        # Create Profile
        profile = EmployeeProfile.objects.create(
            user=user,
            employee_id=employee_id,
            department=department,
            job_title=data.get('job_title', 'Staff').strip(),
            contact_number=data.get('contact_number', '').strip(),
            shift_start=data.get('shift_start') or time(8, 0),
            shift_end=data.get('shift_end') or time(17, 0),
            grace_period_minutes=int(data.get('grace_period_minutes', 15)),
            hire_date=data.get('hire_date') or date.today(),
            is_active=True
        )

        # Audit Log
        AuditLog.objects.create(
            user=actor_user,
            action="CREATE_EMPLOYEE",
            details=f"Created employee profile {employee_id} ({user.username})."
        )

        return True, Employee(profile)

    @classmethod
    @transaction.atomic
    def update_employee(cls, profile_id: int, data: Dict[str, Any], actor_user: Optional[DjangoUser] = None) -> tuple[bool, Any]:
        """Updates employee profile and user details"""
        try:
            profile = EmployeeProfile.objects.select_related('user').get(id=profile_id)
        except EmployeeProfile.DoesNotExist:
            return False, "Employee not found."

        user = profile.user
        if 'first_name' in data:
            user.first_name = data['first_name'].strip()
        if 'last_name' in data:
            user.last_name = data['last_name'].strip()
        if 'email' in data:
            user.email = data['email'].strip()
        if data.get('password'):
            user.set_password(data['password'].strip())
        user.save()

        if 'department_id' in data:
            dept_id = data['department_id']
            profile.department = Department.objects.filter(id=dept_id).first() if dept_id else None
        if 'job_title' in data:
            profile.job_title = data['job_title'].strip()
        if 'contact_number' in data:
            profile.contact_number = data['contact_number'].strip()
        if 'shift_start' in data and data['shift_start']:
            profile.shift_start = data['shift_start']
        if 'shift_end' in data and data['shift_end']:
            profile.shift_end = data['shift_end']
        if 'grace_period_minutes' in data:
            profile.grace_period_minutes = int(data['grace_period_minutes'])
        if 'is_active' in data:
            profile.is_active = bool(data['is_active'])
            user.is_active = bool(data['is_active'])
            user.save()

        profile.save()

        AuditLog.objects.create(
            user=actor_user,
            action="UPDATE_EMPLOYEE",
            details=f"Updated profile for {profile.employee_id} ({user.username})."
        )

        return True, Employee(profile)

    @classmethod
    @transaction.atomic
    def delete_employee(cls, profile_id: int, actor_user: Optional[DjangoUser] = None) -> tuple[bool, str]:
        """Deactivates/deletes employee record safely"""
        try:
            profile = EmployeeProfile.objects.select_related('user').get(id=profile_id)
        except EmployeeProfile.DoesNotExist:
            return False, "Employee does not exist."

        emp_code = profile.employee_id
        username = profile.user.username
        user = profile.user

        # Delete user (cascades profile, but audit log remains)
        user.delete()

        AuditLog.objects.create(
            user=actor_user,
            action="DELETE_EMPLOYEE",
            details=f"Deleted employee {emp_code} (Username: {username})."
        )
        return True, f"Employee {emp_code} successfully deleted."

    @classmethod
    def search_employees(cls, query: str, department_id: Optional[int] = None) -> List[Employee]:
        """Filters employee records by search keywords and department"""
        qs = EmployeeProfile.objects.select_related('user', 'department')
        if department_id:
            qs = qs.filter(department_id=department_id)
        if query:
            query = query.strip()
            qs = qs.filter(
                models.Q(employee_id__icontains=query) |
                models.Q(user__first_name__icontains=query) |
                models.Q(user__last_name__icontains=query) |
                models.Q(user__username__icontains=query) |
                models.Q(job_title__icontains=query)
            )
        return [Employee(p) for p in qs]
