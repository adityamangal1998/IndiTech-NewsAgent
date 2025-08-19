# PowerShell script to run Aditya Daily Digest with Uvicorn
Write-Host "Starting Aditya Daily Digest with Uvicorn..." -ForegroundColor Green
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Install requirements
Write-Host "Installing requirements..." -ForegroundColor Yellow
pip install -r requirements.txt

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "ERROR: .env file not found!" -ForegroundColor Red
    Write-Host "Please copy .env and configure your credentials." -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Start the application with Uvicorn
Write-Host ""
Write-Host "Starting Flask application with Uvicorn..." -ForegroundColor Green
Write-Host "Open your browser and go to: http://localhost:5000" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python app.py

Read-Host "Press Enter to exit"
