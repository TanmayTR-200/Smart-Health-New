"""
Database schema for Smart Health PHC Management System
"""
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class PHC(Base):
    """Primary Health Centre / Community Health Centre"""
    __tablename__ = "phcs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(20), nullable=False, unique=True)
    type = Column(String(20), nullable=False)  # PHC or CHC
    district = Column(String(100), nullable=False)
    total_beds = Column(Integer, nullable=False)
    expected_doctors = Column(Integer, nullable=False)
    base_footfall = Column(Integer, default=80)  # average daily footfall
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    stocks = relationship("Stock", back_populates="phc")
    footfalls = relationship("Footfall", back_populates="phc")
    bed_occupancies = relationship("BedOccupancy", back_populates="phc")
    attendances = relationship("DoctorAttendance", back_populates="phc")
    test_availabilities = relationship("TestAvailability", back_populates="phc")


class Medicine(Base):
    """Medicine master data"""
    __tablename__ = "medicines"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(20), nullable=False, unique=True)
    category = Column(String(50))  # antibiotic, painkiller, etc.
    unit = Column(String(20), nullable=False)  # tablets, bottles, etc.
    min_stock_threshold = Column(Integer, nullable=False)  # days of supply
    base_daily_usage = Column(Integer, default=20)  # average daily usage
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    stocks = relationship("Stock", back_populates="medicine")


class Stock(Base):
    """Daily stock levels for each medicine at each PHC"""
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, index=True)
    phc_id = Column(Integer, ForeignKey("phcs.id"), nullable=False, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    min_required = Column(Integer, nullable=False)  # minimum stock level
    last_restocked = Column(Date)
    restock_arrives_on = Column(Date, nullable=True)  # Date when pending restock arrives
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    phc = relationship("PHC", back_populates="stocks")
    medicine = relationship("Medicine", back_populates="stocks")
    
    # Composite indexes for common query patterns
    __table_args__ = (
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
    )


class Footfall(Base):
    """Daily patient footfall at each PHC"""
    __tablename__ = "footfalls"
    
    id = Column(Integer, primary_key=True, index=True)
    phc_id = Column(Integer, ForeignKey("phcs.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    total_patients = Column(Integer, nullable=False)
    new_patients = Column(Integer)
    follow_up_patients = Column(Integer)
    emergency_cases = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    phc = relationship("PHC", back_populates="footfalls")


class BedOccupancy(Base):
    """Daily bed occupancy at each PHC"""
    __tablename__ = "bed_occupancies"
    
    id = Column(Integer, primary_key=True, index=True)
    phc_id = Column(Integer, ForeignKey("phcs.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    total_beds = Column(Integer, nullable=False)
    occupied_beds = Column(Integer, nullable=False)
    reserved_beds = Column(Integer, default=0)
    available_beds = Column(Integer, nullable=False)
    occupancy_rate = Column(Float, nullable=False)  # percentage
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    phc = relationship("PHC", back_populates="bed_occupancies")


class DoctorAttendance(Base):
    """Daily doctor attendance at each PHC"""
    __tablename__ = "doctor_attendances"
    
    id = Column(Integer, primary_key=True, index=True)
    phc_id = Column(Integer, ForeignKey("phcs.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    expected_doctors = Column(Integer, nullable=False)
    present_doctors = Column(Integer, nullable=False)
    absent_doctors = Column(Integer, nullable=False)
    attendance_rate = Column(Float, nullable=False)  # percentage
    patient_load_per_doctor = Column(Float, nullable=True)  # patients per doctor, tracks strain
    reasons = Column(Text)  # JSON string of absence reasons
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    phc = relationship("PHC", back_populates="attendances")


class TestAvailability(Base):
    """Daily diagnostic test availability at each PHC"""
    __tablename__ = "test_availabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    phc_id = Column(Integer, ForeignKey("phcs.id"), nullable=False, index=True)
    test_name = Column(String(100), nullable=False)  # e.g., "Blood Glucose", "Malaria Rapid Test"
    test_code = Column(String(20), nullable=False)  # e.g., "GLU", "MAL_RDT"
    date = Column(Date, nullable=False, index=True)
    is_available = Column(Boolean, nullable=False, default=True)
    equipment_status = Column(String(20), default="functional")  # functional, maintenance, broken
    last_calibration_date = Column(Date)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    phc = relationship("PHC", back_populates="test_availabilities")
    
    # Composite unique constraint
    __table_args__ = (
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
    )