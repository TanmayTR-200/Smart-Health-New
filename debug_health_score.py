#!/usr/bin/env python3
"""
Debug health score calculation to see why bed occupancy is 0%
"""
import sys
sys.path.insert(0, 'backend')

from app.database.connection import SessionLocal  # type: ignore
from app.database.schema import Stock, Footfall, BedOccupancy, DoctorAttendance, TestAvailability, PHC  # type: ignore
import pandas as pd
from datetime import datetime, timedelta

# Import ML models
from app.models.ml_models import MLModelManager  # type: ignore

db = SessionLocal()
try:
    print("="*60)
    print("DEBUGGING HEALTH SCORE CALCULATION")
    print("="*60)
    
    # Load all data
    stock_df = pd.read_sql(db.query(Stock).statement, db.bind)
    footfall_df = pd.read_sql(db.query(Footfall).statement, db.bind)
    bed_df = pd.read_sql(db.query(BedOccupancy).statement, db.bind)
    attendance_df = pd.read_sql(db.query(DoctorAttendance).statement, db.bind)
    test_df = pd.read_sql(db.query(TestAvailability).statement, db.bind)
    
    print(f"\nData loaded:")
    print(f"  Stock records: {len(stock_df)}")
    print(f"  Footfall records: {len(footfall_df)}")
    print(f"  Bed records: {len(bed_df)}")
    print(f"  Attendance records: {len(attendance_df)}")
    print(f"  Test records: {len(test_df)}")
    
    # Check dates
    if len(stock_df) > 0:
        stock_df['date'] = pd.to_datetime(stock_df['date'])
        print(f"\nStock date range: {stock_df['date'].min()} to {stock_df['date'].max()}")
    
    if len(bed_df) > 0:
        bed_df['date'] = pd.to_datetime(bed_df['date'])
        print(f"Bed date range: {bed_df['date'].min()} to {bed_df['date'].max()}")
        
        # Check PHC 1 bed data
        phc1_beds = bed_df[bed_df['phc_id'] == 1]
        print(f"\nPHC 1 bed records: {len(phc1_beds)}")
        if len(phc1_beds) > 0:
            print(f"  Date range: {phc1_beds['date'].min()} to {phc1_beds['date'].max()}")
            print(f"  Sample rates: {phc1_beds['occupancy_rate'].head(5).tolist()}")
    
    # Calculate health score for PHC 1
    ml_manager = MLModelManager()
    
    print("\n" + "="*60)
    print("CALCULATING HEALTH SCORE FOR PHC 1")
    print("="*60)
    
    score = ml_manager.anomaly_detector.calculate_phc_health_score(
        1, stock_df, attendance_df, bed_df, footfall_df, test_df
    )
    
    print(f"\nHealth Score Results:")
    print(f"  Overall Score: {score['health_score']}")
    print(f"  Stock Health: {score['stock_health']}%")
    print(f"  Attendance Rate: {score['attendance_rate']}%")
    print(f"  Bed Occupancy Rate: {score['bed_occupancy_rate']}%")
    print(f"  Test Availability: {score['test_availability_rate']}%")
    
    # Manual calculation to debug
    print("\n" + "="*60)
    print("MANUAL CALCULATION")
    print("="*60)
    
    if len(stock_df) > 0:
        latest_stock_date = stock_df['date'].max()
        cutoff_date = latest_stock_date - timedelta(days=30)
        print(f"\nLatest stock date: {latest_stock_date}")
        print(f"Cutoff date: {cutoff_date}")
        
        # Check bed data after cutoff
        if len(bed_df) > 0:
            recent_beds = bed_df[
                (bed_df['phc_id'] == 1) & 
                (bed_df['date'] >= cutoff_date)
            ]
            print(f"\nPHC 1 recent beds (after cutoff): {len(recent_beds)}")
            if len(recent_beds) > 0:
                avg_occupancy = recent_beds['occupancy_rate'].mean()
                print(f"  Average occupancy: {avg_occupancy}%")
            else:
                print(f"  ❌ No bed data found after cutoff!")
                print(f"\n  This is the bug - cutoff date is too recent")
                print(f"  or bed data doesn't extend far enough back")
    
finally:
    db.close()