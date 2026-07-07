#!/usr/bin/env python
"""
Comprehensive repair script for main.py - removes corruption and fixes trigger_simulation_event
"""
import os
import re

MAIN_PY_PATH = os.path.join(os.path.dirname(__file__), '..', 'backend', 'main.py')

def repair():
    with open(MAIN_PY_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Step 1: Remove all lines containing >>>>>>>>> markers
    lines = content.split('\n')
    cleaned_lines = [l for l in lines if '>>>>>>>' not in l]
    
    # Step 2: Join and find duplicate function definitions
    cleaned = '\n'.join(cleaned_lines)
    
    # Find all advance-day decorator positions
    advance_matches = list(re.finditer(r'@app\.post\("/api/simulation/advance-day"', cleaned))
    
    if len(advance_matches) > 1:
        # Find the first corrupted definition (the incomplete one with "return result")
        # Remove everything from first match until just before the second match
        
        first_start = advance_matches[0].start()
        second_start = advance_matches[1].start()
        
        # Find where the corrupted first function ends (look for the next @app.post or def)
        # The corrupted one has "return result" in it
        corrupted_section = cleaned[first_start:second_start]
        
        # The corruption starts at line 761-774 (the incomplete function)
        # We need to find where to cut - look for "return result" line
        return_result_pos = corrupted_section.find('return result')
        if return_result_pos != -1:
            # Find the end of this corrupted block (after return result + newlines)
            end_of_corruption = corrupted_section.find('\n\n', return_result_pos)
            if end_of_corruption == -1:
                end_of_corruption = len(corrupted_section)
            
            # Rebuild the content without the corrupted section
            before_corruption = cleaned[:first_start]
            after_corruption = cleaned[second_start:]
            cleaned = before_corruption + after_corruption
            
            print(f"Removed corrupted advance-day section (first incomplete definition)")
    
    # Step 3: Fix the key issue in trigger_simulation_event
    # Change PHC-specific date query to district-wide
    old_pattern = r'latest_stock = db\.query\(Stock\)\.filter\(Stock\.phc_id == request\.phc_id\)\.order_by\(Stock\.date\.desc\(\)\)\.first\(\)'
    cleaned = re.sub(old_pattern, 'latest_stock = db.query(Stock).order_by(Stock.date.desc()).first()', cleaned)
    print("Fixed PHC-specific date query to district-wide in trigger_simulation_event")
    
    # Step 4: Fix new_date -> event_date bug in trigger_simulation_event
    # Find trigger-event section and fix
    trigger_start = cleaned.find('@app.post("/api/simulation/trigger-event"')
    if trigger_start == -1:
        trigger_start = cleaned.find("@app.post('/api/simulation/trigger-event'")
    
    if trigger_start != -1:
        next_endpoint = cleaned.find('\n\n@app.get("/api/dashboard/summary"', trigger_start)
        if next_endpoint == -1:
            next_endpoint = cleaned.find("\n\nif __name__", trigger_start)
            if next_endpoint == -1:
                next_endpoint = len(cleaned)
        
        trigger_section = cleaned[trigger_start:next_endpoint]
        trigger_section = trigger_section.replace('new_date.strftime("%Y-%m-%d")', 'event_date.strftime("%Y-%m-%d")')
        cleaned = cleaned[:trigger_start] + trigger_section + cleaned[next_endpoint:]
        print("Fixed new_date -> event_date bug in trigger_simulation_event")
    
    with open(MAIN_PY_PATH, 'w', encoding='utf-8') as f:
        f.write(cleaned)
    
    print("main.py repaired successfully!")

if __name__ == "__main__":
    repair()