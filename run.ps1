# =====================================================================
# NER Landslide Early Warning & Risk Monitoring System
# One-Click PowerShell Launcher
# MDoNER Problem Statement ID: 26001
# =====================================================================

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host " NER LANDSLIDE EARLY WARNING & RISK MONITORING SYSTEM" -ForegroundColor Green
Write-Host " MDoNER Problem Statement ID: 26001" -ForegroundColor Yellow
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "[ERROR] Virtual environment not detected at .venv\Scripts\python.exe" -ForegroundColor Red
    Write-Host "Please initialize the environment:" -ForegroundColor White
    Write-Host "  python -m venv .venv" -ForegroundColor Gray
    Write-Host "  .venv\Scripts\pip install -r requirements.txt" -ForegroundColor Gray
    Exit 1
}

$modelFile = Join-Path $PSScriptRoot "backend\ml_engine\models\landslide_rf_model.joblib"
if (-not (Test-Path $modelFile)) {
    Write-Host "[*] Model artifact not found. Triggering automated training..." -ForegroundColor Yellow
    & $venvPython -m backend.ml_engine.train
}

Write-Host "[*] Launching Tactical GIS Dashboard in browser..." -ForegroundColor Green
Start-Process "http://127.0.0.1:8000/"

Write-Host "[*] Starting Uvicorn ASGI Server on http://127.0.0.1:8000 ..." -ForegroundColor Cyan
Write-Host "[*] Press Ctrl+C to terminate the server.`n" -ForegroundColor DarkGray

& $venvPython -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
