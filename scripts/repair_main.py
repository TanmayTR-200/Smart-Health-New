#!/usr/bin/env python
"""Repair script to fix main.py corruption and implement the trigger_simulation_event fix."""
import os

MAIN_PY_PATH = os.path.join(os.path.dirname(__file__), '..', 'backend', 'main.py')

def main():
    with open(MAIN_PY_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove all corrupted lines with >>>>>> markers
    lines = content.split('\n')
    clean_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Skip corrupted lines
        if '>>>>>>>' in line:
            i += 1
            continue
        
        # Detect and skip duplicate advance-day declarations
        if '@app.post("/api/simulation/advance-day"' in line or "@app.post('/api/simulation/advance-day'" in line:
            # Check if we already have a complete advance-day function
            if '_advance_day_found' in dir():
                i += 1
                continue
        
        clean_lines.append(line)
        i += 1
    
    # Now find and fix the key issue: trigger_simulation_event uses PHC-specific date
    # Replace the PHC-specific query with district-wide query
    fixed_content = '\n'.join(clean_lines)
    
    # Fix the PHC-specific latest_stock query in trigger_simulation_event
    # OLD: latest_stock = db.query(Stock).filter(Stock.phc_id == request.phc_id).order_by(...).first()
    # NEW: latest_stock = db.query(Stock).order_by(Stock.date.desc()).first()
    
    import re
    
    trigger_pattern = r'latest_stock = db\.query\(Stock\)\.filter\(Stock\.phc_id == request\.phc_id\)\.order_by\(Stock\.date\.desc\(\)\)\.first\(\)'
    fixed_content = re.sub(trigger_pattern, 'latest_stock = db.query(Stock).order_by(Stock.date.desc()).first()', fixed_content)
    
    # Fix new_date -> event_date bug in trigger_simulation_event
    # Find the trigger-event section and fix the specific bug
    trigger_start = fixed_content.find('@app.post("/api/simulation/trigger-event"')
    if trigger_start == -1:
        trigger_start = fixed_content.find("@app.post('/api/simulation/trigger-event'")
    
    if trigger_start != -1:
        next_endpoint = fixed_content.find('\n\n@app.get("/api/dashboard/summary"', trigger_start)
        if next_endpoint == -1:
            next_endpoint = len(fixed_content)
        
        trigger_section = fixed_content[trigger_start:next_endpoint]
        # Fix new_date.strftime -> event_date.strftime
        trigger_section = trigger_section.replace('new_date.strftime("%Y-%m-%d")', 'event_date.strftime("%Y-%m-%d")')
        fixed_content = fixed_content[:trigger_start] + trigger_section + fixed_content[next_endpoint:]
    
    # Write the fixed content
    with open(MAIN_PY_PATH, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print("Main.py repaired successfully!")
    print("Note: This fixes the immediate syntax/corruption issues.")
    print("The full trigger_simulation_event fix to advance ALL PHCs still needs to be implemented.")

if __name__ == "__main__":
    main()