#!/usr/bin/env python
"""
Final repair script for main.py - removes all corruption and duplicate functions
"""
import os
import re

MAIN_PY_PATH = os.path.join(os.path.dirname(__file__), '..', 'backend', 'main.py')

with open(MAIN_PY_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# Step 1: Remove all lines with >>>>>>>>> markers
lines = content.split('\n')
cleaned_lines = [l for l in lines if '>>>>>>>' not in l]
cleaned = '\n'.join(cleaned_lines)

# Step 2: Find and remove the duplicate advance-day function declarations
# The pattern is: @app.post("/api/simulation/advance-day" appears multiple times
advance_pattern = r'@app\.post\("/api/simulation/advance-day"'
matches = list(re.finditer(advance_pattern, cleaned))

print(f"Found {len(matches)} advance-day decorator matches")

# We want to keep only the LAST complete one
if len(matches) > 1:
    # Find the last occurrence
    last_start = matches[-1].start()
    
    # Remove everything before the last occurrence except the header code
    # Also remove any incomplete declarations
    
    # Find the previous decorator/function to keep as cutoff point
    prev_match_start = matches[-2].start() if len(matches) > 1 else 0
    
    # Extract everything before prev_match to keep
    before_section = cleaned[:prev_match_start]
    
    # Extract the last complete function
    after_section = cleaned[last_start:]
    
    cleaned = before_section + after_section
    print(f"Removed duplicate advance-day declarations, kept the last one")

# Step 3: Fix the double function declaration if present
# Pattern: async def advance_simulation_day appears twice in a row
corrupted_decl = r'(async def advance_simulation_day\([^)]+\) -> [^:]+:\s*\nasync def advance_simulation_day\()'
cleaned = re.sub(corrupted_decl, r'\1', cleaned)

# Write the fixed content
with open(MAIN_PY_PATH, 'w', encoding='utf-8') as f:
    f.write(cleaned)

print("main.py repair completed!")

# Verify the file is valid Python
try:
    with open(MAIN_PY_PATH, 'r', encoding='utf-8') as f:
        compile(f.read(), MAIN_PY_PATH, 'exec')
    print("✓ main.py is now valid Python syntax")
except SyntaxError as e:
    print(f"✗ Syntax error still present: {e}")