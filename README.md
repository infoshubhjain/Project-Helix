# 🧬 Project Helix @ UIUC

**The Central Intelligence for Campus Life.**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.x-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Project Helix is a campus event aggregation platform for the University of Illinois Urbana-Champaign. It centralizes **1,000+ events** from diverse sources into a single, actionable interface—eliminating calendar fragmentation.

[**Explore Live Demo**](https://infoshubhjain.github.io/Project-Helix/) · [**Quickstart Guide**](QUICKSTART.md) · [**View Architecture**](CLAUDE.md)

**Note:** This project originated from CS 196 (CS 124 Honors) Group 7. It has been customized for personal use. Full credit to the original team.

---

## ✨ Key Features

- **🔍 Omni-Source Aggregator** — Real-time scraping of UIUC Campus Calendars, State Farm Center, and Fighting Illini Athletics.
- **🗓️ Bi-Directional Sync** — View your personal Google Calendar events alongside campus happenings; add new events with one click.
- **🤖 AI Email Intelligence (Beta)** — Automatically parses event details from Outlook emails using OpenAI/OpenRouter to bridge inbox and schedule.
- **⚡ Automated Pipeline** — Robust scraping with Playwright and BeautifulSoup; optional cloud-scaling via Modal.

---

## 🛠️ Technical Ecosystem

| Layer | Technologies |
|-------|--------------|
| Backend | Flask, Flask-CORS, python-dotenv |
| Scraping | BeautifulSoup4, lxml, Playwright, requests |
| Auth & APIs | MSAL (Microsoft), google-auth, Google Calendar API, OpenAI/OpenRouter |
| Frontend | Vanilla JS, CSS; Google Calendar API, Firebase SDK (optional) |
| Infra | Modal (optional), Firebase Realtime Database (optional) |

---

## 🚀 Getting Started

### 1. Environment setup

- Python 3.8+, pip

```bash
git clone https://github.com/infoshubhjain/Project-Helix.git
cd Project-Helix

cd Project
pip install -r requirements.txt
playwright install chromium
```

### 2. Launching the platform

From the repo root:

```bash
./run.sh
```

**Access the dashboard at:** [http://localhost:5001](http://localhost:5001)

Browsing events works immediately with no credentials.

**Optional — virtual environment:**

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

## 📂 Repository Anatomy

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
└── .env.example, Project/.env.example
```

---

## 🔑 Configuration & Security

Helix works **out-of-the-box** for event browsing. To unlock Google Calendar and AI email parsing, follow the [**Credentials Guide**](CREDENTIALS_GUIDE.md).

| Step | Action |
|------|--------|
| **Environment** | Rename `Project/.env.example` to `Project/.env` and fill in values. |
| **Google Cloud** | Place `credentials.json` in `Project/calander/`. |
| **AI parsing** | Add your OpenRouter API key to `Project/.env`. |

---

## Usage

**Local dev:** `./run.sh` or `cd Project && python3 app.py`

**Scrapers (local):** `cd Project && python3 scrape.py`  
**Scrapers (Modal):** `cd Project && modal run scrape.py`

**Smoke test:** `python3 test_app.py` or `make test`

---

## 🌐 Live Demo

**[https://infoshubhjain.github.io/Project-Helix/](https://infoshubhjain.github.io/Project-Helix/)**

GitHub Pages serves the app with Google Calendar integration and persistent auth.

---

## Documentation

- [QUICKSTART.md](QUICKSTART.md) — Short setup
- [CREDENTIALS_GUIDE.md](CREDENTIALS_GUIDE.md) — Azure, OpenRouter, Google
- [SETUP.md](SETUP.md) — Full setup and troubleshooting
- [DEPLOY_TO_GITHUB_PAGES.md](DEPLOY_TO_GITHUB_PAGES.md) — Deploy to GitHub Pages
- [CLAUDE.md](CLAUDE.md) — Architecture and dev notes

---

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT License — see [LICENSE](LICENSE).

---

## Links

[Flask](https://flask.palletsprojects.com/) · [Google Calendar API](https://developers.google.com/calendar) · [Microsoft Graph](https://docs.microsoft.com/en-us/graph/) · [Modal](https://modal.com/) · [Firebase](https://firebase.google.com/)
