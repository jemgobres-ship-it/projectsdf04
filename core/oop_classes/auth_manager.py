"""
OOP Module: Authentication & Role-Based Access Control (RBAC)
Proposal Mapping: Login / Authentication Module
Key Classes: User, AuthManager
"""

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User as DjangoUser
from core.models import EmployeeProfile, AuditLog


class User:
    """
    Domain Entity representing an authenticated or target user in the system.
    Demonstrates OOP Encapsulation: encapsulating user identity, roles, and profile state.
    """
    def __init__(self, django_user: DjangoUser):
        self._django_user = django_user
        self.username = django_user.username
        self.email = django_user.email
        self.first_name = django_user.first_name
        self.last_name = django_user.last_name
        self.is_staff = django_user.is_staff
        self.is_superuser = django_user.is_superuser
        self.is_active = django_user.is_active

    @property
    def full_name(self) -> str:
        name = f"{self.first_name} {self.last_name}".strip()
        return name if name else self.username

    @property
    def is_admin(self) -> bool:
        """Role check: Administrator / HR privileges"""
        return self.is_staff or self.is_superuser

    @property
    def is_employee(self) -> bool:
        """Role check: Regular staff member"""
        return not self.is_admin

    @property
    def profile(self):
        """Encapsulated access to the linked EmployeeProfile model"""
        try:
            return self._django_user.profile
        except EmployeeProfile.DoesNotExist:
            return None

    def get_raw_user(self) -> DjangoUser:
        """Protected accessor to underlying Django ORM user"""
        return self._django_user

    def __str__(self):
        role_label = "Administrator" if self.is_admin else "Employee"
        return f"{self.full_name} ({self.username}) - [{role_label}]"


class AuthManager:
    """
    Service/Manager Class handling User Authentication, Authorization, and Session Management.
    Demonstrates OOP Service Pattern & Single Responsibility Principle.
    """
    @classmethod
    def authenticate_user(cls, request, username, password, ip_address=''):
        """
        Authenticates credentials and establishes session if valid.
        Returns tuple: (is_success: bool, user_or_error: User | str)
        """
        if not username or not password:
            return False, "Username and password are required."

        auth_user = authenticate(request, username=username, password=password)
        if auth_user is None:
            return False, "Invalid username or password."

        if not auth_user.is_active:
            return False, "Your account has been deactivated. Please contact HR/Admin."

        # Establish Django session
        login(request, auth_user)

        # Record Audit Log
        AuditLog.objects.create(
            user=auth_user,
            action="USER_LOGIN",
            details=f"User {auth_user.username} logged in successfully.",
            ip_address=ip_address
        )

        return True, User(auth_user)

    @classmethod
    def logout_user(cls, request, ip_address=''):
        """Terminates session and records audit event"""
        raw_user = request.user
        if raw_user.is_authenticated:
            AuditLog.objects.create(
                user=raw_user,
                action="USER_LOGOUT",
                details=f"User {raw_user.username} logged out.",
                ip_address=ip_address
            )
        logout(request)

    @classmethod
    def get_current_user(cls, request) -> User | None:
        """Wraps request.user into the Domain User object"""
        if request.user.is_authenticated:
            return User(request.user)
        return None

    @classmethod
    def has_admin_access(cls, request) -> bool:
        """Strict authorization gate for admin/HR views"""
        user = cls.get_current_user(request)
        return user is not None and user.is_admin
