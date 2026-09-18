from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.database import Base


class BatchJob(Base):
    __tablename__ = "batch_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String(255), nullable=False)
    upload_type = Column(String(64), nullable=False, default="files")
    status = Column(String(64), nullable=False, default="queued")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    total_files = Column(Integer, nullable=False, default=0)
    processed_files = Column(Integer, nullable=False, default=0)
    failed_files = Column(Integer, nullable=False, default=0)
    entity_count = Column(Integer, nullable=False, default=0)
    storage_path = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class BatchFile(Base):
    __tablename__ = "batch_files"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("batch_jobs.id"), nullable=False, index=True)
    relative_path = Column(String(1024), nullable=False)
    stored_path = Column(Text, nullable=False)
    status = Column(String(64), nullable=False, default="pending")
    entity_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ExtractedEntity(Base):
    __tablename__ = "extracted_entities"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("batch_jobs.id"), nullable=False, index=True)
    file_id = Column(Integer, ForeignKey("batch_files.id"), nullable=True, index=True)
    text = Column(String(1024), nullable=False)
    label = Column(String(128), nullable=False, index=True)
    score = Column(Float, nullable=False, default=0.0)
    start = Column(Integer, nullable=True)
    end = Column(Integer, nullable=True)
    source = Column(String(64), nullable=False, default="gliner")
    file_path = Column(String(1024), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(128), nullable=False)
    detail = Column(Text, nullable=True)
    batch_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
