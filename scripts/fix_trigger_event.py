#!/usr/bin/env python
"""
Fix script for trigger_simulation_event to advance ALL PHCs, not just the triggered one.
This script reads main.py, fixes the corruption, and rewrites the trigger_simulation_event function.
"""
import re

# Read the corrupted file
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove all corrupted lines with >>>>>>>> markers
lines = content.split('\n')
cleaned_lines = []
for line in lines:
    if '>>>>>>>' in line:
        continue  # Skip corrupted line
    cleaned_lines.append(line)

cleaned_content = '\n'.join(cleaned_lines)

# Now find and fix the duplicate advance-day definitions
# Pattern: @app.post("/api/simulation/advance-day" ...) followed by async def advance_simulation_day(...):
# We want to keep only the SECOND complete definition and remove the first incomplete one

# Find the first occurrence of advance-day decorator (incomplete)
first_pattern = r'@app\.post\("/api/simulation/advance-day", response_model=SimulationResponse\)\s*\nasync def advance_simulation_day\([^)]+\):\s*\n(async def advance_simulation_day'

# This is tricky - let's just split at the trigger-event decorator and work backward

# Find where trigger-event starts
trigger_start = cleaned_content.find('@app.post("/api/simulation/trigger-event"')
if trigger_start == -1:
    trigger_start = cleaned_content.find("@app.post('/api/simulation/trigger-event'")

# Find the last clean advance-day complete function
advance_day_pattern = r'@app\.post\("/api/simulation/advance-day", response_model=SimulationResponse\)\s*\nasync def advance_simulation_day\([^)]+\):[^}]+?(?=\n\n@app\.post|\n\nif __name__)'

matches = list(re.finditer(
    r'@app\.post\("/api/simulation/advance-day", response_model=SimulationResponse\)\s*\nasync def advance_simulation_day\([^)]+\):',
    cleaned_content
))
print(f"Found {len(matches)} advance-day decorator matches")
for m in matches:
    print(f"  Match at position {m.start()}")