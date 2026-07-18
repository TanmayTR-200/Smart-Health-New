"""
Pydantic schemas for API request/response models
"""
from pydantic import BaseModel, Field
from datetime import datetime, date as date_type
from typing import Optional, List, Dict, Any, Union


# PHC Schemas
class PHCBase(BaseModel):
    name: str
    code: str
    type: str
    district: str
    total_beds: int
    expected_doctors: int
    base_footfall: int = 80
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class PHCResponse(PHCBase):
    id: int
    created_at: datetime
    health_score: Optional[float] = None
    status: Optional[str] = None
    
    class Config:
        from_attributes = True


# Medicine Schemas
class MedicineBase(BaseModel):
    name: str
    code: str
    category: str
    unit: str
    min_stock_threshold: int
    base_daily_usage: int = 20


class MedicineResponse(MedicineBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Stock Schemas
class StockBase(BaseModel):
    phc_id: int
    medicine_id: int
    date: date_type
    quantity: int
    min_required: int
    last_restocked: Optional[date_type] = None


class StockResponse(StockBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class StockWithDetails(StockResponse):
    phc_name: str
    medicine_name: str
    medicine_code: str
    days_remaining: Optional[int] = None


# Footfall Schemas
class FootfallBase(BaseModel):
    phc_id: int
    date: date_type
    total_patients: int
    new_patients: Optional[int] = None
    follow_up_patients: Optional[int] = None
    emergency_cases: Optional[int] = None


class FootfallResponse(FootfallBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Bed Occupancy Schemas
class BedOccupancyBase(BaseModel):
    phc_id: int
    date: date_type
    total_beds: int
    occupied_beds: int
    reserved_beds: int = 0
    available_beds: int
    occupancy_rate: float


class BedOccupancyResponse(BedOccupancyBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Doctor Attendance Schemas
class DoctorAttendanceBase(BaseModel):
    phc_id: int
    date: date_type
    expected_doctors: int
    present_doctors: int
    absent_doctors: int
    attendance_rate: float
    patient_load_per_doctor: Optional[float] = None
    reasons: Optional[str] = None


class DoctorAttendanceResponse(DoctorAttendanceBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Test Availability Schemas
class TestAvailabilityBase(BaseModel):
    phc_id: int
    test_name: str
    test_code: str
    date: date_type
    is_available: bool
    equipment_status: str = "functional"
    last_calibration_date: Optional[date_type] = None
    notes: Optional[str] = None


class TestAvailabilityResponse(TestAvailabilityBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class TestAvailabilityWithPHC(TestAvailabilityResponse):
    phc_name: str
    phc_code: str


# Prediction Schemas
class PredictionBase(BaseModel):
    phc_id: int
    prediction_type: str
    prediction_date: date_type
    target_date: date_type
    predicted_value: float
    confidence_lower: Optional[float] = None
    confidence_upper: Optional[float] = None
    model_version: Optional[str] = None


class PredictionResponse(PredictionBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Anomaly Schemas
class AnomalyBase(BaseModel):
    phc_id: int
    anomaly_date: date_type
    anomaly_type: str
    severity: str
    score: float
    description: Optional[str] = None
    is_resolved: bool = False


class AnomalyResponse(AnomalyBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class AnomalyWithPHC(AnomalyResponse):
    phc_name: str
    phc_code: str


# Redistribution Recommendation Schemas
class RedistributionBase(BaseModel):
    from_phc_id: int
    to_phc_id: int
    medicine_id: int
    recommended_quantity: int
    reason: Optional[str] = None
    priority: str
    status: str = "pending"


class RedistributionResponse(RedistributionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RedistributionWithDetails(RedistributionResponse):
    from_phc_name: str
    to_phc_name: str
    medicine_name: str
    medicine_code: str


# Dashboard Summary Schemas
class PHCHealthScore(BaseModel):
    phc_id: int
    phc_name: str
    phc_code: str
    health_score: float  # 0-100
    stock_health: float
    attendance_rate: float
    bed_occupancy_rate: float
    test_availability_rate: float
    footfall_trend: str  # increasing, decreasing, stable
    alert_count: int
    status: str  # good, warning, critical


class DistrictSummary(BaseModel):
    total_phcs: int
    total_patients_today: int
    total_stockouts: int
    avg_attendance_rate: float
    avg_bed_occupancy: float
    avg_test_availability: float
    avg_health_score: float = 0.0
    simulated_date: Optional[str] = None
    critical_alerts: int
    warning_alerts: int
    phc_health_scores: List[PHCHealthScore]


class AlertItem(BaseModel):
    id: int
    type: str  # stockout, underperforming, attendance, bed_shortage, test_unavailable
    severity: str
    phc_id: int
    phc_name: str
    description: str
    created_at: datetime
    is_resolved: bool
    method: Optional[str] = None


# ML Model Response Schemas
class StockoutPredictionResponse(BaseModel):
    phc_id: int
    phc_name: str
    medicine_id: int
    medicine_name: str
    current_stock: int
    days_until_stockout: float
    confidence: float
    method: str
    recommended_action: str


class DemandForecastResponse(BaseModel):
    phc_id: int
    phc_name: str
    forecast_date: Optional[date_type] = None
    predicted_footfall: int
    confidence_lower: int
    confidence_upper: int
    trend: str
    method: str


class RedistributionSuggestion(BaseModel):
    from_phc_id: int
    from_phc_name: str
    to_phc_id: int
    to_phc_name: str
    medicine_id: int
    medicine_name: str
    quantity: int
    urgency: str
    reason: str
    impact: str
    method: str


# Simulation Schemas
class SimulationAdvanceRequest(BaseModel):
    phc_id: Optional[int] = None
    days: int = 1


class SimulationEventRequest(BaseModel):
    event_type: str  # disease_outbreak, delayed_resupply, doctor_absence_spike
    phc_id: int
    duration_days: int = 3
    severity: str = "medium"  # low, medium, high
    parameters: Optional[Dict[str, Any]] = {}


class SimulationResponse(BaseModel):
    success: bool
    message: str
    simulated_date: date_type
    changes: Dict[str, Any]


# Generic Response
class MessageResponse(BaseModel):
    message: str
    success: bool = True