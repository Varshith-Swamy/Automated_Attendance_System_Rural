import datetime
from flask import Blueprint, jsonify
from ..extensions import db, token_required
from ..models import Attendance, Student, SchoolClass, User, AuditLog

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/summary', methods=['GET'])
@token_required
def get_summary():
    """
    GET /api/dashboard/summary
    Returns dashboard metrics for admin/teacher overview.
    """
    today = datetime.date.today()

    # Total counts
    total_students = Student.query.filter_by(is_active=True).count()
    total_classes = SchoolClass.query.count()
    total_teachers = User.query.filter_by(role='teacher', is_active=True).count()
    registered_faces = Student.query.filter_by(face_registered=True, is_active=True).count()

    # Today's attendance
    today_records = Attendance.query.filter_by(date=today).all()
    today_present = sum(1 for r in today_records if r.status in ('present', 'late'))
    today_late = sum(1 for r in today_records if r.status == 'late')

    today_pct = round(today_present / total_students * 100, 1) if total_students > 0 else 0

    # Week attendance trend (last 7 days)
    week_trend = []
    for i in range(6, -1, -1):
        day = today - datetime.timedelta(days=i)
        day_count = Attendance.query.filter(
            Attendance.date == day,
            Attendance.status.in_(['present', 'late'])
        ).count()
        week_trend.append({
            'date': day.isoformat(),
            'day': day.strftime('%a'),
            'present': day_count,
            'percentage': round(day_count / total_students * 100, 1) if total_students > 0 else 0,
        })

    # Class-wise today's summary
    class_summary = []
    classes = SchoolClass.query.all()
    for sc in classes:
        class_students = Student.query.filter_by(class_id=sc.id, is_active=True).count()
        if class_students == 0:
            continue
        class_present = Attendance.query.filter_by(
            class_id=sc.id, date=today
        ).filter(Attendance.status.in_(['present', 'late'])).count()

        class_summary.append({
            'class_id': sc.id,
            'class_name': f'{sc.name} {sc.section}',
            'total': class_students,
            'present': class_present,
            'percentage': round(class_present / class_students * 100, 1) if class_students > 0 else 0,
        })

    # Recent activity (last 10 audit logs)
    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()

    return jsonify({
        'overview': {
            'total_students': total_students,
            'total_classes': total_classes,
            'total_teachers': total_teachers,
            'registered_faces': registered_faces,
        },
        'today': {
            'date': today.isoformat(),
            'present': today_present,
            'late': today_late,
            'absent': total_students - today_present,
            'total': total_students,
            'attendance_percentage': today_pct,
        },
        'week_trend': week_trend,
        'class_summary': class_summary,
        'recent_activity': [log.to_dict() for log in recent_logs],
    }), 200
