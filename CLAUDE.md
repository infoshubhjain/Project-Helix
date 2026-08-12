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
make validate      # py_compile syntax check on scrape.py
make scrape-local  # cd Project && python3 scrape.py  → writes scraped_events.json (hits live network)
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
  - **Before adding a calendar to `GENERAL_CALENDAR_LINKS`, measure its *unique* yield**, not its event count. Most UIUC department calendars already feed the aggregate ones, so they contribute literally zero after the UID dedupe — an Aug 2026 audit of 21 candidates found 15 with 0 unique events. A calendar logging `0 events` in a run is usually correct dedupe, not a failure; confirm by diffing its future UIDs against the calendars listed above it.
  - Calendars 44 (McKinley), 59 (Economics) and 75 (Saturday Physics) return **valid but completely empty** feeds as of Aug 2026. They are kept in case they repopulate; if they are still empty a year on, drop them.
  - A full ID sweep (760–8100) found 116 more feeds with events, but nearly all are room-reservation calendars, course sections, test calendars, IT job schedules and personal calendars — deliberately **not** added. Judge a candidate by reading its event titles, not its event count.
- `scrape_state_farm()` — Playwright headless browser (statefarmcenter.com); has an SSRF guard rejecting off-domain event URLs
- `scrape_athletics()` — **feed-first**: Sidearm per-sport ICS feeds (`fightingillini.com/calendar.ashx/calendar.ics?sport_id=N`), HTML schedule pages as fallback. Home games = "vs" in the summary.
- `_parse_ics_events()` / `_parse_ics_dt()` — minimal stdlib iCal parser both feed paths share (feeds are flat pre-expanded VEVENT lists, no RRULEs)
- `scrape_kcpa()`, `scrape_kam()`, `scrape_music()`, `scrape_spurlock()`, `scrape_parkland()`, `scrape_urbana_library()`, `scrape_gies()`, `scrape_cs()` — per-venue HTML scrapers
- `scrape_food_resources()` — not a scraper: expands the curated recurrence table in `Project/food_resources.py` (soup kitchens, pantries, campus meal programs) into dated occurrences; academic-only programs are gated to `ACADEMIC_TERMS`, which `_refresh_academic_terms()` now derives at scrape time from the Academic Dates calendar (ID 557) via `derive_academic_terms()`; the hardcoded list in `food_resources.py` is only a fallback for when that feed is unreachable. Entries marked `"active": "directory_only"` (appointment-only pantries, reference links) emit **no** dated events — they exist only for the resource list. The same table is dumped to `Project/food_resources.json` by `main()` and rendered by the Food Resource List panel, so the directory and the events never drift apart.

Post-processing, in order: `cap_events()` per source → merge into a numbered-key dict → `drop_past_events()` → `dedupe_events()` (keyed by normalized title + start-to-the-minute; longer description wins) → `cap_recurring_series()` → minified JSON.

`cap_recurring_series()` keeps only the next `MAX_OCCURRENCES_PER_SERIES` (8) of each same-titled series. The frontend already collapses a series into one card, so shipping 210 copies of one office-hours slot was ~380 KB of payload rendering nothing extra. Grouping uses the same normalization as `normalizeTitle()` in browse-events.js — **change both together**. Survivors carry `series_total` / `series_end` so `inferCadence()` can still report the true count.

Resilience layers: every source is isolated (one failure never stops the others); each event carries a `source` tag, and any source returning zero events **salvages** its own events from the previously published JSON (they age out via `drop_past_events`, so a dead source decays gracefully). Empty sources emit `::warning::` annotations on the Actions run. The run only **raises** (preserving the committed JSON) if all sources are empty, or a `CRITICAL_SOURCES` member (`general`, `parkland`, `urbana_library`) is empty *and* nothing could be salvaged. If you add a source that should never be empty, add it there.

Every event dict must pass `validate_event()`; `detect_free_food()` and `classify_event()` assign the tag string the frontend filters on.

