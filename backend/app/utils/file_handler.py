from dataclasses import dataclass
import logging
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.utils.config_handler import get_ingestion_config

logger = logging.getLogger("app.utils.file_handler")


@dataclass(frozen=True)
class SavedUpload:
    path: Path
    file_type: str
    size: int


def ensure_directory(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def ensure_upload_dir() -> Path:
    return ensure_directory(settings.upload_path)


def ensure_chroma_dir() -> Path:
    return ensure_directory(settings.chroma_persist_path)


def _normalize_suffix(file_name: str | None) -> str:
    if not file_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing file name")
    return Path(file_name).suffix.lower().lstrip(".")


def validate_upload_file(file: UploadFile) -> str:
    file_type = _normalize_suffix(file.filename)
    allowed_types = set(get_ingestion_config().supported_types)
    if file_type not in allowed_types:
        logger.warning(
            "upload_validation_failed filename=%s file_type=%s allowed_types=%s reason=unsupported_type",
            file.filename,
            file_type,
            sorted(allowed_types),
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")
    return file_type


async def save_upload_file(file: UploadFile) -> SavedUpload:
    file_type = validate_upload_file(file)
    content = await file.read()
    logger.info(
        "upload_file_received filename=%s file_type=%s content_type=%s size_bytes=%s",
        file.filename,
        file_type,
        file.content_type,
        len(content),
    )

    max_size_mb = get_ingestion_config().upload.max_file_size_mb
    max_size_bytes = max_size_mb * 1024 * 1024
    if len(content) > max_size_bytes:
        logger.warning(
            "upload_validation_failed filename=%s file_type=%s size_bytes=%s max_size_bytes=%s reason=file_too_large",
            file.filename,
            file_type,
            len(content),
            max_size_bytes,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds the configured size limit of {max_size_mb} MB",
        )

    file_name = f"{uuid4().hex}.{file_type}"
    file_path = ensure_upload_dir() / file_name
    file_path.write_bytes(content)
    logger.info("upload_file_saved filename=%s saved_path=%s size_bytes=%s", file.filename, file_path, len(content))
    return SavedUpload(path=file_path, file_type=file_type, size=len(content))


def delete_file_if_exists(file_path: str | Path) -> None:
    path = Path(file_path)
    if path.exists():
        path.unlink()
