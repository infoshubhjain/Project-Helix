# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Project Helix is a **static-site** campus event aggregator for UIUC. It is served via **GitHub Pages** from `index.html` at the repo root — there is no Flask server, no backend runtime in production.

Events are scraped daily by a **GitHub Actions workflow** running `Project/scrape.py`, which commits the result as `Project/scraped_events.json`. The frontend fetches that JSON at load time.

## Development Commands

```bash
make install       # pip install -r Project/requirements.txt + playwright chromium
make test          # Python + JS test suites
make test-py       # python3 -m unittest discover -s tests -v
make test-js       # node --test tests/js/*.test.js
make scrape-local  # cd Project && python3 scrape.py  → writes scraped_events.json
ruff check Project/scrape.py   # lint (CI enforces this)
```

Run a single Python test: `python3 -m unittest tests.test_scrapers -v` (or narrower: `tests.test_scrapers.ClassName.test_name`). Tests use unittest with mocked HTTP — no live network.

Serve the site locally: open `index.html` directly, or `python3 -m http.server 8080`.

Lint style note: `ruff.toml` deliberately ignores E701 — the scrapers use compact one-line time-parsing statements (e.g. `if mer == "pm" and h != 12: h += 12`). Keep that style; don't "fix" it.

## Architecture

```text
GitHub Actions (daily cron) → scrape.py → Project/scraped_events.json (committed)
                                                      ↓
                                            index.html (GitHub Pages)
                                            browse-events.js fetches the JSON
```

### Scrape pipeline (Project/scrape.py, ~1700 lines, single file)

`scrape()` runs **12 sources** in sequence, each isolated in try/except so one failure never kills the run:

- `scrape_general()` — **feed-first**: per-calendar iCal feeds (`calendars.illinois.edu/icalGmail/<id>.ics`), falling back to HTML scraping of the list pages only if the feeds go dark. Feeds are stable contracts; the HTML broke in July 2026.
- `scrape_state_farm()` — Playwright headless browser (statefarmcenter.com); has an SSRF guard rejecting off-domain event URLs
- `scrape_athletics()` — **feed-first**: Sidearm per-sport ICS feeds (`fightingillini.com/calendar.ashx/calendar.ics?sport_id=N`), HTML schedule pages as fallback. Home games = "vs" in the summary.
- `_parse_ics_events()` / `_parse_ics_dt()` — minimal stdlib iCal parser both feed paths share (feeds are flat pre-expanded VEVENT lists, no RRULEs)
- `scrape_kcpa()`, `scrape_kam()`, `scrape_music()`, `scrape_spurlock()`, `scrape_parkland()`, `scrape_urbana_library()`, `scrape_gies()`, `scrape_cs()` — per-venue HTML scrapers
- `scrape_food_resources()` — not a scraper: expands the curated recurrence table in `Project/food_resources.py` (soup kitchens, pantries, campus meal programs) into dated occurrences; academic-only programs are gated to the `ACADEMIC_TERMS` dates there, which need **yearly manual updates**

Post-processing, in order: `cap_events()` per source → merge into a numbered-key dict → `drop_past_events()` → `dedupe_events()` (keyed by normalized title + start-to-the-minute; longer description wins) → minified JSON.

Health checks in `main()`: the run **raises** (preserving the previously committed JSON) if all sources return zero events, or if any source in `CRITICAL_SOURCES` (`general`, `parkland`, `urbana_library`) returns zero. If you add a source that should never be empty, add it there.

Every event dict must pass `validate_event()`; `detect_free_food()` and `classify_event()` assign the tag string the frontend filters on.

### Frontend (vanilla JS, no frameworks, no build step)

- [index.html](index.html) — single entry point; also a PWA (`manifest.webmanifest`, `service-worker.js` caches the app shell)
- [Project/static/event-utils.js](Project/static/event-utils.js) — **UMD module** of pure helpers (escapeHtml, category mapping, date/time formatting) shared by the browser and the Node test suite. Pure display logic belongs here so it's testable; DOM code goes in browse-events.js.
- [Project/static/browse-events.js](Project/static/browse-events.js) — event cards, Fuse.js fuzzy search, category filter chips, infinite scroll
- [Project/static/calendar-connect.js](Project/static/calendar-connect.js) — Google Calendar OAuth2 (GIS + GAPI, client-side only)
- [Project/static/export.js](Project/static/export.js) — iCal / CSV export
- [Project/static/manual-event-parser.js](Project/static/manual-event-parser.js) + `manual-event-handler.js` — NLP event extraction from pasted text (parser is pure and Node-tested; handler is the UI)
- [Project/static/script.js](Project/static/script.js) — toasts, add-event modal, theme toggle

Event categories are canonical and ordered in `CANONICAL_CATEGORIES` in event-utils.js; the scraper's tag strings map onto them via substring matching.

### CI ([.github/workflows/scraper.yml](.github/workflows/scraper.yml))

Two cron entries (14:00 and 15:00 UTC) so the run lands at 9 AM America/Chicago across DST; a guard step skips the duplicate. The job lints with ruff, runs the smoke test + JS tests, scrapes, and commits `scraped_events.json` with `[skip ci]`. Actions are SHA-pinned.

## Security Notes

- Google OAuth token lives in `sessionStorage` (not `localStorage`) — cleared when tab closes
- CSP meta tag in index.html restricts script/style/connect/frame sources; Fuse.js CDN tag is SRI-pinned
- `index.html` contains a **real, committed** Google OAuth client ID and API key (client-side credentials are public by design). They MUST stay restricted in Google Cloud Console: API key locked to the Pages domain via HTTP-referrer + Calendar API only; OAuth client origin-restricted. Never commit an unrestricted key.
- All user/scraped strings rendered into HTML must go through `escapeHtml()` from event-utils.js

## Conventions

- Python: PEP 8, `snake_case`; JS/CSS files: `kebab-case`
- Commit messages: present tense, short summary
