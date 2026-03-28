from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_students: int
    total_marksheets: int
    pending_review: int
    completed: int
    failed: int
    total_boards: int
    total_subjects: int
    unresolved_mappings: int
