# Project Helix @ UIUC

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.1.2-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> A comprehensive campus event aggregation platform for UIUC students

NOTE: This project was orignally part of cs196 (cs124 hons) and I worked on it as part of group 7. I just customised this for my own usecase. All credits go to them.

## 🎯 What is Project Helix?

Project Helix is a Flask-based web application that:
- 📅 **Aggregates 1000+ campus events** from 15+ UIUC sources
- 📧 **Parses emails** using AI to find event information
- 🗓️ **Syncs with Google Calendar** for personal event management
- 🔍 **Smart search & filtering** to find events that matter to you
- 🤖 **Automated scraping** via Modal for fresh event data

## ✨ Features

### 🌐 Browse Events
- 1000+ events from UIUC calendars, State Farm Center, Athletics
- Real-time search across titles, descriptions, and locations
- Category filtering (Sports, Entertainment, Academic, etc.)
- Detailed event pages with venue and timing information

### 📧 Email-to-Event Parsing
- Scan your Outlook emails for event invitations
- AI-powered extraction of event details
- Automatically add to Google Calendar
- Process up to 25 emails at once

### 🗓️ Calendar Integration
- Full Google Calendar sync
- View your personal events alongside campus events
- Add events directly to your calendar
- Month and agenda views

### 🤖 Automated Scraping
- Web scrapers for 15+ event sources
- Modal-based serverless execution
- Firebase Realtime Database storage
- Weekly automated updates

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd Project
pip3 install -r requirements.txt
playwright install chromium
```

### 2. Run the App
```bash
./run.sh
```
Open http://localhost:5000

**That's it!** The browse events feature works immediately without any setup.

## 📚 Documentation

### Start Here:
- 🚀 **[QUICKSTART.md](QUICKSTART.md)** - Get running in 5 minutes
- 🔑 **[CREDENTIALS_SUMMARY.md](CREDENTIALS_SUMMARY.md)** - Quick credential overview
- 🔐 **[CREDENTIALS_GUIDE.md](CREDENTIALS_GUIDE.md)** - Detailed credential setup

### Reference:
- 📖 **[SETUP.md](SETUP.md)** - Comprehensive setup guide
- 🏗️ **[CLAUDE.md](CLAUDE.md)** - Architecture & development docs
- 📄 **[.env.example](.env.example)** - Environment variables template

## 🔑 Required Credentials (Optional Features)

Project Helix works out of the box for browsing events, but requires credentials for advanced features:

| Feature | Required Credentials | Cost | Guide |
|---------|---------------------|------|-------|
| 📧 Email Import | Azure AD + OpenRouter | ~$0.01/email | [Guide](CREDENTIALS_GUIDE.md#1-azure-ad-credentials-for-outlook-email-import) |
| 🗓️ Calendar Sync | Google Cloud | FREE | [Guide](CREDENTIALS_GUIDE.md#3-google-calendar-credentials-optional-but-recommended) |

### Quick Setup:
1. **Azure AD** (for email import):
   - Get from: https://portal.azure.com/
   - Add to `Project/.env`: `CLIENT_ID`, `TENANT_ID`, `CLIENT_SECRET`

2. **OpenRouter** (for AI parsing):
   - Get from: https://openrouter.ai/
   - Add to `Project/.env`: `CHAT_KEY`

3. **Google Calendar** (optional):
   - Get from: https://console.cloud.google.com/
   - Save as: `Project/calander/credentials.json`

See [CREDENTIALS_GUIDE.md](CREDENTIALS_GUIDE.md) for detailed instructions.

## 📁 Project Structure

```
Project-Helix/
├── README.md                    # This file
├── QUICKSTART.md                # 5-minute setup guide
├── CREDENTIALS_GUIDE.md         # Detailed credential instructions
├── CREDENTIALS_SUMMARY.md       # Quick credential reference
├── SETUP.md                     # Comprehensive setup guide
├── CLAUDE.md                    # Architecture documentation
├── run.sh                       # Quick start script
├── .vscode/
│   └── launch.json              # VS Code debug configuration
└── Project/
    ├── app.py                   # Flask application
    ├── scrape.py                # Event scrapers + Modal
    ├── .env                     # Your credentials (create this)
    ├── requirements.txt         # Python dependencies
    ├── templates/
    │   └── index.html           # Main UI
    ├── static/
    │   ├── script.js            # Event handling
    │   ├── browse-events.js     # Browse functionality
    │   ├── calendar-connect.js  # Google Calendar integration
    │   └── style.css            # Styling
    └── calander/
        ├── readEmail.py         # Email parsing logic
        ├── credentials.json     # Google OAuth (create this)
        └── prompt.txt           # AI prompt template
