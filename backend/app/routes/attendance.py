import base64
import datetime
import json
import numpy as np
from flask import Blueprint, request, jsonify, current_app
from ..extensions import db, token_required, teacher_or_admin_required, admin_required
from ..models import Attendance, Student, FaceEmbedding, SyncQueue
from ..utils.helpers import log_audit, parse_date

attendance_bp = Blueprint('attendance', __name__)


@attendance_bp.route('/recognize', methods=['POST'])
@teacher_or_admin_required
def recognize_face():
    """
    POST /api/attendance/recognize
    Request: { "image": "base64_encoded_image" }
    Response: { "recognized": true, "student": {...}, "confidence": 0.85 }

    Detects and identifies faces without marking attendance.
    """
    data = request.get_json()
    if not data or not data.get('image'):
        return jsonify({'error': 'Image data is required'}), 400

    try:
        from ..services.face_recognition import FaceRecognitionService
        fr_service = FaceRecognitionService()

        # Decode image
        img_bytes = base64.b64decode(data['image'])
        nparr = np.frombuffer(img_bytes, np.uint8)

        import cv2
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return jsonify({'error': 'Invalid image data'}), 400

        # Load all embeddings from database
        all_embeddings = _load_all_embeddings()

        # Recognize
        results = fr_service.recognize_faces(img, all_embeddings)

        if not results:
            return jsonify({
                'recognized': False,
                'message': 'No face detected in image',
                'faces': [],
            }), 200

        response_faces = []
        for result in results:
            face_data = {
                'recognized': result['matched'],
                'confidence': round(result['confidence'], 4),
                'bbox': result.get('bbox', []),
            }
            if result['matched']:
                student = Student.query.get(result['student_db_id'])
                if student:
                    face_data['student'] = student.to_dict()
            response_faces.append(face_data)

        return jsonify({
            'recognized': any(f['recognized'] for f in response_faces),
            'faces': response_faces,
        }), 200

    except ImportError:
        return jsonify({'error': 'Face recognition service not available'}), 500
    except Exception as e:
        current_app.logger.error(f"Recognition error: {e}")
        return jsonify({'error': 'Face recognition failed'}), 500


