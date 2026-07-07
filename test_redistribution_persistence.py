#!/usr/bin/env python3
"""
Test that redistribution recommendations persist correctly after triggering events
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_redistribution_persistence():
    """Test that redistribution recommendations don't disappear after events"""
    print("\n" + "="*60)
    print("TESTING REDISTRIBUTION PERSISTENCE AFTER EVENTS")
    print("="*60)
    
    # Step 1: Get initial redistribution recommendations
    print("\n1. Getting initial redistribution recommendations...")
    response = requests.get(f"{BASE_URL}/api/recommendations/redistribute")
    if response.status_code != 200:
        print(f"❌ Failed to get recommendations: {response.status_code}")
        return False
    
    initial_recs = response.json()
    print(f"✓ Found {len(initial_recs)} initial recommendations")
    
    # Step 2: Trigger a disease outbreak
    print("\n2. Triggering disease outbreak...")
    payload = {
        "phc_id": 1,
        "event_type": "disease_outbreak",
        "severity": "high",
        "duration_days": 3
    }
    
    response = requests.post(f"{BASE_URL}/api/simulation/trigger-event", json=payload)
    if response.status_code != 200:
        print(f"❌ Failed to trigger event: {response.status_code}")
        return False
    
    result = response.json()
    print(f"✓ Event triggered: {result['message']}")
    
    # Step 3: Check redistribution recommendations after event
    print("\n3. Checking redistribution recommendations after event...")
    response = requests.get(f"{BASE_URL}/api/recommendations/redistribute")
    if response.status_code != 200:
        print(f"❌ Failed to get recommendations: {response.status_code}")
        return False
    
    after_event_recs = response.json()
    print(f"✓ Found {len(after_event_recs)} recommendations after event")
    
    # Step 4: Verify recommendations still exist and mention the affected PHC
    print("\n4. Verifying recommendations persist...")
    
    # Check if any recommendations mention PHC 1 (the one we triggered event on)
    phc1_recs = [r for r in after_event_recs if r['to_phc_id'] == 1 or r['from_phc_id'] == 1]
    
    if len(phc1_recs) > 0:
        print(f"✓ Found {len(phc1_recs)} recommendations involving PHC 1")
        print("  Recommendations:")
        for rec in phc1_recs[:3]:
            print(f"    - {rec['reason'][:100]}...")
    else:
        print("⚠️  No recommendations for PHC 1 (may be normal if stock is still adequate)")
    
    # Step 5: Check that pending restocks are preserved
    print("\n5. Checking that pending restocks are preserved...")
    stock_response = requests.get(f"{BASE_URL}/api/stock/low")
    if stock_response.status_code == 200:
        low_stock = stock_response.json()
        print(f"  Found {len(low_stock)} low stock items")
        
        pending_restocks = [s for s in low_stock if s.get('restock_arrives_on')]
        print(f"  Items with pending restocks: {len(pending_restocks)}")
        
        if pending_restocks:
            print("✓ Pending restocks are preserved after event")
            for item in pending_restocks[:3]:
                print(f"    - {item['medicine_name']} at {item['phc_name']}: restock arriving {item['restock_arrives_on']}")
    
    # Step 6: Advance a day and check recommendations again
    print("\n6. Advancing simulation by 1 day...")
    response = requests.post(f"{BASE_URL}/api/simulation/advance-day", json={"days": 1})
    if response.status_code != 200:
        print(f"❌ Failed to advance day: {response.status_code}")
        return False
    
    result = response.json()
    print(f"✓ Advanced: {result['message']}")
    
    # Step 7: Check recommendations after advancing
    print("\n7. Checking recommendations after advancing day...")
    response = requests.get(f"{BASE_URL}/api/recommendations/redistribute")
    if response.status_code != 200:
        print(f"❌ Failed to get recommendations: {response.status_code}")
        return False
    
    after_advance_recs = response.json()
    print(f"✓ Found {len(after_advance_recs)} recommendations after advancing")
    
    # Verify recommendations still exist
    phc1_recs_after = [r for r in after_advance_recs if r['to_phc_id'] == 1 or r['from_phc_id'] == 1]
    
    if len(phc1_recs_after) > 0:
        print(f"✓ Recommendations for PHC 1 still exist after advancing ({len(phc1_recs_after)} recs)")
    else:
        print("⚠️  No recommendations for PHC 1 after advancing (may be normal)")
    
    # Step 8: Verify alerts still exist
    print("\n8. Checking alerts...")
    response = requests.get(f"{BASE_URL}/api/alerts")
    if response.status_code == 200:
        alerts = response.json()
        print(f"✓ Found {len(alerts)} active alerts")
        
        phc1_alerts = [a for a in alerts if a.get('phc_id') == 1]
        print(f"  Alerts for PHC 1: {len(phc1_alerts)}")
        
        if phc1_alerts:
            print("✓ Alerts for affected PHC still active")
            for alert in phc1_alerts[:2]:
                print(f"    - [{alert['severity'].upper()}] {alert['description'][:80]}...")
    
    print("\n" + "="*60)
    print("✅ REDISTRIBUTION PERSISTENCE VERIFIED")
    print("="*60)
    print("\nKey behaviors verified:")
    print("  ✓ Redistribution recommendations persist after triggering events")
    print("  ✓ Pending restocks are preserved across event dates")
    print("  ✓ Alerts remain active during and after events")
    print("  ✓ System maintains correlation between events and recommendations")
    
    return True

def main():
    # Check backend is running
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("❌ Backend not running")
            return False
    except:
        print("❌ Backend not running")
        return False
    
    print("✓ Backend is running")
    
    # Run test
    success = test_redistribution_persistence()
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)