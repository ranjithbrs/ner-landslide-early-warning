"""
Phase 2 Machine Learning Test Suite.
Verifies dataset generation, preprocessing hygiene, model performance metrics,
prediction service behavior across edge scenarios, and REST API integration.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.ml.interface import get_ml_service, BaseLandslideModel
from backend.app.ml.schemas import (
    TerrainFeatures,
    MeteorologicalFeatures,
    GeotechnicalFeatures,
    LandslidePredictionInput,
)
from backend.ml_engine.synthetic_generator import generate_synthetic_ner_dataset
from backend.ml_engine.pipeline import (
    build_preprocessor,
    extract_feature_matrix,
    ALL_MODEL_FEATURES,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_synthetic_dataset_properties():
    """Verifies that the prototype dataset adheres to physical bounds and schema requirements."""
    df = generate_synthetic_ner_dataset(n_samples=500, random_seed=99)

    # 1. Shape and null checks
    assert len(df) == 500
    assert df.isnull().sum().sum() == 0, "Synthetic dataset must contain zero NULL or NaN values"

    # 2. Physics bounds
    assert df["slope_deg"].between(0.0, 90.0).all()
    assert df["soil_moisture_pct"].between(0.0, 100.0).all()
    assert (df["rainfall_24h_mm"] >= 0.0).all()
    assert (df["elevation_m"] > 0.0).all()
    assert set(df["landslide_occurred"].unique()).issubset({0, 1})

    # 3. Positive class representation
    positive_ratio = df["landslide_occurred"].mean()
    assert 0.15 <= positive_ratio <= 0.40, f"Positive class ratio {positive_ratio} out of expected range"


def test_preprocessing_pipeline_fit_transform():
    """Verifies that the preprocessing ColumnTransformer scales and encodes correctly."""
    df = generate_synthetic_ner_dataset(n_samples=200, random_seed=12)
    X, y = extract_feature_matrix(df)

    preprocessor = build_preprocessor()
    X_transformed = preprocessor.fit_transform(X)

    assert X_transformed.shape[0] == 200
    assert X_transformed.shape[1] >= len(ALL_MODEL_FEATURES)
    assert not (X_transformed == float("nan")).any()


def test_trained_model_loading_and_metrics():
    """Verifies that saved artifacts exist and model performance exceeds required benchmarks."""
    ml_service = get_ml_service()
    assert ml_service.is_calibrated is True
    assert "random-forest" in ml_service.version

    # Verify metadata metrics
    metadata_file = Path("backend/ml_engine/models/model_metadata.json")
    assert metadata_file.exists()

    import json
    with open(metadata_file, "r") as f:
        meta = json.load(f)

    rf_metrics = meta["model_comparison"]["random_forest"]
    assert rf_metrics["roc_auc"] >= 0.90, f"Expected ROC-AUC >= 0.90, got {rf_metrics['roc_auc']}"
    assert rf_metrics["f1_score"] >= 0.85, f"Expected F1 >= 0.85, got {rf_metrics['f1_score']}"
    assert rf_metrics["recall"] >= 0.90, f"Expected Recall >= 0.90, got {rf_metrics['recall']}"


def test_prediction_service_high_risk_scenario():
    """Verifies that an extreme monsoon storm on steep cut slope triggers high hazard / RED alert."""
    high_risk_input = LandslidePredictionInput(
        location_name="NH-10 Teesta Valley Mile 9",
        state="Sikkim",
        district="Pakyong",
        latitude=27.15,
        longitude=88.52,
        terrain=TerrainFeatures(
            elevation_m=1100.0,
            slope_deg=48.0,
            aspect_deg=190.0,
            profile_curvature=-0.04,
            plan_curvature=0.03,
            topographic_wetness_index=11.0,
            dist_to_fault_m=200.0,
            dist_to_drainage_m=80.0,
            lithology_code=4,
            lulc_code=3,  # Road Cut
        ),
        meteorology=MeteorologicalFeatures(
            rainfall_24h_mm=135.0,
            rainfall_72h_antecedent_mm=280.0,
            rainfall_intensity_mm_h=38.0,
        ),
        geotechnical=GeotechnicalFeatures(
            soil_moisture_pct=94.0,
            pore_water_pressure_kpa=26.5,
            tilt_rate_mm_h=3.8,
        ),
    )

    ml_service = get_ml_service()
    result = ml_service.predict(high_risk_input)

    assert result.susceptibility_class in ["High", "Very High"]
    assert result.susceptibility_probability >= 0.70
    assert result.dynamic_hazard_index >= 70.0
    assert result.early_warning_level in ["ORANGE", "RED"]
    assert "evacuation" in result.recommended_action.lower() or "traffic" in result.recommended_action.lower()


def test_prediction_service_low_risk_scenario():
    """Verifies that a gentle, forested slope during dry conditions triggers GREEN / normal."""
    low_risk_input = LandslidePredictionInput(
        location_name="Diphu Lowland Reserve",
        state="Assam",
        district="Karbi Anglong",
        latitude=25.84,
        longitude=93.43,
        terrain=TerrainFeatures(
            elevation_m=320.0,
            slope_deg=10.0,
            aspect_deg=90.0,
            profile_curvature=0.0,
            plan_curvature=0.0,
            topographic_wetness_index=5.0,
            dist_to_fault_m=3500.0,
            dist_to_drainage_m=950.0,
            lithology_code=1,
            lulc_code=1,  # Dense Forest
        ),
        meteorology=MeteorologicalFeatures(
            rainfall_24h_mm=3.0,
            rainfall_72h_antecedent_mm=8.0,
            rainfall_intensity_mm_h=1.0,
        ),
        geotechnical=GeotechnicalFeatures(
            soil_moisture_pct=28.0,
            pore_water_pressure_kpa=1.0,
            tilt_rate_mm_h=0.0,
        ),
    )

    ml_service = get_ml_service()
    result = ml_service.predict(low_risk_input)

    assert result.susceptibility_class in ["Very Low", "Low"]
    assert result.susceptibility_probability < 0.35
    assert result.dynamic_hazard_index < 35.0
    assert result.early_warning_level == "GREEN"


def test_api_predict_endpoint_live(client):
    """Verifies that the live REST API /api/v1/risk/predict produces calibrated predictions."""
    payload = {
        "location_name": "Kohima By-pass Km 14",
        "state": "Nagaland",
        "district": "Kohima",
        "latitude": 25.67,
        "longitude": 94.11,
        "terrain": {
            "elevation_m": 1420.0,
            "slope_deg": 38.0,
            "aspect_deg": 210.0,
            "profile_curvature": -0.02,
            "plan_curvature": 0.01,
            "topographic_wetness_index": 8.0,
            "dist_to_fault_m": 550.0,
            "dist_to_drainage_m": 180.0,
            "lithology_code": 3,
            "lulc_code": 3,
        },
        "meteorology": {
            "rainfall_24h_mm": 65.0,
            "rainfall_72h_antecedent_mm": 110.0,
            "rainfall_intensity_mm_h": 15.0,
        },
        "geotechnical": {
            "soil_moisture_pct": 76.0,
            "pore_water_pressure_kpa": 12.0,
            "tilt_rate_mm_h": 0.8,
        },
    }

    res = client.post("/api/v1/risk/predict", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["location_name"] == "Kohima By-pass Km 14"
    assert "random-forest" in data["model_version"]
    assert 0.0 <= data["susceptibility_probability"] <= 1.0
    assert 0.0 <= data["dynamic_hazard_index"] <= 100.0
    assert data["early_warning_level"] in ["GREEN", "YELLOW", "ORANGE", "RED"]
    assert len(data["recommended_action"]) > 10
