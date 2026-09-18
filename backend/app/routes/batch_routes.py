from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.batch_models import ActivityLog, BatchFile, BatchJob, ExtractedEntity
from app.database import get_db
from app.models import User
from app.services.archive_service import extract_archive
from app.services.batch_processor import process_batch_job
from app.services.batch_storage_service import (
    create_batch_directory,
    delete_batch_directory,
    save_uploaded_file,
)
from app.utils.auth_utils import get_current_user

router = APIRouter(prefix="/api/batches", tags=["Batch Processing"])


def _resolve_relative_paths(
    relative_paths: Optional[list[str]],
    relative_paths_json: Optional[str],
) -> Optional[list[str]]:
    if not relative_paths_json:
        return relative_paths
    try:
        parsed = json.loads(relative_paths_json)
    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=400,
            detail="relative_paths_json must be a JSON array of strings",
        ) from error
    if not isinstance(parsed, list):
        raise HTTPException(
            status_code=400,
            detail="relative_paths_json must be a JSON array of strings",
        )
    return [str(item) for item in parsed]


def _batch_query(db: Session, current_user: User):
    query = db.query(BatchJob)
    if current_user.role != "admin":
        query = query.filter(BatchJob.user_id == current_user.id)
    return query


def _serialize_batch(batch: BatchJob, owner_email: str | None = None) -> dict:
    total = max(batch.total_files, 1)
    percent = round((batch.processed_files / total) * 100, 2) if batch.total_files else 0
    remaining = max(batch.total_files - batch.processed_files, 0)
    return {
        "id": batch.id,
        "job_name": batch.job_name,
        "upload_type": batch.upload_type,
        "status": batch.status,
        "user_id": batch.user_id,
        "owner_email": owner_email,
        "total_files": batch.total_files,
        "processed_files": batch.processed_files,
        "failed_files": batch.failed_files,
        "remaining_files": remaining,
        "entity_count": batch.entity_count,
        "percent_complete": percent,
        "error_message": batch.error_message,
        "created_at": batch.created_at,
        "started_at": batch.started_at,
        "completed_at": batch.completed_at,
    }


