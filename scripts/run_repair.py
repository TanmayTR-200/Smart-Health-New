#!/usr/bin/env python
"""Run this script to repair the main.py file"""
import os
import re

MAIN_PY_PATH = os.path.join(os.path.dirname(__file__), '..', 'backend', 'main.py')

with open(MAIN_PY_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove all lines with >>>>>>>>> markers
lines = content.split('\n')
cleaned_lines = [l for l in lines if '>>>>>>>' not in l]

# Join and find the duplicate advance-day function
cleaned = '\n'.join(cleaned_lines)

# Find all @app.post("/api/simulation/advance-day" occurrences
advance_pattern = r'@app\.post\("/api/simulation/advance-day"'
matches = list(re.finditer(advance_pattern, cleaned))

print(f"Found {len(matches)} advance-day decorator matches")

# The corrupted file has 2 matches - we need to keep only the second (complete) one
# and remove the incomplete first one that ends with "return result"
if len(matches) >= 2:
    first_start = matches[0].start()
    second_start = matches[1].start()
    
    # Find where the corrupted first function ends (look for the pattern)
    # The corrupted one ends with "return result"
    corrupted_section = cleaned[first_start:second_start]
    
    # Try to find the "return result" line which ends the corrupted function
    return_match = re.search(r'\n\nasync def advance_simulation_day.*?\n    return result', corrupted_section, re.DOTALL)
    
    if return_match:
        # Calculate the end position in the full file
        end_pos = first_start + return_match.end()
        # Remove the corrupted section
        cleaned = cleaned[:first_start] + cleaned[end_pos:]
        print(f"Removed corrupted first advance-day function")

# Now fix trigger_simulation_event to use district-wide date query
# OLD: latest_stock = db.query(Stock).filter(Stock.phc_id == request.phc_id).order_by(...).first()
# NEW: latest_stock = db.query(Stock).order_by(Stock.date.desc()).first()

old_query = r'latest_stock = db\.query\(Stock\)\.filter\(Stock\.phc_id == request\.phc_id\)\.order_by\(Stock\.date\.desc\(\)\)\.first\(\)'
cleaned = re.sub(old_query, 'latest_stock = db.query(Stock).order_by(Stock.date.desc()).first()', cleaned)
print("Fixed trigger_simulation_event to use district-wide date query")

# Fix new_date -> event_date bug in trigger_event (for test_changes)
cleaned = cleaned.replace('new_date.strftime("%Y-%m-%d")', 'event_date.strftime("%Y-%m-%d")')
print("Fixed new_date -> event_date bug in trigger_simulation_event")

with open(MAIN_PY_PATH, 'w', encoding='utf-8') as f:
    f.write(cleaned)

print("main.py repaired successfully!")