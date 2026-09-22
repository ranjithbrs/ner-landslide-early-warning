"""
Phase 3 GIS Endpoints Test Suite.
Verifies that all GIS GeoJSON endpoints strictly follow OGC GeoJSON specifications
and serve real-time database and ML-evaluated attributes for Leaflet visualization.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.core.database import init_db
from backend.app.main import app


@pytest.fixture(autouse=True)
def ensure_db():
    init_db()


@pytest.fixture
def client():
    return TestClient(app)


def test_risk_zones_geojson_structure(client):
    """Verifies that /api/v1/risk/zones serves valid GeoJSON Polygons with ML scores."""
    res = client.get("/api/v1/risk/zones")
    assert res.status_code == 200
    data = res.json()

    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) >= 8

    for f in data["features"]:
        assert f["type"] == "Feature"
        assert f["geometry"]["type"] == "Polygon"
        assert len(f["geometry"]["coordinates"][0]) >= 4  # Closed polygon
        props = f["properties"]
        assert "zone_id" in props
        assert "name" in props
        assert "state" in props
        assert props["susceptibility_class"] in ["Very Low", "Low", "Moderate", "High", "Very High"]
        assert 0.0 <= props["dynamic_hazard_index"] <= 100.0
        assert props["early_warning_level"] in ["GREEN", "YELLOW", "ORANGE", "RED"]
        assert len(props["recommended_action"]) > 0


def test_road_corridors_geojson_structure(client):
    """Verifies that /api/v1/roads/geojson serves valid LineStrings for critical highways."""
    res = client.get("/api/v1/roads/geojson")
    assert res.status_code == 200
    data = res.json()

    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) >= 8

    codes = [f["properties"]["corridor_code"] for f in data["features"]]
    assert "NH-10" in codes
    assert "NH-29" in codes
    assert "NH-6" in codes
    assert "NH-27" in codes

    for f in data["features"]:
        assert f["geometry"]["type"] == "LineString"
        assert len(f["geometry"]["coordinates"]) >= 2
        assert f["properties"]["status"] in ["open", "single_lane", "blocked", "risky"]


def test_sensors_geojson_structure(client):
    """Verifies that /api/v1/sensors/geojson serves valid Point features with telemetry."""
    res = client.get("/api/v1/sensors/geojson")
    assert res.status_code == 200
    data = res.json()

    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) >= 8

    for f in data["features"]:
        assert f["geometry"]["type"] == "Point"
        coords = f["geometry"]["coordinates"]
        assert len(coords) == 2
        # Check Longitude/Latitude bounds for NER
        assert 88.0 <= coords[0] <= 97.0
        assert 21.0 <= coords[1] <= 30.0
        props = f["properties"]
        assert 0.0 <= props["soil_moisture_pct"] <= 100.0
        assert props["rainfall_1h_mm"] >= 0.0


def test_reports_geojson_structure(client):
    """Verifies that /api/v1/reports/geojson serves valid crowdsourced hazard points."""
    res = client.get("/api/v1/reports/geojson")
    assert res.status_code == 200
    data = res.json()

    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) >= 1

    for f in data["features"]:
        assert f["geometry"]["type"] == "Point"
        props = f["properties"]
        assert "incident_type" in props
        assert "severity" in props
        assert "description" in props


def test_risk_summary_endpoint(client):
    """Verifies that /api/v1/risk/summary aggregates regional statistics properly."""
    res = client.get("/api/v1/risk/summary")
    assert res.status_code == 200
    summary = res.json()

    assert summary["total_monitored_zones"] >= 8
    assert len(summary["states_monitored"]) == 8
    assert "warning_breakdown" in summary
    assert "highest_risk_zone" in summary
    assert summary["highest_risk_zone"]["hazard_index"] >= 0.0
