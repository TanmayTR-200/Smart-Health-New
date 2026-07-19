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
    # Verify Prophet actually works (not just importable)
    _test = Prophet()
    PROPHET_AVAILABLE = True
except Exception:
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
        self._prediction_cache = {}  # (phc_id, medicine_id, latest_date) -> prediction dict
    
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
        Predict days until stock-out for a specific PHC-medicine combination.
        Uses caching: refits Prophet only when latest data date changes.
        """
        prophet_df = self.prepare_data(df, phc_id, medicine_id)
        
        if len(prophet_df) < 30:
            return {
                "days_until_stockout": None,
                "confidence": 0.0,
                "method": "insufficient_data",
                "recommended_action": "Insufficient data for prediction"
            }
        
        current_stock = prophet_df['y'].iloc[-1]
        latest_date = prophet_df['ds'].iloc[-1]
        
        # If already below threshold
        if current_stock < min_threshold:
            return {
                "days_until_stockout": 0,
                "confidence": 1.0,
                "method": "threshold_check",
                "recommended_action": "IMMEDIATE RESTOCKING REQUIRED"
            }
        
        # Check prediction cache — refit only when latest_date changes
        cache_key = (phc_id, medicine_id, str(latest_date))
        if cache_key in self._prediction_cache:
            return dict(self._prediction_cache[cache_key])
        
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
                
                result = {
                    "days_until_stockout": days_until_stockout,
                    "confidence": confidence,
                    "method": "prophet" if PROPHET_AVAILABLE else "moving_average",
                    "recommended_action": self._get_action_recommendation(days_until_stockout)
                }
                self._prediction_cache[cache_key] = result
                return result
                
            except Exception as e:
                print(f"Prophet error: {e}, falling back to simple method")
        
        # Fallback: Simple moving average method
        recent_avg = prophet_df['y'].tail(7).mean()
        if recent_avg > 0:
            days_until_stockout = int((current_stock - min_threshold) / recent_avg)
            days_until_stockout = max(0, days_until_stockout)
        else:
            days_until_stockout = 0
        
        result = {
            "days_until_stockout": days_until_stockout,
            "confidence": 0.6,
            "method": "moving_average",
            "recommended_action": self._get_action_recommendation(days_until_stockout)
        }
        self._prediction_cache[cache_key] = result
        return result
    
    def invalidate_cache(self):
        """Clear prediction cache — call when simulation advances a day"""
        self._prediction_cache.clear()
    
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
    """Patient footfall forecasting — Prophet time-series with seasonal trend fallback"""

    def __init__(self):
        self.model_version = "v2.0"

    def forecast_footfall(self, df: pd.DataFrame, phc_id: int, days: int = 7) -> Dict:
        """
        Forecast footfall for next N days.

        Primary method: Prophet time-series on (date, total_patients).
        Falls back to seasonal trend + fixed multipliers when Prophet is
        unavailable or there are fewer than 14 days of history.
        """
        phc_data = df[df['phc_id'] == phc_id].copy()
        phc_data = phc_data.sort_values('date')

        if len(phc_data) < 14:
            return {
                "method": "seasonal_trend",
                "predicted_footfall": 0,
                "confidence_lower": 0,
                "confidence_upper": 0,
                "trend": "insufficient_data"
            }

        # --- Prophet path ---------------------------------------------------
        if PROPHET_AVAILABLE:
            try:
                prophet_df = pd.DataFrame({
                    'ds': pd.to_datetime(phc_data['date']),
                    'y': phc_data['total_patients']
                })
                model = Prophet(
                    daily_seasonality=False,
                    weekly_seasonality=True,
                    yearly_seasonality=True,
                    changepoint_prior_scale=0.05
                )
                model.fit(prophet_df)
                future = model.make_future_dataframe(periods=days)
                forecast = model.predict(future)
                forecast_tail = forecast.tail(days)

                predicted = int(forecast_tail['yhat'].mean())
                confidence_lower = int(forecast_tail['yhat_lower'].min())
                confidence_upper = int(forecast_tail['yhat_upper'].max())

                # Trend detection from Prophet's slope
                if len(forecast) >= 2:
                    slope = forecast['yhat'].iloc[-1] - forecast['yhat'].iloc[-days - 1]
                    if slope > phc_data['total_patients'].mean() * 0.05:
                        trend = "increasing"
                    elif slope < phc_data['total_patients'].mean() * -0.05:
                        trend = "decreasing"
                    else:
                        trend = "stable"
                else:
                    trend = "stable"

                return {
                    "method": "prophet",
                    "predicted_footfall": predicted,
                    "confidence_lower": confidence_lower,
                    "confidence_upper": confidence_upper,
                    "trend": trend
                }
            except Exception as e:
                print(f"[DEMAND] Prophet error: {e} — falling back to seasonal_trend")

        # --- Seasonal trend fallback ----------------------------------------
        recent_7 = phc_data.tail(7)['total_patients'].mean()
        recent_14 = phc_data.tail(14)['total_patients'].mean()

        if recent_7 > recent_14 * 1.1:
            trend = "increasing"
            trend_factor = 1.05
        elif recent_7 < recent_14 * 0.9:
            trend = "decreasing"
            trend_factor = 0.95
        else:
            trend = "stable"
            trend_factor = 1.0

        latest_data_date = pd.to_datetime(phc_data['date'].iloc[-1])
        current_month = latest_data_date.month
        seasonal_factor = 1.0
        if current_month in [6, 7, 8, 9]:
            seasonal_factor = 1.3
        elif current_month in [12, 1, 2]:
            seasonal_factor = 1.15

        base_prediction = recent_7 * trend_factor * seasonal_factor
        predicted = int(base_prediction)
        confidence_lower = int(predicted * 0.8)
        confidence_upper = int(predicted * 1.2)

        return {
            "method": "seasonal_trend",
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
        Detect anomalous PHCs using IsolationForest on the four-component
        health feature vector, combined with district-average comparison.

        Falls back to pure average-threshold logic when IsolationForest
        cannot fit (too few PHCs or exception).
        """
        if len(phc_scores) < 2:
            return []

        avg_health = sum(s['health_score'] for s in phc_scores) / len(phc_scores)

        # --- Try IsolationForest on the 4-component feature vector -------
        ifo_labels = {}     # phc_id -> -1 (outlier) or 1 (normal)
        ifo_scores = {}     # phc_id -> decision_function value (more negative = more anomalous)
        method = "isolation_forest"

        if len(phc_scores) >= 4:
            try:
                feature_cols = ['stock_health', 'attendance_rate',
                                'bed_occupancy_rate', 'test_availability_rate']
                X = np.array([[s[c] for c in feature_cols] for s in phc_scores])
                X_scaled = self.scaler.fit_transform(X)
                labels = self.model.fit_predict(X_scaled)
                scores = self.model.decision_function(X_scaled)
                for i, s in enumerate(phc_scores):
                    ifo_labels[s['phc_id']] = int(labels[i])
                    ifo_scores[s['phc_id']] = float(scores[i])
            except Exception as e:
                print(f"[ANOMALY] IsolationForest failed: {e} — falling back to average_threshold")
                method = "average_threshold"
        else:
            print(f"[ANOMALY] Only {len(phc_scores)} PHCs — IsolationForest needs >=4 for meaningful output, using average_threshold")
            method = "average_threshold"

        # --- Build anomaly list combining both signals -------------------
        anomalies = []
        for score_dict in phc_scores:
            health_score = score_dict['health_score']
            if health_score < avg_health:
                gap = avg_health - health_score
                is_outlier = ifo_labels.get(score_dict['phc_id']) == -1
                ifo_score = ifo_scores.get(score_dict['phc_id'], 0.0)

                # Severity incorporates BOTH signals:
                # - IsolationForest outlier flagged AND below average → escalate
                # - Below average but NOT flagged by model → de-escalate
                if health_score < 60 or (is_outlier and gap >= 5):
                    severity = "critical"
                elif gap >= 10 or (is_outlier and gap >= 3):
                    severity = "high"
                elif gap >= 3:
                    severity = "medium"
                else:
                    severity = "low"

                # If the model did NOT flag this PHC as an outlier, de-escalate
                # by one level (the average gap alone is a weaker signal)
                if method == "isolation_forest" and not is_outlier and severity != "low":
                    deescalate = {"critical": "high", "high": "medium", "medium": "low"}
                    severity = deescalate.get(severity, severity)

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
                if is_outlier:
                    description += f". Flagged as statistical outlier by IsolationForest (score={ifo_score:.3f})"

                anomalies.append({
                    "phc_id": score_dict['phc_id'],
                    "phc_name": score_dict['phc_name'],
                    "phc_code": score_dict['phc_code'],
                    "anomaly_type": "underperforming",
                    "severity": severity,
                    "score": round(health_score, 2),
                    "avg_deviation": round(gap, 2),
                    "anomaly_score": round(ifo_score, 4),
                    "is_outlier": is_outlier,
                    "method": method,
                    "description": description,
                    "details": score_dict
                })

        return anomalies


