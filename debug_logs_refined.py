
import os
import sys

# Define base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Add backend to path
sys.path.append(os.path.join(BASE_DIR, 'backend'))

from app import create_app
from app.models import AuditLog, Student, FaceEmbedding

app = create_app('development')
with app.app_context():
    print("--- RECENT FAILURES ---")
    logs = AuditLog.query.filter(AuditLog.status == 'failure').order_by(AuditLog.created_at.desc()).limit(20).all()
    for log in logs:
        print(f"[{log.created_at}] {log.action}: {log.details}")
    
    print("\n--- ATTENDANCE ATTEMPTS ---")
    logs = AuditLog.query.filter(AuditLog.action.in_(['attendance_face', 'liveness_failed'])).order_by(AuditLog.created_at.desc()).limit(20).all()
    for log in logs:
        print(f"[{log.created_at}] {log.action}: {log.status} - {log.details}")
