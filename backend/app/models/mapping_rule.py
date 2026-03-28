from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class SubjectMappingRule(Base):
    __tablename__ = "subject_mapping_rules"

    id = Column(Integer, primary_key=True, index=True)
    raw_text = Column(String(200), nullable=False, index=True)
    standard_subject_id = Column(Integer, ForeignKey("standard_subjects.id"), nullable=False)
    board_id = Column(Integer, ForeignKey("boards.id"), nullable=True)  # NULL = global rule
    confidence_threshold = Column(Float, default=85.0)
    is_manual = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    standard_subject = relationship("StandardSubject", back_populates="mapping_rules")
    board = relationship("Board", back_populates="mapping_rules")
