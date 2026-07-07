@echo off
REM Smart Health - Setup Script for Windows
REM This script sets up the entire project for the first time

echo =========================================
echo Smart Health - Project Setup
echo =========================================
echo.

REM Check Python version
echo Checking Python version...
python --version
echo.

REM Check Node.js version
echo Checking Node.js version...
node --version
echo.

echo =========================================
echo Step 1: Setting up Backend
echo =========================================

cd backend

REM Create virtual environment
echo Creating Python virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

cd ..

echo.
echo =========================================
echo Step 2: Setting up Frontend
echo =========================================

cd frontend

REM Install dependencies
echo Installing Node.js dependencies...
call npm install

cd ..

echo.
echo =========================================
echo Step 3: Generating Synthetic Data
echo =========================================

cd data

echo Generating 12 months of synthetic PHC data...
python generator.py

cd ..

echo.
echo =========================================
echo Setup Complete!
echo =========================================
echo.
echo To run the project:
echo 1. Start backend:  cd backend ^&^& venv\Scripts\activate ^&^& uvicorn main:app --reload
echo 2. Start frontend: cd frontend ^&^& npm run dev
echo.
echo Then open http://localhost:5173 in your browser
echo.
echo To seed the database (after starting backend):
echo   python data/seed_data.py
echo.
pause