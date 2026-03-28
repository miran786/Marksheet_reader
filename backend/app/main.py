from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine, Base, get_db
from app.models.marksheet import Marksheet
from app.routers import upload, students, marksheets, mappings, erp, dashboard, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    Base.metadata.create_all(bind=engine)
    # Ensure upload directory exists
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Automated marksheet reading and intelligent subject mapping system",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploaded marksheets
app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(students.router, prefix="/api/students", tags=["Students"])
app.include_router(marksheets.router, prefix="/api/marksheets", tags=["Marksheets"])
app.include_router(mappings.router, prefix="/api/mappings", tags=["Mappings"])
app.include_router(erp.router, prefix="/api/erp", tags=["ERP Integration"])


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/api/marksheets/{marksheet_id}/image")
def serve_marksheet_image(marksheet_id: int, db: Session = Depends(get_db)):
    """Serve the uploaded marksheet image file by marksheet ID."""
    m = db.query(Marksheet).filter(Marksheet.id == marksheet_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Marksheet not found")
    file_path = Path(m.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found on disk")
    return FileResponse(str(file_path))
