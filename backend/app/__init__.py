from flask import Flask
from .config import config_by_name
from .extensions import db, cors, bcrypt
from .models import User, Student, SchoolClass, Attendance, FaceEmbedding, AuditLog, SyncQueue


def create_app(config_name='development'):
    """Flask application factory."""
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Initialize extensions
    db.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    bcrypt.init_app(app)

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.students import students_bp
    from .routes.attendance import attendance_bp
    from .routes.reports import reports_bp
    from .routes.dashboard import dashboard_bp
    from .routes.sync import sync_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(students_bp, url_prefix='/api/students')
    app.register_blueprint(attendance_bp, url_prefix='/api/attendance')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(sync_bp, url_prefix='/api/sync')

    # Health check
    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy', 'message': 'Automated Attendance System is running'}

    # Create tables and seed default admin on first run
    with app.app_context():
        db.create_all()
        _seed_defaults()

    return app


def _seed_defaults():
    """Create default admin user and classes if they don't exist."""
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password_hash=bcrypt.generate_password_hash('admin123').decode('utf-8'),
            full_name='System Administrator',
            role='admin',
            email='admin@school.local',
        )
        db.session.add(admin)

    if not User.query.filter_by(username='teacher1').first():
        teacher = User(
            username='teacher1',
            password_hash=bcrypt.generate_password_hash('teacher123').decode('utf-8'),
            full_name='Rajesh Kumar',
            role='teacher',
            email='teacher1@school.local',
        )
        db.session.add(teacher)

    # Create default classes
    if not SchoolClass.query.first():
        for grade in range(1, 11):
            for section in ['A', 'B']:
                sc = SchoolClass(name=f'Class {grade}', section=section)
                db.session.add(sc)

    db.session.commit()
