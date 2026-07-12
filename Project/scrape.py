#-----------------------IMPORTS & VARIABLES-----------------------#
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import os
import re
import json
import html
import time
import logging
from typing import Dict, List, Optional, Any
from playwright.sync_api import sync_playwright
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from urllib.parse import urljoin, urlparse


#-----------------------CONFIGURATION & LOGGING-----------------------#
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraping.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Scraping configuration
MAX_RETRIES = 3
RETRY_DELAY = 2            # seconds (retry backoff factor)
REQUEST_TIMEOUT = 30       # seconds
MAX_PAGES_PER_CALENDAR = 10
MAX_EVENTS_PER_SOURCE = 2000
USER_AGENT = 'Mozilla/5.0 (compatible; ProjectHelix/1.0; +https://github.com/infoshubhjain/Project-Helix)'
RATE_LIMIT_DELAY = 1       # seconds between requests

# Variables & Constants
last_scrape_stats: Dict[str, Dict[str, Any]] = {}
GENERAL_CALENDAR_LINKS = [
    # Original sources
    "https://calendars.illinois.edu/list/7",    # General Events
    "https://calendars.illinois.edu/list/557",  # Academic Dates
    "https://calendars.illinois.edu/list/594",  # Advising & Placement
    "https://calendars.illinois.edu/list/4756", # Chicago-area campus events
    "https://calendars.illinois.edu/list/596",  # Cultural & International
    "https://calendars.illinois.edu/list/62",   # Exhibits
    "https://calendars.illinois.edu/list/597",  # Performances
    "https://calendars.illinois.edu/list/637",  # Recreation, Health & Wellness
    "https://calendars.illinois.edu/list/4757", # Research Calendar (OVCRI)
    "https://calendars.illinois.edu/list/598",  # Speakers
    "https://calendars.illinois.edu/list/2568", # Grainger College of Engineering
    "https://calendars.illinois.edu/list/4063", # Illini Union All Events
    "https://calendars.illinois.edu/list/5510", # IASL Campus Events
    "https://calendars.illinois.edu/list/4092", # Library Calendar
    # Additional sources discovered via ID scan
    "https://calendars.illinois.edu/list/33",   # Krannert Center
    "https://calendars.illinois.edu/list/44",   # McKinley Health Center
    "https://calendars.illinois.edu/list/45",   # Center for Global Studies
    "https://calendars.illinois.edu/list/59",   # Department of Economics
    "https://calendars.illinois.edu/list/60",   # University Housing
    "https://calendars.illinois.edu/list/75",   # Saturday Physics for Everyone
    "https://calendars.illinois.edu/list/79",   # Materials Research Laboratory
    "https://calendars.illinois.edu/list/25",   # Center for Advanced Study
    "https://calendars.illinois.edu/list/7767", # Illinois Public Media (WILL)
]
KCPA_CALENDAR_LINK    = "https://krannertcenter.com/calendar"
KAM_EVENTS_LINK       = "https://kam.illinois.edu/exhibitions-events/events"
MUSIC_EVENTS_LINK     = "https://music.illinois.edu/events"
SPURLOCK_EVENTS_LINK  = "https://spurlock.illinois.edu/events"
PARKLAND_EVENTS_JSON  = "https://25livepub.collegenet.com/calendars/Website-Events.json"
URBANA_LIBRARY_WIDGET = "https://urbanafreelibrary.libnet.info/widget?id=15863&style=1168&location=1672"
GIES_EVENTS_LINK      = "https://giesbusiness.illinois.edu/events"
CS_CALENDAR_LINK      = "https://siebelschool.illinois.edu/news/calendar"
STATE_FARM_CENTER_CALENDAR_LINK = "https://www.statefarmcenter.com/events/all"
ATHLETIC_TICKET_LINKS = [
    "https://fightingillini.com/sports/football/schedule",
    "https://fightingillini.com/sports/mens-basketball/schedule",
    "https://fightingillini.com/sports/womens-basketball/schedule",
    "https://fightingillini.com/sports/womens-volleyball/schedule"
]
# Sidearm per-sport ICS feeds: (sport name, feed URL, public schedule page)
ATHLETICS_ICS_FEEDS = [
    ("Football",           "https://fightingillini.com/calendar.ashx/calendar.ics?sport_id=2",
     "https://fightingillini.com/sports/football/schedule"),
    ("Men's Basketball",   "https://fightingillini.com/calendar.ashx/calendar.ics?sport_id=5",
     "https://fightingillini.com/sports/mens-basketball/schedule"),
    ("Women's Basketball", "https://fightingillini.com/calendar.ashx/calendar.ics?sport_id=10",
     "https://fightingillini.com/sports/womens-basketball/schedule"),
    ("Volleyball",         "https://fightingillini.com/calendar.ashx/calendar.ics?sport_id=17",
     "https://fightingillini.com/sports/womens-volleyball/schedule"),
]
#-----------------------HELPER FUNCTIONS-----------------------#
def create_robust_session() -> requests.Session:
    """Create a requests session with retry logic and proper headers."""
    session = requests.Session()

    retry_strategy = Retry(
        total=MAX_RETRIES,
        status_forcelist=[429, 500, 502, 503, 504],
        backoff_factor=RETRY_DELAY,
        raise_on_status=False,
        allowed_methods=["HEAD", "GET", "OPTIONS"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Set headers
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    })
    
    return session

def safe_request(url: str, session: requests.Session, method: str = "GET", **kwargs) -> Optional[requests.Response]:
    """Make a safe HTTP request with error handling and logging."""
    try:
        # Add rate limiting
        time.sleep(RATE_LIMIT_DELAY)

        response = session.request(method, url, timeout=REQUEST_TIMEOUT, **kwargs)

        if response.status_code == 200:
            logger.debug(f"Successfully fetched: {url}")
            return response
        logger.warning(f"HTTP {response.status_code} for {url}")
        return None
    except Exception as e:
        logger.error(f"Request failed for {url}: {e}")
        return None

def validate_event(event: Dict[str, Any]) -> bool:
    """An event must have a non-empty summary."""
    if not event.get('summary'):
        logger.warning(f"Event missing required field 'summary': {event}")
        return False
    return True


def parse_month_to_number(month_str: str) -> int:
    """Return 1-12 for a month name or abbreviation; returns 1 on unrecognised input."""
    month_str = month_str.strip()
    for fmt in ("%B", "%b"):
        try:
            return datetime.strptime(month_str, fmt).month
        except ValueError:
            continue
    logger.warning("Unrecognised month string: %r — defaulting to 1", month_str)
    return 1


def _to_24h(h: int, mer: str) -> int:
    """12-hour value → 24-hour, given its meridiem ('am'/'pm')."""
    if mer == "pm" and h != 12: h += 12
    elif mer == "am" and h == 12: h = 0
    return h


def parse_12h_time(text: str) -> Optional[tuple]:
    """First '5:30 pm' / '5 pm' / '7 p.m.' clock in text → (hour24, minute), or None."""
    m = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", text.replace(".", ""), re.IGNORECASE)
    if not m:
        return None
    return _to_24h(int(m.group(1)), m.group(3).lower()), int(m.group(2) or 0)


# ---- Minimal iCalendar parsing (stdlib only) -------------------------------
# The WebTools and Sidearm feeds are flat, pre-expanded VEVENT lists (no
# RRULEs), so a ~30-line parser beats a dependency.

def _ics_unescape(s: str) -> str:
    """Undo RFC 5545 text escaping."""
    return (s.replace("\\n", " ").replace("\\N", " ")
             .replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\"))


def _parse_ics_events(text: str) -> List[Dict[str, str]]:
    """Return one {PROPERTY: raw_value} dict per VEVENT (params stripped)."""
    # Unfold continuation lines (RFC 5545 §3.1)
    lines: List[str] = []
    for raw in text.splitlines():
        if raw[:1] in (" ", "\t") and lines:
            lines[-1] += raw[1:]
        else:
            lines.append(raw)

    events: List[Dict[str, str]] = []
    cur: Optional[Dict[str, str]] = None
    for line in lines:
        if line.startswith("BEGIN:VEVENT"):
            cur = {}
        elif line.startswith("END:VEVENT"):
            if cur is not None:
                events.append(cur)
            cur = None
        elif cur is not None and ":" in line:
            key, _, value = line.partition(":")
            cur[key.split(";", 1)[0].upper()] = value
    return events


def _parse_ics_dt(value: str, tz: ZoneInfo) -> Optional[datetime]:
    """ICS datetime → aware datetime. Handles UTC ('...Z'), naive-local, and date-only."""
    value = value.strip()
    try:
        if value.endswith("Z"):
            return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).astimezone(tz)
        if "T" in value:
            return datetime.strptime(value, "%Y%m%dT%H%M%S").replace(tzinfo=tz)
        return datetime.strptime(value, "%Y%m%d").replace(tzinfo=tz)
    except ValueError:
        return None


