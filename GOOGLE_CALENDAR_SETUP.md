# Google Calendar Setup Guide

## 🎯 What This Feature Does

Once connected, you can:
- ✅ View your personal Google Calendar in the app
- ✅ See your upcoming events in the agenda view
- ✅ Add scraped campus events to your Google Calendar
- ✅ Create new events that sync to your calendar
- ✅ See everything in one place

---

## 📋 Prerequisites

- A Google account (Gmail, university email, etc.)
- 5-10 minutes of setup time
- Internet connection

---

## 🚀 Setup Steps (Detailed)

### Step 1: Go to Google Cloud Console

1. Open your browser
2. Go to: **https://console.cloud.google.com/**
3. Sign in with your Google account

---

### Step 2: Create a New Project

1. **At the top of the page**, look for the project dropdown
   - It might say "Select a project" or show a current project name
   - It's next to the Google Cloud logo

2. **Click the dropdown** → Click **"NEW PROJECT"** in the top-right corner

3. **Fill in the project details:**
   - **Project name**: `Project Helix` (or any name you like)
   - **Organization**: Leave as "No organization" (unless you have one)
   - **Location**: Leave as default

4. **Click "CREATE"**

5. **Wait a few seconds** for the project to be created

6. **Select your new project** from the dropdown to make it active

---

### Step 3: Enable Google Calendar API

1. **In the left sidebar**, click **"APIs & Services"** → **"Library"**
   - Or use the search bar at the top and type: "API Library"

2. **In the API Library search box**, type: `Google Calendar API`

3. **Click on "Google Calendar API"** from the search results
   - It should have a blue calendar icon

4. **Click the "ENABLE" button** (blue button)

5. **Wait** for it to enable (takes a few seconds)
   - You'll see a checkmark when it's done

---

### Step 4: Configure OAuth Consent Screen

This tells Google what your app is and who can use it.

1. **In the left sidebar**, click **"OAuth consent screen"**

2. **Choose user type:**
   - Select **"External"** (radio button)
   - Click **"CREATE"**

3. **Fill in OAuth consent screen (Page 1):**
   - **App name**: `Project Helix` or `UIUC Calendar App`
   - **User support email**: Select your email from dropdown
   - **App logo**: Leave blank (optional)
   - **App domain**: Leave blank
   - **Authorized domains**: Leave blank
   - **Developer contact information**: Enter your email address

4. **Scroll down** and click **"SAVE AND CONTINUE"**

5. **Scopes (Page 2):**
   - Click **"ADD OR REMOVE SCOPES"**
   - In the filter box, search for: `calendar`
   - Find and check the box for:
     - ✅ `https://www.googleapis.com/auth/calendar`
     - Description: "See, edit, share, and permanently delete all the calendars you can access using Google Calendar"
   - Click **"UPDATE"** at the bottom
   - Click **"SAVE AND CONTINUE"**

