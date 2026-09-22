"""
Emergency Alert and Warning notification endpoints.
"""

import sqlite3
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from backend.app.core.database import get_db
from backend.app.models.schemas import AlertLogCreate, AlertLogResponse

router = APIRouter()


@router.post("/", response_model=AlertLogResponse, status_code=201, summary="Log and Dispatch Emergency Alert")
def create_alert(payload: AlertLogCreate, db: sqlite3.Connection = Depends(get_db)):
    """Logs an alert dispatched to District Administration or public channels."""
    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO alert_logs (
            alert_level, state, district, corridor_affected, title, message, channels
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload.alert_level,
            payload.state,
            payload.district,
            payload.corridor_affected,
            payload.title,
            payload.message,
            payload.channels,
        ),
    )
    alert_id = cursor.lastrowid
    cursor.execute("SELECT * FROM alert_logs WHERE id = ?", (alert_id,))
    row = cursor.fetchone()

    return AlertLogResponse(
        id=row["id"],
        alert_level=row["alert_level"],
        state=row["state"],
        district=row["district"],
        corridor_affected=row["corridor_affected"],
        title=row["title"],
        message=row["message"],
        channels=row["channels"],
        dispatched_at=str(row["dispatched_at"]),
    )


@router.get("/", response_model=List[AlertLogResponse], summary="List Recent Disaster Alerts")
def list_alerts(limit: int = 20, db: sqlite3.Connection = Depends(get_db)):
    """Returns recent early warnings issued by the system."""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM alert_logs ORDER BY dispatched_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()

    return [
        AlertLogResponse(
            id=row["id"],
            alert_level=row["alert_level"],
            state=row["state"],
            district=row["district"],
            corridor_affected=row["corridor_affected"],
            title=row["title"],
            message=row["message"],
            channels=row["channels"],
            dispatched_at=str(row["dispatched_at"]),
        )
        for row in rows
    ]
