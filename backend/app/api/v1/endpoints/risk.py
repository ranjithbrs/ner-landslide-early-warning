"""
Landslide Risk and Early Warning prediction endpoints.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from backend.app.ml.interface import get_ml_service, BaseLandslideModel
from backend.app.ml.schemas import (
    LandslidePredictionInput,
    LandslidePredictionOutput,
)

router = APIRouter()


@router.post("/predict", response_model=LandslidePredictionOutput, summary="Calculate Landslide Risk & Warning Level")
def predict_landslide_risk(
    payload: LandslidePredictionInput,
    ml_service: BaseLandslideModel = Depends(get_ml_service),
):
    """
    Evaluates terrain, meteorological, and geotechnical variables
    to produce spatial susceptibility class and dynamic early warning stage.
    """
    try:
        return ml_service.predict(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction evaluation failed: {str(e)}")


@router.get("/summary", summary="Regional Landslide Risk Summary across NER States")
def get_regional_summary():
    """
    Returns regional monitoring summary.
    Serves as an architectural foundation for the live GIS dashboard.
    """
    return {
        "region": "North Eastern Region (NER)",
        "monitored_states": [
            "Arunachal Pradesh",
            "Assam",
            "Manipur",
            "Meghalaya",
            "Mizoram",
            "Nagaland",
            "Sikkim",
            "Tripura",
        ],
        "active_corridors_count": 8,
        "critical_alert_count": 0,
        "status": "Foundation Ready",
    }