async def _create_upload_batch(
    *,
    files: list[UploadFile],
    relative_paths: Optional[list[str]],
    job_name: str,
    upload_type: str,
    background_tasks: BackgroundTasks,
    db: Session,
    current_user: User,
    relative_paths_json: Optional[str] = None,
):
    if not files:
        raise HTTPException(status_code=400, detail="No files selected")

    relative_paths = _resolve_relative_paths(relative_paths, relative_paths_json)

    batch = BatchJob(
        job_name=job_name or f"{upload_type.title()} Batch",
        upload_type=upload_type,
        status="uploading",
        user_id=current_user.id,
        total_files=0,
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    batch_dir = create_batch_directory(batch.id)
    batch.storage_path = str(batch_dir)
    db.commit()

    saved = 0
    try:
        for index, upload in enumerate(files):
            rel = None
            if relative_paths and index < len(relative_paths):
                rel = relative_paths[index]
            stored = await save_uploaded_file(upload, batch_dir, rel)
            rel_path = rel or upload.filename or stored.name
            db.add(
                BatchFile(
                    batch_id=batch.id,
                    relative_path=rel_path.replace("\\", "/"),
                    stored_path=str(stored),
                    status="pending",
                )
            )
            saved += 1
        batch.total_files = saved
        batch.status = "queued"
        db.add(
            ActivityLog(
                user_id=current_user.id,
                action="batch_uploaded",
                detail=f"Uploaded {saved} files as {upload_type}",
                batch_id=batch.id,
            )
        )
        db.commit()
    except Exception:
        delete_batch_directory(batch.storage_path)
        batch.status = "failed"
        batch.error_message = "Upload failed"
        db.commit()
        raise

    background_tasks.add_task(process_batch_job, batch.id)
    return _serialize_batch(batch, current_user.email)


@router.post("/upload-files")
async def upload_files(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    relative_paths: Optional[list[str]] = Form(default=None),
    relative_paths_json: Optional[str] = Form(default=None),
    job_name: str = Form(default="File Batch"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _create_upload_batch(
        files=files,
        relative_paths=relative_paths,
        relative_paths_json=relative_paths_json,
        job_name=job_name,
        upload_type="files",
        background_tasks=background_tasks,
        db=db,
        current_user=current_user,
    )


@router.post("/upload-folder")
async def upload_folder(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    relative_paths: Optional[list[str]] = Form(default=None),
    relative_paths_json: Optional[str] = Form(default=None),
    job_name: str = Form(default="Folder Batch"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _create_upload_batch(
        files=files,
        relative_paths=relative_paths,
        relative_paths_json=relative_paths_json,
        job_name=job_name,
        upload_type="folder",
        background_tasks=background_tasks,
        db=db,
        current_user=current_user,
    )


@router.post("/upload-archive")
async def upload_archive(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    job_name: str = Form(default="Archive Batch"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    batch = BatchJob(
        job_name=job_name or "Archive Batch",
        upload_type="archive",
        status="uploading",
        user_id=current_user.id,
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    batch_dir = create_batch_directory(batch.id)
    batch.storage_path = str(batch_dir)
    db.commit()

    try:
        archive_path = await save_uploaded_file(file, batch_dir, file.filename)
        extract_dir = batch_dir / "extracted"
        extracted_files = extract_archive(archive_path, extract_dir)
        if not extracted_files:
            raise HTTPException(status_code=400, detail="Archive contained no usable files")

        for path in extracted_files:
            rel = str(path.relative_to(extract_dir)).replace("\\", "/")
            db.add(
                BatchFile(
                    batch_id=batch.id,
                    relative_path=rel,
                    stored_path=str(path),
                    status="pending",
                )
            )
        batch.total_files = len(extracted_files)
        batch.status = "queued"
        db.add(
            ActivityLog(
                user_id=current_user.id,
                action="batch_uploaded",
                detail=f"Uploaded archive with {batch.total_files} files",
                batch_id=batch.id,
            )
        )
        db.commit()
    except Exception:
        delete_batch_directory(batch.storage_path)
        batch.status = "failed"
        batch.error_message = "Archive upload failed"
        db.commit()
        raise

    background_tasks.add_task(process_batch_job, batch.id)
    return _serialize_batch(batch, current_user.email)


@router.get("")
def list_batches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    batches = _batch_query(db, current_user).order_by(BatchJob.created_at.desc()).all()
    emails = {}
    if current_user.role == "admin":
        user_ids = {b.user_id for b in batches}
        for user in db.query(User).filter(User.id.in_(user_ids)).all():
            emails[user.id] = user.email
    return [
        _serialize_batch(batch, emails.get(batch.user_id) if current_user.role == "admin" else current_user.email)
        for batch in batches
    ]


@router.get("/{batch_id}")
def get_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    batch = _batch_query(db, current_user).filter(BatchJob.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    owner = db.query(User).filter(User.id == batch.user_id).first()
    return _serialize_batch(batch, owner.email if owner else None)


@router.get("/{batch_id}/progress")
def get_progress(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    batch = _batch_query(db, current_user).filter(BatchJob.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    total = max(batch.total_files, 1)
    percent = round((batch.processed_files / total) * 100, 2) if batch.total_files else 0
    return {
        "batch_id": batch.id,
        "status": batch.status,
        "total_files": batch.total_files,
        "processed_files": batch.processed_files,
        "failed_files": batch.failed_files,
        "remaining_files": max(batch.total_files - batch.processed_files, 0),
        "entity_count": batch.entity_count,
        "percent_complete": percent,
        "done": batch.status in {"completed", "completed_with_errors", "failed"},
    }


@router.get("/{batch_id}/entities")
def get_entities(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    batch = _batch_query(db, current_user).filter(BatchJob.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    entities = (
        db.query(ExtractedEntity)
        .filter(ExtractedEntity.batch_id == batch_id)
        .order_by(ExtractedEntity.id.asc())
        .all()
    )
    return [
        {
            "id": e.id,
            "text": e.text,
            "label": e.label,
            "score": e.score,
            "start": e.start,
            "end": e.end,
            "source": e.source,
            "file_path": e.file_path,
            "filename": Path(str(e.file_path or "").replace("\\", "/")).name
            if e.file_path
            else None,
        }
        for e in entities
    ]


@router.get("/{batch_id}/entity-files")
def get_entity_files(
    batch_id: int,
    text: str,
    label: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return filenames only for a clicked entity. Never returns file content."""
    batch = _batch_query(db, current_user).filter(BatchJob.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    needle_text = (text or "").strip().lower()
    needle_label = (label or "").strip().upper()
    rows = (
        db.query(ExtractedEntity)
        .filter(ExtractedEntity.batch_id == batch_id)
        .all()
    )
    files = sorted(
        {
            Path(str(row.file_path).replace("\\", "/")).name
            for row in rows
            if row.file_path
            and str(row.text or "").strip().lower() == needle_text
            and str(row.label or "").strip().upper() == needle_label
        }
    )
    return {
        "text": text,
        "label": label,
        "file_count": len(files),
        "files": files,
    }


@router.get("/{batch_id}/comparison")
def get_comparison(
    batch_id: int,
    refresh_openai: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compare GLiNER (+regex/dictionary) entities vs OpenAI on the same files."""
    from app.services.comparison_service import compare_gliner_openai, run_openai_on_files
    from app.services.openai_ner_service import openai_configured

    batch = _batch_query(db, current_user).filter(BatchJob.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    stored = (
        db.query(ExtractedEntity)
        .filter(ExtractedEntity.batch_id == batch_id)
        .all()
    )
    gliner_rows = [e for e in stored if str(e.source or "").lower() != "openai"]
    openai_rows = [e for e in stored if str(e.source or "").lower() == "openai"]

    openai_payload = [
        {
            "text": e.text,
            "label": e.label,
            "score": e.score,
            "file_path": e.file_path,
            "source": "openai",
        }
        for e in openai_rows
    ]

    openai_status = "ready"
    if refresh_openai or not openai_payload:
        if not openai_configured():
            openai_status = "missing_api_key"
        else:
            files = (
                db.query(BatchFile)
                .filter(BatchFile.batch_id == batch_id)
                .order_by(BatchFile.id.asc())
                .all()
            )
            try:
                openai_payload = run_openai_on_files(files)
                openai_status = "computed"
                # Persist newly computed OpenAI entities for later visits
                if refresh_openai or not openai_rows:
                    for entity in openai_payload:
                        db.add(
                            ExtractedEntity(
                                batch_id=batch_id,
                                file_id=None,
                                text=str(entity.get("text", ""))[:1024],
                                label=str(entity.get("label", "UNKNOWN"))[:128],
                                score=float(entity.get("score") or 0.9),
                                start=entity.get("start"),
                                end=entity.get("end"),
                                source="openai",
                                file_path=entity.get("file_path"),
                            )
                        )
                    db.commit()
            except Exception as exc:
                openai_status = f"error: {exc}"

    comparison = compare_gliner_openai(gliner_rows, openai_payload)
    comparison["openai_status"] = openai_status
    comparison["openai_configured"] = openai_configured()
    return comparison

