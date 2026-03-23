from flask import Blueprint, request, jsonify
from ..extensions import db, bcrypt, create_token, token_required
from ..models import User
from ..utils.helpers import log_audit

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    POST /api/auth/login
    Request: { "username": "admin", "password": "admin123" }
    Response: { "token": "...", "user": { ... } }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        log_audit('login_failed', details=f'Failed login attempt for {username}',
                  ip_address=request.remote_addr, status='failure')
        return jsonify({'error': 'Invalid username or password'}), 401

    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 403

    token = create_token(user.id, user.role)
    log_audit('login_success', user_id=user.id,
              details=f'{user.role} login: {username}',
              ip_address=request.remote_addr)

    return jsonify({
        'token': token,
        'user': user.to_dict(),
        'message': 'Login successful',
    }), 200


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user():
    """Get current user from token."""
    user = User.query.get(request.current_user['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': user.to_dict()}), 200


@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password():
    """Change password for current user."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    if not old_password or not new_password:
        return jsonify({'error': 'Old and new passwords are required'}), 400

    if len(new_password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    user = User.query.get(request.current_user['user_id'])
    if not bcrypt.check_password_hash(user.password_hash, old_password):
        return jsonify({'error': 'Current password is incorrect'}), 400

    user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.session.commit()

    log_audit('password_changed', user_id=user.id, details='Password changed')
    return jsonify({'message': 'Password changed successfully'}), 200
