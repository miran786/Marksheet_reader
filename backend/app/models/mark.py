from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class Mark(Base):
    __tablename__ = "marks"

    id = Column(Integer, primary_key=True, index=True)
    marksheet_id = Column(Integer, ForeignKey("marksheets.id"), nullable=False)
    raw_subject_name = Column(String(200), nullable=False)
    standard_subject_id = Column(Integer, ForeignKey("standard_subjects.id"), nullable=True)
    mapping_confidence = Column(Float, nullable=True)  # 0-100
    marks_obtained = Column(Float, nullable=True)
    max_marks = Column(Float, nullable=True)
    grade = Column(String(5), nullable=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    marksheet = relationship("Marksheet", back_populates="marks")
    standard_subject = relationship("StandardSubject", back_populates="marks")
