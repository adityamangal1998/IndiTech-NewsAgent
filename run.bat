@echo off
echo Starting Aditya Daily Digest with Uvicorn...
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt

REM Check if .env file exists
if not exist ".env" (
    echo.
    echo ERROR: .env file not found!
    echo Please copy .env and configure your credentials.
    echo.
    pause
    exit /b 1
)

REM Start the application with Uvicorn
echo.
echo Starting Flask application with Uvicorn...
echo Open your browser and go to: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.
python app.py

pause
