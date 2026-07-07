#!/usr/bin/env python
"""
Complete fix for trigger_simulation_event to advance ALL PHCs first, then apply event effects.
This script modifies the function in-place.
"""
import re
import os

MAIN_PY_PATH = os.path.join(os.path.dirname(__file__), '..', 'backend', 'main.py')

NEW_TRIGGER_FUNCTION = '''    @app.post("/api/simulation/trigger-event", response_model=SimulationResponse)
async def trigger_simulation_event(request: SimulationEventRequest, db: Session = Depends(get_db)):
    """Trigger a simulation event for a specific PHC while keeping ALL PHCs in sync.
    First advances ALL PHCs for N days (normal data), then applies event-specific adjustments only to the target PHC.
    """
    from app.database.schema import Stock, Footfall, BedOccupancy, DoctorAttendance, TestAvailability, Medicine
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'data'))
    from generator import PHCDataGenerator  # type: ignore
    
    phc = db.query(PHC).filter(PHC.id == request.phc_id).first()
    if not phc:
        raise HTTPException(status_code=404, detail="PHC not found")
    
    print(f"Triggering event: {request.event_type} at {phc.name} for {request.duration_days} days (DISTRICT-SYNC)")
    
    # Get DISTRICT-WIDE latest date (not just this PHC's date)
    latest_stock = db.query(Stock).order_by(Stock.date.desc()).first()
    if not latest_stock:
        raise HTTPException(status_code=400, detail="No data available")
    
    current_date = latest_stock.date
    generator = PHCDataGenerator()
    
    # Initialize changes dict
    changes = {
        "new_dates": [],
        "event_phc_changes": {"phc_id": request.phc_id, "phc_name": phc.name},  # Specific to triggered PHC
        "other_phcs_normal_days": [],  # Track what other PHCs advanced
        "district_summary": {
            "total_phcs_affected": 1,
            "total_stock_change": 0,
            "total_patients": 0,
            "total_emergency": 0,
            "avg_attendance": 0,
            "avg_bed_occupancy": 0
        }
    }
    
    # STEP 1: Generate N normal days for ALL OTHER PHCs (not the triggered one)
    all_phc_ids = [p.id for p in db.query(PHC).all()]
    other_phc_ids = [pid for pid in all_phc_ids if pid != request.phc_id]
    
    for day_offset in range(request.duration_days):
        target_date = current_date + timedelta(days=day_offset + 1)
        changes["new_dates"].append(target_date.strftime("%Y-%m-%d"))
        
        for other_phc_id in other_phc_ids:
            other_phc = db.query(PHC).filter(PHC.id == other_phc_id).first()
            if not other_phc:
                continue
            
            # Check if this other PHC already has data for target_date
            existing_stock = db.query(Stock).filter(
                Stock.phc_id == other_phc_id,
                Stock.date == target_date
            ).first()
            
            if not existing_stock:
                _generate_normal_day(db, other_phc, target_date, generator)
                changes["other_phcs_normal_days"].append((other_phc_id, target_date.strftime("%Y-%m-%d")))
    
    # STEP 2: Apply event effects to the TARGET PHC for each day
    # ... (existing event logic for disease_outbreak, delayed_resupply, doctor_absence_spike)
    
    if request.event_type == "disease_outbreak":
        # Spike footfall and medicine usage
        severity_multiplier = {"low": 1.5, "medium": 2.0, "high": 2.5}.get(request.severity, 2.0)
        
        for day in range(request.duration_days):
            event_date = current_date + timedelta(days=day + 1)
            
            # Generate event-adjusted footfall
            footfall = db.query(Footfall).filter(
                Footfall.phc_id == request.phc_id,
                Footfall.date == event_date
            ).first()
            
            if not footfall:
                seasonal = generator.generate_seasonal_factor(event_date)
                weekly = generator.generate_weekly_factor(event_date)
                base_footfall = getattr(phc, 'base_footfall', None) or 80
                noise = np.random.normal(1.0, 0.15)
                total_patients = int(base_footfall * seasonal * weekly * noise * severity_multiplier)
                total_patients = max(20, min(200, total_patients))
                
                footfall = Footfall(
                    phc_id=request.phc_id,
                    date=event_date,
                    total_patients=total_patients,
                    new_patients=int(total_patients * random.uniform(0.3, 0.5)),
                    follow_up_patients=0,
                    emergency_cases=int(total_patients * random.uniform(0.05, 0.15))
                )
                footfall.follow_up_patients = total_patients - footfall.new_patients - footfall.emergency_cases
                db.add(footfall)
            else:
                footfall.total_patients = int(footfall.total_patients * severity_multiplier)
                footfall.emergency_cases = int(footfall.emergency_cases * severity_multiplier * 1.5)
            
            changes["event_phc_changes"]["footfall"] = changes["event_phc_changes"].get("footfall", [])
            changes["event_phc_changes"]["footfall"].append({
                "date": event_date.strftime("%Y-%m-%d"),
                "total_patients": footfall.total_patients,
                "emergency_cases": footfall.emergency_cases
            })
            changes["district_summary"]["total_patients"] += footfall.total_patients
            changes["district_summary"]["total_emergency"] += footfall.emergency_cases
            
            # Generate event-adjusted bed occupancy (boosted by outbreak)
            bed = db.query(BedOccupancy).filter(
                BedOccupancy.phc_id == request.phc_id,
                BedOccupancy.date == event_date
            ).first()
            
            if not bed:
                existing_bed = db.query(BedOccupancy).filter(
                    BedOccupancy.phc_id == request.phc_id
                ).first()
                reserved_beds_stable = existing_bed.reserved_beds if existing_bed else min(max(0, int(phc.total_beds * 0.1)), 2)
                
                seasonal = generator.generate_seasonal_factor(event_date)
                base_occupancy = random.uniform(0.65, 0.85) * seasonal * np.random.normal(1.0, 0.1)
                base_occupancy = max(0.5, min(0.98, base_occupancy))
                occupied = int(phc.total_beds * base_occupancy)
                reserved = reserved_beds_stable
                available = max(0, phc.total_beds - occupied - reserved)
                occupancy_rate = round((occupied / phc.total_beds) * 100, 2) if phc.total_beds > 0 else 0
                
                bed = BedOccupancy(
                    phc_id=request.phc_id,
                    date=event_date,
                    total_beds=phc.total_beds,
                    occupied_beds=occupied,
                    reserved_beds=reserved,
                    available_beds=available,
                    occupancy_rate=occupancy_rate
                )
                db.add(bed)
            
            # Apply outbreak bed pressure
            emergency_ratio = (footfall.emergency_cases / max(footfall.total_patients, 1))
            bed_pressure = 1.0 + (severity_multiplier - 1.0) * (0.3 + 0.7 * emergency_ratio)
            new_occupied = min(int(bed.occupied_beds * bed_pressure), bed.total_beds)
            bed.occupied_beds = new_occupied
            bed.available_beds = max(0, bed.total_beds - new_occupied - bed.reserved_beds)
            bed.occupancy_rate = round((new_occupied / bed.total_beds) * 100, 2) if bed.total_beds > 0 else 0
            
            changes["event_phc_changes"]["beds"] = changes["event_phc_changes"].get("beds", [])
            changes["event_phc_changes"]["beds"].append({
                "date": event_date.strftime("%Y-%m-%d"),
                "occupancy_rate": bed.occupancy_rate,
                "outbreak_adjusted": True
            })
            changes["district_summary"]["avg_bed_occupancy"] += bed.occupancy_rate
            
            # Generate event-adjusted doctor attendance
            attendance = db.query(DoctorAttendance).filter(
                DoctorAttendance.phc_id == request.phc_id,
                DoctorAttendance.date == event_date
            ).first()
            
            if not attendance:
                base_attendance = random.uniform(0.78, 0.88)
                if event_date.weekday() == 0:
                    attendance_rate = max(0.6, min(0.98, base_attendance * 0.9))
                else:
                    attendance_rate = max(0.6, min(0.98, base_attendance * np.random.normal(1.0, 0.05)))
                present = int(phc.expected_doctors * attendance_rate)
                present = max(0, min(phc.expected_doctors, present))
                absent = phc.expected_doctors - present
                attendance_rate_pct = round((present / phc.expected_doctors) * 100, 2) if phc.expected_doctors > 0 else 0.0
                
                attendance = DoctorAttendance(
                    phc_id=request.phc_id,
                    date=event_date,
                    expected_doctors=phc.expected_doctors,
                    present_doctors=present,
                    absent_doctors=absent,
                    attendance_rate=attendance_rate_pct,
                    patient_load_per_doctor=round(footfall.total_patients / max(present, 1), 1),
                    reasons=""
                )
                db.add(attendance)
            else:
                attendance.patient_load_per_doctor = round(
                    footfall.total_patients / max(attendance.present_doctors, 1), 1
                )
            
            changes["event_phc_changes"]["attendance"] = changes["event_phc_changes"].get("attendance", [])
            changes["event_phc_changes"]["attendance"].append({
                "date": event_date.strftime("%Y-%m-%d"),
                "attendance_rate": attendance.attendance_rate,
                "patient_load_per_doctor": attendance.patient_load_per_doctor
            })
            changes["district_summary"]["avg_attendance"] += attendance.attendance_rate
            
            # Generate event-adjusted stock for each medicine
            medicines = db.query(Medicine).all()
            for medicine in medicines:
                stock = db.query(Stock).filter(
                    Stock.phc_id == request.phc_id,
                    Stock.medicine_id == medicine.id,
                    Stock.date == event_date
                ).first()
                
                extra_usage = int(medicine.base_daily_usage * 0.5 * severity_multiplier)
                
                if not stock:
                    latest_med_stock = db.query(Stock).filter(
                        Stock.phc_id == request.phc_id,
                        Stock.medicine_id == medicine.id
                    ).order_by(Stock.date.desc()).first()
                    
                    if latest_med_stock:
                        current_stock = latest_med_stock.quantity
                        restock_arrives_on = latest_med_stock.restock_arrives_on
                        last_restocked = latest_med_stock.last_restocked
                    else:
                        current_stock = medicine.min_stock_threshold * 3
                        restock_arrives_on = None
                        last_restocked = None
                    
                    base_footfall = getattr(phc, 'base_footfall', None) or 80
                    base_usage = medicine.base_daily_usage * (base_footfall / 80)
                    daily_usage = int(base_usage * severity_multiplier) + extra_usage
                    new_stock = max(0, current_stock - daily_usage)
                    
                    if restock_arrives_on and restock_arrives_on <= event_date:
                        new_stock = random.randint(medicine.min_stock_threshold * 3, medicine.min_stock_threshold * 5)
                        last_restocked = event_date
                        restock_arrives_on = None
                    elif new_stock < medicine.min_stock_threshold and not restock_arrives_on:
                        restock_delay = random.randint(3, 5)
                        restock_arrives_on = event_date + timedelta(days=restock_delay)
                    
                    stock = Stock(
                        phc_id=request.phc_id,
                        medicine_id=medicine.id,
                        date=event_date,
                        quantity=new_stock,
                        min_required=medicine.min_stock_threshold,
                        last_restocked=last_restocked,
                        restock_arrives_on=restock_arrives_on
                    )
                    db.add(stock)
                else:
                    stock.quantity = max(0, stock.quantity - extra_usage)
                
                changes["event_phc_changes"]["stock"] = changes["event_phc_changes"].get("stock", [])
                changes["event_phc_changes"]["stock"].append({
                    "medicine_id": medicine.id,
                    "medicine_name": medicine.name,
                    "date": event_date.strftime("%Y-%m-%d"),
                    "quantity": stock.quantity,
                    "extra_usage": -extra_usage
                })
                changes["district_summary"]["total_stock_change"] += stock.quantity
            
            # Generate test availability
            tests = db.query(TestAvailability).filter(
                TestAvailability.phc_id == request.phc_id,
                TestAvailability.date == current_date
            ).all()
            
            for test in tests:
                is_available = random.random() < 0.9
                new_test = TestAvailability(
                    phc_id=request.phc_id,
                    test_name=test.test_name,
                    test_code=test.test_code,
                    date=event_date,
                    is_available=is_available,
                    equipment_status="functional" if is_available else "maintenance",
                    last_calibration_date=test.last_calibration_date,
                    notes=""
                )
                db.add(new_test)
        
        changes["event_phc_changes"]["severity_multiplier"] = severity_multiplier
        changes["event_phc_changes"]["event_type"] = "disease_outbreak"
    
    elif request.event_type == "delayed_resupply":
        delay_days = {"low": 5, "medium": 10, "high": 15}.get(request.severity, 10)
        
        for day in range(1, min(delay_days + 1, 8)):
            future_date = current_date + timedelta(days=day)
            changes["new_dates"].append(future_date.strftime("%Y-%m-%d"))
            
            medicines = db.query(Medicine).all()
            for medicine in medicines:
                stock = db.query(Stock).filter(
                    Stock.phc_id == request.phc_id,
                    Stock.medicine_id == medicine.id,
                    Stock.date == future_date
                ).first()
                
                if not stock:
                    latest_med_stock = db.query(Stock).filter(
                        Stock.phc_id == request.phc_id,
                        Stock.medicine_id == medicine.id
                    ).order_by(Stock.date.desc()).first()
                    
                    if latest_med_stock:
                        current_stock = latest_med_stock.quantity
                    else:
                        current_stock = medicine.min_stock_threshold * 3
                    
                    base_usage = medicine.base_daily_usage * 0.8
                    new_stock = max(0, current_stock - int(base_usage))
                    
                    stock = Stock(
                        phc_id=request.phc_id,
                        medicine_id=medicine.id,
                        date=future_date,
                        quantity=new_stock,
                        min_required=medicine.min_stock_threshold,
                        last_restocked=current_date
                    )
                    db.add(stock)
                else:
                    base_usage = medicine.base_daily_usage * 0.8
                    stock.quantity = max(0, stock.quantity - int(base_usage))
                
                changes["event_phc_changes"]["stock"] = changes["event_phc_changes"].get("stock", [])
                changes["event_phc_changes"]["stock"].append({
                    "medicine_id": medicine.id,
                    "medicine_name": medicine.name,
                    "date": future_date.strftime("%Y-%m-%d"),
                    "quantity": stock.quantity,
                    "change": -int(base_usage)
                })
                changes["district_summary"]["total_stock_change"] += stock.quantity
        
        changes["event_phc_changes"]["event_type"] = "delayed_resupply"
    
    elif request.event_type == "doctor_absence_spike":
        absence_rate = {"low": 0.4, "medium": 0.6, "high": 0.8}.get(request.severity, 0.6)
        
        for day in range(request.duration_days):
            event_date = current_date + timedelta(days=day + 1)
            
            attendance = db.query(DoctorAttendance).filter(
                DoctorAttendance.phc_id == request.phc_id,
                DoctorAttendance.date == event_date
            ).first()
            
            if not attendance:
                base_attendance = random.uniform(0.78, 0.88)
                if event_date.weekday() == 0:
                    attendance_rate = max(0.6, min(0.98, base_attendance * 0.9))
                else:
                    attendance_rate = max(0.6, min(0.98, base_attendance * np.random.normal(1.0, 0.05)))
                present = int(phc.expected_doctors * attendance_rate)
                present = max(0, min(phc.expected_doctors, present))
                absent = phc.expected_doctors - present
                attendance_rate_pct = round((present / phc.expected_doctors) * 100, 2) if phc.expected_doctors > 0 else 0.0
                
                attendance = DoctorAttendance(
                    phc_id=request.phc_id,
                    date=event_date,
                    expected_doctors=phc.expected_doctors,
                    present_doctors=present,
                    absent_doctors=absent,
                    attendance_rate=attendance_rate_pct,
                    reasons=""
                )
                db.add(attendance)
            
            new_present = int(attendance.expected_doctors * (1 - absence_rate))
            new_present = max(0, min(attendance.expected_doctors, new_present))
            attendance.present_doctors = new_present
            attendance.absent_doctors = attendance.expected_doctors - new_present
            if attendance.expected_doctors > 0:
                attendance.attendance_rate = round((new_present / attendance.expected_doctors) * 100, 2)
            else:
                attendance.attendance_rate = 0.0
            
            changes["event_phc_changes"]["attendance"] = changes["event_phc_changes"].get("attendance", [])
            changes["event_phc_changes"]["attendance"].append({
                "date": event_date.strftime("%Y-%m-%d"),
                "attendance_rate": attendance.attendance_rate,
                "absent_doctors": attendance.absent_doctors
            })
            changes["district_summary"]["avg_attendance"] += attendance.attendance_rate
            
            # Also generate bed and footfall for these dates if they don't exist
            footfall = db.query(Footfall).filter(
                Footfall.phc_id == request.phc_id,
                Footfall.date == event_date
            ).first()
            
            if not footfall:
                seasonal = generator.generate_seasonal_factor(event_date)
                weekly = generator.generate_weekly_factor(event_date)
                base_footfall = getattr(phc, 'base_footfall', None) or 80
                noise = np.random.normal(1.0, 0.15)
                total_patients = int(base_footfall * seasonal * weekly * noise)
                total_patients = max(20, min(200, total_patients))
                
                footfall = Footfall(
                    phc_id=request.phc_id,
                    date=event_date,
                    total_patients=total_patients,
                    new_patients=int(total_patients * random.uniform(0.3, 0.5)),
                    follow_up_patients=total_patients - int(total_patients * random.uniform(0.3, 0.5)),
                    emergency_cases=int(total_patients * random.uniform(0.05, 0.15))
                )
                footfall.follow_up_patients = total_patients - footfall.new_patients - footfall.emergency_cases
                db.add(footfall)
                
                changes["event_phc_changes"]["footfall"] = changes["event_phc_changes"].get("footfall", [])
                changes["event_phc_changes"]["footfall"].append({
                    "date": event_date.strftime("%Y-%m-%d"),
                    "total_patients": footfall.total_patients
                })
                changes["district_summary"]["total_patients"] += footfall.total_patients
        
        changes["event_phc_changes"]["event_type"] = "doctor_absence_spike"
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown event type: {request.event_type}")
    
    db.commit()
    
    # Invalidate redistribution cache
    ml_manager.redistribution_engine.invalidate_cache()
    
    # Calculate averages
    if request.duration_days > 0:
        if len(changes.get("event_phc_changes", {}).get("attendance", [])) > 0:
            changes["district_summary"]["avg_attendance"] = round(changes["district_summary"]["avg_attendance"] / request.duration_days, 2)
        if len(changes.get("event_phc_changes", {}).get("beds", [])) > 0:
            changes["district_summary"]["avg_bed_occupancy"] = round(changes["district_summary"]["avg_bed_occupancy"] / request.duration_days, 2)
    
    return SimulationResponse(
        success=True,
        message=f"Event {request.event_type} triggered at {phc.name}. {len(changes['other_phcs_normal_days'])} other PHCs advanced {request.duration_days} day(s) each with normal data.",
        simulated_date=current_date + timedelta(days=request.duration_days),
        changes=changes
    )


def _generate_normal_day(db, phc, target_date, generator):
    """Helper function to generate one normal day of data for a PHC."""
    from app.database.schema import Stock, Footfall, BedOccupancy, DoctorAttendance, TestAvailability, Medicine
    
    # Generate footfall
    seasonal = generator.generate_seasonal_factor(target_date)
    weekly = generator.generate_weekly_factor(target_date)
    base_footfall = phc.base_footfall if hasattr(phc, 'base_footfall') else 80
    noise = np.random.normal(1.0, 0.15)
    total_patients = int(base_footfall * seasonal * weekly * noise)
    total_patients = max(20, min(200, total_patients))
    
    footfall = Footfall(
        phc_id=phc.id,
        date=target_date,
        total_patients=total_patients,
        new_patients=int(total_patients * random.uniform(0.3, 0.5)),
        follow_up_patients=total_patients - int(total_patients * random.uniform(0.3, 0.5)),
        emergency_cases=int(total_patients * random.uniform(0.05, 0.15))
    )
    footfall.follow_up_patients = total_patients - footfall.new_patients - footfall.emergency_cases
    db.add(footfall)
    
    # Generate bed occupancy
    existing_beds = db.query(BedOccupancy).filter(BedOccupancy.phc_id == phc.id).first()
    reserved_beds_stable = existing_beds.reserved_beds if existing_beds else min(max(0, int(phc.total_beds * 0.1)), 2)
    occupied = int(phc.total_beds * max(0.5, min(0.98, random.uniform(0.65, 0.85) * seasonal * np.random.normal(1.0, 0.1))))
>>>>>>
occupied = int(phc.total_beds * max(0.5, min(0.98, random.uniform(0.65, 0.85) * seasonal * np.random.normal(1.0, 0.1))))
    available = max(0, phc.total_beds - occupied - reserved_beds_stable)
    
    bed = BedOccupancy(
        phc_id=phc.id,
        date=target_date,
        total_beds=phc.total_beds,
        occupied_beds=occupied,
        reserved_beds=reserved_beds_stable,
        available_beds=available,
        occupancy_rate=round((occupied / phc.total_beds) * 100, 2) if phc.total_beds > 0 else 0
    )
    db.add(bed)
    
    # Generate doctor attendance
    base_attendance = random.uniform(0.78, 0.88)
    if target_date.weekday() == 0:
        attendance_rate = max(0.6, min(0.98, base_attendance * 0.9))
    else:
        attendance_rate = max(0.6, min(0.98, base_attendance * np.random.normal(1.0, 0.05)))
    present = int(phc.expected_doctors * attendance_rate)
    present = max(0, min(phc.expected_doctors, present))
    absent = phc.expected_doctors - present
    attendance_rate_pct = round((present / phc.expected_doctors) * 100, 2) if phc.expected_doctors > 0 else 0.0
    
    attendance = DoctorAttendance(
        phc_id=phc.id,
        date=target_date,
        expected_doctors=phc.expected_doctors,
        present_doctors=present,
        absent_doctors=absent,
        attendance_rate=attendance_rate_pct,
        reasons=""
    )
    db.add(attendance)
    
    # Generate stock updates
    medicines = db.query(Medicine).all()
    for medicine in medicines:
        latest = db.query(Stock).filter(
            Stock.phc_id == phc.id, Stock.medicine_id == medicine.id
        ).order_by(Stock.date.desc()).first()
        
        if latest:
            current = latest.quantity
            usage = int(medicine.base_daily_usage * (base_footfall / 80) * np.random.normal(1.0, 0.2))
            new_q = max(0, current - max(1, usage))
            restock_date = latest.restock_arrives_on
            if restock_date and restock_date <= target_date:
                new_q = random.randint(medicine.min_stock_threshold * 3, medicine.min_stock_threshold * 5)
                restock_date = None
            elif new_q < medicine.min_stock_threshold and not restock_date:
                restock_date = target_date + timedelta(days=random.randint(3, 5))
            
            stock = Stock(
                phc_id=phc.id, medicine_id=medicine.id, date=target_date,
                quantity=new_q, min_required=medicine.min_stock_threshold,
                last_restocked=latest.last_restocked, restock_arrives_on=restock_date
            )
            db.add(stock)
    
    # Generate test availability
    tests = db.query(TestAvailability).filter(
        TestAvailability.phc_id == phc.id,
        TestAvailability.date <= target_date
    ).all()
    for test in tests:
        is_avail = random.random() < 0.9
        new_test = TestAvailability(
            phc_id=phc.id, test_name=test.test_name, test_code=test.test_code,
            date=target_date, is_available=is_avail,
            equipment_status="functional" if is_avail else "maintenance",
            last_calibration_date=test.last_calibration_date, notes=""
        )
        db.add(new_test)
'''

