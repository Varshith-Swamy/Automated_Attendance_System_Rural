"""
Report Generator Service
Handles CSV/PDF-ready report data generation.
"""
import datetime
from ..models import Attendance, Student, SchoolClass
from ..extensions import db


class ReportGenerator:
    """Generate attendance reports and analytics."""

    @staticmethod
    def daily_report(date=None, class_id=None):
        """Generate a daily attendance report."""
        if date is None:
            date = datetime.date.today()

        query = Attendance.query.filter_by(date=date)
        if class_id:
            query = query.filter_by(class_id=class_id)

        records = query.all()

        student_query = Student.query.filter_by(is_active=True)
        if class_id:
            student_query = student_query.filter_by(class_id=class_id)
        total_students = student_query.count()

        present = sum(1 for r in records if r.status in ('present', 'late'))

        return {
            'date': date.isoformat(),
            'total_students': total_students,
            'present': present,
            'absent': total_students - present,
            'attendance_rate': round(present / total_students * 100, 1) if total_students > 0 else 0,
            'records': [r.to_dict() for r in records],
        }

    @staticmethod
    def monthly_report(year, month, class_id=None):
        """Generate a monthly attendance summary."""
        start = datetime.date(year, month, 1)
        end = datetime.date(year, month + 1, 1) if month < 12 else datetime.date(year + 1, 1, 1)

        query = Attendance.query.filter(
            Attendance.date >= start,
            Attendance.date < end
        )
        if class_id:
            query = query.filter_by(class_id=class_id)

        records = query.all()

        # Group by student
        student_stats = {}
        for r in records:
            sid = r.student_db_id
            if sid not in student_stats:
                student_stats[sid] = {'present': 0, 'late': 0, 'absent': 0, 'total': 0}
            student_stats[sid][r.status] = student_stats[sid].get(r.status, 0) + 1
            student_stats[sid]['total'] += 1

        return {
            'year': year,
            'month': month,
            'total_records': len(records),
            'student_stats': student_stats,
        }

    @staticmethod
    def student_trend(student_id, months=6):
        """Get attendance trend for a student over recent months."""
        today = datetime.date.today()
        trends = []

        for i in range(months - 1, -1, -1):
            month = today.month - i
            year = today.year
            while month <= 0:
                month += 12
                year -= 1

            start = datetime.date(year, month, 1)
            end = datetime.date(year, month + 1, 1) if month < 12 else datetime.date(year + 1, 1, 1)

            total = Attendance.query.filter(
                Attendance.student_db_id == student_id,
                Attendance.date >= start,
                Attendance.date < end
            ).count()

            present = Attendance.query.filter(
                Attendance.student_db_id == student_id,
                Attendance.date >= start,
                Attendance.date < end,
                Attendance.status.in_(['present', 'late'])
            ).count()

            trends.append({
                'month': f'{year}-{month:02d}',
                'total_days': total,
                'present_days': present,
                'percentage': round(present / total * 100, 1) if total > 0 else 0,
            })

        return trends
