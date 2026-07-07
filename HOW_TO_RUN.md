# Smart Health - How to Run the Project

## Prerequisites

### Required Software
- **Python 3.8+** (for backend)
- **Node.js 16+** and **npm** (for frontend)
- **Git** (optional, for cloning)

### Verify Installations
```bash
# Check Python version
python --version
# or
python3 --version

# Check Node.js version
node --version

# Check npm version
npm --version
```

---

## Quick Start (Recommended)

### Option 1: Using the Setup Script (Easiest)
```bash
# From the smart-health directory
python setup_database.py
```

This will automatically:
1. Generate synthetic data
2. Seed the database
3. Verify the setup

### Option 2: Using Batch Script (Windows)
```bash
# Double-click this file in File Explorer:
scripts\setup.bat
```

This will automatically:
1. Create Python virtual environment
2. Install backend dependencies
3. Install frontend dependencies
4. Generate synthetic data
5. Seed the database

### Mac/Linux Users
```bash
# Make the script executable (first time only)
chmod +x scripts/setup.sh

# Run the setup script
./scripts/setup.sh
```

---

## Manual Setup (Step-by-Step)

### Step 1: Clone or Navigate to Project
```bash
cd smart-health
```

### Step 2: Backend Setup

#### 2.1 Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 2.2 Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
cd ..
```

#### 2.3 Generate Synthetic Data
```bash
# This creates 12 months of realistic data
python data/generator.py
```

#### 2.4 Seed the Database
```bash
# This loads the generated data into SQLite database
python data/seed_data.py
```

#### 2.5 Start Backend Server
```bash
# From the backend directory
cd backend
uvicorn main:app --reload

# OR from the project root
uvicorn backend/main:app --reload
```

The backend will start at: **http://localhost:8000**

- API Documentation: **http://localhost:8000/docs**
- API Alternative Docs: **http://localhost:8000/redoc**

### Step 3: Frontend Setup

#### 3.1 Install Frontend Dependencies
```bash
# Open a NEW terminal window (keep backend running)
cd frontend
npm install
```

#### 3.2 Start Frontend Development Server
```bash
# From the frontend directory
npm run dev
```

The frontend will start at: **http://localhost:5173**

---

## Access the Application

### URLs
- **Frontend Dashboard**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Default Pages
- Dashboard: http://localhost:5173/
- PHC Detail: http://localhost:5173/phc/1
- Recommendations: http://localhost:5173/recommendations
- Alerts: http://localhost:5173/alerts
- Simulation: http://localhost:5173/simulation

---

## Common Commands

### Backend Commands
```bash
# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Start backend server
cd backend
uvicorn main:app --reload

# Start backend on specific port
uvicorn main:app --reload --port 8001

# Run without auto-reload (production)
uvicorn main:app --workers 4

# Regenerate data
cd data
python generator.py
python seed_data.py
```

### Frontend Commands
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Start on specific port
npm run dev -- --port 3000

# Build for production
npm run build

# Preview production build
npm run preview

# Run linting
npm run lint
```

---

## Troubleshooting

### Backend Issues

#### Issue: "Module not found" errors
```bash
# Make sure you're in the backend directory
cd backend

# Reinstall dependencies
pip install -r requirements.txt
```

#### Issue: Database errors / Empty PHC dropdown
```bash
# IMPORTANT: The database is created at: d:\Hack2Skill\smart-health\smart_health.db
# NOT in the backend folder!

# Delete the database (from smart-health directory)
del smart_health.db  # Windows
rm smart_health.db   # Mac/Linux

# Regenerate and reseed
python data/generator.py
python data/seed_data.py

# OR use the setup script
python setup_database.py
```

**Note**: If you see "No PHCs found" in the simulation dropdown, it means the database is empty. Run the commands above to seed it.

#### Issue: Port 8000 already in use
```bash
# Use a different port
uvicorn main:app --reload --port 8001
```

### Frontend Issues

#### Issue: "Module not found" errors
```bash
# Delete node_modules and reinstall
rm -rf node_modules package-lock.json  # Mac/Linux
rmdir /s node_modules  # Windows
npm install
```

#### Issue: Port 5173 already in use
```bash
# Use a different port
npm run dev -- --port 3000
```

#### Issue: Charts not loading
```bash
# Make sure recharts is installed
npm install recharts

# Clear browser cache and hard refresh (Ctrl+Shift+R)
```

### General Issues

#### Issue: CORS errors
```bash
# Make sure backend is running first, then frontend
# Check that CORS is configured in backend/main.py
# Allowed origins should include: http://localhost:5173
```

#### Issue: Data not showing
```bash
# 1. Make sure database is seeded
python data/seed_data.py

# 2. Check backend logs for errors
# 3. Check browser console for frontend errors
# 4. Verify API endpoints are accessible: http://localhost:8000/docs
```

