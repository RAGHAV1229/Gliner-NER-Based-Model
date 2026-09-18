from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

from fastapi import HTTPException

from app.config.upload_limits import MAX_FILE_SIZE_BYTES


ARCHIVE_EXTENSIONS = {".zip", ".tar", ".gz", ".tgz", ".bz2"}


def extract_archive(archive_path: Path, destination: Path) -> list[Path]:
    destination.mkdir(parents=True, exist_ok=True)
    suffix = archive_path.suffix.lower()
    name = archive_path.name.lower()

    try:
        if suffix == ".zip" or name.endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(destination)
        elif (
            suffix in {".tar", ".gz", ".tgz", ".bz2"}
            or name.endswith(".tar.gz")
            or name.endswith(".tgz")
        ):
            with tarfile.open(archive_path, "r:*") as tf:
                tf.extractall(destination)
        else:
            raise HTTPException(status_code=400, detail="Unsupported archive type")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to extract archive: {exc}") from exc

    files: list[Path] = []
    for path in destination.rglob("*"):
        if path.is_file():
            if path.stat().st_size > MAX_FILE_SIZE_BYTES:
                continue
            files.append(path)
    return files
