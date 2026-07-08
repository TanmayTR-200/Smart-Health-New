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
        print("❌ Error: Please run this script from the smart-health-new directory")
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
    
    # Step 3: Verify database (works with both SQLite and PostgreSQL)
    print("\n3. Verifying database...")
    from sqlalchemy import create_engine, text
    from dotenv import load_dotenv
    load_dotenv()

    db_path = 'smart_health_new.db'
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")
    engine = create_engine(DATABASE_URL)

    tables = ['phcs', 'medicines', 'stocks', 'footfalls', 'bed_occupancies',
              'doctor_attendances', 'test_availabilities']

    with engine.connect() as conn:
        for table in tables:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.fetchone()[0]
                print(f"  ✓ {table}: {count} records")
            except Exception:
                print(f"  ⚠ {table}: table not found")

    print("\n✓ Database setup complete!")
    
    print("\n" + "=" * 60)
    print("Next steps:")
    print("1. Start backend:  python -m uvicorn backend.main:app --reload")
    print("2. Start frontend: cd frontend && npm run dev")
    print("3. Open browser:   http://localhost:5173")
    print("=" * 60)

if __name__ == "__main__":
    setup_database()