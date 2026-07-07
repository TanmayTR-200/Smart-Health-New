#!/usr/bin/env python3
"""
End-to-end test of all 4 bug fixes
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_simulation_status_endpoint():
    """Test 4: Verify simulation status endpoint works"""
    print("\n" + "="*60)
    print("TEST 4: Simulation Status Endpoint")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/simulation/status")
        if response.status_code != 200:
            print(f"  ❌ Request failed with status {response.status_code}")
            return False
        
        data = response.json()
        print(f"  ✅ Endpoint responds successfully")
        print(f"  Is Active: {data.get('is_active')}")
        print(f"  Latest Date: {data.get('latest_simulated_date')}")
        print(f"  Original End: {data.get('original_seed_end_date')}")
        print(f"  Message: {data.get('message')}")
        
        # Verify logic
        if data.get('is_active') and data.get('latest_simulated_date') > data.get('original_seed_end_date'):
            print(f"  ✅ Simulation correctly detected as ACTIVE")
            return True
        else:
            print(f"  ❌ Simulation status logic incorrect")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_trigger_event_creates_data():
    """Test 1: Verify trigger event creates data without advance day"""
    print("\n" + "="*60)
    print("TEST 1: Trigger Event Creates Data")
    print("="*60)
    
    # Get first PHC
    response = requests.get(f"{BASE_URL}/api/phcs")
    phcs = response.json()
    if not phcs:
        print("  ❌ No PHCs found")
        return False
    
    phc = phcs[0]
    print(f"  Testing with: {phc['name']} (ID: {phc['id']})")
    
    # Trigger disease outbreak
    payload = {
        "phc_id": phc['id'],
        "event_type": "disease_outbreak",
        "severity": "medium",
        "duration_days": 2
    }
    
    response = requests.post(f"{BASE_URL}/api/simulation/trigger-event", json=payload)
    if response.status_code != 200:
        print(f"  ❌ Request failed: {response.status_code}")
        print(f"  Response: {response.text}")
        return False
    
    result = response.json()
    print(f"  ✅ Event triggered successfully")
    print(f"  Message: {result.get('message')}")
    print(f"  New dates: {result.get('changes', {}).get('new_dates', [])}")
    print(f"  Stock changes: {len(result.get('changes', {}).get('stock_changes', []))}")
    print(f"  Footfall changes: {len(result.get('changes', {}).get('footfall_changes', []))}")
    
    # Verify data was created
    if result.get('success') and len(result.get('changes', {}).get('new_dates', [])) > 0:
        print(f"  ✅ New data was created")
        return True
    else:
        print(f"  ❌ No new data created")
        return False

def test_bed_occupancy_consistency():
    """Test 2: Verify bed occupancy rate matches occupied/total"""
    print("\n" + "="*60)
    print("TEST 2: Bed Occupancy Consistency")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/api/beds?days=10")
    if response.status_code != 200:
        print(f"  ❌ Request failed: {response.status_code}")
        return False
    
    beds = response.json()
    if not beds:
        print("  ⚠️  No bed data found")
        return True
    
    mismatches = 0
    for bed in beds[:10]:  # Check first 10
        expected = round((bed['occupied_beds'] / bed['total_beds']) * 100, 2) if bed['total_beds'] > 0 else 0
        actual = bed['occupancy_rate']
        
        if abs(expected - actual) > 0.01:
            mismatches += 1
            print(f"  ❌ PHC {bed['phc_id']} {bed['date']}: {bed['occupied_beds']}/{bed['total_beds']} = {expected}% but stored as {actual}%")
    
    if mismatches == 0:
        print(f"  ✅ All {min(10, len(beds))} sampled records are consistent")
        return True
    else:
        print(f"  ❌ Found {mismatches} mismatches")
        return False

def test_redistribution_text():
    """Test 3: Verify redistribution recommendations have specific text"""
    print("\n" + "="*60)
    print("TEST 3: Redistribution Text Specificity")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/api/recommendations/redistribute")
    if response.status_code != 200:
        print(f"  ❌ Request failed: {response.status_code}")
        return False
    
    recommendations = response.json()
    
    if not recommendations:
        print("  ⚠️  No recommendations found (OK if no redistribution needed)")
        return True
    
    print(f"  Found {len(recommendations)} recommendations")
    
    # Check first 3 for specific text
    all_specific = True
    for i, rec in enumerate(recommendations[:3]):
        reason = rec.get('reason', '')
        impact = rec.get('impact', '')
        
        print(f"\n  Recommendation {i+1}:")
        print(f"    {rec.get('from_phc_name')} → {rec.get('to_phc_name')}")
        print(f"    {rec.get('medicine_name')}: {rec.get('quantity')} units")
        print(f"    Reason: {reason[:80]}...")
        
        # Check for generic template
        if "Source has" in reason and "destination has" in reason:
            print(f"    ❌ Still using generic template")
            all_specific = False
        else:
            print(f"    ✅ Using specific text")
    
    if all_specific:
        print(f"\n  ✅ All recommendations have specific text")
        return True
    else:
        print(f"\n  ❌ Some recommendations use generic text")
        return False

def main():
    print("\n" + "="*60)
    print("END-TO-END VERIFICATION OF ALL BUG FIXES")
    print("="*60)
    
    # Check backend
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("❌ Backend not running")
            return False
        print("✅ Backend is running")
    except:
        print("❌ Backend not running")
        return False
    
    # Run all tests
    results = []
    results.append(("Trigger Event Creates Data", test_trigger_event_creates_data()))
    results.append(("Bed Occupancy Consistency", test_bed_occupancy_consistency()))
    results.append(("Redistribution Text Specificity", test_redistribution_text()))
    results.append(("Simulation Status Endpoint", test_simulation_status_endpoint()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n✅ ALL TESTS PASSED - All 4 bug fixes verified!")
        print("\nNext steps:")
        print("1. Start frontend: npm run dev (in frontend directory)")
        print("2. Open http://localhost:5173")
        print("3. Go to Simulation page")
        print("4. Verify simulation mode shows 'ACTIVE' (not INACTIVE)")
        print("5. Click 'Trigger Event' without clicking 'Advance Day' first")
        print("6. Verify results appear in the results panel")
        print("7. Navigate to Dashboard/Alerts/Recommendations to see live updates")
        return True
    else:
        print("\n❌ SOME TESTS FAILED")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)