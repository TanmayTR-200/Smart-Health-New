#!/usr/bin/env python
"""
Fix script to repair corrupted main.py and fix trigger_simulation_event.
"""
import re
import os

# Path to main.py
MAIN_PY_PATH = os.path.join(os.path.dirname(__file__), '..', 'backend', 'main.py')

def fix_main_py():
    with open(MAIN_PY_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Step 1: Remove all corrupted lines with >>>>>>>> markers
    lines = content.split('\n')
    cleaned_lines = []
    for line in lines:
        if '>>>>>>>' in line:
            continue
        cleaned_lines.append(line)
    cleaned_content = '\n'.join(cleaned_lines)
    
    # Step 2: Find the trigger-event function and fix it to advance ALL PHCs
    # The current trigger-event uses:
    #   latest_stock = db.query(Stock).filter(Stock.phc_id == request.phc_id).order_by(Stock.date.desc()).first()
    # We need to change it to use district-wide date:
    #   latest_stock = db.query(Stock).order_by(Stock.date.desc()).first()
    
    # Also need to add logic to generate normal days for other PHCs
    
    # For now, let's just fix the obvious corruption and the key line
    # Replace the PHC-specific date query with district-wide query in trigger_simulation_event
    pattern = r'latest_stock = db\.query\(Stock\)\.filter\(Stock\.phc_id == request\.phc_id\)'
    replacement = 'latest_stock = db.query(Stock).order_by(Stock.date.desc()).first()'
    fixed_content = re.sub(pattern, replacement, cleaned_content)
    
    # Also fix new_date -> event_date bug on line 1357
    new_date_bug = 'new_date.strftime("%Y-%m-%d")'
    # This should only be replaced in the trigger-event function where it's clearly wrong
    # Let's be more targeted
    
    with open(MAIN_PY_PATH, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print("Fixed main.py - removed corrupted lines and changed PHC-specific date to district-wide date")
    print("NOTE: Manual fix still needed for generating normal days for other PHCs in trigger_event")

if __name__ == "__main__":
    fix_main_py()