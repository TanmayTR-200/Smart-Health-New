<div align="center">

# 🏥 Smart Health

### AI-Powered District Health Management System

An intelligent healthcare management platform that optimizes Primary Health Centre (PHC) operations through ML-powered predictions, anomaly detection, and AI-driven resource redistribution recommendations.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)](https://react.dev/)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Vite](https://img.shields.io/badge/Vite-5-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3-38BDF8?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-Hackathon_Project-orange)](LICENSE)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Problem Statement](#-problem-statement)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [ML Models](#-ml-models)
- [Getting Started](#-getting-started)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Data Transparency](#-data-transparency)
- [Deployment](#-deployment)
- [License](#-license)

---

## 📖 Overview

Smart Health is a full-stack AI-powered platform designed to bring real-time visibility and predictive intelligence to district-level health resource management in India. It monitors **6 PHCs/CHCs** across a sample district, tracking medicine stocks, patient footfall, bed availability, doctor attendance, and diagnostic test availability — all powered by ML forecasting and Google Gemini AI for natural-language reasoning.

### Why It Matters

| Problem | Impact |
|---|---|
| **30% of PHCs** face regular medicine stock-outs | Patients turned away without treatment |
| **15–20% doctor absenteeism** in rural areas | Erodes trust in public healthcare |
| **No real-time district-wide visibility** | Reactive instead of proactive management |
| **Manual redistribution** is slow & inefficient | Wastage alongside shortages |

---

## 🎯 Key Features

### 📊 Dashboard
- District-wide health overview with real-time metrics
- **Health Score (0–100)** per PHC — color-coded with composite scoring:
  - Stock reliability (35%) · Doctor attendance (25%) · Bed utilization (20%) · Test availability (20%)
- Active alerts panel with severity indicators
- Interactive charts (health score comparison, status distribution)

### 🏥 PHC Detail View
- 30-day footfall trends with emergency case highlighting
- Bed occupancy & doctor attendance charts
- Medicine stock table with low-stock alerts
- Individual health score with trend indicators

### 🤖 AI-Powered Redistribution
- Optimization engine computing optimal transfer routes between PHCs
- Priority classification: **Critical → High → Medium**
- **Google Gemini AI** generates contextual reasoning for each recommendation
- Transfer quantity calculations with impact projections

### 🚨 Alerts Center
- Real-time anomaly detection across 4 categories:
  - Stock-out warnings · Underperforming PHCs · Attendance drops · Bed shortages
- Filterable by severity with timestamped details

### 🎮 Simulation Mode
- **Advance Day** — move the simulation forward to see predictions evolve
- **Trigger Events**:
  - 🦠 Disease outbreak (spikes footfall + medicine usage)
  - 📦 Delayed resupply (causes stock-out risk)
  - 👨‍⚕️ Doctor absence spike (sharp attendance drop)
- Live system reactions visible across all dashboard pages

### 🌐 Multilingual Support
- English · Hindi (हिं) · Kannada (ಕನ್ನಡ)
- UI translation via dictionary + **Gemini-powered dynamic translation** for AI-generated content

---

## 🛠 Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend** | FastAPI · SQLAlchemy · Pydantic | Async REST API with auto-generated docs |
| **ML/AI** | Prophet · scikit-learn · SciPy · Google Gemini | Forecasting, anomaly detection, optimization, reasoning |
| **Frontend** | React 18 · Vite 5 · Tailwind CSS · Recharts | Modern glassmorphism UI with responsive charts |
| **Database** | SQLite (demo) / PostgreSQL (production) | Time-series schema with 10 relational tables |
| **DevOps** | Docker · Vercel-ready frontend | Containerized backend, static frontend deploy |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                │
│  Dashboard · PHC Detail · Recommendations · Alerts · Sim │
└──────────────────────────┬──────────────────────────────┘
                           │ REST API (JSON)
┌──────────────────────────▼──────────────────────────────┐
│                  Backend (FastAPI)                        │
│  ┌─────────┐  ┌──────────┐  ┌───────────┐  ┌─────────┐ │
│  │ Routes  │  │ Schemas  │  │ ML Models │  │ Gemini  │ │
│  │ (25+    │→ │ (Pydantic│→ │ (Prophet, │→ │ Service │ │
│  │ endpoints)│  │  models) │  │  IsoForest)│  │ (AI)   │ │
│  └─────────┘  └──────────┘  └───────────┘  └─────────┘ │
└──────────────────────────┬──────────────────────────────┘
                           │ SQLAlchemy ORM
┌──────────────────────────▼──────────────────────────────┐
│              Database (SQLite / PostgreSQL)              │
│  phcs · medicines · stocks · footfalls · beds ·         │
│  doctor_attendances · test_availabilities ·             │
│  predictions · anomalies · recommendations              │
└─────────────────────────────────────────────────────────┘
```

---

## 🧠 ML Models

| Model | Type | What It Does |
|---|---|---|
| **Stock-out Prediction** | Prophet time-series | Forecasts days until stockout per medicine per PHC using 12 months of historical data with seasonality & trend detection |
| **Demand Forecasting** | Trend + seasonal adjustment | Predicts 7-day patient footfall using historical patterns (monsoon/winter multipliers, weekly cycles) |
| **Anomaly Detection** | Isolation Forest (unsupervised) | Flags underperforming PHCs by detecting statistical outliers across composite health scores |
| **Redistribution Engine** | Rule-based optimization + Gemini AI | Computes optimal resource transfers between PHCs; Gemini generates human-readable reasoning and impact analysis |
| **Gemini AI Service** | Google Gemini API | Provides dynamic natural-language reasoning for recommendations and real-time multilingual translation |

> All ML models gracefully degrade to fallback strategies (e.g., moving average) if dependencies are unavailable.

---

## 🚀 Getting Started

### Prerequisites

- **Python** 3.9+
- **Node.js** 18+
- **PostgreSQL** 14+ (or use bundled SQLite for demo)

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

### Option 3: Docker

```bash
docker build -t smart-health .
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key smart-health
```

### Environment Variables

Copy `backend/.env.example` to `backend/.env` and configure:

```env
GEMINI_API_KEY=your_google_gemini_api_key    # Optional — system works without it (uses fallbacks)
DATABASE_URL=sqlite:///smart_health.db       # Or postgresql://user:pass@host:5432/dbname
```

---

## 📡 API Documentation

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

## 📁 Project Structure

```
Smart-Health-New/
├── backend/
│   ├── app/
│   │   ├── database/
│   │   │   ├── schema.py              # 10 SQLAlchemy models
│   │   │   └── connection.py          # DB connection & session
│   │   ├── models/
│   │   │   └── ml_models.py           # ML model classes (Prophet, Isolation Forest, etc.)
│   │   ├── schemas/
│   │   │   └── models.py              # Pydantic schemas
│   │   ├── services/
│   │   │   └── gemini_service.py      # Google Gemini AI wrapper
│   │   └── main.py                    # FastAPI app entry point
│   ├── requirements.txt
│   ├── .env.example
│   └── main.py
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
│   └── start_demo.ps1                 # One-command demo launcher
├── Dockerfile
├── setup_database.py
├── reset_db.py
├── SCOPE.md
└── README.md
```

---

## 📊 Data Transparency

All data is **synthetic** but calibrated to real-world parameters:

| Parameter | Source | Value |
|---|---|---|
| Medicine list | National List of Essential Medicines (NLEM) 2023 | 6 essential medicines |
| Doctor absenteeism | Rural Health Statistics (RHS) 2021–22 | 15–20% (10% higher on Mondays) |
| Bed norms | Indian Public Health Standards (IPHS) | PHC: 6–10 beds · CHC: 30 beds |
| Footfall patterns | IDSP (Integrated Disease Surveillance Programme) | 20–150/day with seasonal multipliers |
| Test availability | NHM Comprehensive Primary Health Care guidelines | 85–95% equipment uptime |
| Seasonal disease | IDSP data | Monsoon: 1.3× (malaria/dengue) · Winter: 1.15× (respiratory) |

**Data volume**: ~35,000+ records across 10 tables covering 12 months of daily data for 6 PHCs.

---

## 🚢 Deployment

### Frontend (Vercel)
```bash
cd frontend
npm run build      # Outputs to dist/
# Deploy the dist/ folder to Vercel, Netlify, or any static host
```

### Backend (Docker)
```bash
docker build -t smart-health .
docker run -p 8000:8000 -e GEMINI_API_KEY=$KEY smart-health
```

### Production Path
- **Database**: Switch from SQLite to PostgreSQL
- **AI**: Configure `GEMINI_API_KEY` for full Gemini-powered reasoning
- **Integration**: Connect to India's HMIS/IHIP APIs for real data
- **Scaling**: Async FastAPI + connection pooling + ML model caching

---

## 📝 License

Hackathon Project — Smart Health 2024. Built for demonstration purposes.

---

<div align="center">

**Built with ❤️ for India's Primary Health Centres**

</div>
