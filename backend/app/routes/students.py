import base64
import numpy as np
from flask import Blueprint, request, jsonify, current_app
from ..extensions import db, token_required, teacher_or_admin_required
from ..models import Student, FaceEmbedding, SchoolClass
from ..utils.helpers import log_audit

students_bp = Blueprint('students', __name__)


@students_bp.route('/register', methods=['POST'])
@teacher_or_admin_required
def register_student():
    """
    POST /api/students/register
    Request: {
        "student_id": "STU-2024-0001",
        "name": "Aarav Sharma",
        "class_id": 1,
        "section": "A",
        "guardian_name": "Ramesh Sharma",
        "guardian_phone": "9876543210",
        "gender": "male",
        "face_images": ["base64_img1", "base64_img2", ...]
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    # Validate required fields
    required = ['student_id', 'name', 'class_id']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    # Check for duplicate student ID
    existing = Student.query.filter_by(student_id=data['student_id']).first()
    if existing:
        return jsonify({'error': 'Student ID already registered'}), 409

    # Validate class exists
    school_class = SchoolClass.query.get(data['class_id'])
    if not school_class:
        return jsonify({'error': 'Invalid class_id'}), 400

    # Create student record
    student = Student(
        student_id=data['student_id'],
        name=data['name'],
        class_id=data['class_id'],
        section=data.get('section', 'A'),
        guardian_name=data.get('guardian_name'),
        guardian_phone=data.get('guardian_phone'),
        gender=data.get('gender'),
        face_registered=False,
    )
    db.session.add(student)
    db.session.flush()  # Get student.id before processing faces

    # Process face images and generate embeddings
    face_images = data.get('face_images', [])
    embeddings_saved = 0

    if face_images:
        try:
            from ..services.face_recognition import FaceRecognitionService
            fr_service = FaceRecognitionService()

            for idx, img_b64 in enumerate(face_images[:current_app.config.get('MAX_FACE_SAMPLES', 10)]):
                try:
                    # Decode base64 image
                    img_bytes = base64.b64decode(img_b64)
                    nparr = np.frombuffer(img_bytes, np.uint8)

                    import cv2
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if img is None:
                        continue

                    # Detect face and generate embedding
                    embedding = fr_service.generate_embedding(img)
                    if embedding is not None:
                        emb_record = FaceEmbedding(
                            student_id=student.id,
                            embedding_data=embedding.tobytes(),
                            sample_index=idx,
                            quality_score=1.0,
                        )
                        db.session.add(emb_record)
                        embeddings_saved += 1
                except Exception as e:
                    current_app.logger.warning(f"Failed to process face sample {idx}: {e}")
                    continue

        except ImportError:
            current_app.logger.warning("Face recognition service not available")

    if embeddings_saved > 0:
        student.face_registered = True

    db.session.commit()

    log_audit(
        'student_registered',
        user_id=request.current_user['user_id'],
        details=f'Registered student {student.student_id} with {embeddings_saved} face samples',
    )

    return jsonify({
        'message': 'Student registered successfully',
        'student': student.to_dict(),
        'embeddings_saved': embeddings_saved,
    }), 201


@students_bp.route('', methods=['GET'])
@token_required
def list_students():
    """
    GET /api/students?class_id=1&search=aarav&page=1&per_page=20
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    class_id = request.args.get('class_id', type=int)
    search = request.args.get('search', '').strip()

    query = Student.query.filter_by(is_active=True)

    if class_id:
        query = query.filter_by(class_id=class_id)
    if search:
        query = query.filter(
            db.or_(
                Student.name.ilike(f'%{search}%'),
                Student.student_id.ilike(f'%{search}%')
            )
        )

    query = query.order_by(Student.name)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'students': [s.to_dict() for s in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
    }), 200


@students_bp.route('/<int:student_id>', methods=['GET'])
@token_required
def get_student(student_id):
    """GET /api/students/<id>"""
    student = Student.query.get_or_404(student_id)
    data = student.to_dict()
    data['embedding_count'] = FaceEmbedding.query.filter_by(student_id=student.id).count()
    data['class_name'] = student.school_class.name if student.school_class else None
    return jsonify({'student': data}), 200


@students_bp.route('/<int:student_id>', methods=['PUT'])
@teacher_or_admin_required
def update_student(student_id):
    """PUT /api/students/<id>"""
    student = Student.query.get_or_404(student_id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    updatable = ['name', 'section', 'guardian_name', 'guardian_phone', 'gender', 'class_id']
    for field in updatable:
        if field in data:
            setattr(student, field, data[field])

    db.session.commit()
    log_audit('student_updated', user_id=request.current_user['user_id'],
              details=f'Updated student {student.student_id}')

    return jsonify({'message': 'Student updated', 'student': student.to_dict()}), 200


@students_bp.route('/<int:student_id>/add-faces', methods=['POST'])
@teacher_or_admin_required
def add_face_samples(student_id):
    """Add additional face samples to an existing student."""
    student = Student.query.get_or_404(student_id)
    data = request.get_json()
    if not data or not data.get('face_images'):
        return jsonify({'error': 'face_images array required'}), 400

    existing_count = FaceEmbedding.query.filter_by(student_id=student.id).count()
    max_samples = current_app.config.get('MAX_FACE_SAMPLES', 10)

    if existing_count >= max_samples:
        return jsonify({'error': f'Maximum {max_samples} face samples reached'}), 400

    embeddings_saved = 0
    try:
        from ..services.face_recognition import FaceRecognitionService
        fr_service = FaceRecognitionService()

        for idx, img_b64 in enumerate(data['face_images']):
            if existing_count + embeddings_saved >= max_samples:
                break
            try:
                img_bytes = base64.b64decode(img_b64)
                nparr = np.frombuffer(img_bytes, np.uint8)

                import cv2
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is None:
                    continue

                embedding = fr_service.generate_embedding(img)
                if embedding is not None:
                    emb_record = FaceEmbedding(
                        student_id=student.id,
                        embedding_data=embedding.tobytes(),
                        sample_index=existing_count + embeddings_saved,
                        quality_score=1.0,
                    )
                    db.session.add(emb_record)
                    embeddings_saved += 1
            except Exception:
                continue

    except ImportError:
        return jsonify({'error': 'Face recognition service not available'}), 500

    if embeddings_saved > 0:
        student.face_registered = True
        db.session.commit()

    return jsonify({
        'message': f'{embeddings_saved} face samples added',
        'total_samples': existing_count + embeddings_saved,
    }), 200


@students_bp.route('/classes', methods=['GET'])
@token_required
def list_classes():
    """GET /api/students/classes - List all classes."""
    classes = SchoolClass.query.order_by(SchoolClass.name, SchoolClass.section).all()
    return jsonify({'classes': [c.to_dict() for c in classes]}), 200