def parse_12h_range(text: str) -> Optional[tuple]:
    """'5:30 pm - 7:00 pm' (start meridiem may be omitted: '9:00 - 10:00 pm')
    → ((start_h24, start_m), (end_h24, end_m)), or None."""
    m = re.search(
        r"(\d{1,2}):(\d{2})\s*(am|pm)?\s*(?:[-–—]|to)\s*(\d{1,2}):(\d{2})\s*(am|pm)",
        text.replace(".", ""), re.IGNORECASE,
    )
    if not m:
        return None
    sh, sm, s_mer, eh, em, e_mer = m.groups()
    s_mer = (s_mer or e_mer).lower()
    return (_to_24h(int(sh), s_mer), int(sm)), (_to_24h(int(eh), e_mer.lower()), int(em))

def detect_free_food(event_info):
    """Append 'Free Food 🍕' tag when event mentions food; does not overwrite existing tags."""
    FREE_FOOD_KEYWORDS = [
        "pizza", "lunch", "dinner", "breakfast", "brunch", "snacks", "refreshments",
        "cookies", "donuts", "bagels", "coffee", "meal", "food",
        "free food", "free pizza", "free lunch", "free dinner", "free breakfast",
        "lunch provided", "dinner provided", "food will be served",
        "snacks provided", "free snacks", "complimentary food", "free meal",
        "pizza party", "food included", "lunch included", "dinner included",
        "continental breakfast", "catered", "potluck", "bbq", "cookout",
        "reception with food", "light refreshments", "food and drinks",
        "social hour", "networking lunch", "luncheon", "banquet", "mixer",
        "tailgate", "picnic", "buffet",
    ]

    FOOD_LOCATIONS = [
        "dining hall", "restaurant", "cafe", "kitchen", "union basement",
        "coffee shop", "bakery", "grill", "pub", "tavern", "snack bar",
    ]

    text_to_check = " ".join([
        event_info.get("summary", ""),
        event_info.get("description", ""),
        event_info.get("location", ""),
    ]).lower()

    def _tag_food():
        existing = event_info.get("tag", "")
        if "Free Food" not in existing:
            event_info["tag"] = (existing + ", Free Food 🍕").lstrip(", ") if existing else "Free Food 🍕"

    for keyword in FREE_FOOD_KEYWORDS:
        if keyword in text_to_check:
            _tag_food()
            return event_info

    summary_lower = event_info.get("summary", "").lower()
    if any(k in summary_lower for k in ["social", "meeting", "workshop", "information", "gathering"]):
        for loc in FOOD_LOCATIONS:
            if loc in text_to_check:
                _tag_food()
                return event_info

    return event_info

# Category keyword map — checked in priority order; first match wins.
# Keywords are matched on word boundaries against summary + description + location.
CATEGORY_KEYWORDS = [
    ("Athletics", [
        "basketball", "football", "volleyball", "soccer", "baseball", "softball",
        "tennis", "wrestling", "gymnastics", "track meet", "cross country",
        "tournament", "scrimmage", "vs.", "match", "home game", "fighting illini",
    ]),
    ("Performances", [
        "concert", "recital", "symphony", "orchestra", "opera", "jazz",
        "ensemble", "musical", "theatre", "theater", "ballet", "choir",
        "chorus", "performance", "live music", "cabaret", "philharmonic",
    ]),
    ("Arts", [
        "exhibit", "exhibition", "gallery", "museum", "sculpture", "painting",
        "photography", "film screening", "screening", "poetry reading",
        "art show", "artmaking", "craft", "ceramics",
    ]),
    ("Academic", [
        "lecture", "seminar", "colloquium", "symposium", "conference",
        "workshop", "defense", "dissertation", "thesis", "prelim",
        "qualifying exam", "final exam", "webinar", "info session",
        "information session", "advising", "research", "tutorial",
        "guest speaker", "distinguished", "panel", "journal club",
        "office hours", "study abroad", "career fair", "graduation",
        "commencement", "orientation",
    ]),
    ("Entertainment", [
        "comedy", "movie", "trivia", "game night", "karaoke", "bingo",
        "open mic", "tailgate",
    ]),
    ("Community", [
        "festival", "fair", "market", "volunteer", "fundraiser", "community",
        "open house", "celebration", "family", "storytime", "story time",
        "book club", "drop-in", "wellness", "yoga", "meditation", "support group",
    ]),
]

_CATEGORY_PATTERNS = [
    (cat, re.compile(r"\b(?:" + "|".join(re.escape(k) for k in kws) + r")\b", re.IGNORECASE))
    for cat, kws in CATEGORY_KEYWORDS
]

def classify_event(summary: str, description: str = "", location: str = "") -> str:
    """Infer a category from event text. Returns a canonical category or 'General'."""
    text = " ".join([summary or "", description or "", location or ""])
    for category, pattern in _CATEGORY_PATTERNS:
        if pattern.search(text):
            return category
    return "General"

def cap_events(events: Dict[Any, Dict[str, Any]], max_events: int) -> Dict[Any, Dict[str, Any]]:
    """Cap source events to avoid runaway growth from parser/site changes."""
    if not isinstance(events, dict):
        return {}
    if len(events) <= max_events:
        return events

    capped_items = list(events.items())[:max_events]
    logger.warning(
        "Capping source events from %s to %s to prevent oversized output.",
        len(events),
        max_events,
    )
    return dict(capped_items)
#-----------------------SCRAPERS-----------------------#
# Individual Scrapers
def scrape_general() -> Dict[str, Any]:
    """General university calendars — iCal feed first (a stable, published
    contract), falling back to HTML scraping only if the feeds go dark.
    The July 2026 site redesign broke the HTML path for four days; feeds
    don't churn like markup does."""
    events, dead_links = _scrape_general_feed()
    if not events:
        logger.warning("General iCal feeds yielded no events — falling back to HTML scraping.")
        return _scrape_general_html()
    if dead_links:
        # A broken feed shouldn't drop its calendar — HTML-scrape just those.
        logger.warning("General: %d feed(s) unusable, HTML-scraping: %s", len(dead_links), dead_links)
        for ev in _scrape_general_html(dead_links).values():
            events[len(events)] = ev
    return events


def _scrape_general_feed() -> tuple:
    """Read each calendar's whole-calendar ICS feed (icalGmail/<id>.ics).

    Returns (events, dead_links) — dead_links are calendars whose feed was
    unreachable or not a calendar at all (a valid-but-empty feed is normal:
    several calendars are dormant, and cross-calendar UID dedup can leave a
    later calendar with nothing new to add)."""
    session = create_robust_session()
    events: Dict[int, Any] = {}
    dead_links: List[str] = []
    seen_uids: set = set()
    TZ = ZoneInfo("America/Chicago")
    cutoff = datetime.now(tz=TZ) - timedelta(days=1)  # feeds include history; keep volume sane

    for base_link in GENERAL_CALENDAR_LINKS:
        cal_id = base_link.rstrip("/").rsplit("/", 1)[-1]
        if not cal_id.isdigit():
            continue
        response = safe_request(f"https://calendars.illinois.edu/icalGmail/{cal_id}.ics", session)
        if not response or "BEGIN:VCALENDAR" not in response.text:
            logger.warning("General: unusable ICS feed for calendar %s — will HTML-scrape it", cal_id)
            dead_links.append(base_link)
            continue
        if "BEGIN:VEVENT" not in response.text:
            logger.info("General: calendar %s feed is valid but empty", cal_id)
            continue

        count = 0
        for ve in _parse_ics_events(response.text):
            try:
                summary = _ics_unescape(ve.get("SUMMARY", "")).strip()
                start_raw = ve.get("DTSTART", "")
                start_dt = _parse_ics_dt(start_raw, TZ)
                if not summary or not start_dt:
                    continue

                end_dt = _parse_ics_dt(ve.get("DTEND", ""), TZ)
                if "T" not in start_raw:  # date-only → all-day
                    end_dt = start_dt.replace(hour=23, minute=59)
                elif not end_dt or end_dt <= start_dt:
                    end_dt = start_dt + timedelta(hours=1)
                if end_dt < cutoff:
                    continue

                # UID is unique per occurrence and shared across calendars,
                # so it also dedupes events listed on several feeds.
                uid = ve.get("UID") or f"{summary}|{start_raw}"
                if uid in seen_uids:
                    continue
                seen_uids.add(uid)

                description = _ics_unescape(ve.get("DESCRIPTION", "")).strip()[:500]
                location = _ics_unescape(ve.get("LOCATION", "")).strip() or "TBA"
                categories = _ics_unescape(ve.get("CATEGORIES", ""))

                event_info = {
                    "summary": summary,
                    "description": description,
                    "location": location,
                    "htmlLink": ve.get("URL", "").replace("http://", "https://", 1)
                                or f"https://calendars.illinois.edu/list/{cal_id}",
                    "tag": classify_event(summary, f"{description} {categories}", location),
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat(),
                }
                event_info = detect_free_food(event_info)
                if validate_event(event_info):
                    events[len(events)] = event_info
                    count += 1
            except Exception as e:
                logger.error("General feed: error parsing VEVENT: %s", e)
                continue
        logger.info("General feed: %s events from calendar %s", count, cal_id)

    return events, dead_links


