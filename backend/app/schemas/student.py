from pydantic import BaseModel
from datetime import datetime, date


class StudentResponse(BaseModel):
    id: int
    name: str
    roll_number: str
    board_id: int | None
    board_name: str | None = None
    exam_year: int | None
    exam_type: str | None
    date_of_birth: date | None
    school_name: str | None
    created_at: datetime
    marksheet_count: int = 0

    model_config = {"from_attributes": True}


class StudentListResponse(BaseModel):
    students: list[StudentResponse]
    total: int
    page: int
    page_size: int
