from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.database import get_db
from app.models import Student, Marksheet
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
