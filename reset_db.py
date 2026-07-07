#!/usr/bin/env python3
"""
Reset database - drops all tables and recreates them
Uses the same database path as the main application
"""
import sqlite3
import os
import sys

# Get absolute path to smart_health.db (same as connection.py)
current_file = os.path.abspath(__file__)  # reset_db.py location
smart_health_dir = os.path.dirname(current_file)  # smart-health directory
db_path = os.path.join(smart_health_dir, "smart_health.db")

print(f"Resetting database at: {db_path}")

# Connect and drop all tables
if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table[0]};")
        conn.commit()
        conn.close()
        print("✓ All tables dropped successfully")
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
else:
    print("✓ Database file doesn't exist yet (will be created on first run)")

print("✓ Database reset complete")
