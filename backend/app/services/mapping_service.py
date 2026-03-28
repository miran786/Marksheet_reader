"""Intelligent subject name mapping using exact + fuzzy matching."""

import re
import logging
from dataclasses import dataclass

from rapidfuzz import fuzz, process
from sqlalchemy.orm import Session

from app.models import SubjectMappingRule, StandardSubject
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class MappingResult:
    standard_subject_id: int | None
    standard_subject_name: str | None
    confidence: float  # 0-100
    match_type: str  # "exact", "fuzzy", "none"


def normalize_subject_name(raw: str) -> str:
    """Normalize a raw subject name for matching."""
    text = raw.upper().strip()
    # Remove subject codes like "041", "301", "(041)"
    text = re.sub(r"\(\d{2,3}\)", "", text)
    text = re.sub(r"\b\d{2,3}\b", "", text)
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Remove common suffixes
    text = re.sub(r"\s*\(STANDARD\)|\(BASIC\)|\(ELECTIVE\)|\(CORE\)", "", text, flags=re.IGNORECASE)
    return text


def find_mapping(raw_subject_name: str, db: Session, board_id: int | None = None) -> MappingResult:
    """Find the best matching standard subject for a raw subject name."""
    normalized = normalize_subject_name(raw_subject_name)

    # Step 1: Exact match in mapping rules
    result = _exact_match(normalized, db, board_id)
    if result:
        return result

    # Step 2: Exact match against standard subject names
    result = _exact_subject_match(normalized, db)
    if result:
        return result

    # Step 3: Fuzzy match
    result = _fuzzy_match(normalized, db, board_id)
    if result:
        return result

    return MappingResult(
        standard_subject_id=None,
        standard_subject_name=None,
        confidence=0.0,
        match_type="none",
    )


def _exact_match(normalized: str, db: Session, board_id: int | None) -> MappingResult | None:
    """Check for exact match in subject_mapping_rules."""
    query = db.query(SubjectMappingRule).filter(
        SubjectMappingRule.raw_text.ilike(normalized)
    )

    # Prefer board-specific rules
    if board_id:
        rule = query.filter(SubjectMappingRule.board_id == board_id).first()
        if rule:
            subject = db.query(StandardSubject).filter(StandardSubject.id == rule.standard_subject_id).first()
            return MappingResult(
                standard_subject_id=rule.standard_subject_id,
                standard_subject_name=subject.name if subject else None,
                confidence=100.0,
                match_type="exact",
            )

    # Fall back to global rules
    rule = query.filter(SubjectMappingRule.board_id.is_(None)).first()
    if not rule:
        rule = query.first()

    if rule:
        subject = db.query(StandardSubject).filter(StandardSubject.id == rule.standard_subject_id).first()
        return MappingResult(
            standard_subject_id=rule.standard_subject_id,
            standard_subject_name=subject.name if subject else None,
            confidence=100.0,
            match_type="exact",
        )

    return None


def _exact_subject_match(normalized: str, db: Session) -> MappingResult | None:
    """Check for exact match against standard subject names."""
    subject = db.query(StandardSubject).filter(
        StandardSubject.name.ilike(normalized)
    ).first()

    if subject:
        return MappingResult(
            standard_subject_id=subject.id,
            standard_subject_name=subject.name,
            confidence=100.0,
            match_type="exact",
        )
    return None


def _fuzzy_match(normalized: str, db: Session, board_id: int | None) -> MappingResult | None:
    """Fuzzy match against all known names."""
    # Build choices from mapping rules + standard subject names
    choices: dict[str, int] = {}  # text -> standard_subject_id

    # Add mapping rules
    rules = db.query(SubjectMappingRule).all()
    for rule in rules:
        choices[rule.raw_text.upper()] = rule.standard_subject_id

    # Add standard subject names
    subjects = db.query(StandardSubject).all()
    subject_map = {s.id: s.name for s in subjects}
    for s in subjects:
        choices[s.name.upper()] = s.id

    if not choices:
        return None

    # Use token_sort_ratio for best matching with word reordering
    match = process.extractOne(
        normalized,
        choices.keys(),
        scorer=fuzz.token_sort_ratio,
        score_cutoff=settings.FUZZY_REVIEW_THRESHOLD,
    )

    if match:
        matched_text, score, _ = match
        subject_id = choices[matched_text]
        subject_name = subject_map.get(subject_id, matched_text)

        return MappingResult(
            standard_subject_id=subject_id,
            standard_subject_name=subject_name,
            confidence=score,
            match_type="fuzzy",
        )

    return None
