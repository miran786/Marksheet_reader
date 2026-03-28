from app.board_parsers.base import BaseMarksheetParser, ParsedMarksheet, SubjectMark
from app.board_parsers.cbse import CBSEParser
from app.board_parsers.icse import ICSEParser
from app.board_parsers.maharashtra import MaharashtraParser
from app.board_parsers.karnataka import KarnatakaParser
from app.board_parsers.tamil_nadu import TamilNaduParser
from app.board_parsers.rajasthan import RajasthanParser
from app.board_parsers.up_board import UPBoardParser
from app.board_parsers.gujarat import GujaratParser
from app.board_parsers.generic import GenericParser

# Parser chain: tried in order, first match wins
PARSER_CHAIN: list[BaseMarksheetParser] = [
    CBSEParser(),
    ICSEParser(),
    MaharashtraParser(),
    KarnatakaParser(),
    TamilNaduParser(),
    RajasthanParser(),
    UPBoardParser(),
    GujaratParser(),
    GenericParser(),  # Always matches as fallback
]


def detect_and_parse(ocr_text: str) -> tuple[ParsedMarksheet, str | None]:
    """Try each parser in chain, return (parsed_data, board_code)."""
    for parser in PARSER_CHAIN:
        if parser.can_parse(ocr_text):
            result = parser.parse(ocr_text)
            return result, parser.board_code

    # Should never reach here since GenericParser always matches
    return GenericParser().parse(ocr_text), None


__all__ = [
    "BaseMarksheetParser", "ParsedMarksheet", "SubjectMark",
    "CBSEParser", "ICSEParser", "MaharashtraParser",
    "KarnatakaParser", "TamilNaduParser", "RajasthanParser",
    "UPBoardParser", "GujaratParser", "GenericParser",
    "PARSER_CHAIN", "detect_and_parse",
]
