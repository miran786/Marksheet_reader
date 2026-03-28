"""Shared test fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Board, StandardSubject, SubjectMappingRule, User
from app.services.auth_service import hash_password, create_access_token


TEST_DB_URL = "sqlite:///./test_marksheet_reader.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    """Get a test database session."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def override_get_db(db):
    """Override FastAPI's get_db dependency with the test session."""
    def _override():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(override_get_db):
    """FastAPI TestClient."""
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c


@pytest.fixture
def seed_data(db):
    """Seed test DB with boards, subjects, and mapping rules."""
    # Boards
    cbse = Board(name="CBSE", code="CBSE", pattern_hints=["CBSE"])
    mh = Board(name="Maharashtra", code="MH_SSC", pattern_hints=["MAHARASHTRA"])
    db.add_all([cbse, mh])
    db.flush()

    # Subjects
    math = StandardSubject(name="Mathematics", code="MATH", category="Science")
    eng = StandardSubject(name="English", code="ENG", category="Language")
    phy = StandardSubject(name="Physics", code="PHY", category="Science")
    chem = StandardSubject(name="Chemistry", code="CHEM", category="Science")
    hindi = StandardSubject(name="Hindi", code="HIN", category="Language")
    db.add_all([math, eng, phy, chem, hindi])
    db.flush()

    # Mapping rules
    db.add_all([
        SubjectMappingRule(raw_text="MATHEMATICS", standard_subject_id=math.id),
        SubjectMappingRule(raw_text="MATHS", standard_subject_id=math.id),
        SubjectMappingRule(raw_text="ENGLISH", standard_subject_id=eng.id),
        SubjectMappingRule(raw_text="PHYSICS", standard_subject_id=phy.id),
        SubjectMappingRule(raw_text="CHEMISTRY", standard_subject_id=chem.id),
    ])
    db.commit()

    return {"cbse": cbse, "mh": mh, "math": math, "eng": eng, "phy": phy, "chem": chem, "hindi": hindi}


@pytest.fixture
def admin_user(db):
    """Create an admin user and return auth token."""
    user = User(
        username="testadmin",
        email="admin@test.com",
        hashed_password=hash_password("password123"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(data={"sub": user.id, "role": user.role})
    return {"user": user, "token": token}


@pytest.fixture
def auth_headers(admin_user):
    """Authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {admin_user['token']}"}