```

## 🛠️ Technology Stack

### Backend
- **Flask** - Web framework
- **BeautifulSoup4** - HTML parsing
- **Playwright** - Dynamic web scraping
- **MSAL** - Microsoft authentication
- **OpenAI** - Email parsing AI

### Frontend
- **Vanilla JavaScript** - No frameworks (simple for intro CS)
- **Google Calendar API** - Calendar integration
- **Firebase SDK** - Real-time data

### Infrastructure
- **Modal** - Serverless scraper execution
- **Firebase Realtime Database** - Event storage
- **Google Cloud** - OAuth & Calendar API

## 🔍 Event Sources

Project Helix scrapes from:
- 10 calendars.illinois.edu sources (general campus events)
- State Farm Center (concerts, shows)
- 4 Fighting Illini athletics schedules
- **Total: 15+ sources, 1000+ events**

## 🌐 Live Demo

**🚀 View it live:** [https://infoshubhjain.github.io/Project-Helix/](https://infoshubhjain.github.io/Project-Helix/)

The app is deployed on GitHub Pages with:
- ✅ Persistent Google Calendar authentication
- ✅ Automatic token refresh (session lasts indefinitely)
- ✅ Browse 1000+ campus events
- ✅ Full calendar integration

## 🎓 Development

### Running Locally
```bash
cd Project
python3 app.py
```

### Running Scrapers
```bash
# Local test (no database upload)
python3 scrape.py

# Production with Modal (uploads to Firebase)
modal run scrape.py
```

### Deploying to GitHub Pages
See [DEPLOY_TO_GITHUB_PAGES.md](DEPLOY_TO_GITHUB_PAGES.md) for complete deployment instructions.

Quick deploy:
```bash
git add .
git commit -m "Deploy updates"
git push origin main
```

### VS Code Debugging
1. Open project in VS Code
2. Press `F5`
3. Select "Flask: Run Project Helix App"

## 🐛 Troubleshooting

### App won't start?
- Check port 5000 is free: `lsof -i :5000`
- Verify dependencies: `pip3 install -r requirements.txt`

### Credentials not working?
- See [CREDENTIALS_GUIDE.md](CREDENTIALS_GUIDE.md)
- Check `.env` file location: `Project/.env`
- Restart app after editing `.env`

### More help:
- Check [SETUP.md](SETUP.md) troubleshooting section
- Review terminal error messages
- Verify all dependencies installed

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     EVENT SOURCES                            │
│  calendars.illinois.edu • State Farm Center • Athletics     │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ↓
┌──────────────────────────────────────────────────────────────┐
│              SCRAPERS (scrape.py via Modal)                  │
│   BeautifulSoup (static) • Playwright (dynamic)             │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ↓
┌──────────────────────────────────────────────────────────────┐
│            FIREBASE REALTIME DATABASE                        │
│              Stores 1000+ scraped events                     │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ↓
┌──────────────────────────────────────────────────────────────┐
│               FLASK BACKEND (app.py)                         │
│   API Endpoints • Email Processing • Serving Frontend       │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ↓
┌──────────────────────────────────────────────────────────────┐
│              FRONTEND (HTML/CSS/JS)                          │
│  Browse Events • Calendar Sync • Email Import • Search      │
└──────────────────────────────────────────────────────────────┘
```

## 🤝 Contributing

This is an academic project for UIUC students. Contributions welcome!

## 📄 License

Copyright © 2025 Project Helix

## 👥 Team

Calendar Crew - Group 7

## 🔗 Links

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Google Calendar API](https://developers.google.com/calendar)
- [Microsoft Graph API](https://docs.microsoft.com/en-us/graph/)
- [Firebase](https://firebase.google.com/)
- [Modal](https://modal.com/)

---

**🎉 Ready to explore campus events? Run `./run.sh` and visit http://localhost:5000**

For detailed setup: See [QUICKSTART.md](QUICKSTART.md) | For credentials: See [CREDENTIALS_GUIDE.md](CREDENTIALS_GUIDE.md)
