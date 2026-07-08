#!/usr/bin/env python3
"""
Add restock_arrives_on column to existing Stock table
"""
import sys
sys.path.insert(0, 'backend')

from app.database.connection import engine, SessionLocal  # type: ignore
from sqlalchemy import text
from datetime import date

def migrate():
    """Add restock_arrives_on column if it doesn't exist"""
    db = SessionLocal()
    try:
        # Check if column already exists
        result = db.execute(text("""
            SELECT COUNT(*) 
            FROM pragma_table_info('stocks') 
            WHERE name = 'restock_arrives_on'
        """))
        
        if result.scalar() == 0:
            print("Adding restock_arrives_on column...")
            db.execute(text("""
                ALTER TABLE stocks 
                ADD COLUMN restock_arrives_on DATE
            """))
            db.commit()
            print("✓ Column added successfully")
        else:
            print("✓ Column already exists")
        
        # Initialize existing records with NULL (no pending restock)
        result = db.execute(text("""
            UPDATE stocks 
            SET restock_arrives_on = NULL 
            WHERE restock_arrives_on IS NOT NULL
        """))
        db.commit()
        print(f"✓ Initialized {result.rowcount} existing stock records")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate()