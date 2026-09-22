"""
FastAPI application entrypoint for the AI-Based Early Warning & Landslide Risk Monitoring System in NER.
MDoNER Problem Statement ID: 26001.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.app.core.config import settings, BASE_DIR
from backend.app.core.database import init_db
from backend.app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager: initializes database and ensures storage directories exist."""
    # Ensure necessary folders exist
    (BASE_DIR / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "backend" / "ml_engine" / "models").mkdir(parents=True, exist_ok=True)

    # Initialize database schema
    init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered early warning and real-time landslide risk monitoring platform for the North Eastern Region of India.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Serve frontend static assets
frontend_path = BASE_DIR / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(frontend_path / "index.html")
