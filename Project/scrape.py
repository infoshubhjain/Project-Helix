#-----------------------IMPORTS & VARIABLES-----------------------#
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import re
import json
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
CONFIG = {
    'max_retries': 3,
    'retry_delay': 2,  # seconds
    'request_timeout': 30,
    'max_pages_per_calendar': 10,
    'max_events_per_source': 2000,
    'user_agent': 'Mozilla/5.0 (compatible; ProjectHelix/1.0; +https://github.com/infoshubhjain/Project-Helix)',
    'rate_limit_delay': 1  # seconds between requests
}

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
]
KCPA_CALENDAR_LINK    = "https://krannertcenter.com/calendar"
KAM_EVENTS_LINK       = "https://kam.illinois.edu/exhibitions-events/events"
MUSIC_EVENTS_LINK     = "https://music.illinois.edu/events"
SPURLOCK_EVENTS_LINK  = "https://spurlock.illinois.edu/events"
STATE_FARM_CENTER_CALENDAR_LINK = "https://www.statefarmcenter.com/events/all"
ATHLETIC_TICKET_LINKS = [
    "https://fightingillini.com/sports/football/schedule",
    "https://fightingillini.com/sports/mens-basketball/schedule",
    "https://fightingillini.com/sports/womens-basketball/schedule",
    "https://fightingillini.com/sports/womens-volleyball/schedule"
]
#-----------------------HELPER FUNCTIONS-----------------------#
def create_robust_session() -> requests.Session:
    """Create a requests session with retry logic and proper headers."""
    session = requests.Session()
    
    # Configure retry strategy
    retry_kwargs = {
        "total": CONFIG['max_retries'],
        "status_forcelist": [429, 500, 502, 503, 504],
        "backoff_factor": CONFIG['retry_delay'],
        "raise_on_status": False,
    }
    try:
        # urllib3>=2 renamed method_whitelist to allowed_methods.
        retry_strategy = Retry(allowed_methods=["HEAD", "GET", "OPTIONS"], **retry_kwargs)
    except TypeError:
        retry_strategy = Retry(method_whitelist=["HEAD", "GET", "OPTIONS"], **retry_kwargs)
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Set headers
    session.headers.update({
        "User-Agent": CONFIG['user_agent'],
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
        time.sleep(CONFIG['rate_limit_delay'])
        
        response = session.request(
            method, 
            url, 
            timeout=CONFIG['request_timeout'],
            **kwargs
        )
        
        if response.status_code == 200:
            logger.debug(f"Successfully fetched: {url}")
            return response
        else:
            logger.warning(f"HTTP {response.status_code} for {url}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error(f"Timeout for {url}")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error for {url}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request exception for {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error for {url}: {e}")
        return None

def validate_event(event: Dict[str, Any]) -> bool:
    """Validate that an event has required fields."""
    required_fields = ['summary']
    
    for field in required_fields:
        if field not in event or not event[field]:
            logger.warning(f"Event missing required field '{field}': {event}")
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
    """Scrape general university calendars with enhanced error handling."""
    session = create_robust_session()
    events: Dict[int, Any] = {}
    seen_links: set = set()   # deduplicate across calendar pages
    local_count = 0
    successful_calendars = 0
    failed_calendars = 0
    
    logger.info(f"Starting to scrape {len(GENERAL_CALENDAR_LINKS)} general calendars")
    
    for i, base_calendar_link in enumerate(GENERAL_CALENDAR_LINKS):
        logger.info(f"Processing calendar {i+1}/{len(GENERAL_CALENDAR_LINKS)}: {base_calendar_link}")
        
        # Ensure we use list view and show recurring events
        current_url = f"{base_calendar_link}?listType=list&isRecurring=true"
        page_num = 0
        calendar_events = 0
        
        try:
            while current_url and page_num < CONFIG['max_pages_per_calendar']:
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
                    date_str = header.get_text(strip=True)
                    # Example date_str: "Tuesday, February 10, 2026"
                    
                    # Verify this is actually a date header
                    try:
                        # Attempt to parse date to confirm it's a date header
                        # Format: DayOfWeek, Month Day, Year
                        current_date_obj = datetime.strptime(date_str, "%A, %B %d, %Y")
                        current_date_str = current_date_obj.strftime("%Y-%m-%d")
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
                                
                                # Title and Link
                                title_div = entry.find("div", class_="title")
                                if not title_div: continue
                                link_tag = title_div.find("a")
                                if not link_tag: continue
                                
                                event_info["summary"] = link_tag.get_text(strip=True)
                                raw_href = link_tag.get("href", "")
                                if raw_href.startswith("/"):
                                    event_info["htmlLink"] = "https://calendars.illinois.edu" + raw_href
                                else:
                                    event_info["htmlLink"] = raw_href

                                # Skip duplicate events seen on another calendar page
                                if event_info["htmlLink"] in seen_links:
                                    continue
                                seen_links.add(event_info["htmlLink"])
                                    
                                # Meta: Time and Location
                                meta = entry.find("div", class_="event-meta")
                                time_str = "All Day"
                                location = "TBA"
                                if meta:
                                    time_tag = meta.find("li", class_="date")
                                    if time_tag:
                                        time_str = time_tag.get_text(strip=True)
                                    
                                    loc_tag = meta.find("li", class_="location")
                                    if loc_tag:
                                        location = loc_tag.get_text(strip=True)

                                event_info["location"] = location
                                event_info["tag"] = "General"
                                event_info["description"] = "" # List view doesn't have full description
                                
                                # Parse Time
                                start_dt = None
                                end_dt = None
                                
                                TZ = ZoneInfo("America/Chicago")
                                y, mo, d = current_date_obj.year, current_date_obj.month, current_date_obj.day

                                # Handle "All Day"
                                if "All Day" in time_str:
                                    start_dt = datetime(y, mo, d, 0, 0, tzinfo=TZ)
                                    end_dt   = datetime(y, mo, d, 23, 59, tzinfo=TZ)
                                else:
                                    time_str = time_str.replace(".", "").lower()

                                    range_match = re.search(
                                        r"(\d{1,2}):(\d{2})\s*(am|pm)?\s*-\s*(\d{1,2}):(\d{2})\s*(am|pm)",
                                        time_str,
                                    )
                                    if range_match:
                                        sh, sm, s_mer, eh, em, e_mer = range_match.groups()
                                        sh, sm, eh, em = int(sh), int(sm), int(eh), int(em)
                                        if not s_mer:
                                            s_mer = e_mer
                                        if s_mer == "pm" and sh != 12: sh += 12
                                        elif s_mer == "am" and sh == 12: sh = 0
                                        if e_mer == "pm" and eh != 12: eh += 12
                                        elif e_mer == "am" and eh == 12: eh = 0
                                        start_dt = datetime(y, mo, d, sh, sm, tzinfo=TZ)
                                        end_dt   = datetime(y, mo, d, eh, em, tzinfo=TZ)
                                    else:
                                        single_match = re.search(r"(\d{1,2}):(\d{2})\s*(am|pm)", time_str)
                                        if single_match:
                                            sh, sm, s_mer = single_match.groups()
                                            sh, sm = int(sh), int(sm)
                                            if s_mer == "pm" and sh != 12: sh += 12
                                            elif s_mer == "am" and sh == 12: sh = 0
                                            start_dt = datetime(y, mo, d, sh, sm, tzinfo=TZ)
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
                            
                            if re.search(r"\d{1,2}:\d{2}\s*(am|pm)", start_time_str, re.IGNORECASE):
                                time_match = re.search(r"(\d{1,2}):(\d{2})\s*(am|pm)", start_time_str, re.IGNORECASE)
                                hour = int(time_match.group(1))
                                minute = int(time_match.group(2))
                                meridiem = time_match.group(3).lower()
                                if meridiem == "pm" and hour != 12:
                                    hour += 12
                                elif meridiem == "am" and hour == 12:
                                    hour = 0
                                start_dt = datetime(year, parse_month_to_number(month), day, hour, minute, tzinfo=ZoneInfo("America/Chicago"))
                            else:
                                # Default to 7PM if time missing but date exists
                                start_dt = datetime(year, parse_month_to_number(month), day, 19, 0, tzinfo=ZoneInfo("America/Chicago"))
                            
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
            event_listings = soup.find_all("li", class_="sidearm-schedule-home-game")
            print(f"      Found {len(event_listings)} home games")

            title_div = soup.find("div", class_="sidearm-schedule-title")
            sport = "Sport"
            if title_div:
                h2 = title_div.find("h2")
                if h2 and h2.text:
                    # Match "2023-24 Men's Basketball Schedule" or similar
                    m = re.search(r"[\d-]+\s*(.*)\s*Schedule", h2.text)
                    if m:
                        sport = m.group(1).strip()

            for i, listing in enumerate(event_listings):
                try:
                    event_info = {"description": "", "tag": "Athletics", "htmlLink": calendar_link}
                    
                    opp_div = listing.find("div", class_="sidearm-schedule-game-opponent-name")
                    opponent = "Opponent"
                    if opp_div:
                        a_tag = opp_div.find("a")
                        if a_tag and a_tag.text:
                            opponent = a_tag.text.strip()
                        elif opp_div.text:
                            opponent = opp_div.text.strip()
                    
                    event_info["summary"] = f"{sport} Game: Illinois VS. {opponent}"

                    date_div = listing.find("div", class_="sidearm-schedule-game-opponent-date")
                    event_info["start"] = ""
                    event_info["end"] = ""
                    if date_div:
                        date_spans = date_div.find_all("span")
                        if len(date_spans) >= 1 and date_spans[0].text:
                            date_match = re.search(r"(\w+)\s+(\d+)", date_spans[0].text)
                            if date_match:
                                month = date_match.group(1)
                                day = int(date_match.group(2))
                                month_num = parse_month_to_number(month)

                                _now = datetime.now()
                                current_month = _now.month
                                current_year = _now.year
                                # Simple school year wrap-around logic
                                if current_month >= 8 and month_num < 8:
                                    year = current_year + 1
                                else:
                                    year = current_year
                                
                                start_dt = None
                                if len(date_spans) >= 2 and date_spans[1].text:
                                    time_match = re.search(r"(\d{1,2}):?(\d{2})?\s*(am|pm)", date_spans[1].text, re.IGNORECASE)
                                    if time_match:
                                        hour = int(time_match.group(1))
                                        minute = int(time_match.group(2)) if time_match.group(2) else 0
                                        meridiem = time_match.group(3).lower()
                                        if meridiem == "pm" and hour != 12:
                                            hour += 12
                                        elif meridiem == "am" and hour == 12:
                                            hour = 0
                                        start_dt = datetime(year, month_num, day, hour, minute, tzinfo=ZoneInfo("America/Chicago"))
                                
                                if start_dt is None:
                                    start_dt = datetime(year, month_num, day, 12, 0, tzinfo=ZoneInfo("America/Chicago"))
                                
                                end_dt = start_dt + timedelta(hours=3)
                                event_info["start"] = start_dt.isoformat()
                                event_info["end"] = end_dt.isoformat()

                    loc_div = listing.find("div", class_="sidearm-schedule-game-location")
                    if loc_div:
                        loc_spans = loc_div.find_all("span")
                        if len(loc_spans) >= 2:
                            event_info["location"] = f"{loc_spans[1].text.strip()}, {loc_spans[0].text.strip()}"
                        elif len(loc_spans) == 1:
                            event_info["location"] = loc_spans[0].text.strip()
                        else:
                            event_info["location"] = "Champaign, Ill."
                    else:
                        event_info["location"] = "Champaign, Ill."

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
                date_el = row.find(class_=lambda c: c and "date" in (c if isinstance(c, str) else " ".join(c)).lower())
                list_date_text = date_el.get_text(strip=True) if date_el else row.get_text(" ", strip=True)

                # Fetch detail page for time + venue + description
                detail_resp = safe_request(event_url, session)
                if not detail_resp:
                    continue
                detail = BeautifulSoup(detail_resp.text, "lxml")

                summary = (detail.find("h1") or link_el).get_text(strip=True)

                # Description
                body_el = detail.find(class_=lambda c: c and "body" in (c if isinstance(c, str) else " ".join(c)).lower())
                description = body_el.get_text(" ", strip=True)[:500] if body_el else ""

                # Venue from field--name-field-display-venue
                venue_el = detail.find(class_=lambda c: c and "field-display-venue" in " ".join(c if isinstance(c, list) else [c]))
                venue = venue_el.get_text(strip=True) if venue_el else "Krannert Center for the Performing Arts"
                location = f"{venue}, Krannert Center, 500 S Goodwin Ave, Urbana, IL 61801"

                # Price / tag — default to Performances; detect_free_food handles food keywords separately
                tag = "Performances"

                # Date + time from detail event-date: "Th Jul 16, 2026 - 5:30pm CT"
                event_date_el = detail.find(class_=lambda c: c and "event-date" in (c if isinstance(c, str) else " ".join(c)))
                event_date_text = event_date_el.get_text(strip=True) if event_date_el else list_date_text

                # Parse "Th Jul 16, 2026 - 5:30pm CT" or "JUL 16, 2026"
                date_match = re.search(
                    r"(?:\w{2,3}\s+)?(\w+)\s+(\d{1,2}),?\s+(\d{4})",
                    event_date_text, re.IGNORECASE,
                )
                time_match = re.search(r"(\d{1,2}):(\d{2})\s*(am|pm)", event_date_text, re.IGNORECASE)

                if not date_match:
                    logger.warning("KCPA: could not parse date from %r", event_date_text)
                    continue

                month_str, day_str, year_str = date_match.groups()
                month_num = parse_month_to_number(month_str)
                day, year = int(day_str), int(year_str)

                if time_match:
                    h, m, mer = time_match.groups()
                    h, m = int(h), int(m)
                    if mer.lower() == "pm" and h != 12: h += 12
                    elif mer.lower() == "am" and h == 12: h = 0
                    start_dt = datetime(year, month_num, day, h, m, tzinfo=TZ)
                else:
                    start_dt = datetime(year, month_num, day, 19, 0, tzinfo=TZ)  # default 7 PM

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
                title_el = row.find(class_=lambda c: c and "views-field-title" in " ".join(c if isinstance(c, list) else [c]))
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
        all_cards = soup.find_all(class_=lambda c: c and "event-card" in " ".join(c if isinstance(c, list) else [c]))
        # Only top-level cards (no ancestor event-card) to avoid duplicates
        cards = [c for c in all_cards if not c.find_parent(
            class_=lambda c2: c2 and "event-card" in " ".join(c2 if isinstance(c2, list) else [c2])
        )]
        print(f"   Found {len(cards)} event cards")

        seen_hrefs: set = set()
        for card in cards:
            try:
                link_el = card.find("a", class_=lambda c: c and "linked-title" in " ".join(c if isinstance(c, list) else [c]))
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
                date_el = card.find(class_=lambda c: c and "event-card-content__date" in " ".join(c if isinstance(c, list) else [c]))
                date_text = date_el.get_text(strip=True) if date_el else ""

                # Time: <div class="event-card-content__time ...">Sunday, 5:30 PM - 7:00 PM</div>
                time_el = card.find(class_=lambda c: c and "event-card-content__time" in " ".join(c if isinstance(c, list) else [c]))
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
                range_m = re.search(r"(\d{1,2}):(\d{2})\s*(AM|PM)\s*[-–]\s*(\d{1,2}):(\d{2})\s*(AM|PM)", time_text, re.IGNORECASE)
                single_m = re.search(r"(\d{1,2}):(\d{2})\s*(AM|PM)", time_text, re.IGNORECASE)

                if range_m:
                    sh, sm, s_mer, eh, em, e_mer = range_m.groups()
                    sh, sm, eh, em = int(sh), int(sm), int(eh), int(em)
                    if s_mer.upper() == "PM" and sh != 12: sh += 12
                    elif s_mer.upper() == "AM" and sh == 12: sh = 0
                    if e_mer.upper() == "PM" and eh != 12: eh += 12
                    elif e_mer.upper() == "AM" and eh == 12: eh = 0
                    start_dt = datetime(y, mo, d, sh, sm, tzinfo=TZ)
                    end_dt   = datetime(y, mo, d, eh, em, tzinfo=TZ)
                elif single_m:
                    sh, sm, s_mer = single_m.groups()
                    sh, sm = int(sh), int(sm)
                    if s_mer.upper() == "PM" and sh != 12: sh += 12
                    elif s_mer.upper() == "AM" and sh == 12: sh = 0
                    start_dt = datetime(y, mo, d, sh, sm, tzinfo=TZ)
                    end_dt   = start_dt + timedelta(hours=2)
                else:
                    start_dt = datetime(y, mo, d, 19, 0, tzinfo=TZ)
                    end_dt   = start_dt + timedelta(hours=2)

                is_free = bool(card.find(class_=lambda c: c and "is-free" in " ".join(c if isinstance(c, list) else [c])))
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

                def _parse_hm(t: str):
                    t = t.strip().lower().replace(" ", "")
                    m = re.match(r"(\d{1,2}):(\d{2})(am|pm)", t)
                    if not m:
                        return 12, 0
                    h, mn, mer = int(m.group(1)), int(m.group(2)), m.group(3)
                    if mer == "pm" and h != 12: h += 12
                    elif mer == "am" and h == 12: h = 0
                    return h, mn

                if time_match:
                    sh, sm = _parse_hm(time_match.group(1))
                    eh, em = _parse_hm(time_match.group(2))
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


# Scrape All Function
def scrape():
    global last_scrape_stats
    combined_json_data = {}
    last_scrape_stats = {}
    max_events_per_source = CONFIG.get("max_events_per_source", 2000)

    for scraper_name, scraper_fn in [
        ("state_farm", scrape_state_farm),
        ("athletics",  scrape_athletics),
        ("general",    scrape_general),
        ("kcpa",       scrape_kcpa),
        ("kam",        scrape_kam),
        ("music",      scrape_music),
        ("spurlock",   scrape_spurlock),
    ]:
        source_events = {}
        try:
            scraped = scraper_fn()
            if isinstance(scraped, dict):
                source_events = cap_events(scraped, max_events_per_source)
                for event in source_events.values():
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
    logger.info("Total merged events: %s", len(combined_json_data))

    return combined_json_data
def main():
    print("Scraping events...")
    data = scrape()
    source_event_total = sum(stat.get("events", 0) for stat in last_scrape_stats.values())
    if source_event_total == 0:
        raise RuntimeError("All sources returned zero events. Failing run to surface scraper outage.")
    
    # Save to JSON file (minified for faster loading)
    output_file = os.path.join(os.path.dirname(__file__), "scraped_events.json")
    with open(output_file, "w") as f:
        json.dump(data, f, separators=(',', ':'))
        
    print(f"Scraped {len(data)} events. Saved to {output_file}")
    
if __name__ == "__main__":
    main()
