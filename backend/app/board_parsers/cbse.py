"""CBSE marksheet parser."""

import re
from app.board_parsers.base import BaseMarksheetParser, ParsedMarksheet, SubjectMark

# Valid CBSE grade values
CBSE_GRADES = {"A1", "A2", "B1", "B2", "C1", "C2", "D1", "D2", "E1", "E2", "E", "AB", "ER"}

# Words that appear in marks-in-words column — not subject names
MARKS_IN_WORDS = {
    "ZERO", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE", "TEN",
    "ELEVEN", "TWELVE", "THIRTEEN", "FOURTEEN", "FIFTEEN", "SIXTEEN", "SEVENTEEN",
    "EIGHTEEN", "NINETEEN", "TWENTY", "THIRTY", "FORTY", "FIFTY", "SIXTY", "SEVENTY",
    "EIGHTY", "NINETY", "HUNDRED",
}

# Lines to skip (headers, labels, etc.)
SKIP_LINES = {
    "SUBJECT", "NAME", "TOTAL", "GRAND TOTAL", "RESULT", "PASS", "FAIL", "MARKS OBTAINED",
    "MARKS STATEMENT", "SUB", "CODE", "GRADE", "THEORY", "ADDITIONAL SUBJECT",
    "POSITIONAL", "INTERNAL ASSESSMENT", "PRACTICAL", "TORDS", "WORDS",
    "FATHER", "MOTHER", "SCHOOL", "ROLL", "DATE OF BIRTH",
}


def _is_number(s: str) -> bool:
    """Return True if s is a plain integer (possibly with leading zeros)."""
    return bool(re.match(r"^\d{1,3}$", s.strip()))


def _is_subject_code(s: str) -> bool:
    """CBSE subject codes are 3-digit numbers (041, 085, 184, 402 …)."""
    return bool(re.match(r"^\d{3}$", s.strip()))


def _is_skip_line(s: str) -> bool:
    upper = s.upper().strip()
    if upper in SKIP_LINES:
        return True
    # Marks-in-words like "SEVENTY EIGHT" or "SIXTY TWO"
    words = set(upper.split())
    if words & MARKS_IN_WORDS:
        return True
    return False


def _is_ascii(s: str) -> bool:
    try:
        s.encode("ascii")
        return True
    except UnicodeEncodeError:
        return False


