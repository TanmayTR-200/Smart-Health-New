"""
Smart Health - FastAPI Backend Main Application
"""
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict
import os
import random
import numpy as np

from app.database.connection import get_db, init_db
from app.database.schema import PHC, Medicine, Stock, Footfall, BedOccupancy, DoctorAttendance, TestAvailability
from app.schemas.models import (
    PHCResponse, MedicineResponse, StockResponse, StockWithDetails,
    FootfallResponse, BedOccupancyResponse, DoctorAttendanceResponse, TestAvailabilityResponse,
    DistrictSummary, AlertItem, PHCHealthScore,
    StockoutPredictionResponse, DemandForecastResponse,
    RedistributionSuggestion, MessageResponse,
    SimulationAdvanceRequest, SimulationEventRequest, SimulationResponse
)
from app.models.ml_models import MLModelManager
from app.services.gemini_service import generate_text
import pandas as pd

# Initialize FastAPI app
app = FastAPI(
    title="Smart Health API",
    description="AI-Powered District Health Management System",
    version="2.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ML Model Manager
ml_manager = MLModelManager()

# ==================== Performance Cache ====================
# Simple TTL-based cache for expensive computations
import time as _time
from functools import lru_cache

class DataCache:
    """In-memory cache with TTL for expensive data operations"""
    def __init__(self, ttl_seconds=30):
        self._cache = {}
        self._ttl = ttl_seconds
    
    def get(self, key):
        if key in self._cache:
            entry = self._cache[key]
            if _time.time() - entry['time'] < self._ttl:
                return entry['data']
            del self._cache[key]
        return None
    
    def set(self, key, data):
        self._cache[key] = {'data': data, 'time': _time.time()}
    
    def invalidate(self, key_prefix=None):
        if key_prefix is None:
            self._cache.clear()
        else:
            keys_to_delete = [k for k in self._cache if k.startswith(key_prefix)]
            for k in keys_to_delete:
                del self._cache[k]

# Global cache instances
_health_score_cache = DataCache(ttl_seconds=15)  # Short TTL for health scores
_dataframe_cache = DataCache(ttl_seconds=10)     # Short TTL for DataFrames


def _get_cached_dataframes(db: Session) -> dict:
    """Get DataFrames with caching to avoid repeated full-table loads"""
    cache_key = f"dataframes_{id(db)}"
    cached = _dataframe_cache.get(cache_key)
    if cached:
        return cached
    
    from app.database.schema import Stock, Footfall, BedOccupancy, DoctorAttendance, TestAvailability
    
    result = {
        'stock': pd.read_sql(db.query(Stock).statement, db.bind),
        'footfall': pd.read_sql(db.query(Footfall).statement, db.bind),
        'bed': pd.read_sql(db.query(BedOccupancy).statement, db.bind),
        'attendance': pd.read_sql(db.query(DoctorAttendance).statement, db.bind),
        'test': pd.read_sql(db.query(TestAvailability).statement, db.bind),
    }
    _dataframe_cache.set(cache_key, result)
    return result


def _get_phc_health_scores_cached(db: Session, phcs_list=None) -> list:
    """Get health scores with caching to avoid redundant calculations"""
    cache_key = f"health_scores_{id(db)}"
    cached = _health_score_cache.get(cache_key)
    if cached:
        return cached
    
    from app.database.schema import PHC
    dfs = _get_cached_dataframes(db)
    phcs = phcs_list if phcs_list is not None else db.query(PHC).all()
    
    phc_scores = []
    for phc in phcs:
        score = ml_manager.anomaly_detector.calculate_phc_health_score(
            phc.id, dfs['stock'], dfs['attendance'], dfs['bed'], dfs['footfall'], dfs['test']
        )
        score['phc_id'] = phc.id
        score['phc_name'] = phc.name
        score['phc_code'] = phc.code
        phc_scores.append(score)
    
    _health_score_cache.set(cache_key, phc_scores)
    return phc_scores


def _invalidate_caches():
    """Invalidate all caches - call after data mutations"""
    _health_score_cache.invalidate()
    _dataframe_cache.invalidate()


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    
    # Auto-seed database if empty
    from app.database.schema import PHC, Stock
    from sqlalchemy.orm import Session
    from app.database.connection import SessionLocal
    
    db = SessionLocal()
    try:
        phc_count = db.query(PHC).count()
        stock_count = db.query(Stock).count()
        
        if phc_count == 0 or stock_count == 0:
            print("\n" + "="*60)
            print("⚠️  Database is empty. Auto-seeding...")
            print("="*60)
            
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'data'))
            from generator import PHCDataGenerator  # type: ignore
            
            # Generate and seed data
            print("Generating synthetic data...")
            generator = PHCDataGenerator()
            
            print("Seeding database...")
            from data.seed_data import seed_database
            seed_database()
            
            print("="*60)
            print("✓ Database seeded successfully!")
            print("="*60 + "\n")
    except Exception as e:
        print(f"⚠️  Auto-seed failed: {e}")
        print("Please run: python data/generator.py && python data/seed_data.py")
    finally:
        db.close()
    
    print("✓ Smart Health API started successfully")


@app.get("/", response_model=MessageResponse)
async def root():
    """Health check endpoint"""
    return {"message": "Smart Health API is running", "success": True}


# ==================== PHC Endpoints ====================

@app.get("/api/phcs", response_model=List[PHCResponse])
async def get_phcs(db: Session = Depends(get_db)):
    """Get all PHCs"""
    phcs = db.query(PHC).all()
    print(f"[DEBUG] /api/phcs endpoint called, returning {len(phcs)} PHCs")
    return phcs


@app.get("/api/phcs/{phc_id}", response_model=PHCResponse)
async def get_phc(phc_id: int, db: Session = Depends(get_db)):
    """Get specific PHC details with live health score and status"""
    from sqlalchemy import func
    from app.database.schema import Stock, Footfall, BedOccupancy, DoctorAttendance, TestAvailability

    phc = db.query(PHC).filter(PHC.id == phc_id).first()
    if not phc:
        raise HTTPException(status_code=404, detail="PHC not found")

    # Compute health score and detect anomalies (same logic as dashboard)
    stock_df = pd.read_sql(db.query(Stock).statement, db.bind)
    footfall_df = pd.read_sql(db.query(Footfall).statement, db.bind)
    bed_df = pd.read_sql(db.query(BedOccupancy).statement, db.bind)
    attendance_df = pd.read_sql(db.query(DoctorAttendance).statement, db.bind)
    test_df = pd.read_sql(db.query(TestAvailability).statement, db.bind)

    phc_scores = []
    for p in db.query(PHC).all():
        s = ml_manager.anomaly_detector.calculate_phc_health_score(
            p.id, stock_df, attendance_df, bed_df, footfall_df, test_df
        )
        s['phc_id'] = p.id
        s['phc_name'] = p.name
        s['phc_code'] = p.code
        phc_scores.append(s)

    anomalies = ml_manager.anomaly_detector.detect_anomalies(phc_scores)

    alert_severity_map = {}
    for anomaly in anomalies:
        aid = anomaly.get('phc_id')
        if aid:
            sev = anomaly.get('severity', 'low')
            if sev == 'critical':
                alert_severity_map[aid] = 'critical'
            elif sev == 'high' and alert_severity_map.get(aid) != 'critical':
                alert_severity_map[aid] = 'warning'
            elif aid not in alert_severity_map:
                alert_severity_map[aid] = 'warning'

    score = next((s for s in phc_scores if s['phc_id'] == phc_id), None)
    if score:
        phc.health_score = score['health_score']
        if phc_id in alert_severity_map:
            phc.status = alert_severity_map[phc_id]
        elif score['health_score'] >= 80:
            phc.status = "good"
        elif score['health_score'] >= 60:
            phc.status = "warning"
        else:
            phc.status = "critical"
    else:
        phc.health_score = 0
        phc.status = "critical"

    return phc


# ==================== Medicine Endpoints ====================

@app.get("/api/medicines", response_model=List[MedicineResponse])
async def get_medicines(db: Session = Depends(get_db)):
    """Get all medicines"""
    medicines = db.query(Medicine).all()
    return medicines


@app.get("/api/medicines/{medicine_id}", response_model=MedicineResponse)
async def get_medicine(medicine_id: int, db: Session = Depends(get_db)):
    """Get specific medicine details"""
    medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return medicine


# ==================== Stock Endpoints ====================

@app.get("/api/stock", response_model=List[StockWithDetails])
async def get_stock(
    phc_id: Optional[int] = None,
    medicine_id: Optional[int] = None,
    days: int = Query(15, description="Number of recent days to fetch"),
    latest_only: bool = Query(True, description="Return only the latest record per PHC+medicine"),
    db: Session = Depends(get_db)
):
    """Get stock levels with optional filters.
    
    By default returns only the latest stock record per PHC+medicine combination
    to avoid showing duplicate rows for the same medicine in PHC detail views.
    Set latest_only=false to fetch full time-series history.
    """
    query = db.query(Stock)
    
    if phc_id:
        query = query.filter(Stock.phc_id == phc_id)
    if medicine_id:
        query = query.filter(Stock.medicine_id == medicine_id)
    
    # Get recent data based on simulated date, not wall-clock date
    latest_stock = db.query(Stock).order_by(Stock.date.desc()).first()
    if latest_stock:
        cutoff_date = latest_stock.date - pd.Timedelta(days=days - 1)
    else:
        # No data yet - return empty result
        cutoff_date = date(2100, 1, 1)
    query = query.filter(Stock.date >= cutoff_date)
    query = query.order_by(Stock.date.desc())
    
    stocks = query.all()
    
    # Deduplicate: keep only the latest record per PHC+medicine
    if latest_only:
        seen = {}
        for stock in stocks:
            key = (stock.phc_id, stock.medicine_id)
            if key not in seen:
                seen[key] = stock
        stocks = list(seen.values())
    
    # Enrich with PHC and Medicine names
    result = []
    for stock in stocks:
        result.append(StockWithDetails(
            id=stock.id,
            phc_id=stock.phc_id,
            medicine_id=stock.medicine_id,
            date=stock.date,
            quantity=stock.quantity,
            min_required=stock.min_required,
            last_restocked=stock.last_restocked,
            created_at=stock.created_at,
            phc_name=stock.phc.name,
            medicine_name=stock.medicine.name,
            medicine_code=stock.medicine.code,
            days_remaining=stock.quantity // (stock.min_required // 15) if stock.min_required > 0 else None
        ))
    
    return result