def _scrape_general_html(links: Optional[List[str]] = None) -> Dict[str, Any]:
    """Scrape general university calendars from their HTML list pages."""
    session = create_robust_session()
    events: Dict[int, Any] = {}
    seen_links: set = set()   # deduplicate across calendar pages
    local_count = 0
    successful_calendars = 0
    failed_calendars = 0

    if links is None:
        links = GENERAL_CALENDAR_LINKS
    logger.info(f"Starting to scrape {len(links)} general calendars")

    for i, base_calendar_link in enumerate(links):
        logger.info(f"Processing calendar {i+1}/{len(links)}: {base_calendar_link}")
        
        # Ensure we use list view and show recurring events
        current_url = f"{base_calendar_link}?listType=list&isRecurring=true"
        page_num = 0
        calendar_events = 0
        
        try:
            while current_url and page_num < MAX_PAGES_PER_CALENDAR:
                logger.debug(f"Scraping page {page_num + 1}: {current_url}")
                
                response = safe_request(current_url, session)
                if not response:
                    logger.warning(f"Failed to fetch page {page_num + 1} for {base_calendar_link}")
                    break
                    
                soup = BeautifulSoup(response.text, "lxml")
                container = soup.find(id="ws-calendar-container")
                if not container:
                    logger.warning(f"No calendar container found for {base_calendar_link}")
                    break

                # The structure in list view:
                # <h2>Date Header</h2>
                # <ul class="event-entries">...events...</ul>
                
                # We iterate through all h2 headers in the container
                headers = container.find_all("h2")
                
                for header in headers:
                    # The site emits non-breaking spaces ("July\xa012") — normalize them.
                    date_str = header.get_text(strip=True).replace("\xa0", " ")
                    # Example date_str: "Tuesday, February 10, 2026"
                    
                    # Verify this is actually a date header
                    try:
                        # Attempt to parse date to confirm it's a date header
                        # Format: DayOfWeek, Month Day, Year
                        current_date_obj = datetime.strptime(date_str, "%A, %B %d, %Y")
                    except ValueError:
                        # Not a date header, skip
                        continue

                    # The next sibling should be the list of events
                    next_sibling = header.find_next_sibling()
                    if next_sibling and next_sibling.name == "ul" and "event-entries" in next_sibling.get("class", []):
                        event_entries = next_sibling.find_all("li", class_="entry")
                        
                        for entry in event_entries:
                            try:
                                event_info = {}

                                # Title and Link — old markup: div.title > a;
                                # July 2026 redesign: .entry-heading > h3 > a
                                title_div = entry.find("div", class_="title") or entry.find(class_="entry-heading")
                                if not title_div: continue
                                link_tag = title_div.find("a")
                                if not link_tag: continue
                                
                                event_info["summary"] = link_tag.get_text(strip=True)
                                raw_href = link_tag.get("href", "")
                                if raw_href.startswith("/"):
                                    event_info["htmlLink"] = "https://calendars.illinois.edu" + raw_href
                                else:
                                    event_info["htmlLink"] = raw_href

                                # Skip duplicates from overlapping calendar pages —
                                # keyed by (date, link) so a recurring event keeps
                                # every occurrence, not just its first date.
                                seen_key = (current_date_obj.date(), event_info["htmlLink"])
                                if seen_key in seen_links:
                                    continue
                                seen_links.add(seen_key)
                                    
                                # Meta: Time and Location — old markup: div.event-meta with
                                # li.date / li.location; redesign: dl.entry-meta with
                                # .entry-time / .entry-location holding the value in a <dd>.
                                meta = entry.find("div", class_="event-meta") or entry.find(class_="entry-meta")
                                time_str = "All Day"
                                location = "TBA"
                                if meta:
                                    time_tag = meta.find("li", class_="date") or meta.find(class_="entry-time")
                                    if time_tag:
                                        time_str = (time_tag.find("dd") or time_tag).get_text(" ", strip=True)

                                    loc_tag = meta.find("li", class_="location") or meta.find(class_="entry-location")
                                    if loc_tag:
                                        location = (loc_tag.find("dd") or loc_tag).get_text(" ", strip=True)

                                event_info["location"] = location
                                event_info["description"] = "" # List view doesn't have full description
                                event_info["tag"] = classify_event(
                                    event_info["summary"], "", location
                                )
                                
                                # Parse Time
                                start_dt = None
                                end_dt = None
                                
                                TZ = ZoneInfo("America/Chicago")
                                y, mo, d = current_date_obj.year, current_date_obj.month, current_date_obj.day

                                # Handle "All Day"
                                rng = None if "All Day" in time_str else parse_12h_range(time_str)
                                single = None if "All Day" in time_str else parse_12h_time(time_str)
                                if rng:
                                    (sh, sm), (eh, em) = rng
                                    start_dt = datetime(y, mo, d, sh, sm, tzinfo=TZ)
                                    end_dt   = datetime(y, mo, d, eh, em, tzinfo=TZ)
                                elif single:
                                    start_dt = datetime(y, mo, d, single[0], single[1], tzinfo=TZ)
                                    end_dt   = start_dt + timedelta(hours=1)
                                else:
                                    start_dt = datetime(y, mo, d, 0, 0, tzinfo=TZ)
                                    end_dt   = datetime(y, mo, d, 23, 59, tzinfo=TZ)

                                event_info["start"] = start_dt.isoformat()
                                event_info["end"]   = end_dt.isoformat() if end_dt else ""

                                # Validate and add event
                                if validate_event(event_info):
                                    event_info = detect_free_food(event_info)
                                    events[local_count] = event_info
                                    local_count += 1
                                    calendar_events += 1
                                
                            except Exception as e:
                                logger.error(f"Error parsing event entry: {e}")
                                continue

                # Pagination
                next_link_div = soup.select_one("div.next-link a")
                if next_link_div and next_link_div.get("href"):
                    next_href = next_link_div.get("href")
                    if next_href.startswith("/"):
                        current_url = "https://calendars.illinois.edu" + next_href
                    else:
                        current_url = next_href  # Should probably handle relative paths better if needed
                    page_num += 1
                else:
                    current_url = None # No more pages

            if calendar_events > 0:
                successful_calendars += 1
                logger.info(f"Successfully scraped {calendar_events} events from {base_calendar_link}")
            else:
                failed_calendars += 1
                logger.warning(f"No events found in {base_calendar_link}")
                
        except Exception as e:
            failed_calendars += 1
            logger.error(f"Error scraping {base_calendar_link}: {e}")
            continue

    logger.info(f"General scraping complete: {successful_calendars} successful, {failed_calendars} failed calendars")
    return events

_STATEFARM_ALLOWED_HOST = "www.statefarmcenter.com"

def scrape_state_farm():
    events: Dict[int, Any] = {}
    local_count = 0
    print("\n🔍 Scraping State Farm Center...")
    print(f"   Link: {STATE_FARM_CENTER_CALENDAR_LINK}")
    try:
        session = create_robust_session()
        response = safe_request(STATE_FARM_CENTER_CALENDAR_LINK, session)
        if not response:
            print("   ❌ Failed to fetch State Farm Center main page")
            return events

        soup = BeautifulSoup(response.text, "lxml")
        event_listings = soup.find_all("a", class_="more buttons-hide")
        if not event_listings:
            event_listings = soup.select('a[href*="/events/detail/"]')
        
        print(f"   Found {len(event_listings)} event listings")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
            
            seen_urls = set()
            for i, a in enumerate(event_listings):
                try:
                    event_link = a.get("href")
                    if not event_link or event_link in seen_urls:
                        continue
                    if not event_link.startswith("http"):
                        event_link = urljoin("https://www.statefarmcenter.com/", event_link)
                    # SSRF guard: only follow links on the expected host
                    if urlparse(event_link).netloc != _STATEFARM_ALLOWED_HOST:
                        logger.warning("Skipping off-domain URL: %s", event_link)
                        continue
                    seen_urls.add(event_link)

                    print(f"   [{i+1}/{len(event_listings)}] Detail: {event_link}")
                    page.goto(event_link, wait_until="domcontentloaded", timeout=20000)
                    detail_soup = BeautifulSoup(page.content(), "lxml")

                    event_info = {}
                    title_el = detail_soup.find("h1", class_="title") or detail_soup.find("h1")
                    event_info["summary"] = title_el.text.strip() if title_el and title_el.text else "State Farm Center Event"
                    
                    event_info["description"] = ""
                    desc = detail_soup.find("div", class_="description_inner")
                    if desc:
                        ps = desc.find_all("p")
                        event_info["description"] = " ".join(p.text for p in ps if p.text).strip()
                    
                    event_info["htmlLink"] = event_link
                    event_info["location"] = "State Farm Center 1800 S 1st St, Champaign, IL 61820"
                    event_info["tag"] = "Entertainment"

                    sidebar = detail_soup.find("ul", class_="eventDetailList")
                    if sidebar:
                        month_el = sidebar.find("span", class_="m-date__month")
                        day_el = sidebar.find("span", class_="m-date__day")
                        year_el = sidebar.find("span", class_="m-date__year")
                        
                        if month_el and day_el and year_el:
                            month = month_el.text.strip()
                            day = int(re.sub(r"\D", "", day_el.text.strip()) or "1")
                            year = int(re.sub(r"\D", "", year_el.text.strip()) or str(datetime.now().year))
                            
                            start_li = sidebar.find("li", class_="item sidebar_event_starts")
                            start_time_str = start_li.find("span").text.strip() if start_li and start_li.find("span") else ""
                            
                            t = parse_12h_time(start_time_str)
                            # Default to 7PM if time missing but date exists
                            hour, minute = t if t else (19, 0)
                            start_dt = datetime(year, parse_month_to_number(month), day, hour, minute, tzinfo=ZoneInfo("America/Chicago"))
                            
                            end_dt = start_dt + timedelta(hours=3)
                            event_info["start"] = start_dt.isoformat()
                            event_info["end"] = end_dt.isoformat()
                        else:
                            event_info["start"] = ""
                            event_info["end"] = ""
                    else:
                        event_info["start"] = ""
                        event_info["end"] = ""

                    event_info = {k: (v.strip() if isinstance(v, str) else v) for k, v in event_info.items()}
                    event_info = detect_free_food(event_info)
                    if not validate_event(event_info):
                        continue
                    events[local_count] = event_info
                    local_count += 1

                except Exception as e:
                    print(f"      ⚠️  Error processing {event_link}: {e}")
                    continue

            browser.close()
    except Exception as e:
        print(f"   ❌ Error in scrape_state_farm: {e}")
    return events

