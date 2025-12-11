# How to Run Project Helix

## 🚀 Quick Start

### Method 1: Using the run script (Easiest)
```bash
cd /Users/shubh/Desktop/Project-Helix
./run.sh
```

Then open: **http://localhost:5001**

### Method 2: Direct Python command
```bash
cd /Users/shubh/Desktop/Project-Helix/Project
python3 app.py
```

Then open: **http://localhost:5001**

### Method 3: VS Code (For debugging)
1. Open the project in VS Code
2. Press `F5`
3. Select "Flask: Run Project Helix App"
4. Open: **http://localhost:5001**

---

## 📝 Important Notes

### Port Number
- **The app runs on PORT 5001** (not 5000)
- This is because port 5000 is used by macOS AirPlay Receiver

### First Time Opening
1. The app will start on http://localhost:5001
2. You'll see the Project Helix interface
3. Scroll down to "Browse Events Near UIUC" to see events
4. Events load automatically from Firebase

---

## 🎯 What You'll See

### Header Section:
- Project Helix @ Illinois logo
- "Connect Your Google Calendar" button (optional)

### Main Sections:
1. **Your Calendar** - Google Calendar iframe
2. **Upcoming Events** - Today's agenda
3. **Browse Events Near UIUC** - **START HERE!** ← This works immediately

### Browse Events:
- Search bar (type keywords to filter)
- Category dropdown
- Event cards showing:
  - Event title
  - Date and time
  - Location
  - Description
- Click any card for full details

---

## 🛠️ Troubleshooting

### App won't start?

**Try this:**
```bash
# Kill any process on port 5001
lsof -ti :5001 | xargs kill -9

# Try running again
./run.sh
```

### Port 5001 is also in use?

**Change to a different port:**
1. Edit `Project/app.py`
2. Change line: `app.run(debug=True, port=5001)`
3. To: `app.run(debug=True, port=5002)` (or any free port)
4. Update `run.sh` to show the new port
5. Restart the app

### Browser shows "This site can't be reached"?

**Check if Flask is running:**
```bash
# Look for "Running on http://127.0.0.1:5001"
# in the terminal where you ran ./run.sh
```

### Events not loading?

**Check:**
1. Internet connection (Firebase requires internet)
2. Browser console for errors (F12 → Console tab)
3. Refresh the page

### Disable macOS AirPlay Receiver (Optional)

If you really want to use port 5000:
1. System Settings → General → AirDrop & Handoff
2. Turn off "AirPlay Receiver"
3. Change app back to port 5000

---

## 📱 Testing the App

### Test 1: Home Page Loads
- Open http://localhost:5001
- Should see Project Helix interface
- No errors in browser console

### Test 2: Browse Events Works
- Scroll to "Browse Events Near UIUC"
- Should see event cards appearing
- Try typing in the search box
- Try selecting a category filter

### Test 3: Event Details
- Click any event card
- Modal should open with full details
- Close button (×) should work

### Test 4: Search Functionality
- Type "sports" in search box
- Should filter to sports-related events
- Clear search to see all events again

---

## 🔧 Running Tests

Test everything is working:
```bash
cd /Users/shubh/Desktop/Project-Helix
python3 test_app.py
```

Should show:
```
✅ 7/8 tests passed
✅ Core functionality working
```

---

## 📚 Next Steps

### Just Browse Events:
- You're ready! Just run the app

### Add Google Calendar:
- Read [SIMPLE_SETUP.md](SIMPLE_SETUP.md)
- Get credentials.json from Google Cloud
- Place in `Project/calander/credentials.json`

---

## 🎉 You're All Set!

**To start:**
```bash
./run.sh
```

**Then open:** http://localhost:5001

**Enjoy browsing 1000+ campus events!** 🎓
