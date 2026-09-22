@echo off
title NER Landslide Early Warning & Risk Monitoring System
color 0A

echo =====================================================================
echo  NER LANDSLIDE EARLY WARNING & RISK MONITORING SYSTEM
echo  MDoNER Problem Statement ID: 26001
echo =====================================================================
echo.

cd /d "%~dp0"

REM Verify virtual environment existence
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found in .venv.
    echo Please run:
    echo   python -m venv .venv
    echo   .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

echo [*] Activating virtual environment (.venv)...
call .venv\Scripts\activate.bat

echo [*] Checking database and ML model artifacts...
if not exist "backend\ml_engine\models\landslide_rf_model.joblib" (
    echo [*] Model artifact missing. Running automated training pipeline...
    python -m backend.ml_engine.train
)

echo [*] Launching GIS Tactical Dashboard in default browser...
start http://127.0.0.1:8000/

echo [*] Starting FastAPI Uvicorn Server on http://127.0.0.1:8000 ...
echo [*] Press Ctrl+C to terminate the server.
echo.

uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

pause
