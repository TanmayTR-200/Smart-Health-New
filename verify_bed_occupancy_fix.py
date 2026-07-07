#!/usr/bin/env python3
"""
Verify that bed occupancy is now consistent between individual PHCs and dashboard
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def verify_bed_occupancy_consistency():
    """Verify bed occupancy values are consistent"""
    print("\n" + "="*60)
    print("VERIFYING BED OCCUPANCY CONSISTENCY")
    print("="*60)
    
    # Get dashboard summary
    response = requests.get(f"{BASE_URL}/api/dashboard/summary")
    if response.status_code != 200:
        print(f"❌ Failed to get dashboard summary: {response.status_code}")
        return False
    
    data = response.json()
    dashboard_avg = data['avg_bed_occupancy']
    phc_scores = data['phc_health_scores']
    
    print(f"\nDashboard Summary:")
    print(f"  Average Bed Occupancy: {dashboard_avg}%")
    print(f"\nIndividual PHC Bed Occupancy Rates:")
    
    # Calculate average from individual PHCs
    phc_rates = []
    for phc in phc_scores:
        rate = phc['bed_occupancy_rate']
        phc_rates.append(rate)
        print(f"  {phc['phc_name']}: {rate}%")
    
    # Calculate average
    if phc_rates:
        calculated_avg = sum(phc_rates) / len(phc_rates)
        print(f"\nCalculated Average from PHCs: {calculated_avg:.2f}%")
        print(f"Dashboard Reported Average: {dashboard_avg}%")
        
        # Check if they match (within 1% tolerance for rounding)
        if abs(calculated_avg - dashboard_avg) < 1.0:
            print(f"\n✅ CONSISTENT: Individual PHC rates average matches dashboard")
            return True
        else:
            print(f"\n❌ INCONSISTENT: Mismatch of {abs(calculated_avg - dashboard_avg):.2f}%")
            return False
    else:
        print("❌ No PHC data found")
        return False

def main():
    # Check backend is running
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("❌ Backend not running")
            return False
    except:
        print("❌ Backend not running. Start it with:")
        print("   cd d:\\Hack2Skill\\smart-health\\backend")
        print("   uvicorn main:app --reload")
        return False
    
    print("✅ Backend is running")
    
    # Run verification
    success = verify_bed_occupancy_consistency()
    
    print("\n" + "="*60)
    if success:
        print("✅ BED OCCUPANCY IS NOW CONSISTENT!")
        print("\nThe dashboard average should match the individual PHC rates.")
    else:
        print("❌ BED OCCUPANCY STILL INCONSISTENT")
        print("\nPossible issues:")
        print("1. Backend needs to be restarted to pick up code changes")
        print("2. Database needs to be refreshed")
    print("="*60)
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)