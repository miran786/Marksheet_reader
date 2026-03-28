from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    roll_number = Column(String(50), nullable=False, index=True)
    board_id = Column(Integer, ForeignKey("boards.id"), nullable=True)
    exam_year = Column(Integer, nullable=True)
    exam_type = Column(String(50), nullable=True)  # "Class 10", "Class 12", "Semester 3"
    date_of_birth = Column(Date, nullable=True)
    school_name = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("roll_number", "board_id", "exam_year", name="uq_student_roll_board_year"),
    )

    # Relationships
    board = relationship("Board", back_populates="students")
    marksheets = relationship("Marksheet", back_populates="student", cascade="all, delete-orphan")
