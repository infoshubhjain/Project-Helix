# Project Helix - EventFlow Setup Guide

## Overview
Project Helix (EventFlow) is a Flask-based campus event aggregation web application that scrapes events from 15+ university sources and displays them in an interactive calendar interface with email parsing capabilities.

## Prerequisites

- Python 3.8+ (tested with Python 3.13.7)
- pip (Python package manager)
- VS Code (recommended IDE)
- Git
- Microsoft Azure AD credentials (for Outlook email integration)
- OpenRouter API key (for AI-powered email parsing)
- Google Cloud credentials (for Google Calendar integration)
- Firebase Realtime Database (for event storage)

## Quick Start

### 1. Clone the Repository
```bash
cd /Users/shubh/Desktop/Project-Helix
```

### 2. Install Python Dependencies
```bash
cd Project
pip install -r requirements.txt
```

### 3. Install Playwright Browsers
```bash
playwright install chromium
```

### 4. Configure Environment Variables

Edit the `.env` file in the `Project/` directory with your credentials:

```env
# Microsoft Azure AD Credentials (for Outlook email integration)
CLIENT_ID=your_azure_client_id
TENANT_ID=your_azure_tenant_id
CLIENT_SECRET=your_azure_client_secret

# OpenAI/OpenRouter API Key (for email parsing)
CHAT_KEY=your_openrouter_api_key
```

**How to Get Credentials:**

- **Azure AD**: https://portal.azure.com/
  1. Register a new application
  2. Add Microsoft Graph API permissions: `Mail.Read`
  3. Get Client ID, Tenant ID, and Client Secret

- **OpenRouter API**: https://openrouter.ai/
  1. Sign up for an account
  2. Generate an API key
  3. Use it for `CHAT_KEY`

### 5. Configure Google Calendar Integration

For Google Calendar features, you need `credentials.json`:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or use existing
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download as `credentials.json` and place in `Project/calander/` directory

The `GOOGLE_CLIENT_ID` and `GOOGLE_API_KEY` are already configured in `templates/index.html` (lines 183-184).

### 6. Firebase Configuration

The Firebase configuration is already set up in `static/browse-events.js`. The app connects to:
- Database: `eventflowdatabase-default-rtdb.firebaseio.com`

If you need to change Firebase settings, edit `browse-events.js` (lines 12-21).

## Running the Application

### Option 1: VS Code Launch Configuration (Recommended)
1. Open the project in VS Code
2. Press `F5` or go to Run and Debug
3. Select **"Flask: Run EventFlow App"**
4. Access the app at `http://localhost:5000`

### Option 2: Command Line
```bash
cd Project
python app.py
```

Access the app at `http://localhost:5000`

## Running the Scrapers

### Local Testing (No Database Upload)
```bash
cd Project
python scrape.py
```

### Production with Modal (Uploads to Firebase)
```bash
cd Project
modal run scrape.py
```

**Note:** Modal requires:
- Modal CLI installed: `pip install modal`
- Modal account and authentication: `modal setup`
- Modal secrets named `firebase-creds` with Firebase credentials

## Application Features

### 1. **Your Calendar** (Google Calendar Integration)
- Sync your Google Calendar
- View events in calendar format
- Add events to your calendar

### 2. **Upcoming Events** (Agenda View)
- See upcoming events from your calendar
- Today's agenda view

### 3. **Browse Events** (Scraped Events)
- Browse 1000+ events from UIUC sources
- Search by title, description, location
- Filter by category
- View detailed event information

### 4. **Email Import**
- Scan Outlook emails for events
- AI-powered event parsing
- Automatically add to Google Calendar
- Process 1-25 emails at a time

## Project Structure

```
Project-Helix/
├── .vscode/
│   └── launch.json           # VS Code debug configuration
├── Project/
│   ├── .env                  # Environment variables (DO NOT COMMIT)
│   ├── app.py                # Flask web server
│   ├── scrape.py             # Web scraping logic
│   ├── requirements.txt      # Python dependencies
│   ├── templates/
│   │   └── index.html        # Main HTML template
│   ├── static/
│   │   ├── script.js         # Calendar and event handling
│   │   ├── browse-events.js  # Browse events functionality
│   │   ├── calendar-connect.js # Google Calendar connection
│   │   ├── style.css         # Styling
│   │   └── images/           # Logo and favicon
│   ├── calander/
│   │   ├── readEmail.py      # Email parsing logic
│   │   ├── add_scraped_events.py # Google Calendar sync
│   │   ├── prompt.txt        # AI prompt for email parsing
│   │   └── requirements.txt  # Calendar dependencies
│   └── email_parser/         # Alternative email parser
└── CLAUDE.md                 # Project documentation
```

## Troubleshooting

### Issue: Flask app won't start
**Solution:**
1. Check if port 5000 is available: `lsof -i :5000`
2. Make sure all dependencies are installed: `pip install -r requirements.txt`
3. Verify `.env` file exists with valid credentials

### Issue: Playwright errors
**Solution:**
```bash
playwright install --with-deps chromium
```

### Issue: Firebase connection errors
**Solution:**
1. Check your internet connection
2. Verify Firebase configuration in `browse-events.js`
3. Check Firebase Realtime Database rules

### Issue: Google Calendar not connecting
**Solution:**
1. Verify `credentials.json` exists in `Project/calander/`
2. Check Google Cloud Console API is enabled
3. Delete `token.json` and re-authenticate

### Issue: Email parsing not working
**Solution:**
1. Check `.env` has valid `CLIENT_ID`, `TENANT_ID`, `CHAT_KEY`
2. Verify Azure AD permissions include `Mail.Read`
3. Try re-authenticating when prompted

## Development Notes

### Running Tests
Currently, the app doesn't have automated tests. To verify functionality:
1. Start the Flask app
2. Open `http://localhost:5000`
3. Test each feature manually

### Making Changes
- Frontend: Edit files in `static/` and `templates/`
- Backend: Edit `app.py` for routes and API endpoints
- Scrapers: Edit `scrape.py` for scraping logic
- Email parsing: Edit `calander/readEmail.py`

### Git Workflow
```bash
git add .
git commit -m "Your commit message"
git push
```

**Files to NOT commit:**
- `.env` (contains secrets)
- `token.json` (Google OAuth token)
- `credentials.json` (Google OAuth credentials)
- `__pycache__/` (Python cache)

## API Endpoints

### GET /
Returns the main HTML page

### POST /api/process_emails
Process emails and return parsed events
- Request body: `{"amount": 5}` (1-25)
- Response: List of parsed events

### GET /api/process_emails_stream
Stream events as they are parsed (Server-Sent Events)
- Query param: `amount=5` (1-25)

## Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Playwright Python](https://playwright.dev/python/)
- [Google Calendar API](https://developers.google.com/calendar)
- [Microsoft Graph API](https://docs.microsoft.com/en-us/graph/)
- [Firebase Realtime Database](https://firebase.google.com/docs/database)

## Support

For issues or questions:
1. Check this setup guide
2. Review [CLAUDE.md](CLAUDE.md) for architecture details
3. Check the error logs in your terminal
4. Search for similar issues on Stack Overflow

## License

Copyright © 2025 EventFlow
