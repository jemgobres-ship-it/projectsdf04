from django.urls import path
from . import views

urlpatterns = [
    # Dashboard & Auth
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Timekeeping & Attendance
    path('clock/', views.clock_terminal_view, name='clock_terminal'),
    path('attendance/', views.attendance_logs_view, name='attendance_logs'),
    path('attendance/<int:record_id>/adjust/', views.adjust_attendance_view, name='adjust_attendance'),

    # Employee Records Management (CRUD)
    path('employees/', views.employee_list_view, name='employee_list'),
    path('employees/create/', views.employee_create_view, name='employee_create'),
    path('employees/<int:profile_id>/edit/', views.employee_update_view, name='employee_update'),
    path('employees/<int:profile_id>/delete/', views.employee_delete_view, name='employee_delete'),

    # Reports & Exports (Pandas & ReportLab)
    path('reports/', views.reports_index_view, name='reports_index'),
    path('reports/export/csv/', views.export_csv_view, name='export_csv'),
    path('reports/export/pdf/', views.export_pdf_dtr_view, name='export_pdf_dtr'),

    # System Audit
    path('audit-logs/', views.audit_logs_view, name='audit_logs'),
]
