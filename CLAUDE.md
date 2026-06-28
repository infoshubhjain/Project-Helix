# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Project Helix is a **static-site** campus event aggregator for UIUC. It is served via **GitHub Pages** from `index.html` at the repo root — there is no Flask server, no app.py, no Supabase, and no backend runtime in production.

Events are scraped daily by a **GitHub Actions workflow** (`scrape.py`), which commits the result as `Project/scraped_events.json` to the repo. The frontend reads that JSON file at load time.

## Architecture

```text
GitHub Actions (daily) → scrape.py → Project/scraped_events.json (committed)
                                                  ↓
                                        index.html (GitHub Pages)
                                        browse-events.js fetches the JSON
```

### Key Files

- [index.html](index.html) — Single HTML entry point (GitHub Pages root)
- [Project/scrape.py](Project/scrape.py) — All three scrapers + `scrape()` orchestrator
- [Project/scraped_events.json](Project/scraped_events.json) — Output committed by CI
- [Project/static/browse-events.js](Project/static/browse-events.js) — Event card rendering, fuzzy search, filters, infinite scroll
- [Project/static/calendar-connect.js](Project/static/calendar-connect.js) — Google Calendar OAuth2 (GIS + GAPI, client-side only)
- [Project/static/export.js](Project/static/export.js) — iCal / CSV export
- [Project/static/manual-event-parser.js](Project/static/manual-event-parser.js) — NLP event extraction from free text
- [Project/static/manual-event-handler.js](Project/static/manual-event-handler.js) — UI for manual event parsing
- [Project/static/script.js](Project/static/script.js) — Toast notifications, add-event modal, theme toggle
- [Project/static/style.css](Project/static/style.css) — Complete styling
- [.github/workflows/scraper.yml](.github/workflows/scraper.yml) — Daily scrape CI job
- [tests/](tests/) — Unit tests (unittest, no live HTTP)

### Three Scrapers in scrape.py

1. `scrape_general()` — BeautifulSoup scraping of 14 `calendars.illinois.edu` URLs
2. `scrape_state_farm()` — Playwright headless browser for `statefarmcenter.com`
3. `scrape_athletics()` — HTML parsing of 4 `fightingillini.com` schedule pages

`scrape()` orchestrates all three, caps each source, and merges into a numbered-key dict saved as JSON.

## Development Commands

### Running Scrapers Locally

```bash
cd Project
python scrape.py
```
Writes `Project/scraped_events.json`.

### Running Tests

```bash
python3 -m unittest discover -s tests -v
# or
make test
```

### Installing Dependencies

```bash
cd Project
pip install -r requirements.txt
playwright install --with-deps chromium
# or
make install
```

### Serving the Site Locally

Open `index.html` directly in a browser, or use any static server:

```bash
python3 -m http.server 8080
```
Then visit `http://localhost:8080`.

## Technology Stack

- **Frontend:** Vanilla HTML/CSS/JavaScript (no frameworks)
- **Scraping:** Python, BeautifulSoup4, Playwright, Requests
- **Storage:** `Project/scraped_events.json` (committed to repo)
- **Hosting:** GitHub Pages (static, no server)
- **CI:** GitHub Actions (daily cron, SHA-pinned actions)
- **Search:** Fuse.js (CDN, SRI-verified)
- **Calendar:** Google Calendar API (client-side OAuth2 via GIS + GAPI)

## Security Notes

- Google OAuth token is stored in `sessionStorage` (not `localStorage`) — cleared when tab closes
- CSP meta tag restricts script/style/connect/frame sources
- Fuse.js CDN tag has SRI `integrity=` hash
- Google credentials in `index.html` are **placeholder values** — real credentials must never be committed
- SSRF guard in `scrape_state_farm()` rejects off-domain event URLs