@app.get("/api/stock/low", response_model=List[StockWithDetails])
async def get_low_stock(db: Session = Depends(get_db)):
    """Get all stock items below minimum threshold (latest record per PHC+medicine only)"""
    # First get latest stock record per PHC+medicine, then filter for low stock
    latest_date = db.query(Stock).order_by(Stock.date.desc()).first()
    if not latest_date:
        return []
    
    # Get all records from the latest date
    stocks = db.query(Stock).filter(Stock.date == latest_date.date).all()
    
    # Filter for low stock and deduplicate by PHC+medicine
    seen = {}
    low_stocks = []
    for stock in stocks:
        if stock.quantity < stock.min_required:
            key = (stock.phc_id, stock.medicine_id)
            if key not in seen:
                seen[key] = stock
                low_stocks.append(stock)
    
    result = []
    for stock in low_stocks:
        result.append(StockWithDetails(
            id=stock.id,
            phc_id=stock.phc_id,
            medicine_id=stock.medicine_id,
            date=stock.date,
            quantity=stock.quantity,
            min_required=stock.min_required,
            last_restocked=stock.last_restocked,
            created_at=stock.created_at,
            phc_name=stock.phc.name,
            medicine_name=stock.medicine.name,
            medicine_code=stock.medicine.code,
            days_remaining=0
        ))
    
    return result


# ==================== Footfall Endpoints ====================

@app.get("/api/footfall", response_model=List[FootfallResponse])
async def get_footfall(
    phc_id: Optional[int] = None,
    days: int = Query(15, description="Number of recent days to fetch"),
    db: Session = Depends(get_db)
):
    """Get footfall data"""
    query = db.query(Footfall)
    
    if phc_id:
        query = query.filter(Footfall.phc_id == phc_id)
    
    latest_footfall = db.query(Footfall).order_by(Footfall.date.desc()).first()
    if latest_footfall:
        cutoff_date = latest_footfall.date - pd.Timedelta(days=days - 1)
        query = query.filter(Footfall.date >= cutoff_date)
    query = query.order_by(Footfall.date.desc())
    query = query.limit(days)
    
    return query.all()


@app.get("/api/footfall/summary")
async def get_footfall_summary(db: Session = Depends(get_db)):
    """Get footfall summary by PHC"""
    from sqlalchemy import func
    
    results = db.query(
        PHC.id,
        PHC.name,
        func.avg(Footfall.total_patients).label('avg_patients'),
        func.sum(Footfall.total_patients).label('total_patients'),
        func.sum(Footfall.emergency_cases).label('total_emergency')
    ).join(Footfall).group_by(PHC.id, PHC.name).all()
    
    return [
        {
            "phc_id": r.id,
            "phc_name": r.name,
            "avg_patients": round(r.avg_patients, 1),
            "total_patients": r.total_patients,
            "total_emergency": r.total_emergency
        }
        for r in results
    ]


# ==================== Bed Occupancy Endpoints ====================

@app.get("/api/beds", response_model=List[BedOccupancyResponse])
async def get_bed_occupancy(
    phc_id: Optional[int] = None,
    days: int = Query(15, description="Number of recent days to fetch"),
    db: Session = Depends(get_db)
):
    """Get bed occupancy data"""
    query = db.query(BedOccupancy)
    
    if phc_id:
        query = query.filter(BedOccupancy.phc_id == phc_id)
    
    # Get recent data based on simulated date, not wall-clock date
    latest_bed_query = db.query(BedOccupancy)
    if phc_id:
        latest_bed_query = latest_bed_query.filter(BedOccupancy.phc_id == phc_id)
    latest_bed = latest_bed_query.order_by(BedOccupancy.date.desc()).first()
    if latest_bed:
        cutoff_date = latest_bed.date - pd.Timedelta(days=days - 1)
        query = query.filter(BedOccupancy.date >= cutoff_date)
    query = query.order_by(BedOccupancy.date.desc())
    query = query.limit(days)
    
    results = query.all()
    # Safety clamp: ensure consistent bed counts
    for r in results:
        if r.occupied_beds < 0:
            r.occupied_beds = 0
        if r.reserved_beds < 0:
            r.reserved_beds = 0
        # Clamp occupied + reserved to not exceed total_beds
        if r.occupied_beds + r.reserved_beds > r.total_beds:
            r.occupied_beds = min(r.occupied_beds, r.total_beds - r.reserved_beds)
            r.occupied_beds = max(0, r.occupied_beds)
        if r.available_beds < 0:
            r.available_beds = 0
        if r.occupancy_rate < 0:
            r.occupancy_rate = 0
        # Recalculate available from total - occupied - reserved
        expected_avail = r.total_beds - r.occupied_beds - r.reserved_beds
        r.available_beds = max(0, expected_avail)
        r.occupancy_rate = round((r.occupied_beds / r.total_beds) * 100, 2) if r.total_beds > 0 else 0
    return results


@app.get("/api/beds/available")
async def get_available_beds(db: Session = Depends(get_db)):
    """Get current available beds by PHC"""
    from sqlalchemy import func
    
    # Get latest bed occupancy for each PHC
    subquery = db.query(
        BedOccupancy.phc_id,
        func.max(BedOccupancy.date).label('latest_date')
    ).group_by(BedOccupancy.phc_id).subquery()
    
    results = db.query(
        PHC.id,
        PHC.name,
        PHC.total_beds,
        BedOccupancy.available_beds,
        BedOccupancy.occupied_beds,
        BedOccupancy.occupancy_rate
    ).join(
        BedOccupancy, (PHC.id == BedOccupancy.phc_id) & 
        (BedOccupancy.date == subquery.c.latest_date)
    ).join(subquery, PHC.id == subquery.c.phc_id).all()
    
    return [
        {
            "phc_id": r.id,
            "phc_name": r.name,
            "total_beds": r.total_beds,
            "available_beds": r.available_beds,
            "occupied_beds": r.occupied_beds,
            "occupancy_rate": r.occupancy_rate
        }
        for r in results
    ]


# ==================== Doctor Attendance Endpoints ====================

@app.get("/api/attendance", response_model=List[DoctorAttendanceResponse])
async def get_attendance(
    phc_id: Optional[int] = None,
    days: int = Query(15, description="Number of recent days to fetch"),
    db: Session = Depends(get_db)
):
    """Get doctor attendance data"""
    query = db.query(DoctorAttendance)
    
    if phc_id:
        query = query.filter(DoctorAttendance.phc_id == phc_id)
    
    # Get recent data based on simulated date, not wall-clock date
    latest_attendance_query = db.query(DoctorAttendance)
    if phc_id:
        latest_attendance_query = latest_attendance_query.filter(DoctorAttendance.phc_id == phc_id)
    latest_attendance = latest_attendance_query.order_by(DoctorAttendance.date.desc()).first()
    if latest_attendance:
        cutoff_date = latest_attendance.date - pd.Timedelta(days=days - 1)
    else:
        cutoff_date = date(2100, 1, 1) - pd.Timedelta(days=days - 1)
    query = query.filter(DoctorAttendance.date >= cutoff_date)
    query = query.order_by(DoctorAttendance.date.desc())
    query = query.limit(days)
    
    return query.all()


@app.get("/api/attendance/summary")
async def get_attendance_summary(db: Session = Depends(get_db)):
    """Get attendance summary by PHC"""
    from sqlalchemy import func
    
    results = db.query(
        PHC.id,
        PHC.name,
        func.avg(DoctorAttendance.attendance_rate).label('avg_attendance_rate'),
        func.sum(DoctorAttendance.absent_doctors).label('total_absent')
    ).join(DoctorAttendance).group_by(PHC.id, PHC.name).all()
    
    return [
        {
            "phc_id": r.id,
            "phc_name": r.name,
            "avg_attendance_rate": round(r.avg_attendance_rate, 2),
            "total_absent": r.total_absent
        }
        for r in results
    ]


# ==================== Test Availability Endpoints ====================

@app.get("/api/tests", response_model=List[TestAvailabilityResponse])
async def get_test_availability(
    phc_id: Optional[int] = None,
    days: int = Query(15, description="Number of recent days to fetch"),
    db: Session = Depends(get_db)
):
    """Get test availability data"""
    query = db.query(TestAvailability)
    
    if phc_id:
        query = query.filter(TestAvailability.phc_id == phc_id)
    
    # Get recent data based on simulated date, not wall-clock date
    latest_test = db.query(TestAvailability).order_by(TestAvailability.date.desc()).first()
    if latest_test:
        cutoff_date = latest_test.date - pd.Timedelta(days=days - 1)
    else:
        cutoff_date = date(2100, 1, 1) - pd.Timedelta(days=days - 1)
    query = query.filter(TestAvailability.date >= cutoff_date)
    query = query.order_by(TestAvailability.date.desc())
    query = query.limit(days)
    
    return query.all()


