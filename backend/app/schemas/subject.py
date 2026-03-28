from pydantic import BaseModel
from datetime import datetime


class StandardSubjectCreate(BaseModel):
    name: str
    code: str
    category: str | None = None


class StandardSubjectResponse(BaseModel):
    id: int
    name: str
    code: str
    category: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
