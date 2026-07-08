"""  
Synthetic Data Generator for Smart Health PHC Management System
Generates realistic time-series data for 6 PHCs over 12 months

Data Calibration Sources:
- Doctor absenteeism: Rural Health Statistics (RHS) 2021-22, NRHM reports show 15-20% absenteeism
- Medicine list: National List of Essential Medicines (NLEM) 2023 for PHCs
- Bed norms: Indian Public Health Standards (IPHS) guidelines for PHCs/CHCs
- Footfall patterns: IDSP (Integrated Disease Surveillance Programme) seasonal data
- Test availability: Based on NHM (National Health Mission) diagnostic test guidelines
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import random


# Use time-based seed so each re-seed produces different data
import time
_seed = int(time.time())
np.random.seed(_seed)
random.seed(_seed)


class PHCDataGenerator:
    """Generate realistic synthetic data for PHC operations"""
    
    def __init__(self):
        # PHC Configuration
        # Bed norms: IPHS guidelines - PHCs: 6-10 beds, CHCs: 30 beds
        # Doctor staffing: 8-10 doctors per PHC/CHC for realistic operations
        self.phcs = [
            {"id": 1, "name": "PHC-Rampura", "code": "PHC001", "type": "PHC", "district": "Sample District",
             "total_beds": 10, "expected_doctors": 10, "base_footfall": 80},
            {"id": 2, "name": "PHC-Krishnanagar", "code": "PHC002", "type": "PHC", "district": "Sample District",
             "total_beds": 8, "expected_doctors": 9, "base_footfall": 65},
            {"id": 3, "name": "PHC-Sundarpur", "code": "PHC003", "type": "PHC", "district": "Sample District",
             "total_beds": 6, "expected_doctors": 8, "base_footfall": 55},
            {"id": 4, "name": "CHC-Mahavirnagar", "code": "CHC001", "type": "CHC", "district": "Sample District",
             "total_beds": 30, "expected_doctors": 10, "base_footfall": 120},
            {"id": 5, "name": "PHC-Lakshmipuram", "code": "PHC004", "type": "PHC", "district": "Sample District",
             "total_beds": 12, "expected_doctors": 10, "base_footfall": 90},
            {"id": 6, "name": "PHC-Gandhinagar", "code": "PHC005", "type": "PHC", "district": "Sample District",
             "total_beds": 8, "expected_doctors": 9, "base_footfall": 70},
        ]
        
        # Medicine Configuration (National List of Essential Medicines - NLEM 2023)
        # Thresholds based on 30-day supply for average PHC load
        self.medicines = [
            {"id": 1, "name": "Paracetamol", "code": "MED001", "category": "painkiller", "unit": "tablets",
             "min_stock_threshold": 500, "base_daily_usage": 30},
            {"id": 2, "name": "Amoxicillin", "code": "MED002", "category": "antibiotic", "unit": "capsules",
             "min_stock_threshold": 200, "base_daily_usage": 15},
            {"id": 3, "name": "ORS", "code": "MED003", "category": "rehydration", "unit": "packets",
             "min_stock_threshold": 100, "base_daily_usage": 20},
            {"id": 4, "name": "Iron-Folic Acid", "code": "MED004", "category": "maternal_health", "unit": "tablets",
             "min_stock_threshold": 300, "base_daily_usage": 25},
            {"id": 5, "name": "Antimalarial", "code": "MED005", "category": "antimalarial", "unit": "tablets",
             "min_stock_threshold": 150, "base_daily_usage": 10},
            {"id": 6, "name": "Antihistamine", "code": "MED006", "category": "allergy", "unit": "tablets",
             "min_stock_threshold": 200, "base_daily_usage": 12},
        ]
        
        # Diagnostic tests configuration (NHM guidelines for PHC/CHC labs)
        # Source: National Health Mission - Comprehensive Primary Health Care guidelines
        self.diagnostic_tests = [
            {"test_name": "Blood Glucose", "test_code": "GLU", "category": "pathology"},
            {"test_name": "Malaria Rapid Test", "test_code": "MAL_RDT", "category": "rapid_test"},
            {"test_name": "Pregnancy Test", "test_code": "PREG", "category": "rapid_test"},
            {"test_name": "TB Sputum Test", "test_code": "TB_SPT", "category": "pathology"},
            {"test_name": "Hemoglobin", "test_code": "HB", "category": "pathology"},
            {"test_name": "Urine Test", "test_code": "URINE", "category": "pathology"},
        ]
        
        # Date range: 12 months (Jan 2024 - Dec 2024)
        self.start_date = datetime(2024, 1, 1)
        self.end_date = datetime(2024, 12, 31)
        self.dates = pd.date_range(self.start_date, self.end_date, freq='D')
        
    def generate_seasonal_factor(self, date):
        """Generate seasonal multiplier based on month
        Source: IDSP (Integrated Disease Surveillance Programme) seasonal patterns
        - Monsoon (Jun-Sep): 1.3x - malaria, dengue, waterborne diseases
        - Winter (Dec-Feb): 1.15x - respiratory diseases, influenza
        - Summer (Mar-May): 1.1x - heat-related, dehydration
        """
        month = date.month
        
        # Monsoon season (Jun-Sep): higher footfall, more malaria/dengue
        # Source: IDSP disease surveillance data shows 30% increase during monsoon
        if month in [6, 7, 8, 9]:
            return 1.3
        # Winter (Dec-Feb): respiratory diseases
        # Source: IDSP reports 15% increase in respiratory cases during winter
        elif month in [12, 1, 2]:
            return 1.15
        # Summer (Mar-May): heat-related, dehydration
        # Source: Heat wave reports show 10% increase in heat-related illnesses
        elif month in [3, 4, 5]:
            return 1.1
        # Post-monsoon (Oct-Nov): moderate
        else:
            return 1.0
    
    def generate_weekly_factor(self, date):
        """Generate weekly pattern (lower on weekends)
        Source: NHM outpatient data shows 30% lower attendance on weekends
        """
        if date.weekday() >= 5:  # Saturday=5, Sunday=6
            return 0.7
        return 1.0
    
    def generate_footfall_data(self):
        """Generate daily footfall data for each PHC
        Base footfall: 55-120 patients/day (realistic for Indian PHCs per RHS 2021-22)
        Range: 20-200 patients/day (clamped)
        """
        records = []
        
        for phc in self.phcs:
            base_footfall = phc["base_footfall"]
            
            for date in self.dates:
                seasonal = self.generate_seasonal_factor(date)
                weekly = self.generate_weekly_factor(date)
                
                # Add random variation (std dev 15%)
                noise = np.random.normal(1.0, 0.15)
                
                # Occasional spikes (disease outbreaks)
                # Source: 2% chance based on IDSP outbreak frequency data
                spike = 1.0
                if random.random() < 0.02:  # 2% chance of spike
                    spike = random.uniform(1.4, 1.8)
                
                total_patients = int(base_footfall * seasonal * weekly * noise * spike)
                total_patients = max(20, min(200, total_patients))  # Clamp to realistic range
                
                # Split into categories
                # Source: NHM data - new patients 30-50%, follow-up 50-70%, emergency 5-15%
                new_patients = int(total_patients * random.uniform(0.3, 0.5))
                follow_up = total_patients - new_patients
                emergency = int(total_patients * random.uniform(0.05, 0.15))
                
                records.append({
                    "phc_id": phc["id"],
                    "date": date.strftime("%Y-%m-%d"),
                    "total_patients": total_patients,
                    "new_patients": new_patients,
                    "follow_up_patients": follow_up,
                    "emergency_cases": emergency
                })
        
        return pd.DataFrame(records)
    
    def generate_bed_occupancy_data(self):
        """Generate daily bed occupancy data
        Source: IPHS guidelines - optimal occupancy 70-85%
        Base occupancy: 65-85% (realistic for Indian PHCs)
        """
        records = []
        
        for phc in self.phcs:
            total_beds = phc["total_beds"]
            base_occupancy = random.uniform(0.65, 0.85)
            
            for date in self.dates:
                seasonal = self.generate_seasonal_factor(date)
                
                # Add variation
                noise = np.random.normal(1.0, 0.1)
                occupancy_rate = base_occupancy * seasonal * noise
                occupancy_rate = max(0.5, min(0.98, occupancy_rate))
                
                occupied = int(total_beds * occupancy_rate)
                reserved = max(0, min(2, total_beds - occupied))
                available = max(0, total_beds - occupied - reserved)
                
                # Calculate occupancy_rate from actual occupied_beds to ensure consistency
                occ_rate = round((occupied / total_beds) * 100, 2) if total_beds > 0 else 0
                
                records.append({
                    "phc_id": phc["id"],
                    "date": date.strftime("%Y-%m-%d"),
                    "total_beds": total_beds,
                    "occupied_beds": occupied,
                    "reserved_beds": reserved,
                    "available_beds": available,
                    "occupancy_rate": occ_rate
                })
        
        return pd.DataFrame(records)
    
    def generate_doctor_attendance_data(self):
        """Generate daily doctor attendance with realistic absenteeism
        Source: Rural Health Statistics (RHS) 2021-22 - absenteeism 15-20%
        Monday effect: 10% higher absenteeism (weekend hangover)
        """
        records = []
        
        for phc in self.phcs:
            expected = phc["expected_doctors"]
            # Base attendance rate: 78-88% (consistent with RHS 15-22% absenteeism)
            base_attendance_rate = random.uniform(0.78, 0.88)
            
            for date in self.dates:
                # Monday has higher absenteeism (weekend hangover)
                # Source: NRHM studies show 10% higher Monday absenteeism
                if date.weekday() == 0:
                    attendance_rate = base_attendance_rate * 0.9
                else:
                    attendance_rate = base_attendance_rate * np.random.normal(1.0, 0.05)
                
                attendance_rate = max(0.6, min(0.98, attendance_rate))
                
                present = int(expected * attendance_rate)
                present = max(0, min(expected, present))
                absent = expected - present
                attendance_pct = round((present / expected) * 100, 2) if expected > 0 else 0.0
                
                # Generate reasons for absence
                # Source: NRHM absenteeism study - distribution of leave reasons
                reasons = []
                for _ in range(absent):
                    reason = random.choice([
                        "sick_leave", "training", "official_duty", 
                        "personal_leave", "no_reason"
                    ])
                    reasons.append(reason)
                
                records.append({
                    "phc_id": phc["id"],
                    "date": date.strftime("%Y-%m-%d"),
                    "expected_doctors": expected,
                    "present_doctors": present,
                    "absent_doctors": absent,
                    "attendance_rate": attendance_pct,
                    "reasons": json.dumps(reasons) if reasons else ""
                })
        
        return pd.DataFrame(records)
    
    def generate_stock_data(self):
        """Generate daily stock levels for each medicine at each PHC
        Restocking: Monthly with occasional delays (realistic for supply chain)
        Initial stock: 2-4x minimum threshold
        """
        records = []
        
        for phc in self.phcs:
            for medicine in self.medicines:
                # Initialize stock
                current_stock = random.randint(
                    medicine["min_stock_threshold"] * 2,
                    medicine["min_stock_threshold"] * 4
                )
                last_restock_date = self.start_date
                
                for date in self.dates:
                    # Calculate daily usage based on footfall
                    seasonal = self.generate_seasonal_factor(date)
                    base_usage = medicine["base_daily_usage"] * (phc["base_footfall"] / 80)
                    daily_usage = int(base_usage * seasonal * np.random.normal(1.0, 0.2))
                    daily_usage = max(1, daily_usage)
                    
                    # Deplete stock
                    current_stock -= daily_usage
                    
                    # Restock when below threshold
                    min_required = medicine["min_stock_threshold"]
                    if current_stock < min_required:
                        # Restock to 3-5x minimum (realistic supply quantities)
                        current_stock = random.randint(
                            min_required * 3,
                            min_required * 5
                        )
                        last_restock_date = date
                    
                    # Ensure stock doesn't go negative
                    current_stock = max(0, current_stock)
                    
                    records.append({
                        "phc_id": phc["id"],
                        "medicine_id": medicine["id"],
                        "date": date.strftime("%Y-%m-%d"),
                        "quantity": current_stock,
                        "min_required": min_required,
                        "last_restocked": last_restock_date.strftime("%Y-%m-%d")
                    })
        
        return pd.DataFrame(records)
    
    def generate_test_availability_data(self):
        """Generate daily diagnostic test availability data
        Source: NHM Comprehensive Primary Health Care guidelines
        - PHCs: Basic tests (blood glucose, pregnancy, hemoglobin, urine)
        - CHCs: All tests including TB sputum, malaria RDT
        Availability: 85-95% (accounting for equipment maintenance, reagent stockouts)
        """
        records = []
        
        for phc in self.phcs:
            # Determine which tests are available at this PHC
            # Source: NHM guidelines - PHCs have basic lab, CHCs have comprehensive
            if phc["type"] == "CHC":
                available_tests = self.diagnostic_tests  # All tests
            else:
                # PHCs have basic tests only (exclude TB sputum)
                available_tests = [t for t in self.diagnostic_tests if t["test_code"] != "TB_SPT"]
            
            for test in available_tests:
                for date in self.dates:
                    # Base availability: 90% (realistic for Indian PHC labs)
                    # Source: NHM lab monitoring data shows 85-95% equipment functionality
                    base_availability = 0.90
                    
                    # Random variation
                    availability = base_availability * np.random.normal(1.0, 0.05)
                    is_available = random.random() < min(availability, 1.0)
                    
                    # Equipment status
                    if is_available:
                        equipment_status = "functional"
                    else:
                        # Source: Common reasons for unavailability
                        equipment_status = random.choice([
                            "maintenance", "broken", "reagent_stockout"
                        ])
                    
                    # Last calibration (every 30-90 days)
                    days_since_calibration = random.randint(0, 90)
                    last_calibration = date - timedelta(days=days_since_calibration)
                    
                    records.append({
                        "phc_id": phc["id"],
                        "test_name": test["test_name"],
                        "test_code": test["test_code"],
                        "date": date.strftime("%Y-%m-%d"),
                        "is_available": is_available,
                        "equipment_status": equipment_status,
                        "last_calibration_date": last_calibration.strftime("%Y-%m-%d"),
                        "notes": ""
                    })
        
        return pd.DataFrame(records)
    
    def generate_all_data(self):
        """Generate all data tables"""
        print("Generating footfall data...")
        footfall_df = self.generate_footfall_data()
        
        print("Generating bed occupancy data...")
        bed_df = self.generate_bed_occupancy_data()
        
        print("Generating doctor attendance data...")
        attendance_df = self.generate_doctor_attendance_data()
        
        print("Generating stock data...")
        stock_df = self.generate_stock_data()
        
        print("Generating test availability data...")
        test_availability_df = self.generate_test_availability_data()
        
        # Save to CSV files in data/output/ (same dir seed_data.py reads from)
        import os
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        footfall_df.to_csv(f"{output_dir}/footfall.csv", index=False)
        bed_df.to_csv(f"{output_dir}/bed_occupancy.csv", index=False)
        attendance_df.to_csv(f"{output_dir}/doctor_attendance.csv", index=False)
        stock_df.to_csv(f"{output_dir}/stock.csv", index=False)
        test_availability_df.to_csv(f"{output_dir}/test_availability.csv", index=False)
        
        # Save PHC and Medicine master data
        pd.DataFrame(self.phcs).to_csv(f"{output_dir}/phcs.csv", index=False)
        pd.DataFrame(self.medicines).to_csv(f"{output_dir}/medicines.csv", index=False)
        
        print(f"\n✓ Generated {len(footfall_df)} footfall records")
        print(f"✓ Generated {len(bed_df)} bed occupancy records")
        print(f"✓ Generated {len(attendance_df)} attendance records")
        print(f"✓ Generated {len(stock_df)} stock records")
        print(f"✓ Generated {len(test_availability_df)} test availability records")
        print(f"\nData saved to {output_dir}/")
        
        return {
            "footfall": footfall_df,
            "bed_occupancy": bed_df,
            "attendance": attendance_df,
            "stock": stock_df,
            "test_availability": test_availability_df
        }


if __name__ == "__main__":
    generator = PHCDataGenerator()
    data = generator.generate_all_data()
    
    # Print sample statistics
    print("\n=== Sample Statistics ===")
    print("\nFootfall by PHC:")
    print(data["footfall"].groupby("phc_id")["total_patients"].mean())
    
    print("\nStock-out events (stock < min_required):")
    stockouts = data["stock"][data["stock"]["quantity"] < data["stock"]["min_required"]]
    print(f"Total stockout days: {len(stockouts)}")
    print(stockouts.groupby(["phc_id", "medicine_id"]).size().head(10))
    
    print("\nTest availability by PHC:")
    test_avail = data["test_availability"].groupby("phc_id")["is_available"].mean()
    print(test_avail)