@app.get("/api/tests/summary")
async def get_test_availability_summary(db: Session = Depends(get_db)):
    """Get test availability summary by PHC"""
    from sqlalchemy import func, Integer
    
    results = db.query(
        PHC.id,
        PHC.name,
        func.avg(TestAvailability.is_available.cast(Integer)).label('availability_rate'),
        func.count(TestAvailability.id).label('total_tests')
    ).join(TestAvailability).group_by(PHC.id, PHC.name).all()
    
    return [
        {
            "phc_id": r.id,
            "phc_name": r.name,
            "availability_rate": round(float(r.availability_rate) * 100, 2) if r.availability_rate else 0,
            "total_tests": r.total_tests
        }
        for r in results
    ]


# ==================== ML-Powered Endpoints ====================

@app.get("/api/predictions/stockouts", response_model=List[StockoutPredictionResponse])
async def get_stockout_predictions(phc_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get stock-out predictions for all PHC-medicine combinations"""
    from app.database.schema import Stock, Medicine
    
    # Load stock data
    stock_query = db.query(Stock)
    if phc_id:
        stock_query = stock_query.filter(Stock.phc_id == phc_id)
    stock_df = pd.read_sql(stock_query.statement, db.bind)
    
    # Get medicines
    medicines = db.query(Medicine).all()
    
    # Run predictions
    predictions = []
    phcs = db.query(PHC).all() if not phc_id else db.query(PHC).filter(PHC.id == phc_id).all()
    
    for phc in phcs:
        for medicine in medicines:
            pred = ml_manager.stockout_predictor.predict_stockout(
                stock_df, phc.id, medicine.id, medicine.min_stock_threshold
            )
            
            if pred['days_until_stockout'] is not None and pred['days_until_stockout'] <= 14:
                current_stock = stock_df[
                    (stock_df['phc_id'] == phc.id) & 
                    (stock_df['medicine_id'] == medicine.id)
                ]['quantity'].iloc[-1] if len(stock_df) > 0 else 0
                
                predictions.append(StockoutPredictionResponse(
                    phc_id=phc.id,
                    phc_name=phc.name,
                    medicine_id=medicine.id,
                    medicine_name=medicine.name,
                    current_stock=int(current_stock),
                    days_until_stockout=pred['days_until_stockout'],
                    confidence=pred['confidence'],
                    recommended_action=pred['recommended_action']
                ))
    
    return predictions


@app.get("/api/predictions/demand", response_model=List[DemandForecastResponse])
async def get_demand_forecasts(phc_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get demand forecasts for patient footfall"""
    from app.database.schema import Footfall
    
    # Load footfall data
    footfall_query = db.query(Footfall)
    if phc_id:
        footfall_query = footfall_query.filter(Footfall.phc_id == phc_id)
    footfall_df = pd.read_sql(footfall_query.statement, db.bind)
    
    # Generate forecasts
    forecasts = []
    phcs = db.query(PHC).all() if not phc_id else db.query(PHC).filter(PHC.id == phc_id).all()
    
    for phc in phcs:
        forecast = ml_manager.demand_forecaster.forecast_footfall(footfall_df, phc.id)
        forecast['phc_id'] = phc.id
        forecast['phc_name'] = phc.name
        forecasts.append(DemandForecastResponse(**forecast))
    
    return forecasts


@app.get("/api/anomalies", response_model=List[dict])
async def get_anomalies(db: Session = Depends(get_db)):
    """Get detected anomalies (underperforming PHCs) - OPTIMIZED with caching"""
    from app.database.schema import PHC
    
    # Use cached health scores and dataframes
    phcs = db.query(PHC).all()
    phc_scores = _get_phc_health_scores_cached(db, phcs)
    
    # Detect anomalies
    anomalies = ml_manager.anomaly_detector.detect_anomalies(phc_scores)
    
    return anomalies


# In-memory cache for translations: key = (text, language)
_translation_cache: dict = {}


@app.post("/api/translate")
async def translate_text(request: Dict):
    """Translate dynamic text to the requested language using Gemini with cache."""
    text = request.get("text")
    language = request.get("language", "en")
    if not text:
        raise HTTPException(status_code=400, detail="Missing 'text'")
    cache_key = (text, language)
    if cache_key in _translation_cache:
        return {"translated_text": _translation_cache[cache_key], "cached": True}
    if language == "en":
        _translation_cache[cache_key] = text
        return {"translated_text": text, "cached": True}
    prompt = f"Translate the following text into {language}. Return ONLY the translated text, no explanations.\n\n{text}"
    translated = generate_text(prompt, max_retries=1, timeout_seconds=6, fallback=None)
    if not translated:
        translated = text
    _translation_cache[cache_key] = translated
    return {"translated_text": translated, "cached": False}


@app.get("/api/recommendations/redistribute", response_model=List[RedistributionSuggestion])
async def get_redistribution_recommendations(db: Session = Depends(get_db)):
    """Get resource redistribution recommendations.
    Returns empty array when district is balanced.
    Returns recommendations ONLY when there are actual PHCs with excess to transfer.
    Never returns 'All Good' falsely - empty means no surplus available.
    """
    from app.database.schema import Stock, Medicine
    
    # Load stock data
    stock_df = pd.read_sql(db.query(Stock).statement, db.bind)
    
    # Get stockout predictions
    predictions_response = await get_stockout_predictions(db=db)
    predictions_map = {p.phc_id: p.dict() for p in predictions_response}
    
    # Get PHCs
    phcs = db.query(PHC).all()
    phcs_list = [{"id": p.id, "name": p.name, "code": p.code} for p in phcs]
    
    # Find redistribution opportunities
    recommendations = ml_manager.redistribution_engine.find_redistribution_opportunities(
        stock_df, predictions_map, phcs_list
    )
    
    # Enrich with medicine names
    medicines = db.query(Medicine).all()
    medicine_map = {m.id: m.name for m in medicines}
    
    result = []
    for rec in recommendations:
        result.append(RedistributionSuggestion(
            from_phc_id=rec['from_phc_id'],
            from_phc_name=rec['from_phc_name'],
            to_phc_id=rec['to_phc_id'],
            to_phc_name=rec['to_phc_name'],
            medicine_id=rec['medicine_id'],
            medicine_name=medicine_map.get(rec['medicine_id'], f"Medicine-{rec['medicine_id']}"),
            quantity=rec['quantity'],
            urgency=rec['urgency'],
            reason=rec['reason'],
            impact=rec['impact']
        ))
    
    return result


def _generate_day_for_phc(db, phc, target_date, generator, changes, medicines_cache=None):
    """Generate one day of normal data for a single PHC.
    Used by both advance_simulation_day and trigger_simulation_event.
    """
    from app.database.schema import Stock, Footfall, BedOccupancy, DoctorAttendance, TestAvailability, Medicine
    
    # Generate footfall
    seasonal = generator.generate_seasonal_factor(target_date)
    weekly = generator.generate_weekly_factor(target_date)
    base_footfall = phc.base_footfall if hasattr(phc, 'base_footfall') else 80
    noise = np.random.normal(1.0, 0.15)
    total_patients = int(base_footfall * seasonal * weekly * noise)
    total_patients = max(20, min(200, total_patients))
    
    footfall = Footfall(
        phc_id=phc.id,
        date=target_date,
        total_patients=total_patients,
        new_patients=int(total_patients * random.uniform(0.3, 0.5)),
        follow_up_patients=0,
        emergency_cases=int(total_patients * random.uniform(0.05, 0.15))
    )
    footfall.follow_up_patients = total_patients - footfall.new_patients - footfall.emergency_cases
    db.add(footfall)
    
    changes["footfall_changes"].append({
        "phc_id": phc.id,
        "phc_name": phc.name,
        "date": target_date.strftime("%Y-%m-%d"),
        "total_patients": total_patients,
        "emergency_cases": footfall.emergency_cases
    })
    changes["district_summary"]["total_patients"] += total_patients
    changes["district_summary"]["total_emergency"] += footfall.emergency_cases
    
    # Generate bed occupancy
    existing_beds = db.query(BedOccupancy).filter(BedOccupancy.phc_id == phc.id).first()
    reserved_beds_stable = existing_beds.reserved_beds if existing_beds else min(max(0, int(phc.total_beds * 0.1)), 2)
    
    base_occupancy = random.uniform(0.65, 0.85) * seasonal * np.random.normal(1.0, 0.1)
    base_occupancy = max(0.5, min(0.98, base_occupancy))
    occupied = int(phc.total_beds * base_occupancy)
    reserved = reserved_beds_stable
    # Ensure occupied + reserved doesn't exceed total_beds
    occupied = min(occupied, phc.total_beds - reserved)
    occupied = max(0, occupied)
    available = max(0, phc.total_beds - occupied - reserved)
    occupancy_rate = round((occupied / phc.total_beds) * 100, 2) if phc.total_beds > 0 else 0
    
    bed = BedOccupancy(
        phc_id=phc.id,
        date=target_date,
        total_beds=phc.total_beds,
        occupied_beds=occupied,
        reserved_beds=reserved,
        available_beds=available,
        occupancy_rate=occupancy_rate
    )
    db.add(bed)
    
    changes["bed_changes"].append({
        "phc_id": phc.id,
        "phc_name": phc.name,
        "date": target_date.strftime("%Y-%m-%d"),
        "occupancy_rate": bed.occupancy_rate,
        "available_beds": bed.available_beds
    })
    
    # Generate doctor attendance
    base_attendance = random.uniform(0.78, 0.88)
    if target_date.weekday() == 0:
        attendance_rate = max(0.6, min(0.98, base_attendance * 0.9))
    else:
        attendance_rate = max(0.6, min(0.98, base_attendance * np.random.normal(1.0, 0.05)))
    present = int(phc.expected_doctors * attendance_rate)
    present = max(0, min(phc.expected_doctors, present))
    absent = phc.expected_doctors - present
    attendance_rate_pct = round((present / phc.expected_doctors) * 100, 2) if phc.expected_doctors > 0 else 0.0
    
    attendance = DoctorAttendance(
        phc_id=phc.id,
        date=target_date,
        expected_doctors=phc.expected_doctors,
        present_doctors=present,
        absent_doctors=absent,
        attendance_rate=attendance_rate_pct,
        reasons=""
    )
    db.add(attendance)
    
    changes["attendance_changes"].append({
        "phc_id": phc.id,
        "phc_name": phc.name,
        "date": target_date.strftime("%Y-%m-%d"),
        "attendance_rate": attendance.attendance_rate,
        "absent_doctors": attendance.absent_doctors
    })
    
    # Generate stock updates for each medicine (batch query latest stocks)
    medicines = medicines_cache if medicines_cache is not None else db.query(Medicine).all()
    
    latest_stocks = db.query(Stock).filter(
        Stock.phc_id == phc.id,
        Stock.medicine_id.in_([m.id for m in medicines])
    ).order_by(Stock.date.desc()).all()
    
    latest_stock_map = {}
    for ls in latest_stocks:
        if ls.medicine_id not in latest_stock_map:
            latest_stock_map[ls.medicine_id] = ls
    
    for medicine in medicines:
        latest_med_stock = latest_stock_map.get(medicine.id)
        
        if latest_med_stock:
            current_stock = latest_med_stock.quantity
            base_usage = medicine.base_daily_usage * (base_footfall / 80)
            daily_usage = int(base_usage * seasonal * np.random.normal(1.0, 0.2))
            daily_usage = max(1, daily_usage)
            new_stock = max(0, current_stock - daily_usage)
            
            last_restocked = latest_med_stock.last_restocked
            restock_arrives_on = latest_med_stock.restock_arrives_on
            
            if restock_arrives_on and restock_arrives_on <= target_date:
                new_stock = random.randint(medicine.min_stock_threshold * 3, medicine.min_stock_threshold * 5)
                last_restocked = target_date
                restock_arrives_on = None
            elif new_stock < medicine.min_stock_threshold and not restock_arrives_on:
                restock_delay = random.randint(3, 5)
                restock_arrives_on = target_date + timedelta(days=restock_delay)
            
            stock = Stock(
                phc_id=phc.id,
                medicine_id=medicine.id,
                date=target_date,
                quantity=new_stock,
                min_required=medicine.min_stock_threshold,
                last_restocked=last_restocked,
                restock_arrives_on=restock_arrives_on
            )
            db.add(stock)
    
    # Generate test availability (only from latest date for this PHC)
    latest_test_date = db.query(TestAvailability.date).filter(
        TestAvailability.phc_id == phc.id
    ).order_by(TestAvailability.date.desc()).first()
    if latest_test_date:
        tests = db.query(TestAvailability).filter(
            TestAvailability.phc_id == phc.id,
            TestAvailability.date == latest_test_date[0]
        ).all()
    else:
        tests = []
    for test in tests:
        is_available = random.random() < 0.9
        equipment_status = "functional" if is_available else random.choice(["maintenance", "broken", "reagent_stockout"])
        new_test = TestAvailability(
            phc_id=phc.id,
            test_name=test.test_name,
            test_code=test.test_code,
            date=target_date,
            is_available=is_available,
            equipment_status=equipment_status,
            last_calibration_date=test.last_calibration_date,
            notes=""
        )
        db.add(new_test)


@app.post("/api/simulation/advance-day", response_model=SimulationResponse)
async def advance_simulation_day(request: SimulationAdvanceRequest, db: Session = Depends(get_db)):
    """Advance simulation by one or more days, generating new data for ALL PHCs district-wide"""
    from app.database.schema import Stock, Footfall, BedOccupancy, DoctorAttendance, TestAvailability, PHC, Medicine
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'data'))
    from generator import PHCDataGenerator  # type: ignore
    
    # Get current latest date
    latest_stock = db.query(Stock).order_by(Stock.date.desc()).first()
    if not latest_stock:
        raise HTTPException(status_code=400, detail="No data available. Please run: python data/generator.py && python data/seed_data.py")
    
    current_date = latest_stock.date
    print(f"Advancing simulation from {current_date} by {request.days} days (DISTRICT-WIDE)")
    
    # Create generator for new data
    generator = PHCDataGenerator()
    changes = {
        "new_dates": [],
        "stock_changes": [],
        "footfall_changes": [],
        "bed_changes": [],
        "attendance_changes": [],
        "test_changes": [],
        "district_summary": {
            "total_phcs_affected": 0,
            "total_stock_change": 0,
            "total_patients": 0,
            "total_emergency": 0,
            "avg_attendance": 0,
            "avg_bed_occupancy": 0
        }
    }
    
    # Always update ALL PHCs for district-wide simulation
    phc_ids = [p.id for p in db.query(PHC).all()]
    phc_map = {p.id: p for p in db.query(PHC).all()}
    medicines = db.query(Medicine).all()
    medicine_ids = [m.id for m in medicines]
    attendance_sum = 0
    bed_occupancy_sum = 0
    
    for day in range(request.days):
        new_date = current_date + timedelta(days=day + 1)
        changes["new_dates"].append(new_date.strftime("%Y-%m-%d"))
        
        for phc_id in phc_ids:
            phc = phc_map[phc_id]
            if not phc:
                continue
            
            # Generate footfall
            seasonal = generator.generate_seasonal_factor(new_date)
            weekly = generator.generate_weekly_factor(new_date)
            base_footfall = phc.base_footfall if hasattr(phc, 'base_footfall') else 80
            noise = np.random.normal(1.0, 0.15)
            total_patients = int(base_footfall * seasonal * weekly * noise)
            total_patients = max(20, min(200, total_patients))
            
            footfall = Footfall(
                phc_id=phc_id,
                date=new_date,
                total_patients=total_patients,
                new_patients=int(total_patients * random.uniform(0.3, 0.5)),
                follow_up_patients=0,
                emergency_cases=int(total_patients * random.uniform(0.05, 0.15))
            )
            footfall.follow_up_patients = total_patients - footfall.new_patients - footfall.emergency_cases
            db.add(footfall)
            changes["footfall_changes"].append({
                "phc_id": phc_id,
                "phc_name": phc.name,
                "date": new_date.strftime("%Y-%m-%d"),
                "total_patients": total_patients,
                "emergency_cases": footfall.emergency_cases
            })
            changes["district_summary"]["total_patients"] += total_patients
            changes["district_summary"]["total_emergency"] += footfall.emergency_cases
            
            # Generate bed occupancy - use stable reserved_beds for this PHC (not random per day)
            # Get or create a stable reserved count for this PHC (10% of total, min 0, max 2)
            existing_beds = db.query(BedOccupancy).filter(
                BedOccupancy.phc_id == phc_id
            ).first()
            if existing_beds:
                reserved_beds_stable = existing_beds.reserved_beds
            else:
                reserved_beds_stable = min(max(0, int(phc.total_beds * 0.1)), 2)
            
            base_occupancy = random.uniform(0.65, 0.85) * seasonal * np.random.normal(1.0, 0.1)
            base_occupancy = max(0.5, min(0.98, base_occupancy))
            occupied = int(phc.total_beds * base_occupancy)
            reserved = reserved_beds_stable
            # Ensure occupied + reserved doesn't exceed total_beds
            occupied = min(occupied, phc.total_beds - reserved)
            occupied = max(0, occupied)
            available = max(0, phc.total_beds - occupied - reserved)
            
            # Calculate occupancy_rate from actual occupied_beds to ensure consistency
            occupancy_rate = round((occupied / phc.total_beds) * 100, 2) if phc.total_beds > 0 else 0
            
            bed = BedOccupancy(
                phc_id=phc_id,
                date=new_date,
                total_beds=phc.total_beds,
                occupied_beds=occupied,
                reserved_beds=reserved,
                available_beds=available,
                occupancy_rate=occupancy_rate
            )
            db.add(bed)
            changes["bed_changes"].append({
                "phc_id": phc_id,
                "phc_name": phc.name,
                "date": new_date.strftime("%Y-%m-%d"),
                "occupancy_rate": bed.occupancy_rate,
                "available_beds": bed.available_beds
            })
            bed_occupancy_sum += bed.occupancy_rate
            
            # Generate doctor attendance (compute rate FROM headcount to stay consistent)
            base_attendance = random.uniform(0.78, 0.88)
            if new_date.weekday() == 0:  # Monday
                attendance_rate = max(0.6, min(0.98, base_attendance * 0.9))
            else:
                attendance_rate = max(0.6, min(0.98, base_attendance * np.random.normal(1.0, 0.05)))
            present = int(phc.expected_doctors * attendance_rate)
            present = max(0, min(phc.expected_doctors, present))  # clamp to valid range
            absent = phc.expected_doctors - present
            attendance_rate_pct = round((present / phc.expected_doctors) * 100, 2) if phc.expected_doctors > 0 else 0.0
            
            attendance = DoctorAttendance(
                phc_id=phc_id,
                date=new_date,
                expected_doctors=phc.expected_doctors,
                present_doctors=present,
                absent_doctors=absent,
                attendance_rate=attendance_rate_pct,
                reasons=""
            )
            db.add(attendance)
            changes["attendance_changes"].append({
                "phc_id": phc_id,
                "phc_name": phc.name,
                "date": new_date.strftime("%Y-%m-%d"),
                "attendance_rate": attendance.attendance_rate,
                "absent_doctors": attendance.absent_doctors
            })
            attendance_sum += attendance.attendance_rate
            
            # Generate stock updates for each medicine (batch query latest stocks)
            latest_stocks = db.query(Stock).filter(
                Stock.phc_id == phc_id,
                Stock.medicine_id.in_(medicine_ids)
            ).order_by(Stock.date.desc()).all()
            latest_stock_map = {}
            for ls in latest_stocks:
                if ls.medicine_id not in latest_stock_map:
                    latest_stock_map[ls.medicine_id] = ls
            for medicine in medicines:
                latest_med_stock = latest_stock_map.get(medicine.id)
                
                if latest_med_stock:
                    current_stock = latest_med_stock.quantity
                    base_usage = medicine.base_daily_usage * (base_footfall / 80)
                    daily_usage = int(base_usage * seasonal * np.random.normal(1.0, 0.2))
                    daily_usage = max(1, daily_usage)
                    new_stock = max(0, current_stock - daily_usage)
                    
                    last_restocked = latest_med_stock.last_restocked
                    restock_arrives_on = latest_med_stock.restock_arrives_on
                    
                    # Check if a pending restock arrives today
                    if restock_arrives_on and restock_arrives_on <= new_date:
                        # Restock arrives - refill to 3x-5x threshold
                        new_stock = random.randint(medicine.min_stock_threshold * 3, medicine.min_stock_threshold * 5)
                        last_restocked = new_date
                        restock_arrives_on = None  # Clear the pending restock
                        changes["stock_changes"].append({
                            "phc_id": phc_id,
                            "phc_name": phc.name,
                            "medicine_id": medicine.id,
                            "medicine_name": medicine.name,
                            "date": new_date.strftime("%Y-%m-%d"),
                            "quantity": new_stock,
                            "change": new_stock - current_stock,
                            "restock_arrived": True
                        })
                    elif new_stock < medicine.min_stock_threshold and not restock_arrives_on:
                        # Stock below threshold and no pending restock - order restock with 3-5 day delay
                        restock_delay = random.randint(3, 5)
                        restock_arrives_on = new_date + timedelta(days=restock_delay)
                        changes["stock_changes"].append({
                            "phc_id": phc_id,
                            "phc_name": phc.name,
                            "medicine_id": medicine.id,
                            "medicine_name": medicine.name,
                            "date": new_date.strftime("%Y-%m-%d"),
                            "quantity": new_stock,
                            "change": new_stock - current_stock,
                            "restock_ordered": True,
                            "restock_arrives_on": restock_arrives_on.strftime("%Y-%m-%d")
                        })
                    else:
                        changes["stock_changes"].append({
                            "phc_id": phc_id,
                            "phc_name": phc.name,
                            "medicine_id": medicine.id,
                            "medicine_name": medicine.name,
                            "date": new_date.strftime("%Y-%m-%d"),
                            "quantity": new_stock,
                            "change": new_stock - current_stock
                        })
                    
                    stock = Stock(
                        phc_id=phc_id,
                        medicine_id=medicine.id,
                        date=new_date,
                        quantity=new_stock,
                        min_required=medicine.min_stock_threshold,
                        last_restocked=last_restocked,
                        restock_arrives_on=restock_arrives_on
                    )
                    db.add(stock)
                    changes["district_summary"]["total_stock_change"] += (new_stock - current_stock)
            
            # Generate test availability
            tests = db.query(TestAvailability).filter(
                TestAvailability.phc_id == phc_id,
                TestAvailability.date == current_date
            ).all()
            
            for test in tests:
                is_available = random.random() < 0.9
                equipment_status = "functional" if is_available else random.choice(["maintenance", "broken", "reagent_stockout"])
                
                new_test = TestAvailability(
                    phc_id=phc_id,
                    test_name=test.test_name,
                    test_code=test.test_code,
                    date=new_date,
                    is_available=is_available,
                    equipment_status=equipment_status,
                    last_calibration_date=test.last_calibration_date,
                    notes=""
                )
                db.add(new_test)
                changes["test_changes"].append({
                    "phc_id": phc_id,
                    "phc_name": phc.name,
                    "test_name": test.test_name,
                    "date": new_date.strftime("%Y-%m-%d"),
                    "is_available": is_available
                })
    
    db.commit()
    
    # Invalidate all caches since data has changed
    ml_manager.redistribution_engine.invalidate_cache()
    _invalidate_caches()
    
    # Calculate district-wide averages
    changes["district_summary"]["total_phcs_affected"] = len(phc_ids)
    if len(phc_ids) > 0:
        changes["district_summary"]["avg_attendance"] = round(attendance_sum / len(phc_ids), 2)
        changes["district_summary"]["avg_bed_occupancy"] = round(bed_occupancy_sum / len(phc_ids), 2)
    
    # Create summary message
    total_changes = (
        len(changes["stock_changes"]) +
        len(changes["footfall_changes"]) +
        len(changes["bed_changes"]) +
        len(changes["attendance_changes"]) +
        len(changes["test_changes"])
    )
    
    message = f"Advanced simulation by {request.days} day(s) across {len(phc_ids)} PHCs. {total_changes} total changes. District avg attendance: {changes['district_summary']['avg_attendance']}%, Avg bed occupancy: {changes['district_summary']['avg_bed_occupancy']}%"
    
    return SimulationResponse(
        success=True,
        message=message,
        simulated_date=current_date + timedelta(days=request.days),
        changes=changes
    )


