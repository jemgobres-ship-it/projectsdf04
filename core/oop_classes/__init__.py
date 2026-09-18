"""
SDF04 Object-Oriented Programming (OOP) Domain & Service Architecture
Contains pure domain entities and manager/controller classes:
- AuthManager & User
- EmployeeManager & Employee
- TimeTracker & AttendanceLog
- DashboardController & Dashboard
- ReportGenerator & Report
"""

from .auth_manager import User, AuthManager
from .employee_manager import Employee, EmployeeManager
from .time_tracker import AttendanceLog, TimeTracker
from .dashboard_controller import Dashboard, DashboardController
from .report_generator import Report, ReportGenerator

__all__ = [
    'User',
    'AuthManager',
    'Employee',
    'EmployeeManager',
    'AttendanceLog',
    'TimeTracker',
    'Dashboard',
    'DashboardController',
    'Report',
    'ReportGenerator',
]
