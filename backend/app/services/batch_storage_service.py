from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.config.upload_limits import MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB

BACKEND_DIR = Path(__file__).resolve().parents[2]
BATCH_UPLOAD_ROOT = BACKEND_DIR / "batch_uploads"
BATCH_UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)

MAX_FILES_PER_BATCH = float("inf")
MAX_BATCH_SIZE_BYTES = float("inf")


def create_batch_directory(batch_id: int) -> Path:
    path = BATCH_UPLOAD_ROOT / f"batch_{batch_id}_{uuid.uuid4().hex[:8]}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def delete_batch_directory(path: str | Path | None) -> None:
    if not path:
        return
    directory = Path(path)
    if directory.exists() and directory.is_dir():
        shutil.rmtree(directory, ignore_errors=True)


async def save_uploaded_file(
    upload: UploadFile,
    destination_dir: Path,
    relative_path: str | None = None,
) -> Path:
    safe_name = (relative_path or upload.filename or "file.bin").replace("\\", "/").lstrip("/")
    # Prevent path escape
    parts = [part for part in Path(safe_name).parts if part not in ("..", ".")]
    target = destination_dir.joinpath(*parts) if parts else destination_dir / "file.bin"
    target.parent.mkdir(parents=True, exist_ok=True)

    size = 0
    with target.open("wb") as handle:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_FILE_SIZE_BYTES:
                handle.close()
                target.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail=f"File exceeds {MAX_FILE_SIZE_MB} MB limit",
                )
            handle.write(chunk)
    await upload.close()
    return target


def copy_local_file(source: Path, destination_dir: Path, relative_path: str) -> Path:
    parts = [part for part in Path(relative_path).parts if part not in ("..", ".")]
    target = destination_dir.joinpath(*parts)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def resolve_import_source(source_path: str) -> Path:
    path = Path(source_path).expanduser().resolve()
    if not path.exists():
        raise HTTPException(status_code=400, detail="Source path does not exist")
    return path
