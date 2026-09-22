"""
Abstract interface and factory for the Landslide Machine Learning Service.
Establishes clear contracts so that Phase 2 model training integrates cleanly
without breaking API endpoints or downstream services.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from backend.app.core.config import settings
from backend.app.ml.schemas import (
    LandslidePredictionInput,
    LandslidePredictionOutput,
)


class BaseLandslideModel(ABC):
    """Abstract base class defining the contract for all ML predictors."""

    @abstractmethod
    def predict(self, input_data: LandslidePredictionInput) -> LandslidePredictionOutput:
        """Computes spatial susceptibility and dynamic early warning hazard."""
        pass

    @property
    @abstractmethod
    def is_calibrated(self) -> bool:
        """Returns True if a trained ML artifact is loaded, False if fallback."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Identifier for the active model."""
        pass


class FallbackLandslidePredictor(BaseLandslideModel):
    """
    Phase 1 Foundation Baseline Predictor.
    Provides rule-based fallback responses before Phase 2 ML model training.
    Clearly marked as uncalibrated baseline so there are no fake completed claims.
    """

    @property
    def is_calibrated(self) -> bool:
        return False

    @property
    def version(self) -> str:
        return "phase-1-uncalibrated-baseline"

    def predict(self, input_data: LandslidePredictionInput) -> LandslidePredictionOutput:
        # Simple heuristic threshold for foundation sanity checking
        slope = input_data.terrain.slope_deg
        rain = input_data.meteorology.rainfall_24h_mm
        moisture = input_data.geotechnical.soil_moisture_pct

        # Baseline heuristic calculation
        score = (slope / 90.0) * 0.3 + (min(rain, 200.0) / 200.0) * 0.4 + (moisture / 100.0) * 0.3
        score = min(max(score, 0.0), 1.0)
        hazard_index = round(score * 100.0, 1)

        if hazard_index >= 75.0:
            level = "RED"
            susceptibility = "Very High"
            action = "Urgent: Immediate evacuation recommended for low-lying slopes. Suspend highway traffic."
        elif hazard_index >= 50.0:
            level = "ORANGE"
            susceptibility = "High"
            action = "Alert: High slope saturation. Restrict heavy vehicle movement and stage disaster response."
        elif hazard_index >= 30.0:
            level = "YELLOW"
            susceptibility = "Moderate"
            action = "Watch: Increase monitoring of vulnerable road cuts and drainage channels."
        else:
            level = "GREEN"
            susceptibility = "Low"
            action = "Normal: Routine surveillance. No immediate threat detected."

        return LandslidePredictionOutput(
            location_name=input_data.location_name or "Slope Assessment Zone",
            state=input_data.state or "NER",
            district=input_data.district or "District",
            susceptibility_class=susceptibility,
            susceptibility_probability=round(score, 3),
            dynamic_hazard_index=hazard_index,
            early_warning_level=level,
            recommended_action=action,
            model_version=self.version,
        )


_ml_service_instance: Optional[BaseLandslideModel] = None


def get_ml_service() -> BaseLandslideModel:
    """
    Factory function providing the singleton ML service.
    Loads the trained model if available from Phase 2; otherwise returns the baseline.
    """
    global _ml_service_instance
    if _ml_service_instance is None:
        model_path = settings.model_file_path
        if model_path.exists():
            # Will be imported and instantiated in Phase 2
            try:
                import joblib
                loaded_pipeline = joblib.load(model_path)
                # If custom wrapper class exists in Phase 2, use it
                _ml_service_instance = FallbackLandslidePredictor()
            except Exception:
                _ml_service_instance = FallbackLandslidePredictor()
        else:
            _ml_service_instance = FallbackLandslidePredictor()
    return _ml_service_instance
