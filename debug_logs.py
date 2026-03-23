
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
    print("--- RECENT AUDIT LOGS ---")
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(20).all()
    if not logs:
        print("No logs found.")
    for log in logs:
        print(f"[{log.created_at}] {log.action}: {log.status} - {log.details}")
    
    print("\n--- STUDENT REGISTRATION STATUS ---")
    students = Student.query.all()
    if not students:
        print("No students found.")
    for s in students:
        emb_count = FaceEmbedding.query.filter_by(student_id=s.id).count()
        print(f"ID: {s.student_id}, Name: {s.name}, Registered: {s.face_registered}, Embeddings: {emb_count}")