6. **Test users (Page 3):**
   - Click **"+ ADD USERS"**
   - Enter your email address (the one you'll use to test)
   - Click **"ADD"**
   - Click **"SAVE AND CONTINUE"**

7. **Summary (Page 4):**
   - Review everything
   - Click **"BACK TO DASHBOARD"**

---

### Step 5: Create OAuth Credentials

Now we'll create the credentials.json file that the app needs.

1. **In the left sidebar**, click **"Credentials"**

2. **At the top**, click **"+ CREATE CREDENTIALS"**

3. **Select "OAuth client ID"** from the dropdown

4. **Configure the OAuth client:**
   - **Application type**: Select **"Desktop app"** from dropdown
   - **Name**: `Project Helix Desktop Client` (or any name)

5. **Click "CREATE"**

6. **A popup appears** saying "OAuth client created"
   - You'll see your Client ID and Client Secret
   - Click **"DOWNLOAD JSON"** button

7. **The file downloads** as something like:
   - `client_secret_123456789-abc.apps.googleusercontent.com.json`

---

### Step 6: Rename and Move the File

1. **Find the downloaded file** (probably in your Downloads folder)

2. **Rename it** to exactly: `credentials.json`
   - Right-click → Rename
   - Or click once, press Enter/Return, type new name

3. **Move it** to this exact location:
   ```
   /Users/shubh/Desktop/Project-Helix/Project/calander/credentials.json
   ```

   **How to move it:**
   - **Option 1 (Finder):**
     - Open Finder
     - Go to your Downloads folder
     - Drag `credentials.json` to:
       `Desktop → Project-Helix → Project → calander`

   - **Option 2 (Terminal):**
     ```bash
     mv ~/Downloads/credentials.json /Users/shubh/Desktop/Project-Helix/Project/calander/
     ```

4. **Verify it's in the right place:**
   ```bash
   ls -la /Users/shubh/Desktop/Project-Helix/Project/calander/credentials.json
   ```

   Should show: `-rw-r--r--  ... credentials.json`

---

### Step 7: Restart Your App

1. **If your app is running**, press `Ctrl+C` in the terminal to stop it

2. **Start it again:**
   ```bash
   ./run.sh
   ```

3. **Open in browser:** http://localhost:5001

---

### Step 8: Connect Your Calendar

1. **In the Project Helix app**, look at the **top-right corner**

2. **Click the button:** "🔗 Connect Your Google Calendar"

3. **A browser window/tab will open** asking you to:
   - Choose your Google account
   - Click on the account you want to use

4. **Google will show a warning:**
   - "Google hasn't verified this app"
   - This is NORMAL - it's your own app
   - Click **"Advanced"** (small text at bottom)
   - Click **"Go to Project Helix (unsafe)"**

5. **Grant permissions:**
   - Google will ask: "Project Helix wants to access your Google Account"
   - Review the permissions (it will show Calendar access)
   - Click **"Continue"** or **"Allow"**

6. **You'll be redirected** back to your app
   - The button will change to show: "✅ Connected as your-email@gmail.com"
   - Your calendar will appear in the iframe!

---

## 🎉 Success! What You Can Do Now

### 1. View Your Calendar
- The "Your Calendar" section now shows YOUR actual Google Calendar
- Navigate months with the controls
- See all your personal events

### 2. See Upcoming Events
- The "Upcoming Events" section shows your agenda
- See what's coming up today and this week

### 3. Add Events to Your Calendar
- Click "+ Add Event" button
- Fill in event details
- Events are added to your Google Calendar automatically

### 4. Add Campus Events to Your Calendar
- Browse events in "Browse Events Near UIUC"
- Click an event to see details
- (Feature to add to calendar - if implemented)

---

## 🔧 Troubleshooting

### "OAuth client not found" error

**Solution:**
- Make sure `credentials.json` is in the right location
- Check the file name is exactly `credentials.json`
- Verify you enabled the Google Calendar API

**Check:**
```bash
cat /Users/shubh/Desktop/Project-Helix/Project/calander/credentials.json
```

Should show JSON content starting with: `{"installed":` or `{"web":`

---

### "This app isn't verified" warning

This is **NORMAL**! It's your own app running locally.

**To proceed:**
1. Click "Advanced" at the bottom
2. Click "Go to Project Helix (unsafe)"
3. This is safe because it's YOUR app on YOUR computer

---

### Calendar not showing after connecting

**Try:**
1. Refresh the browser page
2. Click the "🔄 Refresh" button
3. Check browser console for errors (F12 → Console tab)

---

### Need to reconnect or use different account

**Option 1: Disconnect and reconnect**
1. Click "Disconnect" button (if visible)
2. Click "Connect Your Google Calendar" again
3. Choose different account

**Option 2: Clear token**
```bash
rm /Users/shubh/Desktop/Project-Helix/Project/calander/token.json
```
Then restart app and connect again

---

### Permission denied errors

**Solution:**
- Go back to Google Cloud Console
- OAuth consent screen → Edit App
- Make sure you added yourself as a test user
- Make sure the Calendar scope is selected

---

## 📁 Files Created

After connecting, you'll see a new file:
```
Project/calander/token.json
```

**What it does:**
- Stores your authentication token
- Lets you stay logged in
- Don't commit this to Git (already in .gitignore)

**If you want to disconnect:**
```bash
rm Project/calander/token.json
```

---

## 🔐 Security Notes

### Your credentials.json file:
- ✅ Contains OAuth client ID and secret
- ✅ Only works with YOUR Google Cloud project
- ✅ Only you can see your calendar data
- ⚠️ Don't share this file publicly
- ✅ Already protected by .gitignore

### Your token.json file:
- ✅ Contains your personal access token
- ✅ Specific to your Google account
- ⚠️ Never share this file
- ✅ Can be deleted to disconnect

---

## 📊 What Data is Shared?

**The app can:**
- ✅ Read your calendar events
- ✅ Create new events
- ✅ Modify events it created
- ✅ Delete events it created

**The app CANNOT:**
- ❌ Access your Gmail
- ❌ Access other Google services
- ❌ Share your data with anyone else
- ❌ Work when you're not running it locally

**All data stays on your computer!**

---

## 🎓 Testing It Works

### Test 1: View Your Calendar
1. Connect your calendar
2. You should see your existing events in the calendar view
3. Try navigating to different months

### Test 2: Add an Event
1. Click "+ Add Event"
2. Fill in: Title, Date/Time, Location
3. Click "Save to Google Calendar"
4. Check your actual Google Calendar - it should be there!

### Test 3: See Upcoming Events
1. Look at "Upcoming Events" section
2. Should show events coming up soon
3. Should match what's in your Google Calendar

---

## ❓ FAQ

### Q: Do I need to pay for Google Cloud?
**A:** No! The Calendar API is free for personal use.

### Q: Can my friends use my app?
**A:** Not easily. They'd need to be added as test users in your OAuth consent screen, or you'd need to publish the app (complex).

### Q: Will this work after I close my laptop?
**A:** The connection stays active. Next time you run the app, you'll still be connected (token.json remembers).

### Q: Can I use a different Google account?
**A:** Yes! Delete `token.json` and reconnect with a different account.

### Q: Do I need to redo this setup?
**A:** No! Once credentials.json is in place, you're set. You only connect your calendar once.

---

## 📞 Need Help?

### Quick Checks:
```bash
# Check credentials.json exists
ls -la /Users/shubh/Desktop/Project-Helix/Project/calander/credentials.json

# Check credentials.json content
cat /Users/shubh/Desktop/Project-Helix/Project/calander/credentials.json | head -5

# Test the app
python3 test_app.py
```

### Still stuck?
1. Read the error message carefully
2. Check Google Cloud Console:
   - Is the API enabled?
   - Is OAuth consent screen configured?
   - Are you a test user?
3. Try deleting token.json and reconnecting

---

## 🎉 You're Done!

Once you see "✅ Connected as your-email@gmail.com" in the app, you're all set!

Enjoy having your personal calendar integrated with campus events! 📅

---

**Summary:**
1. ✅ Create Google Cloud project
2. ✅ Enable Calendar API
3. ✅ Configure OAuth consent screen
4. ✅ Download credentials.json
5. ✅ Move to Project/calander/
6. ✅ Restart app
7. ✅ Click "Connect Your Google Calendar"
8. ✅ Done!

**Time needed:** 5-10 minutes
**Cost:** FREE
**Difficulty:** Easy (just follow the steps)