class CBSEParser(BaseMarksheetParser):
    board_code = "CBSE"

    BOARD_KEYWORDS = [
        "CENTRAL BOARD OF SECONDARY EDUCATION",
        "CBSE",
        "CERTIFICATE OF SECONDARY EDUCATION",
        "ALL INDIA SENIOR SCHOOL",
        "ALL INDIA SECONDARY SCHOOL",
    ]

    def can_parse(self, ocr_text: str) -> bool:
        text_upper = ocr_text.upper()
        return any(kw in text_upper for kw in self.BOARD_KEYWORDS)

    def parse(self, ocr_text: str) -> ParsedMarksheet:
        result = ParsedMarksheet(confidence=70.0)

        result.student_name = self._extract_name(ocr_text)
        result.roll_number = self._extract_roll_number(ocr_text)
        result.exam_year = self._extract_year(ocr_text)
        result.exam_type = self._detect_exam_type(ocr_text)
        result.school_name = self._extract_school(ocr_text)
        result.subjects = self._extract_subjects(ocr_text)

        found = sum(1 for v in [result.student_name, result.roll_number, result.subjects] if v)
        result.confidence = min(40 + found * 20, 100)

        return result

    def _extract_name(self, text: str) -> str | None:
        # CBSE marksheet: "This is to certify that\nMIRAN JAMADAR"
        match = re.search(
            r"(?:certify\s+that|CERTIFIED\s+THAT)\s*\n+\s*([A-Z][A-Z\s\.]{2,40}?)(?:\n|$)",
            text, re.IGNORECASE,
        )
        if match:
            name = match.group(1).strip()
            # Remove trailing non-name text
            name = re.sub(r"\s*(अनुक्रमांक|Roll|Father|Mother|Date).*", "", name, flags=re.IGNORECASE)
            name = name.strip()
            if len(name) >= 3 and _is_ascii(name):
                return name.title()

        # Fallback: explicit label
        for pattern in [
            r"(?:NAME\s*(?:OF\s*(?:THE\s*)?)?(?:CANDIDATE|STUDENT)|STUDENT\s*NAME)\s*[:\-]?\s*([A-Z][A-Z\s\.]{2,40})",
        ]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                name = re.sub(r"\s*(FATHER|MOTHER|CLASS|ROLL|DOB).*", "", name, flags=re.IGNORECASE)
                return name.strip().title() or None

        return None

    def _extract_roll_number(self, text: str) -> str | None:
        for p in [
            r"ROLL\s*(?:NO|NUMBER)[\.\s]*[:\-]?\s*(\d{5,15})",
            r"ROLL\s*[:\-]?\s*(\d{5,15})",
        ]:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_year(self, text: str) -> int | None:
        match = re.search(r"(?:EXAM(?:INATION)?|YEAR)\s*[:\-]?\s*(20\d{2})", text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        years = re.findall(r"\b(20\d{2})\b", text)
        if years:
            return int(years[0])
        return None

    def _detect_exam_type(self, text: str) -> str | None:
        upper = text.upper()
        if "SENIOR SCHOOL" in upper or "CLASS XII" in upper or "CLASS 12" in upper:
            return "Class 12"
        if "SECONDARY SCHOOL" in upper or "CLASS X" in upper or "CLASS 10" in upper:
            return "Class 10"
        return None

    def _extract_school(self, text: str) -> str | None:
        match = re.search(
            r"(?:SCHOOL|INSTITUTION)\s*(?:NAME)?\s*[:\-]?\s*([A-Z0-9][A-Z0-9\s\.,\-]{5,60})",
            text, re.IGNORECASE,
        )
        if match:
            return match.group(1).strip().title()
        return None

    def _extract_subjects(self, text: str) -> list[SubjectMark]:
        """Parse CBSE multi-line OCR where each field is on its own line.

        Expected block format (may vary):
            {SUB_CODE}          ← 3-digit number, e.g. 041
            {SUBJECT_NAME}      ← one or more lines, ASCII
            {THEORY}            ← 1-3 digit number
            {IA}                ← 1-3 digit number (Internal Assessment)
            {TOTAL}             ← 1-3 digit number (= THEORY + IA)
            {TOTAL_IN_WORDS}    ← "SEVENTY EIGHT" etc.  (skipped)
            {GRADE}             ← A1/B2/C1 etc.
        """
        subjects: list[SubjectMark] = []
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

        i = 0
        while i < len(lines):
            if not _is_subject_code(lines[i]):
                i += 1
                continue

            # Found a subject code — collect subject name (non-numeric ASCII lines)
            i += 1
            name_parts: list[str] = []
            while i < len(lines) and not _is_number(lines[i]):
                ln = lines[i]
                if _is_ascii(ln) and not _is_skip_line(ln) and not re.match(r"^[\W\d]+$", ln):
                    name_parts.append(ln)
                i += 1

            if not name_parts:
                continue

            subject_name = " ".join(name_parts).strip()

            # Collect up to 3 consecutive numeric lines (theory, IA, total)
            nums: list[int] = []
            while i < len(lines) and len(nums) < 3:
                ln = lines[i]
                if _is_number(ln):
                    nums.append(int(ln))
                    i += 1
                else:
                    # Some lines have colons or extra chars: "062:" → "062"
                    cleaned = re.sub(r"[^\d]", "", ln)
                    if cleaned and 1 <= len(cleaned) <= 3:
                        nums.append(int(cleaned))
                        i += 1
                    else:
                        break

            if not nums:
                continue

            # Use TOTAL (3rd number) if available; else last number found
            total = nums[2] if len(nums) >= 3 else nums[-1]

            # Try to read the grade from the line right after the numbers
            # (skip marks-in-words line if present)
            grade: str | None = None
            for offset in range(2):
                if i + offset < len(lines):
                    candidate = lines[i + offset].strip().upper()
                    if candidate in CBSE_GRADES:
                        grade = candidate
                        i += offset + 1
                        break

            subjects.append(SubjectMark(
                subject_name=subject_name,
                marks_obtained=float(total),
                max_marks=100.0,
                grade=grade,
            ))

        return subjects
