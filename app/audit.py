from flask import Blueprint, render_template, request, abort
from flask_login import login_required, current_user
from .models import db, AuditLog

audit_bp = Blueprint("audit", __name__)


def record_event(action, status="success", target_type=None, target_id=None, details=None,
                 actor_id=None):
    """Save an audit event. Never pass passwords, tokens, or other secrets in details."""
    if actor_id is None and current_user.is_authenticated:
        actor_id = current_user.id

    entry = AuditLog(
        actor_user_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        status=status,
        details=details,
    )
    db.session.add(entry)
    db.session.commit()


@audit_bp.route("/audit-logs")
@login_required
def audit_logs():
    if not current_user.has_role("Administrator"):
        abort(403)

    query = AuditLog.query
    user_id = request.args.get("user_id", "").strip()
    action = request.args.get("action", "").strip()
    status = request.args.get("status", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    if user_id.isdigit():
        query = query.filter_by(actor_user_id=int(user_id))
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    if status:
        query = query.filter_by(status=status)
    if date_from:
        query = query.filter(db.func.date(AuditLog.timestamp) >= date_from)
    if date_to:
        query = query.filter(db.func.date(AuditLog.timestamp) <= date_to)

    logs = query.order_by(AuditLog.timestamp.desc()).limit(250).all()
    return render_template("audit_logs.html", logs=logs)
