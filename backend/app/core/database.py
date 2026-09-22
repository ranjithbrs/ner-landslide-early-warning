"""
Database configuration and session management for the application.
Uses standard library sqlite3 for lightweight, zero-overhead relational persistence.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from backend.app.core.config import settings


def get_db_path() -> Path:
    db_path = Path(settings.DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for obtaining a thread-safe database connection."""
    conn = sqlite3.connect(get_db_path(), timeout=15.0)
    conn.row_factory = sqlite3.Row  # Access columns by name
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Dependency for FastAPI route handlers."""
    with get_db_connection() as conn:
        yield conn


def init_db() -> None:
    """Initializes the database schema if tables do not already exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. IoT Sensor Telemetry Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station_id TEXT NOT NULL,
                station_name TEXT NOT NULL,
                state TEXT NOT NULL,
                district TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                soil_moisture_pct REAL NOT NULL,
                pore_pressure_kpa REAL NOT NULL,
                rainfall_1h_mm REAL NOT NULL,
                tilt_displacement_mm REAL NOT NULL,
                battery_pct REAL DEFAULT 100.0,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. Citizen / Field Official Crowdsourced Incident Reports
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS incident_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_name TEXT NOT NULL,
                contact_number TEXT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                state TEXT NOT NULL,
                district TEXT NOT NULL,
                incident_type TEXT NOT NULL, -- Crack, Rockfall, Mudslide, Blockage, Subsidence
                severity TEXT NOT NULL,      -- Low, Medium, High, Critical
                description TEXT NOT NULL,
                photo_url TEXT,
                sync_status TEXT DEFAULT 'synced', -- synced, offline_queued
                status TEXT DEFAULT 'pending',     -- pending, verified, dispatched, resolved
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 3. Emergency Alerts & Dispatches
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_level TEXT NOT NULL,  -- GREEN, YELLOW, ORANGE, RED
                state TEXT NOT NULL,
                district TEXT NOT NULL,
                corridor_affected TEXT,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                channels TEXT NOT NULL,     -- SMS, WhatsApp, Web, Siren
                dispatched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 4. Critical Road Corridors
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS road_corridors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                corridor_code TEXT UNIQUE NOT NULL, -- e.g. NH-10, NH-29, NH-6
                name TEXT NOT NULL,
                state TEXT NOT NULL,
                start_point TEXT NOT NULL,
                end_point TEXT NOT NULL,
                status TEXT DEFAULT 'open',         -- open, single_lane, blocked, risky
                risk_level TEXT DEFAULT 'LOW',      -- LOW, MODERATE, HIGH, VERY_HIGH
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sensor_station ON sensor_readings(station_id, recorded_at);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_incident_state ON incident_reports(state, district);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_level ON alert_logs(alert_level, dispatched_at);")