@attendance_bp.route('/mark', methods=['POST'])
@teacher_or_admin_required
def mark_attendance():
    """
    POST /api/attendance/mark
    Request: { "image": "base64_encoded_image", "class_id": 1 }
    OR: { "student_db_id": 5, "status": "present", "class_id": 1 } (manual)
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    today = datetime.date.today()
    now = datetime.datetime.now().time()
    results = []

    # Manual marking
    if data.get('student_db_id'):
        student = Student.query.get(data['student_db_id'])
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        existing = Attendance.query.filter_by(
            student_db_id=student.id, date=today
        ).first()

        if existing:
            return jsonify({
                'message': 'Attendance already marked for today',
                'attendance': existing.to_dict(),
            }), 200

        record = Attendance(
            student_db_id=student.id,
            date=today,
            time_in=now,
            status=data.get('status', 'present'),
            confidence=1.0,
            marked_by='manual',
            class_id=data.get('class_id', student.class_id),
        )
        db.session.add(record)
        db.session.commit()

        _queue_sync('attendance_mark', record.to_dict())
        log_audit('attendance_manual', user_id=request.current_user['user_id'],
                  details=f'Manual attendance for {student.student_id}')

        return jsonify({
            'message': 'Attendance marked manually',
            'attendance': record.to_dict(),
        }), 201

    # Face-based marking
    if data.get('image'):
        try:
            from ..services.face_recognition import FaceRecognitionService
            from ..services.liveness import LivenessDetector

            fr_service = FaceRecognitionService()
            liveness = LivenessDetector()

            img_bytes = base64.b64decode(data['image'])
            nparr = np.frombuffer(img_bytes, np.uint8)

            import cv2
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return jsonify({'error': 'Invalid image data'}), 400

            # Liveness check
            is_live, liveness_msg = liveness.check_single_frame(img)
            if not is_live:
                log_audit('liveness_failed', user_id=request.current_user['user_id'],
                          details=liveness_msg, status='failure')
                return jsonify({
                    'error': 'Liveness check failed',
                    'detail': liveness_msg,
                }), 400

            # Load embeddings and recognize
            all_embeddings = _load_all_embeddings()
            recognized = fr_service.recognize_faces(img, all_embeddings)

            if not recognized:
                return jsonify({
                    'message': 'No face detected',
                    'results': [],
                }), 200

            for face in recognized:
                if not face['matched']:
                    results.append({
                        'recognized': False,
                        'message': 'Unknown face',
                    })
                    continue

                student = Student.query.get(face['student_db_id'])
                if not student:
                    continue

                # Check if already marked today
                existing = Attendance.query.filter_by(
                    student_db_id=student.id, date=today
                ).first()

                if existing:
                    results.append({
                        'recognized': True,
                        'student': student.to_dict(),
                        'message': 'Already marked today',
                        'attendance': existing.to_dict(),
                    })
                    continue

                threshold = current_app.config.get('FACE_RECOGNITION_THRESHOLD', 0.6)
                if face['confidence'] < threshold:
                    results.append({
                        'recognized': False,
                        'message': 'Low confidence match',
                        'confidence': face['confidence'],
                    })
                    continue

                record = Attendance(
                    student_db_id=student.id,
                    date=today,
                    time_in=now,
                    status='present',
                    confidence=face['confidence'],
                    marked_by='system',
                    class_id=data.get('class_id', student.class_id),
                )
                db.session.add(record)
                results.append({
                    'recognized': True,
                    'student': student.to_dict(),
                    'message': 'Attendance marked',
                    'confidence': face['confidence'],
                })

            db.session.commit()

            for r in results:
                if r.get('recognized') and r.get('message') == 'Attendance marked':
                    _queue_sync('attendance_mark', r)
                    log_audit('attendance_face', user_id=request.current_user['user_id'],
                              details=f'Face attendance: {r["student"]["student_id"]}')

            return jsonify({
                'message': f'Processed {len(results)} face(s)',
                'results': results,
            }), 201

        except ImportError:
            return jsonify({'error': 'Face recognition service not available'}), 500
        except Exception as e:
            current_app.logger.error(f"Attendance marking error: {e}")
            return jsonify({'error': 'Failed to process attendance'}), 500

    return jsonify({'error': 'Provide image or student_db_id'}), 400


@attendance_bp.route('/daily', methods=['GET'])
@token_required
def get_daily_attendance():
    """
    GET /api/attendance/daily?date=2024-01-15&class_id=1
    """
    date_str = request.args.get('date')
    class_id = request.args.get('class_id', type=int)

    if date_str:
        target_date = parse_date(date_str)
        if not target_date:
            return jsonify({'error': 'Invalid date format'}), 400
    else:
        target_date = datetime.date.today()

    query = Attendance.query.filter_by(date=target_date)
    if class_id:
        query = query.filter_by(class_id=class_id)

    records = query.order_by(Attendance.time_in).all()

    # Also get students who are absent (not in attendance)
    present_ids = {r.student_db_id for r in records}
    student_query = Student.query.filter_by(is_active=True)
    if class_id:
        student_query = student_query.filter_by(class_id=class_id)
    all_students = student_query.all()

    absent_students = [s.to_dict() for s in all_students if s.id not in present_ids]

    return jsonify({
        'date': target_date.isoformat(),
        'attendance': [r.to_dict() for r in records],
        'present_count': len(records),
        'absent_count': len(absent_students),
        'total_students': len(all_students),
        'absent_students': absent_students,
    }), 200


@attendance_bp.route('/<int:attendance_id>', methods=['PUT'])
@admin_required
def update_attendance(attendance_id):
    """
    PUT /api/attendance/<id>
    Admin manual correction.
    Request: { "status": "late", "time_in": "09:15:00" }
    """
    record = Attendance.query.get_or_404(attendance_id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    if 'status' in data:
        record.status = data['status']
    if 'time_in' in data:
        try:
            record.time_in = datetime.datetime.strptime(data['time_in'], '%H:%M:%S').time()
        except ValueError:
            return jsonify({'error': 'Invalid time format, use HH:MM:SS'}), 400

    record.marked_by = 'admin'
    db.session.commit()

    log_audit('attendance_edited', user_id=request.current_user['user_id'],
              details=f'Edited attendance #{attendance_id}')

    return jsonify({
        'message': 'Attendance updated',
        'attendance': record.to_dict(),
    }), 200


def _load_all_embeddings():
    """Load all face embeddings from database into memory for matching."""
    embeddings_list = []
    records = db.session.query(
        FaceEmbedding.student_id, FaceEmbedding.embedding_data
    ).all()

    for student_id, emb_data in records:
        try:
            emb_array = np.frombuffer(emb_data, dtype=np.float64)
            embeddings_list.append({
                'student_db_id': student_id,
                'embedding': emb_array,
            })
        except Exception:
            continue

    return embeddings_list


def _queue_sync(action, data):
    """Add an action to the sync queue for offline-first support."""
    try:
        entry = SyncQueue(
            action=action,
            payload=json.dumps(data, default=str),
        )
        db.session.add(entry)
        db.session.commit()
    except Exception:
        pass
