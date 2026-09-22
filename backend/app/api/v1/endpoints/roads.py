"""
Road Network & Corridor Status Endpoints.
Serves road blockage statuses and GeoJSON line geometry for the interactive GIS map.
"""

import sqlite3
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.app.core.database import get_db
from backend.app.models.schemas import RoadCorridorResponse

router = APIRouter()

# Approximate GeoJSON LineString coordinates for primary NER mountain corridors
CORRIDOR_GEOMETRIES: Dict[str, List[List[float]]] = {
    # NH-10: Sevoke to Gangtok (along Teesta river gorge)
    "NH-10": [
        [88.4715, 26.8835],  # Sevoke
        [88.4682, 26.9642],  # Coronation Bridge
        [88.5120, 27.0580],  # Teesta Bazaar
        [88.5250, 27.1520],  # Rangpo Border
        [88.5520, 27.2340],  # Singtam
        [88.6138, 27.3314],  # Gangtok
    ],
    # NH-29: Dimapur to Kohima
    "NH-29": [
        [93.7266, 25.9044],  # Dimapur
        [93.8540, 25.8210],  # Chumukedima
        [93.9850, 25.7420],  # Medziphema
        [94.0620, 25.6980],  # Zubza
        [94.1106, 25.6751],  # Kohima
    ],
    # NH-6: Jorabat to Shillong
    "NH-6": [
        [91.8740, 26.1120],  # Jorabat
        [91.8920, 25.9230],  # Nongpoh
        [91.8933, 25.6820],  # Umiam Lake
        [91.8933, 25.5788],  # Shillong
    ],
    # NH-27: Lumding to Haflong to Silchar (Dima Hasao hill section)
    "NH-27": [
        [93.1700, 25.7500],  # Lumding
        [93.0800, 25.4200],  # Maibang
        [93.0200, 25.1700],  # Haflong
        [92.8600, 24.9600],  # Jatinga Valley
        [92.7900, 24.8300],  # Silchar
    ],
    # NH-102: Imphal to Moreh (Manipur Indo-Myanmar corridor)
    "NH-102": [
        [93.9368, 24.8170],  # Imphal
        [93.9720, 24.6210],  # Thoubal
        [94.0210, 24.4320],  # Kakching
        [94.1820, 24.3120],  # Tengnoupal
        [94.3012, 24.2482],  # Moreh
    ],
    # NH-13: Bhalukpong to Bomdila to Tawang (Arunachal Pradesh)
    "NH-13": [
        [92.6500, 27.0100],  # Bhalukpong
        [92.5100, 27.1800],  # Tenga Valley
        [92.4200, 27.2600],  # Bomdila
        [92.1200, 27.5100],  # Sela Pass
        [91.8600, 27.5800],  # Tawang
    ],
    # NH-2: Aizawl to Lunglei (Mizoram)
    "NH-2": [
        [92.7176, 23.7307],  # Aizawl
        [92.7540, 23.5120],  # Hmuifang
        [92.7680, 23.2140],  # Thenzawl
        [92.7380, 22.8830],  # Lunglei
    ],
    # NH-8: Agartala to Sabroom (Tripura)
    "NH-8": [
        [91.2868, 23.8315],  # Agartala
        [91.4120, 23.5340],  # Udaipur
        [91.4920, 23.3420],  # Santirbazar
        [91.7320, 23.0010],  # Sabroom
    ],
}


@router.get("/", response_model=List[RoadCorridorResponse], summary="List Road Corridors and Connectivity Status")
def list_road_corridors(db: sqlite3.Connection = Depends(get_db)):
    """Queries all monitored mountain highway corridors."""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM road_corridors ORDER BY corridor_code ASC")
    rows = cursor.fetchall()

    return [
        RoadCorridorResponse(
            id=row["id"],
            corridor_code=row["corridor_code"],
            name=row["name"],
            state=row["state"],
            start_point=row["start_point"],
            end_point=row["end_point"],
            status=row["status"],
            risk_level=row["risk_level"],
            last_updated=str(row["last_updated"]),
        )
        for row in rows
    ]


@router.get("/geojson", summary="Get Road Corridors as GeoJSON LineStrings for Leaflet")
def get_road_corridors_geojson(db: sqlite3.Connection = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns critical highway corridors as a GeoJSON FeatureCollection
    styled with current connectivity status and risk ratings.
    """
    cursor = db.cursor()
    cursor.execute("SELECT * FROM road_corridors")
    rows = cursor.fetchall()
    row_dict = {row["corridor_code"]: dict(row) for row in rows}

    features = []
    for code, coords in CORRIDOR_GEOMETRIES.items():
        info = row_dict.get(code, {})
        status = info.get("status", "open")
        risk_level = info.get("risk_level", "LOW")

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": coords,
            },
            "properties": {
                "corridor_code": code,
                "name": info.get("name", code),
                "state": info.get("state", "NER"),
                "start_point": info.get("start_point", ""),
                "end_point": info.get("end_point", ""),
                "status": status,
                "risk_level": risk_level,
                "detour_available": status in ["blocked", "single_lane"],
                "last_updated": str(info.get("last_updated", "")),
            },
        })

    return {
        "type": "FeatureCollection",
        "features": features,
    }
