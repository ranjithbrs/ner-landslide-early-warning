"""
Sensor telemetry ingestion and querying endpoints.
"""

import sqlite3
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from backend.app.core.database import get_db
from backend.app.models.schemas import SensorReadingCreate, SensorReadingResponse

router = APIRouter()


@router.post("/readings", response_model=SensorReadingResponse, status_code=201, summary="Ingest IoT Sensor Telemetry")
def ingest_sensor_reading(payload: SensorReadingCreate, db: sqlite3.Connection = Depends(get_db)):
    """Records a single telemetry packet from ground monitoring sensors."""
    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO sensor_readings (
            station_id, station_name, state, district, latitude, longitude,
            soil_moisture_pct, pore_pressure_kpa, rainfall_1h_mm, tilt_displacement_mm, battery_pct
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload.station_id,
            payload.station_name,
            payload.state,
            payload.district,
            payload.latitude,
            payload.longitude,
            payload.soil_moisture_pct,
            payload.pore_pressure_kpa,
            payload.rainfall_1h_mm,
            payload.tilt_displacement_mm,
            payload.battery_pct,
        ),
    )
    reading_id = cursor.lastrowid
    cursor.execute("SELECT * FROM sensor_readings WHERE id = ?", (reading_id,))
    row = cursor.fetchone()

    return SensorReadingResponse(
        id=row["id"],
        station_id=row["station_id"],
        station_name=row["station_name"],
        state=row["state"],
        district=row["district"],
        latitude=row["latitude"],
        longitude=row["longitude"],
        soil_moisture_pct=row["soil_moisture_pct"],
        pore_pressure_kpa=row["pore_pressure_kpa"],
        rainfall_1h_mm=row["rainfall_1h_mm"],
        tilt_displacement_mm=row["tilt_displacement_mm"],
        battery_pct=row["battery_pct"],
        recorded_at=str(row["recorded_at"]),
    )


@router.get("/latest", response_model=List[SensorReadingResponse], summary="Get Latest Readings from All Stations")
def get_latest_sensor_readings(db: sqlite3.Connection = Depends(get_db)):
    """Queries the most recent sensor reading per station."""
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT * FROM sensor_readings
        WHERE id IN (
            SELECT MAX(id) FROM sensor_readings GROUP BY station_id
        )
        ORDER BY recorded_at DESC
        """
    )
    rows = cursor.fetchall()
    results = []
    for row in rows:
        results.append(
            SensorReadingResponse(
                id=row["id"],
                station_id=row["station_id"],
                station_name=row["station_name"],
                state=row["state"],
                district=row["district"],
                latitude=row["latitude"],
                longitude=row["longitude"],
                soil_moisture_pct=row["soil_moisture_pct"],
                pore_pressure_kpa=row["pore_pressure_kpa"],
                rainfall_1h_mm=row["rainfall_1h_mm"],
                tilt_displacement_mm=row["tilt_displacement_mm"],
                battery_pct=row["battery_pct"],
                recorded_at=str(row["recorded_at"]),
            )
        )
    return results
