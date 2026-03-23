from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import jwt as pyjwt
import datetime
from functools import wraps
from flask import request, jsonify, current_app

db = SQLAlchemy()
cors = CORS()
bcrypt = Bcrypt()


def create_token(user_id, role):
    """Create a JWT token for authentication."""
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(
            seconds=current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 86400)
        ),
        'iat': datetime.datetime.utcnow(),
    }
    return pyjwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')


def decode_token(token):
    """Decode and validate a JWT token."""
    try:
        payload = pyjwt.decode(
            token,
            current_app.config['JWT_SECRET_KEY'],
            algorithms=['HS256']
        )
        return payload
    except pyjwt.ExpiredSignatureError:
        return None
    except pyjwt.InvalidTokenError:
        return None


def token_required(f):
    """Decorator to require valid JWT token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        payload = decode_token(token)
        if payload is None:
            return jsonify({'error': 'Token is invalid or expired'}), 401
        request.current_user = payload
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if request.current_user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated


def teacher_or_admin_required(f):
    """Decorator to require teacher or admin role."""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        role = request.current_user.get('role')
        if role not in ('admin', 'teacher'):
            return jsonify({'error': 'Teacher or admin access required'}), 403
        return f(*args, **kwargs)
    return decorated
