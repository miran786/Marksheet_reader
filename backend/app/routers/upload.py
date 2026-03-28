import uuid
import hashlib
import shutil
from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models import Marksheet, UploadBatch
from app.schemas import UploadResponse, BatchStatusResponse
from app.services.pipeline import process_marksheet

router = APIRouter()

# MIME types corresponding to allowed image/document extensions
ALLOWED_MIME_TYPES: dict[str, set[str]] = {
    "jpg": {"image/jpeg", "image/jpg"},
    "jpeg": {"image/jpeg", "image/jpg"},
    "png": {"image/png"},
    "bmp": {"image/bmp", "image/x-bmp", "image/x-ms-bmp"},
    "tiff": {"image/tiff", "image/x-tiff"},
    "tif": {"image/tiff", "image/x-tiff"},
    "webp": {"image/webp"},
    "pdf": {"application/pdf"},
}

# Generic MIME types that browsers sometimes send — skip content-type check for these
GENERIC_MIME_TYPES = {"application/octet-stream", "binary/octet-stream", ""}

MAX_FILE_SIZE_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


def _validate_file(file: UploadFile) -> str:
    """Validate file extension, MIME type, and return the extension."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not allowed. Allowed: {', '.join(sorted(settings.ALLOWED_EXTENSIONS))}",
        )

    # Validate MIME type (skip check for generic browser content-types)
    if file.content_type and file.content_type not in GENERIC_MIME_TYPES:
        allowed_mimes = ALLOWED_MIME_TYPES.get(ext, set())
        if allowed_mimes and file.content_type not in allowed_mimes:
            raise HTTPException(
                status_code=400,
                detail=f"MIME type '{file.content_type}' does not match extension '{ext}'. Expected: {', '.join(sorted(allowed_mimes))}",
            )

    return ext


def _validate_file_size(content: bytes) -> None:
    """Validate that file content does not exceed the maximum allowed size."""
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB",
        )


def _compute_file_hash(content: bytes) -> str:
    """Compute SHA-256 hash of file content."""
    return hashlib.sha256(content).hexdigest()


def _check_duplicate(file_hash: str, db: Session) -> Marksheet | None:
    """Check if a file with the same hash has already been uploaded."""
    return db.query(Marksheet).filter(Marksheet.file_hash == file_hash).first()


def _save_content(content: bytes, ext: str) -> Path:
    """Save file content with a UUID name and return the path."""
    filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = settings.UPLOAD_DIR / filename
    with open(file_path, "wb") as f:
        f.write(content)
    return file_path


@router.post("/single", response_model=UploadResponse)
async def upload_single(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    ext = _validate_file(file)

    # Read content for size check and hashing
    content = await file.read()
    _validate_file_size(content)

    # Duplicate detection
    file_hash = _compute_file_hash(content)
    existing = _check_duplicate(file_hash, db)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Duplicate file detected. This file was already uploaded as '{existing.file_name}' (ID: {existing.id})",
        )

    file_path = _save_content(content, ext)

    marksheet = Marksheet(
        file_path=str(file_path),
        file_name=file.filename,
        file_type=ext,
        file_hash=file_hash,
        processing_status="pending",
    )
    db.add(marksheet)
    db.commit()
    db.refresh(marksheet)

    # Process in background
    background_tasks.add_task(process_marksheet, marksheet.id)

    return UploadResponse(
        id=marksheet.id,
        file_name=file.filename,
        processing_status="pending",
        message="File uploaded successfully. Processing started.",
    )


@router.post("/bulk", response_model=BatchStatusResponse)
async def upload_bulk(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    batch = UploadBatch(
        name=f"Batch upload - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
        total_files=len(files),
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    upload_responses = []
    for file in files:
        try:
            ext = _validate_file(file)

            content = await file.read()
            _validate_file_size(content)

            file_hash = _compute_file_hash(content)
            existing = _check_duplicate(file_hash, db)
            if existing:
                raise HTTPException(
                    status_code=409,
                    detail=f"Duplicate file: already uploaded as '{existing.file_name}' (ID: {existing.id})",
                )

            file_path = _save_content(content, ext)

            marksheet = Marksheet(
                file_path=str(file_path),
                file_name=file.filename,
                file_type=ext,
                file_hash=file_hash,
                processing_status="pending",
                batch_id=batch.id,
            )
            db.add(marksheet)
            db.commit()
            db.refresh(marksheet)

            background_tasks.add_task(process_marksheet, marksheet.id)

            upload_responses.append(UploadResponse(
                id=marksheet.id,
                file_name=file.filename,
                processing_status="pending",
                message="Queued for processing",
            ))
        except HTTPException as e:
            upload_responses.append(UploadResponse(
                id=0,
                file_name=file.filename or "unknown",
                processing_status="failed",
                message=str(e.detail),
            ))
            batch.failed_count += 1
            db.commit()

    return BatchStatusResponse(
        id=batch.id,
        name=batch.name,
        total_files=batch.total_files,
        processed_count=batch.processed_count,
        failed_count=batch.failed_count,
        status=batch.status,
        created_at=batch.created_at,
        marksheets=upload_responses,
    )


@router.get("/batch/{batch_id}", response_model=BatchStatusResponse)
def get_batch_status(batch_id: int, db: Session = Depends(get_db)):
    batch = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    marksheet_responses = [
        UploadResponse(
            id=m.id,
            file_name=m.file_name,
            processing_status=m.processing_status,
            message="",
        )
        for m in batch.marksheets
    ]

    return BatchStatusResponse(
        id=batch.id,
        name=batch.name,
        total_files=batch.total_files,
        processed_count=batch.processed_count,
        failed_count=batch.failed_count,
        status=batch.status,
        created_at=batch.created_at,
        marksheets=marksheet_responses,
    )