def scrape_athletics():
    """Home games for the four ticketed sports — Sidearm ICS feed first,
    HTML schedule pages as fallback (the markup broke silently in July 2026;
    the feed is a published contract)."""
    events = _scrape_athletics_feed()
    if events:
        return events
    logger.warning("Athletics ICS feeds yielded no events — falling back to HTML scraping.")
    return _scrape_athletics_html()


def _scrape_athletics_feed() -> Dict[str, Any]:
    session = create_robust_session()
    events: Dict[int, Any] = {}
    TZ = ZoneInfo("America/Chicago")

    print("\n🔍 Scraping Athletics ICS feeds...")
    for sport, feed_url, schedule_url in ATHLETICS_ICS_FEEDS:
        response = safe_request(feed_url, session)
        if not response or "BEGIN:VEVENT" not in response.text:
            logger.warning("Athletics: no usable ICS feed for %s", sport)
            continue

        count = 0
        for ve in _parse_ics_events(response.text):
            try:
                summary = _ics_unescape(ve.get("SUMMARY", "")).strip()
                # Past games carry a result prefix like "[W] " — strip it.
                summary = re.sub(r"^\[\w\]\s*", "", summary)
                # Home games say "vs"; away games say "at".
                m = re.search(r"\bvs\.?\s+(.+)", summary)
                if not m:
                    continue
                opponent = re.split(r"\s+[-–—|]\s+", m.group(1))[0].strip()

                start_dt = _parse_ics_dt(ve.get("DTSTART", ""), TZ)
                if not start_dt:
                    continue
                end_dt = _parse_ics_dt(ve.get("DTEND", ""), TZ) or start_dt + timedelta(hours=3)

                event_info = {
                    "summary": f"{sport} Game: Illinois VS. {opponent}",
                    "description": _ics_unescape(ve.get("DESCRIPTION", "")).strip()[:500],
                    "location": _ics_unescape(ve.get("LOCATION", "")).strip() or "Champaign, Ill.",
                    "tag": "Athletics",
                    "htmlLink": schedule_url,
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat(),
                }
                event_info = detect_free_food(event_info)
                if validate_event(event_info):
                    events[len(events)] = event_info
                    count += 1
            except Exception as e:
                logger.error("Athletics feed: error parsing VEVENT: %s", e)
                continue
        print(f"   ✅ {sport}: {count} home games from feed")

    return events


def _scrape_athletics_html():
    session = create_robust_session()
    events: Dict[int, Any] = {}
    local_count = 0

    print("\n🔍 Scraping Athletics Schedules...")
    for calendar_link in ATHLETIC_TICKET_LINKS:
        try:
            print(f"   Scraping {calendar_link}...")
            response = safe_request(calendar_link, session)
            if not response:
                print(f"   ❌ Failed to fetch {calendar_link}")
                continue
            
            soup = BeautifulSoup(response.text, "lxml")

            # Sport title — legacy: div.sidearm-schedule-title h2;
            # July 2026 redesign: h1.s-common__header-title. Both read
            # e.g. "2026 Football Schedule".
            sport = "Sport"
            title_el = (soup.select_one("div.sidearm-schedule-title h2")
                        or soup.find("h1", class_=re.compile("header-title")))
            if title_el and title_el.get_text(strip=True):
                m = re.search(r"[\d-]+\s*(.*)\s*Schedule", title_el.get_text(" ", strip=True))
                if m:
                    sport = m.group(1).strip()

            # Normalize both markups to (opponent, date_text, time_text, location).
            games = []

            # Legacy Sidearm list layout
            for listing in soup.find_all("li", class_="sidearm-schedule-home-game"):
                opp_div = listing.find("div", class_="sidearm-schedule-game-opponent-name")
                opponent = "Opponent"
                if opp_div:
                    a_tag = opp_div.find("a")
                    if a_tag and a_tag.text:
                        opponent = a_tag.text.strip()
                    elif opp_div.text:
                        opponent = opp_div.text.strip()

                date_text = time_text = ""
                date_div = listing.find("div", class_="sidearm-schedule-game-opponent-date")
                if date_div:
                    spans = date_div.find_all("span")
                    if len(spans) >= 1 and spans[0].text:
                        date_text = spans[0].text
                    if len(spans) >= 2 and spans[1].text:
                        time_text = spans[1].text

                location = "Champaign, Ill."
                loc_div = listing.find("div", class_="sidearm-schedule-game-location")
                if loc_div:
                    loc_spans = loc_div.find_all("span")
                    if len(loc_spans) >= 2:
                        location = f"{loc_spans[1].text.strip()}, {loc_spans[0].text.strip()}"
                    elif len(loc_spans) == 1:
                        location = loc_spans[0].text.strip()
                games.append((opponent, date_text, time_text, location))

            # July 2026 Sidearm card layout — home games carry a "vs" stamp.
            if not games:
                for card in soup.find_all(class_="s-game-card"):
                    stamp = card.find(class_="s-game-card__header__stamp")
                    if not stamp or stamp.get_text(strip=True).lower() != "vs":
                        continue  # away game
                    opp = card.find(attrs={"data-test-id": "s-game-card-standard__header-team-opponent-link"})
                    opponent = opp.get_text(strip=True) if opp else "Opponent"
                    dt_el = card.find(class_="s-game-card__header__game-score-time")
                    dt_text = dt_el.get_text(" ", strip=True) if dt_el else ""  # "Sep 3 (Thu) 8 PM CT"
                    facility = card.find(attrs={"data-test-id": "s-game-card-facility-and-location__game-facility-title-link"})
                    city = card.find(attrs={"data-test-id": "s-game-card-facility-and-location__standard-location-details"})
                    location = ", ".join(x.get_text(strip=True) for x in (facility, city) if x) or "Champaign, Ill."
                    games.append((opponent, dt_text, dt_text, location))

            print(f"      Found {len(games)} home games")

            for i, (opponent, date_text, time_text, location) in enumerate(games):
                try:
                    event_info = {
                        "description": "", "tag": "Athletics", "htmlLink": calendar_link,
                        "summary": f"{sport} Game: Illinois VS. {opponent}",
                        "location": location, "start": "", "end": "",
                    }

                    date_match = re.search(r"(\w+)\s+(\d+)", date_text or "")
                    if date_match:
                        month_num = parse_month_to_number(date_match.group(1))
                        day = int(date_match.group(2))

                        _now = datetime.now()
                        # Simple school year wrap-around logic
                        if _now.month >= 8 and month_num < 8:
                            year = _now.year + 1
                        else:
                            year = _now.year

                        t = parse_12h_time(time_text or "")
                        hour, minute = t if t else (12, 0)
                        start_dt = datetime(year, month_num, day, hour, minute, tzinfo=ZoneInfo("America/Chicago"))
                        end_dt = start_dt + timedelta(hours=3)
                        event_info["start"] = start_dt.isoformat()
                        event_info["end"] = end_dt.isoformat()

                    event_info = {k: (v.strip() if isinstance(v, str) else v) for k, v in event_info.items()}
                    event_info = detect_free_food(event_info)
                    if not validate_event(event_info):
                        continue
                    events[local_count] = event_info
                    local_count += 1
                except Exception as e:
                    print(f"      ⚠️  Error parsing game {i+1}: {e}")
                    continue

        except Exception as e:
            print(f"   ❌ Error scraping {calendar_link}: {e}")
    return events

