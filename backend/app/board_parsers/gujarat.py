"""Gujarat Board (GSEB) marksheet parser."""

import re
from app.board_parsers.base import BaseMarksheetParser, ParsedMarksheet, SubjectMark


class GujaratParser(BaseMarksheetParser):
    board_code = "GJ"

    BOARD_KEYWORDS = [
        "GUJARAT SECONDARY",
        "GSEB",
        "GUJARAT STATE EDUCATION BOARD",
        "GSHSEB",
        "GUJARAT SECONDARY AND HIGHER SECONDARY",
        "GUJARAT BOARD",
    ]

    def can_parse(self, ocr_text: str) -> bool:
        text_upper = ocr_text.upper()
        return any(kw in text_upper for kw in self.BOARD_KEYWORDS)

    def parse(self, ocr_text: str) -> ParsedMarksheet:
        result = ParsedMarksheet(confidence=65.0)

        result.student_name = self._extract_name(ocr_text)
        result.roll_number = self._extract_seat_number(ocr_text)
        result.exam_year = self._extract_year(ocr_text)
        result.exam_type = self._detect_exam_type(ocr_text)
        result.school_name = self._extract_school(ocr_text)
        result.subjects = self._extract_subjects(ocr_text)

        found = sum(1 for v in [result.student_name, result.roll_number, result.subjects] if v)
        result.confidence = min(35 + found * 20, 100)

        return result

    def _extract_name(self, text: str) -> str | None:
        patterns = [
            r"(?:NAME\s*(?:OF\s*(?:THE\s*)?)?(?:CANDIDATE|STUDENT)|STUDENT\s*NAME|CANDIDATE\s*NAME|NAME)\s*[:\-]?\s*([A-Z][A-Z\s\.]{2,50})",
            r"(?:VIDHYARTHI\s*(?:NU|NO)\s*NAAM|NAAM)\s*[:\-]?\s*([A-Z][A-Z\s\.]{2,50})",
        ]
        for p in patterns:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                name = re.sub(r"\s*(FATHER|MOTHER|SEAT|PITA|MATA).*", "", name, flags=re.IGNORECASE)
                return name.title()
        return None

    def _extract_seat_number(self, text: str) -> str | None:
        patterns = [
            r"SEAT\s*(?:NO|NUMBER)\s*[:\-]?\s*([A-Z]?\d{5,15})",
            r"ROLL\s*(?:NO|NUMBER)\s*[:\-]?\s*(\d{5,15})",
            r"BAITHAK\s*(?:KRAMANK|NO)\s*[:\-]?\s*(\d{5,15})",
        ]
        for p in patterns:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_year(self, text: str) -> int | None:
        match = re.search(
            r"(?:EXAM(?:INATION)?|YEAR|MARCH|JULY)\s*[:\-]?\s*(20\d{2})",
            text, re.IGNORECASE,
        )
        if match:
            return int(match.group(1))
        years = re.findall(r"\b(20\d{2})\b", text)
        return int(years[0]) if years else None

    def _detect_exam_type(self, text: str) -> str | None:
        text_upper = text.upper()
        if "HSC" in text_upper or "HIGHER SECONDARY" in text_upper or "CLASS XII" in text_upper:
            return "Class 12"
        if "SSC" in text_upper or "SECONDARY SCHOOL" in text_upper or "CLASS X" in text_upper:
            return "Class 10"
        return None

    def _extract_school(self, text: str) -> str | None:
        match = re.search(
            r"(?:SCHOOL|COLLEGE|INSTITUTION|CENTRE|VIDYALAYA)\s*(?:NAME)?\s*[:\-]?\s*([A-Z][A-Z\s\.,]{5,60})",
            text, re.IGNORECASE,
        )
        if match:
            return match.group(1).strip().title()
        return None

    def _extract_subjects(self, text: str) -> list[SubjectMark]:
        subjects = []
        skip_words = {
            "SUBJECT", "NAME", "TOTAL", "GRAND TOTAL", "RESULT", "MARKS",
            "OBTAINED", "MAXIMUM", "MAX", "GRADE", "VISHAY", "YOGFAL",
        }

        # Gujarat pattern: Subject Marks/Max
        pattern = r"([A-Z][A-Za-z\s\.\-&]{2,35}?)\s+(\d{1,3})\s*/\s*(\d{1,3})"
        for match in re.finditer(pattern, text, re.IGNORECASE):
            subject_name = match.group(1).strip()
            if subject_name.upper() in skip_words:
                continue
            subjects.append(SubjectMark(
                subject_name=subject_name,
                marks_obtained=float(match.group(2)),
                max_marks=float(match.group(3)),
            ))

        # Alternate: Code Subject Marks [/Max]
        if not subjects:
            pattern2 = r"(\d{2,4})\s+([A-Z][A-Za-z\s\.\-&]{2,35}?)\s+(\d{1,3})\s*(?:/\s*(\d{1,3}))?"
            for match in re.finditer(pattern2, text, re.IGNORECASE):
                subject_name = match.group(2).strip()
                if subject_name.upper() in skip_words:
                    continue
                marks = float(match.group(3))
                max_marks = float(match.group(4)) if match.group(4) else 100.0
                if marks <= 200:
                    subjects.append(SubjectMark(
                        subject_name=subject_name,
                        marks_obtained=marks,
                        max_marks=max_marks,
                    ))

        # Fallback: Subject Marks (line-end)
        if not subjects:
            pattern3 = r"^([A-Z][A-Za-z\s\.\-&]{3,30}?)\s+(\d{1,3})\s*$"
            for match in re.finditer(pattern3, text, re.MULTILINE):
                subject_name = match.group(1).strip()
                if subject_name.upper() in skip_words or len(subject_name) < 3:
                    continue
                marks = float(match.group(2))
                if marks <= 200:
                    subjects.append(SubjectMark(
                        subject_name=subject_name,
                        marks_obtained=marks,
                        max_marks=100.0,
                    ))

        return subjects
