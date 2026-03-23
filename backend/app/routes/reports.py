import datetime
import io
import csv
from flask import Blueprint, request, jsonify, make_response
from ..extensions import db, token_required
from ..models import Attendance, Student, SchoolClass
from ..utils.helpers import parse_date

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/student/<int:student_id>', methods=['GET'])
@token_required
def student_report(student_id):
    """
    GET /api/reports/student/<id>?month=2024-01
    Returns attendance history for a specific student.
    """
    student = Student.query.get_or_404(student_id)
    month_str = request.args.get('month', '')

    query = Attendance.query.filter_by(student_db_id=student.id)

    if month_str:
        try:
            year, month = map(int, month_str.split('-'))
            start_date = datetime.date(year, month, 1)
            if month == 12:
                end_date = datetime.date(year + 1, 1, 1)
            else:
                end_date = datetime.date(year, month + 1, 1)
            query = query.filter(Attendance.date >= start_date, Attendance.date < end_date)
        except (ValueError, IndexError):
            return jsonify({'error': 'Invalid month format, use YYYY-MM'}), 400

    records = query.order_by(Attendance.date.desc()).all()

    total_days = len(records)
    present_days = sum(1 for r in records if r.status == 'present')
    late_days = sum(1 for r in records if r.status == 'late')
    absent_days = sum(1 for r in records if r.status == 'absent')
    attendance_pct = round((present_days + late_days) / total_days * 100, 1) if total_days > 0 else 0

    return jsonify({
        'student': student.to_dict(),
        'summary': {
            'total_days': total_days,
            'present': present_days,
            'late': late_days,
            'absent': absent_days,
            'attendance_percentage': attendance_pct,
        },
        'records': [r.to_dict() for r in records],
    }), 200


@reports_bp.route('/class/<int:class_id>', methods=['GET'])
@token_required
def class_report(class_id):
    """
    GET /api/reports/class/<id>?date=2024-01-15&month=2024-01
    Returns class-level attendance summary.
    """
    school_class = SchoolClass.query.get_or_404(class_id)
    students = Student.query.filter_by(class_id=class_id, is_active=True).all()

    date_str = request.args.get('date', '')
    month_str = request.args.get('month', '')

    student_reports = []
    for student in students:
        query = Attendance.query.filter_by(student_db_id=student.id)

        if date_str:
            target_date = parse_date(date_str)
            if target_date:
                query = query.filter_by(date=target_date)
        elif month_str:
            try:
                year, month = map(int, month_str.split('-'))
                start = datetime.date(year, month, 1)
                end = datetime.date(year, month + 1, 1) if month < 12 else datetime.date(year + 1, 1, 1)
                query = query.filter(Attendance.date >= start, Attendance.date < end)
            except (ValueError, IndexError):
                pass

        records = query.all()
        total = len(records)
        present = sum(1 for r in records if r.status in ('present', 'late'))
        pct = round(present / total * 100, 1) if total > 0 else 0

        student_reports.append({
            'student': student.to_dict(),
            'total_days': total,
            'present_days': present,
            'attendance_percentage': pct,
        })

    avg_attendance = (
        round(sum(s['attendance_percentage'] for s in student_reports) / len(student_reports), 1)
        if student_reports else 0
    )

    return jsonify({
        'class': school_class.to_dict(),
        'student_count': len(students),
        'average_attendance': avg_attendance,
        'students': student_reports,
    }), 200


@reports_bp.route('/export', methods=['GET'])
@token_required
def export_report():
    """
    GET /api/reports/export?date=2024-01-15&class_id=1&format=csv
    Export attendance data as CSV.
    """
    date_str = request.args.get('date')
    class_id = request.args.get('class_id', type=int)
    export_format = request.args.get('format', 'csv')

    if not date_str:
        target_date = datetime.date.today()
    else:
        target_date = parse_date(date_str)
        if not target_date:
            return jsonify({'error': 'Invalid date format'}), 400

    query = Attendance.query.filter_by(date=target_date)
    if class_id:
        query = query.filter_by(class_id=class_id)

    records = query.all()

    if export_format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Student ID', 'Name', 'Class', 'Date', 'Time In', 'Status', 'Confidence', 'Marked By'])

        for r in records:
            student = Student.query.get(r.student_db_id)
            class_name = ''
            if student and student.school_class:
                class_name = f"{student.school_class.name}-{student.section}"
            writer.writerow([
                student.student_id if student else '',
                student.name if student else '',
                class_name,
                r.date.isoformat(),
                r.time_in.isoformat() if r.time_in else '',
                r.status,
                round(r.confidence, 2),
                r.marked_by,
            ])

        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=attendance_{target_date}.csv'
        return response

    return jsonify({'error': 'Unsupported format'}), 400


@reports_bp.route('/monthly-summary', methods=['GET'])
@token_required
def monthly_summary():
    """
    GET /api/reports/monthly-summary?month=2024-01&class_id=1
    """
    month_str = request.args.get('month', '')
    class_id = request.args.get('class_id', type=int)

    if not month_str:
        now = datetime.date.today()
        year, month = now.year, now.month
    else:
        try:
            year, month = map(int, month_str.split('-'))
        except (ValueError, IndexError):
            return jsonify({'error': 'Invalid month format'}), 400

    start = datetime.date(year, month, 1)
    end = datetime.date(year, month + 1, 1) if month < 12 else datetime.date(year + 1, 1, 1)

    query = Attendance.query.filter(Attendance.date >= start, Attendance.date < end)
    if class_id:
        query = query.filter_by(class_id=class_id)

    records = query.all()

    # Group by date
    daily = {}
    for r in records:
        date_key = r.date.isoformat()
        if date_key not in daily:
            daily[date_key] = {'present': 0, 'late': 0, 'absent': 0, 'total': 0}
        daily[date_key][r.status] = daily[date_key].get(r.status, 0) + 1
        daily[date_key]['total'] += 1

    return jsonify({
        'month': f'{year}-{month:02d}',
        'total_records': len(records),
        'daily_breakdown': daily,
    }), 200
