"""
OOP Module: Reports & Analytics
Proposal Mapping: Reports Module
Key Classes: Report, ReportGenerator
Uses pandas for data manipulation & CSV formatting
Uses reportlab for high-fidelity PDF DTR generation
"""

import io
from datetime import datetime, date
from typing import Optional, List, Dict, Any
import pandas as pd

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from core.models import AttendanceRecord, EmployeeProfile


class Report:
    """
    Domain Entity representing an Attendance Report.
    Encapsulates metadata, filtering parameters, record count, and statistical summary.
    """
    def __init__(self, title: str, start_date: date, end_date: date, total_records: int, summary: Dict[str, Any]):
        self.title = title
        self.start_date = start_date
        self.end_date = end_date
        self.total_records = total_records
        self.summary = summary
        self.generated_at = datetime.now()

    @property
    def formatted_range(self) -> str:
        s = self.start_date.strftime("%B %d, %Y") if self.start_date else "Beginning"
        e = self.end_date.strftime("%B %d, %Y") if self.end_date else "Present"
        return f"{s} to {e}"

    def __str__(self):
        return f"Report: {self.title} ({self.formatted_range}) - {self.total_records} records"


class ReportGenerator:
    """
    Service/Generator Class leveraging pandas & reportlab to produce
    enterprise-ready CSV exports and professional PDF Daily Time Records (DTR).
    """

    @classmethod
    def generate_csv_report(cls, queryset) -> bytes:
        """
        Uses pandas to process the AttendanceRecord queryset and generate
        a clean, structured CSV file.
        """
        data = []
        for r in queryset:
            data.append({
                'Employee ID': r.employee.employee_id,
                'Employee Name': r.employee.full_name,
                'Department': r.employee.department.name if r.employee.department else 'N/A',
                'Date': r.date.strftime('%Y-%m-%d'),
                'Time In': r.time_in.strftime('%I:%M:%S %p') if r.time_in else 'N/A',
                'Time Out': r.time_out.strftime('%I:%M:%S %p') if r.time_out else 'N/A',
                'Status': r.get_status_display(),
                'Late (Mins)': r.late_minutes,
                'Total Hours': float(r.total_hours),
                'Overtime (Hrs)': float(r.overtime_hours),
                'IP Address': r.ip_address or 'N/A',
                'Notes': r.notes or ''
            })

        if not data:
            df = pd.DataFrame(columns=[
                'Employee ID', 'Employee Name', 'Department', 'Date',
                'Time In', 'Time Out', 'Status', 'Late (Mins)', 'Total Hours',
                'Overtime (Hrs)', 'IP Address', 'Notes'
            ])
        else:
            df = pd.DataFrame(data)

        # Generate CSV string in UTF-8
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8')
        return csv_buffer.getvalue().encode('utf-8')

    @classmethod
    def generate_pdf_dtr(cls, queryset, report_title: str = "Daily Time Record (DTR)",
                         start_date: Optional[date] = None, end_date: Optional[date] = None,
                         employee_profile: Optional[EmployeeProfile] = None) -> bytes:
        """
        Uses reportlab to generate an official, print-ready PDF DTR document
        matching Philippine corporate and academic grading standards.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        elements = []
        styles = getSampleStyleSheet()

        # Custom Styles
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontSize=16,
            leading=20,
            alignment=1, # Center
            textColor=colors.HexColor('#1E293B'),
            fontName='Helvetica-Bold'
        )
        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            alignment=1, # Center
            textColor=colors.HexColor('#64748B'),
            fontName='Helvetica'
        )
        meta_style = ParagraphStyle(
            'MetaStyle',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#334155'),
            fontName='Helvetica'
        )
        meta_bold = ParagraphStyle(
            'MetaBold',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#0F172A'),
            fontName='Helvetica-Bold'
        )

        # Header Title
        elements.append(Paragraph("EMPLOYEE ATTENDANCE MANAGEMENT SYSTEM", subtitle_style))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(report_title, title_style))
        elements.append(Spacer(1, 6))

        # Date Range Subtitle
        date_range_str = "All Dates Recorded"
        if start_date and end_date:
            date_range_str = f"Period: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}"
        elif start_date:
            date_range_str = f"From: {start_date.strftime('%B %d, %Y')}"
        elements.append(Paragraph(date_range_str, subtitle_style))
        elements.append(Spacer(1, 10))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#3B82F6'), spaceAfter=12))

        # Metadata Card (If single employee or general report)
        if employee_profile:
            meta_data = [
                [Paragraph("<b>Employee ID:</b>", meta_bold), Paragraph(employee_profile.employee_id, meta_style),
                 Paragraph("<b>Department:</b>", meta_bold), Paragraph(employee_profile.department.name if employee_profile.department else "Unassigned", meta_style)],
                [Paragraph("<b>Employee Name:</b>", meta_bold), Paragraph(employee_profile.full_name, meta_style),
                 Paragraph("<b>Designation:</b>", meta_bold), Paragraph(employee_profile.job_title, meta_style)],
                [Paragraph("<b>Shift Schedule:</b>", meta_bold), Paragraph(f"{employee_profile.shift_start.strftime('%I:%M %p')} - {employee_profile.shift_end.strftime('%I:%M %p')}", meta_style),
                 Paragraph("<b>Generated Date:</b>", meta_bold), Paragraph(datetime.now().strftime('%Y-%m-%d %I:%M %p'), meta_style)],
            ]
            meta_table = Table(meta_data, colWidths=[1.3*inch, 2.3*inch, 1.3*inch, 2.3*inch])
            meta_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
                ('PADDING', (0,0), (-1,-1), 4),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            elements.append(meta_table)
            elements.append(Spacer(1, 14))

        # Attendance Table Headers & Data
        table_headers = ['Date', 'Day', 'Time In', 'Time Out', 'Status', 'Late', 'Hours', 'OT']
        if not employee_profile:
            table_headers = ['Emp ID', 'Name', 'Date', 'Time In', 'Time Out', 'Status', 'Late', 'Hours']

        table_rows = [table_headers]

        total_hours_sum = 0.0
        total_late_sum = 0
        total_ot_sum = 0.0

        for r in queryset:
            time_in_str = r.time_in.strftime('%I:%M %p') if r.time_in else '--:--'
            time_out_str = r.time_out.strftime('%I:%M %p') if r.time_out else '--:--'
            late_str = f"{r.late_minutes}m" if r.late_minutes > 0 else "-"
            hours_val = float(r.total_hours)
            ot_val = float(r.overtime_hours)

            total_hours_sum += hours_val
            total_late_sum += r.late_minutes
            total_ot_sum += ot_val

            if employee_profile:
                table_rows.append([
                    r.date.strftime('%m/%d/%Y'),
                    r.date.strftime('%a'),
                    time_in_str,
                    time_out_str,
                    r.get_status_display(),
                    late_str,
                    f"{hours_val:.2f}",
                    f"{ot_val:.2f}"
                ])
            else:
                table_rows.append([
                    r.employee.employee_id,
                    r.employee.full_name[:18],
                    r.date.strftime('%m/%d/%y'),
                    time_in_str,
                    time_out_str,
                    r.get_status_display()[:8],
                    late_str,
                    f"{hours_val:.2f}"
                ])

        # Summary / Totals row
        if employee_profile:
            table_rows.append([
                'TOTAL', '', '', '', '', f"{total_late_sum}m", f"{total_hours_sum:.2f}", f"{total_ot_sum:.2f}"
            ])
        else:
            table_rows.append([
                'TOTAL RECORDS', f"{len(queryset)} records", '', '', '', f"{total_late_sum}m", '', f"{total_hours_sum:.2f}"
            ])

        # Column widths configuration
        if employee_profile:
            col_widths = [1.0*inch, 0.6*inch, 1.1*inch, 1.1*inch, 1.3*inch, 0.7*inch, 0.8*inch, 0.7*inch]
        else:
            col_widths = [0.9*inch, 1.8*inch, 0.8*inch, 0.9*inch, 0.9*inch, 0.9*inch, 0.6*inch, 0.7*inch]

        att_table = Table(table_rows, colWidths=col_widths, repeatRows=1)
        att_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 8.5),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('TOPPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('FONTNAME', (0,1), (-1,-2), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-2), 8),
            ('ALIGN', (0,1), (-1,-1), 'CENTER'),
            ('PADDING', (0,1), (-1,-1), 4),
            ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.HexColor('#F8FAFC')]),
            # Totals row styling
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#E2E8F0')),
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,-1), (-1,-1), 8.5),
        ]))
        elements.append(att_table)

        # Certification Signature section (standard for DTRs)
        elements.append(Spacer(1, 30))
        sig_data = [
            [Paragraph("I certify on my honor that the above is a true and correct report of the hours of work performed.", meta_style), ""],
            [Spacer(1, 20), ""],
            [Paragraph("________________________________________<br/><b>Verified by Immediate Supervisor / HR</b>", meta_style),
             Paragraph("________________________________________<br/><b>Employee Signature</b>", meta_style)]
        ]
        sig_table = Table(sig_data, colWidths=[3.7*inch, 3.7*inch])
        sig_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ]))
        elements.append(sig_table)

        doc.build(elements)
        return buffer.getvalue()
