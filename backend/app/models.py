import datetime
from .extensions import db


class User(db.Model):
    """Admin and teacher user accounts."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='teacher')  # 'admin' or 'teacher'
    email = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'role': self.role,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class SchoolClass(db.Model):
    """School classes/grades."""
    __tablename__ = 'classes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # e.g., "Class 5"
    section = db.Column(db.String(10), default='A')
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    teacher = db.relationship('User', backref='classes')
    students = db.relationship('Student', backref='school_class', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'section': self.section,
            'teacher_id': self.teacher_id,
            'student_count': len(self.students) if self.students else 0,
        }


class Student(db.Model):
    """Registered students."""
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    section = db.Column(db.String(10), default='A')
    guardian_name = db.Column(db.String(120))
    guardian_phone = db.Column(db.String(15))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    is_active = db.Column(db.Boolean, default=True)
    face_registered = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    embeddings = db.relationship('FaceEmbedding', backref='student', lazy=True, cascade='all, delete-orphan')
    attendance_records = db.relationship('Attendance', backref='student', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'name': self.name,
            'class_id': self.class_id,
            'section': self.section,
            'guardian_name': self.guardian_name,
            'guardian_phone': self.guardian_phone,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'gender': self.gender,
            'is_active': self.is_active,
            'face_registered': self.face_registered,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class FaceEmbedding(db.Model):
    """Stored facial embeddings for each student."""
    __tablename__ = 'face_embeddings'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    embedding_data = db.Column(db.LargeBinary, nullable=False)  # numpy array serialized
    sample_index = db.Column(db.Integer, default=0)
    quality_score = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'sample_index': self.sample_index,
            'quality_score': self.quality_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Attendance(db.Model):
    """Attendance records."""
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    student_db_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, default=datetime.date.today, index=True)
    time_in = db.Column(db.Time, nullable=False, default=lambda: datetime.datetime.now().time())
    status = db.Column(db.String(10), default='present')  # present, absent, late
    confidence = db.Column(db.Float, default=0.0)
    marked_by = db.Column(db.String(20), default='system')  # system, manual, admin
    verified = db.Column(db.Boolean, default=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('student_db_id', 'date', name='unique_student_date'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'student_db_id': self.student_db_id,
            'student_name': self.student.name if self.student else None,
            'student_id': self.student.student_id if self.student else None,
            'date': self.date.isoformat() if self.date else None,
            'time_in': self.time_in.isoformat() if self.time_in else None,
            'status': self.status,
            'confidence': self.confidence,
            'marked_by': self.marked_by,
            'verified': self.verified,
            'class_id': self.class_id,
        }


class AuditLog(db.Model):
    """Audit trail for all actions."""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(50), nullable=False)  # login, attendance_mark, edit, sync, etc.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    status = db.Column(db.String(20), default='success')  # success, failure
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'action': self.action,
            'user_id': self.user_id,
            'details': self.details,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class SyncQueue(db.Model):
    """Queue for offline-to-cloud sync."""
    __tablename__ = 'sync_queue'

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(50), nullable=False)  # attendance_mark, student_register, etc.
    payload = db.Column(db.Text, nullable=False)  # JSON serialized data
    synced = db.Column(db.Boolean, default=False, index=True)
    retry_count = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    synced_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'action': self.action,
            'synced': self.synced,
            'retry_count': self.retry_count,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'synced_at': self.synced_at.isoformat() if self.synced_at else None,
        }