`classify_event()` prefers the publisher-assigned ICS `CATEGORIES` value via `_ICS_CATEGORY_MAP` and only keyword-matches when that value is missing or carries no signal (`Other`, `Informational`, `Meeting` are deliberately unmapped). This reclassified 102 of 708 events on calendar 7 — "YMCA Dump & Run" was filed under Performances — and was the first thing ever to assign the `Entertainment` category.

`detect_free_food()` is tiered on purpose — a wrongly tagged event walks a hungry student to a talk with no food:
1. `_FOOD_ABSOLUTE` — "free lunch", "food pantry", "soup kitchen". Tags unconditionally, *outranking the veto*, so a pantry whose own blurb says "food insecurity" is not vetoed by it.
2. `_FOOD_OFFERED` / `_FOOD_TITLE` / `_FOOD_IDIOM` — "lunch provided", a title naming the food ("Crafts and Snacks"), or the campus giveaway idiom ("Donuts with the Deans"). Veto applies.
3. `_FOOD_NOUN` + `_FREE_CUE` co-occurring anywhere in the record — they routinely sit in different sentences, so proximity is deliberately *not* tested.

`_FOOD_VETO` kills tiers 2–3 on paid ("$45", "tickets required") or metaphorical ("food for thought", "food science") matches. Matching is word-boundary regex, never substring — the old substring list tagged "Public Affairs Building" via "pub".

### Frontend (vanilla JS, no frameworks, no build step)

- [index.html](index.html) — single entry point; also a PWA (`manifest.webmanifest`, `service-worker.js` caches the app shell)
- [Project/static/event-utils.js](Project/static/event-utils.js) — **UMD module** of pure helpers (escapeHtml, category mapping, date/time formatting) shared by the browser and the Node test suite. Pure display logic belongs here so it's testable; DOM code goes in browse-events.js.
- [Project/static/browse-events.js](Project/static/browse-events.js) — event cards, Fuse.js fuzzy search, category filter chips, infinite scroll
- [Project/static/calendar-connect.js](Project/static/calendar-connect.js) — Google Calendar OAuth2 (GIS + GAPI, client-side only)
- [Project/static/export.js](Project/static/export.js) — iCal / CSV export
- [Project/static/food-resources.js](Project/static/food-resources.js) — "Food Resource List by Shubh" panel; fetches `Project/food_resources.json` on first open. Links are whitelisted to `http(s)` before rendering — `escapeHtml()` keeps a URL inside its attribute but does not stop a `javascript:` scheme. "Add all to Google Calendar" sends one **recurring** event per recurrence rule (from the `calendar` array `_calendar_entries()` builds), not one per occurrence — ~37 API calls instead of hundreds, and a calendar the user can still read. It adds only what the current filters show, and always confirms first.
- [Project/static/manual-event-parser.js](Project/static/manual-event-parser.js) + `manual-event-handler.js` — NLP event extraction from pasted text (parser is pure and Node-tested; handler is the UI)
- [Project/static/script.js](Project/static/script.js) — toasts, add-event modal, theme toggle

Event categories are canonical and ordered in `CANONICAL_CATEGORIES` in event-utils.js; the scraper's tag strings map onto them via substring matching.

### CI ([.github/workflows/scraper.yml](.github/workflows/scraper.yml))

Two cron entries (14:00 and 15:00 UTC) so the run lands at 9 AM America/Chicago across DST; a guard step skips the duplicate. The job lints with ruff, runs the smoke test + JS tests, scrapes, and commits `scraped_events.json` with `[skip ci]`. Actions are SHA-pinned.

## Security Notes

- Google OAuth token lives in `sessionStorage` (not `localStorage`) — cleared when tab closes
- CSP meta tag in index.html restricts script/style/connect/frame sources; Fuse.js CDN tag is SRI-pinned
- `Project/static/google-config.js` contains a **real, committed** Google OAuth client ID and API key (client-side credentials are public by design). They MUST stay restricted in Google Cloud Console: API key locked to the Pages domain via HTTP-referrer + Calendar API only; OAuth client origin-restricted. Never commit an unrestricted key.
- All user/scraped strings rendered into HTML must go through `escapeHtml()` from event-utils.js

## Conventions

- Python: PEP 8, `snake_case`; JS/CSS files: `kebab-case`
- Commit messages: present tense, short summary
