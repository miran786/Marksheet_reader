from pydantic import BaseModel
from datetime import datetime


class MarkResponse(BaseModel):
    id: int
    raw_subject_name: str
    standard_subject_id: int | None
    standard_subject_name: str | None = None
    mapping_confidence: float | None
    marks_obtained: float | None
    max_marks: float | None
    grade: str | None
    is_verified: bool

    model_config = {"from_attributes": True}


class MarkUpdateRequest(BaseModel):
    raw_subject_name: str | None = None
    standard_subject_id: int | None = None
    marks_obtained: float | None = None
    max_marks: float | None = None
    grade: str | None = None


class MarksheetResponse(BaseModel):
    id: int
    student_id: int | None
    student_name: str | None = None
    file_name: str
    file_url: str | None = None   # served path e.g. /uploads/uuid.png
    file_type: str
    processing_status: str
    confidence_score: float | None
    board_detected_id: int | None
    board_name: str | None = None
    uploaded_at: datetime
    processed_at: datetime | None
    reviewed_by: str | None
    marks: list[MarkResponse] = []

    model_config = {"from_attributes": True}


class UploadResponse(BaseModel):
    id: int
    file_name: str
    processing_status: str
    message: str


class BatchStatusResponse(BaseModel):
    id: int
    name: str | None
    total_files: int
    processed_count: int
    failed_count: int
    status: str
    created_at: datetime
    marksheets: list[UploadResponse] = []

    model_config = {"from_attributes": True}
