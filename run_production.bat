@echo off
echo Starting Aditya Daily Digest with Uvicorn (Production Mode)...
echo.

REM Activate virtual environment if it exists
if exist "venv" (
    call venv\Scripts\activate.bat
)

REM Set production environment
set FLASK_ENV=production
set FLASK_DEBUG=False

REM Start with Uvicorn directly (production settings)
echo Starting production server...
echo Server will be available at: http://localhost:5000
echo.

uvicorn app:app --host 0.0.0.0 --port 5000 --workers 4 --log-level warning

pause
