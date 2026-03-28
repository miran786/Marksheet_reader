from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    APP_NAME: str = "Marksheet Reader"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./marksheet_reader.db"

    # File uploads
    UPLOAD_DIR: Path = Path(__file__).resolve().parent.parent.parent / "uploads"
    MAX_FILE_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: set[str] = {"jpg", "jpeg", "png", "bmp", "tiff", "tif", "webp", "pdf"}

    # OCR
    OCR_ENGINE: str = "easyocr"  # "easyocr" or "tesseract"
    TESSERACT_PATH: str | None = None
    OCR_LANGUAGES: list[str] = ["en", "hi"]

    # Subject mapping
    FUZZY_MATCH_THRESHOLD: int = 85
    FUZZY_REVIEW_THRESHOLD: int = 60

    # ERP integration
    ERP_API_KEY: str = "dev-api-key-change-me"

    # JWT
    JWT_SECRET_KEY: str = "change-me-to-a-random-secret-key-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # 7 days

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
