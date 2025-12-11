# Fix: Error 400 - redirect_uri_mismatch

## 🔍 What Happened:
You got this error because you created **Desktop app** credentials, but the web app needs **Web application** credentials with the proper redirect URIs configured.

## ✅ Two Options to Fix This:

---

## OPTION 1: Add Authorized Redirect URIs (Easier - 2 minutes)

### Step 1: Go to Google Cloud Console
1. Open: https://console.cloud.google.com/apis/credentials
2. Sign in if needed
3. Make sure your project "plated-life-480911-g4" is selected

### Step 2: Edit Your OAuth Client
1. Find your OAuth 2.0 Client ID in the list
   - Should show: `691968245686-jqj22uc...`
2. Click the **pencil/edit icon** (✏️) on the right

### Step 3: Add Authorized Origins and Redirect URIs
Under **"Authorized JavaScript origins"**, add:
```
http://localhost:5001
http://127.0.0.1:5001
```

Under **"Authorized redirect URIs"**, add:
```
http://localhost:5001
http://127.0.0.1:5001
http://localhost
```

### Step 4: Save
Click **"SAVE"** at the bottom

### Step 5: Test Again
1. Wait 1-2 minutes for changes to propagate
2. Restart your app: `./run.sh`
3. Try connecting again

---

## OPTION 2: Create New Web Application Credentials (Fresh Start - 5 minutes)

If Option 1 doesn't work, create proper Web Application credentials:

### Step 1: Delete Current Credentials (Optional)
1. Go to: https://console.cloud.google.com/apis/credentials
2. Find your OAuth 2.0 Client ID
3. Click the trash icon to delete it

### Step 2: Create New Credentials
1. Click **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**
2. **Application type**: Select **"Web application"** (NOT Desktop app!)
3. **Name**: "EventFlow Web Client"

### Step 3: Configure Web Application
Under **"Authorized JavaScript origins"**, add:
```
http://localhost:5001
http://127.0.0.1:5001
```

Under **"Authorized redirect URIs"**, add:
```
http://localhost:5001
http://127.0.0.1:5001
http://localhost
```

### Step 4: Create and Download
1. Click **"CREATE"**
2. In the popup, click **"DOWNLOAD JSON"**
3. Rename the file to `credentials.json`
4. Move it to replace the old one:
   ```bash
   mv ~/Downloads/client_secret_*.json \
      /Users/shubh/Desktop/Project-Helix/Project/calander/credentials.json
   ```

### Step 5: Update the App
I already updated the HTML file with your current CLIENT_ID. If you create new credentials, we'll need to update it again.

---

## 🔧 I Already Updated Your App

I changed the `index.html` file to use your CLIENT_ID:
```
691968245686-jqj22uc5hbgtb1tabc6fccl6lg1bdjok.apps.googleusercontent.com
```

Now you just need to:
1. Add the redirect URIs in Google Cloud Console (Option 1 above)
2. OR create new Web app credentials (Option 2 above)

---

## 📋 Quick Fix (Try This First):

```bash
# Step 1: Go to Google Cloud Console
open https://console.cloud.google.com/apis/credentials

# Step 2: Edit your OAuth client and add these redirect URIs:
# - http://localhost:5001
# - http://127.0.0.1:5001
# - http://localhost

# Step 3: Wait 1 minute, then restart app
cd /Users/shubh/Desktop/Project-Helix
./run.sh
```

Then try connecting again!

---

## ⚠️ Important Notes:

### Why This Happened:
- You created "Desktop app" credentials
- But the web app needs "Web application" credentials
- Different OAuth flows have different redirect URI requirements

### What are Redirect URIs:
- After you sign in with Google, it redirects you back to your app
- You need to tell Google which URLs are safe to redirect to
- For local development, that's `http://localhost:5001`

### Application Type Matters:
- **Desktop app**: For native apps (Python scripts, etc.)
- **Web application**: For web apps (what we need!)

---

## 🎯 After You Fix This:

1. **Restart the app**: `./run.sh`
2. **Clear browser cache**: Cmd+Shift+R (or Ctrl+Shift+R)
3. **Try connecting again**
4. Should work! ✅

---

## 🆘 Still Getting Errors?

### Check These:
1. ✅ Redirect URIs include `http://localhost:5001`
2. ✅ OAuth consent screen is configured
3. ✅ You're added as a test user
4. ✅ Google Calendar API is enabled
5. ✅ Using "Web application" not "Desktop app"

### Debug Command:
```bash
# Check your credentials.json
cat /Users/shubh/Desktop/Project-Helix/Project/calander/credentials.json | python3 -m json.tool
```

Should show either `"installed":` or `"web":` at the start.

---

**Try Option 1 first (adding redirect URIs) - it's faster!**
