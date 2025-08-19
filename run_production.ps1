# PowerShell script to run Aditya Daily Digest with Uvicorn (Production Mode)
Write-Host "Starting Aditya Daily Digest with Uvicorn (Production Mode)..." -ForegroundColor Green
Write-Host ""

# Activate virtual environment if it exists
if (Test-Path "venv") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
}

# Set production environment
$env:FLASK_ENV = "production"
$env:FLASK_DEBUG = "False"

# Start with Uvicorn directly (production settings)
Write-Host "Starting production server..." -ForegroundColor Green
Write-Host "Server will be available at: http://localhost:5000" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

uvicorn app:app --host 0.0.0.0 --port 5000 --workers 4 --log-level warning

Read-Host "Press Enter to exit"
