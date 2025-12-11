# Fix: "Error loading calendar. Please try again"

## 🔍 What's Happening:
You successfully connected to Google, but the app can't load your calendar data because the **Google Calendar API** might not be enabled, or you need a valid API key.

## ✅ Solution 1: Enable Google Calendar API (Most Likely Fix)

### Step 1: Go to API Library
Open: **https://console.cloud.google.com/apis/library**

Make sure **"plated-life-480911-g4"** is selected at the top.

### Step 2: Search for Google Calendar API
1. In the search box, type: **`Google Calendar API`**
2. Click on **"Google Calendar API"** (has a blue calendar icon)

### Step 3: Enable the API
1. Click the **"ENABLE"** button (big blue button)
2. Wait a few seconds for it to enable

### Step 4: Verify It's Enabled
You should see:
- ✅ A green checkmark
- "API enabled" message
- **"MANAGE"** button (instead of "ENABLE")

---

## ✅ Solution 2: Create API Key (If Solution 1 Doesn't Work)

The app currently uses a placeholder API key. Let's create a real one:

### Step 1: Go to Credentials
Open: **https://console.cloud.google.com/apis/credentials**

### Step 2: Create API Key
1. Click **"+ CREATE CREDENTIALS"** at the top
2. Select **"API key"**
3. A popup shows your new API key - **copy it!**

### Step 3: Restrict the API Key (Optional but Recommended)
1. Click **"RESTRICT KEY"** in the popup
2. Under **"Application restrictions"**:
   - Select **"HTTP referrers (web sites)"**
   - Click **"+ ADD AN ITEM"**
   - Add: `http://localhost:5001`
   - Add: `http://127.0.0.1:5001`
3. Under **"API restrictions"**:
   - Select **"Restrict key"**
   - Check ✅ **"Google Calendar API"**
4. Click **"SAVE"**

### Step 4: Update Your App
After creating the API key, tell me what it is and I'll update the app with it.

Or you can update it yourself in:
**File:** `Project/templates/index.html` (line 185)

Change:
```javascript
const GOOGLE_API_KEY = 'AIzaSyA7uXknS3AhXWG5IpcfdnI2eNo6-6hcmMA';
```

To:
```javascript
const GOOGLE_API_KEY = 'YOUR_NEW_API_KEY_HERE';
```

---

## 🎯 Quick Fix Steps (Try This First):

1. **Enable Google Calendar API**:
   ```bash
   open https://console.cloud.google.com/apis/library/calendar-json.googleapis.com
   ```
   Click **"ENABLE"**

2. **Restart your app**:
   ```bash
   ./run.sh
   ```

3. **Try connecting again**:
   - Go to http://localhost:5001
   - Refresh page (Cmd+R)
   - Click "Connect Your Google Calendar"
   - Sign in again

---

## 🔍 Check If API Is Already Enabled:

```bash
# Open APIs & Services dashboard
open https://console.cloud.google.com/apis/dashboard
```

Look for **"Google Calendar API"** in the list of enabled APIs.

---

## 📋 Checklist:

- [ ] Opened Google Cloud Console
- [ ] Went to API Library
- [ ] Searched for "Google Calendar API"
- [ ] Clicked on Google Calendar API
- [ ] Clicked "ENABLE" button
- [ ] Saw "API enabled" confirmation
- [ ] Went back to app at http://localhost:5001
- [ ] Refreshed the page
- [ ] Clicked "Connect Your Google Calendar"
- [ ] Successfully loaded calendar!

---

## 🆘 Still Getting Errors?

### Check Browser Console for Detailed Error:
1. Open your app: http://localhost:5001
2. Right-click → **"Inspect"** (or press F12)
3. Click **"Console"** tab
4. Try connecting again
5. Look for red error messages

Common errors and fixes:

| Error Message | Fix |
|---------------|-----|
| `The API key doesn't exist` | Create a new API key (Solution 2 above) |
| `API key not valid` | Restrict API key to Google Calendar API |
| `accessNotConfigured` | Enable Google Calendar API (Solution 1 above) |
| `Request had insufficient authentication scopes` | Check OAuth scopes include calendar access |

---

## 🎓 Why Both OAuth Credentials AND API Key?

- **OAuth Credentials (credentials.json)**: Allows your app to act on behalf of the user (read/write their calendar)
- **API Key**: Identifies your app to Google's servers (proves your app is allowed to use the API)

Both are needed for Google Calendar integration to work!

---

**Try Solution 1 first (Enable Google Calendar API) - it's the most common fix!**

Let me know if you still see errors after enabling the API!
