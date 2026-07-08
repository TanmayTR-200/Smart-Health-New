"""
ML Models for Smart Health PHC Management System
Includes:
1. Stock-out prediction (Prophet time-series)
2. Demand forecasting (footfall prediction)
3. Anomaly detection (underperforming PHCs)
4. Redistribution recommendation engine
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import json
from scipy.optimize import linprog
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

from app.services.gemini_service import generate_text

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    print("Warning: Prophet not available. Using simple moving average for forecasting.")


class PHCDataGenerator:
    """Generate realistic synthetic data for PHC operations during simulation"""
    
    def generate_seasonal_factor(self, date):
        """Generate seasonal multiplier based on month
        - Monsoon (Jun-Sep): 1.3x - malaria, dengue, waterborne diseases
        - Winter (Dec-Feb): 1.15x - respiratory diseases, influenza
        - Summer (Mar-May): 1.1x - heat-related, dehydration
        """
        month = date.month if isinstance(date, datetime) else pd.to_datetime(date).month
        
        if month in [6, 7, 8, 9]:
            return 1.3
        elif month in [12, 1, 2]:
            return 1.15
        elif month in [3, 4, 5]:
            return 1.1
        else:
            return 1.0
    
    def generate_weekly_factor(self, date):
        """Generate weekly pattern (lower on weekends - 30% lower attendance)"""
        dt = date if isinstance(date, datetime) else pd.to_datetime(date)
        if dt.weekday() >= 5:  # Saturday=5, Sunday=6
            return 0.7
        return 1.0


class StockoutPredictor:
    """Predict stock-out events using time-series forecasting"""
    
    def __init__(self):
        self.models = {}  # Cache for trained models
        self.model_version = "v1.0"
    
    def prepare_data(self, df: pd.DataFrame, phc_id: int, medicine_id: int) -> pd.DataFrame:
        """Prepare time-series data for Prophet"""
        mask = (df['phc_id'] == phc_id) & (df['medicine_id'] == medicine_id)
        data = df[mask].copy()
        data = data.sort_values('date')
        
        # Prophet requires columns: 'ds' (date) and 'y' (value)
        prophet_df = pd.DataFrame({
            'ds': pd.to_datetime(data['date']),
            'y': data['quantity']
        })
        
        return prophet_df
    
    def predict_stockout(self, df: pd.DataFrame, phc_id: int, medicine_id: int, 
                        min_threshold: int) -> Dict:
        """
        Predict days until stock-out for a specific PHC-medicine combination
        Returns prediction with confidence interval
        """
        prophet_df = self.prepare_data(df, phc_id, medicine_id)
        
        if len(prophet_df) < 30:
            return {
                "days_until_stockout": None,
                "confidence": 0.0,
                "recommended_action": "Insufficient data for prediction"
            }
        
        current_stock = prophet_df['y'].iloc[-1]
        
        # If already below threshold
        if current_stock < min_threshold:
            return {
                "days_until_stockout": 0,
                "confidence": 1.0,
                "recommended_action": "IMMEDIATE RESTOCKING REQUIRED"
            }
        
        # Use Prophet for forecasting
        if PROPHET_AVAILABLE:
            try:
                model = Prophet(
                    daily_seasonality=False,
                    weekly_seasonality=True,
                    yearly_seasonality=True,
                    changepoint_prior_scale=0.05
                )
                model.fit(prophet_df)
                
                # Forecast next 30 days
                future = model.make_future_dataframe(periods=30)
                forecast = model.predict(future)
                
                # Find when stock drops below threshold
                forecast_tail = forecast.tail(30)
                below_threshold = forecast_tail[forecast_tail['yhat'] < min_threshold]
                
                if len(below_threshold) > 0:
                    days_until_stockout = int((below_threshold.iloc[0]['ds'] - prophet_df['ds'].iloc[-1]).days)
                    confidence = 0.8
                else:
                    days_until_stockout = 30  # Safe for next 30 days
                    confidence = 0.7
                
                return {
                    "days_until_stockout": days_until_stockout,
                    "confidence": confidence,
                    "recommended_action": self._get_action_recommendation(days_until_stockout)
                }
                
            except Exception as e:
                print(f"Prophet error: {e}, falling back to simple method")
        
        # Fallback: Simple moving average method
        recent_avg = prophet_df['y'].tail(7).mean()
        if recent_avg > 0:
            days_until_stockout = int((current_stock - min_threshold) / recent_avg)
            days_until_stockout = max(0, days_until_stockout)
        else:
            days_until_stockout = 0
        
        return {
            "days_until_stockout": days_until_stockout,
            "confidence": 0.6,
            "recommended_action": self._get_action_recommendation(days_until_stockout)
        }
    
    def _get_action_recommendation(self, days: int) -> str:
        """Get recommended action based on days until stockout"""
        if days == 0:
            return "IMMEDIATE RESTOCKING REQUIRED"
        elif days <= 7:
            return "URGENT: Restock within 7 days"
        elif days <= 14:
            return "WARNING: Plan restock within 2 weeks"
        elif days <= 30:
            return "MONITOR: Schedule restock within month"
        else:
            return "OK: Stock sufficient for 30+ days"


class DemandForecaster:
    """Forecast patient footfall demand"""
    
    def __init__(self):
        self.model_version = "v1.0"
    
    def forecast_footfall(self, df: pd.DataFrame, phc_id: int, days: int = 7) -> Dict:
        """
        Forecast footfall for next N days
        Uses simple trend + seasonal pattern
        """
        phc_data = df[df['phc_id'] == phc_id].copy()
        phc_data = phc_data.sort_values('date')
        
        if len(phc_data) < 14:
            return {
                "predicted_footfall": 0,
                "confidence_lower": 0,
                "confidence_upper": 0,
                "trend": "insufficient_data"
            }
        
        # Calculate recent average and trend
        recent_7 = phc_data.tail(7)['total_patients'].mean()
        recent_14 = phc_data.tail(14)['total_patients'].mean()
        
        # Simple trend detection
        if recent_7 > recent_14 * 1.1:
            trend = "increasing"
            trend_factor = 1.05
        elif recent_7 < recent_14 * 0.9:
            trend = "decreasing"
            trend_factor = 0.95
        else:
            trend = "stable"
            trend_factor = 1.0
        
        # Seasonal adjustment (simplified) - use latest data date, not wall-clock
        if len(phc_data) > 0:
            latest_data_date = pd.to_datetime(phc_data['date'].iloc[-1])
            current_month = latest_data_date.month
        else:
            current_month = datetime.now().month
        seasonal_factor = 1.0
        if current_month in [6, 7, 8, 9]:  # Monsoon
            seasonal_factor = 1.3
        elif current_month in [12, 1, 2]:  # Winter
            seasonal_factor = 1.15
        
        # Forecast
        base_prediction = recent_7 * trend_factor * seasonal_factor
        predicted = int(base_prediction)
        
        # Confidence interval (±20%)
        confidence_lower = int(predicted * 0.8)
        confidence_upper = int(predicted * 1.2)
        
        return {
            "predicted_footfall": predicted,
            "confidence_lower": confidence_lower,
            "confidence_upper": confidence_upper,
            "trend": trend
        }


class AnomalyDetector:
    """Detect underperforming PHCs using anomaly detection"""
    
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        self.model_version = "v1.0"
    
    def calculate_phc_health_score(self, phc_id: int, stock_df: pd.DataFrame, 
                                   attendance_df: pd.DataFrame, 
                                   bed_df: pd.DataFrame, footfall_df: pd.DataFrame,
                                   test_df: Optional[pd.DataFrame] = None) -> Dict:
        """
        Calculate composite health score for a PHC
        Score components:
        - Stock reliability (35%)
        - Doctor attendance (25%)
        - Bed utilization efficiency (20%)
        - Test availability (20%)
        """
        # Create copies to avoid modifying original dataframes
        stock_df = stock_df.copy()
        attendance_df = attendance_df.copy()
        bed_df = bed_df.copy()
        footfall_df = footfall_df.copy()
        if test_df is not None:
            test_df = test_df.copy()
        
        # Convert date columns to datetime if they're strings
        stock_df['date'] = pd.to_datetime(stock_df['date'])
        attendance_df['date'] = pd.to_datetime(attendance_df['date'])
        bed_df['date'] = pd.to_datetime(bed_df['date'])
        footfall_df['date'] = pd.to_datetime(footfall_df['date'])
        if test_df is not None:
            test_df['date'] = pd.to_datetime(test_df['date'])
        
        # Get recent data (last 30 days from latest simulated date, not wall-clock)
        # Use the latest date from each relevant data source
        latest_stock_date = stock_df['date'].max() if len(stock_df) > 0 else datetime.now()
        latest_attendance_date = attendance_df['date'].max() if len(attendance_df) > 0 else datetime.now()
        latest_bed_date = bed_df['date'].max() if len(bed_df) > 0 else datetime.now()
        latest_footfall_date = footfall_df['date'].max() if len(footfall_df) > 0 else datetime.now()
        
        # Use the overall latest date for consistency
        latest_date = max(latest_stock_date, latest_attendance_date, latest_bed_date, latest_footfall_date)
        cutoff_date = latest_date - timedelta(days=14)
        
        # Stock health: percentage of medicines ABOVE minimum threshold RIGHT NOW
        # Use ONLY the LATEST record per PHC+medicine (not an average over 30 days!)
        recent_stock = stock_df[
            (stock_df['phc_id'] == phc_id) & 
            (stock_df['date'] >= cutoff_date)
        ]
        
        if len(recent_stock) > 0:
            # Get only the latest record for each PHC+medicine combination
            latest_per_medicine = recent_stock.sort_values('date').groupby(['phc_id', 'medicine_id']).last().reset_index()
            medicines_above_threshold = (latest_per_medicine['quantity'] >= latest_per_medicine['min_required']).sum()
            total_medicines = len(latest_per_medicine)
            stock_health = (medicines_above_threshold / total_medicines * 100) if total_medicines > 0 else 50.0
        else:
            stock_health = 50.0
        
        # Attendance health: combines headcount rate with patient load (strain)
        recent_attendance = attendance_df[
            (attendance_df['phc_id'] == phc_id) & 
            (attendance_df['date'] >= cutoff_date)
        ]
        
        if len(recent_attendance) > 0:
            # Base attendance rate from headcount
            attendance_health = recent_attendance['attendance_rate'].mean()
            
            # Penalize for overworked doctors: compare patient_load_per_doctor vs normal
            # Normal load is ~30-40 patients per doctor per day at average PHC
            # If patient_load_per_doctor is recorded, factor it in
            if 'patient_load_per_doctor' in recent_attendance.columns:
                latest_att = recent_attendance.sort_values('date').iloc[-1]
                patient_load = latest_att.get('patient_load_per_doctor')
                if patient_load is not None and patient_load > 0:
                    normal_load = 35  # baseline: ~35 patients per doctor per day
                    load_ratio = patient_load / normal_load
                    if load_ratio > 1.0:
                        # Each 10% above normal load reduces attendance health by 5 points
                        overload_penalty = min((load_ratio - 1.0) * 50, 30)
                        attendance_health = max(0, attendance_health - overload_penalty)
        else:
            attendance_health = 75.0
        
        # Bed utilization health (optimal is 70-85%)
        recent_beds = bed_df[
            (bed_df['phc_id'] == phc_id) & 
            (bed_df['date'] >= cutoff_date)
        ]
        
        if len(recent_beds) > 0:
            avg_occupancy = recent_beds['occupancy_rate'].mean()
            # Score is highest when occupancy is 70-85%
            if 70 <= avg_occupancy <= 85:
                bed_health = 100.0
            elif avg_occupancy < 70:
                bed_health = 70.0 + (avg_occupancy / 70) * 30
            else:  # > 85%
                bed_health = max(0, 100 - (avg_occupancy - 85) * 5)
            actual_bed_occupancy = avg_occupancy
        else:
            bed_health = 75.0
            actual_bed_occupancy = 0.0
        
        # Test availability health
        if test_df is not None and len(test_df) > 0:
            recent_tests = test_df[
                (test_df['phc_id'] == phc_id) & 
                (test_df['date'] >= cutoff_date)
            ]
            if len(recent_tests) > 0:
                test_availability_rate = recent_tests['is_available'].mean() * 100
            else:
                test_availability_rate = 75.0
        else:
            test_availability_rate = 75.0
        
        # Composite score (weighted)
        health_score = (
            stock_health * 0.35 +
            attendance_health * 0.25 +
            bed_health * 0.20 +
            test_availability_rate * 0.20
        )
        
        return {
            "health_score": round(health_score, 2),
            "stock_health": round(stock_health, 2),
            "attendance_rate": round(attendance_health, 2),
            "bed_occupancy_rate": round(actual_bed_occupancy, 2),  # Actual occupancy, not health score
            "test_availability_rate": round(test_availability_rate, 2)
        }
    
    def detect_anomalies(self, phc_scores: List[Dict]) -> List[Dict]:
        """
        Detect anomalous PHCs based on health scores.
        Flags any PHC whose health score is below the district average.
        """
        if len(phc_scores) < 2:
            return []

        avg_health = sum(s['health_score'] for s in phc_scores) / len(phc_scores)

        anomalies = []
        for score_dict in phc_scores:
            health_score = score_dict['health_score']
            if health_score < avg_health:
                # Determine severity based on how far below average
                gap = avg_health - health_score
                if health_score < 60:
                    severity = "critical"
                elif gap >= 10:
                    severity = "high"
                elif gap >= 3:
                    severity = "medium"
                else:
                    severity = "low"

                # Generate description based on weak areas
                weak_areas = []
                if score_dict['stock_health'] < 70:
                    weak_areas.append("stock management")
                if score_dict['attendance_rate'] < 75:
                    weak_areas.append("doctor attendance")
                if score_dict['bed_occupancy_rate'] < 60:
                    weak_areas.append("bed utilization")
                if score_dict['test_availability_rate'] < 75:
                    weak_areas.append("diagnostic test availability")

                description = f"PHC health score ({health_score:.1f}) below district average ({avg_health:.1f})"
                if weak_areas:
                    description += f". Weak areas: {', '.join(weak_areas)}"

                anomalies.append({
                    "phc_id": score_dict['phc_id'],
                    "phc_name": score_dict['phc_name'],
                    "phc_code": score_dict['phc_code'],
                    "anomaly_type": "underperforming",
                    "severity": severity,
                    "score": round(health_score, 2),
                    "anomaly_score": round(gap, 2),
                    "description": description,
                    "details": score_dict
                })

        return anomalies


class RedistributionEngine:
    """Optimize resource redistribution across PHCs"""
    
    def __init__(self):
        self.model_version = "v1.0"
        self._cached_recommendations = None
        self._cache_timestamp = None
        self._cache_ttl = 3600  # Cache for 1 hour (in seconds)
    
    def find_redistribution_opportunities(self, stock_df: pd.DataFrame, 
                                          predictions: Dict[int, Dict],
                                          phcs: List[Dict]) -> List[Dict]:
        """
        Find optimal redistribution recommendations
        Strategy:
        1. Identify PHCs with excess stock (stock > 3x threshold)
        2. Identify PHCs with critical stock (stock < 1.5x threshold or predicted stockout < 7 days)
        3. Calculate optimal transfer quantities
        
        NOTE: Cache is DISABLED by default because stock levels change frequently.
        Enable only if you need to reduce computation time for large datasets.
        """
        import time
        
        # DISABLE CACHE: Always recalculate to ensure recommendations match current stock levels
        # The cache was causing recommendations to show excess stock that no longer exists
        # But preserve Gemini-generated reasons across calls if recommendations haven't changed
        prev_recommendations = self._cached_recommendations
        self._cached_recommendations = None
        self._cache_timestamp = None
        
        recommendations = []
        
        # Get latest stock data — use per-PHC latest dates (not global max)
        # so PHCs at different simulation dates are all included
        latest_stock = stock_df.sort_values('date').groupby(['phc_id', 'medicine_id']).last().reset_index()
        
        # For each medicine, find redistribution opportunities
        medicines = stock_df['medicine_id'].unique()
        
        # Track district-wide aggregate: PHC IDs that have deficit for ANY medicine
        district_deficit_phcs = set()
        district_excess_phcs = set()
        
        for medicine_id in medicines:
            medicine_stock = latest_stock[latest_stock['medicine_id'] == medicine_id]
            
            if len(medicine_stock) == 0:
                continue
            
            # Get medicine details
            medicine_info = medicine_stock.iloc[0]
            min_threshold = medicine_info['min_required']
            
            # Find PHCs with excess and deficit
            excess_phcs = []
            deficit_phcs = []
            
            for _, row in medicine_stock.iterrows():
                phc_id = row['phc_id']
                current_stock = row['quantity']
                stock_ratio = current_stock / min_threshold if min_threshold > 0 else 0
                
                # Check prediction
                pred = predictions.get(phc_id, {})
                days_until_stockout = pred.get('days_until_stockout', 999)
                
                # Check if there's a pending restock
                restock_arrives_on = row.get('restock_arrives_on', None)
                has_pending_restock = pd.notna(restock_arrives_on) if restock_arrives_on else False
                
                if stock_ratio > 2.0:  # Excess stock (> 2x threshold)
                    # Calculate actual excess above safety reserve (1.5x threshold)
                    actual_excess = int(current_stock - (min_threshold * 1.5))
                    if actual_excess > 0:  # Only include if there's actual surplus to transfer
                        district_excess_phcs.add(phc_id)
                        excess_phcs.append({
                            'phc_id': phc_id,
                            'stock': current_stock,
                            'ratio': stock_ratio,
                            'excess': actual_excess,
                            'has_pending_restock': has_pending_restock
                        })
                elif stock_ratio < 1.0:  # Below 1x threshold — needs restock
                    # Calculate need to bring back to 1x threshold
                    need_amount = int(min_threshold - current_stock)
                    if need_amount > 0:
                        district_deficit_phcs.add(phc_id)
                        deficit_phcs.append({
                            'phc_id': phc_id,
                            'stock': current_stock,
                            'ratio': stock_ratio,
                            'need': need_amount,
                            'days_until_stockout': days_until_stockout,
                            'has_pending_restock': has_pending_restock,
                            'restock_arrives_on': restock_arrives_on
                        })
            
            # Match excess with deficit — one deficit should only be covered once
            for deficit in deficit_phcs:
                if deficit['need'] <= 0:
                    continue
                for excess in excess_phcs:
                    if excess['excess'] <= 0 or deficit['need'] <= 0:
                        continue
                    
                    # Calculate transfer quantity
                    transfer_qty = min(excess['excess'], deficit['need'])
                    transfer_qty = max(0, transfer_qty)
                    
                    if transfer_qty > 0:
                        # Determine priority
                        if deficit['days_until_stockout'] <= 3:
                            priority = "critical"
                        elif deficit['days_until_stockout'] <= 7:
                            priority = "high"
                        else:
                            priority = "medium"
                        
                        # Get PHC names
                        from_phc = next((p for p in phcs if p['id'] == excess['phc_id']), {})
                        to_phc = next((p for p in phcs if p['id'] == deficit['phc_id']), {})
                        
                        # Get actual stock values for more specific messaging
                        source_stock = excess['stock']  # key is 'stock' not 'current_stock'
                        source_excess = excess['excess']  # surplus above 2x threshold
                        dest_stock = deficit['stock']  # key is 'stock' not 'current_stock'
                        deficit_ratio = deficit['ratio']  # how depleted they are
                        days_until_stockout = deficit.get('days_until_stockout', 'unknown')
                        
                        # Calculate surplus: how much above 2x threshold (conservative - keeps 2x reserve)
                        surplus = source_excess  # already calculated as current_stock - (min_threshold * 2)
                        
                        # Build specific, data-driven reason text
                        reason_parts = []
                        reason_parts.append(f"{to_phc.get('name', 'Destination')} has {dest_stock} units remaining")
                        if days_until_stockout and days_until_stockout != 'unknown':
                            reason_parts.append(f"with {days_until_stockout} days until stockout at current usage")
                        reason_parts.append(f"({deficit['ratio']:.1f}x of threshold)")
                        
                        # Add urgency if there's a pending restock
                        if deficit.get('has_pending_restock') and deficit.get('restock_arrives_on'):
                            reason_parts.append(f"[RESTOCK PENDING - arrives {deficit['restock_arrives_on']}]")
                        
                        impact_parts = []
                        impact_parts.append(f"Transferring {transfer_qty} units from {from_phc.get('name', 'Source')}")
                        impact_parts.append(f"(surplus: {surplus} units above safety reserve)")
                        
                        fallback_reason = "; ".join(reason_parts)
                        fallback_impact = ". ".join(impact_parts) + "."
                        
                        recommendations.append({
                            "from_phc_id": excess['phc_id'],
                            "from_phc_name": from_phc.get('name', f"PHC-{excess['phc_id']}"),
                            "to_phc_id": deficit['phc_id'],
                            "to_phc_name": to_phc.get('name', f"PHC-{deficit['phc_id']}"),
                            "medicine_id": medicine_id,
                            "medicine_name": f"Medicine-{medicine_id}",  # Will be enriched later
                            "quantity": transfer_qty,
                            "urgency": priority,
                            "reason": fallback_reason,
                            "impact": fallback_impact,
                        })
                        
                        # Decrement so the same deficit isn't covered twice
                        excess['excess'] -= transfer_qty
                        deficit['need'] -= transfer_qty
        
        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda x: priority_order.get(x['urgency'], 4))
        
        # Gemini API: only call if recommendations changed (saves quota)
        def _rec_key(recs):
            """Build a fingerprint of recommendation identities for cache comparison"""
            return tuple((r['from_phc_id'], r['to_phc_id'], r['medicine_id'], r['quantity']) for r in recs)
        
        current_key = _rec_key(recommendations)
        prev_key = _rec_key(prev_recommendations) if prev_recommendations else None
        gemini_cached_reasons = {}
        
        if prev_key and current_key == prev_key:
            # Recommendations identical — reuse previous Gemini reasons
            for i, rec in enumerate(recommendations):
                if i < len(prev_recommendations) and prev_recommendations[i].get('_gemini_reason'):
                    rec['reason'] = prev_recommendations[i]['_gemini_reason']
                    rec['_gemini_reason'] = prev_recommendations[i]['_gemini_reason']
            print("[GEMINI] Recommendations unchanged — reusing cached reasons")
        elif recommendations:
            # Recommendations changed — call Gemini once for all
            try:
                lines = []
                for i, rec in enumerate(recommendations, 1):
                    lines.append(
                        f"{i}. Transfer {rec['quantity']} units of Medicine-{rec['medicine_id']} "
                        f"from {rec['from_phc_name']} to {rec['to_phc_name']}. "
                        f"Urgency: {rec['urgency']}. {rec['reason']}"
                    )
                prompt = (
                    "You are a district health logistics advisor. For each transfer below, write a "
                    "concise 1-sentence reason why it makes sense. Number each line to match. "
                    "Return ONLY the numbered lines, no extra text.\n\n"
                    + "\n".join(lines)
                )
                ai_text = generate_text(prompt, max_retries=1, timeout_seconds=8, fallback=None)
                if ai_text:
                    import re
                    for match in re.finditer(r'(\d+)\.\s*(.+)', ai_text):
                        idx = int(match.group(1)) - 1
                        if 0 <= idx < len(recommendations):
                            recommendations[idx]["reason"] = match.group(2).strip()
                            recommendations[idx]["_gemini_reason"] = match.group(2).strip()
                else:
                    for rec in recommendations:
                        rec["_gemini_reason"] = rec["reason"]
            except Exception as e:
                print(f"[GEMINI] Batched redistribution reasoning failed: {e}")
                for rec in recommendations:
                    rec["_gemini_reason"] = rec["reason"]
        
        # Determine district-wide state across ALL medicines
        self._cached_analysis = {
            "excess_count": len(district_excess_phcs),
            "deficit_count": len(district_deficit_phcs),
            "has_excess": len(district_excess_phcs) > 0,
            "has_deficit": len(district_deficit_phcs) > 0,
            "total_recommendations": len(recommendations)
        }
        
        # Cache the recommendations
        self._cached_recommendations = recommendations
        self._cache_timestamp = time.time()
        print(f"[CACHE] Cached {len(recommendations)} recommendations")
        
        return recommendations
    
    def invalidate_cache(self):
        """Invalidate the cached recommendations (call after executing transfers)"""
        self._cached_recommendations = None
        self._cache_timestamp = None
        print("[CACHE] Cache invalidated")
    
    def optimize_redistribution_linear_programming(self, stock_df: pd.DataFrame,
                                                    min_thresholds: Dict[int, int],
                                                    phcs: List[Dict]) -> List[Dict]:
        """
        Advanced: Use linear programming for optimal redistribution
        Minimize total shortage across all PHCs
        """
        # This is a simplified version - full LP would consider transportation costs
        return self.find_redistribution_opportunities(stock_df, {}, phcs)


class MLModelManager:
    """Manager class to coordinate all ML models"""
    
    def __init__(self):
        self.stockout_predictor = StockoutPredictor()
        self.demand_forecaster = DemandForecaster()
        self.anomaly_detector = AnomalyDetector()
        self.redistribution_engine = RedistributionEngine()
    
    def run_all_predictions(self, db_session, phc_id: Optional[int] = None) -> Dict:
        """
        Run all ML models and return comprehensive predictions
        """
        from app.database.schema import Stock, Footfall, BedOccupancy, DoctorAttendance, PHC, Medicine, TestAvailability
        
        # Load data
        stock_query = db_session.query(Stock)
        if phc_id:
            stock_query = stock_query.filter(Stock.phc_id == phc_id)
        stock_df = pd.read_sql(stock_query.statement, db_session.bind)
        
        footfall_query = db_session.query(Footfall)
        if phc_id:
            footfall_query = footfall_query.filter(Footfall.phc_id == phc_id)
        footfall_df = pd.read_sql(footfall_query.statement, db_session.bind)
        
        bed_query = db_session.query(BedOccupancy)
        if phc_id:
            bed_query = bed_query.filter(BedOccupancy.phc_id == phc_id)
        bed_df = pd.read_sql(bed_query.statement, db_session.bind)
        
        attendance_query = db_session.query(DoctorAttendance)
        if phc_id:
            attendance_query = attendance_query.filter(DoctorAttendance.phc_id == phc_id)
        attendance_df = pd.read_sql(attendance_query.statement, db_session.bind)
        
        test_query = db_session.query(TestAvailability)
        if phc_id:
            test_query = test_query.filter(TestAvailability.phc_id == phc_id)
        test_df = pd.read_sql(test_query.statement, db_session.bind)
        
        phcs = db_session.query(PHC).all()
        phcs_list = [{"id": p.id, "name": p.name, "code": p.code} for p in phcs]
        
        medicines = db_session.query(Medicine).all()
        medicine_map = {m.id: m.name for m in medicines}
        
        # 1. Stock-out predictions
        print("Running stock-out predictions...")
        stockout_predictions = []
        for phc in phcs:
            for medicine in medicines:
                pred = self.stockout_predictor.predict_stockout(
                    stock_df, phc.id, medicine.id, medicine.min_stock_threshold
                )
                if pred['days_until_stockout'] is not None and pred['days_until_stockout'] <= 14:
                    stockout_predictions.append({
                        "phc_id": phc.id,
                        "phc_name": phc.name,
                        "medicine_id": medicine.id,
                        "medicine_name": medicine.name,
                        "current_stock": int(stock_df[
                            (stock_df['phc_id'] == phc.id) & 
                            (stock_df['medicine_id'] == medicine.id)
                        ]['quantity'].iloc[-1]) if len(stock_df) > 0 else 0,
                        **pred
                    })
        
        # 2. Demand forecasts
        print("Running demand forecasts...")
        demand_forecasts = []
        for phc in phcs:
            forecast = self.demand_forecaster.forecast_footfall(footfall_df, phc.id)
            forecast['phc_id'] = phc.id
            forecast['phc_name'] = phc.name
            demand_forecasts.append(forecast)
        
        # 3. Anomaly detection
        print("Running anomaly detection...")
        phc_health_scores = []
        for phc in phcs:
            score = self.anomaly_detector.calculate_phc_health_score(
                phc.id, stock_df, attendance_df, bed_df, footfall_df, test_df
            )
            score['phc_id'] = phc.id
            score['phc_name'] = phc.name
            score['phc_code'] = phc.code
            phc_health_scores.append(score)
        
        anomalies = self.anomaly_detector.detect_anomalies(phc_health_scores)
        
        # 4. Redistribution recommendations
        print("Finding redistribution opportunities...")
        predictions_map = {p['phc_id']: p for p in stockout_predictions}
        redistribution = self.redistribution_engine.find_redistribution_opportunities(
            stock_df, predictions_map, phcs_list
        )
        
        # Enrich with medicine names
        for rec in redistribution:
            rec['medicine_name'] = medicine_map.get(rec['medicine_id'], f"Medicine-{rec['medicine_id']}")
        
        return {
            "stockout_predictions": stockout_predictions,
            "demand_forecasts": demand_forecasts,
            "phc_health_scores": phc_health_scores,
            "anomalies": anomalies,
            "redistribution_recommendations": redistribution
        }