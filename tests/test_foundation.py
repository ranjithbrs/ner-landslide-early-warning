"""
Phase 1 Foundation Test Suite.
Verifies backend setup, database initialization, ML schemas and interfaces,
and API endpoint contracts.
"""

import sqlite3
import pytest
from fastapi.testclient import TestClient
from backend.app.core.config import settings
from backend.app.core.database import init_db, get_db_connection
from backend.app.main import app
from backend.app.ml.schemas import (
    TerrainFeatures,
    MeteorologicalFeatures,
    GeotechnicalFeatures,
    LandslidePredictionInput,
)
from backend.app.ml.interface import get_ml_service, FallbackLandslidePredictor


@pytest.fixture(autouse=True)
def setup_test_db():
    """Ensure database schema is initialized before every test."""
    init_db()


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


def test_settings_loaded():
    """Verifies that configuration settings are loaded with correct types."""
    assert settings.PROJECT_NAME is not None
    assert settings.API_V1_STR == "/api/v1"
    assert settings.PORT == 8000
    assert settings.RAINFALL_YELLOW_THRESHOLD_MM > 0.0


def test_database_tables_exist():
    """Verifies that SQLite schema initialization creates all foundation tables."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row["name"] for row in cursor.fetchall()]

        assert "sensor_readings" in tables
        assert "incident_reports" in tables
        assert "alert_logs" in tables
        assert "road_corridors" in tables


def test_health_check_endpoint(client):
    """Verifies that GET /api/v1/health returns 200 with operational components."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "operational"
    assert "baseline" in data["ml_service_status"] or "loaded" in data["ml_service_status"]


def test_ml_schemas_and_fallback_predictor():
    """Verifies input validation and fallback predictor contract."""
    sample_input = LandslidePredictionInput(
        location_name="Kalimpong Slope NH-10",
        state="Sikkim",
        district="Pakyong",
        latitude=27.12,
        longitude=88.51,
        terrain=TerrainFeatures(
            elevation_m=1250.0,
            slope_deg=42.5,
            aspect_deg=180.0,
            profile_curvature=-0.03,
            plan_curvature=0.02,
            topographic_wetness_index=7.5,
            dist_to_fault_m=350.0,
            dist_to_drainage_m=120.0,
            lithology_code=4,
            lulc_code=3,
        ),
        meteorology=MeteorologicalFeatures(
            rainfall_24h_mm=85.0,
            rainfall_72h_antecedent_mm=160.0,
            rainfall_intensity_mm_h=25.0,
        ),
        geotechnical=GeotechnicalFeatures(
            soil_moisture_pct=82.0,
            pore_water_pressure_kpa=18.5,
            tilt_rate_mm_h=2.1,
        ),
    )

    # Verify direct FallbackLandslidePredictor contract
    fallback_service = FallbackLandslidePredictor()
    assert fallback_service.is_calibrated is False
    assert fallback_service.version == "phase-1-uncalibrated-baseline"

    prediction = fallback_service.predict(sample_input)
    assert prediction.location_name == "Kalimpong Slope NH-10"
    assert prediction.early_warning_level in ["GREEN", "YELLOW", "ORANGE", "RED"]
    assert 0.0 <= prediction.susceptibility_probability <= 1.0
    assert 0.0 <= prediction.dynamic_hazard_index <= 100.0

    # Also verify that get_ml_service() returns a valid BaseLandslideModel instance
    active_service = get_ml_service()
    assert active_service is not None
    assert hasattr(active_service, "predict")


def test_incident_reporting_workflow(client):
    """Verifies full cycle: submitting an incident report and querying it."""
    payload = {
        "reporter_name": "Test Inspector",
        "contact_number": "+91 9999999999",
        "latitude": 25.68,
        "longitude": 91.91,
        "state": "Meghalaya",
        "district": "Ri Bhoi",
        "incident_type": "Tension Crack",
        "severity": "High",
        "description": "50-meter lateral ground crack across hillside road",
        "sync_status": "synced",
    }

    # 1. Submit
    create_res = client.post("/api/v1/reports/", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["id"] is not None
    assert created_data["reporter_name"] == "Test Inspector"

    # 2. Query
    list_res = client.get("/api/v1/reports/?state=Meghalaya")
    assert list_res.status_code == 200
    reports = list_res.json()
    assert any(r["id"] == created_data["id"] for r in reports)


def test_sensor_telemetry_workflow(client):
    """Verifies inserting a sensor telemetry record and reading latest readings."""
    sensor_payload = {
        "station_id": "ST-TEST-01",
        "station_name": "Haflong Hill Cut Station",
        "state": "Assam",
        "district": "Dima Hasao",
        "latitude": 25.17,
        "longitude": 93.02,
        "soil_moisture_pct": 74.5,
        "pore_pressure_kpa": 12.3,
        "rainfall_1h_mm": 15.0,
        "tilt_displacement_mm": 1.4,
        "battery_pct": 98.0,
    }

    post_res = client.post("/api/v1/sensors/readings", json=sensor_payload)
    assert post_res.status_code == 201
    reading = post_res.json()
    assert reading["station_id"] == "ST-TEST-01"

    latest_res = client.get("/api/v1/sensors/latest")
    assert latest_res.status_code == 200
    latest_readings = latest_res.json()
    assert any(s["station_id"] == "ST-TEST-01" for s in latest_readings)


def test_frontend_static_serving(client):
    """Verifies that the root URL serves the frontend index.html."""
    res = client.get("/")
    assert res.status_code == 200
    assert "NER Landslide Early Warning" in res.text
