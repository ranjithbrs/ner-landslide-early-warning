"""
Production Landslide Risk and Early Warning Prediction Service.
Loads the trained Random Forest pipeline, executes feature extraction,
and computes both static spatial susceptibility and dynamic multi-variable hazard indices.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any

import joblib
import numpy as np
import pandas as pd

from backend.app.core.config import settings
from backend.app.ml.interface import BaseLandslideModel
from backend.app.ml.schemas import (
    LandslidePredictionInput,
    LandslidePredictionOutput,
)
from backend.ml_engine.pipeline import ALL_MODEL_FEATURES


class TrainedLandslidePredictor(BaseLandslideModel):
    """
    Production-grade predictor wrapping the trained Random Forest pipeline.
    Combines machine-learned spatial susceptibility with empirical real-time trigger dynamics.
    """

    def __init__(self, model_path: Path, metadata_path: Path):
        self.model_path = model_path
        self.metadata_path = metadata_path
        self.pipeline = joblib.load(model_path)
        
        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}

        self._version = self.metadata.get("version", "1.0.0")

    @property
    def is_calibrated(self) -> bool:
        return True

    @property
    def version(self) -> str:
        return f"random-forest-v{self._version}"

    def _prepare_feature_row(self, input_data: LandslidePredictionInput) -> pd.DataFrame:
        """Flattens the nested Pydantic input schema into a DataFrame matching training features."""
        row_dict = {
            "elevation_m": input_data.terrain.elevation_m,
            "slope_deg": input_data.terrain.slope_deg,
            "aspect_deg": input_data.terrain.aspect_deg,
            "profile_curvature": input_data.terrain.profile_curvature,
            "plan_curvature": input_data.terrain.plan_curvature,
            "topographic_wetness_index": input_data.terrain.topographic_wetness_index,
            "dist_to_fault_m": input_data.terrain.dist_to_fault_m,
            "dist_to_drainage_m": input_data.terrain.dist_to_drainage_m,
            "lithology_code": input_data.terrain.lithology_code,
            "lulc_code": input_data.terrain.lulc_code,
            "rainfall_24h_mm": input_data.meteorology.rainfall_24h_mm,
            "rainfall_72h_antecedent_mm": input_data.meteorology.rainfall_72h_antecedent_mm,
            "rainfall_intensity_mm_h": input_data.meteorology.rainfall_intensity_mm_h,
            "soil_moisture_pct": input_data.geotechnical.soil_moisture_pct,
            "pore_water_pressure_kpa": input_data.geotechnical.pore_water_pressure_kpa,
            "tilt_rate_mm_h": input_data.geotechnical.tilt_rate_mm_h,
        }
        return pd.DataFrame([row_dict])[ALL_MODEL_FEATURES]

    def predict(self, input_data: LandslidePredictionInput) -> LandslidePredictionOutput:
        # 1. Prepare features
        X = self._prepare_feature_row(input_data)

        # 2. Run Random Forest Inference for Spatial Susceptibility
        proba = float(self.pipeline.predict_proba(X)[0, 1])

        # Map probability to susceptibility class
        if proba < 0.20:
            susceptibility = "Very Low"
        elif proba < 0.40:
            susceptibility = "Low"
        elif proba < 0.60:
            susceptibility = "Moderate"
        elif proba < 0.80:
            susceptibility = "High"
        else:
            susceptibility = "Very High"

        # 3. Dynamic Real-Time Landslide Hazard Index (DLHI) calculation
        # Synthesizes:
        # - ML spatial probability (35%)
        # - Real-time rainfall trigger vs regional threshold (30%)
        # - Soil moisture saturation (20%)
        # - Biaxial ground tilt displacement (15%)
        rain_ratio = min(input_data.meteorology.rainfall_24h_mm / settings.RAINFALL_RED_THRESHOLD_MM, 1.2)
        moisture_ratio = min(input_data.geotechnical.soil_moisture_pct / settings.SOIL_MOISTURE_CRITICAL_PCT, 1.2)
        tilt_ratio = min(input_data.geotechnical.tilt_rate_mm_h / 2.0, 1.5)

        dlhi = (
            (proba * 100.0) * 0.35
            + (rain_ratio * 100.0) * 0.30
            + (moisture_ratio * 100.0) * 0.20
            + (tilt_ratio * 100.0) * 0.15
        )
        dlhi = round(float(np.clip(dlhi, 0.0, 100.0)), 1)

        # 4. Multi-level Warning Assignment and Recommended Operational Action
        if dlhi >= 75.0:
            level = "RED"
            action = (
                "CRITICAL ALERT (RED): Imminent landslide danger. Recommend immediate evacuation of downhill settlements, "
                "halt all vehicular traffic along highway corridor, and dispatch SDRF/NDRF search and rescue teams."
            )
        elif dlhi >= 50.0:
            level = "ORANGE"
            action = (
                "HIGH ALERT (ORANGE): Soil saturation critical and rainfall thresholds breached. Restrict heavy commercial traffic, "
                "activate district emergency operations centers (DEOC), and place earth-moving machinery on standby."
            )
        elif dlhi >= 30.0:
            level = "YELLOW"
            action = (
                "ADVISORY (YELLOW): Elevated soil moisture and steady rainfall. Issue traveler advisories for vulnerable road cuts "
                "and deploy field patrols along chronic landslide points."
            )
        else:
            level = "GREEN"
            action = "NORMAL (GREEN): Low slope destabilization probability. Continue routine telemetry surveillance."

        return LandslidePredictionOutput(
            location_name=input_data.location_name or "Slope Assessment Zone",
            state=input_data.state or "NER",
            district=input_data.district or "District",
            susceptibility_class=susceptibility,
            susceptibility_probability=round(proba, 4),
            dynamic_hazard_index=dlhi,
            early_warning_level=level,
            recommended_action=action,
            model_version=self.version,
        )
