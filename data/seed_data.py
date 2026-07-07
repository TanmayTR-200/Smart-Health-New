"""
Database seeding script - loads generated CSV data into PostgreSQL/SQLite
"""
import pandas as pd
import os
import sys
from datetime import datetime

# Add parent directory to path to import backend modules
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.database.connection import engine, SessionLocal, init_db  # type: ignore
from app.database.schema import Base, PHC, Medicine, Stock, Footfall, BedOccupancy, DoctorAttendance, TestAvailability  # type: ignore
from sqlalchemy.orm import Session


def load_csv_data():
    """Load generated CSV files"""
    data_dir = os.path.join(os.path.dirname(__file__), 'output')
    
    print("Loading CSV data...")
    phcs_df = pd.read_csv(f"{data_dir}/phcs.csv")
    medicines_df = pd.read_csv(f"{data_dir}/medicines.csv")
    stock_df = pd.read_csv(f"{data_dir}/stock.csv")
    footfall_df = pd.read_csv(f"{data_dir}/footfall.csv")
    bed_df = pd.read_csv(f"{data_dir}/bed_occupancy.csv")
    attendance_df = pd.read_csv(f"{data_dir}/doctor_attendance.csv")
    test_availability_df = pd.read_csv(f"{data_dir}/test_availability.csv")
    
    return phcs_df, medicines_df, stock_df, footfall_df, bed_df, attendance_df, test_availability_df


def seed_database():
    """Seed database with generated data"""
    # Initialize database tables
    print("Initializing database...")
    init_db()
    
    # Load CSV data
    phcs_df, medicines_df, stock_df, footfall_df, bed_df, attendance_df, test_availability_df = load_csv_data()
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Clear existing data
        print("Clearing existing data...")
        db.query(TestAvailability).delete()
        db.query(DoctorAttendance).delete()
        db.query(BedOccupancy).delete()
        db.query(Footfall).delete()
        db.query(Stock).delete()
        db.query(Medicine).delete()
        db.query(PHC).delete()
        db.commit()
        
        # Seed PHCs
        print("Seeding PHCs...")
        for _, row in phcs_df.iterrows():
            phc = PHC(
                name=row['name'],
                code=row['code'],
                type=row['type'],
                district=row['district'],
                total_beds=row['total_beds'],
                expected_doctors=row['expected_doctors'],
                latitude=row.get('latitude', None),
                longitude=row.get('longitude', None)
            )
            db.add(phc)
        db.commit()
        print(f"✓ Seeded {len(phcs_df)} PHCs")
        
        # Seed Medicines
        print("Seeding Medicines...")
        for _, row in medicines_df.iterrows():
            medicine = Medicine(
                name=row['name'],
                code=row['code'],
                category=row['category'],
                unit=row['unit'],
                min_stock_threshold=row['min_stock_threshold'],
                base_daily_usage=row.get('base_daily_usage', 20)
            )
            db.add(medicine)
        db.commit()
        print(f"✓ Seeded {len(medicines_df)} medicines")
        
        # Seed Stock data
        print("Seeding Stock data...")
        batch_size = 1000
        stock_records = []
        for _, row in stock_df.iterrows():
            stock = Stock(
                phc_id=row['phc_id'],
                medicine_id=row['medicine_id'],
                date=datetime.strptime(row['date'], '%Y-%m-%d').date(),
                quantity=row['quantity'],
                min_required=row['min_required'],
                last_restocked=datetime.strptime(row['last_restocked'], '%Y-%m-%d').date() if pd.notna(row['last_restocked']) else None
            )
            stock_records.append(stock)
            
            if len(stock_records) >= batch_size:
                db.bulk_save_objects(stock_records)
                db.commit()
                stock_records = []
        
        if stock_records:
            db.bulk_save_objects(stock_records)
            db.commit()
        print(f"✓ Seeded {len(stock_df)} stock records")
        
        # Seed Footfall data
        print("Seeding Footfall data...")
        footfall_records = []
        for _, row in footfall_df.iterrows():
            footfall = Footfall(
                phc_id=row['phc_id'],
                date=datetime.strptime(row['date'], '%Y-%m-%d').date(),
                total_patients=row['total_patients'],
                new_patients=row.get('new_patients', None),
                follow_up_patients=row.get('follow_up_patients', None),
                emergency_cases=row.get('emergency_cases', None)
            )
            footfall_records.append(footfall)
            
            if len(footfall_records) >= batch_size:
                db.bulk_save_objects(footfall_records)
                db.commit()
                footfall_records = []
        
        if footfall_records:
            db.bulk_save_objects(footfall_records)
            db.commit()
        print(f"✓ Seeded {len(footfall_df)} footfall records")
        
        # Seed Bed Occupancy data
        print("Seeding Bed Occupancy data...")
        bed_records = []
        for _, row in bed_df.iterrows():
            bed = BedOccupancy(
                phc_id=row['phc_id'],
                date=datetime.strptime(row['date'], '%Y-%m-%d').date(),
                total_beds=row['total_beds'],
                occupied_beds=row['occupied_beds'],
                reserved_beds=row.get('reserved_beds', 0),
                available_beds=row['available_beds'],
                occupancy_rate=row['occupancy_rate']
            )
            bed_records.append(bed)
            
            if len(bed_records) >= batch_size:
                db.bulk_save_objects(bed_records)
                db.commit()
                bed_records = []
        
        if bed_records:
            db.bulk_save_objects(bed_records)
            db.commit()
        print(f"✓ Seeded {len(bed_df)} bed occupancy records")
        
        # Seed Doctor Attendance data
        print("Seeding Doctor Attendance data...")
        attendance_records = []
        for _, row in attendance_df.iterrows():
            attendance = DoctorAttendance(
                phc_id=row['phc_id'],
                date=datetime.strptime(row['date'], '%Y-%m-%d').date(),
                expected_doctors=row['expected_doctors'],
                present_doctors=row['present_doctors'],
                absent_doctors=row['absent_doctors'],
                attendance_rate=row['attendance_rate'],
                reasons=row.get('reasons', '')
            )
            attendance_records.append(attendance)
            
            if len(attendance_records) >= batch_size:
                db.bulk_save_objects(attendance_records)
                db.commit()
                attendance_records = []
        
        if attendance_records:
            db.bulk_save_objects(attendance_records)
            db.commit()
        print(f"✓ Seeded {len(attendance_df)} attendance records")
        
        # Seed Test Availability data
        print("Seeding Test Availability data...")
        test_records = []
        for _, row in test_availability_df.iterrows():
            test = TestAvailability(
                phc_id=row['phc_id'],
                test_name=row['test_name'],
                test_code=row['test_code'],
                date=datetime.strptime(row['date'], '%Y-%m-%d').date(),
                is_available=row['is_available'],
                equipment_status=row['equipment_status'],
                last_calibration_date=datetime.strptime(row['last_calibration_date'], '%Y-%m-%d').date() if pd.notna(row['last_calibration_date']) else None,
                notes=row.get('notes', '')
            )
            test_records.append(test)
            
            if len(test_records) >= batch_size:
                db.bulk_save_objects(test_records)
                db.commit()
                test_records = []
        
        if test_records:
            db.bulk_save_objects(test_records)
            db.commit()
        print(f"✓ Seeded {len(test_availability_df)} test availability records")
        
        print("\n✓ Database seeding completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()