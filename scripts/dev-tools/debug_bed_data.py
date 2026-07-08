#!/usr/bin/env python3
"""
Debug bed occupancy data to understand why health scores show 0%
"""
import sys
sys.path.insert(0, 'backend')

from app.database.connection import SessionLocal  # type: ignore
from app.database.schema import BedOccupancy, Stock  # type: ignore
from datetime import datetime
import pandas as pd

db = SessionLocal()
try:
    # Check bed data
    print("="*60)
    print("BED OCCUPANCY DATA ANALYSIS")
    print("="*60)
    
    # Get all bed records
    beds = db.query(BedOccupancy).limit(10).all()
    print(f"\nTotal bed records (showing first 10): {len(beds)}")
    
    if beds:
        print("\nSample bed records:")
        for bed in beds[:3]:
            print(f"  PHC {bed.phc_id} on {bed.date}: {bed.occupied_beds}/{bed.total_beds} = {bed.occupancy_rate}%")
    
    # Get latest dates from each table
    latest_stock = db.query(Stock).order_by(Stock.date.desc()).first()
    latest_bed = db.query(BedOccupancy).order_by(BedOccupancy.date.desc()).first()
    
    print(f"\nLatest dates in database:")
    print(f"  Stock: {latest_stock.date if latest_stock else 'None'}")
    print(f"  Bed: {latest_bed.date if latest_bed else 'None'}")
    
    # Check what cutoff date would be used
    if latest_stock:
        cutoff = latest_stock.date - pd.Timedelta(days=30)
        print(f"\nCutoff date (30 days before latest stock): {cutoff}")
        
        # Count records after cutoff
        recent_beds = db.query(BedOccupancy).filter(BedOccupancy.date >= cutoff).count()
        print(f"Bed records after cutoff: {recent_beds}")
        
        # Check specific PHC
        phc1_beds = db.query(BedOccupancy).filter(
            BedOccupancy.phc_id == 1,
            BedOccupancy.date >= cutoff
        ).all()
        print(f"\nPHC 1 bed records after cutoff: {len(phc1_beds)}")
        if phc1_beds:
            for bed in phc1_beds[:3]:
                print(f"  {bed.date}: {bed.occupancy_rate}%")
    
finally:
    db.close()