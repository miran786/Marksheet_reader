from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class UploadBatch(Base):
    __tablename__ = "upload_batches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=True)
    total_files = Column(Integer, default=0)
    processed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    status = Column(String(20), default="in_progress")  # in_progress, completed, partial
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    marksheets = relationship("Marksheet", back_populates="batch")
