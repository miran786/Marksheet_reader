"""Tests for board-specific marksheet parsers."""

from app.board_parsers import (
    CBSEParser, ICSEParser, MaharashtraParser,
    KarnatakaParser, TamilNaduParser, RajasthanParser,
    UPBoardParser, GujaratParser, GenericParser,
    detect_and_parse,
)


CBSE_TEXT = """
CENTRAL BOARD OF SECONDARY EDUCATION
ALL INDIA SENIOR SCHOOL CERTIFICATE EXAMINATION 2024

NAME OF THE CANDIDATE: RAHUL SHARMA
FATHER NAME: SURESH SHARMA
ROLL NO: 12345678
SCHOOL NAME: Delhi Public School, R.K. Puram

SUBJECT CODE  SUBJECT NAME          MARKS
041           MATHEMATICS             095/100
042           PHYSICS                 088/100
043           CHEMISTRY               092/100
044           ENGLISH                 085/100
083           COMPUTER SCIENCE        090/100
"""

ICSE_TEXT = """
COUNCIL FOR THE INDIAN SCHOOL CERTIFICATE EXAMINATIONS
ICSE EXAMINATION 2024

CANDIDATE NAME: PRIYA PATEL
UNIQUE ID: ISC2024001234
YEAR: 2024

SUBJECT                INTERNAL  EXTERNAL  TOTAL/MAX
MATHEMATICS             20        75        95/100
ENGLISH                 18        70        88/100
PHYSICS                 19        72        91/100
"""

MAHARASHTRA_TEXT = """
MAHARASHTRA STATE BOARD OF SECONDARY AND HIGHER SECONDARY EDUCATION, PUNE
HSC EXAMINATION 2024

NAME: AMIT DESHMUKH
SEAT NUMBER: 987654
SCHOOL: St. Xavier's College, Mumbai

SUBJECT          MARKS OBTAINED    OUT OF
MATHEMATICS         85              100
PHYSICS             78              100
CHEMISTRY           82              100
ENGLISH             90              100
"""


class TestCBSEParser:
    parser = CBSEParser()

    def test_can_parse_positive(self):
        assert self.parser.can_parse(CBSE_TEXT)

    def test_can_parse_negative(self):
        assert not self.parser.can_parse("Some random text without board keywords")

    def test_parse_student_name(self):
        result = self.parser.parse(CBSE_TEXT)
        assert result.student_name is not None
        assert "Rahul" in result.student_name

    def test_parse_roll_number(self):
        result = self.parser.parse(CBSE_TEXT)
        assert result.roll_number == "12345678"

    def test_parse_exam_year(self):
        result = self.parser.parse(CBSE_TEXT)
        assert result.exam_year == 2024

    def test_parse_exam_type(self):
        result = self.parser.parse(CBSE_TEXT)
        assert result.exam_type == "Class 12"

    def test_parse_subjects(self):
        result = self.parser.parse(CBSE_TEXT)
        assert len(result.subjects) >= 3
        subject_names = [s.subject_name.upper() for s in result.subjects]
        assert any("MATH" in n for n in subject_names)

    def test_confidence_with_all_fields(self):
        result = self.parser.parse(CBSE_TEXT)
        assert result.confidence >= 60


class TestICSEParser:
    parser = ICSEParser()

    def test_can_parse(self):
        assert self.parser.can_parse(ICSE_TEXT)

    def test_parse_name(self):
        result = self.parser.parse(ICSE_TEXT)
        assert result.student_name is not None
        assert "Priya" in result.student_name

    def test_parse_subjects(self):
        result = self.parser.parse(ICSE_TEXT)
        assert len(result.subjects) >= 2


class TestMaharashtraParser:
    parser = MaharashtraParser()

    def test_can_parse(self):
        assert self.parser.can_parse(MAHARASHTRA_TEXT)

    def test_parse_seat_number(self):
        result = self.parser.parse(MAHARASHTRA_TEXT)
        assert result.roll_number == "987654"

    def test_parse_exam_type(self):
        result = self.parser.parse(MAHARASHTRA_TEXT)
        assert result.exam_type == "Class 12"


class TestKarnatakaParser:
    parser = KarnatakaParser()

    def test_can_parse(self):
        assert self.parser.can_parse("KARNATAKA SECONDARY EDUCATION EXAMINATION BOARD")
        assert not self.parser.can_parse("Random text")


class TestTamilNaduParser:
    parser = TamilNaduParser()

    def test_can_parse(self):
        assert self.parser.can_parse("DIRECTORATE OF GOVERNMENT EXAMINATIONS TAMIL NADU")
        assert not self.parser.can_parse("Random text")


class TestRajasthanParser:
    parser = RajasthanParser()

    def test_can_parse(self):
        assert self.parser.can_parse("BOARD OF SECONDARY EDUCATION RAJASTHAN")
        assert self.parser.can_parse("RBSE EXAMINATION 2024")


class TestUPBoardParser:
    parser = UPBoardParser()

    def test_can_parse(self):
        assert self.parser.can_parse("MADHYAMIK SHIKSHA PARISHAD UTTAR PRADESH")
        assert self.parser.can_parse("UP BOARD HIGH SCHOOL")


class TestGujaratParser:
    parser = GujaratParser()

    def test_can_parse(self):
        assert self.parser.can_parse("GUJARAT SECONDARY AND HIGHER SECONDARY EDUCATION BOARD")
        assert self.parser.can_parse("GSEB SSC EXAMINATION")


class TestGenericParser:
    parser = GenericParser()

    def test_always_can_parse(self):
        assert self.parser.can_parse("literally anything")
        assert self.parser.can_parse("")


class TestDetectAndParse:
    def test_detects_cbse(self):
        result, board_code = detect_and_parse(CBSE_TEXT)
        assert board_code == "CBSE"
        assert result.student_name is not None

    def test_detects_icse(self):
        result, board_code = detect_and_parse(ICSE_TEXT)
        assert board_code == "ICSE"

    def test_detects_maharashtra(self):
        result, board_code = detect_and_parse(MAHARASHTRA_TEXT)
        assert board_code == "MH_SSC"

    def test_falls_back_to_generic(self):
        result, board_code = detect_and_parse("No known board text here. Name: John Doe. Marks: 95")
        assert board_code is None or board_code == "GENERIC"
