"""
Health check endpoint providing runtime verification of backend, database, and ML services.
"""

import sqlite3
from fastapi import APIRouter, Depends
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.ml.interface import get_ml_service
from backend.app.models.schemas import HealthCheckResponse

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse, summary="System Health & Diagnostic Check")
def health_check(db: sqlite3.Connection = Depends(get_db)):
    """Verifies that the API server, database, and ML subsystem are responsive."""
    # 1. Test database connectivity
    cursor = db.cursor()
    cursor.execute("SELECT 1;")
    db_result = cursor.fetchone()
    db_status = "operational" if db_result and db_result[0] == 1 else "degraded"

    # 2. Check ML service state
    ml_service = get_ml_service()
    ml_status = f"loaded ({ml_service.version})" if ml_service.is_calibrated else f"baseline ({ml_service.version})"

    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
        environment=settings.ENVIRONMENT,
        database=db_status,
        ml_service_status=ml_status,
    )
