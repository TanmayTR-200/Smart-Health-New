"""
Database connection and session management
"""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL - defaults to SQLite for easy demo
# Use absolute path to smart-health directory for database
import os
current_file = os.path.abspath(__file__)  # backend/app/database/connection.py
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))  # backend dir
parent_dir = os.path.dirname(backend_dir)  # smart-health dir
db_path = os.path.join(parent_dir, "smart_health.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")

# Create engine - with performance optimizations
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "check_same_thread": False,
            "timeout": 30,  # Increase timeout for busy situations
        },
        pool_pre_ping=True,
        pool_recycle=3600,
    )

    # Add connect listener for SQLite performance options
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        # WAL mode for better concurrent read performance
        cursor.execute("PRAGMA journal_mode=WAL")
        # Increase cache size to 64MB
        cursor.execute("PRAGMA cache_size=-64000")
        # Enable synchronous mode for better performance (NORMAL is safe with WAL)
        cursor.execute("PRAGMA synchronous=NORMAL")
        # Increase temp storage to memory
        cursor.execute("PRAGMA temp_store=MEMORY")
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=10,
        max_overflow=20,
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables and run migrations"""
    from app.database.schema import Base
    Base.metadata.create_all(bind=engine)

    # Run migrations for existing databases
    _run_migrations(engine)


def _run_migrations(engine):
    """Run ALTER TABLE migrations for existing databases"""
    from sqlalchemy import text, inspect

    inspector = inspect(engine)

    # Migration 1: Add patient_load_per_doctor to doctor_attendances if missing
    if 'doctor_attendances' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('doctor_attendances')]
        if 'patient_load_per_doctor' not in columns:
            print("Migrating: Adding patient_load_per_doctor column to doctor_attendances...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE doctor_attendances ADD COLUMN patient_load_per_doctor FLOAT"))
                conn.commit()
            print("✓ Migration complete: patient_load_per_doctor column added")

    # Migration 2: Create performance indexes for foreign key and date columns
    # These improve query speed dramatically for filtering by phc_id, date, etc.
    index_migrations = [
        ("ix_stocks_phc_id", "stocks", "phc_id"),
        ("ix_stocks_medicine_id", "stocks", "medicine_id"),
        ("ix_stocks_date", "stocks", "date"),
        ("ix_footfalls_phc_id", "footfalls", "phc_id"),
        ("ix_footfalls_date", "footfalls", "date"),
        ("ix_bed_occupancies_phc_id", "bed_occupancies", "phc_id"),
        ("ix_bed_occupancies_date", "bed_occupancies", "date"),
        ("ix_doctor_attendances_phc_id", "doctor_attendances", "phc_id"),
        ("ix_doctor_attendances_date", "doctor_attendances", "date"),
        ("ix_test_availabilities_phc_id", "test_availabilities", "phc_id"),
        ("ix_test_availabilities_date", "test_availabilities", "date"),
    ]

    for idx_name, table, column in index_migrations:
        try:
            # Check if index already exists
            existing_indexes = [idx['name'] for idx in inspector.get_indexes(table)]
            if idx_name not in existing_indexes:
                print(f"Migrating: Creating index {idx_name} on {table}({column})...")
                with engine.connect() as conn:
                    conn.execute(text(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({column})"))
                    conn.commit()
                print(f"✓ Index created: {idx_name}")
        except Exception as e:
            print(f"  Skipping index {idx_name}: {e}")
