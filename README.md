# Smart Health

### AI-Powered District Health Management System

**Live:** https://smart-health-new.vercel.app

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)](https://react.dev/)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Vite](https://img.shields.io/badge/Vite-5-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3-38BDF8?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-Portfolio_Project-blue)](#license)

---

## Table of Contents

- [Overview](#overview)
- [Engineering Highlights](#engineering-highlights)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [ML Models](#ml-models)
- [Getting Started](#getting-started)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Data Transparency](#data-transparency)
- [Deployment](#deployment)
- [License](#license)

---

## Overview

Smart Health is a full-stack platform that applies ML forecasting, anomaly detection, and linear programming optimization to a real-world problem: district-level health resource management in India. It monitors **6 PHCs/CHCs** across a sample district, tracking medicine stocks, patient footfall, bed availability, doctor attendance, and diagnostic test availability.

The project explores what happens when you take statistical models (Prophet, IsolationForest, LP) and apply them honestly to an operational domain — including graceful fallbacks when compute constraints prevent the primary model from running, and transparent method reporting so consumers always know which algorithm produced the result they're looking at.

---

## Engineering Highlights

**Honest method transparency** — Every ML component (Prophet, IsolationForest, LP optimization) has a tested fallback and reports which method actually ran via a `method` field in the API response. The frontend surfaces this as a badge on every page (Dashboard, PHC Detail, Recommendations, Alerts) so the consumer always knows whether they're looking at a Prophet prediction or a moving-average fallback.

**pytest suite covering decision boundaries** — Tests verify that fallback triggers fire correctly (<30 days of data returns insufficient_data, deficit exceeds excess triggers rule_based_fallback, fewer than 4 PHCs falls back to average_threshold), that LP solutions respect supply/demand constraints, and that IsolationForest genuinely flags outlier PHCs. Not just happy-path tests.

**Linear programming with real scipy.optimize.linprog** — The redistribution engine formulates a genuine LP: minimise unmet deficit plus transfer distance across a 6x6 PHC cost matrix, with an equality constraint that makes the problem infeasible when total deficit exceeds total excess (triggering the rule-based fallback). Not a threshold-matching algorithm relabeled as "optimization."

**Multilingual with live AI translation** — UI text uses a dictionary, but all AI-generated content (recommendation reasoning, alert descriptions) is translated live via Google Gemini, with in-memory caching to minimise API calls.

---

## Key Features

### Dashboard
- District-wide health overview with real-time metrics
- **Health Score (0-100)** per PHC — color-coded with composite scoring:
  - Stock reliability (35%) / Doctor attendance (25%) / Bed utilization (20%) / Test availability (20%)
- Active alerts panel with severity indicators
- Interactive charts (health score comparison, status distribution)

### PHC Detail View
- 30-day footfall trends with emergency case highlighting
- Bed occupancy and doctor attendance charts
- Medicine stock table with low-stock alerts and prediction method badges
- Individual health score with trend indicators

### Redistribution Recommendations
- Linear programming engine computing optimal transfer routes between PHCs
- Priority classification: Critical, High, Medium
- **Google Gemini AI** generates contextual reasoning for each recommendation
- Transfer quantity calculations with impact projections and route distances

### Alerts Center
- Real-time anomaly detection across 4 categories:
  - Stock-out warnings, underperforming PHCs, attendance drops, bed shortages
- Filterable by severity with timestamped details

### Simulation Mode
- **Advance Day** — move the simulation forward to see predictions evolve
- **Trigger Events**:
  - Disease outbreak (spikes footfall + medicine usage)
  - Delayed resupply (causes stock-out risk)
  - Doctor absence spike (sharp attendance drop)
- Live system reactions visible across all dashboard pages

### Multilingual Support
- English, Hindi, Kannada
- UI translation via dictionary + **Gemini-powered dynamic translation** for AI-generated content

---

## Tech Stack

|     Layer    |                 Technology                    |                        Purpose                          |
|--------------|-----------------------------------------------|---------------------------------------------------------|
| **Backend**  |        FastAPI, SQLAlchemy, Pydantic          |      Async REST API with auto-generated docs            |
| **ML/AI**    | Prophet, scikit-learn, SciPy, Google Gemini   | Forecasting, anomaly detection, optimization, reasoning |
| **Frontend** |   React 18, Vite 5, Tailwind CSS, Recharts    |      Glassmorphism UI with responsive charts            |
| **Database** | SQLite (local) / Neon PostgreSQL (production) |     Time-series schema with 10 relational tables        |
| **DevOps**   |       Docker, Vercel-ready frontend           |    Containerized backend, static frontend deploy        |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)              │
│  Dashboard · PHC Detail · Recommendations · Alerts · Sim│
└──────────────────────────┬──────────────────────────────┘
                           │ REST API (JSON)
┌──────────────────────────▼──────────────────────────────┐
│                  Backend (FastAPI)                      │
│  ┌─────────┐  ┌──────────┐  ┌───────────┐  ┌─────────┐  │ 
│  │ Routes  │  │ Schemas  │  │ ML Models │  │ Gemini  │  │
│  │ (25+    │→ │ (Pydantic│→ │ (Prophet, │→ │ Service │  │
│  │ endpoints)│  │  models) │  │  IsoForest)│  │ (AI) │  │
│  └─────────┘  └──────────┘  └───────────┘  └─────────┘  │
└──────────────────────────┬──────────────────────────────┘
                           │ SQLAlchemy ORM
┌──────────────────────────▼──────────────────────────────┐
│              Database (SQLite / PostgreSQL)             │
│  phcs · medicines · stocks · footfalls · beds ·         │
│  doctor_attendances · test_availabilities ·             │
│  predictions · anomalies · recommendations              │
└─────────────────────────────────────────────────────────┘
```

---

## ML Models

| Model | Type | What It Does |
|---|---|---|
| **Stock-out Prediction** | Prophet time-series (local) / 7-day moving average (deployed) | Forecasts days until stockout per medicine per PHC. Prophet runs locally with confidence 0.8; Render free tier OOMs on Prophet, so production uses the moving average fallback (confidence 0.6). `method` field in API response reports which one ran. |
| **Demand Forecasting** | Prophet time-series (local) / seasonal trend (fallback) | Fits Prophet on PHC footfall history to forecast the next 7 days with real confidence intervals from `yhat_lower`/`yhat_upper`. Falls back to trend + fixed seasonal multipliers (monsoon 1.3x, winter 1.15x) when Prophet is unavailable or <14 days of data. `method: "prophet"` or `"seasonal_trend"`. |
| **Anomaly Detection** | IsolationForest with average-threshold fallback | Fits IsolationForest on the 4-component health feature vector (stock, attendance, beds, tests) per PHC. `decision_function()` produces a real anomaly score; `fit_predict()` flags statistical outliers. Severity combines both the model signal and the district-average gap — outliers below average escalate, non-outliers de-escalate. Falls back to average-threshold when <4 PHCs. `method: "isolation_forest"` or `"average_threshold"`. |
| **Redistribution Engine** | Linear programming (scipy.optimize.linprog) with rule-based fallback | Minimises unmet deficit + transfer distance across a 6x6 PHC distance matrix. Falls back to greedy threshold matching when total deficit exceeds total excess (LP infeasible). `method` field reports `"linear_programming"` or `"rule_based_fallback"`. |
| **Gemini AI Service** | Google Gemini API | Generates natural-language reasoning for recommendations and real-time multilingual translation. Degrades to template text if API key is missing. |

> Every prediction endpoint reports its `method` field in the JSON response, and the frontend surfaces it as a badge so the consumer can verify which algorithm actually produced the result.
>
> **Compute**: Render free tier web service (spins down after 15 min inactivity — first request may take 30-60s).
> **Database**: Neon serverless PostgreSQL (free tier, scales to zero — first query after idle may take a few seconds). SQLite for local development.

---

## Getting Started

### Prerequisites

- **Python** 3.9+
- **Node.js** 18+
- **PostgreSQL** 14+ (optional — SQLite works out of the box)

### Option 1: Quick Start (Windows)

```powershell
cd Smart-Health-New
.\scripts\start_demo.ps1
```

This single command sets up the database, starts both servers, and opens the browser.

### Option 2: Manual Setup

**1. Clone the repository**
```bash
git clone https://github.com/TanmayTR-200/Smart-Health-New.git
cd Smart-Health-New
```

**2. Backend setup**
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # On Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

**3. Frontend setup**
```bash
cd ../frontend
npm install
```

**4. Generate & seed synthetic data**
```bash
cd ../data
python generator.py
python seed_data.py
```

**5. Start the servers**

```bash
# Terminal 1 — Backend
cd backend
uvicorn main:app --reload

# Terminal 2 — Frontend
cd frontend
npm run dev
```

**6. Access the application**

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

### Tests

```bash
cd backend && pytest
```

### Option 3: Docker

```bash
docker build -t smart-health-new .
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key smart-health-new
```

### Environment Variables

Copy `backend/.env.example` to `backend/.env` and configure:

```env
GEMINI_API_KEY=your_google_gemini_api_key    # Optional — system works without it (uses fallbacks)
DATABASE_URL=sqlite:///smart_health_new.db       # Or postgresql://user:pass@host:5432/dbname
```

### Database

| Environment | Database | Notes |
|---|---|---|
| **Local development** | SQLite | Default — no setup required; a `smart_health_new.db` file is created automatically |
| **Production (Render)** | Neon PostgreSQL | Serverless Postgres free tier (no credit card required) |

- **Neon scales to zero** after a period of inactivity. The first request after idle time may take a few seconds while the database wakes up.
- `DATABASE_URL` is **set via Render's dashboard environment variables** — it is never committed to the repo.
- The backend auto-detects the URL format: `postgres://` / `postgresql://` (including Neon's `?sslmode=require` query parameter) are converted to the SQLAlchemy `postgresql+psycopg2://` driver transparently. SQLite URLs are used as-is.

---

## API Documentation

FastAPI auto-generates interactive docs at `/docs` (Swagger UI) and `/redoc`.

### Endpoints Overview

| Category | Endpoint | Method | Description |
|---|---|---|---|
| **CRUD** | `/api/phcs` | GET | List all PHCs |
| | `/api/phcs/{id}` | GET | PHC details |
| | `/api/medicines` | GET | List medicines |
| | `/api/stock` | GET | Stock levels (filterable) |
| | `/api/stock/low` | GET | Low-stock items |
| | `/api/footfall` | GET | Patient footfall data |
| | `/api/beds` | GET | Bed occupancy data |
| | `/api/attendance` | GET | Doctor attendance |
| **Tests** | `/api/tests` | GET | Diagnostic test availability |
| | `/api/tests/summary` | GET | Test availability summary |
| **ML** | `/api/predictions/stockouts` | GET | Stock-out predictions |
| | `/api/predictions/demand` | GET | 7-day demand forecast |
| | `/api/anomalies` | GET | Anomaly detection results |
| | `/api/recommendations/redistribute` | GET | Redistribution recommendations |
| | `/api/translate` | POST | Gemini-powered text translation |
| **Simulation** | `/api/simulation/advance-day` | POST | Advance simulation by N days |
| | `/api/simulation/trigger-event` | POST | Trigger a simulation event |
| **Dashboard** | `/api/dashboard/summary` | GET | District-wide summary |
| | `/api/alerts` | GET | Active alerts |

---

## Project Structure

```
Smart-Health-New/
├── backend/
│   ├── app/
│   │   ├── database/
│   │   │   ├── schema.py              # 10 SQLAlchemy models
│   │   │   └── connection.py          # DB connection & session
│   │   ├── models/
│   │   │   └── ml_models.py           # ML model classes (Prophet, Isolation Forest, LP)
│   │   ├── schemas/
│   │   │   └── models.py              # Pydantic schemas
│   │   ├── services/
│   │   │   └── gemini_service.py      # Google Gemini AI wrapper
│   │   └── main.py                    # FastAPI app entry point
│   ├── tests/
│   │   └── test_ml_models.py          # pytest suite (8 tests)
│   ├── requirements.txt
│   ├── conftest.py
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── Navbar.jsx             # Navigation with language switcher
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx          # District overview
│   │   │   ├── PHCDetail.jsx          # Individual PHC analytics
│   │   │   ├── Recommendations.jsx    # AI redistribution page
│   │   │   ├── Alerts.jsx             # Alerts center
│   │   │   └── Simulation.jsx         # Simulation control panel
│   │   ├── contexts/
│   │   │   └── LanguageContext.jsx    # Multilingual management
│   │   ├── utils/
│   │   │   └── translations.js        # Translation dictionaries
│   │   ├── services/
│   │   │   └── api.js                 # API service layer
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css                  # Glassmorphism global styles
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── index.html
├── data/
│   ├── generator.py                   # Synthetic data generator
│   └── seed_data.py                   # Database seeding script
├── scripts/
│   ├── setup.sh                       # Unix setup script
│   ├── setup.bat                      # Windows setup script
│   └── start_demo.ps1                 # One-command launcher
├── docs/                              # Screenshots and assets
├── Dockerfile
├── setup_database.py
└── README.md
```

---

## Data Transparency

All data is **synthetic** but calibrated to real-world parameters:

| Parameter | Source | Value |
|---|---|---|
| Medicine list | National List of Essential Medicines (NLEM) 2023 | 6 essential medicines |
| Doctor absenteeism | Rural Health Statistics (RHS) 2021-22 | 15-20% (10% higher on Mondays) |
| Bed norms | Indian Public Health Standards (IPHS) | PHC: 6-10 beds, CHC: 30 beds |
| Footfall patterns | IDSP (Integrated Disease Surveillance Programme) | 20-150/day with seasonal multipliers |
| Test availability | NHM Comprehensive Primary Health Care guidelines | 85-95% equipment uptime |
| Seasonal disease | IDSP data | Monsoon: 1.3x (malaria/dengue), Winter: 1.15x (respiratory) |

**Data volume**: ~35,000+ records across 10 tables covering 12 months of daily data for 6 PHCs.

---

## Deployment

### Frontend (Vercel)
```bash
cd frontend
npm run build      # Outputs to dist/
# Deploy the dist/ folder to Vercel, Netlify, or any static host
```

### Backend (Docker)
```bash
docker build -t smart-health-new .
docker run -p 8000:8000 -e GEMINI_API_KEY=$KEY smart-health-new
```

### Production Path
- **Database**: Neon serverless PostgreSQL (free tier, no card required, scales to zero)
- **AI**: Configure `GEMINI_API_KEY` for full Gemini-powered reasoning
- **Integration**: Connect to India's HMIS/IHIP APIs for real data
- **Scaling**: Async FastAPI + connection pooling + ML model caching

---

## License

Personal/portfolio project with a live demo deployment for showcase purposes — not built or maintained as a production service. Demonstrates full-stack ML engineering, honest fallback design, and real-time system architecture.
