# EventFlow - Simple Setup (No Email Parsing)

## What You'll Get
✅ Browse 1000+ scraped campus events
✅ Google Calendar integration
✅ Add events to your calendar
✅ Search and filter events

❌ No email parsing (we're skipping that!)

---

## Setup in 3 Steps

### Step 1: Install Dependencies (2 minutes)
```bash
cd /Users/shubh/Desktop/Project-Helix/Project
pip3 install -r requirements.txt
playwright install chromium
```

### Step 2: Get Google Calendar Credentials (5 minutes)

This allows the app to connect to your Google Calendar.

#### A. Go to Google Cloud Console
1. Visit: https://console.cloud.google.com/
2. Sign in with your Google account

#### B. Create a Project
1. Click the project dropdown at the top
2. Click **"NEW PROJECT"**
3. Name it: `EventFlow`
4. Click **"CREATE"**
5. Wait a few seconds, then select your new project from the dropdown

#### C. Enable Google Calendar API
1. Search for "Calendar API" in the top search bar
2. Click **"Google Calendar API"**
3. Click **"ENABLE"**

#### D. Create OAuth Consent Screen
1. Left sidebar → **"OAuth consent screen"**
2. Choose **"External"**
3. Click **"CREATE"**
4. Fill in:
   - **App name**: `EventFlow`
   - **User support email**: Your email (from dropdown)
   - **Developer contact**: Your email
5. Click **"SAVE AND CONTINUE"**
6. Click **"ADD OR REMOVE SCOPES"**
7. Search and check: `https://www.googleapis.com/auth/calendar`
8. Click **"UPDATE"** → **"SAVE AND CONTINUE"**
9. Click **"+ ADD USERS"**
10. Enter your email address
11. Click **"ADD"** → **"SAVE AND CONTINUE"**
12. Click **"BACK TO DASHBOARD"**

#### E. Create Credentials
1. Left sidebar → **"Credentials"**
2. Click **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**
3. **Application type**: Select **"Desktop app"**
4. **Name**: `EventFlow Desktop`
5. Click **"CREATE"**
6. Click **"DOWNLOAD JSON"** in the popup
7. Rename the downloaded file to `credentials.json`
8. Move it to: `/Users/shubh/Desktop/Project-Helix/Project/calander/credentials.json`

**✅ That's it! You're done with credentials.**

### Step 3: Run the App (30 seconds)
```bash
cd /Users/shubh/Desktop/Project-Helix
./run.sh
```

Open in browser: **http://localhost:5000**

---

## First Time Using the App

### 1. Connect Your Calendar
- Click **"🔗 Connect Your Google Calendar"** in the top right
- Sign in with Google when prompted
- Grant calendar permissions
- Your calendar will appear!

### 2. Browse Scraped Events
- Scroll to **"Browse Events Near UIUC"**
- 1000+ events are already loaded from Firebase
- Search by keyword or filter by category

### 3. Add Events to Your Calendar
- Click on any event card
- View event details
- Click **"Add to Calendar"** (if that button exists)
- Or use the **"+ Add Event"** button to create your own

---

## File Structure (Simple Version)

You only need these files:
```
Project-Helix/
├── run.sh                       # Start the app
└── Project/
    ├── app.py                   # Flask app
    ├── requirements.txt         # Dependencies
    └── calander/
        └── credentials.json     # Google OAuth (YOU CREATE THIS)
```

That's it! No `.env` file needed.

---

## Troubleshooting

### "credentials.json not found"
- Make sure it's at: `Project/calander/credentials.json`
- Check the filename is exactly `credentials.json` (not `credentials.json.json`)

### "OAuth client not found"
- Verify Google Calendar API is enabled in Google Cloud Console
- Check OAuth consent screen is configured
- Make sure you added yourself as a test user

### Calendar not connecting
- Try deleting `Project/calander/token.json` if it exists
- Restart the app and reconnect

### Port 5000 in use
```bash
lsof -i :5000
kill -9 <PID>
```

---

## That's It!

No Azure AD, no OpenRouter, no email parsing. Just:
1. ✅ Install dependencies
2. ✅ Get Google credentials
3. ✅ Run the app

**Questions?** The app will work immediately for browsing events. Google Calendar sync requires the `credentials.json` file above.

---

## Optional: Hide Email Parsing Button

If you want to hide the email parsing button from the UI, I can do that for you. Just let me know!
