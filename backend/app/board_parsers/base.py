"""Abstract base class for board-specific marksheet parsers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class SubjectMark:
    subject_name: str
    marks_obtained: float | None = None
    max_marks: float | None = None
    grade: str | None = None


@dataclass
class ParsedMarksheet:
    student_name: str | None = None
    roll_number: str | None = None
    exam_year: int | None = None
    exam_type: str | None = None
    school_name: str | None = None
    date_of_birth: str | None = None
    subjects: list[SubjectMark] = field(default_factory=list)
    confidence: float = 0.0  # 0-100 overall parse confidence


class BaseMarksheetParser(ABC):
    """Base class for board-specific parsers."""

    board_code: str | None = None  # e.g., "CBSE", "MH_SSC"

    @abstractmethod
    def can_parse(self, ocr_text: str) -> bool:
        """Return True if this parser can handle the given OCR text."""
        ...

    @abstractmethod
    def parse(self, ocr_text: str) -> ParsedMarksheet:
        """Extract structured data from OCR text."""
        ...
