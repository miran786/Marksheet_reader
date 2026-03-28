"""Tests for the subject mapping service."""

from app.services.mapping_service import normalize_subject_name, find_mapping


class TestNormalizeSubjectName:
    def test_basic_normalization(self):
        assert normalize_subject_name("  Mathematics  ") == "MATHEMATICS"

    def test_removes_subject_codes(self):
        assert normalize_subject_name("MATHEMATICS (041)") == "MATHEMATICS"
        assert normalize_subject_name("041 MATHEMATICS") == "MATHEMATICS"

    def test_removes_suffixes(self):
        result = normalize_subject_name("MATHEMATICS (STANDARD)")
        assert result.strip() == "MATHEMATICS"
        result = normalize_subject_name("MATHEMATICS (BASIC)")
        assert result.strip() == "MATHEMATICS"

    def test_collapses_whitespace(self):
        assert normalize_subject_name("COMPUTER   SCIENCE") == "COMPUTER SCIENCE"


class TestFindMapping:
    def test_exact_match(self, db, seed_data):
        result = find_mapping("MATHEMATICS", db)
        assert result.standard_subject_id == seed_data["math"].id
        assert result.confidence == 100.0
        assert result.match_type == "exact"

    def test_exact_match_case_insensitive(self, db, seed_data):
        result = find_mapping("mathematics", db)
        assert result.standard_subject_id == seed_data["math"].id
        assert result.confidence == 100.0

    def test_exact_match_alternate_name(self, db, seed_data):
        result = find_mapping("MATHS", db)
        assert result.standard_subject_id == seed_data["math"].id

    def test_exact_match_standard_subject(self, db, seed_data):
        # "Hindi" is a standard subject but has no mapping rule
        result = find_mapping("Hindi", db)
        assert result.standard_subject_id == seed_data["hindi"].id
        assert result.confidence == 100.0

    def test_fuzzy_match(self, db, seed_data):
        result = find_mapping("MATHAMATICS", db)  # misspelling
        assert result.standard_subject_id == seed_data["math"].id
        assert result.match_type == "fuzzy"
        assert result.confidence >= 60

    def test_fuzzy_match_with_code(self, db, seed_data):
        result = find_mapping("MATHEMATICS-041", db)
        assert result.standard_subject_id == seed_data["math"].id

    def test_no_match(self, db, seed_data):
        result = find_mapping("ZXCVBNMASDFG", db)
        assert result.standard_subject_id is None
        assert result.match_type == "none"
        assert result.confidence == 0.0
