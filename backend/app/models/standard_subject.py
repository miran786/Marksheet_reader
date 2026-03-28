from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class StandardSubject(Base):
    __tablename__ = "standard_subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=True)  # Language, Science, Commerce, Arts
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    mapping_rules = relationship("SubjectMappingRule", back_populates="standard_subject")
    marks = relationship("Mark", back_populates="standard_subject")
