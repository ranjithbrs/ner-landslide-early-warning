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

        _seed_initial_data(cursor)


def _seed_initial_data(cursor: sqlite3.Cursor) -> None:
    """Seeds initial real-world representative sensor stations, corridors, and reports if tables are empty."""
    # 1. Seed Road Corridors
    cursor.execute("SELECT COUNT(*) FROM road_corridors;")
    if cursor.fetchone()[0] == 0:
        corridors = [
            ("NH-10", "Sevoke-Gangtok Highway", "Sikkim", "Sevoke (WB)", "Gangtok (Sikkim)", "single_lane", "HIGH"),
            ("NH-29", "Dimapur-Kohima Highway", "Nagaland", "Dimapur", "Kohima", "open", "MODERATE"),
            ("NH-6", "Guwahati-Shillong Highway", "Meghalaya", "Jorabat", "Shillong", "open", "MODERATE"),
            ("NH-27", "Lumding-Haflong-Silchar Highway", "Assam", "Lumding", "Silchar", "blocked", "VERY_HIGH"),
            ("NH-102", "Imphal-Moreh Corridor", "Manipur", "Imphal", "Moreh", "risky", "HIGH"),
            ("NH-13", "Bhalukpong-Bomdila-Tawang Route", "Arunachal Pradesh", "Bhalukpong", "Tawang", "open", "MODERATE"),
            ("NH-2", "Aizawl-Lunglei Highway", "Mizoram", "Aizawl", "Lunglei", "open", "LOW"),
            ("NH-8", "Agartala-Sabroom Highway", "Tripura", "Agartala", "Sabroom", "open", "LOW"),
        ]
        cursor.executemany(
            """
            INSERT INTO road_corridors (corridor_code, name, state, start_point, end_point, status, risk_level)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            corridors,
        )

    # 2. Seed IoT Sensor Stations
    stations = [
        ("ST-SKM-01", "NH-10 Mile 9 Teesta Station", "Sikkim", "Pakyong", 27.15, 88.52, 84.5, 18.2, 28.0, 1.2, 96.0),
        ("ST-NGL-01", "NH-29 Kohima By-pass Station", "Nagaland", "Kohima", 25.67, 94.11, 72.0, 11.5, 15.0, 0.6, 98.0),
        ("ST-MEG-01", "NH-6 Umiam Valley Station", "Meghalaya", "Ri Bhoi", 25.68, 91.91, 78.2, 14.0, 22.0, 0.9, 94.0),
        ("ST-ASM-01", "NH-27 Haflong Hill Cut Station", "Assam", "Dima Hasao", 25.17, 93.02, 88.1, 21.0, 35.0, 1.8, 91.0),
        ("ST-ARN-01", "Bhalukpong-Bomdila Station", "Arunachal Pradesh", "West Kameng", 27.26, 92.42, 65.0, 9.0, 12.0, 0.3, 99.0),
        ("ST-MNP-01", "Tupul Railway Corridor Station", "Manipur", "Noney", 24.78, 93.65, 81.0, 16.5, 25.0, 1.1, 95.0),
        ("ST-MIZ-01", "Champhai Highway Station", "Mizoram", "Champhai", 23.47, 93.32, 68.4, 10.2, 14.0, 0.4, 97.0),
        ("ST-TRP-01", "Jampui Hills Ridge Station", "Tripura", "North Tripura", 23.95, 92.27, 58.0, 6.5, 8.0, 0.1, 100.0),
    ]
    for st in stations:
        cursor.execute("SELECT COUNT(*) FROM sensor_readings WHERE station_id = ?", (st[0],))
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                """
                INSERT INTO sensor_readings (
                    station_id, station_name, state, district, latitude, longitude,
                    soil_moisture_pct, pore_pressure_kpa, rainfall_1h_mm, tilt_displacement_mm, battery_pct
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                st,
            )

    # 3. Seed Sample Crowdsourced Incident Reports
    cursor.execute("SELECT COUNT(*) FROM incident_reports;")
    if cursor.fetchone()[0] == 0:
        reports = [
            ("Border Roads Patrol Officer", "+91 9435012345", 27.148, 88.518, "Sikkim", "Pakyong", "Tension Crack", "Critical", "30m fissure observed on uphill slope above NH-10 road cut. Slump movement suspected.", None, "synced", "verified"),
            ("Highway Engineer PWD", "+91 9862098765", 25.165, 93.025, "Assam", "Dima Hasao", "Mudslide", "High", "Debris flow blocking both lanes at Km 24 near Haflong railway cut. Heavy rainfall continuing.", None, "synced", "dispatched"),
            ("Village Disaster Volunteer", "+91 9774054321", 25.682, 91.908, "Meghalaya", "Ri Bhoi", "Rockfall", "Medium", "Minor rock boulders detached onto highway shoulder near Umiam lake cut.", None, "synced", "verified"),
        ]
        cursor.executemany(
            """
            INSERT INTO incident_reports (
                reporter_name, contact_number, latitude, longitude, state, district,
                incident_type, severity, description, photo_url, sync_status, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            reports,
        )
