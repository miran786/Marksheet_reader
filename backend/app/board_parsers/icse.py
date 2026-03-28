"""ICSE/ISC marksheet parser."""

import re
from app.board_parsers.base import BaseMarksheetParser, ParsedMarksheet, SubjectMark


class ICSEParser(BaseMarksheetParser):
    board_code = "ICSE"

    BOARD_KEYWORDS = [
        "COUNCIL FOR THE INDIAN SCHOOL CERTIFICATE",
        "INDIAN SCHOOL CERTIFICATE",
        "ICSE",
        "ISC EXAMINATION",
        "CISCE",
    ]

    def can_parse(self, ocr_text: str) -> bool:
        text_upper = ocr_text.upper()
        return any(kw in text_upper for kw in self.BOARD_KEYWORDS)

    def parse(self, ocr_text: str) -> ParsedMarksheet:
        result = ParsedMarksheet(confidence=65.0)

        result.student_name = self._extract_name(ocr_text)
        result.roll_number = self._extract_id(ocr_text)
        result.exam_year = self._extract_year(ocr_text)
        result.exam_type = self._detect_exam_type(ocr_text)
        result.subjects = self._extract_subjects(ocr_text)

        found = sum(1 for v in [result.student_name, result.roll_number, result.subjects] if v)
        result.confidence = min(35 + found * 20, 100)

        return result

    def _extract_name(self, text: str) -> str | None:
        match = re.search(
            r"(?:NAME\s*(?:OF\s*(?:THE\s*)?)?CANDIDATE|STUDENT\s*NAME|NAME)\s*[:\-]?\s*([A-Z][A-Z\s\.]{2,40})",
            text, re.IGNORECASE
        )
        if match:
            name = match.group(1).strip()
            name = re.sub(r"\s*(FATHER|MOTHER|UID|CLASS|UNIQUE).*", "", name, flags=re.IGNORECASE)
            return name.title()
        return None

    def _extract_id(self, text: str) -> str | None:
        patterns = [
            r"UNIQUE\s*ID\s*[:\-]?\s*(\w{5,20})",
            r"UID\s*[:\-]?\s*(\w{5,20})",
            r"INDEX\s*(?:NO|NUMBER)\s*[:\-]?\s*(\w{5,20})",
            r"ROLL\s*(?:NO|NUMBER)?\s*[:\-]?\s*(\d{5,15})",
        ]
        for p in patterns:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_year(self, text: str) -> int | None:
        match = re.search(r"(?:EXAM|YEAR)\s*[:\-]?\s*(20\d{2})", text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        years = re.findall(r"\b(20\d{2})\b", text)
        return int(years[0]) if years else None

    def _detect_exam_type(self, text: str) -> str | None:
        text_upper = text.upper()
        if "ISC" in text_upper:
            return "Class 12"
        if "ICSE" in text_upper:
            return "Class 10"
        return None

    def _extract_subjects(self, text: str) -> list[SubjectMark]:
        subjects = []

        # ICSE pattern: SUBJECT INTERNAL EXTERNAL TOTAL
        pattern = r"([A-Z][A-Z\s\.\-&]{2,35})\s+(\d{1,3})\s+(\d{1,3})\s+(\d{1,3})"
        for match in re.finditer(pattern, text, re.IGNORECASE):
            subject_name = match.group(1).strip()
            if subject_name.upper() in ("SUBJECT", "NAME", "TOTAL", "GRAND TOTAL", "RESULT", "INTERNAL", "EXTERNAL"):
                continue
            total = float(match.group(4))
            subjects.append(SubjectMark(
                subject_name=subject_name,
                marks_obtained=total,
                max_marks=100.0,
            ))

        # Fallback: SUBJECT MARKS/MAX
        if not subjects:
            pattern2 = r"([A-Z][A-Z\s\.\-&]{2,35})\s+(\d{1,3})\s*/\s*(\d{1,3})"
            for match in re.finditer(pattern2, text, re.IGNORECASE):
                subject_name = match.group(1).strip()
                if subject_name.upper() in ("SUBJECT", "NAME", "TOTAL", "GRAND TOTAL"):
                    continue
                subjects.append(SubjectMark(
                    subject_name=subject_name,
                    marks_obtained=float(match.group(2)),
                    max_marks=float(match.group(3)),
                ))

        return subjects
