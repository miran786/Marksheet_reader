from pydantic import BaseModel
from datetime import datetime


class BoardCreate(BaseModel):
    name: str
    code: str
    pattern_hints: list[str] = []


class BoardResponse(BaseModel):
    id: int
    name: str
    code: str
    pattern_hints: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}
