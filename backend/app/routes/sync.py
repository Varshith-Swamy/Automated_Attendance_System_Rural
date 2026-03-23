import datetime
import json
from flask import Blueprint, request, jsonify
from ..extensions import db, admin_required, token_required
from ..models import SyncQueue, AuditLog
from ..utils.helpers import log_audit

sync_bp = Blueprint('sync', __name__)


@sync_bp.route('/status', methods=['GET'])
@token_required
def sync_status():
    """
    GET /api/sync/status
    Returns sync queue status.
    """
    pending = SyncQueue.query.filter_by(synced=False).count()
    synced = SyncQueue.query.filter_by(synced=True).count()
    failed = SyncQueue.query.filter(
        SyncQueue.synced == False,
        SyncQueue.retry_count > 0
    ).count()

    recent = SyncQueue.query.order_by(SyncQueue.created_at.desc()).limit(20).all()

    return jsonify({
        'pending': pending,
        'synced': synced,
        'failed': failed,
        'total': pending + synced,
        'recent': [s.to_dict() for s in recent],
    }), 200


@sync_bp.route('/upload', methods=['POST'])
@admin_required
def sync_upload():
    """
    POST /api/sync/upload
    Triggers sync of pending items to cloud.
    In a real deployment, this would push to PostgreSQL/Firebase.
    For demo, we just mark items as synced.
    """
    pending_items = SyncQueue.query.filter_by(synced=False).all()
    synced_count = 0

    for item in pending_items:
        try:
            # In production: push item.payload to cloud database
            # For demo: simulate successful sync
            item.synced = True
            item.synced_at = datetime.datetime.utcnow()
            synced_count += 1
        except Exception as e:
            item.retry_count += 1
            item.error_message = str(e)

    db.session.commit()

    log_audit('sync_upload', user_id=request.current_user['user_id'],
              details=f'Synced {synced_count}/{len(pending_items)} items')

    return jsonify({
        'message': f'Synced {synced_count} items',
        'synced': synced_count,
        'failed': len(pending_items) - synced_count,
    }), 200


@sync_bp.route('/retry', methods=['POST'])
@admin_required
def retry_failed():
    """Retry failed sync items."""
    failed = SyncQueue.query.filter(
        SyncQueue.synced == False,
        SyncQueue.retry_count > 0
    ).all()

    retried = 0
    for item in failed:
        try:
            item.synced = True
            item.synced_at = datetime.datetime.utcnow()
            retried += 1
        except Exception as e:
            item.retry_count += 1
            item.error_message = str(e)

    db.session.commit()

    return jsonify({
        'message': f'Retried {retried} items',
        'retried': retried,
    }), 200


@sync_bp.route('/logs', methods=['GET'])
@admin_required
def get_audit_logs():
    """
    GET /api/sync/logs?page=1&per_page=50&action=login
    Returns paginated audit logs.
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    action_filter = request.args.get('action', '')

    query = AuditLog.query

    if action_filter:
        query = query.filter_by(action=action_filter)

    pagination = query.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'logs': [log.to_dict() for log in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
    }), 200
