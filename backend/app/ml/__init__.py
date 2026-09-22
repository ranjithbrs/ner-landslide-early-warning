"""
Machine Learning service package for Landslide Risk and Early Warning.
"""
from backend.app.ml.schemas import (
    TerrainFeatures,
    MeteorologicalFeatures,
    GeotechnicalFeatures,
    LandslidePredictionInput,
    LandslidePredictionOutput,
)
from backend.app.ml.interface import BaseLandslideModel, get_ml_service

__all__ = [
    "TerrainFeatures",
    "MeteorologicalFeatures",
    "GeotechnicalFeatures",
    "LandslidePredictionInput",
    "LandslidePredictionOutput",
    "BaseLandslideModel",
    "get_ml_service",
]
