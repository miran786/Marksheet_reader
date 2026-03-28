from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class Board(Base):
    __tablename__ = "boards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False, index=True)
    pattern_hints = Column(JSON, default=list)  # regex/keywords for detection
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    students = relationship("Student", back_populates="board")
    mapping_rules = relationship("SubjectMappingRule", back_populates="board")
    marksheets = relationship("Marksheet", back_populates="board_detected_rel")
