"""
API v1 Router aggregating all endpoint modules.
"""

from fastapi import APIRouter
from backend.app.api.v1.endpoints import health, risk, sensors, reports, alerts, roads

api_router = APIRouter()

api_router.include_router(health.router, tags=["System Health"])
api_router.include_router(risk.router, prefix="/risk", tags=["Landslide Risk & ML"])
api_router.include_router(sensors.router, prefix="/sensors", tags=["IoT Ground Telemetry"])
api_router.include_router(roads.router, prefix="/roads", tags=["Road Network & Corridors"])
api_router.include_router(reports.router, prefix="/reports", tags=["Crowdsourced Incident Reports"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Emergency Early Warnings"])
