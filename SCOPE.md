# Smart Health - Project Scope Document

## District: Sample District (Fictional)
## PHCs/CHCs: 6 facilities
- PHC-Rampura
- PHC-Krishnanagar
- PHC-Sundarpur
- CHC-Mahavirnagar
- PHC-Lakshmipuram
- PHC-Gandhinagar

## Resources Tracked

### Medicines (6 Essential Medicines - NLEM 2023)
1. Paracetamol (pain/fever)
2. Amoxicillin (antibiotic)
3. ORS (oral rehydration)
4. Iron-Folic Acid (maternal health)
5. Antimalarial (Artemisinin-based)
6. Antihistamine (allergy/cold)

### Diagnostic Tests (6 Tests - NHM Guidelines)
1. Blood Glucose (pathology)
2. Malaria Rapid Test (rapid diagnostic)
3. Pregnancy Test (rapid diagnostic)
4. TB Sputum Test (pathology - CHC only)
5. Hemoglobin (pathology)
6. Urine Test (pathology)

## Metrics Definitions

### Footfall
- Daily patient visits per PHC
- Range: 20-150 patients/day (realistic for Indian PHCs)
- Patterns: Weekly (lower on weekends), seasonal (monsoon spike)
- Categories: new patients, follow-up, emergency cases

### Bed Availability
- Total beds per PHC: 6-30 (IPHS norms)
- Daily occupancy rate: 50-98%
- Track: available, occupied, reserved
- Optimal occupancy: 70-85% (IPHS guidelines)

### Doctor Attendance
- Expected doctors per PHC: 2-5 (IPHS norms)
- Track: present/absent with reason
- Realistic absenteeism: 12-22% (RHS 2021-22)
- Monday effect: 10% higher absenteeism

### Stock Levels
- Track daily stock per medicine per PHC
- Minimum stock threshold: 30 days supply
- Restocking: Monthly with occasional delays
- Stock-out prediction: Prophet time-series model

### Test Availability (NEW)
- Track daily availability of 6 diagnostic tests per PHC
- Equipment status: functional, maintenance, broken
- Last calibration date tracking
- Base availability: 85-95% (NHM guidelines)
- PHCs: Basic tests (exclude TB sputum)
- CHCs: All tests including TB sputum

## District Admin Dashboard Requirements

### At-a-Glance View
1. **Health Score Card**: Overall district performance (0-100)
   - Stock reliability: 35%
   - Doctor attendance: 25%
   - Bed utilization: 20%
   - Test availability: 20%
2. **Alert Feed**: Real-time stock-out warnings, underperforming centres
3. **Resource Map**: Visual overview of all 6 PHCs with status indicators
4. **Key Metrics**: 
   - Total patients served today
   - Medicine stock-out count
   - Average doctor attendance rate
   - Bed occupancy rate
   - Test availability rate (NEW)

### Drill-Down Capabilities
1. Individual PHC view with 30-day trends
2. Medicine-wise stock analysis
3. Doctor attendance patterns
4. Patient footfall analytics
5. Test availability trends (NEW)

### ML-Powered Features
1. **Stock-out Prediction**: Days until stockout per medicine per PHC
2. **Demand Forecasting**: 7-day patient footfall prediction
3. **Anomaly Detection**: Flag underperforming PHCs (composite score)
4. **Redistribution Recommendations**: "Move X units from PHC-A to PHC-B"

### Simulation Mode (NEW)
1. **Advance Day**: Move simulation forward by N days
2. **Trigger Events**:
   - Disease outbreak (footfall spike + medicine usage)
   - Delayed resupply (stock depletion)
   - Doctor absence spike (attendance drop)
3. **Live Demo**: Real-time system reactions visible to judges

### Multilingual Support (NEW)
1. English (default)
2. Hindi (हिं)
3. Tamil (தமிழ்)
4. Language switcher in navbar
5. All UI text translatable

## Data Time Period
- 12 months of historical data (Jan-Dec 2024)
- Daily granularity for all metrics
- Realistic seasonal patterns (monsoon: Jun-Sep, winter: Dec-Feb)
- Test availability data for all 365 days

## Data Sources and Calibration

### Doctor Absenteeism
- Source: Rural Health Statistics (RHS) 2021-22
- Rate: 15-20% absenteeism in rural areas
- Monday effect: 10% higher (NRHM studies)

### Medicine List
- Source: National List of Essential Medicines (NLEM) 2023
- 6 essential medicines for PHCs
- Thresholds: 30-day supply for average PHC load

### Bed Norms
- Source: Indian Public Health Standards (IPHS) guidelines
- PHCs: 6-10 beds
- CHCs: 30 beds
- Optimal occupancy: 70-85%

### Footfall Patterns
- Source: IDSP (Integrated Disease Surveillance Programme)
- Monsoon (Jun-Sep): 1.3x increase (malaria, dengue)
- Winter (Dec-Feb): 1.15x increase (respiratory diseases)
- Summer (Mar-May): 1.1x increase (heat-related)
- Weekends: 0.7x (30% lower attendance)

### Test Availability
- Source: NHM Comprehensive Primary Health Care guidelines
- PHCs: Basic tests (blood glucose, pregnancy, hemoglobin, urine)
- CHCs: All tests including TB sputum
- Base availability: 85-95% (equipment functionality rate)

## Success Criteria
- Dashboard loads in <2 seconds
- ML predictions update daily
- Clear visual distinction between CRUD and ML features
- Judges can understand the problem in <30 seconds from dashboard view
- Simulation mode demonstrates live system reactions
- Multilingual support works across all pages
- Test availability tracked and integrated into health scores

## Out of Scope (Future Enhancements)
- Mobile app for field officers
- Real-time SMS alerts
- Integration with HMIS/IHIP APIs
- Route optimization for redistribution logistics
- Advanced linear programming for redistribution
- More languages (Telugu, Bengali, Marathi)
- User authentication and role-based access
- Offline mode for areas with poor connectivity