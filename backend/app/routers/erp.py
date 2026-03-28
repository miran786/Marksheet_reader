import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import verify_erp_api_key
from app.models import Student, Marksheet, Mark
from app.models.webhook import Webhook

router = APIRouter(dependencies=[Depends(verify_erp_api_key)])


# --- Schemas ---

class WebhookCreate(BaseModel):
    url: HttpUrl
    event_type: str  # "marksheet_completed" or "batch_completed"


class WebhookResponse(BaseModel):
    id: int
    url: str
    event_type: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Student / Marks endpoints ---

@router.get("/students")
def erp_list_students(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Student).options(joinedload(Student.board))
    total = query.count()
    students = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": [
            {
                "roll_number": s.roll_number,
                "name": s.name,
                "board": s.board.code if s.board else None,
                "exam_year": s.exam_year,
                "exam_type": s.exam_type,
                "school_name": s.school_name,
            }
            for s in students
        ],
    }


@router.get("/student/{roll_number}/marks")
def erp_student_marks(roll_number: str, db: Session = Depends(get_db)):
    student = db.query(Student).options(
        joinedload(Student.board),
        joinedload(Student.marksheets).joinedload(Marksheet.marks).joinedload(Mark.standard_subject),
    ).filter(Student.roll_number == roll_number).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    marksheets_data = []
    for ms in student.marksheets:
        marksheets_data.append({
            "id": ms.id,
            "status": ms.processing_status,
            "board": ms.board_detected_rel.code if ms.board_detected_rel else None,
            "subjects": [
                {
                    "subject_code": m.standard_subject.code if m.standard_subject else None,
                    "subject_name": m.standard_subject.name if m.standard_subject else m.raw_subject_name,
                    "raw_name": m.raw_subject_name,
                    "marks_obtained": m.marks_obtained,
                    "max_marks": m.max_marks,
                    "grade": m.grade,
                    "verified": m.is_verified,
                }
                for m in ms.marks
            ],
        })

    return {
        "roll_number": student.roll_number,
        "name": student.name,
        "board": student.board.code if student.board else None,
        "exam_year": student.exam_year,
        "exam_type": student.exam_type,
        "marksheets": marksheets_data,
    }


@router.get("/export/csv")
def erp_export_csv(db: Session = Depends(get_db)):
    marks = db.query(Mark).options(
        joinedload(Mark.marksheet).joinedload(Marksheet.student).joinedload(Student.board),
        joinedload(Mark.standard_subject),
    ).filter(Mark.marksheet.has(Marksheet.processing_status.in_(["completed", "review"]))).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Student Name", "Roll Number", "Board", "Exam Year",
        "Subject (Raw)", "Subject (Standardized)", "Subject Code",
        "Marks Obtained", "Max Marks", "Grade", "Verified",
    ])

    for m in marks:
        student = m.marksheet.student if m.marksheet else None
        writer.writerow([
            student.name if student else "",
            student.roll_number if student else "",
            student.board.code if student and student.board else "",
            student.exam_year if student else "",
            m.raw_subject_name,
            m.standard_subject.name if m.standard_subject else "",
            m.standard_subject.code if m.standard_subject else "",
            m.marks_obtained,
            m.max_marks,
            m.grade or "",
            "Yes" if m.is_verified else "No",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=marksheet_export.csv"},
    )


# --- Webhook endpoints ---

VALID_EVENT_TYPES = {"marksheet_completed", "batch_completed"}


@router.post("/webhooks", response_model=WebhookResponse, status_code=201)
def register_webhook(
    payload: WebhookCreate,
    db: Session = Depends(get_db),
):
    if payload.event_type not in VALID_EVENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid event_type. Must be one of: {', '.join(sorted(VALID_EVENT_TYPES))}",
        )

    webhook = Webhook(
        url=str(payload.url),
        event_type=payload.event_type,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    return webhook


@router.get("/webhooks", response_model=list[WebhookResponse])
def list_webhooks(db: Session = Depends(get_db)):
    return db.query(Webhook).filter(Webhook.is_active.is_(True)).all()


@router.delete("/webhooks/{webhook_id}", status_code=204)
def delete_webhook(webhook_id: int, db: Session = Depends(get_db)):
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    db.delete(webhook)
    db.commit()