def scrape_kcpa() -> Dict[str, Any]:
    """Scrape Krannert Center for the Performing Arts calendar.

    List page: https://krannertcenter.com/calendar
    Structure: <div class="views-row"> contains title link + date
    Detail page provides time and venue.
    """
    events: Dict[int, Any] = {}
    local_count = 0
    session = create_robust_session()
    TZ = ZoneInfo("America/Chicago")

    print("\n🔍 Scraping Krannert Center for the Performing Arts...")
    try:
        response = safe_request(KCPA_CALENDAR_LINK, session)
        if not response:
            print("   ❌ Failed to fetch KCPA calendar page")
            return events

        soup = BeautifulSoup(response.text, "lxml")
        rows = soup.find_all(class_="views-row")
        print(f"   Found {len(rows)} event rows")

        seen_hrefs: set = set()
        for row in rows:
            try:
                link_el = row.find("a")
                if not link_el:
                    continue
                href = link_el.get("href", "")
                if not href or href in seen_hrefs:
                    continue
                seen_hrefs.add(href)
                event_url = href if href.startswith("http") else "https://krannertcenter.com" + href

                # Parse date from list row — "JUL 16, 2026" or "Th Jul 16, 2026 - 5:30pm CT"
                date_el = row.find(class_=re.compile("date", re.I))
                list_date_text = date_el.get_text(strip=True) if date_el else row.get_text(" ", strip=True)

                # Fetch detail page for time + venue + description
                detail_resp = safe_request(event_url, session)
                if not detail_resp:
                    continue
                detail = BeautifulSoup(detail_resp.text, "lxml")

                summary = (detail.find("h1") or link_el).get_text(strip=True)

                # Description
                body_el = detail.find(class_=re.compile("body", re.I))
                description = body_el.get_text(" ", strip=True)[:500] if body_el else ""

                # Venue from field--name-field-display-venue
                venue_el = detail.find(class_=re.compile("field-display-venue"))
                venue = venue_el.get_text(strip=True) if venue_el else "Krannert Center for the Performing Arts"
                location = f"{venue}, Krannert Center, 500 S Goodwin Ave, Urbana, IL 61801"

                # Price / tag — default to Performances; detect_free_food handles food keywords separately
                tag = "Performances"

                # Date + time from detail event-date: "Th Jul 16, 2026 - 5:30pm CT"
                event_date_el = detail.find(class_=re.compile("event-date"))
                event_date_text = event_date_el.get_text(strip=True) if event_date_el else list_date_text

                # Parse "Th Jul 16, 2026 - 5:30pm CT" or "JUL 16, 2026"
                date_match = re.search(
                    r"(?:\w{2,3}\s+)?(\w+)\s+(\d{1,2}),?\s+(\d{4})",
                    event_date_text, re.IGNORECASE,
                )
                if not date_match:
                    logger.warning("KCPA: could not parse date from %r", event_date_text)
                    continue

                month_str, day_str, year_str = date_match.groups()
                month_num = parse_month_to_number(month_str)
                day, year = int(day_str), int(year_str)

                t = parse_12h_time(event_date_text)
                h, m = t if t else (19, 0)  # default 7 PM
                start_dt = datetime(year, month_num, day, h, m, tzinfo=TZ)

                end_dt = start_dt + timedelta(hours=2)

                event_info = {
                    "summary": summary,
                    "description": description,
                    "location": location,
                    "tag": tag,
                    "htmlLink": event_url,
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat(),
                }
                event_info = detect_free_food(event_info)
                if validate_event(event_info):
                    events[local_count] = event_info
                    local_count += 1

            except Exception as e:
                logger.error("KCPA: error parsing event row: %s", e)
                continue

    except Exception as e:
        print(f"   ❌ Error in scrape_kcpa: {e}")

    print(f"   ✅ KCPA: {local_count} events scraped")
    return events


def scrape_kam() -> Dict[str, Any]:
    """Scrape Krannert Art Museum events.

    List page: https://kam.illinois.edu/exhibitions-events/events
    Structure: <div class="views-row"> contains title link + date range.
    KAM events are exhibitions/programs, not single-time events,
    so we use the exhibition start date as start and end date as end.
    """
    events: Dict[int, Any] = {}
    local_count = 0
    session = create_robust_session()
    TZ = ZoneInfo("America/Chicago")

    print("\n🔍 Scraping Krannert Art Museum...")
    try:
        response = safe_request(KAM_EVENTS_LINK, session)
        if not response:
            print("   ❌ Failed to fetch KAM events page")
            return events

        soup = BeautifulSoup(response.text, "lxml")
        rows = soup.find_all(class_="views-row")
        print(f"   Found {len(rows)} KAM event rows")

        for row in rows:
            try:
                link_el = row.find("a")
                if not link_el:
                    continue
                href = link_el.get("href", "")
                event_url = href if href.startswith("http") else "https://kam.illinois.edu" + href

                # Title is in views-field-title span; fall back to link text stripped of date prefix
                title_el = row.find(class_=re.compile("views-field-title"))
                if title_el:
                    summary = title_el.get_text(strip=True)
                else:
                    # Strip leading date pattern "Mon DD, HH am–..." from link text
                    raw = link_el.get_text(strip=True)
                    summary = re.sub(r"^\w+\s+\d+,\s*[\d:]+\s*(?:am|pm)[–\-].*?(?:pm|am)\s*", "", raw, flags=re.IGNORECASE).strip() or raw

                # Row text: "Jun 23, 10 am–Jul 2, 5 pm Title"
                row_text = row.get_text(" ", strip=True)

                # Parse first date from range: "Jun 23, 10 am" or "Jun 23"
                date_match = re.search(
                    r"(\w+)\s+(\d{1,2})(?:,\s*\d{1,2}(?::\d{2})?\s*(?:am|pm))?",
                    row_text, re.IGNORECASE,
                )
                end_date_match = re.search(
                    r"[–\-]\s*(\w+)\s+(\d{1,2})(?:,\s*\d{1,2}(?::\d{2})?\s*(?:am|pm))?",
                    row_text, re.IGNORECASE,
                )

                if not date_match:
                    continue

                now = datetime.now(tz=TZ)
                start_month = parse_month_to_number(date_match.group(1))
                start_day = int(date_match.group(2))
                # Guess year: if month < current month, it's next year
                start_year = now.year if start_month >= now.month else now.year + 1
                start_dt = datetime(start_year, start_month, start_day, 10, 0, tzinfo=TZ)

                if end_date_match:
                    end_month = parse_month_to_number(end_date_match.group(1))
                    end_day = int(end_date_match.group(2))
                    end_year = start_year if end_month >= start_month else start_year + 1
                    end_dt = datetime(end_year, end_month, end_day, 17, 0, tzinfo=TZ)
                else:
                    end_dt = start_dt + timedelta(hours=4)

                event_info = {
                    "summary": summary,
                    "description": f"Exhibition/program at Krannert Art Museum. See {event_url} for details.",
                    "location": "Krannert Art Museum, 500 E Peabody Dr, Champaign, IL 61820",
                    "tag": "Arts",
                    "htmlLink": event_url,
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat(),
                }
                event_info = detect_free_food(event_info)
                if validate_event(event_info):
                    events[local_count] = event_info
                    local_count += 1

            except Exception as e:
                logger.error("KAM: error parsing event row: %s", e)
                continue

    except Exception as e:
        print(f"   ❌ Error in scrape_kam: {e}")

    print(f"   ✅ KAM: {local_count} events scraped")
    return events


