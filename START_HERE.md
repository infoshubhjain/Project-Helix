# 🎉 EventFlow - Start Here!

## What You Have Now

Your app is configured for **web scraping + Google Calendar** only. No email parsing needed!

### ✅ What Works Out of the Box:
- **Browse 1000+ scraped events** from UIUC sources (no setup needed!)
- **Search and filter events** by keyword and category
- **View event details** with dates, times, locations

### ✅ What Requires Google Calendar Setup:
- **Connect your Google Calendar**
- **View your personal events** alongside scraped events
- **Add events to your calendar**
- **Month and agenda views**

---

## Quick Start (2 Options)

### Option 1: Just Browse Events (Zero Setup)
```bash
cd /Users/shubh/Desktop/Project-Helix
./run.sh
```
Open http://localhost:5000 and scroll to "Browse Events Near UIUC"

**That's it!** Events are already loaded from Firebase.

### Option 2: Add Google Calendar Integration (5 minutes)
Follow the guide: **[SIMPLE_SETUP.md](SIMPLE_SETUP.md)**

This will let you:
- Sync your Google Calendar
- Add scraped events to your calendar
- View everything in one place

---

## What Changed?

### 🔧 Code Changes:
1. **Email parsing button is hidden** - You won't see "📧 Add from Email" button
2. **No credentials required** - App runs without Azure/OpenRouter
3. **Simplified .env file** - No need to fill it out (it's optional)

### 📁 New Files:
- **[SIMPLE_SETUP.md](SIMPLE_SETUP.md)** - Simplified guide for Google Calendar only
- **[START_HERE.md](START_HERE.md)** - This file!

### 📚 Reference Files (If You Need Them):
- [QUICKSTART.md](QUICKSTART.md) - 5-minute setup
- [SETUP.md](SETUP.md) - Comprehensive guide
- [CREDENTIALS_GUIDE.md](CREDENTIALS_GUIDE.md) - Detailed credential instructions (skip email sections)

---

## Your Setup Checklist

### For Basic Browsing (No Setup Needed):
- [x] Dependencies installed (`pip3 install -r requirements.txt`)
- [x] Playwright installed (`playwright install chromium`)
- [x] Ready to run!

### For Google Calendar (Optional):
- [ ] Get `credentials.json` from Google Cloud Console
- [ ] Place it in `Project/calander/credentials.json`
- [ ] Run app and click "Connect Your Google Calendar"

---

## How to Run

### Start the App:
```bash
./run.sh
```

### Or manually:
```bash
cd Project
python3 app.py
```

### Then:
1. Open http://localhost:5000
2. Browse events immediately (no login needed!)
3. Optional: Click "Connect Your Google Calendar" to sync

---

## Features You Have

### 🌐 Browse Events Section
- **1000+ events** from 15+ sources
- **Real-time search** - Type to filter
- **Category filters** - Sports, Entertainment, Academic, etc.
- **Detailed view** - Click any event for full details

### 🗓️ Google Calendar Section (After Setup)
- **Your calendar** embedded in the app
- **Today's agenda** - See upcoming events
- **Add events** - Create new calendar events
- **Sync** - See both your events and scraped events

---

## File Structure (Simple)

```
Project-Helix/
├── START_HERE.md              ← You are here!
├── SIMPLE_SETUP.md            ← Google Calendar guide
├── run.sh                     ← Run this to start
└── Project/
    ├── app.py                 ← Flask backend
    ├── .env                   ← Empty (don't need to edit)
    ├── requirements.txt       ← Python dependencies
    ├── templates/
    │   └── index.html         ← UI with email button hidden
    ├── static/                ← Frontend JS/CSS
    └── calander/
        └── credentials.json   ← Create this for Google Calendar
```

---

## Troubleshooting

### Events not loading?
- Check internet connection
- Firebase might be down (check https://status.firebase.google.com/)
- Try refreshing the page

### Calendar not connecting?
- Make sure you created `credentials.json`
- Check file is at: `Project/calander/credentials.json`
- See [SIMPLE_SETUP.md](SIMPLE_SETUP.md) for step-by-step guide

### Port 5000 in use?
```bash
lsof -i :5000
kill -9 <PID>
```

### App won't start?
```bash
cd Project
pip3 install -r requirements.txt
playwright install chromium
```

---

## What About Email Parsing?

It's **disabled** and the button is **hidden**. You don't need it!

If you change your mind later, see [CREDENTIALS_GUIDE.md](CREDENTIALS_GUIDE.md) sections 1-2 for Azure + OpenRouter setup.

---

## Next Steps

1. **Start browsing now**:
   ```bash
   ./run.sh
   ```

2. **Optional: Add Google Calendar**:
   - Read [SIMPLE_SETUP.md](SIMPLE_SETUP.md)
   - Get `credentials.json` (5 minutes)
   - Connect and sync!

3. **Explore events**:
   - Search for keywords
   - Filter by category
   - Click for details

---

## Summary

| Feature | Status | Setup Required |
|---------|--------|----------------|
| Browse scraped events | ✅ Ready | None |
| Search & filter | ✅ Ready | None |
| View event details | ✅ Ready | None |
| Google Calendar sync | ⏳ Optional | credentials.json |
| Email parsing | ❌ Disabled | (Not needed) |

---

**🚀 Ready? Just run:**
```bash
./run.sh
```

**Open:** http://localhost:5000

**Questions?** Read [SIMPLE_SETUP.md](SIMPLE_SETUP.md) for Google Calendar setup.
