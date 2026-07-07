# 🚀 START HERE - Smart Health Demo

## ⚠️ IMPORTANT: Database Location Issue

The database file `smart_health.db` is created at:
```
d:\Hack2Skill\smart-health\smart_health.db
```

**NOT** in the backend folder!

---

## ✅ SOLUTION: Use This Script (One Command)

### Windows - Double Click This File:
```
scripts\quick_start.bat
```

**OR** run in PowerShell:
```powershell
cd d:\Hack2Skill\smart-health
.\scripts\quick_start.bat
```

This will:
1. ✓ Create the database (if needed)
2. ✓ Generate all data
3. ✓ Seed the database with 6 PHCs
4. ✓ Start the backend server
5. ✓ Start the frontend server
6. ✓ Open your browser automatically

---

## 🔧 Manual Setup (If Script Fails)

### Step 1: Delete Old Database (If Exists)
```powershell
cd d:\Hack2Skill\smart-health
del smart_health.db
```

### Step 2: Setup Database
```powershell
cd d:\Hack2Skill\smart-health
python setup_database.py
```

You should see:
```
✓ phcs: 6 records
✓ medicines: 20 records
✓ stock: 2160 records
... etc
```

### Step 3: Start Backend (Terminal 1)
```powershell
cd d:\Hack2Skill\smart-health\backend
python -m uvicorn main:app --reload
```

**Look for this message:**
```
✓ Smart Health API started successfully
```

### Step 4: Start Frontend (Terminal 2)
```powershell
cd d:\Hack2Skill\smart-health\frontend
npm run dev
```

### Step 5: Open Browser
```
http://localhost:5173
```

---

## 🎯 Verify It's Working

### Test 1: Check Database Exists
```powershell
cd d:\Hack2Skill\smart-health
python test_setup.py
```

You should see all green checkmarks (✓).

### Test 2: Check Backend API
Open in browser:
```
http://localhost:8000/api/phcs
```

You should see JSON with 6 PHCs.

### Test 3: Check Simulation Page
Go to:
```
http://localhost:5173/simulation
```

The "Select PHC" dropdown should now show 6 PHCs (not empty!).

---

## 🐛 Troubleshooting

### Problem: "No PHCs found" in dropdown

**Cause:** Database is empty or doesn't exist

**Solution:**
```powershell
# 1. Make sure you're in the right directory
cd d:\Hack2Skill\smart-health

# 2. Delete database if it exists
del smart_health.db

# 3. Run setup
python setup_database.py

# 4. Restart backend (IMPORTANT!)
cd backend
python -m uvicorn main:app --reload

# 5. Refresh browser
```

### Problem: Backend says "Auto-seeding..."

**This is good!** The backend automatically creates the database if it's empty. Just wait for it to finish, then refresh the browser.

### Problem: Still getting errors

**Complete reset:**
```powershell
# Stop all servers (Ctrl+C in both terminals)

# Delete database
cd d:\Hack2Skill\smart-health
del smart_health.db

# Run setup
python setup_database.py

# Start backend
cd backend
python -m uvicorn main:app --reload

# In a NEW terminal, start frontend
cd frontend
npm run dev

# Refresh browser
```

---

## 📋 Quick Reference

| What | Command |
|------|---------|
| **One-click setup** | `scripts\quick_start.bat` |
| **Setup database only** | `python setup_database.py` |
| **Test setup** | `python test_setup.py` |
| **Start backend** | `cd backend && python -m uvicorn main:app --reload` |
| **Start frontend** | `cd frontend && npm run dev` |
| **Open app** | http://localhost:5173 |
| **API docs** | http://localhost:8000/docs |

---

## 🎬 For Your Demo

### The Perfect Demo Flow:

1. **Open Simulation Page**: http://localhost:5173/simulation
   - Show the PHC dropdown is populated ✓

2. **Click "Advance 1 Day"**
   - Watch it process
   - Show success message

3. **Navigate to Dashboard** (click "Back to Dashboard")
   - Show updated metrics
   - Point out the date has changed

4. **Trigger "Disease Outbreak"**
   - Go back to Simulation
   - Select a PHC
   - Click "Trigger Event"
   - Show the impact message

5. **Check Alerts Page**
   - New alerts should appear
   - Show the severity levels

6. **Check Recommendations**
   - New redistribution suggestions
   - Show the AI-powered insights

7. **Switch Language**
   - Click language switcher (EN → HI → TA)
   - Show multilingual support

---

## ✨ Key Features to Highlight

- ✅ **Live Simulation**: Click buttons, see real-time changes
- ✅ **ML Predictions**: Stock-out predictions, demand forecasting
- ✅ **Anomaly Detection**: Auto-detects underperforming PHCs
- ✅ **Smart Redistribution**: AI suggests resource reallocation
- ✅ **Multilingual**: English, Hindi, Tamil
- ✅ **Test Availability**: Tracks diagnostic test availability
- ✅ **Real-time Alerts**: Instant notifications for critical issues

---

## 🆘 Emergency Help

If nothing works, run this:
```powershell
cd d:\Hack2Skill\smart-health
python test_setup.py
```

This will tell you exactly what's wrong and how to fix it.

---

## 📞 Remember

- **Database location**: `d:\Hack2Skill\smart-health\smart_health.db`
- **Backend auto-seeds**: If database is empty, backend creates it automatically
- **Restart after seeding**: Always restart backend after creating database
- **Use the script**: `scripts\quick_start.bat` handles everything

---

**You've got this! The simulation will work perfectly! 🚀**