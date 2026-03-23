"""Tests for attendance endpoints."""
import json
import datetime
import pytest
from app import create_app
from app.extensions import db, bcrypt
from app.models import User, Student, SchoolClass, Attendance


@pytest.fixture
def client():
    """Create test client with seeded data."""
    app = create_app('testing')
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            admin = User(
                username='testadmin',
                password_hash=bcrypt.generate_password_hash('test123').decode('utf-8'),
                full_name='Test Admin',
                role='admin',
            )
            db.session.add(admin)

            sc = SchoolClass(name='Class 5', section='A')
            db.session.add(sc)
            db.session.flush()

            student = Student(
                student_id='STU-2024-0001',
                name='Test Student',
                class_id=sc.id,
                section='A',
                is_active=True,
                face_registered=True,
            )
            db.session.add(student)
            db.session.commit()
        yield client


@pytest.fixture
def auth_header(client):
    """Get auth header."""
    res = client.post('/api/auth/login', json={
        'username': 'testadmin',
        'password': 'test123',
    })
    token = json.loads(res.data)['token']
    return {'Authorization': f'Bearer {token}'}


def test_manual_attendance(client, auth_header):
    """Test manual attendance marking."""
    response = client.post('/api/attendance/mark', json={
        'student_db_id': 1,
        'status': 'present',
        'class_id': 1,
    }, headers=auth_header)

    data = json.loads(response.data)
    assert response.status_code == 201
    assert data['attendance']['status'] == 'present'


def test_duplicate_attendance(client, auth_header):
    """Test that attendance cannot be double-marked."""
    # Mark first time
    client.post('/api/attendance/mark', json={
        'student_db_id': 1,
        'status': 'present',
    }, headers=auth_header)

    # Try marking again
    response = client.post('/api/attendance/mark', json={
        'student_db_id': 1,
        'status': 'present',
    }, headers=auth_header)

    data = json.loads(response.data)
    assert response.status_code == 200
    assert 'already' in data['message'].lower()


def test_daily_attendance(client, auth_header):
    """Test daily attendance retrieval."""
    # Mark attendance
    client.post('/api/attendance/mark', json={
        'student_db_id': 1,
        'status': 'present',
    }, headers=auth_header)

    response = client.get('/api/attendance/daily', headers=auth_header)
    data = json.loads(response.data)
    assert response.status_code == 200
    assert 'attendance' in data
    assert data['present_count'] >= 1


def test_daily_attendance_with_date(client, auth_header):
    """Test daily attendance with specific date."""
    response = client.get(
        '/api/attendance/daily?date=2024-01-01',
        headers=auth_header,
    )
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data['date'] == '2024-01-01'


def test_attendance_missing_data(client, auth_header):
    """Test attendance with no image or student_db_id."""
    response = client.post('/api/attendance/mark', json={},
                           headers=auth_header)
    assert response.status_code == 400
