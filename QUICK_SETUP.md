# Quick Setup Guide for New Features

## 🚀 5-Minute Setup

Follow these steps to enable all new features in Project Helix.

---

## Step 1: Environment Variables

1. **Navigate to Project directory**:
   ```bash
   cd Project
   ```

2. **Copy the example environment file**:
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` file** with your credentials:
   ```bash
   nano .env  # or use any text editor
   ```

4. **Add your Google API credentials**:
   ```env
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_API_KEY=your-api-key
   GOOGLE_CLIENT_SECRET=your-client-secret
   FLASK_SECRET_KEY=generate-a-random-string-here
   ```

---

## Step 2: Generate Flask Secret Key

Run this Python command to generate a secure secret key:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and paste it as `FLASK_SECRET_KEY` in your `.env` file.

---

## Step 3: Get Google API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the **Google Calendar API**:
   - Navigation Menu → APIs & Services → Library
   - Search for "Google Calendar API"
   - Click "Enable"

4. Create OAuth 2.0 Credentials:
   - Navigation Menu → APIs & Services → Credentials
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: "Web application"
   - Name: "Project Helix"
   - Authorized JavaScript origins:
     - `http://localhost:5001`
     - Add your production URL if deploying
   - Authorized redirect URIs:
     - `http://localhost:5001`
     - Add your production URL if deploying
   - Click "Create"

5. Copy credentials to `.env`:
   - **Client ID**: Copy to `GOOGLE_CLIENT_ID`
   - **Client Secret**: Copy to `GOOGLE_CLIENT_SECRET`

6. Create API Key:
   - Click "Create Credentials" → "API key"
   - Copy the generated key to `GOOGLE_API_KEY` in `.env`
   - (Optional) Restrict the key to Google Calendar API only for security

---

## Step 4: Start the Application

```bash
cd Project
python3 app.py
```

The app will start on `http://localhost:5001`

---

## Step 5: Test the New Features

### Test Export Functionality:
1. Open `http://localhost:5001` in your browser
2. Scroll to "Browse Events Near UIUC"
3. Click **📅 iCal** or **📊 CSV** button
4. Check your Downloads folder for the exported file

### Test Dark Mode:
1. Click the **🌙** button in the Browse Events header
2. Page should switch to dark theme
3. Click **☀️** to switch back to light mode

### Test Pagination:
1. Scroll to the Browse Events section
2. Only 30 events should load initially
3. Scroll down to see "Load More (X remaining)" button
4. Click to load next batch

### Test Google Calendar:
1. Click "🔗 Connect Your Google Calendar" in header
2. Complete OAuth flow
3. Try adding an event from Browse Events
4. Event should appear in your Google Calendar

---

## Step 6: Verify Setup

Check the browser console (F12) for these messages:

✅ **Good messages:**
```
✅ Google Calendar credentials loaded from backend
✅ Google API initialized
✅ Google Identity Services initialized
```

❌ **Error messages to fix:**
```
❌ Failed to load Google Calendar config
⚠️ Google Calendar integration is not configured
```

If you see errors, double-check your `.env` file and restart the Flask app.

---

## 🎉 You're Done!

All new features are now active:
- ✅ Event export to iCal and CSV
- ✅ Pagination with Load More
- ✅ Dark mode toggle
- ✅ Enhanced toast notifications
- ✅ Secure Google API credentials

---

## Optional: Email Parsing Setup

If you want email-to-event parsing:

1. **Set up Azure AD App Registration**:
   - Go to [Azure Portal](https://portal.azure.com/)
   - Create App Registration
   - Get Tenant ID and Client ID

2. **Add to `.env`**:
   ```env
   TENANT_ID=your-azure-tenant-id
   CLIENT_ID=your-azure-client-id
   CHAT_KEY=your-openrouter-api-key
   ```

3. **Restart Flask app**

---

## Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt
```

### Port 5001 already in use
```bash
# Find and kill the process using port 5001
lsof -ti:5001 | xargs kill -9
```

Or change the port in `app.py`:
```python
app.run(debug=True, port=5002)  # Use a different port
```

### Google OAuth not working
- Verify redirect URIs in Google Console match your app URL exactly
- Make sure you're using `http://` (not `https://`) for localhost
- Try in incognito mode to rule out cached credentials

### Dark mode not saving
- Check if browser allows localStorage
- Try a different browser
- Check browser console for errors

---

## Need Help?

Check these resources:
- Full documentation: `FEATURE_UPDATE.md`
- Project README: `README.md`
- Google Calendar API Docs: https://developers.google.com/calendar
- Flask Documentation: https://flask.palletsprojects.com/

---

**Estimated Setup Time**: 5-10 minutes

**Last Updated**: 2025-12-17
