"""
Landslide Risk and Early Warning prediction and GIS GeoJSON endpoints.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from backend.app.ml.interface import get_ml_service, BaseLandslideModel
from backend.app.ml.schemas import (
    TerrainFeatures,
    MeteorologicalFeatures,
    GeotechnicalFeatures,
    LandslidePredictionInput,
    LandslidePredictionOutput,
)

router = APIRouter()

# Representative spatial polygons for high-vulnerability hill slopes across NER
# Each polygon represents a monitored critical slope catchment
NER_MONITORED_SLOPE_ZONES = [
    {
        "zone_id": "ZONE-SKM-01",
        "name": "NH-10 Teesta Gorge Slope Section",
        "state": "Sikkim",
        "district": "Pakyong",
        "center": [88.5200, 27.1500],
        # Coordinates: [lon, lat] closed polygon
        "polygon": [
            [88.4900, 27.1300],
            [88.5400, 27.1300],
            [88.5500, 27.1700],
            [88.5000, 27.1700],
            [88.4900, 27.1300],
        ],
        "terrain": {"elevation_m": 1100, "slope_deg": 44.0, "aspect_deg": 195.0, "profile_curvature": -0.04, "plan_curvature": 0.03, "topographic_wetness_index": 10.5, "dist_to_fault_m": 250, "dist_to_drainage_m": 60, "lithology_code": 4, "lulc_code": 3},
        "weather": {"rainfall_24h_mm": 115.0, "rainfall_72h_antecedent_mm": 240.0, "rainfall_intensity_mm_h": 28.0},
        "sensor": {"soil_moisture_pct": 89.0, "pore_water_pressure_kpa": 22.0, "tilt_rate_mm_h": 2.4},
        "vulnerability_notes": "Chronic slump area along Teesta riverbank; NH-10 single-lane operation.",
    },
    {
        "zone_id": "ZONE-ASM-01",
        "name": "Lumding-Haflong Railway & Road Cut",
        "state": "Assam",
        "district": "Dima Hasao",
        "center": [93.0200, 25.1700],
        "polygon": [
            [92.9900, 25.1400],
            [93.0500, 25.1400],
            [93.0600, 25.2000],
            [93.0000, 25.2000],
            [92.9900, 25.1400],
        ],
        "terrain": {"elevation_m": 780, "slope_deg": 38.0, "aspect_deg": 180.0, "profile_curvature": -0.03, "plan_curvature": 0.02, "topographic_wetness_index": 9.8, "dist_to_fault_m": 450, "dist_to_drainage_m": 120, "lithology_code": 2, "lulc_code": 3},
        "weather": {"rainfall_24h_mm": 130.0, "rainfall_72h_antecedent_mm": 275.0, "rainfall_intensity_mm_h": 32.0},
        "sensor": {"soil_moisture_pct": 92.5, "pore_water_pressure_kpa": 25.0, "tilt_rate_mm_h": 3.1},
        "vulnerability_notes": "Fragile Tertiary shale-sandstone sequence; highway currently blocked by debris.",
    },
    {
        "zone_id": "ZONE-NGL-01",
        "name": "Kohima By-pass Phesama Slope",
        "state": "Nagaland",
        "district": "Kohima",
        "center": [94.1100, 25.6700],
        "polygon": [
            [94.0800, 25.6400],
            [94.1400, 25.6400],
            [94.1500, 25.7000],
            [94.0900, 25.7000],
            [94.0800, 25.6400],
        ],
        "terrain": {"elevation_m": 1450, "slope_deg": 34.0, "aspect_deg": 210.0, "profile_curvature": -0.01, "plan_curvature": 0.01, "topographic_wetness_index": 7.5, "dist_to_fault_m": 600, "dist_to_drainage_m": 190, "lithology_code": 3, "lulc_code": 2},
        "weather": {"rainfall_24h_mm": 55.0, "rainfall_72h_antecedent_mm": 95.0, "rainfall_intensity_mm_h": 14.0},
        "sensor": {"soil_moisture_pct": 74.0, "pore_water_pressure_kpa": 12.5, "tilt_rate_mm_h": 0.7},
        "vulnerability_notes": "Disal Sinking Zone on NH-29; slow creep observed.",
    },
    {
        "zone_id": "ZONE-MEG-01",
        "name": "Shillong Escarpment & Umiam Slopes",
        "state": "Meghalaya",
        "district": "East Khasi Hills",
        "center": [91.8900, 25.5800],
        "polygon": [
            [91.8600, 25.5500],
            [91.9300, 25.5500],
            [91.9400, 25.6100],
            [91.8700, 25.6100],
            [91.8600, 25.5500],
        ],
        "terrain": {"elevation_m": 1520, "slope_deg": 31.0, "aspect_deg": 160.0, "profile_curvature": 0.0, "plan_curvature": 0.0, "topographic_wetness_index": 8.0, "dist_to_fault_m": 800, "dist_to_drainage_m": 220, "lithology_code": 2, "lulc_code": 2},
        "weather": {"rainfall_24h_mm": 68.0, "rainfall_72h_antecedent_mm": 130.0, "rainfall_intensity_mm_h": 16.0},
        "sensor": {"soil_moisture_pct": 77.5, "pore_water_pressure_kpa": 14.0, "tilt_rate_mm_h": 0.8},
        "vulnerability_notes": "Heavy orographic rainfall area along Shillong plateau edge.",
    },
    {
        "zone_id": "ZONE-ARN-01",
        "name": "Bhalukpong-Bomdila Mountain Pass",
        "state": "Arunachal Pradesh",
        "district": "West Kameng",
        "center": [92.4200, 27.2600],
        "polygon": [
            [92.3800, 27.2200],
            [92.4600, 27.2200],
            [92.4700, 27.3000],
            [92.3900, 27.3000],
            [92.3800, 27.2200],
        ],
        "terrain": {"elevation_m": 2250, "slope_deg": 41.0, "aspect_deg": 140.0, "profile_curvature": -0.02, "plan_curvature": 0.02, "topographic_wetness_index": 6.8, "dist_to_fault_m": 350, "dist_to_drainage_m": 110, "lithology_code": 5, "lulc_code": 1},
        "weather": {"rainfall_24h_mm": 42.0, "rainfall_72h_antecedent_mm": 80.0, "rainfall_intensity_mm_h": 10.0},
        "sensor": {"soil_moisture_pct": 66.0, "pore_water_pressure_kpa": 9.5, "tilt_rate_mm_h": 0.3},
        "vulnerability_notes": "High relief steep Himalayan terrain; military & civilian lifeline route.",
    },
    {
        "zone_id": "ZONE-MNP-01",
        "name": "Tupul-Noney Railway Incline Cut",
        "state": "Manipur",
        "district": "Noney",
        "center": [93.6500, 24.7800],
        "polygon": [
            [93.6200, 24.7500],
            [93.6900, 24.7500],
            [93.7000, 24.8200],
            [93.6300, 24.8200],
            [93.6200, 24.7500],
        ],
        "terrain": {"elevation_m": 850, "slope_deg": 42.0, "aspect_deg": 175.0, "profile_curvature": -0.04, "plan_curvature": 0.03, "topographic_wetness_index": 9.2, "dist_to_fault_m": 310, "dist_to_drainage_m": 80, "lithology_code": 3, "lulc_code": 3},
        "weather": {"rainfall_24h_mm": 95.0, "rainfall_72h_antecedent_mm": 190.0, "rainfall_intensity_mm_h": 24.0},
        "sensor": {"soil_moisture_pct": 83.5, "pore_water_pressure_kpa": 18.0, "tilt_rate_mm_h": 1.4},
        "vulnerability_notes": "Historic 2022 Tupul debris flow zone; active engineering monitoring.",
    },
    {
        "zone_id": "ZONE-MIZ-01",
        "name": "Champhai Ridge Border Corridor",
        "state": "Mizoram",
        "district": "Champhai",
        "center": [93.3200, 23.4700],
        "polygon": [
            [93.2800, 23.4300],
            [93.3600, 23.4300],
            [93.3700, 23.5100],
            [93.2900, 23.5100],
            [93.2800, 23.4300],
        ],
        "terrain": {"elevation_m": 1380, "slope_deg": 32.0, "aspect_deg": 220.0, "profile_curvature": -0.01, "plan_curvature": 0.01, "topographic_wetness_index": 6.5, "dist_to_fault_m": 900, "dist_to_drainage_m": 310, "lithology_code": 2, "lulc_code": 2},
        "weather": {"rainfall_24h_mm": 35.0, "rainfall_72h_antecedent_mm": 60.0, "rainfall_intensity_mm_h": 8.0},
        "sensor": {"soil_moisture_pct": 64.0, "pore_water_pressure_kpa": 8.0, "tilt_rate_mm_h": 0.2},
        "vulnerability_notes": "Anticlinal ridge topography; prone to shallow translational slides.",
    },
    {
        "zone_id": "ZONE-TRP-01",
        "name": "Jampui Hills Hillside Section",
        "state": "Tripura",
        "district": "North Tripura",
        "center": [92.2700, 23.9500],
        "polygon": [
            [92.2400, 23.9200],
            [92.3000, 23.9200],
            [92.3100, 23.9800],
            [92.2500, 23.9800],
            [92.2400, 23.9200],
        ],
        "terrain": {"elevation_m": 680, "slope_deg": 26.0, "aspect_deg": 120.0, "profile_curvature": 0.0, "plan_curvature": 0.0, "topographic_wetness_index": 6.0, "dist_to_fault_m": 1400, "dist_to_drainage_m": 450, "lithology_code": 1, "lulc_code": 1},
        "weather": {"rainfall_24h_mm": 18.0, "rainfall_72h_antecedent_mm": 35.0, "rainfall_intensity_mm_h": 4.0},
        "sensor": {"soil_moisture_pct": 52.0, "pore_water_pressure_kpa": 4.5, "tilt_rate_mm_h": 0.05},
        "vulnerability_notes": "Highest elevation zone in Tripura; moderate stability under current weather.",
    },
]


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


@router.get("/zones", summary="Get Monitored Landslide Risk Zones as GeoJSON for Leaflet GIS")
def get_risk_zones_geojson(
    ml_service: BaseLandslideModel = Depends(get_ml_service),
) -> Dict[str, Any]:
    """
    Returns spatial GeoJSON Polygons for all monitored NER hill slope catchments.
    Every zone includes dynamically evaluated ML predictions and early warning status.
    """
    features = []

    for z in NER_MONITORED_SLOPE_ZONES:
        # Build prediction input dynamically
        pred_input = LandslidePredictionInput(
            location_name=z["name"],
            state=z["state"],
            district=z["district"],
            latitude=z["center"][1],
            longitude=z["center"][0],
            terrain=TerrainFeatures(**z["terrain"]),
            meteorology=MeteorologicalFeatures(**z["weather"]),
            geotechnical=GeotechnicalFeatures(**z["sensor"]),
        )
        prediction = ml_service.predict(pred_input)

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [z["polygon"]],
            },
            "properties": {
                "zone_id": z["zone_id"],
                "name": z["name"],
                "state": z["state"],
                "district": z["district"],
                "center": z["center"],
                "susceptibility_class": prediction.susceptibility_class,
                "susceptibility_probability": prediction.susceptibility_probability,
                "dynamic_hazard_index": prediction.dynamic_hazard_index,
                "early_warning_level": prediction.early_warning_level,
                "recommended_action": prediction.recommended_action,
                "slope_deg": z["terrain"]["slope_deg"],
                "rainfall_24h_mm": z["weather"]["rainfall_24h_mm"],
                "rainfall_72h_mm": z["weather"]["rainfall_72h_antecedent_mm"],
                "soil_moisture_pct": z["sensor"]["soil_moisture_pct"],
                "pore_water_pressure_kpa": z["sensor"]["pore_water_pressure_kpa"],
                "tilt_rate_mm_h": z["sensor"]["tilt_rate_mm_h"],
                "vulnerability_notes": z["vulnerability_notes"],
                "model_version": prediction.model_version,
            },
        })

    return {
        "type": "FeatureCollection",
        "features": features,
    }


@router.get("/summary", summary="Regional Landslide Risk Summary across NER States")
def get_regional_summary(
    ml_service: BaseLandslideModel = Depends(get_ml_service),
) -> Dict[str, Any]:
    """
    Aggregates live risk assessments across all monitored NER zones.
    """
    zones_geojson = get_risk_zones_geojson(ml_service)
    features = zones_geojson["features"]

    severity_counts = {"GREEN": 0, "YELLOW": 0, "ORANGE": 0, "RED": 0}
    highest_zone = None
    max_hazard = -1.0

    for f in features:
        props = f["properties"]
        level = props["early_warning_level"]
        severity_counts[level] = severity_counts.get(level, 0) + 1

        if props["dynamic_hazard_index"] > max_hazard:
            max_hazard = props["dynamic_hazard_index"]
            highest_zone = {
                "zone_id": props["zone_id"],
                "name": props["name"],
                "state": props["state"],
                "district": props["district"],
                "hazard_index": props["dynamic_hazard_index"],
                "warning_level": props["early_warning_level"],
            }

    return {
        "region": "North Eastern Region (NER)",
        "total_monitored_zones": len(features),
        "states_monitored": [
            "Arunachal Pradesh",
            "Assam",
            "Manipur",
            "Meghalaya",
            "Mizoram",
            "Nagaland",
            "Sikkim",
            "Tripura",
        ],
        "warning_breakdown": severity_counts,
        "highest_risk_zone": highest_zone,
        "active_alerts_count": severity_counts["RED"] + severity_counts["ORANGE"],
        "model_in_use": ml_service.version,
    }
