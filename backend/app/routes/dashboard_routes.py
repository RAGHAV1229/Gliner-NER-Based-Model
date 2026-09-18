from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.batch_models import ActivityLog, BatchJob, ExtractedEntity
from app.database import get_db
from app.models import User
from app.utils.auth_utils import get_current_user

router = APIRouter(prefix="/api", tags=["Dashboard"])


@router.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    batch_query = db.query(BatchJob)
    if current_user.role != "admin":
        batch_query = batch_query.filter(BatchJob.user_id == current_user.id)

    total_batches = batch_query.count()
    processing = batch_query.filter(BatchJob.status.in_(["queued", "processing", "uploading"])).count()
    completed = batch_query.filter(BatchJob.status.in_(["completed", "completed_with_errors"])).count()
    entity_query = db.query(func.coalesce(func.sum(BatchJob.entity_count), 0))
    if current_user.role != "admin":
        entity_query = entity_query.filter(BatchJob.user_id == current_user.id)
    entities = entity_query.scalar()

    recent = batch_query.order_by(BatchJob.created_at.desc()).limit(8).all()
    recent_payload = []
    for batch in recent:
        total = max(batch.total_files, 1)
        percent = round((batch.processed_files / total) * 100, 2) if batch.total_files else 0
        owner = db.query(User).filter(User.id == batch.user_id).first()
        recent_payload.append(
            {
                "id": batch.id,
                "job_name": batch.job_name,
                "status": batch.status,
                "percent_complete": percent,
                "entity_count": batch.entity_count,
                "owner_email": owner.email if owner else None,
                "created_at": batch.created_at,
            }
        )

    return {
        "total_batches": total_batches,
        "processing": processing,
        "completed": completed,
        "entity_count": int(entities or 0),
        "role": current_user.role,
        "recent_batches": recent_payload,
    }


@router.get("/history")
def history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ActivityLog)
    if current_user.role != "admin":
        query = query.filter(ActivityLog.user_id == current_user.id)
    logs = query.order_by(ActivityLog.created_at.desc()).limit(200).all()

    user_map = {}
    if current_user.role == "admin":
        ids = {log.user_id for log in logs if log.user_id}
        for user in db.query(User).filter(User.id.in_(ids)).all():
            user_map[user.id] = user.email

    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "user_email": user_map.get(log.user_id) if current_user.role == "admin" else current_user.email,
            "action": log.action,
            "detail": log.detail,
            "batch_id": log.batch_id,
            "created_at": log.created_at,
        }
        for log in logs
    ]
