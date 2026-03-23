import datetime
import csv
import io
from flask import current_app
from ..models import AuditLog
from ..extensions import db


def log_audit(action, user_id=None, details=None, ip_address=None, status='success'):
    """Create an audit log entry."""
    try:
        entry = AuditLog(
            action=action,
            user_id=user_id,
            details=details,
            ip_address=ip_address,
            status=status,
        )
        db.session.add(entry)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Audit log error: {e}")


def generate_student_id(class_name, count):
    """Generate a unique student ID like 'STU-2024-0001'."""
    year = datetime.datetime.now().year
    return f"STU-{year}-{count + 1:04d}"


def export_to_csv(data, headers):
    """Export data list to CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in data:
        writer.writerow(row)
    return output.getvalue()


def parse_date(date_str):
    """Parse date string in multiple formats."""
    formats = ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d']
    for fmt in formats:
        try:
            return datetime.datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None