class RedistributionEngine:
    """Optimize resource redistribution across PHCs using linear programming"""

    # Synthetic distance matrix (km) between the 6 PHCs (IDs 1–6).
    # Row = source, col = destination. Used as transfer cost in the LP objective.
    _DISTANCE_KM = {
        (1, 2): 15, (1, 3): 22, (1, 4): 35, (1, 5): 28, (1, 6): 40,
        (2, 1): 15, (2, 3): 18, (2, 4): 30, (2, 5): 25, (2, 6): 38,
        (3, 1): 22, (3, 2): 18, (3, 4): 20, (3, 5): 32, (3, 6): 27,
        (4, 1): 35, (4, 2): 30, (4, 3): 20, (4, 5): 26, (4, 6): 19,
        (5, 1): 28, (5, 2): 25, (5, 3): 32, (5, 4): 26, (5, 6): 24,
        (6, 1): 40, (6, 2): 38, (6, 3): 27, (6, 4): 19, (6, 5): 24,
    }

    def __init__(self):
        self.model_version = "v2.0"
        self._cached_recommendations = None
        self._cache_timestamp = None
        self._cache_ttl = 3600
        self._cached_analysis = {}

    # ------------------------------------------------------------------
    # Public entry point — tries LP first, falls back to rule-based
    # ------------------------------------------------------------------
    def find_redistribution_opportunities(self, stock_df: pd.DataFrame,
                                          predictions: Dict[int, Dict],
                                          phcs: List[Dict]) -> List[Dict]:
        """
        Find optimal redistribution recommendations.

        Primary method: scipy.optimize.linprog (minimises unmet deficit +
        transfer distance cost). Falls back to rule-based threshold matching
        if the LP is infeasible or fails.
        """
        import time

        prev_recommendations = self._cached_recommendations
        self._cached_recommendations = None
        self._cache_timestamp = None

        # --- shared data prep ------------------------------------------------
        stock_df = stock_df.copy()
        stock_df['date'] = pd.to_datetime(stock_df['date'])
        latest_stock = (
            stock_df.sort_values('date')
            .groupby(['phc_id', 'medicine_id'])
            .last()
            .reset_index()
        )
        medicines = stock_df['medicine_id'].unique()

        district_excess_phcs: set = set()
        district_deficit_phcs: set = set()

        # --- try LP ----------------------------------------------------------
        lp_recommendations: List[Dict] = []
        lp_ok = False
        try:
            lp_recommendations, lp_ok = self._solve_lp(
                latest_stock, medicines, predictions, phcs,
                district_excess_phcs, district_deficit_phcs,
            )
        except Exception as e:
            print(f"[LP] Exception: {e}")

        if lp_ok and lp_recommendations:
            recommendations = lp_recommendations
            method = "linear_programming"
            print(f"[LP] Solved — {len(recommendations)} recommendations")
        else:
            print("[LP] Infeasible or no solution — falling back to rule-based")
            recommendations = self._find_redistribution_rule_based(
                latest_stock, medicines, predictions, phcs,
                district_excess_phcs, district_deficit_phcs,
            )
            method = "rule_based_fallback"

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda x: priority_order.get(x['urgency'], 4))

        # Stamp method on every recommendation
        for rec in recommendations:
            rec["method"] = method

        # --- Gemini enrichment (unchanged from previous version) -------------
        def _rec_key(recs):
            return tuple((r['from_phc_id'], r['to_phc_id'], r['medicine_id'], r['quantity']) for r in recs)

        current_key = _rec_key(recommendations)
        prev_key = _rec_key(prev_recommendations) if prev_recommendations else None

        if prev_key and current_key == prev_key and prev_recommendations:
            for i, rec in enumerate(recommendations):
                prev_rec = prev_recommendations[i] if i < len(prev_recommendations) else None
                if prev_rec and prev_rec.get('_gemini_reason'):
                    rec['reason'] = prev_rec['_gemini_reason']
                    rec['_gemini_reason'] = prev_rec['_gemini_reason']
            print("[GEMINI] Recommendations unchanged — reusing cached reasons")
        elif recommendations:
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

        self._cached_analysis = {
            "excess_count": len(district_excess_phcs),
            "deficit_count": len(district_deficit_phcs),
            "has_excess": len(district_excess_phcs) > 0,
            "has_deficit": len(district_deficit_phcs) > 0,
            "total_recommendations": len(recommendations),
        }
        self._cached_recommendations = recommendations
        self._cache_timestamp = time.time()
        print(f"[CACHE] Cached {len(recommendations)} recommendations (method={method})")

        return recommendations

    # ------------------------------------------------------------------
    # LP solver — real scipy.optimize.linprog
    # ------------------------------------------------------------------
    def _solve_lp(self, latest_stock, medicines, predictions, phcs,
                  district_excess_phcs, district_deficit_phcs):
        """
        Solve the redistribution LP.

        Decision variables  x_{s,d,m}  = units of medicine m sent from PHC s to PHC d.

        Objective (minimise):
            Σ dist[s,d]·x_{s,d,m}  -  0.001·Σ x_{s,d,m}
        The tiny benefit term (-0.001 per unit) ensures the LP prefers making
        transfers over leaving deficit unmet when distance is tied.

        Constraints (A_ub x ≤ b_ub):
            Supply:  Σ_d x_{s,d,m} ≤ excess[s, m]         for each source s, medicine m
            Demand:  Σ_s x_{s,d,m} ≤ deficit[d, m]         for each dest d, medicine m

        Bounds:  x ≥ 0
        """
        phc_ids = sorted(latest_stock['phc_id'].unique())
        phc_lookup = {p['id']: p for p in phcs}

        # Build per-medicine supply/demand lists
        all_excess = {}   # (phc_id, medicine_id) -> excess qty
        all_deficit = {}  # (phc_id, medicine_id) -> deficit qty
        all_stock = {}    # (phc_id, medicine_id) -> current qty
        all_ratio = {}    # (phc_id, medicine_id) -> ratio
        all_threshold = {}  # (phc_id, medicine_id) -> min_required

        for medicine_id in medicines:
            med_stock = latest_stock[latest_stock['medicine_id'] == medicine_id]
            if len(med_stock) == 0:
                continue
            min_threshold = med_stock.iloc[0]['min_required']

            for _, row in med_stock.iterrows():
                pid = row['phc_id']
                qty = row['quantity']
                ratio = qty / min_threshold if min_threshold > 0 else 0
                all_stock[(pid, medicine_id)] = qty
                all_ratio[(pid, medicine_id)] = ratio
                all_threshold[(pid, medicine_id)] = min_threshold

                pred = predictions.get(str(pid), predictions.get(pid, {}))
                # predictions_map may be keyed by int or str
                days_until_stockout = pred.get('days_until_stockout', 999) if isinstance(pred, dict) else getattr(pred, 'days_until_stockout', 999)

                if ratio > 2.0:
                    excess = int(qty - (min_threshold * 1.5))
                    if excess > 0:
                        all_excess[(pid, medicine_id)] = excess
                        district_excess_phcs.add(pid)
                elif ratio < 1.0:
                    need = int(min_threshold - qty)
                    if need > 0:
                        all_deficit[(pid, medicine_id)] = {
                            'need': need,
                            'stock': qty,
                            'ratio': ratio,
                            'days_until_stockout': days_until_stockout,
                            'min_threshold': min_threshold,
                        }
                        district_deficit_phcs.add(pid)

        # If no excess or no deficit, LP is trivially empty
        if not all_excess or not all_deficit:
            return [], True  # LP "succeeded" but nothing to do

        # Enumerate variables: (source, dest, medicine) where source has excess
        # and dest has deficit for the SAME medicine
        var_list = []
        for (s, sm) in all_excess:
            for (d, dm) in all_deficit:
                if sm == dm and s != d:
                    var_list.append((s, d, sm))

        if not var_list:
            # There are deficits and excess, but no matching medicine pairs —
            # the LP cannot address the problem, so mark as failed to allow
            # the rule-based fallback to attempt a solution.
            print("[LP] No matching source-dest pairs — deficits exist but no transferable medicine matches")
            return [], False

        n_vars = len(var_list)

        # Objective: minimise distance*qty - LARGE_BENEFIT*qty
        # The benefit term (1000 per unit) dominates distance cost (15-50 km),
        # so the LP always prefers transferring to fill deficit.
        # Among transfers that fill the same deficit, it picks the shortest route.
        c = np.zeros(n_vars)
        for i, (s, d, m) in enumerate(var_list):
            dist = self._DISTANCE_KM.get((s, d), 50)
            c[i] = dist - 1000  # benefit per unit transferred

        # Build constraint matrix
        # Supply constraints: for each (source, medicine): Σ_d x ≤ excess
        supply_keys = sorted(set((s, m) for s, d, m in var_list))
        supply_idx = {k: i for i, k in enumerate(supply_keys)}

        # Demand constraints: for each (dest, medicine): Σ_s x ≤ deficit
        demand_keys = sorted(set((d, m) for s, d, m in var_list))
        demand_idx = {k: i for i, k in enumerate(demand_keys)}

        n_constraints = len(supply_keys) + len(demand_keys)
        A_ub = np.zeros((n_constraints, n_vars))
        b_ub = np.zeros(n_constraints)

        for i, (s, d, m) in enumerate(var_list):
            # supply row
            row = supply_idx[(s, m)]
            A_ub[row, i] = 1.0
            # demand row
            row = len(supply_keys) + demand_idx[(d, m)]
            A_ub[row, i] = 1.0

        for k, (s, m) in enumerate(supply_keys):
            b_ub[k] = all_excess[(s, m)]
        for k, (d, m) in enumerate(demand_keys):
            b_ub[len(supply_keys) + k] = all_deficit[(d, m)]['need']

        # Equality constraint: total transfer must equal total deficit.
        # When total excess < total deficit, this makes the LP infeasible,
        # triggering the rule-based fallback.
        total_deficit = sum(d['need'] for d in all_deficit.values())
        A_eq = np.ones((1, n_vars))
        b_eq = np.array([total_deficit])

        # Solve
        result = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                         bounds=(0, None), method='highs')

        if not result.success:
            print(f"[LP] Solver failed: {result.message}")
            return [], False

        # Build recommendations from LP solution
        recommendations = []
        for i, (s, d, m) in enumerate(var_list):
            qty = result.x[i]
            if qty < 1:  # skip negligible transfers
                continue
            transfer_qty = int(round(qty))

            src_phc = phc_lookup.get(s, {})
            dst_phc = phc_lookup.get(d, {})

            deficit_info = all_deficit[(d, m)]
            days_until_stockout = deficit_info['days_until_stockout']
            if days_until_stockout <= 3:
                priority = "critical"
            elif days_until_stockout <= 7:
                priority = "high"
            else:
                priority = "medium"

            dist = self._DISTANCE_KM.get((s, d), 50)

            reason_parts = [
                f"{dst_phc.get('name', 'Destination')} has {deficit_info['stock']} units remaining",
                f"with {days_until_stockout} days until stockout at current usage",
                f"({deficit_info['ratio']:.1f}x of threshold)",
            ]
            impact_parts = [
                f"Transferring {transfer_qty} units from {src_phc.get('name', 'Source')}",
                f"(surplus: {all_excess[(s, m)]} units above safety reserve)",
                f"route: {dist} km",
            ]

            recommendations.append({
                "from_phc_id": s,
                "from_phc_name": src_phc.get('name', f"PHC-{s}"),
                "to_phc_id": d,
                "to_phc_name": dst_phc.get('name', f"PHC-{d}"),
                "medicine_id": m,
                "medicine_name": f"Medicine-{m}",
                "quantity": transfer_qty,
                "urgency": priority,
                "reason": "; ".join(reason_parts),
                "impact": ". ".join(impact_parts) + ".",
            })

        return recommendations, True

    # ------------------------------------------------------------------
    # Rule-based fallback (original logic, extracted)
    # ------------------------------------------------------------------
    def _find_redistribution_rule_based(self, latest_stock, medicines, predictions,
                                        phcs, district_excess_phcs, district_deficit_phcs):
        """Original threshold-based matching — used when LP fails."""
        recommendations = []

        for medicine_id in medicines:
            medicine_stock = latest_stock[latest_stock['medicine_id'] == medicine_id]
            if len(medicine_stock) == 0:
                continue

            min_threshold = medicine_stock.iloc[0]['min_required']
            excess_phcs = []
            deficit_phcs = []

            for _, row in medicine_stock.iterrows():
                phc_id = row['phc_id']
                current_stock = row['quantity']
                stock_ratio = current_stock / min_threshold if min_threshold > 0 else 0

                pred = predictions.get(str(phc_id), predictions.get(phc_id, {}))
                days_until_stockout = pred.get('days_until_stockout', 999) if isinstance(pred, dict) else getattr(pred, 'days_until_stockout', 999)

                restock_arrives_on = row.get('restock_arrives_on', None)
                has_pending_restock = pd.notna(restock_arrives_on) if restock_arrives_on else False

                if stock_ratio > 2.0:
                    actual_excess = int(current_stock - (min_threshold * 1.5))
                    if actual_excess > 0:
                        district_excess_phcs.add(phc_id)
                        excess_phcs.append({
                            'phc_id': phc_id,
                            'stock': current_stock,
                            'ratio': stock_ratio,
                            'excess': actual_excess,
                            'has_pending_restock': has_pending_restock,
                        })
                elif stock_ratio < 1.0:
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
                            'restock_arrives_on': restock_arrives_on,
                        })

            for deficit in deficit_phcs:
                if deficit['need'] <= 0:
                    continue
                for excess in excess_phcs:
                    if excess['excess'] <= 0 or deficit['need'] <= 0:
                        continue
                    transfer_qty = min(excess['excess'], deficit['need'])
                    transfer_qty = max(0, transfer_qty)
                    if transfer_qty > 0:
                        if deficit['days_until_stockout'] <= 3:
                            priority = "critical"
                        elif deficit['days_until_stockout'] <= 7:
                            priority = "high"
                        else:
                            priority = "medium"
                        from_phc: Dict = next((p for p in phcs if p['id'] == excess['phc_id']), {})
                        to_phc: Dict = next((p for p in phcs if p['id'] == deficit['phc_id']), {})
                        surplus = excess['excess']
                        reason_parts = [
                            f"{to_phc.get('name', 'Destination')} has {deficit['stock']} units remaining",
                        ]
                        days_val = deficit.get('days_until_stockout', 'unknown')
                        if days_val and days_val != 'unknown':
                            reason_parts.append(f"with {days_val} days until stockout at current usage")
                        reason_parts.append(f"({deficit['ratio']:.1f}x of threshold)")
                        if deficit.get('has_pending_restock') and deficit.get('restock_arrives_on'):
                            reason_parts.append(f"[RESTOCK PENDING - arrives {deficit['restock_arrives_on']}]")
                        impact_parts = [
                            f"Transferring {transfer_qty} units from {from_phc.get('name', 'Source')}",
                            f"(surplus: {surplus} units above safety reserve)",
                        ]
                        recommendations.append({
                            "from_phc_id": excess['phc_id'],
                            "from_phc_name": from_phc.get('name', f"PHC-{excess['phc_id']}"),
                            "to_phc_id": deficit['phc_id'],
                            "to_phc_name": to_phc.get('name', f"PHC-{deficit['phc_id']}"),
                            "medicine_id": medicine_id,
                            "medicine_name": f"Medicine-{medicine_id}",
                            "quantity": transfer_qty,
                            "urgency": priority,
                            "reason": "; ".join(reason_parts),
                            "impact": ". ".join(impact_parts) + ".",
                        })
                        excess['excess'] -= transfer_qty
                        deficit['need'] -= transfer_qty

        return recommendations

    # ------------------------------------------------------------------
    def invalidate_cache(self):
        """Invalidate the cached recommendations (call after executing transfers)"""
        self._cached_recommendations = None
        self._cache_timestamp = None
        print("[CACHE] Cache invalidated")

    def optimize_redistribution_linear_programming(self, stock_df: pd.DataFrame,
                                                    min_thresholds: Dict[int, int],
                                                    phcs: List[Dict]) -> List[Dict]:
        """
        Public LP entry point — delegates to find_redistribution_opportunities
        which internally calls _solve_lp.
        """
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