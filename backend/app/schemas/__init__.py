from app.schemas.board import BoardCreate, BoardResponse
from app.schemas.subject import StandardSubjectCreate, StandardSubjectResponse
from app.schemas.mapping import MappingRuleCreate, MappingRuleResponse, MappingResolveRequest
from app.schemas.student import StudentResponse, StudentListResponse
from app.schemas.marksheet import (
    MarksheetResponse,
    MarkResponse,
    MarkUpdateRequest,
    UploadResponse,
    BatchStatusResponse,
)
from app.schemas.dashboard import DashboardStats

__all__ = [
    "BoardCreate", "BoardResponse",
    "StandardSubjectCreate", "StandardSubjectResponse",
    "MappingRuleCreate", "MappingRuleResponse", "MappingResolveRequest",
    "StudentResponse", "StudentListResponse",
    "MarksheetResponse", "MarkResponse", "MarkUpdateRequest",
    "UploadResponse", "BatchStatusResponse",
    "DashboardStats",
]
