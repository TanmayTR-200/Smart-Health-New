#!/usr/bin/env python3
"""
Test all 3 bug fixes comprehensively
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.database.connection import SessionLocal, init_db  # type: ignore
from app.database.schema import PHC, Stock, BedOccupancy, DoctorAttendance, TestAvailability, Medicine, Footfall  # type: ignore
from datetime import datetime
import requests
import json

BASE_URL = "http://localhost:8000"

def test_bed_occupancy_consistency():
    """Test 1: Verify bed occupancy rate matches occupied/total beds"""
    print("\n" + "="*60)
    print("TEST 1: Bed Occupancy Rate Consistency")
    print("="*60)
    
    db = SessionLocal()
    try:
        # Get a sample of bed occupancy records
        beds = db.query(BedOccupancy).limit(10).all()
        
        if not beds:
            print("  ⚠️  No bed occupancy data found")
            return True
        
        mismatches = 0
        for bed in beds:
            expected_rate = round((bed.occupied_beds / bed.total_beds) * 100, 2) if bed.total_beds > 0 else 0
            actual_rate = bed.occupancy_rate
            
            if abs(expected_rate - actual_rate) > 0.01:  # Allow tiny floating point differences
                mismatches += 1
                print(f"  ❌ PHC {bed.phc_id} on {bed.date}: {bed.occupied_beds}/{bed.total_beds} = {expected_rate}% but stored as {actual_rate}%")
        
        if mismatches == 0:
            print(f"  ✅ All {len(beds)} sampled records are consistent")
            return True
        else:
            print(f"  ❌ Found {mismatches}/{len(beds)} mismatches")
            return False
    finally:
        db.close()

def test_trigger_event_without_advance():
    """Test 2: Verify trigger-event works without clicking advance-day first"""
    print("\n" + "="*60)
    print("TEST 2: Trigger Event Without Advance Day")
    print("="*60)
    
    # Get first PHC
    db = SessionLocal()
    try:
        phc = db.query(PHC).first()
        if not phc:
            print("  ❌ No PHCs found in database")
            return False
        
        print(f"  Testing with PHC: {phc.name} (ID: {phc.id})")
        
        # Get current latest date
        latest_stock = db.query(Stock).filter(Stock.phc_id == phc.id).order_by(Stock.date.desc()).first()
        if not latest_stock:
            print("  ❌ No stock data found")
            return False
        
        current_date = latest_stock.date
        print(f"  Current date: {current_date}")
        
        # Count records before
        footfall_before = db.query(Footfall).filter(Footfall.phc_id == phc.id).count()
        stock_before = db.query(Stock).filter(Stock.phc_id == phc.id).count()
        
        print(f"  Records before: {footfall_before} footfall, {stock_before} stock")
        
    finally:
        db.close()
    
    # Trigger disease outbreak event
    print("\n  Triggering disease outbreak event...")
    payload = {
        "phc_id": phc.id,
        "event_type": "disease_outbreak",
        "severity": "medium",
        "duration_days": 2
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/simulation/trigger-event", json=payload)
        if response.status_code != 200:
            print(f"  ❌ Request failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
        
        result = response.json()
        print(f"  ✅ Event triggered successfully")
        print(f"  Message: {result.get('message', 'N/A')}")
        print(f"  New dates: {result.get('changes', {}).get('new_dates', [])}")
        print(f"  Stock changes: {len(result.get('changes', {}).get('stock_changes', []))}")
        print(f"  Footfall changes: {len(result.get('changes', {}).get('footfall_changes', []))}")
        print(f"  Bed changes: {len(result.get('changes', {}).get('bed_changes', []))}")
        print(f"  Attendance changes: {len(result.get('changes', {}).get('attendance_changes', []))}")
        
        # Verify data was actually created
        db = SessionLocal()
        try:
            footfall_after = db.query(Footfall).filter(Footfall.phc_id == phc.id).count()
            stock_after = db.query(Stock).filter(Stock.phc_id == phc.id).count()
            
            print(f"\n  Records after: {footfall_after} footfall, {stock_after} stock")
            
            if footfall_after > footfall_before and stock_after > stock_before:
                print(f"  ✅ New data was created in database")
                return True
            else:
                print(f"  ❌ No new data was created")
                return False
        finally:
            db.close()
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_redistribution_text():
    """Test 3: Verify redistribution recommendations have specific text"""
    print("\n" + "="*60)
    print("TEST 3: Redistribution Text Specificity")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/recommendations/redistribute")
        if response.status_code != 200:
            print(f"  ❌ Request failed with status {response.status_code}")
            return False
        
        recommendations = response.json()
        
        if not recommendations:
            print("  ⚠️  No recommendations found (this is OK if no redistribution needed)")
            return True
        
        print(f"  Found {len(recommendations)} recommendations")
        
        # Check that recommendations have specific text
        all_specific = True
        for i, rec in enumerate(recommendations[:3]):  # Check first 3
            reason = rec.get('reason', '')
            impact = rec.get('impact', '')
            
            print(f"\n  Recommendation {i+1}:")
            print(f"    From: {rec.get('from_phc_name')} → To: {rec.get('to_phc_name')}")
            print(f"    Medicine: {rec.get('medicine_name')}, Qty: {rec.get('quantity')}")
            print(f"    Reason: {reason[:100]}...")
            print(f"    Impact: {impact[:100]}...")
            
            # Check if text is generic (old template) or specific (new)
            if "Source has" in reason and "destination has" in reason:
                print(f"    ❌ Still using generic template")
                all_specific = False
            else:
                print(f"    ✅ Using specific text")
        
        if all_specific:
            print(f"\n  ✅ All recommendations have specific text")
            return True
        else:
            print(f"\n  ❌ Some recommendations still use generic text")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("TESTING ALL BUG FIXES")
    print("="*60)
    
    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("❌ Backend is not running. Please start it with:")
            print("   python -m uvicorn backend.main:app --reload")
            return False
    except:
        print("❌ Backend is not running. Please start it with:")
        print("   python -m uvicorn backend.main:app --reload")
        return False
    
    print("✅ Backend is running")
    
    # Run tests
    results = []
    
    # Test 1: Bed occupancy consistency
    results.append(("Bed Occupancy Consistency", test_bed_occupancy_consistency()))
    
    # Test 2: Trigger event without advance
    results.append(("Trigger Event Without Advance", test_trigger_event_without_advance()))
    
    # Test 3: Redistribution text
    results.append(("Redistribution Text Specificity", test_redistribution_text()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n✅ ALL TESTS PASSED")
        return True
    else:
        print("\n❌ SOME TESTS FAILED")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)