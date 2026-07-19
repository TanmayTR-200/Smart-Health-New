# Smart Health - One-Click Starter (PowerShell)
# This script handles EVERYTHING automatically

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Smart Health - Quick Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Change to project directory
$projectDir = "d:\Hack2Skill\smart-health"
Set-Location $projectDir

Write-Host "[1/5] Stopping any running servers..." -ForegroundColor Yellow

# Kill any existing uvicorn or node processes
Get-Process | Where-Object {$_.ProcessName -eq "python" -or $_.ProcessName -eq "node"} | Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep -Seconds 2

Write-Host "[2/5] Setting up database..." -ForegroundColor Yellow

# Delete old database if exists
if (Test-Path "smart_health_new.db") {
    Remove-Item "smart_health_new.db" -Force
    Write-Host "  ✓ Old database removed" -ForegroundColor Green
}

# Run setup script
python setup_database.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Database setup failed!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[3/5] Starting backend server..." -ForegroundColor Yellow

# Start backend in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $projectDir\backend; python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

Write-Host "  ✓ Backend starting..." -ForegroundColor Green
Write-Host "  ⏳ Waiting for backend to initialize (10 seconds)..." -ForegroundColor Yellow

# Wait for backend to start
Start-Sleep -Seconds 10

Write-Host "[4/5] Starting frontend server..." -ForegroundColor Yellow

# Start frontend in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $projectDir\frontend; npm run dev"

Write-Host "  ✓ Frontend starting..." -ForegroundColor Green
Write-Host "  ⏳ Waiting for frontend to initialize (8 seconds)..." -ForegroundColor Yellow

# Wait for frontend to start
Start-Sleep -Seconds 8

Write-Host "[5/5] Opening browser..." -ForegroundColor Yellow

# Open browser
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ Smart Health is running!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "🔧 Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "📚 API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "🎯 Go to Simulation page: http://localhost:5173/simulation" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to exit this window (servers will keep running)..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