@app.post("/api/simulation/trigger-event", response_model=SimulationResponse)
async def trigger_simulation_event(request: SimulationEventRequest, db: Session = Depends(get_db)):
    """Trigger a simulation event (disease outbreak, delayed resupply, doctor absence spike)
    Generates new data for future dates if they don't exist yet, then applies event effects
    """
    from app.database.schema import Stock, Footfall, BedOccupancy, DoctorAttendance, TestAvailability, Medicine
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'data'))
    from generator import PHCDataGenerator  # type: ignore
    
    phc = db.query(PHC).filter(PHC.id == request.phc_id).first()
    if not phc:
        raise HTTPException(status_code=404, detail="PHC not found")
    
    print(f"Triggering event: {request.event_type} at {phc.name} for {request.duration_days} days")
    
    # Get current latest date for THIS PHC (not global)
    latest_stock = db.query(Stock).filter(
        Stock.phc_id == request.phc_id
    ).order_by(Stock.date.desc()).first()
    if not latest_stock:
        raise HTTPException(status_code=400, detail="No data available")
    
    current_date = latest_stock.date
    generator = PHCDataGenerator()
    
    # Initialize changes dict with same structure as advance-day
    changes = {
        "new_dates": [],
        "stock_changes": [],
        "footfall_changes": [],
        "bed_changes": [],
        "attendance_changes": [],
        "test_changes": [],
        "district_summary": {
            "total_phcs_affected": 1,
            "total_stock_change": 0,
            "total_patients": 0,
            "total_emergency": 0,
            "avg_attendance": 0,
            "avg_bed_occupancy": 0
        }
    }
    
    if request.event_type == "disease_outbreak":
        # Spike footfall and medicine usage
        severity_multiplier = {"low": 1.5, "medium": 2.0, "high": 2.5}.get(request.severity, 2.0)
        
        for day in range(request.duration_days):
            event_date = current_date + timedelta(days=day + 1)
            changes["new_dates"].append(event_date.strftime("%Y-%m-%d"))
            
            # Generate or update footfall
            footfall = db.query(Footfall).filter(
                Footfall.phc_id == request.phc_id,
                Footfall.date == event_date
            ).first()
            
            if not footfall:
                # Generate new footfall data for this date
                seasonal = generator.generate_seasonal_factor(event_date)
                weekly = generator.generate_weekly_factor(event_date)
                base_footfall = getattr(phc, 'base_footfall', None) or 80  # Default to 80 if None
                noise = np.random.normal(1.0, 0.15)
                total_patients = int(base_footfall * seasonal * weekly * noise * severity_multiplier)
                total_patients = max(20, min(200, total_patients))
                
                footfall = Footfall(
                    phc_id=request.phc_id,
                    date=event_date,
                    total_patients=total_patients,
                    new_patients=int(total_patients * random.uniform(0.3, 0.5)),
                    follow_up_patients=0,
                    emergency_cases=int(total_patients * random.uniform(0.05, 0.15))
                )
                footfall.follow_up_patients = total_patients - footfall.new_patients - footfall.emergency_cases
                db.add(footfall)
            else:
                # Update existing footfall
                footfall.total_patients = int(footfall.total_patients * severity_multiplier)
                footfall.emergency_cases = int(footfall.emergency_cases * severity_multiplier * 1.5)
            
            changes["footfall_changes"].append({
                "phc_id": request.phc_id,
                "phc_name": phc.name,
                "date": event_date.strftime("%Y-%m-%d"),
                "total_patients": footfall.total_patients,
                "emergency_cases": footfall.emergency_cases
            })
            changes["district_summary"]["total_patients"] += footfall.total_patients
            changes["district_summary"]["total_emergency"] += footfall.emergency_cases
            
            # Generate or update bed occupancy - boosted by disease outbreak severity
            bed = db.query(BedOccupancy).filter(
                BedOccupancy.phc_id == request.phc_id,
                BedOccupancy.date == event_date
            ).first()
            
            if not bed:
                # Generate new bed data with outbreak-adjusted occupancy
                # Use stable reserved_beds for this PHC (not random per day)
                existing_bed = db.query(BedOccupancy).filter(
                    BedOccupancy.phc_id == request.phc_id
                ).first()
                if existing_bed:
                    reserved_beds_stable = existing_bed.reserved_beds
                else:
                    reserved_beds_stable = min(max(0, int(phc.total_beds * 0.1)), 2)
                
                seasonal = generator.generate_seasonal_factor(event_date)
                base_occupancy = random.uniform(0.65, 0.85) * seasonal * np.random.normal(1.0, 0.1)
                base_occupancy = max(0.5, min(0.98, base_occupancy))
                occupied = int(phc.total_beds * base_occupancy)
                reserved = reserved_beds_stable
                # Ensure occupied + reserved doesn't exceed total_beds
                occupied = min(occupied, phc.total_beds - reserved)
                occupied = max(0, occupied)
                available = max(0, phc.total_beds - occupied - reserved)
                occupancy_rate = round((occupied / phc.total_beds) * 100, 2) if phc.total_beds > 0 else 0
                
                bed = BedOccupancy(
                    phc_id=request.phc_id,
                    date=event_date,
                    total_beds=phc.total_beds,
                    occupied_beds=occupied,
                    reserved_beds=reserved,
                    available_beds=available,
                    occupancy_rate=occupancy_rate
                )
                db.add(bed)
            
            # Apply outbreak bed pressure: emergencies drive admissions more than general footfall
            # Scale occupied beds by severity_multiplier, weighted by emergency_cases proportion
            emergency_ratio = (footfall.emergency_cases / max(footfall.total_patients, 1))
            # More weight to emergency cases (they need beds directly)
            bed_pressure = 1.0 + (severity_multiplier - 1.0) * (0.3 + 0.7 * emergency_ratio)
            new_occupied = min(int(bed.occupied_beds * bed_pressure), bed.total_beds)
            new_reserved = bed.reserved_beds  # Keep reserved unchanged
            new_available = max(0, bed.total_beds - new_occupied - new_reserved)
            new_occupancy_rate = round((new_occupied / bed.total_beds) * 100, 2) if bed.total_beds > 0 else 0
            
            bed.occupied_beds = new_occupied
            bed.available_beds = max(0, new_available)
            bed.occupancy_rate = new_occupancy_rate
            
            changes["bed_changes"].append({
                "phc_id": request.phc_id,
                "phc_name": phc.name,
                "date": event_date.strftime("%Y-%m-%d"),
                "occupancy_rate": bed.occupancy_rate,
                "available_beds": bed.available_beds,
                "occupied_beds": bed.occupied_beds,
                "outbreak_adjustment": True
            })
            changes["district_summary"]["avg_bed_occupancy"] += bed.occupancy_rate
            
            # Generate or update doctor attendance - strain tracking
            attendance = db.query(DoctorAttendance).filter(
                DoctorAttendance.phc_id == request.phc_id,
                DoctorAttendance.date == event_date
            ).first()
            
            if not attendance:
                # Generate new attendance data (compute rate FROM headcount)
                base_attendance = random.uniform(0.78, 0.88)
                if event_date.weekday() == 0:
                    attendance_rate = max(0.6, min(0.98, base_attendance * 0.9))
                else:
                    attendance_rate = max(0.6, min(0.98, base_attendance * np.random.normal(1.0, 0.05)))
                present = int(phc.expected_doctors * attendance_rate)
                present = max(0, min(phc.expected_doctors, present))
                absent = phc.expected_doctors - present
                attendance_rate_pct = round((present / phc.expected_doctors) * 100, 2) if phc.expected_doctors > 0 else 0.0
                
                attendance = DoctorAttendance(
                    phc_id=request.phc_id,
                    date=event_date,
                    expected_doctors=phc.expected_doctors,
                    present_doctors=present,
                    absent_doctors=absent,
                    attendance_rate=attendance_rate_pct,
                    patient_load_per_doctor=round(footfall.total_patients / max(present, 1), 1),
                    reasons=""
                )
                db.add(attendance)
            else:
                # Keep present_doctors unchanged (doctors don't skip work in outbreaks)
                # But update patient_load_per_doctor to reflect strain
                attendance.patient_load_per_doctor = round(
                    footfall.total_patients / max(attendance.present_doctors, 1), 1
                )
            
            changes["attendance_changes"].append({
                "phc_id": request.phc_id,
                "phc_name": phc.name,
                "date": event_date.strftime("%Y-%m-%d"),
                "attendance_rate": attendance.attendance_rate,
                "absent_doctors": attendance.absent_doctors,
                "patient_load_per_doctor": attendance.patient_load_per_doctor,
                "present_doctors": attendance.present_doctors
            })
            changes["district_summary"]["avg_attendance"] += attendance.attendance_rate
            
            # Generate or update stock for each medicine
            medicines = db.query(Medicine).all()
            for medicine in medicines:
                stock = db.query(Stock).filter(
                    Stock.phc_id == request.phc_id,
                    Stock.medicine_id == medicine.id,
                    Stock.date == event_date
                ).first()
                
                # Initialize extra_usage for this medicine
                extra_usage = 0
                if request.event_type == "disease_outbreak":
                    extra_usage = int(medicine.base_daily_usage * 0.5 * severity_multiplier)
                
                if not stock:
                    # Get latest stock to calculate usage
                    latest_med_stock = db.query(Stock).filter(
                        Stock.phc_id == request.phc_id,
                        Stock.medicine_id == medicine.id
                    ).order_by(Stock.date.desc()).first()
                    
                    if latest_med_stock:
                        current_stock = latest_med_stock.quantity
                        # CRITICAL: Preserve pending restock from previous day
                        restock_arrives_on = latest_med_stock.restock_arrives_on
                        last_restocked = latest_med_stock.last_restocked
                    else:
                        current_stock = medicine.min_stock_threshold * 3
                        restock_arrives_on = None
                        last_restocked = None
                    
                    base_footfall = getattr(phc, 'base_footfall', None) or 80
                    base_usage = medicine.base_daily_usage * (base_footfall / 80)
                    daily_usage = int(base_usage * severity_multiplier) + extra_usage
                    new_stock = max(0, current_stock - daily_usage)
                    
                    # Check if a pending restock arrives today
                    if restock_arrives_on and restock_arrives_on <= event_date:
                        # Restock arrives - refill to 3x-5x threshold
                        new_stock = random.randint(medicine.min_stock_threshold * 3, medicine.min_stock_threshold * 5)
                        last_restocked = event_date
                        restock_arrives_on = None  # Clear the pending restock
                    elif new_stock < medicine.min_stock_threshold and not restock_arrives_on:
                        # Stock below threshold and no pending restock - order restock with 3-5 day delay
                        restock_delay = random.randint(3, 5)
                        restock_arrives_on = event_date + timedelta(days=restock_delay)
                    
                    stock = Stock(
                        phc_id=request.phc_id,
                        medicine_id=medicine.id,
                        date=event_date,
                        quantity=new_stock,
                        min_required=medicine.min_stock_threshold,
                        last_restocked=last_restocked,
                        restock_arrives_on=restock_arrives_on  # CRITICAL: Save the restock date
                    )
                    db.add(stock)
                else:
                    # Accelerate medicine usage for disease outbreak
                    if request.event_type == "disease_outbreak":
                        stock.quantity = max(0, stock.quantity - extra_usage)
                
                change_data = {
                    "phc_id": request.phc_id,
                    "phc_name": phc.name,
                    "medicine_id": medicine.id,
                    "medicine_name": medicine.name,
                    "date": event_date.strftime("%Y-%m-%d"),
                    "quantity": stock.quantity,
                    "change": -extra_usage if request.event_type == "disease_outbreak" else 0
                }
                
                # Add restock info if applicable
                if stock.restock_arrives_on:
                    change_data["restock_ordered"] = True
                    change_data["restock_arrives_on"] = stock.restock_arrives_on.strftime("%Y-%m-%d")
                
                changes["stock_changes"].append(change_data)
                changes["district_summary"]["total_stock_change"] += stock.quantity
            
            # Generate test availability
            tests = db.query(TestAvailability).filter(
                TestAvailability.phc_id == request.phc_id,
                TestAvailability.date == current_date
            ).all()
            
            for test in tests:
                is_available = random.random() < 0.9
                new_test = TestAvailability(
                    phc_id=request.phc_id,
                    test_name=test.test_name,
                    test_code=test.test_code,
                    date=event_date,
                    is_available=is_available,
                    equipment_status="functional" if is_available else "maintenance",
                    last_calibration_date=test.last_calibration_date,
                    notes=""
                )
                db.add(new_test)
                changes["test_changes"].append({
                    "phc_id": request.phc_id,
                    "phc_name": phc.name,
                    "test_name": test.test_name,
                    "date": event_date.strftime("%Y-%m-%d"),
                    "is_available": is_available
                })
        
        changes["message"] = f"Disease outbreak at {phc.name}: {severity_multiplier}x footfall increase for {request.duration_days} days"
    
    elif request.event_type == "delayed_resupply":
        # Simulate stock depletion without restock
        delay_days = {"low": 5, "medium": 10, "high": 15}.get(request.severity, 10)
        
        # Use this PHC's own latest date, not the global latest
        phc_latest_stock = db.query(Stock).filter(
            Stock.phc_id == request.phc_id
        ).order_by(Stock.date.desc()).first()
        phc_current_date = phc_latest_stock.date if phc_latest_stock else current_date
        
        for day in range(1, request.duration_days + 1):
            event_date = phc_current_date + timedelta(days=day)
            changes["new_dates"].append(event_date.strftime("%Y-%m-%d"))
            
            # Generate all data types for this date (footfall, beds, attendance, tests)
            # using _generate_day_for_phc, then override stock with depletion logic
            _generate_day_for_phc(db, phc, event_date, generator, changes, medicines_cache=db.query(Medicine).all())
            
            medicines = db.query(Medicine).all()
            for medicine in medicines:
                stock = db.query(Stock).filter(
                    Stock.phc_id == request.phc_id,
                    Stock.medicine_id == medicine.id,
                    Stock.date == event_date
                ).first()
                
                # Get previous day's stock as starting point
                prev_stock = db.query(Stock).filter(
                    Stock.phc_id == request.phc_id,
                    Stock.medicine_id == medicine.id,
                    Stock.date < event_date
                ).order_by(Stock.date.desc()).first()
                
                if prev_stock:
                    current_stock = prev_stock.quantity
                else:
                    current_stock = medicine.min_stock_threshold * 3
                
                # Aggressive depletion: 3x normal usage to simulate crisis demand
                base_usage = medicine.base_daily_usage * 2.5
                new_stock = max(0, current_stock - int(base_usage))
                
                if stock:
                    stock.quantity = new_stock
                    stock.restock_arrives_on = None  # Block restocks during delay
                else:
                    stock = Stock(
                        phc_id=request.phc_id,
                        medicine_id=medicine.id,
                        date=event_date,
                        quantity=new_stock,
                        min_required=medicine.min_stock_threshold,
                        last_restocked=prev_stock.last_restocked if prev_stock else None,
                        restock_arrives_on=None  # Block restocks during delay
                    )
                    db.add(stock)
                
                changes["stock_changes"].append({
                    "phc_id": request.phc_id,
                    "phc_name": phc.name,
                    "medicine_id": medicine.id,
                    "medicine_name": medicine.name,
                    "date": event_date.strftime("%Y-%m-%d"),
                    "quantity": new_stock,
                    "change": -int(base_usage)
                })
                changes["district_summary"]["total_stock_change"] += new_stock
        
        changes["message"] = f"Delayed resupply at {phc.name}: {delay_days} day delay simulated"
    
    elif request.event_type == "doctor_absence_spike":
        # Spike doctor absences
        absence_rate = {"low": 0.4, "medium": 0.6, "high": 0.8}.get(request.severity, 0.6)
        
        for day in range(request.duration_days):
            event_date = current_date + timedelta(days=day + 1)
            changes["new_dates"].append(event_date.strftime("%Y-%m-%d"))
            
            attendance = db.query(DoctorAttendance).filter(
                DoctorAttendance.phc_id == request.phc_id,
                DoctorAttendance.date == event_date
            ).first()
            
            if not attendance:
                # Generate new attendance data (compute rate FROM headcount)
                base_attendance = random.uniform(0.78, 0.88)
                if event_date.weekday() == 0:
                    attendance_rate = max(0.6, min(0.98, base_attendance * 0.9))
                else:
                    attendance_rate = max(0.6, min(0.98, base_attendance * np.random.normal(1.0, 0.05)))
                present = int(phc.expected_doctors * attendance_rate)
                present = max(0, min(phc.expected_doctors, present))
                absent = phc.expected_doctors - present
                attendance_rate_pct = round((present / phc.expected_doctors) * 100, 2) if phc.expected_doctors > 0 else 0.0
                
                attendance = DoctorAttendance(
                    phc_id=request.phc_id,
                    date=event_date,
                    expected_doctors=phc.expected_doctors,
                    present_doctors=present,
                    absent_doctors=absent,
                    attendance_rate=attendance_rate_pct,
                    reasons=""
                )
                db.add(attendance)
            
            # Apply absence spike (always recalculate from headcount)
            new_present = int(attendance.expected_doctors * (1 - absence_rate))
            new_present = max(0, min(attendance.expected_doctors, new_present))
            attendance.present_doctors = new_present
            attendance.absent_doctors = attendance.expected_doctors - new_present
            if attendance.expected_doctors > 0:
                attendance.attendance_rate = round((new_present / attendance.expected_doctors) * 100, 2)
            else:
                attendance.attendance_rate = 0.0
            
            changes["attendance_changes"].append({
                "phc_id": request.phc_id,
                "phc_name": phc.name,
                "date": event_date.strftime("%Y-%m-%d"),
                "attendance_rate": attendance.attendance_rate,
                "absent_doctors": attendance.absent_doctors
            })
            changes["district_summary"]["avg_attendance"] += attendance.attendance_rate
            
            # Also generate bed and footfall data for these dates if they don't exist
            footfall = db.query(Footfall).filter(
                Footfall.phc_id == request.phc_id,
                Footfall.date == event_date
            ).first()
            
            if not footfall:
                seasonal = generator.generate_seasonal_factor(event_date)
                weekly = generator.generate_weekly_factor(event_date)
                base_footfall = getattr(phc, 'base_footfall', None) or 80
                noise = np.random.normal(1.0, 0.15)
                total_patients = int(base_footfall * seasonal * weekly * noise)
                total_patients = max(20, min(200, total_patients))
                
                footfall = Footfall(
                    phc_id=request.phc_id,
                    date=event_date,
                    total_patients=total_patients,
                    new_patients=int(total_patients * random.uniform(0.3, 0.5)),
                    follow_up_patients=0,
                    emergency_cases=int(total_patients * random.uniform(0.05, 0.15))
                )
                footfall.follow_up_patients = total_patients - footfall.new_patients - footfall.emergency_cases
                db.add(footfall)
                
                changes["footfall_changes"].append({
                    "phc_id": request.phc_id,
                    "phc_name": phc.name,
                    "date": event_date.strftime("%Y-%m-%d"),
                    "total_patients": footfall.total_patients,
                    "emergency_cases": footfall.emergency_cases
                })
                changes["district_summary"]["total_patients"] += footfall.total_patients
                changes["district_summary"]["total_emergency"] += footfall.emergency_cases
            
            # Generate bed occupancy for this date if it doesn't exist
            bed = db.query(BedOccupancy).filter(
                BedOccupancy.phc_id == request.phc_id,
                BedOccupancy.date == event_date
            ).first()
            
            if not bed:
                existing_bed = db.query(BedOccupancy).filter(
                    BedOccupancy.phc_id == request.phc_id
                ).first()
                if existing_bed:
                    reserved_beds_stable = existing_bed.reserved_beds
                else:
                    reserved_beds_stable = min(max(0, int(phc.total_beds * 0.1)), 2)
                
                seasonal = generator.generate_seasonal_factor(event_date)
                base_occupancy = random.uniform(0.65, 0.85) * seasonal * np.random.normal(1.0, 0.1)
                base_occupancy = max(0.5, min(0.98, base_occupancy))
                occupied = int(phc.total_beds * base_occupancy)
                reserved = reserved_beds_stable
                occupied = min(occupied, phc.total_beds - reserved)
                occupied = max(0, occupied)
                available = max(0, phc.total_beds - occupied - reserved)
                occupancy_rate = round((occupied / phc.total_beds) * 100, 2) if phc.total_beds > 0 else 0
                
                bed = BedOccupancy(
                    phc_id=request.phc_id,
                    date=event_date,
                    total_beds=phc.total_beds,
                    occupied_beds=occupied,
                    reserved_beds=reserved,
                    available_beds=available,
                    occupancy_rate=occupancy_rate
                )
                db.add(bed)
            
            changes["bed_changes"].append({
                "phc_id": request.phc_id,
                "phc_name": phc.name,
                "date": event_date.strftime("%Y-%m-%d"),
                "occupancy_rate": bed.occupancy_rate,
                "available_beds": bed.available_beds
            })
            changes["district_summary"]["avg_bed_occupancy"] += bed.occupancy_rate
        
        changes["message"] = f"Doctor absence spike at {phc.name}: {absence_rate*100:.0f}% absenteeism for {request.duration_days} days"
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown event type: {request.event_type}")
    
    # Sync other PHCs: generate normal data for the same date range
    # so all PHCs advance together (same as advance_simulation_day)
    from app.database.schema import Medicine as _Med
    medicines_cache = db.query(_Med).all()
    other_phcs = db.query(PHC).filter(PHC.id != request.phc_id).all()
    for other_phc in other_phcs:
        # Find this PHC's latest date
        other_latest = db.query(Stock).filter(
            Stock.phc_id == other_phc.id
        ).order_by(Stock.date.desc()).first()
        if not other_latest:
            continue
        
        other_current_date = other_latest.date
        for day in range(request.duration_days):
            target_date = other_current_date + timedelta(days=day + 1)
            _generate_day_for_phc(db, other_phc, target_date, generator, changes, medicines_cache=medicines_cache)
    
    changes["district_summary"]["total_phcs_affected"] = db.query(PHC).count()
    
    db.commit()
    
    # Invalidate all caches since data has changed
    ml_manager.redistribution_engine.invalidate_cache()
    _invalidate_caches()
    
    # Calculate averages (only if we have data)
    if len(changes["attendance_changes"]) > 0:
        changes["district_summary"]["avg_attendance"] = round(changes["district_summary"]["avg_attendance"] / len(changes["attendance_changes"]), 2)
    if len(changes["bed_changes"]) > 0:
        changes["district_summary"]["avg_bed_occupancy"] = round(changes["district_summary"]["avg_bed_occupancy"] / len(changes["bed_changes"]), 2)
    
    return SimulationResponse(
        success=True,
        message=changes.get("message", f"Event {request.event_type} triggered successfully"),
        simulated_date=current_date + timedelta(days=request.duration_days),
        changes=changes
    )


