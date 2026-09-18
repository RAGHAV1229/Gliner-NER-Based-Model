from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.batch_models import ActivityLog, BatchFile, BatchJob, ExtractedEntity
from app.database import SessionLocal
from app.services.entity_pipeline import run_entity_pipeline
from app.services.openai_ner_service import extract_openai_entities, openai_configured
from app.services.parser_service import extract_text_from_file


def process_batch_job(batch_id: int) -> None:
    db = SessionLocal()
    try:
        batch = db.query(BatchJob).filter(BatchJob.id == batch_id).first()
        if not batch:
            return

        batch.status = "processing"
        batch.started_at = datetime.utcnow()
        batch.processed_files = 0
        batch.failed_files = 0
        batch.entity_count = 0
        db.commit()

        files = (
            db.query(BatchFile)
            .filter(BatchFile.batch_id == batch_id)
            .order_by(BatchFile.id.asc())
            .all()
        )
        run_openai = openai_configured()

        for batch_file in files:
            try:
                batch_file.status = "processing"
                db.commit()

                text = extract_text_from_file(Path(batch_file.stored_path))
                if not text.strip():
                    batch_file.entity_count = 0
                    batch_file.status = "skipped_no_text"
                    batch.processed_files += 1
                    db.commit()
                    continue

                entities = run_entity_pipeline(text)

                if run_openai and text.strip():
                    try:
                        entities = entities + extract_openai_entities(text)
                    except Exception as openai_exc:
                        print(
                            f"OpenAI NER failed for {batch_file.relative_path}: {openai_exc}"
                        )

                for entity in entities:
                    db.add(
                        ExtractedEntity(
                            batch_id=batch_id,
                            file_id=batch_file.id,
                            text=str(entity.get("text", ""))[:1024],
                            label=str(entity.get("label", "UNKNOWN"))[:128],
                            score=float(entity.get("score") or 0.0),
                            start=entity.get("start"),
                            end=entity.get("end"),
                            source=str(entity.get("source") or "gliner"),
                            file_path=batch_file.relative_path,
                        )
                    )

                batch_file.entity_count = len(entities)
                batch_file.status = "completed"
                batch.processed_files += 1
                batch.entity_count += len(entities)
                db.commit()
            except Exception as exc:
                batch_file.status = "failed"
                batch_file.error_message = str(exc)[:2000]
                batch.failed_files += 1
                batch.processed_files += 1
                db.commit()

        batch.status = (
            "completed" if batch.failed_files == 0 else "completed_with_errors"
        )
        batch.completed_at = datetime.utcnow()
        db.add(
            ActivityLog(
                user_id=batch.user_id,
                action="batch_completed",
                detail=f"Batch {batch.id} finished with {batch.entity_count} entities",
                batch_id=batch.id,
            )
        )
        db.commit()
    except Exception as exc:
        batch = db.query(BatchJob).filter(BatchJob.id == batch_id).first()
        if batch:
            batch.status = "failed"
            batch.error_message = str(exc)[:2000]
            batch.completed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()
