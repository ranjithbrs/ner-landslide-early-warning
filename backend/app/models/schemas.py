"""
Pydantic schemas for request validation and API responses.
"""

from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field


# ------------------------------------------------------------------------------
# System & Health
# ------------------------------------------------------------------------------
class HealthCheckResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    environment: str
    database: str
    ml_service_status: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ------------------------------------------------------------------------------
# Incident Reports (Citizen & Field Officer)
# ------------------------------------------------------------------------------
class IncidentReportCreate(BaseModel):
    reporter_name: str = Field(..., min_length=2, max_length=100)
    contact_number: Optional[str] = Field(None, max_length=20)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    state: str = Field(..., min_length=2, max_length=50)
    district: str = Field(..., min_length=2, max_length=50)
    incident_type: str = Field(..., description="Crack, Rockfall, Mudslide, Blockage, Subsidence")
    severity: str = Field(default="Medium", description="Low, Medium, High, Critical")
    description: str = Field(..., min_length=5, max_length=1000)
    photo_url: Optional[str] = None
    sync_status: Optional[str] = "synced"


class IncidentReportResponse(IncidentReportCreate):
    id: int
    status: str
    created_at: str


# ------------------------------------------------------------------------------
# Sensor Readings
# ------------------------------------------------------------------------------
class SensorReadingCreate(BaseModel):
    station_id: str
    station_name: str
    state: str
    district: str
    latitude: float
    longitude: float
    soil_moisture_pct: float = Field(..., ge=0.0, le=100.0)
    pore_pressure_kpa: float
    rainfall_1h_mm: float = Field(..., ge=0.0)
    tilt_displacement_mm: float
    battery_pct: float = Field(default=100.0, ge=0.0, le=100.0)


class SensorReadingResponse(SensorReadingCreate):
    id: int
    recorded_at: str


# ------------------------------------------------------------------------------
# Alerts
# ------------------------------------------------------------------------------
class AlertLogCreate(BaseModel):
    alert_level: str = Field(..., description="GREEN, YELLOW, ORANGE, RED")
    state: str
    district: str
    corridor_affected: Optional[str] = None
    title: str
    message: str
    channels: str = "SMS, WhatsApp, Web"


class AlertLogResponse(AlertLogCreate):
    id: int
    dispatched_at: str


# ------------------------------------------------------------------------------
# Road Corridors
# ------------------------------------------------------------------------------
class RoadCorridorResponse(BaseModel):
    id: int
    corridor_code: str
    name: str
    state: str
    start_point: str
    end_point: str
    status: str
    risk_level: str
    last_updated: str
