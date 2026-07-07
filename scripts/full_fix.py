#!/usr/bin/env python
"""
Complete fix script for main.py corruption and trigger_simulation_event bug.
"""
import re
import os

MAIN_PY_PATH = os.path.join(os.path.dirname(__file__), '..', 'backend', 'main.py')

# Read the current corrupted file
with open(MAIN_PY_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# Step 1: Remove all corrupted >>>>>>>> lines
lines = content.split('\n')
cleaned_lines = [line for line in lines if '>>>>>>>' not in line]
cleaned_content = '\n'.join(cleaned_lines)

# Step 2: Remove duplicate advance-day function definitions
# We want to keep only ONE complete advance-day function

# Find all advance-day decorator positions
advance_pattern = r'@app\.post\("/api/simulation/advance-day", response_model=SimulationResponse\)\s*\nasync def advance_simulation_day\('
all_advances = list(re.finditer(advance_pattern, cleaned_content))
print(f"Found {len(all_advances)} advance-day decorators")

if len(all_advances) > 1:
    # Keep the LAST one (most complete) and remove earlier ones
    # Find where to truncate
    keep_start = all_advances[-1].start()
    
    # Find where the previous incomplete function ends (at trigger-event or before)
    # Look backwards to find a good cut point
    prev_end_pattern = r'\n\n(@app\.post\(|\nif __name__|def |async def )'
    prev_matches = list(re.finditer(prev_end_pattern, cleaned_content[:keep_start]))
    
    if prev_matches:
        cut_point = prev_matches[-1].start()
        cleaned_content = cleaned_content[:cut_point] + cleaned_content[keep_start:]
        print(f"Removed {len(all_advances) - 1} duplicate advance-day definitions")

# Step 3: Fix trigger_simulation_event to use district-wide date and advance all PHCs
# The key change: replace the PHC-specific latest_stock query with district-wide

# Find and fix the trigger_simulation_event function
# Current: latest_stock = db.query(Stock).filter(Stock.phc_id == request.phc_id)
# Fixed: latest_stock = db.query(Stock).order_by(Stock.date.desc()).first()

old_pattern = r'latest_stock = db\.query\(Stock\)\.filter\(Stock\.phc_id == request\.phc_id\)\.order_by\(Stock\.date\.desc\(\)\)\.first\(\)'
new_code = 'latest_stock = db.query(Stock).order_by(Stock.date.desc()).first()'

cleaned_content = re.sub(old_pattern, new_code, cleaned_content)
print("Fixed PHC-specific date query to district-wide date query")

# Step 4: Fix the new_date -> event_date bug in trigger_simulation_event
# Only fix within the trigger-event function context
trigger_start = cleaned_content.find('@app.post("/api/simulation/trigger-event"')
if trigger_start == -1:
    trigger_start = cleaned_content.find("@app.post('/api/simulation/trigger-event'")

# Find the next endpoint after trigger-event
next_endpoint = cleaned_content.find('\n\n@app.get("/api/dashboard/summary"', trigger_start)
if next_endpoint == -1:
    next_endpoint = cleaned_content.find("\n\n@app.get('/api/dashboard/summary'", trigger_start)

if trigger_start != -1 and next_endpoint != -1:
    trigger_section = cleaned_content[trigger_start:next_endpoint]
    # Fix new_date.strftime -> event_date.strftime in this section
    fixed_trigger = trigger_section.replace('new_date.strftime("%Y-%m-%d")', 'event_date.strftime("%Y-%m-%d")')
    cleaned_content = cleaned_content[:trigger_start] + fixed_trigger + cleaned_content[next_endpoint:]
    print("Fixed new_date -> event_date bug in trigger_event")

# Write the fixed content
with open(MAIN_PY_PATH, 'w', encoding='utf-8') as f:
    f.write(cleaned_content)

print("Applied fixes to main.py")