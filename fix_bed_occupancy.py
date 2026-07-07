#!/usr/bin/env python3
"""
Fix bed occupancy data in database
"""
import sys
sys.path.insert(0, 'backend')

from app.database.connection import SessionLocal  # type: ignore
from app.database.schema import BedOccupancy  # type: ignore

db = SessionLocal()
try:
    # Get all bed occupancy records
    beds = db.query(BedOccupancy).all()
    print(f"Found {len(beds)} bed occupancy records")
    
    fixed = 0
    for bed in beds:
        # Calculate correct occupancy rate
        if bed.total_beds > 0:
            correct_rate = round((bed.occupied_beds / bed.total_beds) * 100, 2)
        else:
            correct_rate = 0.0
        
        # Update if different
        if bed.occupancy_rate != correct_rate:
            bed.occupancy_rate = correct_rate
            fixed += 1
    
    db.commit()
    print(f"Fixed {fixed} records")
    
    # Verify
    sample = db.query(BedOccupancy).limit(5).all()
    print("\nSample after fix:")
    for bed in sample:
        expected = round((bed.occupied_beds / bed.total_beds) * 100, 2) if bed.total_beds > 0 else 0
        match = "✅" if abs(bed.occupancy_rate - expected) < 0.01 else "❌"
        print(f"  {match} PHC {bed.phc_id} {bed.date}: {bed.occupied_beds}/{bed.total_beds} = {expected}% (stored: {bed.occupancy_rate}%)")
    
finally:
    db.close()