@app.get("/api/dashboard/summary", response_model=DistrictSummary)
async def get_dashboard_summary(db: Session = Depends(get_db)):
    """Get district-wide dashboard summary - OPTIMIZED with caching"""
    from sqlalchemy import func
    from app.database.schema import Stock, Footfall, BedOccupancy, DoctorAttendance, TestAvailability
    
    # Get latest simulated date (not wall-clock date)
    latest_stock = db.query(Stock).order_by(Stock.date.desc()).first()
    if not latest_stock:
        raise HTTPException(status_code=400, detail="No data available")
    
    # Total PHCs
    total_phcs = db.query(PHC).count()
    phcs = db.query(PHC).all()
    
    # Load all data into dataframes (uses cache to avoid repeated loads)
    dfs = _get_cached_dataframes(db)
    stock_df = dfs['stock']
    footfall_df = dfs['footfall']
    bed_df = dfs['bed']
    attendance_df = dfs['attendance']
    test_df = dfs['test']
    
    # Compute district aggregates using each PHC's own latest date
    today_footfall = 0
    total_stockouts = 0
    attendance_rates = []
    bed_occupancy_rates = []
    test_availability_rates = []
    
    for p in phcs:
        pid = p.id
        # Latest footfall
        p_footfall = footfall_df[footfall_df['phc_id'] == pid]
        if len(p_footfall) > 0:
            latest_footfall = p_footfall.sort_values('date').iloc[-1]
            today_footfall += int(latest_footfall['total_patients'])
        
        # Latest stock
        p_stock = stock_df[stock_df['phc_id'] == pid]
        if len(p_stock) > 0:
            latest_stock_rows = p_stock[p_stock['date'] == p_stock['date'].max()]
            total_stockouts += int((latest_stock_rows['quantity'] < latest_stock_rows['min_required']).sum())
        
        # Latest attendance
        p_att = attendance_df[attendance_df['phc_id'] == pid]
        if len(p_att) > 0:
            attendance_rates.append(float(p_att.sort_values('date').iloc[-1]['attendance_rate']))
        
        # Latest bed occupancy
        p_beds = bed_df[bed_df['phc_id'] == pid]
        if len(p_beds) > 0:
            bed_occupancy_rates.append(float(p_beds.sort_values('date').iloc[-1]['occupancy_rate']))
        
        # Latest test availability
        p_tests = test_df[test_df['phc_id'] == pid]
        if len(p_tests) > 0:
            latest_tests = p_tests[p_tests['date'] == p_tests['date'].max()]
            test_availability_rates.append(float(latest_tests['is_available'].mean()) * 100)
    
    today_attendance = sum(attendance_rates) / len(attendance_rates) if attendance_rates else 0
    today_beds = sum(bed_occupancy_rates) / len(bed_occupancy_rates) if bed_occupancy_rates else 0
    avg_test_availability = sum(test_availability_rates) / len(test_availability_rates) if test_availability_rates else 0
    
    # Use cached health scores (avoids redundant recalculations)
    phc_scores = _get_phc_health_scores_cached(db, phcs)
    
    anomalies = ml_manager.anomaly_detector.detect_anomalies(phc_scores)
    
    critical_alerts = sum(1 for a in anomalies if a.get('severity') == 'critical')
    warning_alerts = sum(1 for a in anomalies if a.get('severity') in ['high', 'medium'])
    
    # Build alert count and severity map per PHC
    alert_count_map = {}
    alert_severity_map = {}
    for anomaly in anomalies:
        pid = anomaly.get('phc_id')
        if pid:
            alert_count_map[pid] = alert_count_map.get(pid, 0) + 1
            sev = anomaly.get('severity', 'low')
            if sev == 'critical':
                alert_severity_map[pid] = 'critical'
            elif sev == 'high' and alert_severity_map.get(pid) != 'critical':
                alert_severity_map[pid] = 'warning'
            elif pid not in alert_severity_map:
                alert_severity_map[pid] = 'warning'
    
    # PHC Health Scores - use cached scores, no need to recalculate
    phc_health_scores = []
    for phc in phcs:
        pid = phc.id
        # Find the score from cached results (calculate once, use everywhere)
        score = next((s for s in phc_scores if s['phc_id'] == pid), None)
        if score is None:
            continue
        
        health_score = score['health_score']
        if pid in alert_severity_map:
            status = alert_severity_map[pid]
        elif health_score >= 80:
            status = "good"
        elif health_score >= 60:
            status = "warning"
        else:
            status = "critical"
        
        # Footfall trend
        phc_footfall = footfall_df[footfall_df['phc_id'] == pid]
        if len(phc_footfall) >= 14:
            recent_7 = phc_footfall.tail(7)['total_patients'].mean()
            recent_14 = phc_footfall.tail(14)['total_patients'].mean()
            if recent_7 > recent_14 * 1.1:
                trend = "increasing"
            elif recent_7 < recent_14 * 0.9:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        # Get actual bed occupancy rate using this PHC's own latest date
        actual_bed_occupancy = 0.0
        phc_beds = bed_df[bed_df['phc_id'] == pid]
        if len(phc_beds) > 0:
            latest_bed_row = phc_beds.sort_values('date').iloc[-1]
            actual_bed_occupancy = latest_bed_row['occupancy_rate']
        
        # Get actual attendance rate using this PHC's own latest date
        actual_attendance_rate = 0.0
        phc_attendance = attendance_df[attendance_df['phc_id'] == pid]
        if len(phc_attendance) > 0:
            latest_attendance_row = phc_attendance.sort_values('date').iloc[-1]
            actual_attendance_rate = latest_attendance_row['attendance_rate']
        
        phc_health_scores.append(PHCHealthScore(
            phc_id=phc.id,
            phc_name=phc.name,
            phc_code=phc.code,
            health_score=health_score,
            stock_health=score['stock_health'],
            attendance_rate=actual_attendance_rate,
            bed_occupancy_rate=actual_bed_occupancy,
            test_availability_rate=score['test_availability_rate'],
            footfall_trend=trend,
            alert_count=alert_count_map.get(pid, 0),
            status=status
        ))
    
    # Compute district-wide average health score and simulated date
    avg_health_score = round(sum(s['health_score'] for s in phc_scores) / len(phc_scores), 2) if phc_scores else 0.0
    # Use the latest date from stock_df (handle both string and datetime types)
    if len(stock_df) > 0:
        latest_date_val = stock_df['date'].max()
        simulated_date_str = latest_date_val.strftime('%Y-%m-%d') if hasattr(latest_date_val, 'strftime') else str(latest_date_val)[:10]
    else:
        simulated_date_str = None
    
    return DistrictSummary(
        total_phcs=total_phcs,
        total_patients_today=int(today_footfall),
        total_stockouts=total_stockouts,
        avg_attendance_rate=round(float(today_attendance), 2),
        avg_bed_occupancy=round(float(today_beds), 2),
        avg_test_availability=round(avg_test_availability, 2),
        avg_health_score=avg_health_score,
        simulated_date=simulated_date_str,
        critical_alerts=critical_alerts,
        warning_alerts=warning_alerts,
        phc_health_scores=phc_health_scores
    )


