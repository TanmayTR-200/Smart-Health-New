import requests

res = requests.get('http://localhost:8000/api/dashboard/summary')
data = res.json()

print('Health Scores:')
for s in data['phc_health_scores']:
    print(f"  {s['phc_name']}: {s['health_score']}")
    print(f"    Stock: {s['stock_health']}%, Attendance: {s['attendance_rate']}%, Bed: {s['bed_occupancy_rate']}%, Test: {s['test_availability_rate']}%")