def apply_fix():
    with open(MAIN_PY_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove corrupted lines
    lines = content.split('\n')
    cleaned = '\n'.join([l for l in lines if '>>>>>>>' not in l])
    
    # Find trigger-event function start and end
    trigger_start = cleaned.find('@app.post("/api/simulation/trigger-event"')
    if trigger_start == -1:
        trigger_start = cleaned.find("@app.post('/api/simulation/trigger-event'")
    
    # Find the next endpoint (dashboard summary) after trigger-event
    next_indicator = '\n\n@app.get("/api/dashboard/summary"'
    if trigger_start != -1:
        next_pos = cleaned.find(next_indicator, trigger_start)
        if next_pos == -1:
            next_pos = cleaned.find("\n\nif __name__", trigger_start)
        if next_pos == -1:
            next_pos = len(cleaned) - 200  # fallback
        
        # Replace the entire trigger-event function
        before_trigger = cleaned[:trigger_start]
        after_trigger = cleaned[next_pos:] if next_pos != -1 else ''
        
        # Combine with new function
        fixed_content = before_trigger + NEW_TRIGGER_FUNCTION + after_trigger
        
        with open(MAIN_PY_PATH, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print("Applied trigger_simulation_event fix successfully!")
        print("All PHCs will now be advanced when triggering an event for one PHC.")
    else:
        print("ERROR: Could not find trigger-event function")

if __name__ == "__main__":
    apply_fix()