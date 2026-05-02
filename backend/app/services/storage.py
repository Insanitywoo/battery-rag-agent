from __future__ import annotations

from pathlib import Path
import re
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings


_FILENAME_SANITIZER = re.compile(r"[^A-Za-z0-9._-]+")
_CHUNK_SIZE = 1024 * 1024
_MIME_BY_EXTENSION = {
    ".pdf": {"application/pdf"},
    ".txt": {"text/plain"},
    ".md": {"text/markdown", "text/plain"},
    ".csv": {"text/csv", "application/csv", "text/plain"},
}


def ensure_storage_root() -> Path:
    settings = get_settings()
    settings.storage_root.mkdir(parents=True, exist_ok=True)
    return settings.storage_root


def sanitize_original_filename(filename: str | None) -> str:
    candidate = Path(filename or "upload").name.strip()
    if not candidate:
        candidate = "upload"
    sanitized = _FILENAME_SANITIZER.sub("_", candidate)
    return sanitized[:255] or "upload"


def _validate_extension_and_mime(original_filename: str, mime_type: str | None) -> tuple[str, str]:
    settings = get_settings()
    extension = Path(original_filename).suffix.lower()
    if extension not in settings.allowed_upload_extensions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file extension.")

    normalized_mime = (mime_type or "").strip().lower()
    if normalized_mime not in settings.allowed_upload_mime_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported MIME type.")

    allowed_for_extension = _MIME_BY_EXTENSION.get(extension, set())
    if normalized_mime not in allowed_for_extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File extension and MIME type do not match.",
        )

    return extension, normalized_mime


def _build_storage_path(user_id: str, project_id: str, extension: str) -> tuple[Path, str]:
    storage_root = ensure_storage_root()
    relative_path = Path(user_id) / project_id / f"{uuid4().hex}{extension}"
    absolute_path = (storage_root / relative_path).resolve()

    try:
        absolute_path.relative_to(storage_root)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid storage path.") from exc

    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    return absolute_path, relative_path.as_posix()


def save_upload_file(upload: UploadFile, *, user_id: str, project_id: str) -> dict[str, str | int]:
    safe_original_name = sanitize_original_filename(upload.filename)
    extension, mime_type = _validate_extension_and_mime(safe_original_name, upload.content_type)
    absolute_path, relative_path = _build_storage_path(user_id, project_id, extension)
    settings = get_settings()
    total_size = 0

    try:
        with absolute_path.open("wb") as target:
            while True:
                chunk = upload.file.read(_CHUNK_SIZE)
                if not chunk:
                    break

                total_size += len(chunk)
                if total_size > settings.max_upload_size_bytes:
                    raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large.")
                target.write(chunk)
    except Exception:
        absolute_path.unlink(missing_ok=True)
        raise
    finally:
        upload.file.close()

    return {
        "filename": absolute_path.name,
        "original_filename": safe_original_name,
        "file_type": extension.lstrip("."),
        "mime_type": mime_type,
        "file_size": total_size,
        "storage_path": relative_path,
    }


def resolve_storage_path(storage_path: str) -> Path:
    storage_root = ensure_storage_root()
    resolved_path = (storage_root / storage_path).resolve()
    try:
        resolved_path.relative_to(storage_root)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid storage path.") from exc
    return resolved_path


def delete_stored_file(storage_path: str) -> None:
    resolve_storage_path(storage_path).unlink(missing_ok=True)
