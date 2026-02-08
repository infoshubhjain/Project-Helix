# 🧬 Project Helix @ UIUC

**The Central Intelligence for Campus Life.**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.x-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Project Helix is a campus event aggregation platform for the University of Illinois Urbana-Champaign. It centralizes **1,100+ events** from diverse sources into a single, actionable interface—eliminating calendar fragmentation.

[**Explore Live Demo**](https://infoshubhjain.github.io/Project-Helix/)

---

## ✨ Key Features

- **🔍 Omni-Source Aggregator** — Real-time scraping of UIUC Campus Calendars, State Farm Center, and Fighting Illini Athletics.
- **🗓️ Bi-Directional Sync** — View your personal Google Calendar events alongside campus happenings; add new events with one click.
- **🤖 AI Email Intelligence** — Automatically parses event details from Outlook emails using AI to bridge inbox and schedule.
- **⚡ Automated Pipeline** — Robust scraping with Playwright and BeautifulSoup; optional cloud-scaling via Modal.

---

## 🚀 Quick Start

### 1. Environment Setup
- Python 3.8+, pip

```bash
git clone https://github.com/infoshubhjain/Project-Helix.git
cd Project-Helix

# (Optional) Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
cd Project
pip install -r requirements.txt
playwright install chromium
```

### 2. Launching the Platform
From the repository root:
```bash
./run.sh
```
**Access the dashboard at:** [http://localhost:5001](http://localhost:5001)

---

## 🔑 Configuration & Credentials

Detailed setup for unlocking advanced features.

### 1. Google Calendar Integration
Required for viewing and adding events to your personal calendar.
- Go to [Google Cloud Console](https://console.cloud.google.com/).
- Enable **Google Calendar API**.
- Create **OAuth 2.0 Credentials** (Desktop App).
- Download as `credentials.json` and place in `Project/calendar/`.

### 2. AI Email Parsing (Outlook)
Required to intelligently extract events from your inbox.
- **Azure AD**: Register an app at [Azure Portal](https://portal.azure.com/). Add `Mail.Read` permissions.
- **OpenRouter**: Sign up at [OpenRouter.ai](https://openrouter.ai/) and generate an API key.
- **Environment**: Rename `.env.example` to `.env` in the `Project/` folder and fill in:
  ```env
  CLIENT_ID=your_azure_client_id
  TENANT_ID=your_azure_tenant_id
  CLIENT_SECRET=your_azure_client_secret
  CHAT_KEY=your_openrouter_api_key
  ```

---

## 📂 Repository Structure

```
Project-Helix/
├── run.sh                  # Application launcher
├── index.html              # GitHub Pages entry
├── Project/
│   ├── app.py              # Flask Backend
│   ├── scrape.py           # Web Scrapers
│   ├── calendar/           # Auth & Email logic
│   ├── static/             # Frontend assets
│   └── templates/          # HTML templates
└── tests/                  # Validation scripts
```

---

## 🛠️ Technical Ecosystem

| Layer | Technologies |
|-------|--------------|
| **Backend** | Flask, Flask-CORS, python-dotenv |
| **Scraping** | BeautifulSoup4, Playwright, Requests |
| **APIs** | MSAL (Microsoft), Google Calendar API, OpenRouter |
| **Frontend** | Vanilla JS, CSS, Firebase SDK (optional) |

---

## 🌐 Deployment (GitHub Pages)

The frontend is deployed to GitHub Pages. It works as a static site with Google Calendar integration using client-side OAuth.

1. **Google Console**: Add `https://infoshubhjain.github.io` to Authorized Origins.
2. **GitHub Settings**: Enable Pages from the `main` branch (root folder).

---

## ✅ Validation & Testing

Run smoke tests for the backend and scrapers:
```bash
# General app check
python3 tests/test_app.py

# Scraper verification
python3 tests/test_scrapers.py
```

---

## 📄 License & Credits
Licensed under the **MIT License**.
Original concept from CS 196 (CS 124 Honors) Group 7.
