"""Seed the database with initial data."""

import json
from pathlib import Path

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import Board, StandardSubject, SubjectMappingRule, User
from app.services.auth_service import hash_password

SEED_DIR = Path(__file__).parent / "seed_data"


def seed_boards(db: Session) -> None:
    if db.query(Board).count() > 0:
        print("Boards already seeded, skipping.")
        return

    with open(SEED_DIR / "boards.json") as f:
        boards = json.load(f)

    for b in boards:
        db.add(Board(name=b["name"], code=b["code"], pattern_hints=b["pattern_hints"]))

    db.commit()
    print(f"Seeded {len(boards)} boards.")


def seed_subjects(db: Session) -> None:
    if db.query(StandardSubject).count() > 0:
        print("Subjects already seeded, skipping.")
        return

    with open(SEED_DIR / "standard_subjects.json") as f:
        subjects = json.load(f)

    for s in subjects:
        db.add(StandardSubject(name=s["name"], code=s["code"], category=s["category"]))

    db.commit()
    print(f"Seeded {len(subjects)} standard subjects.")


def seed_mappings(db: Session) -> None:
    if db.query(SubjectMappingRule).count() > 0:
        print("Mappings already seeded, skipping.")
        return

    with open(SEED_DIR / "sample_mappings.json") as f:
        mappings = json.load(f)

    # Build code -> id lookup
    subjects = {s.code: s.id for s in db.query(StandardSubject).all()}

    count = 0
    for m in mappings:
        subject_id = subjects.get(m["subject_code"])
        if subject_id:
            db.add(SubjectMappingRule(
                raw_text=m["raw_text"],
                standard_subject_id=subject_id,
                is_manual=False,
            ))
            count += 1

    db.commit()
    print(f"Seeded {count} mapping rules.")


def seed_admin(db: Session) -> None:
    if db.query(User).filter(User.username == "admin").first():
        print("Admin user already exists, skipping.")
        return

    admin = User(
        username="admin",
        email="admin@marksheetreader.local",
        hashed_password=hash_password("admin123"),
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    print("Seeded default admin user (username=admin, password=admin123).")


def run_seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_boards(db)
        seed_subjects(db)
        seed_mappings(db)
        seed_admin(db)
        print("Seeding complete!")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
