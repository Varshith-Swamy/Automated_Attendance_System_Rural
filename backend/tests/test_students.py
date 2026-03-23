"""Tests for student management endpoints."""
import json
import pytest
from app import create_app
from app.extensions import db, bcrypt
from app.models import User, SchoolClass


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
            db.session.commit()
        yield client


@pytest.fixture
def auth_header(client):
    """Get auth header for requests."""
    res = client.post('/api/auth/login', json={
        'username': 'testadmin',
        'password': 'test123',
    })
    token = json.loads(res.data)['token']
    return {'Authorization': f'Bearer {token}'}


def test_register_student(client, auth_header):
    """Test student registration."""
    response = client.post('/api/students/register', json={
        'student_id': 'STU-2024-0001',
        'name': 'Aarav Sharma',
        'class_id': 1,
        'section': 'A',
        'guardian_name': 'Ramesh Sharma',
        'guardian_phone': '9876543210',
        'gender': 'male',
    }, headers=auth_header)

    data = json.loads(response.data)
    assert response.status_code == 201
    assert data['student']['student_id'] == 'STU-2024-0001'
    assert data['student']['name'] == 'Aarav Sharma'


def test_duplicate_student_id(client, auth_header):
    """Test duplicate student ID rejection."""
    # Register first
    client.post('/api/students/register', json={
        'student_id': 'STU-2024-0002',
        'name': 'Test Student',
        'class_id': 1,
    }, headers=auth_header)

    # Try duplicate
    response = client.post('/api/students/register', json={
        'student_id': 'STU-2024-0002',
        'name': 'Another Student',
        'class_id': 1,
    }, headers=auth_header)
    assert response.status_code == 409


def test_list_students(client, auth_header):
    """Test listing students."""
    # Register a student first
    client.post('/api/students/register', json={
        'student_id': 'STU-2024-0003',
        'name': 'Test Student',
        'class_id': 1,
    }, headers=auth_header)

    response = client.get('/api/students', headers=auth_header)
    data = json.loads(response.data)
    assert response.status_code == 200
    assert 'students' in data
    assert len(data['students']) >= 1


def test_register_missing_fields(client, auth_header):
    """Test registration with missing required fields."""
    response = client.post('/api/students/register', json={
        'name': 'No ID Student',
    }, headers=auth_header)
    assert response.status_code == 400


def test_list_classes(client, auth_header):
    """Test listing classes."""
    response = client.get('/api/students/classes', headers=auth_header)
    data = json.loads(response.data)
    assert response.status_code == 200
    assert 'classes' in data
