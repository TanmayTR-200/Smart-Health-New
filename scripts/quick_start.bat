@echo off
echo ========================================
echo Smart Health - Quick Start Setup
echo ========================================
echo.

REM Check if database exists
if exist "%~dp0..\smart_health.db" (
    echo Database already exists. Skipping setup.
    goto :start_servers
)

echo Setting up database...
echo.

REM Generate data
echo [1/3] Generating synthetic data...
cd /d "%~dp0..\data"
python generator.py
if errorlevel 1 (
    echo ERROR: Failed to generate data
    pause
    exit /b 1
)

REM Seed database
echo.
echo [2/3] Seeding database...
python seed_data.py
if errorlevel 1 (
    echo ERROR: Failed to seed database
    pause
    exit /b 1
)

REM Verify
echo.
echo [3/3] Verifying database...
cd /d "%~dp0.."
python -c "import sqlite3; conn = sqlite3.connect('smart_health.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM phcs'); count = cursor.fetchone()[0]; print(f'SUCCESS: Database created with {count} PHCs'); conn.close()"
if errorlevel 1 (
    echo ERROR: Database verification failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo Database setup complete!
echo ========================================
echo.

:start_servers
echo Starting servers...
echo.
echo Backend will start at: http://localhost:8000
echo Frontend will start at: http://localhost:5173
echo.
echo Press Ctrl+C to stop the servers
echo ========================================
echo.

REM Start backend in a new window
start "Smart Health Backend" cmd /k "cd /d "%~dp0..\backend" && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM Wait a moment for backend to start
timeout /t 3 /nobreak > nul

REM Start frontend in a new window
start "Smart Health Frontend" cmd /k "cd /d "%~dp0..\frontend" && npm run dev"

REM Open browser after a delay
timeout /t 5 /nobreak > nul
start http://localhost:5173

echo.
echo Servers are starting...
echo Check the new windows for server logs
echo.
pause