"""Generic fallback marksheet parser using heuristics."""

import re
from app.board_parsers.base import BaseMarksheetParser, ParsedMarksheet, SubjectMark


class GenericParser(BaseMarksheetParser):
    board_code = None  # Unknown board

    def can_parse(self, ocr_text: str) -> bool:
        return True  # Always matches as fallback

    def parse(self, ocr_text: str) -> ParsedMarksheet:
        result = ParsedMarksheet(confidence=40.0)

        result.student_name = self._extract_name(ocr_text)
        result.roll_number = self._extract_roll(ocr_text)
        result.exam_year = self._extract_year(ocr_text)
        result.subjects = self._extract_subjects(ocr_text)

        found = sum(1 for v in [result.student_name, result.roll_number, result.subjects] if v)
        result.confidence = min(20 + found * 15, 80)

        return result

    def _extract_name(self, text: str) -> str | None:
        patterns = [
            r"(?:NAME\s*(?:OF\s*(?:THE\s*)?)?(?:CANDIDATE|STUDENT|EXAMINEE)|STUDENT\s*NAME)\s*[:\-]?\s*([A-Z][A-Za-z\s\.]{2,40})",
            r"NAME\s*[:\-]\s*([A-Z][A-Za-z\s\.]{2,40})",
        ]
        for p in patterns:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                name = re.sub(r"\s*(FATHER|MOTHER|ROLL|DOB|CLASS|SEAT|DATE).*", "", name, flags=re.IGNORECASE)
                if len(name) > 2:
                    return name.title()
        return None

    def _extract_roll(self, text: str) -> str | None:
        patterns = [
            r"(?:ROLL|SEAT|REG(?:ISTRATION)?|INDEX|HALL\s*TICKET)\s*(?:NO|NUMBER|NUM)?\s*[:\-]?\s*([A-Z0-9]{4,20})",
        ]
        for p in patterns:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_year(self, text: str) -> int | None:
        years = re.findall(r"\b(20\d{2})\b", text)
        return int(years[0]) if years else None

    def _extract_subjects(self, text: str) -> list[SubjectMark]:
        subjects = []
        skip_words = {
            "SUBJECT", "NAME", "TOTAL", "GRAND TOTAL", "RESULT", "MARKS",
            "OBTAINED", "MAXIMUM", "MAX", "GRADE", "PASS", "FAIL",
            "PERCENTAGE", "AGGREGATE", "SEAT", "ROLL", "DATE", "YEAR",
        }

        # Pattern 1: Subject marks/max
        for match in re.finditer(
            r"([A-Z][A-Za-z\s\.\-&]{2,35}?)\s+(\d{1,3})\s*/\s*(\d{1,3})", text
        ):
            name = match.group(1).strip()
            if name.upper() in skip_words:
                continue
            subjects.append(SubjectMark(
                subject_name=name,
                marks_obtained=float(match.group(2)),
                max_marks=float(match.group(3)),
            ))

        # Pattern 2: Subject code Subject marks
        if not subjects:
            for match in re.finditer(
                r"(\d{2,3})\s+([A-Z][A-Za-z\s\.\-&]{2,35}?)\s+(\d{1,3})", text
            ):
                name = match.group(2).strip()
                if name.upper() in skip_words:
                    continue
                marks = float(match.group(3))
                if marks <= 200:
                    subjects.append(SubjectMark(
                        subject_name=name,
                        marks_obtained=marks,
                        max_marks=100.0,
                    ))

        # Pattern 3: Lines with text followed by a number
        if not subjects:
            for match in re.finditer(
                r"^([A-Z][A-Za-z\s\.\-&]{3,30}?)\s+(\d{1,3})\s*$", text, re.MULTILINE
            ):
                name = match.group(1).strip()
                if name.upper() in skip_words or len(name) < 3:
                    continue
                marks = float(match.group(2))
                if marks <= 200:
                    subjects.append(SubjectMark(
                        subject_name=name,
                        marks_obtained=marks,
                    ))

        return subjects
