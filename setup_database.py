"""
Quick database setup script - run this to initialize the database
"""
import os
import sys
import subprocess

def setup_database():
    """Setup and seed the database"""
    print("=" * 60)
    print("Smart Health - Database Setup")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists('data/generator.py'):
        print("❌ Error: Please run this script from the smart-health directory")
        sys.exit(1)
    
    # Step 1: Generate data
    print("\n1. Generating synthetic data...")
    try:
        subprocess.run([sys.executable, 'data/generator.py'], check=True)
        print("✓ Data generated successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating data: {e}")
        sys.exit(1)
    
    # Step 2: Seed database
    print("\n2. Seeding database...")
    try:
        subprocess.run([sys.executable, 'data/seed_data.py'], check=True)
        print("✓ Database seeded successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error seeding database: {e}")
        sys.exit(1)
    
    # Step 3: Verify database
    print("\n3. Verifying database...")
    db_path = 'smart_health.db'
    if os.path.exists(db_path):
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Count records in each table
        tables = ['phcs', 'medicines', 'stock', 'footfall', 'bed_occupancy', 
                  'doctor_attendance', 'test_availability']
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  ✓ {table}: {count} records")
            except:
                print(f"  ⚠ {table}: table not found")
        
        conn.close()
        print("\n✓ Database setup complete!")
    else:
        print(f"❌ Database not found at {db_path}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Next steps:")
    print("1. Start backend:  python -m uvicorn backend.main:app --reload")
    print("2. Start frontend: cd frontend && npm run dev")
    print("3. Open browser:   http://localhost:5173")
    print("=" * 60)

if __name__ == "__main__":
    setup_database()