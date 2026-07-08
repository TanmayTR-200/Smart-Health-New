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
    
    # Check if database already has data (skip re-seeding to preserve simulation state)
    from sqlalchemy import create_engine, text
    from dotenv import load_dotenv
    load_dotenv()

    db_path = 'smart_health_new.db'
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
    elif DATABASE_URL.startswith("postgresql://") and "+" not in DATABASE_URL.split("://")[0]:
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
    engine = create_engine(DATABASE_URL)

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM phcs"))
            phc_count = result.fetchone()[0]
            if phc_count > 0:
                print(f"\n✓ Database already has {phc_count} PHCs. Skipping re-seed (preserving simulation state).")
                # Verify tables
                tables = ['phcs', 'medicines', 'stocks', 'footfalls', 'bed_occupancies',
                          'doctor_attendances', 'test_availabilities']
                for table in tables:
                    try:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = result.fetchone()[0]
                        print(f"  ✓ {table}: {count} records")
                    except Exception:
                        print(f"  ⚠ {table}: table not found")
                print("\n✓ Database setup complete (skipped re-seeding)!")
                return
    except Exception:
        pass  # Tables don't exist yet, proceed with seeding

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