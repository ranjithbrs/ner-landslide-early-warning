# AI-Based Early Warning and Landslide Risk Monitoring System in NER
**Ministry of Development of North Eastern Region (MDoNER) — Problem Statement ID: 26001**

[![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141+-009688.svg)](https://fastapi.tiangolo.com/)
[![SQLite](https://img.shields.io/badge/SQLite-Integrated-003B57.svg)](https://sqlite.org/)
[![Tests](https://img.shields.io/badge/Tests-7%20Passed-brightgreen.svg)]()

---

## 1. Project Overview
The North Eastern Region (NER) of India frequently experiences severe landslides, flash floods, and slope failures caused by torrential monsoon rains, complex Himalayan/Indo-Burman geology, and steep road cuts. Key transportation arteries (such as NH-10 in Sikkim, NH-29 in Nagaland, and NH-6 in Meghalaya) and remote communities face recurring isolation.

This platform provides an **AI-enabled real-time early warning and monitoring system** designed to:
- Ingest and synthesize multi-factor data (terrain geomorphology, meteorological precipitation, and IoT ground sensor telemetry).
- Compute spatial landslide susceptibility and dynamic early warning hazard indices.
- Issue multi-level alerts (Green, Yellow, Orange, Red) to District Disaster Management Authorities (DDMA) and field officers.
- Provide GIS visualization of critical corridors and emergency relief hubs.
- Enable citizen and field official crowdsourced geo-tagged hazard reporting with offline-first synchronization.

---

## 2. Development Roadmap

| Phase | Focus Area | Status | Deliverables |
| :--- | :--- | :--- | :--- |
| **Phase 1** | **Project Foundation** | **Completed** | Clean directory architecture, FastAPI core, SQLite database, Pydantic schemas, ML abstract interface & baseline contract, responsive frontend shell, automated test suite. |
| **Phase 2** | **ML Pipeline** | **Completed** | Calibrated prototype dataset generator for 15 NER corridors, featurization pipeline, model comparisons (Naive vs Logistic Regression vs Random Forest: 94.9% accuracy, 95.9% recall, 0.993 ROC-AUC), serialized artifacts, and real-time prediction service. |
| **Phase 3** | **Interactive GIS Dashboard** | **Completed** | Leaflet.js interactive tactical GIS map with OGC GeoJSON feeds for risk polygons, critical highway corridors, IoT sensor telemetry, crowdsourced field hazard reports, and interactive real-time ML stress simulation sandbox. |

---

## 3. Project Architecture & Directory Structure

```
mlproj/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── health.py        # System health & runtime diagnostic check
│   │   │       │   ├── risk.py          # Landslide risk prediction & summary routes
│   │   │       │   ├── sensors.py       # Ground telemetry ingestion & retrieval
│   │   │       │   ├── reports.py       # Citizen & field officer crowdsourced hazard reports
│   │   │       │   └── alerts.py        # Emergency early warning dispatch logs
│   │   │       └── router.py            # Central aggregated API v1 router
│   │   ├── core/
│   │   │   ├── config.py                # Pydantic Settings (environment & file paths)
│   │   │   └── database.py              # SQLite connection manager & schema initialization
│   │   ├── ml/
│   │   │   ├── __init__.py              # ML package exports
│   │   │   ├── schemas.py               # Feature schemas (Terrain, Meteo, Geotech)
│   │   │   └── interface.py             # BaseLandslideModel contract & uncalibrated baseline
│   │   ├── models/
│   │   │   └── schemas.py               # Entity schemas for API requests and responses
│   │   └── main.py                      # FastAPI application, lifespan manager & static mount
│   └── ml_engine/                       # (Phase 2) Model training, evaluation & serialized artifacts
├── frontend/
│   ├── css/
│   │   └── styles.css                   # Tactical dark emergency response dashboard stylesheet
│   ├── js/
│   │   └── app.js                       # Frontend controller (health ping, live DB reports feed)
│   └── index.html                       # Semantic dashboard shell with #gis-map container
├── config/
│   └── .env.example                     # Environment configuration reference
├── data/
│   ├── raw/                             # Raw simulated datasets (Phase 2)
│   ├── processed/                       # Scaled and encoded datasets (Phase 2)
│   └── landslide_system.db              # SQLite relational database file
├── tests/
│   ├── __init__.py
│   └── test_foundation.py               # Comprehensive pytest suite for Phase 1
├── requirements.txt                     # Pinned project dependencies
└── README.md                            # Project documentation
```

---

## 4. How the Components Connect

```mermaid
flowchart LR
    Browser["Frontend Web UI (index.html, app.js)"]
    API["FastAPI Backend (/api/v1)"]
    DB[("SQLite Database (landslide_system.db)")]
    ML["ML Predictor Interface (BaseLandslideModel)"]

    Browser -->|GET /api/v1/health| API
    Browser -->|POST/GET /api/v1/reports| API
    API <-->|PRAGMA thread-safe queries| DB
    API <-->|predict(features)| ML
```

1. **Frontend to Backend**:
   - `app.js` runs on page load and checks `GET /api/v1/health`.
   - On response, it updates the visual connection status badge and footer diagnostic indicators.
   - The field reporting form submits structured JSON to `POST /api/v1/reports/` and fetches updated lists from `GET /api/v1/reports/`.
2. **Backend to Database**:
   - `database.py` manages connections to SQLite using standard context managers (`get_db_connection()` and FastAPI dependency `get_db()`).
   - `init_db()` runs automatically on startup via FastAPI's `lifespan` event, creating `sensor_readings`, `incident_reports`, `alert_logs`, and `road_corridors` tables.
3. **Backend to Machine Learning**:
   - `backend/app/ml/schemas.py` defines exact input contracts: `TerrainFeatures`, `MeteorologicalFeatures`, `GeotechnicalFeatures`.
   - `backend/app/ml/interface.py` defines the abstract `BaseLandslideModel`. In Phase 1, `FallbackLandslidePredictor` provides an uncalibrated heuristic baseline.
   - In Phase 2, the trained Random Forest pipeline will plug into this exact interface without requiring changes to API routes or frontend code.

---

## 5. Getting Started

### 5.1 Prerequisites
- Python 3.10+ (tested on Python 3.14.3)
- Windows / macOS / Linux

### 5.2 Environment Setup
```powershell
# 1. Create and activate Python virtual environment
python -m venv .venv
.venv\Scripts\activate

# 2. Install pinned dependencies
pip install -r requirements.txt
```

### 5.3 Running the Application
```powershell
# Start the FastAPI server (serves both API and Frontend)
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- **Web Application**: Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Interactive Swagger Docs**: Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check Endpoint**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

### 5.4 Running Tests
```powershell
.venv\Scripts\python.exe -m pytest tests/test_foundation.py -v
```
All 7 automated tests verify database integrity, schemas, fallback ML contract, and API routes.
