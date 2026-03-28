"""Rajasthan Board (RBSE/BSER) marksheet parser."""

import re
from app.board_parsers.base import BaseMarksheetParser, ParsedMarksheet, SubjectMark


class RajasthanParser(BaseMarksheetParser):
    board_code = "RAJ"

    BOARD_KEYWORDS = [
        "RAJASTHAN BOARD",
        "RBSE",
        "BSER",
        "BOARD OF SECONDARY EDUCATION RAJASTHAN",
        "BOARD OF SECONDARY EDUCATION, RAJASTHAN",
        "MADHYAMIK SHIKSHA BOARD RAJASTHAN",
        "RAJASTHAN STATE BOARD",
    ]

    def can_parse(self, ocr_text: str) -> bool:
        text_upper = ocr_text.upper()
        return any(kw in text_upper for kw in self.BOARD_KEYWORDS)

    def parse(self, ocr_text: str) -> ParsedMarksheet:
        result = ParsedMarksheet(confidence=65.0)

        result.student_name = self._extract_name(ocr_text)
        result.roll_number = self._extract_roll_number(ocr_text)
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
            r"(?:VIDHYARTHI\s*KA\s*NAAM|NAAM)\s*[:\-]?\s*([A-Z][A-Z\s\.]{2,50})",
        ]
        for p in patterns:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                name = re.sub(r"\s*(FATHER|MOTHER|ROLL|PITA|MATA).*", "", name, flags=re.IGNORECASE)
                return name.title()
        return None

    def _extract_roll_number(self, text: str) -> str | None:
        patterns = [
            r"ROLL\s*(?:NO|NUMBER|NUM)\s*[:\-]?\s*(\d{5,15})",
            r"ANUCRMAANK\s*[:\-]?\s*(\d{5,15})",
            r"ANUKRAMANK\s*[:\-]?\s*(\d{5,15})",
            r"ROLL\s*[:\-]?\s*(\d{5,15})",
        ]
        for p in patterns:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_year(self, text: str) -> int | None:
        match = re.search(
            r"(?:EXAM(?:INATION)?|YEAR|MARCH|MAY)\s*[:\-]?\s*(20\d{2})",
            text, re.IGNORECASE,
        )
        if match:
            return int(match.group(1))
        years = re.findall(r"\b(20\d{2})\b", text)
        return int(years[0]) if years else None

    def _detect_exam_type(self, text: str) -> str | None:
        text_upper = text.upper()
        if "SENIOR SECONDARY" in text_upper or "CLASS XII" in text_upper or "CLASS 12" in text_upper:
            return "Class 12"
        if "SECONDARY" in text_upper or "CLASS X" in text_upper or "CLASS 10" in text_upper:
            return "Class 10"
        return None

    def _extract_school(self, text: str) -> str | None:
        match = re.search(
            r"(?:SCHOOL|INSTITUTION|VIDYALAYA|CENTRE)\s*(?:NAME)?\s*[:\-]?\s*([A-Z][A-Z\s\.,]{5,60})",
            text, re.IGNORECASE,
        )
        if match:
            return match.group(1).strip().title()
        return None

    def _extract_subjects(self, text: str) -> list[SubjectMark]:
        subjects = []
        skip_words = {
            "SUBJECT", "NAME", "TOTAL", "GRAND TOTAL", "RESULT", "MARKS",
            "OBTAINED", "MAXIMUM", "MAX", "THEORY", "PRACTICAL",
            "VISHAY", "YOGFAL",
        }

        # Rajasthan pattern: Subject Theory Practical Total [/Max]
        pattern_tp = r"([A-Z][A-Za-z\s\.\-&]{2,35}?)\s+(\d{1,3})\s+(\d{1,3})\s+(\d{1,3})\s*/?\s*(\d{1,3})?"
        for match in re.finditer(pattern_tp, text, re.IGNORECASE):
            subject_name = match.group(1).strip()
            if subject_name.upper() in skip_words:
                continue
            total = float(match.group(4))
            max_marks = float(match.group(5)) if match.group(5) else 100.0
            subjects.append(SubjectMark(
                subject_name=subject_name,
                marks_obtained=total,
                max_marks=max_marks,
            ))

        # Fallback: Subject Marks/Max
        if not subjects:
            pattern2 = r"([A-Z][A-Za-z\s\.\-&]{2,35}?)\s+(\d{1,3})\s*/\s*(\d{1,3})"
            for match in re.finditer(pattern2, text, re.IGNORECASE):
                subject_name = match.group(1).strip()
                if subject_name.upper() in skip_words:
                    continue
                subjects.append(SubjectMark(
                    subject_name=subject_name,
                    marks_obtained=float(match.group(2)),
                    max_marks=float(match.group(3)),
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
