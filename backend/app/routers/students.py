from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.database import get_db
from app.models import Student, Marksheet, Mark
from app.schemas import StudentResponse, StudentListResponse

router = APIRouter()


@router.get("", response_model=StudentListResponse)
def list_students(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    board_id: int | None = None,
    exam_year: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Student).options(joinedload(Student.board))

    if search:
        query = query.filter(
            (Student.name.ilike(f"%{search}%")) | (Student.roll_number.ilike(f"%{search}%"))
        )
    if board_id:
        query = query.filter(Student.board_id == board_id)
    if exam_year:
        query = query.filter(Student.exam_year == exam_year)

    total = query.count()
    students = query.offset((page - 1) * page_size).limit(page_size).all()

    student_responses = []
    for s in students:
        ms_count = db.query(func.count(Marksheet.id)).filter(Marksheet.student_id == s.id).scalar() or 0
        student_responses.append(StudentResponse(
            id=s.id,
            name=s.name,
            roll_number=s.roll_number,
            board_id=s.board_id,
            board_name=s.board.name if s.board else None,
            exam_year=s.exam_year,
            exam_type=s.exam_type,
            date_of_birth=s.date_of_birth,
            school_name=s.school_name,
            created_at=s.created_at,
            marksheet_count=ms_count,
        ))

    return StudentListResponse(
        students=student_responses,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{student_id}/profile")
def get_student_profile(student_id: int, db: Session = Depends(get_db)):
    """Get student with all marksheets, marks, and subject-wise summary."""
    from fastapi import HTTPException
    from sqlalchemy.orm import joinedload

    student = db.query(Student).options(joinedload(Student.board)).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    marksheets = db.query(Marksheet).options(
        joinedload(Marksheet.marks).joinedload(Mark.standard_subject),
        joinedload(Marksheet.board_detected_rel),
    ).filter(Marksheet.student_id == student_id).order_by(Marksheet.uploaded_at.desc()).all()

    # Build subject summary across all marksheets
    subject_summary = {}
    for ms in marksheets:
        for mark in ms.marks:
            subj_name = mark.standard_subject.name if mark.standard_subject else mark.raw_subject_name
            if subj_name not in subject_summary:
                subject_summary[subj_name] = []
            if mark.marks_obtained is not None and mark.max_marks:
                pct = round(mark.marks_obtained / mark.max_marks * 100, 1)
                subject_summary[subj_name].append({
                    "marksheet_id": ms.id,
                    "marks_obtained": mark.marks_obtained,
                    "max_marks": mark.max_marks,
                    "percentage": pct,
                    "grade": mark.grade,
                    "exam_year": ms.student.exam_year if ms.student else None,
                })

    marksheet_data = []
    for ms in marksheets:
        total_obtained = sum(m.marks_obtained or 0 for m in ms.marks if m.marks_obtained)
        total_max = sum(m.max_marks or 0 for m in ms.marks if m.max_marks)
        marksheet_data.append({
            "id": ms.id,
            "file_name": ms.file_name,
            "processing_status": ms.processing_status,
            "board_name": ms.board_detected_rel.name if ms.board_detected_rel else None,
            "uploaded_at": ms.uploaded_at.isoformat(),
            "confidence_score": ms.confidence_score,
            "total_obtained": total_obtained,
            "total_max": total_max,
            "percentage": round(total_obtained / total_max * 100, 1) if total_max else None,
            "subjects_count": len(ms.marks),
            "marks": [
                {
                    "subject": m.standard_subject.name if m.standard_subject else m.raw_subject_name,
                    "raw_subject": m.raw_subject_name,
                    "marks_obtained": m.marks_obtained,
                    "max_marks": m.max_marks,
                    "grade": m.grade,
                    "is_verified": m.is_verified,
                }
                for m in ms.marks
            ],
        })

    return {
        "student": {
            "id": student.id,
            "name": student.name,
            "roll_number": student.roll_number,
            "board_name": student.board.name if student.board else None,
            "exam_year": student.exam_year,
            "exam_type": student.exam_type,
            "school_name": student.school_name,
        },
        "marksheets": marksheet_data,
        "subject_summary": [
            {"subject": k, "attempts": v} for k, v in subject_summary.items()
        ],
        "total_marksheets": len(marksheets),
    }


@router.get("/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).options(joinedload(Student.board)).filter(Student.id == student_id).first()
    if not student:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Student not found")

    ms_count = db.query(func.count(Marksheet.id)).filter(Marksheet.student_id == student.id).scalar() or 0

    return StudentResponse(
        id=student.id,
        name=student.name,
        roll_number=student.roll_number,
        board_id=student.board_id,
        board_name=student.board.name if student.board else None,
        exam_year=student.exam_year,
        exam_type=student.exam_type,
        date_of_birth=student.date_of_birth,
        school_name=student.school_name,
        created_at=student.created_at,
        marksheet_count=ms_count,
    )
