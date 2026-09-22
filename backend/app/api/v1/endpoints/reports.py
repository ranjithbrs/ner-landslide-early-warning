"""
Citizen and Field Officer Crowdsourced Reporting Endpoints.
Supports online submissions and bulk sync for offline-first field devices.
"""

import sqlite3
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.app.core.database import get_db
from backend.app.models.schemas import IncidentReportCreate, IncidentReportResponse

router = APIRouter()


@router.post("/", response_model=IncidentReportResponse, status_code=201, summary="Submit Incident Report")
def submit_incident_report(payload: IncidentReportCreate, db: sqlite3.Connection = Depends(get_db)):
    """Logs a ground hazard report (cracks, debris flow, road blocked) from citizens or field teams."""
    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO incident_reports (
            reporter_name, contact_number, latitude, longitude, state, district,
            incident_type, severity, description, photo_url, sync_status, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        """,
        (
            payload.reporter_name,
            payload.contact_number,
            payload.latitude,
            payload.longitude,
            payload.state,
            payload.district,
            payload.incident_type,
            payload.severity,
            payload.description,
            payload.photo_url,
            payload.sync_status or "synced",
        ),
    )
    report_id = cursor.lastrowid
    cursor.execute("SELECT * FROM incident_reports WHERE id = ?", (report_id,))
    row = cursor.fetchone()

    return IncidentReportResponse(
        id=row["id"],
        reporter_name=row["reporter_name"],
        contact_number=row["contact_number"],
        latitude=row["latitude"],
        longitude=row["longitude"],
        state=row["state"],
        district=row["district"],
        incident_type=row["incident_type"],
        severity=row["severity"],
        description=row["description"],
        photo_url=row["photo_url"],
        sync_status=row["sync_status"],
        status=row["status"],
        created_at=str(row["created_at"]),
    )


def _fetch_reports(
    db: sqlite3.Connection,
    state: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> List[IncidentReportResponse]:
    cursor = db.cursor()
    query = "SELECT * FROM incident_reports WHERE 1=1"
    params = []

    if state:
        query += " AND state = ?"
        params.append(state)
    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()

    return [
        IncidentReportResponse(
            id=row["id"],
            reporter_name=row["reporter_name"],
            contact_number=row["contact_number"],
            latitude=row["latitude"],
            longitude=row["longitude"],
            state=row["state"],
            district=row["district"],
            incident_type=row["incident_type"],
            severity=row["severity"],
            description=row["description"],
            photo_url=row["photo_url"],
            sync_status=row["sync_status"],
            status=row["status"],
            created_at=str(row["created_at"]),
        )
        for row in rows
    ]


@router.get("/", response_model=List[IncidentReportResponse], summary="List Incident Reports")
def list_incident_reports(
    state: Optional[str] = Query(None, description="Filter by NER State"),
    status: Optional[str] = Query(None, description="Filter by status (pending, verified, etc.)"),
    limit: int = Query(50, ge=1, le=500),
    db: sqlite3.Connection = Depends(get_db),
):
    """Retrieves reported hazards for dashboard visualization and emergency response."""
    return _fetch_reports(db, state=state, status=status, limit=limit)


@router.post("/batch-sync", summary="Batch Sync Offline Queued Reports")
def batch_sync_reports(reports: List[IncidentReportCreate], db: sqlite3.Connection = Depends(get_db)):
    """Receives an array of reports buffered on field devices during network outage."""
    synced_count = 0
    for report in reports:
        report.sync_status = "synced_from_offline"
        submit_incident_report(report, db)
        synced_count += 1
    return {"status": "success", "synced_records": synced_count}


@router.get("/geojson", summary="Get Incidents as GeoJSON Points for Leaflet GIS")
def get_reports_geojson(db: sqlite3.Connection = Depends(get_db)):
    """Returns all recorded hazard incidents as GeoJSON Point features."""
    reports = _fetch_reports(db, limit=200)
    features = []
    for r in reports:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [r.longitude, r.latitude],
            },
            "properties": {
                "id": r.id,
                "reporter_name": r.reporter_name,
                "contact_number": r.contact_number,
                "state": r.state,
                "district": r.district,
                "incident_type": r.incident_type,
                "severity": r.severity,
                "description": r.description,
                "status": r.status,
                "created_at": r.created_at,
            },
        })
    return {
        "type": "FeatureCollection",
        "features": features,
    }