def scrape_music() -> Dict[str, Any]:
    """Scrape School of Music events.

    List page: https://music.illinois.edu/events
    Structure: <div class="event-card-content ..."> contains month/day spans,
    a date string, a time string, and a title link.
    """
    events: Dict[int, Any] = {}
    local_count = 0
    session = create_robust_session()
    TZ = ZoneInfo("America/Chicago")

    print("\n🔍 Scraping School of Music events...")
    try:
        response = safe_request(MUSIC_EVENTS_LINK, session)
        if not response:
            print("   ❌ Failed to fetch Music events page")
            return events

        soup = BeautifulSoup(response.text, "lxml")
        all_cards = soup.find_all(class_=re.compile("event-card"))
        # Only top-level cards (no ancestor event-card) to avoid duplicates
        cards = [c for c in all_cards if not c.find_parent(class_=re.compile("event-card"))]
        print(f"   Found {len(cards)} event cards")

        seen_hrefs: set = set()
        for card in cards:
            try:
                link_el = card.find("a", class_=re.compile("linked-title"))
                if not link_el:
                    continue
                href = link_el.get("href", "")
                if not href or href in seen_hrefs:
                    continue
                seen_hrefs.add(href)
                event_url = href if href.startswith("http") else "https://music.illinois.edu" + href

                # Title — strip the SVG icon text
                summary = link_el.find("span", class_="linked-title__link-icon")
                if summary:
                    summary.decompose()
                summary = link_el.get_text(strip=True)

                # Date: <div class="event-card-content__date ...">July 5, 2026</div>
                date_el = card.find(class_=re.compile("event-card-content__date"))
                date_text = date_el.get_text(strip=True) if date_el else ""

                # Time: <div class="event-card-content__time ...">Sunday, 5:30 PM - 7:00 PM</div>
                time_el = card.find(class_=re.compile("event-card-content__time"))
                time_text = time_el.get_text(" ", strip=True) if time_el else ""

                if not date_text:
                    continue

                # Parse date "July 5, 2026"
                try:
                    date_obj = datetime.strptime(date_text, "%B %d, %Y")
                except ValueError:
                    try:
                        date_obj = datetime.strptime(date_text, "%B %d %Y")
                    except ValueError:
                        logger.warning("Music: could not parse date %r", date_text)
                        continue

                y, mo, d = date_obj.year, date_obj.month, date_obj.day

                # Parse time range "Sunday, 5:30 PM - 7:00 PM" → strip day-of-week first
                time_text = re.sub(r"^\w+,\s*", "", time_text)
                rng = parse_12h_range(time_text)
                single = parse_12h_time(time_text)

                if rng:
                    (sh, sm), (eh, em) = rng
                    start_dt = datetime(y, mo, d, sh, sm, tzinfo=TZ)
                    end_dt   = datetime(y, mo, d, eh, em, tzinfo=TZ)
                elif single:
                    start_dt = datetime(y, mo, d, single[0], single[1], tzinfo=TZ)
                    end_dt   = start_dt + timedelta(hours=2)
                else:
                    start_dt = datetime(y, mo, d, 19, 0, tzinfo=TZ)
                    end_dt   = start_dt + timedelta(hours=2)

                is_free = bool(card.find(class_=re.compile("is-free")))
                tag = "Free Performances" if is_free else "Performances"

                event_info = {
                    "summary": summary,
                    "description": f"School of Music event. See {event_url} for details.",
                    "location": "University of Illinois School of Music, 1114 W Nevada St, Urbana, IL 61801",
                    "tag": tag,
                    "htmlLink": event_url,
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat(),
                }
                event_info = detect_free_food(event_info)
                if validate_event(event_info):
                    events[local_count] = event_info
                    local_count += 1

            except Exception as e:
                logger.error("Music: error parsing card: %s", e)
                continue

    except Exception as e:
        print(f"   ❌ Error in scrape_music: {e}")

    print(f"   ✅ Music: {local_count} events scraped")
    return events


def scrape_spurlock() -> Dict[str, Any]:
    """Scrape Spurlock Museum of World Cultures events.

    List page: https://spurlock.illinois.edu/events
    Structure: <div class="card"> with nested .month/.day/.year spans and
    an .title anchor; time in plain text "Event Time: HH:MM pm–HH:MM pm".
    """
    events: Dict[int, Any] = {}
    local_count = 0
    session = create_robust_session()
    TZ = ZoneInfo("America/Chicago")

    print("\n🔍 Scraping Spurlock Museum events...")
    try:
        response = safe_request(SPURLOCK_EVENTS_LINK, session)
        if not response:
            print("   ❌ Failed to fetch Spurlock events page")
            return events

        soup = BeautifulSoup(response.text, "lxml")
        # Top-level .card divs that contain a date-plaque (not nested inside another .card)
        all_cards = soup.find_all("div", class_="card")
        cards = [c for c in all_cards if c.find(class_="month") and not c.find_parent("div", class_="card")]
        print(f"   Found {len(cards)} event cards")

        seen_hrefs: set = set()
        for card in cards:
            try:
                # Date from .month / .day / .year spans
                month_el = card.find(class_="month")
                day_el   = card.find(class_="day")
                year_el  = card.find(class_="year")
                if not (month_el and day_el and year_el):
                    continue

                month_str = month_el.get_text(strip=True)   # "JUN"
                day_str   = day_el.get_text(strip=True)     # "28"
                year_str  = year_el.get_text(strip=True)    # "2026"
                month_num = parse_month_to_number(month_str)
                day, year = int(day_str), int(year_str)

                # Title link
                title_el = card.find(class_="title")
                link_el  = title_el.find("a") if title_el else card.find("a")
                if not link_el:
                    continue
                href = link_el.get("href", "")
                if href in seen_hrefs:
                    continue
                seen_hrefs.add(href)
                event_url = href if href.startswith("http") else "https://spurlock.illinois.edu/" + href.lstrip("/")
                summary   = link_el.get_text(strip=True)

                # Time from card text: "Event Time: 12:00 pm (CDT)–3:00 pm (CDT)"
                card_text = card.get_text(" ", strip=True)
                time_match = re.search(
                    r"Event Time:\s*(\d{1,2}:\d{2}\s*(?:am|pm))[^–\-]*[–\-]\s*(\d{1,2}:\d{2}\s*(?:am|pm))",
                    card_text, re.IGNORECASE,
                )

                if time_match:
                    sh, sm = parse_12h_time(time_match.group(1)) or (12, 0)
                    eh, em = parse_12h_time(time_match.group(2)) or (12, 0)
                    start_dt = datetime(year, month_num, day, sh, sm, tzinfo=TZ)
                    end_dt   = datetime(year, month_num, day, eh, em, tzinfo=TZ)
                else:
                    start_dt = datetime(year, month_num, day, 10, 0, tzinfo=TZ)
                    end_dt   = datetime(year, month_num, day, 17, 0, tzinfo=TZ)

                event_info = {
                    "summary": summary,
                    "description": f"Event at Spurlock Museum. See {event_url} for details.",
                    "location": "Spurlock Museum, 600 S Gregory St, Urbana, IL 61801",
                    "tag": "Arts",
                    "htmlLink": event_url,
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat(),
                }
                event_info = detect_free_food(event_info)
                if validate_event(event_info):
                    events[local_count] = event_info
                    local_count += 1

            except Exception as e:
                logger.error("Spurlock: error parsing card: %s", e)
                continue

    except Exception as e:
        print(f"   ❌ Error in scrape_spurlock: {e}")

    print(f"   ✅ Spurlock: {local_count} events scraped")
    return events


def scrape_parkland() -> Dict[str, Any]:
    """Scrape Parkland College events from its 25Live Publisher JSON feed.

    Feed: https://25livepub.collegenet.com/calendars/Website-Events.json
    Each event has ISO startDateTime/endDateTime (naive, America/Chicago),
    HTML-encoded title and HTML-body description.
    """
    events: Dict[int, Any] = {}
    local_count = 0
    session = create_robust_session()
    TZ = ZoneInfo("America/Chicago")

    print("\n🔍 Scraping Parkland College events...")
    try:
        response = safe_request(PARKLAND_EVENTS_JSON, session)
        if not response:
            print("   ❌ Failed to fetch Parkland feed")
            return events

        try:
            feed = response.json()
        except ValueError as e:
            logger.error("Parkland: invalid JSON: %s", e)
            return events

        print(f"   Found {len(feed)} feed entries")
        for item in feed:
            try:
                if item.get("canceled"):
                    continue

                summary = html.unescape(item.get("title", "")).strip()
                if not summary:
                    continue

                # Strip HTML from description
                raw_desc = item.get("description", "") or ""
                description = BeautifulSoup(raw_desc, "lxml").get_text(" ", strip=True)[:500]

                location = html.unescape(item.get("location", "") or "").strip()
                if not location:
                    location = "Parkland College, 2400 W Bradley Ave, Champaign, IL 61821"

                start_raw = item.get("startDateTime", "")
                end_raw   = item.get("endDateTime", "")
                if not start_raw:
                    continue

                # Parse naive ISO "2026-06-30T13:00:00" and attach tz
                start_naive = datetime.fromisoformat(start_raw)
                start_dt = start_naive.replace(tzinfo=TZ)

                if item.get("allDay"):
                    start_dt = datetime(start_naive.year, start_naive.month, start_naive.day, 0, 0, tzinfo=TZ)
                    end_dt   = datetime(start_naive.year, start_naive.month, start_naive.day, 23, 59, tzinfo=TZ)
                elif end_raw:
                    end_dt = datetime.fromisoformat(end_raw).replace(tzinfo=TZ)
                else:
                    end_dt = start_dt + timedelta(hours=1)

                web_link = item.get("permaLinkUrl") or item.get("webLink") or PARKLAND_EVENTS_JSON

                event_info = {
                    "summary": summary,
                    "description": description,
                    "location": location,
                    "tag": "Community",
                    "htmlLink": web_link,
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat(),
                }
                event_info = detect_free_food(event_info)
                if validate_event(event_info):
                    events[local_count] = event_info
                    local_count += 1

            except Exception as e:
                logger.error("Parkland: error parsing event: %s", e)
                continue

    except Exception as e:
        print(f"   ❌ Error in scrape_parkland: {e}")

    print(f"   ✅ Parkland: {local_count} events scraped")
    return events


