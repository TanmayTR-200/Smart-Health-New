#!/bin/bash
# Smart Health - Setup Script
# This script sets up the entire project for the first time

echo "========================================="
echo "Smart Health - Project Setup"
echo "========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Check Node.js version
echo "Checking Node.js version..."
node_version=$(node --version 2>&1)
echo "Found Node.js $node_version"

echo ""
echo "========================================="
echo "Step 1: Setting up Backend"
echo "========================================="

cd backend

# Create virtual environment
echo "Creating Python virtual environment..."
python -m venv venv

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

cd ..

echo ""
echo "========================================="
echo "Step 2: Setting up Frontend"
echo "========================================="

cd frontend

# Install dependencies
echo "Installing Node.js dependencies..."
npm install

cd ..

echo ""
echo "========================================="
echo "Step 3: Generating Synthetic Data"
echo "========================================="

cd data

echo "Generating 12 months of synthetic PHC data..."
python generator.py

cd ..

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "To run the project:"
echo "1. Start backend:  cd backend && source venv/bin/activate && uvicorn main:app --reload"
echo "2. Start frontend: cd frontend && npm run dev"
echo ""
echo "Then open http://localhost:5173 in your browser"
echo ""
echo "To seed the database (after starting backend):"
echo "  python data/seed_data.py"
echo ""