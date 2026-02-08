# Project Helix @ UIUC

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.x-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> A campus event aggregation platform for UIUC: browse 1000+ events, sync with Google Calendar, and import events from email.

**Note:** This project originated from CS 196 (CS 124 Honors) Group 7. It has been customized for personal use. Full credit to the original team.

---

## Features

- **Browse events** — 1000+ events from UIUC calendars, State Farm Center, and Fighting Illini athletics; search, filter, and view details.
- **Google Calendar** — Connect your calendar, view personal events alongside campus events, add events with one click.
- **Email-to-event parsing** — Scan Outlook emails with AI-powered extraction and add events to Google Calendar (optional; requires Azure AD + OpenRouter).
- **Automated scraping** — Playwright/BeautifulSoup scrapers; optional Modal + Firebase pipeline for weekly updates.

---

## Tech stack

| Layer | Technologies |
|-------|--------------|
| Backend | Flask, Flask-CORS, python-dotenv |
| Scraping | BeautifulSoup4, lxml, Playwright, requests |
| Auth & APIs | MSAL (Microsoft), google-auth, Google Calendar API, OpenAI/OpenRouter |
| Frontend | Vanilla JS, CSS; Google Calendar API, Firebase SDK (optional) |
| Infra | Modal (optional), Firebase Realtime Database (optional) |

---

## Getting started

### Prerequisites

- Python 3.8+
- pip

### Install and run

```bash
# Clone the repository
git clone https://github.com/infoshubhjain/Project-Helix.git
cd Project-Helix

# Install dependencies
cd Project
pip install -r requirements.txt
playwright install chromium

# Run the app (from repo root)
./run.sh
```

Then open **http://localhost:5001**. Browsing events works without any credentials.

### Using a virtual environment (recommended)

```bash
cd Project
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
cd ..
./run.sh
```

---

## Usage

### Local development

```bash
./run.sh
# or
cd Project && python3 app.py
```

### Run scrapers

```bash
# Local (no database upload)
cd Project && python3 scrape.py

# Production with Modal (uploads to Firebase)
cd Project && modal run scrape.py
```

### Validate app (smoke test)

```bash
python3 test_app.py
# or, if you add the Makefile: make test
```

---

## Credentials (optional)

| Feature | Credentials | Guide |
|---------|-------------|--------|
| Email import | Azure AD + OpenRouter | [CREDENTIALS_GUIDE.md](CREDENTIALS_GUIDE.md) |
| Google Calendar | Google Cloud OAuth | [CREDENTIALS_GUIDE.md](CREDENTIALS_GUIDE.md) |

- Copy `Project/.env.example` to `Project/.env` and fill in values.
- For Google Calendar, place `credentials.json` in `Project/calander/` (see CREDENTIALS_GUIDE.md).

---

## Project structure

```
Project-Helix/
├── README.md
├── run.sh
├── index.html                 # GitHub Pages entry
├── Project/
│   ├── app.py                 # Flask app
│   ├── scrape.py              # Scrapers (+ Modal)
│   ├── requirements.txt
│   ├── templates/
│   │   └── index.html
│   ├── static/                # JS, CSS, images
│   ├── calander/              # Google Calendar + email parsing
│   └── email_parser/
├── docs/                      # Additional documentation
└── .env.example / Project/.env.example
```

---

## Live demo

**https://infoshubhjain.github.io/Project-Helix/**

GitHub Pages serves the static `index.html` with Google Calendar integration and persistent auth.

---

## Documentation

- [QUICKSTART.md](QUICKSTART.md) — Short setup
- [CREDENTIALS_GUIDE.md](CREDENTIALS_GUIDE.md) — Azure, OpenRouter, Google
- [SETUP.md](SETUP.md) — Full setup and troubleshooting
- [DEPLOY_TO_GITHUB_PAGES.md](DEPLOY_TO_GITHUB_PAGES.md) — Deploy to GitHub Pages
- [CLAUDE.md](CLAUDE.md) — Architecture and dev notes

---

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines and code style.

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE).

---

## Links

- [Flask](https://flask.palletsprojects.com/) · [Google Calendar API](https://developers.google.com/calendar) · [Microsoft Graph](https://docs.microsoft.com/en-us/graph/) · [Modal](https://modal.com/) · [Firebase](https://firebase.google.com/)
