@echo off
echo ========================================
echo STARTING BACKEND (NO RELOAD - CLEAN START)
echo ========================================
echo.

echo Stopping any existing backend...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak > nul
echo ✓ Stopped
echo.

echo Starting backend server (clean start, no reload)...
cd /d "%~dp0backend"
python -m uvicorn main:app --host 0.0.0.0 --port 8000