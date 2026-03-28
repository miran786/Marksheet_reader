from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Student, Marksheet, Mark, Board, StandardSubject
from app.schemas import DashboardStats

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_students = db.query(func.count(Student.id)).scalar() or 0
    total_marksheets = db.query(func.count(Marksheet.id)).scalar() or 0
    pending_review = db.query(func.count(Marksheet.id)).filter(
        Marksheet.processing_status == "review"
    ).scalar() or 0
    completed = db.query(func.count(Marksheet.id)).filter(
        Marksheet.processing_status == "completed"
    ).scalar() or 0
    failed = db.query(func.count(Marksheet.id)).filter(
        Marksheet.processing_status == "failed"
    ).scalar() or 0
    total_boards = db.query(func.count(Board.id)).scalar() or 0
    total_subjects = db.query(func.count(StandardSubject.id)).scalar() or 0
    unresolved_mappings = db.query(func.count(Mark.id)).filter(
        Mark.standard_subject_id.is_(None)
    ).scalar() or 0

    return DashboardStats(
        total_students=total_students,
        total_marksheets=total_marksheets,
        pending_review=pending_review,
        completed=completed,
        failed=failed,
        total_boards=total_boards,
        total_subjects=total_subjects,
        unresolved_mappings=unresolved_mappings,
    )
