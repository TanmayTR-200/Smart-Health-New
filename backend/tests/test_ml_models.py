"""
Minimal test suite for the four ML components in Smart Health.
Run with: cd backend && pytest
"""
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Ensure backend/ is on sys.path so `app` is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.models.ml_models import (
    StockoutPredictor,
    DemandForecaster,
    AnomalyDetector,
    RedistributionEngine,
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _make_stock_df(rows):
    """Build a stock DataFrame from [(phc_id, medicine_id, date_str, qty, min_req), ...]"""
    return pd.DataFrame(rows, columns=['phc_id', 'medicine_id', 'date', 'quantity', 'min_required'])


def _make_footfall_df(phc_id, days=60, base=80):
    """Build a footfall DataFrame with `days` days of data for one PHC."""
    start = datetime(2024, 1, 1)
    dates = [start + timedelta(days=i) for i in range(days)]
    return pd.DataFrame({
        'phc_id': phc_id,
        'date': dates,
        'total_patients': [base + int(np.random.randint(-10, 10)) for _ in range(days)],
    })


# --------------------------------------------------------------------------- #
# 1. StockoutPredictor
# --------------------------------------------------------------------------- #
class TestStockoutPredictor:
    def setup_method(self):
        self.predictor = StockoutPredictor()

    def test_insufficient_data_returns_none(self):
        """With <30 days of data, prediction should return days_until_stockout=None."""
        rows = [(1, 1, f'2024-01-{i:02d}', 500, 100) for i in range(1, 11)]
        df = _make_stock_df(rows)
        result = self.predictor.predict_stockout(df, 1, 1, min_threshold=100)
        assert result['days_until_stockout'] is None
        assert result['method'] == 'insufficient_data'

    def test_below_threshold_returns_zero(self):
        """When current stock < threshold, days_until_stockout=0, method=threshold_check."""
        rows = [(1, 1, f'2024-01-{i:02d}', 50, 100) for i in range(1, 32)]
        df = _make_stock_df(rows)
        result = self.predictor.predict_stockout(df, 1, 1, min_threshold=100)
        assert result['days_until_stockout'] == 0
        assert result['method'] == 'threshold_check'


# --------------------------------------------------------------------------- #
# 2. AnomalyDetector
# --------------------------------------------------------------------------- #
class TestAnomalyDetector:
    def setup_method(self):
        self.detector = AnomalyDetector()

    def test_few_phcs_falls_back_to_average_threshold(self):
        """With <4 PHCs, method should be average_threshold."""
        scores = [
            {'phc_id': 1, 'phc_name': 'A', 'phc_code': 'P1', 'health_score': 90,
             'stock_health': 90, 'attendance_rate': 90, 'bed_occupancy_rate': 90, 'test_availability_rate': 90},
            {'phc_id': 2, 'phc_name': 'B', 'phc_code': 'P2', 'health_score': 80,
             'stock_health': 80, 'attendance_rate': 80, 'bed_occupancy_rate': 80, 'test_availability_rate': 80},
        ]
        anomalies = self.detector.detect_anomalies(scores)
        for a in anomalies:
            assert a['method'] == 'average_threshold'

    def test_isolation_forest_flags_outlier(self):
        """With >=4 PHCs and one clearly bad PHC, method=isolation_forest and bad PHC is flagged."""
        scores = [
            {'phc_id': 1, 'phc_name': 'A', 'phc_code': 'P1', 'health_score': 95,
             'stock_health': 95, 'attendance_rate': 95, 'bed_occupancy_rate': 95, 'test_availability_rate': 95},
            {'phc_id': 2, 'phc_name': 'B', 'phc_code': 'P2', 'health_score': 92,
             'stock_health': 92, 'attendance_rate': 92, 'bed_occupancy_rate': 92, 'test_availability_rate': 92},
            {'phc_id': 3, 'phc_name': 'C', 'phc_code': 'P3', 'health_score': 90,
             'stock_health': 90, 'attendance_rate': 90, 'bed_occupancy_rate': 90, 'test_availability_rate': 90},
            {'phc_id': 4, 'phc_name': 'D', 'phc_code': 'P4', 'health_score': 40,
             'stock_health': 30, 'attendance_rate': 40, 'bed_occupancy_rate': 50, 'test_availability_rate': 40},
        ]
        anomalies = self.detector.detect_anomalies(scores)
        assert len(anomalies) > 0
        # The bad PHC (id=4) should appear in the anomalies
        phc_ids = [a['phc_id'] for a in anomalies]
        assert 4 in phc_ids
        # All anomalies should be tagged with isolation_forest method
        for a in anomalies:
            assert a['method'] == 'isolation_forest'
        # The bad PHC should have a real anomaly_score from decision_function
        bad_phc = next(a for a in anomalies if a['phc_id'] == 4)
        assert 'anomaly_score' in bad_phc
        assert bad_phc['is_outlier'] is True


# --------------------------------------------------------------------------- #
# 3. RedistributionEngine
# --------------------------------------------------------------------------- #
class TestRedistributionEngine:
    def setup_method(self):
        self.engine = RedistributionEngine()

    def test_deficit_exceeds_excess_triggers_fallback(self):
        """When total deficit > total excess, method should be rule_based_fallback."""
        rows = [
            # PHC 1: small excess for med 1 (qty=1100, min=500, excess=350)
            (1, 1, '2024-12-31', 1100, 500),
            # PHC 2: big deficit for med 1 (qty=100, min=500, deficit=400)
            (2, 1, '2024-12-31', 100, 500),
            # Other PHCs at threshold
            (3, 1, '2024-12-31', 501, 500),
            (4, 1, '2024-12-31', 501, 500),
            (5, 1, '2024-12-31', 501, 500),
            (6, 1, '2024-12-31', 501, 500),
        ]
        df = _make_stock_df(rows)
        phcs = [
            {'id': 1, 'name': 'P1', 'code': 'C1'},
            {'id': 2, 'name': 'P2', 'code': 'C2'},
            {'id': 3, 'name': 'P3', 'code': 'C3'},
            {'id': 4, 'name': 'P4', 'code': 'C4'},
            {'id': 5, 'name': 'P5', 'code': 'C5'},
            {'id': 6, 'name': 'P6', 'code': 'C6'},
        ]
        result = self.engine.find_redistribution_opportunities(df, {}, phcs)
        assert len(result) > 0
        assert result[0]['method'] == 'rule_based_fallback'

    def test_lp_solves_when_excess_covers_deficit(self):
        """When excess covers deficit, method should be linear_programming and
        no transfer should exceed source excess or destination deficit."""
        rows = [
            # PHC 1: big excess for med 1 (qty=2000, min=500, excess=1250)
            (1, 1, '2024-12-31', 2000, 500),
            # PHC 2: deficit for med 1 (qty=100, min=500, deficit=400)
            (2, 1, '2024-12-31', 100, 500),
            # Other PHCs at threshold (no excess, no deficit)
            (3, 1, '2024-12-31', 501, 500),
            (4, 1, '2024-12-31', 501, 500),
            (5, 1, '2024-12-31', 501, 500),
            (6, 1, '2024-12-31', 501, 500),
        ]
        df = _make_stock_df(rows)
        phcs = [
            {'id': i, 'name': f'P{i}', 'code': f'C{i}'} for i in range(1, 7)
        ]
        result = self.engine.find_redistribution_opportunities(df, {}, phcs)
        assert len(result) > 0
        assert result[0]['method'] == 'linear_programming'
        # Verify constraints: quantity <= source excess, quantity <= dest deficit
        for rec in result:
            assert rec['quantity'] > 0
            assert rec['quantity'] <= 400  # destination deficit
            assert rec['quantity'] <= 1250  # source excess


# --------------------------------------------------------------------------- #
# 4. DemandForecaster
# --------------------------------------------------------------------------- #
class TestDemandForecaster:
    def setup_method(self):
        self.forecaster = DemandForecaster()

    def test_method_field_present_and_valid(self):
        """The method field should be present and one of prophet/seasonal_trend."""
        df = _make_footfall_df(phc_id=1, days=60)
        result = self.forecaster.forecast_footfall(df, 1)
        assert 'method' in result
        assert result['method'] in ('prophet', 'seasonal_trend')

    def test_insufficient_data_returns_seasonal_trend(self):
        """With <14 days of data, method should be seasonal_trend (fallback)."""
        df = _make_footfall_df(phc_id=1, days=10)
        result = self.forecaster.forecast_footfall(df, 1)
        assert result['method'] == 'seasonal_trend'
        assert result['trend'] == 'insufficient_data'
