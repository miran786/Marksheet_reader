"""Shared test fixtures for the Marksheet Reader backend."""

import os
import sys
import pytest
from pathlib import Path

# Ensure backend/app is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models import (
    Board,
    StandardSubject,
    SubjectMappingRule,
    Student,
    Marksheet,
    Mark,
    UploadBatch,
)

# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite:///file::memory:?cache=shared"


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    # Enable WAL mode for SQLite to allow concurrent reads during tests
    @event.listens_for(eng, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)
    eng.dispose()


@pytest.fixture()
def db_session(engine):
    """Provide a transactional database session that rolls back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    """FastAPI test client with the database session overridden."""

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_board(db_session):
    board = Board(name="Central Board of Secondary Education", code="CBSE")
    db_session.add(board)
    db_session.flush()
    return board


@pytest.fixture()
def sample_board_mh(db_session):
    board = Board(name="Maharashtra State Board", code="MH_SSC")
    db_session.add(board)
    db_session.flush()
    return board


@pytest.fixture()
def sample_subjects(db_session):
    subjects = [
        StandardSubject(name="Mathematics", code="MATH", category="Science"),
        StandardSubject(name="English", code="ENG", category="Language"),
        StandardSubject(name="Physics", code="PHY", category="Science"),
        StandardSubject(name="Chemistry", code="CHEM", category="Science"),
        StandardSubject(name="Hindi", code="HINDI", category="Language"),
        StandardSubject(name="Computer Science", code="CS", category="Science"),
        StandardSubject(name="Biology", code="BIO", category="Science"),
    ]
    for s in subjects:
        db_session.add(s)
    db_session.flush()
    return {s.code: s for s in subjects}


@pytest.fixture()
def sample_mapping_rules(db_session, sample_board, sample_subjects):
    rules = [
        SubjectMappingRule(
            raw_text="MATHEMATICS",
            standard_subject_id=sample_subjects["MATH"].id,
            board_id=sample_board.id,
        ),
        SubjectMappingRule(
            raw_text="ENGLISH CORE",
            standard_subject_id=sample_subjects["ENG"].id,
            board_id=sample_board.id,
        ),
        SubjectMappingRule(
            raw_text="ENGLISH",
            standard_subject_id=sample_subjects["ENG"].id,
            board_id=None,  # global rule
        ),
        SubjectMappingRule(
            raw_text="PHYSICS",
            standard_subject_id=sample_subjects["PHY"].id,
            board_id=None,
        ),
    ]
    for r in rules:
        db_session.add(r)
    db_session.flush()
    return rules


@pytest.fixture()
def sample_student(db_session, sample_board):
    student = Student(
        name="Rahul Kumar",
        roll_number="12345678",
        board_id=sample_board.id,
        exam_year=2025,
        exam_type="Class 12",
        school_name="Delhi Public School",
    )
    db_session.add(student)
    db_session.flush()
    return student


@pytest.fixture()
def sample_marksheet(db_session, sample_student):
    marksheet = Marksheet(
        student_id=sample_student.id,
        file_path="/fake/path/test.jpg",
        file_name="test.jpg",
        file_type="jpg",
        file_hash="a" * 64,
        processing_status="completed",
        confidence_score=85.0,
    )
    db_session.add(marksheet)
    db_session.flush()
    return marksheet


@pytest.fixture()
def sample_marks(db_session, sample_marksheet, sample_subjects):
    marks = [
        Mark(
            marksheet_id=sample_marksheet.id,
            raw_subject_name="MATHEMATICS",
            standard_subject_id=sample_subjects["MATH"].id,
            mapping_confidence=100.0,
            marks_obtained=95,
            max_marks=100,
            is_verified=True,
        ),
        Mark(
            marksheet_id=sample_marksheet.id,
            raw_subject_name="ENGLISH CORE",
            standard_subject_id=sample_subjects["ENG"].id,
            mapping_confidence=100.0,
            marks_obtained=88,
            max_marks=100,
            is_verified=True,
        ),
        Mark(
            marksheet_id=sample_marksheet.id,
            raw_subject_name="FIZICS",
            standard_subject_id=None,
            mapping_confidence=72.0,
            marks_obtained=76,
            max_marks=100,
            is_verified=False,
        ),
    ]
    for m in marks:
        db_session.add(m)
    db_session.flush()
    return marks


@pytest.fixture()
def upload_dir(tmp_path):
    """Provide a temporary upload directory and patch settings."""
    from app.config import settings
    original = settings.UPLOAD_DIR
    settings.UPLOAD_DIR = tmp_path
    tmp_path.mkdir(parents=True, exist_ok=True)
    yield tmp_path
    settings.UPLOAD_DIR = original
