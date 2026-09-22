"""
Pydantic schemas for Machine Learning feature vectors and prediction payloads.
Strictly defines the input features required for Landslide Susceptibility Mapping (LSM)
and Dynamic Early Warning scoring.
"""

from typing import Optional
from pydantic import BaseModel, Field


class TerrainFeatures(BaseModel):
    elevation_m: float = Field(..., ge=0.0, le=9000.0, description="Elevation above sea level in meters")
    slope_deg: float = Field(..., ge=0.0, le=90.0, description="Slope inclination angle in degrees")
    aspect_deg: float = Field(..., ge=0.0, le=360.0, description="Slope aspect / compass direction")
    profile_curvature: float = Field(..., description="Curvature parallel to slope direction")
    plan_curvature: float = Field(..., description="Curvature perpendicular to slope direction")
    topographic_wetness_index: float = Field(..., ge=0.0, description="TWI calculated from catchment area and slope")
    dist_to_fault_m: float = Field(..., ge=0.0, description="Distance to geological thrust/fault line in meters")
    dist_to_drainage_m: float = Field(..., ge=0.0, description="Distance to nearest river/drainage in meters")
    lithology_code: int = Field(..., ge=1, le=10, description="Geological formation code (1: Alluvium to 10: Schist/Gneiss)")
    lulc_code: int = Field(default=2, ge=1, le=10, description="Land use / land cover code")


class MeteorologicalFeatures(BaseModel):
    rainfall_24h_mm: float = Field(..., ge=0.0, description="Last 24 hours cumulative rainfall in mm")
    rainfall_72h_antecedent_mm: float = Field(..., ge=0.0, description="Antecedent 72 hours cumulative precipitation in mm")
    rainfall_intensity_mm_h: float = Field(default=0.0, ge=0.0, description="Peak hourly rainfall intensity in mm/hr")


class GeotechnicalFeatures(BaseModel):
    soil_moisture_pct: float = Field(..., ge=0.0, le=100.0, description="Volumetric soil water content percentage")
    pore_water_pressure_kpa: float = Field(..., description="Pore water pressure measured by piezometer in kPa")
    tilt_rate_mm_h: float = Field(default=0.0, ge=0.0, description="Ground displacement or tilt rate in mm/hour")


class LandslidePredictionInput(BaseModel):
    location_name: Optional[str] = "Unnamed Slope"
    state: Optional[str] = "Assam"
    district: Optional[str] = "Dima Hasao"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    terrain: TerrainFeatures
    meteorology: MeteorologicalFeatures
    geotechnical: GeotechnicalFeatures


class LandslidePredictionOutput(BaseModel):
    location_name: str
    state: str
    district: str
    susceptibility_class: str = Field(..., description="Very Low, Low, Moderate, High, Very High")
    susceptibility_probability: float = Field(..., ge=0.0, le=1.0)
    dynamic_hazard_index: float = Field(..., ge=0.0, le=100.0)
    early_warning_level: str = Field(..., description="GREEN, YELLOW, ORANGE, RED")
    recommended_action: str
    model_version: str