---

## Project Structure

```
smart-health/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── requirements.txt        # Python dependencies
│   └── app/
│       ├── database/
│       │   ├── schema.py       # Database models
│       │   └── connection.py   # DB connection
│       ├── models/
│       │   └── ml_models.py    # ML models
│       └── schemas/
│           └── models.py       # Pydantic schemas
├── frontend/
│   ├── src/
│   │   ├── pages/              # React pages
│   │   ├── components/         # Reusable components
│   │   ├── services/           # API calls
│   │   └── utils/              # Translations
│   ├── package.json
│   └── vite.config.js
├── data/
│   ├── generator.py            # Data generator
│   └── seed_data.py            # Database seeder
└── scripts/
    ├── setup.sh                # Mac/Linux setup
    └── setup.bat               # Windows setup
```

---

## Development Workflow

### 1. Start Backend (Terminal 1)
```bash
cd smart-health/backend
uvicorn main:app --reload
```

### 2. Start Frontend (Terminal 2)
```bash
cd smart-health/frontend
npm run dev
```

### 3. Open Browser
```
http://localhost:5173
```

### 4. Make Changes
- Backend changes auto-reload (thanks to `--reload`)
- Frontend changes auto-reload (thanks to Vite HMR)

---

## Testing the Application

### Test Checklist
- [ ] Dashboard loads with metrics
- [ ] PHC detail pages load
- [ ] Recommendations page shows data
- [ ] Alerts page displays alerts
- [ ] Simulation page works
- [ ] Language switcher changes text
- [ ] Charts render correctly
- [ ] No console errors

### Test Simulation Mode
1. Go to http://localhost:5173/simulation
2. Click "Advance 1 Day"
3. Navigate to Dashboard - metrics should update
4. Trigger "Disease Outbreak" at a PHC
5. Check Alerts page - new alerts should appear
6. Check Recommendations - new suggestions should show

### Test Multilingual Support
1. Click language switcher in navbar (top right)
2. Cycle through: EN → HI → TA
3. Verify all page text changes
4. Check all 4 pages work in all languages

---

## Production Deployment

### Backend
```bash
# Install production dependencies
pip install gunicorn

# Run with gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend
```bash
# Build for production
npm run build

# Serve with any static file server
# Example: serve -s dist -l 3000
npm install -g serve
serve -s dist -l 3000
```

---

## Environment Variables

### Backend (.env file in backend/)
```env
DATABASE_URL=sqlite:///./smart_health.db
# For PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost/smart_health
```

### Frontend (.env file in frontend/)
```env
VITE_API_URL=http://localhost:8000
```

---

## Quick Reference

| Service | URL | Port |
|---------|-----|------|
| Frontend | http://localhost:5173 | 5173 |
| Backend API | http://localhost:8000 | 8000 |
| API Docs | http://localhost:8000/docs | 8000 |

| Command | Purpose |
|---------|---------|
| `python data/generator.py` | Generate synthetic data |
| `python data/seed_data.py` | Seed database |
| `uvicorn main:app --reload` | Start backend |
| `npm run dev` | Start frontend |
| `npm run build` | Build frontend for production |

---

## Need Help?

1. Check the **README.md** for architecture overview
2. Check **DEMO_GUIDE.md** for demo instructions
3. Check **SCOPE.md** for project scope
4. Check **PROJECT_SUMMARY.md** for complete feature list

---

## Success Indicators

✅ Backend starts without errors
✅ Frontend loads at http://localhost:5173
✅ Dashboard shows 6 PHCs with metrics
✅ Simulation page shows PHCs in dropdown (not empty)
✅ Charts render correctly
✅ Simulation mode works
✅ Language switcher works
✅ No console errors

If all of the above work, you're ready for the demo! 🚀

---

## Important Notes

### Database Location
The SQLite database is created at: **`smart-health/smart_health.db`**

This is in the project root, NOT in the backend folder. If you delete the database, make sure you're deleting from the correct location.

### Common Issues

1. **Empty PHC dropdown in Simulation page**
   - Cause: Database not seeded
   - Fix: Run `python setup_database.py` or `python data/seed_data.py`

2. **"Error advancing simulation"**
   - Cause: Database is empty or backend can't find it
   - Fix: Ensure database exists at `smart-health/smart_health.db` and restart backend

3. **Backend can't find database after seeding**
   - Cause: Backend was started before database was created
   - Fix: Restart the backend server after seeding

### Complete Setup Workflow
```bash
# 1. Navigate to project root
cd d:\Hack2Skill\smart-health

# 2. Setup database (first time only)
python setup_database.py

# 3. Start backend (Terminal 1)
cd backend
python -m uvicorn main:app --reload

# 4. Start frontend (Terminal 2)
cd frontend
npm run dev

# 5. Open browser
# http://localhost:5173
```
