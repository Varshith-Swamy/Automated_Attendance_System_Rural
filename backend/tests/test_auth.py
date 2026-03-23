"""Tests for authentication endpoints."""
import json
import pytest
from app import create_app
from app.extensions import db, bcrypt
from app.models import User


@pytest.fixture
def client():
    """Create test client."""
    app = create_app('testing')
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Create test user
            admin = User(
                username='testadmin',
                password_hash=bcrypt.generate_password_hash('test123').decode('utf-8'),
                full_name='Test Admin',
                role='admin',
            )
            db.session.add(admin)
            db.session.commit()
        yield client


def test_login_success(client):
    """Test successful login."""
    response = client.post('/api/auth/login', json={
        'username': 'testadmin',
        'password': 'test123',
    })
    data = json.loads(response.data)
    assert response.status_code == 200
    assert 'token' in data
    assert data['user']['username'] == 'testadmin'
    assert data['user']['role'] == 'admin'


def test_login_invalid_password(client):
    """Test login with wrong password."""
    response = client.post('/api/auth/login', json={
        'username': 'testadmin',
        'password': 'wrongpassword',
    })
    assert response.status_code == 401


def test_login_missing_fields(client):
    """Test login with missing fields."""
    response = client.post('/api/auth/login', json={
        'username': 'testadmin',
    })
    assert response.status_code == 400


def test_login_nonexistent_user(client):
    """Test login with non-existent user."""
    response = client.post('/api/auth/login', json={
        'username': 'nobody',
        'password': 'test123',
    })
    assert response.status_code == 401


def test_protected_endpoint_no_token(client):
    """Test accessing protected endpoint without token."""
    response = client.get('/api/students')
    assert response.status_code == 401


def test_protected_endpoint_with_token(client):
    """Test accessing protected endpoint with valid token."""
    # Login first
    login_res = client.post('/api/auth/login', json={
        'username': 'testadmin',
        'password': 'test123',
    })
    token = json.loads(login_res.data)['token']

    # Access protected endpoint
    response = client.get('/api/students', headers={
        'Authorization': f'Bearer {token}',
    })
    assert response.status_code == 200
