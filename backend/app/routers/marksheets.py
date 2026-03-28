from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timezone
from pathlib import Path

from app.database import get_db
from app.models import Marksheet, Mark
from app.schemas import MarksheetResponse, MarkResponse, MarkUpdateRequest

router = APIRouter()


def _build_marksheet_response(m: Marksheet) -> MarksheetResponse:
    marks = []
    for mark in m.marks:
        marks.append(MarkResponse(
            id=mark.id,
            raw_subject_name=mark.raw_subject_name,
            standard_subject_id=mark.standard_subject_id,
            standard_subject_name=mark.standard_subject.name if mark.standard_subject else None,
            mapping_confidence=mark.mapping_confidence,
            marks_obtained=mark.marks_obtained,
            max_marks=mark.max_marks,
            grade=mark.grade,
            is_verified=mark.is_verified,
        ))

    # Build a URL-safe relative path from the stored absolute file_path
    file_url = f"/uploads/{Path(m.file_path).name}" if m.file_path else None

    return MarksheetResponse(
        id=m.id,
        student_id=m.student_id,
        student_name=m.student.name if m.student else None,
        file_name=m.file_name,
        file_url=file_url,
        file_type=m.file_type,
        processing_status=m.processing_status,
        confidence_score=m.confidence_score,
        board_detected_id=m.board_detected_id,
        board_name=m.board_detected_rel.name if m.board_detected_rel else None,
        uploaded_at=m.uploaded_at,
        processed_at=m.processed_at,
        reviewed_by=m.reviewed_by,
        marks=marks,
    )


