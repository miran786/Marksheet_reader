"""Image preprocessing for better OCR accuracy."""

from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np

# Optional OpenCV import for advanced preprocessing
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


def load_image(file_path: str | Path) -> Image.Image:
    """Load image from file path. Handles PDF conversion if needed."""
    file_path = Path(file_path)
    ext = file_path.suffix.lower()

    if ext == ".pdf":
        return _pdf_to_image(file_path)

    return Image.open(file_path)


def _pdf_to_image(pdf_path: Path) -> Image.Image:
    """Convert first page of PDF to image."""
    try:
        from pdf2image import convert_from_path
        images = convert_from_path(str(pdf_path), first_page=1, last_page=1, dpi=300)
        if images:
            return images[0]
        raise ValueError("No pages found in PDF")
    except ImportError:
        raise RuntimeError(
            "pdf2image is required for PDF support. "
            "Install it with: pip install pdf2image. "
            "Also ensure poppler is installed on your system."
        )


def preprocess_for_ocr(image: Image.Image) -> Image.Image:
    """Apply preprocessing pipeline to improve OCR accuracy."""
    # Convert to RGB if needed
    if image.mode != "RGB":
        image = image.convert("RGB")

    if HAS_CV2:
        return _preprocess_cv2(image)
    return _preprocess_pillow(image)


def _preprocess_pillow(image: Image.Image) -> Image.Image:
    """Pillow-based preprocessing (fallback)."""
    # Convert to grayscale
    gray = image.convert("L")

    # Enhance contrast
    enhancer = ImageEnhance.Contrast(gray)
    gray = enhancer.enhance(2.0)

    # Enhance sharpness
    enhancer = ImageEnhance.Sharpness(gray)
    gray = enhancer.enhance(2.0)

    # Apply slight blur to reduce noise, then sharpen
    gray = gray.filter(ImageFilter.MedianFilter(size=3))
    gray = gray.filter(ImageFilter.SHARPEN)

    # Binarize using threshold
    threshold = 140
    gray = gray.point(lambda x: 255 if x > threshold else 0, "1")

    return gray.convert("RGB")


def _preprocess_cv2(image: Image.Image) -> Image.Image:
    """OpenCV-based preprocessing (preferred)."""
    # Convert PIL to numpy array
    img_array = np.array(image)

    # Convert to grayscale
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

    # Denoise
    gray = cv2.fastNlMeansDenoising(gray, h=10)

    # Adaptive thresholding for varying lighting
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # Deskew
    binary = _deskew(binary)

    # Convert back to PIL
    return Image.fromarray(binary).convert("RGB")


def _deskew(image: np.ndarray) -> np.ndarray:
    """Correct image skew using minimum area rectangle."""
    if not HAS_CV2:
        return image

    coords = np.column_stack(np.where(image > 0))
    if len(coords) < 10:
        return image

    angle = cv2.minAreaRect(coords)[-1]

    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    # Only deskew if angle is small (avoid flipping)
    if abs(angle) > 10:
        return image

    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )
    return rotated
