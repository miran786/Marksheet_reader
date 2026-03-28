from pydantic import BaseModel
from datetime import datetime


class MappingRuleCreate(BaseModel):
    raw_text: str
    standard_subject_id: int
    board_id: int | None = None
    confidence_threshold: float = 85.0


class MappingRuleResponse(BaseModel):
    id: int
    raw_text: str
    standard_subject_id: int
    standard_subject_name: str | None = None
    board_id: int | None
    board_name: str | None = None
    confidence_threshold: float
    is_manual: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MappingResolveRequest(BaseModel):
    standard_subject_id: int