@router.get("", response_model=list[MarksheetResponse])
def list_marksheets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Marksheet).options(
        joinedload(Marksheet.student),
        joinedload(Marksheet.board_detected_rel),
        joinedload(Marksheet.marks).joinedload(Mark.standard_subject),
    )

    if status:
        query = query.filter(Marksheet.processing_status == status)

    marksheets = query.order_by(Marksheet.uploaded_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return [_build_marksheet_response(m) for m in marksheets]


@router.post("/bulk-verify")
def bulk_verify_marksheets(
    min_confidence: float = Query(90.0, ge=0, le=100),
    reviewer: str = "auto",
    db: Session = Depends(get_db),
):
    """Auto-verify all marks with confidence >= min_confidence across all marksheets in 'review' status."""
    marks_in_review = db.query(Mark).join(
        Marksheet, Mark.marksheet_id == Marksheet.id
    ).filter(
        Marksheet.processing_status == "review",
        Mark.is_verified == False,
        Mark.mapping_confidence >= min_confidence,
    ).all()

    verified_count = 0
    marksheet_ids = set()
    for mark in marks_in_review:
        mark.is_verified = True
        verified_count += 1
        marksheet_ids.add(mark.marksheet_id)

    # For each affected marksheet, check if all marks are now verified → set completed
    for ms_id in marksheet_ids:
        ms = db.query(Marksheet).filter(Marksheet.id == ms_id).first()
        if ms and all(m.is_verified for m in ms.marks):
            ms.processing_status = "completed"
            ms.reviewed_by = reviewer

    db.commit()
    return {
        "verified_marks": verified_count,
        "affected_marksheets": len(marksheet_ids),
        "min_confidence_used": min_confidence,
    }


@router.get("/{marksheet_id}/image")
def get_marksheet_image(marksheet_id: int, db: Session = Depends(get_db)):
    """Serve the uploaded marksheet image by ID."""
    m = db.query(Marksheet).filter(Marksheet.id == marksheet_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Marksheet not found")
    file_path = Path(m.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found")
    return FileResponse(str(file_path))


@router.get("/{marksheet_id}", response_model=MarksheetResponse)
def get_marksheet(marksheet_id: int, db: Session = Depends(get_db)):
    m = db.query(Marksheet).options(
        joinedload(Marksheet.student),
        joinedload(Marksheet.board_detected_rel),
        joinedload(Marksheet.marks).joinedload(Mark.standard_subject),
    ).filter(Marksheet.id == marksheet_id).first()

    if not m:
        raise HTTPException(status_code=404, detail="Marksheet not found")
    return _build_marksheet_response(m)


@router.put("/{marksheet_id}/marks/{mark_id}", response_model=MarkResponse)
def update_mark(
    marksheet_id: int,
    mark_id: int,
    data: MarkUpdateRequest,
    db: Session = Depends(get_db),
):
    mark = db.query(Mark).filter(
        Mark.id == mark_id, Mark.marksheet_id == marksheet_id
    ).first()
    if not mark:
        raise HTTPException(status_code=404, detail="Mark not found")

    if data.raw_subject_name is not None:
        mark.raw_subject_name = data.raw_subject_name
    if data.standard_subject_id is not None:
        mark.standard_subject_id = data.standard_subject_id
        mark.is_verified = True

    # Validate marks_obtained
    if data.marks_obtained is not None:
        if data.marks_obtained < 0:
            raise HTTPException(
                status_code=422,
                detail="marks_obtained must be >= 0",
            )
        # Check against max_marks (use incoming or existing value)
        effective_max = data.max_marks if data.max_marks is not None else mark.max_marks
        if effective_max is not None and data.marks_obtained > effective_max:
            raise HTTPException(
                status_code=422,
                detail=f"marks_obtained ({data.marks_obtained}) must be <= max_marks ({effective_max})",
            )
        mark.marks_obtained = data.marks_obtained

    if data.max_marks is not None:
        if data.max_marks < 0:
            raise HTTPException(
                status_code=422,
                detail="max_marks must be >= 0",
            )
        # Re-check existing marks_obtained against new max
        effective_obtained = data.marks_obtained if data.marks_obtained is not None else mark.marks_obtained
        if effective_obtained is not None and effective_obtained > data.max_marks:
            raise HTTPException(
                status_code=422,
                detail=f"marks_obtained ({effective_obtained}) must be <= max_marks ({data.max_marks})",
            )
        mark.max_marks = data.max_marks

    if data.grade is not None:
        import re
        # Allow grades like A1, A2, B1, B2, C1, C2, D, E, A+, A-, A, B, C, O, etc.
        if not re.match(r"^[A-Oa-o][+\-12]?$", data.grade):
            raise HTTPException(
                status_code=422,
                detail=f"Invalid grade format: '{data.grade}'. Expected formats: A1, B2, A+, A, O, etc.",
            )
        mark.grade = data.grade

    db.commit()
    db.refresh(mark)

    return MarkResponse(
        id=mark.id,
        raw_subject_name=mark.raw_subject_name,
        standard_subject_id=mark.standard_subject_id,
        standard_subject_name=mark.standard_subject.name if mark.standard_subject else None,
        mapping_confidence=mark.mapping_confidence,
        marks_obtained=mark.marks_obtained,
        max_marks=mark.max_marks,
        grade=mark.grade,
        is_verified=mark.is_verified,
    )


@router.post("/{marksheet_id}/verify")
def verify_marksheet(
    marksheet_id: int,
    reviewer: str = "admin",
    db: Session = Depends(get_db),
):
    m = db.query(Marksheet).filter(Marksheet.id == marksheet_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Marksheet not found")

    m.processing_status = "completed"
    m.reviewed_by = reviewer
    m.processed_at = datetime.now(timezone.utc)

    # Mark all marks as verified
    db.query(Mark).filter(Mark.marksheet_id == marksheet_id).update({"is_verified": True})
    db.commit()

    return {"message": "Marksheet verified successfully"}


@router.delete("/{marksheet_id}")
def delete_marksheet(marksheet_id: int, db: Session = Depends(get_db)):
    m = db.query(Marksheet).filter(Marksheet.id == marksheet_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Marksheet not found")

    db.delete(m)
    db.commit()
    return {"message": "Marksheet deleted successfully"}
