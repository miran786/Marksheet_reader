from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class Marksheet(Base):
    __tablename__ = "marksheets"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    batch_id = Column(Integer, ForeignKey("upload_batches.id"), nullable=True)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(200), nullable=False)
    file_type = Column(String(10), nullable=False)  # jpg, png, pdf, etc.
    file_hash = Column(String(64), nullable=True, index=True)  # SHA-256 hash for duplicate detection
    raw_ocr_text = Column(Text, nullable=True)
    processing_status = Column(String(20), default="pending")  # pending, processing, review, completed, failed
    confidence_score = Column(Float, nullable=True)
    board_detected_id = Column(Integer, ForeignKey("boards.id"), nullable=True)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    processed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String(100), nullable=True)

    # Relationships
    student = relationship("Student", back_populates="marksheets")
    board_detected_rel = relationship("Board", back_populates="marksheets")
    marks = relationship("Mark", back_populates="marksheet", cascade="all, delete-orphan")
    batch = relationship("UploadBatch", back_populates="marksheets")