def scrape_urbana_library() -> Dict[str, Any]:
    """Scrape Urbana Free Library events from its Communico widget.

    Widget renders <div class="amev-event"> rows with title/time/location.
    Time format: "Sun, Jun 28, 1:00pm - 2:00pm" (no year — inferred).
    """
    events: Dict[int, Any] = {}
    local_count = 0
    session = create_robust_session()
    TZ = ZoneInfo("America/Chicago")

    print("\n🔍 Scraping Urbana Free Library events...")
    try:
        response = safe_request(URBANA_LIBRARY_WIDGET, session)
        if not response:
            print("   ❌ Failed to fetch Urbana Free Library widget")
            return events

        soup = BeautifulSoup(response.text, "lxml")
        rows = soup.find_all(class_="amev-event")
        print(f"   Found {len(rows)} event rows")

        now = datetime.now(tz=TZ)
        seen_hrefs: set = set()
        for row in rows:
            try:
                title_el = row.find(class_="amev-event-title")
                link_el = title_el.find("a") if title_el else None
                if not link_el:
                    continue
                summary = link_el.get_text(strip=True)
                href = link_el.get("href", "")
                if not summary or href in seen_hrefs:
                    continue
                seen_hrefs.add(href)

                time_el = row.find(class_="amev-event-time")
                time_text = time_el.get_text(" ", strip=True) if time_el else ""

                loc_el = row.find(class_="amev-event-location")
                location = loc_el.get_text(" ", strip=True) if loc_el else "The Urbana Free Library, 210 W Green St, Urbana, IL 61801"

                # Parse "Sun, Jun 28, 1:00pm - 2:00pm" → month, day, start/end time
                date_m = re.search(r"(\w{3}),\s*(\w{3})\s+(\d{1,2})", time_text)
                if not date_m:
                    logger.warning("Urbana: could not parse date %r", time_text)
                    continue
                month_num = parse_month_to_number(date_m.group(2))
                day = int(date_m.group(3))
                # Infer year: if month is before current month, assume next year
                year = now.year if month_num >= now.month else now.year + 1

                times = re.findall(r"\d{1,2}(?::\d{2})?\s*(?:am|pm)", time_text, re.IGNORECASE)
                if times:
                    st = parse_12h_time(times[0])
                    start_dt = datetime(year, month_num, day, st[0], st[1], tzinfo=TZ) if st else datetime(year, month_num, day, 9, 0, tzinfo=TZ)
                    if len(times) > 1:
                        et = parse_12h_time(times[1])
                        end_dt = datetime(year, month_num, day, et[0], et[1], tzinfo=TZ) if et else start_dt + timedelta(hours=1)
                    else:
                        end_dt = start_dt + timedelta(hours=1)
                else:
                    start_dt = datetime(year, month_num, day, 0, 0, tzinfo=TZ)
                    end_dt   = datetime(year, month_num, day, 23, 59, tzinfo=TZ)

                event_info = {
                    "summary": summary,
                    "description": "",
                    "location": location,
                    "tag": "Community",
                    "htmlLink": href,
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat(),
                }
                event_info = detect_free_food(event_info)
                if validate_event(event_info):
                    events[local_count] = event_info
                    local_count += 1

            except Exception as e:
                logger.error("Urbana: error parsing row: %s", e)
                continue

    except Exception as e:
        print(f"   ❌ Error in scrape_urbana_library: {e}")

    print(f"   ✅ Urbana Free Library: {local_count} events scraped")
    return events


def scrape_gies() -> Dict[str, Any]:
    """Scrape Gies College of Business events.

    List page: https://giesbusiness.illinois.edu/events
    Structure: <div class="event-item"> with title link (date in URL path
    /event/YYYY/MM/DD/...) and <time class="event-time"> "6:00 PM - 7:00 PM".
    """
    events: Dict[int, Any] = {}
    local_count = 0
    session = create_robust_session()
    TZ = ZoneInfo("America/Chicago")

    print("\n🔍 Scraping Gies College of Business events...")
    try:
        response = safe_request(GIES_EVENTS_LINK, session)
        if not response:
            print("   ❌ Failed to fetch Gies events page")
            return events

        soup = BeautifulSoup(response.text, "lxml")
        rows = soup.find_all(class_="event-item")
        print(f"   Found {len(rows)} event items")

        seen_hrefs: set = set()
        for row in rows:
            try:
                link_el = row.find("a")
                if not link_el:
                    continue
                href = link_el.get("href", "")
                if not href or href in seen_hrefs:
                    continue
                seen_hrefs.add(href)
                event_url = href if href.startswith("http") else "https://giesbusiness.illinois.edu" + href
                summary = link_el.get_text(strip=True)

                # Date from URL path /event/YYYY/MM/DD/
                date_m = re.search(r"/event/(\d{4})/(\d{2})/(\d{2})/", href)
                if not date_m:
                    logger.warning("Gies: no date in URL %r", href)
                    continue
                year, month_num, day = int(date_m.group(1)), int(date_m.group(2)), int(date_m.group(3))

                time_el = row.find(class_="event-time")
                time_text = time_el.get_text(" ", strip=True) if time_el else ""
                rng = parse_12h_range(time_text)
                single = parse_12h_time(time_text)

                if rng:
                    (sh, sm), (eh, em) = rng
                    start_dt = datetime(year, month_num, day, sh, sm, tzinfo=TZ)
                    end_dt   = datetime(year, month_num, day, eh, em, tzinfo=TZ)
                elif single:
                    start_dt = datetime(year, month_num, day, single[0], single[1], tzinfo=TZ)
                    end_dt   = start_dt + timedelta(hours=1)
                else:
                    start_dt = datetime(year, month_num, day, 0, 0, tzinfo=TZ)
                    end_dt   = datetime(year, month_num, day, 23, 59, tzinfo=TZ)

                event_info = {
                    "summary": summary,
                    "description": f"Gies College of Business event. See {event_url} for details.",
                    "location": "Gies College of Business, 515 E Gregory Dr, Champaign, IL 61820",
                    "tag": "Academic",
                    "htmlLink": event_url,
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat(),
                }
                event_info = detect_free_food(event_info)
                if validate_event(event_info):
                    events[local_count] = event_info
                    local_count += 1

            except Exception as e:
                logger.error("Gies: error parsing item: %s", e)
                continue

    except Exception as e:
        print(f"   ❌ Error in scrape_gies: {e}")

    print(f"   ✅ Gies: {local_count} events scraped")
    return events


def scrape_cs() -> Dict[str, Any]:
    """Scrape Siebel School of Computing & Data Science (CS) calendar.

    List page: https://siebelschool.illinois.edu/news/calendar
    Structure: <div class="event col"> with .title link, and a fa-ul list
    whose items carry the date ("June 29, 2026"), .time ("Monday, 9:30 AM"),
    and .location ("Siebel Center Room 3102").
    """
    events: Dict[int, Any] = {}
    local_count = 0
    session = create_robust_session()
    TZ = ZoneInfo("America/Chicago")

    print("\n🔍 Scraping Siebel School (CS) calendar...")
    try:
        response = safe_request(CS_CALENDAR_LINK, session)
        if not response:
            print("   ❌ Failed to fetch CS calendar page")
            return events

        soup = BeautifulSoup(response.text, "lxml")
        rows = [e for e in soup.find_all(class_="event")
                if e.find(class_="title") and "event" in (e.get("class") or [])]
        print(f"   Found {len(rows)} event blocks")

        seen_hrefs: set = set()
        for row in rows:
            try:
                title_el = row.find(class_="title")
                link_el = title_el.find("a") if title_el else None
                if not link_el:
                    continue
                href = link_el.get("href", "")
                if href in seen_hrefs:
                    continue
                seen_hrefs.add(href)
                summary = link_el.get_text(strip=True)
                if not summary:
                    continue

                # List items: first non-time/location li holds the date
                date_text = ""
                time_text = ""
                location = "University of Illinois, Urbana, IL"
                for li in row.find_all("li"):
                    classes = li.get("class") or []
                    txt = li.get_text(" ", strip=True)
                    if "time" in classes:
                        time_text = txt
                    elif "location" in classes:
                        if txt:
                            location = txt
                    elif not date_text and re.search(r"\w+\s+\d{1,2},\s*\d{4}", txt):
                        date_text = txt

                date_m = re.search(r"(\w+)\s+(\d{1,2}),\s*(\d{4})", date_text)
                if not date_m:
                    logger.warning("CS: could not parse date %r", date_text)
                    continue
                month_num = parse_month_to_number(date_m.group(1))
                day, year = int(date_m.group(2)), int(date_m.group(3))

                t = parse_12h_time(time_text)
                if t:
                    start_dt = datetime(year, month_num, day, t[0], t[1], tzinfo=TZ)
                    end_dt   = start_dt + timedelta(hours=1)
                else:
                    start_dt = datetime(year, month_num, day, 0, 0, tzinfo=TZ)
                    end_dt   = datetime(year, month_num, day, 23, 59, tzinfo=TZ)

                event_url = href if href.startswith("http") else "https://siebelschool.illinois.edu" + href

                event_info = {
                    "summary": summary,
                    "description": "",
                    "location": location,
                    "tag": "Academic",
                    "htmlLink": event_url,
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat(),
                }
                event_info = detect_free_food(event_info)
                if validate_event(event_info):
                    events[local_count] = event_info
                    local_count += 1

            except Exception as e:
                logger.error("CS: error parsing block: %s", e)
                continue

    except Exception as e:
        print(f"   ❌ Error in scrape_cs: {e}")

    print(f"   ✅ CS: {local_count} events scraped")
    return events