@app.get("/api/simulation/status")
async def get_simulation_status(db: Session = Depends(get_db)):
    """Get simulation status - returns whether simulation is active based on latest date in database"""
    from app.database.schema import Stock
    
    # Get latest date in database
    latest_stock = db.query(Stock).order_by(Stock.date.desc()).first()
    
    if not latest_stock:
        return {
            "is_active": False,
            "latest_simulated_date": None,
            "original_seed_end_date": "2024-12-31",
            "message": "No data available"
        }
    
    latest_date = latest_stock.date
    
    # Original seed data ends on 2024-12-31 (from generator.py)
    original_seed_end = date(2024, 12, 31)
    
    # Simulation is active if latest date is beyond original seed end
    is_active = latest_date > original_seed_end
    
    return {
        "is_active": is_active,
        "latest_simulated_date": latest_date.strftime("%Y-%m-%d"),
        "original_seed_end_date": original_seed_end.strftime("%Y-%m-%d"),
        "message": f"Simulation active - data extends to {latest_date.strftime('%Y-%m-%d')}" if is_active else "Simulation inactive - showing original seed data"
    }


@app.get("/api/alerts", response_model=List[AlertItem])
async def get_alerts(db: Session = Depends(get_db)):
    """Get all active alerts - computed live from current data - OPTIMIZED with caching"""
    from app.database.schema import PHC, Stock
    
    # Get latest simulated date
    latest_stock = db.query(Stock).order_by(Stock.date.desc()).first()
    if not latest_stock:
        return []
    
    # Use cached health scores
    phcs = db.query(PHC).all()
    phc_scores = _get_phc_health_scores_cached(db, phcs)
    
    anomalies = ml_manager.anomaly_detector.detect_anomalies(phc_scores)
    
    # Convert to AlertItem format
    result = []
    for anomaly in anomalies:
        result.append(AlertItem(
            id=anomaly.get('id', 0),
            type=anomaly.get('anomaly_type', 'underperforming'),
            severity=anomaly.get('severity', 'medium'),
            phc_id=anomaly.get('phc_id', 0),
            phc_name=anomaly.get('phc_name', 'Unknown'),
            description=anomaly.get('description', ''),
            created_at=datetime.now(),
            is_resolved=False
        ))
    
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)