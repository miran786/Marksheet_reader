from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import SubjectMappingRule, Mark, StandardSubject
from app.schemas import (
    MappingRuleCreate,
    MappingRuleResponse,
    MappingResolveRequest,
    StandardSubjectCreate,
    StandardSubjectResponse,
    MarkResponse,
)

router = APIRouter()


# --- Standard Subjects ---

@router.get("/subjects", response_model=list[StandardSubjectResponse])
def list_subjects(db: Session = Depends(get_db)):
    return db.query(StandardSubject).order_by(StandardSubject.name).all()


@router.post("/subjects", response_model=StandardSubjectResponse)
def create_subject(data: StandardSubjectCreate, db: Session = Depends(get_db)):
    subject = StandardSubject(name=data.name, code=data.code, category=data.category)
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


# --- Mapping Rules ---

@router.get("", response_model=list[MappingRuleResponse])
def list_mappings(
    board_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(SubjectMappingRule).options(
        joinedload(SubjectMappingRule.standard_subject),
        joinedload(SubjectMappingRule.board),
    )
    if board_id:
        query = query.filter(SubjectMappingRule.board_id == board_id)

    rules = query.order_by(SubjectMappingRule.raw_text).all()

    return [
        MappingRuleResponse(
            id=r.id,
            raw_text=r.raw_text,
            standard_subject_id=r.standard_subject_id,
            standard_subject_name=r.standard_subject.name if r.standard_subject else None,
            board_id=r.board_id,
            board_name=r.board.name if r.board else None,
            confidence_threshold=r.confidence_threshold,
            is_manual=r.is_manual,
            created_at=r.created_at,
        )
        for r in rules
    ]


@router.post("", response_model=MappingRuleResponse)
def create_mapping(data: MappingRuleCreate, db: Session = Depends(get_db)):
    rule = SubjectMappingRule(
        raw_text=data.raw_text,
        standard_subject_id=data.standard_subject_id,
        board_id=data.board_id,
        confidence_threshold=data.confidence_threshold,
        is_manual=True,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    subject = db.query(StandardSubject).filter(StandardSubject.id == rule.standard_subject_id).first()
    return MappingRuleResponse(
        id=rule.id,
        raw_text=rule.raw_text,
        standard_subject_id=rule.standard_subject_id,
        standard_subject_name=subject.name if subject else None,
        board_id=rule.board_id,
        board_name=None,
        confidence_threshold=rule.confidence_threshold,
        is_manual=rule.is_manual,
        created_at=rule.created_at,
    )


@router.delete("/{rule_id}")
def delete_mapping(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(SubjectMappingRule).filter(SubjectMappingRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Mapping rule not found")
    db.delete(rule)
    db.commit()
    return {"message": "Mapping rule deleted"}


# --- Unresolved mappings ---

@router.get("/unresolved", response_model=list[MarkResponse])
def list_unresolved(db: Session = Depends(get_db)):
    marks = db.query(Mark).filter(
        Mark.standard_subject_id.is_(None)
    ).order_by(Mark.created_at.desc()).limit(100).all()

    return [
        MarkResponse(
            id=m.id,
            raw_subject_name=m.raw_subject_name,
            standard_subject_id=m.standard_subject_id,
            standard_subject_name=None,
            mapping_confidence=m.mapping_confidence,
            marks_obtained=m.marks_obtained,
            max_marks=m.max_marks,
            grade=m.grade,
            is_verified=m.is_verified,
        )
        for m in marks
    ]


@router.post("/resolve/{mark_id}", response_model=MarkResponse)
def resolve_mapping(
    mark_id: int,
    data: MappingResolveRequest,
    db: Session = Depends(get_db),
):
    mark = db.query(Mark).filter(Mark.id == mark_id).first()
    if not mark:
        raise HTTPException(status_code=404, detail="Mark not found")

    # Update the mark
    mark.standard_subject_id = data.standard_subject_id
    mark.mapping_confidence = 100.0
    mark.is_verified = True

    # Auto-create a mapping rule for future use (the learning loop)
    existing_rule = db.query(SubjectMappingRule).filter(
        SubjectMappingRule.raw_text == mark.raw_subject_name,
        SubjectMappingRule.standard_subject_id == data.standard_subject_id,
    ).first()

    if not existing_rule:
        rule = SubjectMappingRule(
            raw_text=mark.raw_subject_name,
            standard_subject_id=data.standard_subject_id,
            is_manual=True,
        )
        db.add(rule)

    db.commit()
    db.refresh(mark)

    subject = db.query(StandardSubject).filter(StandardSubject.id == mark.standard_subject_id).first()

    return MarkResponse(
        id=mark.id,
        raw_subject_name=mark.raw_subject_name,
        standard_subject_id=mark.standard_subject_id,
        standard_subject_name=subject.name if subject else None,
        mapping_confidence=mark.mapping_confidence,
        marks_obtained=mark.marks_obtained,
        max_marks=mark.max_marks,
        grade=mark.grade,
        is_verified=mark.is_verified,
    )
