#!/usr/bin/env python3
"""
Seed data generator for testing.
Creates 50+ sample students with synthetic face embeddings, attendance records, and classes.
"""
import os
import sys
import random
import datetime
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db, bcrypt
from app.models import User, Student, SchoolClass, Attendance, FaceEmbedding, AuditLog

# Sample Indian names for realistic test data
FIRST_NAMES = [
    'Aarav', 'Vivaan', 'Aditya', 'Vihaan', 'Arjun', 'Sai', 'Reyansh', 'Ayaan',
    'Krishna', 'Ishaan', 'Shaurya', 'Atharv', 'Advait', 'Dhruv', 'Kabir',
    'Ananya', 'Aanya', 'Aadhya', 'Aaradhya', 'Saanvi', 'Myra', 'Diya',
    'Prisha', 'Anvi', 'Anika', 'Kavya', 'Ira', 'Riya', 'Kiara', 'Navya',
    'Rahul', 'Priya', 'Amit', 'Neha', 'Vikram', 'Pooja', 'Rohit', 'Suman',
    'Deepak', 'Anjali', 'Suresh', 'Meena', 'Rajesh', 'Sunita', 'Manoj',
    'Geeta', 'Karan', 'Nisha', 'Pawan', 'Rekha', 'Sandeep', 'Seema',
    'Mohan', 'Radha', 'Gopal', 'Lakshmi',
]

LAST_NAMES = [
    'Sharma', 'Verma', 'Singh', 'Kumar', 'Patel', 'Gupta', 'Reddy',
    'Joshi', 'Mishra', 'Yadav', 'Chauhan', 'Pandey', 'Thakur', 'Dubey',
    'Nair', 'Iyer', 'Pillai', 'Das', 'Bose', 'Sen', 'Rao', 'Naidu',
    'Patil', 'Deshmukh', 'Kulkarni', 'Jain', 'Agarwal', 'Malhotra',
]

GUARDIAN_RELATIONS = ['Father', 'Mother', 'Uncle', 'Aunt', 'Grandfather']


def generate_phone():
    """Generate a random Indian phone number."""
    return f"9{random.randint(100000000, 999999999)}"


def generate_embedding(size=128):
    """Generate a random normalized 128-d embedding vector."""
    vec = np.random.randn(size).astype(np.float64)
    vec = vec / np.linalg.norm(vec)
    return vec


def seed_database():
    """Seed the database with test data."""
    app = create_app('development')

    with app.app_context():
        print("Seeding database...")

        # Check if already seeded
        if Student.query.count() > 10:
            print(f"Database already has {Student.query.count()} students. Skipping seed.")
            return

        # Ensure default users exist (from app factory)
        admin = User.query.filter_by(username='admin').first()
        teacher1 = User.query.filter_by(username='teacher1').first()

        # Create additional teachers
        teacher_names = [
            ('teacher2', 'Priya Mishra'),
            ('teacher3', 'Suresh Nair'),
            ('teacher4', 'Anita Deshmukh'),
            ('teacher5', 'Vikram Joshi'),
        ]
        for uname, fname in teacher_names:
            if not User.query.filter_by(username=uname).first():
                t = User(
                    username=uname,
                    password_hash=bcrypt.generate_password_hash('teacher123').decode('utf-8'),
                    full_name=fname,
                    role='teacher',
                    email=f'{uname}@school.local',
                )
                db.session.add(t)

        db.session.commit()
        print(f"  Users: {User.query.count()}")

        # Get classes
        classes = SchoolClass.query.all()
        if not classes:
            print("  No classes found! Creating defaults...")
            for grade in range(1, 11):
                for section in ['A', 'B']:
                    sc = SchoolClass(name=f'Class {grade}', section=section)
                    db.session.add(sc)
            db.session.commit()
            classes = SchoolClass.query.all()

        print(f"  Classes: {len(classes)}")

        # Create 55 students (distributed across classes)
        used_names = set()
        student_count = 0

        for i in range(55):
            # Pick unique name
            while True:
                first = random.choice(FIRST_NAMES)
                last = random.choice(LAST_NAMES)
                name = f"{first} {last}"
                if name not in used_names:
                    used_names.add(name)
                    break

            school_class = random.choice(classes)
            gender = random.choice(['male', 'female'])
            year = datetime.datetime.now().year

            student = Student(
                student_id=f"STU-{year}-{i + 1:04d}",
                name=name,
                class_id=school_class.id,
                section=school_class.section,
                guardian_name=f"{random.choice(GUARDIAN_RELATIONS)}: {random.choice(FIRST_NAMES)} {last}",
                guardian_phone=generate_phone(),
                gender=gender,
                date_of_birth=datetime.date(
                    year - random.randint(6, 16),
                    random.randint(1, 12),
                    random.randint(1, 27),  # max 27 to avoid month-end edge cases
                ),
                is_active=True,
                face_registered=True,
            )
            db.session.add(student)
            db.session.flush()

            # Generate 3-5 face embeddings per student
            num_samples = random.randint(3, 5)
            for sample_idx in range(num_samples):
                emb = generate_embedding()
                emb_record = FaceEmbedding(
                    student_id=student.id,
                    embedding_data=emb.tobytes(),
                    sample_index=sample_idx,
                    quality_score=round(random.uniform(0.75, 1.0), 3),
                )
                db.session.add(emb_record)

            student_count += 1

        db.session.commit()
        print(f"  Students created: {student_count}")
        print(f"  Face embeddings: {FaceEmbedding.query.count()}")

        # Generate attendance records for the last 30 days
        students = Student.query.all()
        attendance_count = 0
        today = datetime.date.today()

        for day_offset in range(30):
            date = today - datetime.timedelta(days=day_offset)

            # Skip weekends
            if date.weekday() >= 5:
                continue

            for student in students:
                # 85% attendance rate
                if random.random() < 0.85:
                    status = 'present'
                    if random.random() < 0.1:
                        status = 'late'

                    hour = random.randint(8, 9)
                    minute = random.randint(0, 59)
                    time_in = datetime.time(hour, minute)

                    record = Attendance(
                        student_db_id=student.id,
                        date=date,
                        time_in=time_in,
                        status=status,
                        confidence=round(random.uniform(0.75, 0.99), 4),
                        marked_by=random.choice(['system', 'system', 'system', 'manual']),
                        class_id=student.class_id,
                    )
                    db.session.add(record)
                    attendance_count += 1

        db.session.commit()
        print(f"  Attendance records: {attendance_count}")

        # Add some audit logs
        actions = ['login_success', 'attendance_face', 'student_registered', 'sync_upload']
        for _ in range(50):
            log = AuditLog(
                action=random.choice(actions),
                user_id=random.choice([admin.id if admin else 1, teacher1.id if teacher1 else 2]),
                details=f"Sample audit log entry",
                status='success',
                created_at=datetime.datetime.now() - datetime.timedelta(
                    hours=random.randint(0, 720)
                ),
            )
            db.session.add(log)

        db.session.commit()
        print(f"  Audit logs: {AuditLog.query.count()}")

        print("\n✓ Seed data generation complete!")
        print(f"  Total students: {Student.query.count()}")
        print(f"  Users: admin/admin123, teacher1-5/teacher123")


if __name__ == '__main__':
    seed_database()
