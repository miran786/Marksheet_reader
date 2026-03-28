"""Pipeline orchestrator: OCR -> Parse -> Map -> Store."""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Marksheet, Student, Mark, Board
from app.services.image_preprocess import load_image, preprocess_for_ocr
from app.services.ocr_service import extract_text
from app.services.mapping_service import find_mapping
from app.services.webhook_service import fire_webhook
from app.board_parsers import detect_and_parse
from app.config import settings

logger = logging.getLogger(__name__)


def _fire_webhook_sync(event_type: str, payload: dict) -> None:
    """Helper to fire an async webhook from synchronous pipeline code."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(fire_webhook(event_type, payload))
        else:
            loop.run_until_complete(fire_webhook(event_type, payload))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(fire_webhook(event_type, payload))
        loop.close()


def process_marksheet(marksheet_id: int) -> None:
    """Full processing pipeline for a single marksheet. Runs as background task."""
    db = SessionLocal()
    try:
        marksheet = db.query(Marksheet).filter(Marksheet.id == marksheet_id).first()
        if not marksheet:
            logger.error(f"Marksheet {marksheet_id} not found")
            return

        marksheet.processing_status = "processing"
        db.commit()

        # Step 1: Load and preprocess image
        try:
            image = load_image(marksheet.file_path)
            # EasyOCR performs its own internal preprocessing via the CRAFT detection model.
            # Applying aggressive binarization/deskew beforehand degrades its accuracy.
            # Only preprocess when Tesseract is the primary engine.
            if settings.OCR_ENGINE == "tesseract":
                processed_image = preprocess_for_ocr(image)
            else:
                from app.services.image_preprocess import preprocess_for_easyocr
                processed_image = preprocess_for_easyocr(image)
        except Exception as e:
            logger.error(f"Image preprocessing failed for marksheet {marksheet_id}: {e}")
            marksheet.processing_status = "failed"
            marksheet.raw_ocr_text = f"Error: Image preprocessing failed - {e}"
            db.commit()
            return

        # Step 2: OCR extraction
        try:
            ocr_result = extract_text(processed_image)
            marksheet.raw_ocr_text = ocr_result.text
        except Exception as e:
            logger.error(f"OCR failed for marksheet {marksheet_id}: {e}")
            marksheet.processing_status = "failed"
            marksheet.raw_ocr_text = f"Error: OCR failed - {e}"
            db.commit()
            return

        if not ocr_result.text.strip():
            marksheet.processing_status = "failed"
            marksheet.raw_ocr_text = "Error: No text extracted from image"
            db.commit()
            return

        # Step 3: Board detection + field parsing
        try:
            parsed, board_code = detect_and_parse(ocr_result.text)
        except Exception as e:
            logger.error(f"Parsing failed for marksheet {marksheet_id}: {e}")
            marksheet.processing_status = "failed"
            db.commit()
            return

        # Link to board
        board = None
        if board_code:
            board = db.query(Board).filter(Board.code == board_code).first()
            if board:
                marksheet.board_detected_id = board.id

        # Step 4: Create/update student record
        if parsed.student_name or parsed.roll_number:
            student = _get_or_create_student(db, parsed, board)
            marksheet.student_id = student.id

        # Step 5: Map subjects and create mark records
        needs_review = False
        validation_warnings = []
        for subject_mark in parsed.subjects:
            # Validate marks before storing
            marks_valid = True
            if subject_mark.marks_obtained is not None and subject_mark.marks_obtained < 0:
                validation_warnings.append(
                    f"{subject_mark.subject_name}: marks_obtained ({subject_mark.marks_obtained}) is negative"
                )
                marks_valid = False

            if (
                subject_mark.marks_obtained is not None
                and subject_mark.max_marks is not None
                and subject_mark.marks_obtained > subject_mark.max_marks
            ):
                validation_warnings.append(
                    f"{subject_mark.subject_name}: marks_obtained ({subject_mark.marks_obtained}) "
                    f"exceeds max_marks ({subject_mark.max_marks})"
                )
                marks_valid = False

            mapping = find_mapping(
                subject_mark.subject_name, db,
                board_id=board.id if board else None,
            )

            mark = Mark(
                marksheet_id=marksheet.id,
                raw_subject_name=subject_mark.subject_name,
                standard_subject_id=mapping.standard_subject_id,
                mapping_confidence=mapping.confidence,
                marks_obtained=subject_mark.marks_obtained,
                max_marks=subject_mark.max_marks,
                grade=subject_mark.grade,
                is_verified=mapping.confidence >= 100 and marks_valid,
            )
            db.add(mark)

            if mapping.confidence < settings.FUZZY_MATCH_THRESHOLD:
                needs_review = True

            if not marks_valid:
                needs_review = True

        # Step 6: Set final status
        marksheet.confidence_score = parsed.confidence
        marksheet.processed_at = datetime.now(timezone.utc)

        if not parsed.subjects:
            marksheet.processing_status = "failed"
        elif needs_review or validation_warnings:
            marksheet.processing_status = "review"
        else:
            marksheet.processing_status = "completed"

        # Append validation warnings to OCR text for review
        if validation_warnings:
            warning_text = "\n\n--- VALIDATION WARNINGS ---\n" + "\n".join(validation_warnings)
            marksheet.raw_ocr_text = (marksheet.raw_ocr_text or "") + warning_text
            logger.warning(
                f"Marksheet {marksheet_id} has validation issues: {validation_warnings}"
            )

        # Update batch counters if part of a batch
        if marksheet.batch_id and marksheet.batch:
            if marksheet.processing_status == "failed":
                marksheet.batch.failed_count += 1
            else:
                marksheet.batch.processed_count += 1

            total_done = marksheet.batch.processed_count + marksheet.batch.failed_count
            if total_done >= marksheet.batch.total_files:
                marksheet.batch.status = "completed" if marksheet.batch.failed_count == 0 else "partial"

        db.commit()
        logger.info(
            f"Marksheet {marksheet_id} processed: status={marksheet.processing_status}, "
            f"subjects={len(parsed.subjects)}, confidence={parsed.confidence:.1f}"
        )

        # Fire webhooks
        if marksheet.processing_status in ("completed", "review"):
            _fire_webhook_sync("marksheet_completed", {
                "marksheet_id": marksheet.id,
                "status": marksheet.processing_status,
                "student_roll_number": marksheet.student.roll_number if marksheet.student_id else None,
                "subject_count": len(parsed.subjects),
                "confidence": parsed.confidence,
            })

        if (
            marksheet.batch_id
            and marksheet.batch
            and marksheet.batch.status in ("completed", "partial")
        ):
            _fire_webhook_sync("batch_completed", {
                "batch_id": marksheet.batch.id,
                "status": marksheet.batch.status,
                "total_files": marksheet.batch.total_files,
                "processed_count": marksheet.batch.processed_count,
                "failed_count": marksheet.batch.failed_count,
            })

    except Exception as e:
        logger.error(f"Pipeline error for marksheet {marksheet_id}: {e}", exc_info=True)
        try:
            marksheet = db.query(Marksheet).filter(Marksheet.id == marksheet_id).first()
            if marksheet:
                marksheet.processing_status = "failed"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


def _get_or_create_student(db: Session, parsed, board) -> Student:
    """Find existing student or create a new one."""
    if parsed.roll_number:
        student = db.query(Student).filter(
            Student.roll_number == parsed.roll_number,
            Student.board_id == (board.id if board else None),
            Student.exam_year == parsed.exam_year,
        ).first()

        if student:
            # Update name if we have a better one
            if parsed.student_name and not student.name:
                student.name = parsed.student_name
            return student

    student = Student(
        name=parsed.student_name or "Unknown",
        roll_number=parsed.roll_number or f"UNKNOWN-{datetime.now(timezone.utc).timestamp():.0f}",
        board_id=board.id if board else None,
        exam_year=parsed.exam_year,
        exam_type=parsed.exam_type,
        school_name=parsed.school_name,
    )
    db.add(student)
    db.flush()
    return student
