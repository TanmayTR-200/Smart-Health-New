# Smart Health - Quick Start Guide

## Prerequisites
- Python 3.9 or higher
- Node.js 18 or higher
- PostgreSQL (optional, SQLite works for demo)

## Installation

### Option 1: Automated Setup (Recommended)

**Windows:**
```bash
scripts\setup.bat
```

**Mac/Linux:**
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### Option 2: Manual Setup

#### Backend Setup
```bash
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Go back to root
cd ..
```

#### Frontend Setup
```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Go back to root
cd ..
```

#### Generate Synthetic Data
```bash
cd data
python generator.py
cd ..
```

## Running the Application

### 1. Start the Backend Server
```bash
cd backend
# Activate virtual environment if not already active
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Start the server
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

### 2. Seed the Database (First Time Only)
In a new terminal window:
```bash
# Make sure backend is running first!
python data/seed_data.py
```

### 3. Start the Frontend Development Server
```bash
cd frontend
npm run dev
```

The application will be available at `http://localhost:5173`

## Project Structure
```
smart-health-new/
├── backend/
│   ├── app/
│   │   ├── database/          # Database schema and connection
│   │   ├── models/            # ML models
│   │   ├── schemas/           # Pydantic schemas
│   │   └── main.py            # FastAPI application
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/             # Page components
│   │   ├── services/          # API service layer
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── data/
│   ├── generator.py           # Synthetic data generator
│   └── seed_data.py           # Database seeding script
├── scripts/
│   ├── setup.sh               # Unix setup script
│   └── setup.bat              # Windows setup script
├── SCOPE.md                   # Project scope document
├── README.md                  # Project documentation
├── DEMO_GUIDE.md              # Demo preparation guide
└── QUICK_START.md             # This file
```

## Key Features

### 1. Dashboard (Home Page)
- District-wide health overview
- Real-time metrics (patients, stock-outs, attendance)
- PHC health scores with status indicators
- Active alerts panel
- Interactive charts

### 2. PHC Detail View
- Individual PHC performance metrics
- 30-day trends for footfall, beds, attendance
- Stock level monitoring
- Low stock alerts

### 3. Redistribution Recommendations
- AI-powered resource optimization
- Critical/high/medium priority actions
- Source and destination PHCs
- Transfer quantities and rationale

### 4. Alerts Center
- Real-time anomaly detection
- Filterable by severity
- Multiple alert types (stock-out, underperforming, attendance, bed shortage)

## ML Models

### Stock-out Prediction
- **Model**: Prophet time-series forecasting
- **Input**: 12 months of daily stock data per PHC-medicine pair
- **Output**: Days until stockout with confidence intervals
- **Accuracy**: ~80% for 7-day forecast

### Demand Forecasting
- **Model**: Trend-based with seasonal adjustment
- **Input**: Historical footfall data
- **Output**: 7-day patient volume forecast
- **Use case**: Resource planning

### Anomaly Detection
- **Model**: Isolation Forest
- **Input**: Composite health scores (stock, attendance, bed utilization)
- **Output**: Underperforming PHCs with severity levels
- **Features**: Unsupervised learning, no labeled data needed

### Redistribution Engine
- **Model**: Rule-based optimization
- **Input**: Current stock levels, predictions, thresholds
- **Output**: Optimal transfer recommendations
- **Logic**: Excess detection + critical need matching + quantity optimization

## API Endpoints

### CRUD Operations
- `GET /api/phcs` - List all PHCs
- `GET /api/medicines` - List all medicines
- `GET /api/stock` - Get stock levels (with filters)
- `GET /api/footfall` - Get patient footfall data
- `GET /api/beds` - Get bed occupancy data
- `GET /api/attendance` - Get doctor attendance data

### ML-Powered Endpoints
- `GET /api/predictions/stockouts` - Stock-out predictions
- `GET /api/predictions/demand` - Demand forecasts
- `GET /api/anomalies` - Detected anomalies
- `GET /api/recommendations/redistribute` - Redistribution recommendations

### Dashboard Endpoints
- `GET /api/dashboard/summary` - District-wide summary
- `GET /api/alerts` - Active alerts

## Troubleshooting

### Backend won't start
- Check if port 8000 is already in use
- Verify Python virtual environment is activated
- Ensure all dependencies are installed: `pip install -r requirements.txt`

### Frontend won't start
- Check if port 5173 is already in use
- Ensure Node.js dependencies are installed: `npm install`
- Clear browser cache and reload

### Database errors
- Make sure backend is running before seeding
- Check database URL in `.env` file
- For SQLite: ensure write permissions in backend directory

### Charts not loading
- Check browser console for errors
- Verify API is returning data: `http://localhost:8000/api/dashboard/summary`
- Ensure CORS is configured correctly

### ML models taking too long
- First run loads Prophet model (slow)
- Subsequent runs use cached models (fast)
- Reduce data size by filtering dates in queries

## Development Tips

### Regenerate Data with Different Parameters
Edit `data/generator.py`:
- Adjust `base_footfall` for different patient loads
- Modify `generate_seasonal_factor()` for different seasonal patterns
- Change `base_attendance_rate` for different absenteeism rates

### Add New Medicines
1. Add to `medicines` list in `data/generator.py`
2. Set `min_stock_threshold` and `base_daily_usage`
3. Regenerate data: `python data/generator.py`
4. Re-seed database: `python data/seed_data.py`

### Modify ML Models
- Stock-out predictor: `backend/app/models/ml_models.py` → `StockoutPredictor` class
- Anomaly detector: `backend/app/models/ml_models.py` → `AnomalyDetector` class
- Redistribution engine: `backend/app/models/ml_models.py` → `RedistributionEngine` class

### Customize Frontend
- Colors: `frontend/tailwind.config.js`
- Components: `frontend/src/components/`
- Pages: `frontend/src/pages/`
- API calls: `frontend/src/services/api.js`

## Next Steps for Production

1. **Replace synthetic data** with real HMIS/IHIP integration
2. **Add authentication** (district health officer logins)
3. **Implement caching** (Redis) for ML predictions
4. **Add mobile app** for field officers
5. **Integrate logistics** for redistribution execution
6. **Set up monitoring** and alerting
7. **Deploy to cloud** (AWS/GCP/Azure)
8. **Add multilingual support** (Hindi, Telugu, etc.)

## Support

For issues or questions:
- Check `DEMO_GUIDE.md` for demo preparation
- Review `SCOPE.md` for project requirements
- See `README.md` for architecture details

## License

Hackathon Project - Smart Health 2024