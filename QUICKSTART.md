# EventFlow - Quick Start Guide

## Prerequisites Check
- [ ] Python 3.8+ installed (`python3 --version`)
- [ ] pip installed (`pip3 --version`)
- [ ] VS Code (optional but recommended)

## 5-Minute Setup

### 1. Install Dependencies (2 minutes)
```bash
cd /Users/shubh/Desktop/Project-Helix/Project
pip3 install -r requirements.txt
playwright install chromium
```

### 2. Configure Environment (1 minute)
Edit `Project/.env` and add your credentials:
```env
CLIENT_ID=your_azure_client_id_here
TENANT_ID=your_azure_tenant_id_here
CLIENT_SECRET=your_azure_client_secret_here
CHAT_KEY=your_openrouter_api_key_here
```

### 3. Run the Application (30 seconds)
```bash
./run.sh
```
Or:
```bash
cd Project
python3 app.py
```

### 4. Open in Browser
Navigate to: **http://localhost:5000**

## First Time Setup

### Getting Required Credentials

#### Azure AD (for Email Import)
1. Go to https://portal.azure.com/
2. Register a new app
3. Add API permission: Microsoft Graph → `Mail.Read`
4. Copy Client ID, Tenant ID, and create a Client Secret

#### OpenRouter (for AI Email Parsing)
1. Go to https://openrouter.ai/
2. Sign up and generate an API key
3. Use this for `CHAT_KEY` in .env

#### Google Calendar (Optional)
1. Go to https://console.cloud.google.com/
2. Enable Google Calendar API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download as `credentials.json` → place in `Project/calander/`

## VS Code Setup

1. Open folder in VS Code:
   ```bash
   code /Users/shubh/Desktop/Project-Helix
   ```

2. Press `F5` or click "Run and Debug"

3. Select **"Flask: Run EventFlow App"**

4. The app will start with debugging enabled

## Testing the Application

### Test 1: Browse Events
1. Open http://localhost:5000
2. Scroll to "Browse Events Near UIUC"
3. You should see scraped events from Firebase

### Test 2: Google Calendar Integration
1. Click "Connect Your Google Calendar"
2. Sign in with Google
3. Your calendar should appear

### Test 3: Email Import (Requires Setup)
1. Click "Add from Email"
2. Enter number of emails (1-25)
3. Click "Process Emails"
4. Events should be parsed and displayed

## Common Issues

### Port 5000 already in use
```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>
```

### Module not found errors
```bash
cd Project
pip3 install -r requirements.txt
```

### Playwright errors
```bash
playwright install --with-deps chromium
```

## What's Next?

- Read [SETUP.md](SETUP.md) for detailed configuration
- Read [CLAUDE.md](CLAUDE.md) for architecture details
- Customize the frontend in `Project/static/` and `Project/templates/`
- Add more event sources in `Project/scrape.py`

## Key Features

✓ **Browse 1000+ Events** - Scraped from UIUC sources
✓ **Google Calendar Sync** - View and add events
✓ **Email Import** - AI-powered event extraction from Outlook
✓ **Search & Filter** - Find events by keyword or category
✓ **Interactive Calendar** - Month and agenda views

## Project Structure

```
Project-Helix/
├── run.sh              # Quick run script
├── SETUP.md            # Detailed setup guide
├── QUICKSTART.md       # This file
├── Project/
│   ├── app.py          # Main Flask application
│   ├── .env            # Your credentials (DO NOT COMMIT)
│   └── static/         # Frontend files
```

## Support

Need help? Check:
1. [SETUP.md](SETUP.md) - Detailed setup guide
2. [CLAUDE.md](CLAUDE.md) - Project documentation
3. Terminal error messages
4. Git commit history for recent changes

---

**Ready to run?** Just execute: `./run.sh`