def scrape_food_resources() -> Dict[str, Any]:
    """Expand the curated recurring free-food resources into upcoming dated events."""
    print("\n🔍 Generating recurring free-food resource events...")
    try:
        from food_resources import generate_food_events, ACADEMIC_TERMS
        # The term table needs a manual yearly update — warn while there is
        # still runway instead of letting academic programs silently vanish.
        last_term_end = max(end for _, end in ACADEMIC_TERMS)
        if datetime.now().date() > last_term_end - timedelta(days=60):
            warn = (f"ACADEMIC_TERMS in food_resources.py ends {last_term_end} — "
                    "add next year's UIUC term dates.")
            logger.warning(warn)
            print(f"::warning title=ACADEMIC_TERMS needs updating::{warn}")
        events = generate_food_events()
        print(f"   ✅ Food resources: {len(events)} upcoming occurrences")
        return events
    except Exception as e:
        print(f"   ❌ Error in scrape_food_resources: {e}")
        logger.exception("food_resources generation failed: %s", e)
        return {}


# Sources that should always return events; zero means a likely outage/markup break.
CRITICAL_SOURCES = {"general", "parkland", "urbana_library"}

# The published dataset — also the salvage pool: when a source breaks, its
# events from the previous run are reused so one failure never blanks it.
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "scraped_events.json")


def drop_past_events(events: Dict[Any, Dict[str, Any]], now: Optional[datetime] = None) -> Dict[Any, Dict[str, Any]]:
    """Remove events whose end time is already in the past (re-keyed sequentially)."""
    TZ = ZoneInfo("America/Chicago")
    if now is None:
        now = datetime.now(tz=TZ)

    result: Dict[int, Any] = {}
    for ev in events.values():
        end_raw = ev.get("end") or ev.get("start")
        if not end_raw:
            result[len(result)] = ev
            continue
        try:
            end_dt = datetime.fromisoformat(end_raw)
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=TZ)
        except (ValueError, TypeError):
            result[len(result)] = ev  # keep if unparseable
            continue
        if end_dt >= now:
            result[len(result)] = ev
    return result


def _normalize_title(title: str) -> str:
    """Lowercase and collapse non-alphanumerics for fuzzy title comparison."""
    return re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).strip()


def dedupe_events(events: Dict[Any, Dict[str, Any]]) -> Dict[Any, Dict[str, Any]]:
    """Drop duplicate events across sources, keyed by (normalized title, start datetime).

    The start is compared to the minute so the same event listed on several
    department calendars collapses, while two same-titled sessions at different
    times on one day (e.g. recurring tutoring) stay separate. On collision the
    entry with the richer (longer) description wins, so the more detailed source
    prevails (e.g. KCPA over a bare calendars.illinois.edu row). Events lacking a
    title or start are always kept.
    """
    chosen: Dict[Any, Dict[str, Any]] = {}
    order: List[Any] = []

    for ev in events.values():
        title = _normalize_title(ev.get("summary", ""))
        start = (ev.get("start") or "")[:16]  # YYYY-MM-DDTHH:MM
        if not title or not start:
            key = ("__unique__", len(order))
        else:
            key = (title, start)

        if key not in chosen:
            chosen[key] = ev
            order.append(key)
        else:
            existing = chosen[key]
            if len(ev.get("description") or "") > len(existing.get("description") or ""):
                chosen[key] = ev

    result: Dict[int, Any] = {}
    for key in order:
        result[len(result)] = chosen[key]
    return result


# Scrape All Function
def scrape():
    global last_scrape_stats
    combined_json_data = {}
    last_scrape_stats = {}

    for scraper_name, scraper_fn in [
        ("state_farm", scrape_state_farm),
        ("athletics",  scrape_athletics),
        ("general",    scrape_general),
        ("kcpa",       scrape_kcpa),
        ("kam",        scrape_kam),
        ("music",      scrape_music),
        ("spurlock",   scrape_spurlock),
        ("parkland",   scrape_parkland),
        ("urbana_library", scrape_urbana_library),
        ("gies",       scrape_gies),
        ("cs",         scrape_cs),
        ("food_resources", scrape_food_resources),
    ]:
        source_events = {}
        try:
            scraped = scraper_fn()
            if isinstance(scraped, dict):
                source_events = cap_events(scraped, MAX_EVENTS_PER_SOURCE)
                for event in source_events.values():
                    event["source"] = scraper_name  # enables per-source salvage
                    combined_json_data[len(combined_json_data)] = event
            else:
                logger.warning(f"{scraper_name} scraper returned non-dict payload; skipping merge.")
        except Exception as e:
            logger.exception(f"{scraper_name} scraper failed: {e}")
        finally:
            source_count = len(source_events) if isinstance(source_events, dict) else 0
            status = "success" if source_count > 0 else "empty_or_failed"
            last_scrape_stats[scraper_name] = {"events": source_count, "status": status}

    logger.info("Scrape summary by source: %s", last_scrape_stats)

    # Salvage: a source that returned nothing shouldn't blank its events —
    # reuse the ones published last run. drop_past_events ages them out, so a
    # long-dead source decays gracefully instead of vanishing overnight.
    empty_sources = {n for n, s in last_scrape_stats.items() if s["events"] == 0}
    if empty_sources:
        try:
            with open(OUTPUT_FILE) as f:
                previous = json.load(f)
        except (OSError, ValueError):
            previous = {}
        for ev in previous.values():
            src = ev.get("source")
            if src in empty_sources:
                combined_json_data[len(combined_json_data)] = ev
                stats = last_scrape_stats[src]
                stats["salvaged"] = stats.get("salvaged", 0) + 1
                stats["status"] = "salvaged_from_previous_run"
        for name in sorted(empty_sources):
            salvaged = last_scrape_stats[name].get("salvaged", 0)
            if salvaged:
                logger.warning("Source '%s' empty — reusing %d events from previous run.", name, salvaged)

    raw_count = len(combined_json_data)
    combined_json_data = drop_past_events(combined_json_data)
    after_past = len(combined_json_data)
    combined_json_data = dedupe_events(combined_json_data)
    after_dedupe = len(combined_json_data)
    logger.info(
        "Post-processing: %d merged -> %d after past-filter (-%d) -> %d after dedupe (-%d)",
        raw_count, after_past, raw_count - after_past, after_dedupe, after_past - after_dedupe,
    )
    logger.info("Total events: %s", len(combined_json_data))

    return combined_json_data
def main():
    print("Scraping events...")
    data = scrape()
    source_event_total = sum(stat.get("events", 0) for stat in last_scrape_stats.values())
    if source_event_total == 0:
        raise RuntimeError("All sources returned zero events. Failing run to surface scraper outage.")

    # Health check — fail (and skip the save) only if a critical source produced
    # nothing AND nothing could be salvaged from the previous run. With salvage,
    # publishing (fresh healthy sources + last-known-good for the broken one) is
    # strictly better than aborting.
    broken = sorted(
        name for name in CRITICAL_SOURCES
        if last_scrape_stats.get(name, {}).get("events", 0) == 0
        and not last_scrape_stats.get(name, {}).get("salvaged", 0)
    )
    if broken:
        raise RuntimeError(
            f"Critical source(s) returned zero events and nothing could be salvaged: "
            f"{', '.join(broken)}. Likely a site or markup change — failing run to "
            "surface the outage and preserve the previously committed data."
        )

    # Any source that went silent must stay visible even though the run succeeds:
    # emit GitHub Actions warning annotations on the run page. No-op locally.
    for name, stat in sorted(last_scrape_stats.items()):
        if stat.get("events", 0) == 0:
            salvaged = stat.get("salvaged", 0)
            if salvaged:
                warn = (f"Source '{name}' returned zero events — reused {salvaged} "
                        "events from the previous run. Check for a site/markup change.")
            else:
                warn = f"Source '{name}' returned zero events — possible site or markup change."
            logger.warning(warn)
            print(f"::warning title=Empty scraper source::{warn}")

    # Save to JSON file (minified for faster loading)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, separators=(',', ':'))

    print(f"Scraped {len(data)} events. Saved to {OUTPUT_FILE}")
    
if __name__ == "__main__":
    main()
