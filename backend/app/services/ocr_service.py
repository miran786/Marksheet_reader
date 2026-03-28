"""OCR extraction service using EasyOCR and Tesseract."""

from dataclasses import dataclass
from PIL import Image
import numpy as np
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Lazy-loaded OCR readers
_easyocr_reader = None


@dataclass
class OCRResult:
    text: str
    blocks: list[dict]  # Each: {"text": str, "confidence": float, "bbox": list}
    avg_confidence: float
    engine_used: str


def _get_easyocr_reader():
    global _easyocr_reader
    if _easyocr_reader is None:
        import sys
        import io
        import easyocr
        # Windows cp1252 stdout/stderr can't handle EasyOCR's tqdm block chars (█ U+2588)
        # Reconfigure to UTF-8 with replacement to avoid UnicodeEncodeError on download
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, "reconfigure"):
                try:
                    stream.reconfigure(encoding="utf-8", errors="replace")
                except Exception:
                    pass
        _easyocr_reader = easyocr.Reader(settings.OCR_LANGUAGES, gpu=False, verbose=False)
    return _easyocr_reader


def extract_text_easyocr(image: Image.Image) -> OCRResult:
    """Extract text using EasyOCR."""
    reader = _get_easyocr_reader()
    img_array = np.array(image)

    results = reader.readtext(img_array)

    blocks = []
    for bbox, text, confidence in results:
        blocks.append({
            "text": text,
            "confidence": float(confidence),
            "bbox": [[float(c) for c in point] for point in bbox],
        })

    full_text = "\n".join(b["text"] for b in blocks)
    avg_conf = sum(b["confidence"] for b in blocks) / len(blocks) if blocks else 0.0

    return OCRResult(
        text=full_text,
        blocks=blocks,
        avg_confidence=avg_conf * 100,
        engine_used="easyocr",
    )


def extract_text_tesseract(image: Image.Image) -> OCRResult:
    """Extract text using Tesseract (fallback)."""
    import pytesseract

    if settings.TESSERACT_PATH:
        pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH

    # Get detailed data
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    blocks = []
    full_lines = []
    confidences = []

    for i in range(len(data["text"])):
        text = data["text"][i].strip()
        conf = int(data["conf"][i])
        if text and conf > 0:
            blocks.append({
                "text": text,
                "confidence": conf / 100.0,
                "bbox": [
                    [data["left"][i], data["top"][i]],
                    [data["left"][i] + data["width"][i], data["top"][i]],
                    [data["left"][i] + data["width"][i], data["top"][i] + data["height"][i]],
                    [data["left"][i], data["top"][i] + data["height"][i]],
                ],
            })
            full_lines.append(text)
            confidences.append(conf)

    # Also get plain text for better line structure
    plain_text = pytesseract.image_to_string(image)
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

    return OCRResult(
        text=plain_text,
        blocks=blocks,
        avg_confidence=avg_conf,
        engine_used="tesseract",
    )


def extract_text(image: Image.Image) -> OCRResult:
    """Extract text using configured OCR engine with fallback."""
    primary_engine = settings.OCR_ENGINE

    try:
        if primary_engine == "easyocr":
            result = extract_text_easyocr(image)
        else:
            result = extract_text_tesseract(image)

        # If confidence is too low, try the other engine
        if result.avg_confidence < 40:
            logger.warning(
                f"Low confidence ({result.avg_confidence:.1f}%) with {primary_engine}, trying fallback"
            )
            try:
                fallback = (
                    extract_text_tesseract(image)
                    if primary_engine == "easyocr"
                    else extract_text_easyocr(image)
                )
                if fallback.avg_confidence > result.avg_confidence:
                    return fallback
            except Exception as e:
                logger.warning(f"Fallback OCR engine failed: {e}")

        return result

    except Exception as e:
        logger.error(f"Primary OCR engine ({primary_engine}) failed: {e}")
        # Try fallback
        try:
            if primary_engine == "easyocr":
                return extract_text_tesseract(image)
            else:
                return extract_text_easyocr(image)
        except Exception as e2:
            logger.error(f"Fallback OCR also failed: {e2}")
            return OCRResult(text="", blocks=[], avg_confidence=0.0, engine_used="none")
