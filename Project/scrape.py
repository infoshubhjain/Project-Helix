#-----------------------IMPORTS & VARIABLES-----------------------#
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import re
import json
from playwright.sync_api import sync_playwright
import requests

try:
    import modal
except ImportError:
    modal = None
try:
    import firebase_admin
    from firebase_admin import credentials, db
except ImportError:
    firebase_admin = None

# Variables & Constants
global event_count
GENERAL_CALENDAR_LINKS = [
    "https://calendars.illinois.edu/list/7",
    "https://calendars.illinois.edu/list/557",
    "https://calendars.illinois.edu/list/594",
    "https://calendars.illinois.edu/list/4756",
    "https://calendars.illinois.edu/list/596",
    "https://calendars.illinois.edu/list/62",
    "https://calendars.illinois.edu/list/597",
    "https://calendars.illinois.edu/list/637",
    "https://calendars.illinois.edu/list/4757",
    "https://calendars.illinois.edu/list/598",
    "https://calendars.illinois.edu/list/2568",
    "https://calendars.illinois.edu/list/4063",
    "https://calendars.illinois.edu/list/5510",
    "https://calendars.illinois.edu/list/4092"
]
STATE_FARM_CENTER_CALENDAR_LINK = "https://www.statefarmcenter.com/events/all"
ATHLETIC_TICKET_LINKS = [
    "https://fightingillini.com/sports/football/schedule",
    "https://fightingillini.com/sports/mens-basketball/schedule",
    "https://fightingillini.com/sports/womens-basketball/schedule",
    "https://fightingillini.com/sports/womens-volleyball/schedule"
]
#-----------------------HELPER FUNCTIONS-----------------------#
def parse_month_to_number(month_str):
    try:
        return datetime.strptime(month_str, "%B").month
    except ValueError:
        return datetime.strptime(month_str, "%b").month
#-----------------------SCRAPERS-----------------------#
# Individual Scrapers
def scrape_general():
    global event_count
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; ProjectHelix/1.0)"})
    events = {}
    
    # We will verify up to this many pages per calendar to avoid infinite loops
    MAX_PAGES = 10 
    
    for base_calendar_link in GENERAL_CALENDAR_LINKS:
        # Ensure we use list view and show recurring events
        current_url = f"{base_calendar_link}?listType=list&isRecurring=true"
        page_num = 0
        
        while current_url and page_num < MAX_PAGES:
            try:
                print(f"Scraping {current_url}...")
                response = session.get(current_url, timeout=20)
                if response.status_code != 200:
                    print(f"Failed to fetch {current_url}: Status {response.status_code}")
                    break
                    
                soup = BeautifulSoup(response.text, "lxml")
                container = soup.find(id="ws-calendar-container")
                if not container:
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
                                
                                # Handle "All Day"
                                if "All Day" in time_str:
                                    start_dt = current_date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
                                    end_dt = current_date_obj.replace(hour=23, minute=59, second=59, microsecond=0)
                                else:
                                    # Handle time range: "9:00 am - 12:00 pm" or "9:00 am"
                                    # Normalize string
                                    original_time_str = time_str
                                    time_str = time_str.replace(".", "").lower() # 9:00 a.m. -> 9:00 am
                                    
                                    # Regex for range
                                    range_match = re.search(r"(\d{1,2}):(\d{2})\s*(am|pm)?\s*-\s*(\d{1,2}):(\d{2})\s*(am|pm)", time_str)
                                    if range_match:
                                        sh, sm, s_mer, eh, em, e_mer = range_match.groups()
                                        sh, sm, eh, em = int(sh), int(sm), int(eh), int(em)
                                        
                                        if not s_mer: s_mer = e_mer # Inherit suffix if missing
                                        
                                        if s_mer == "pm" and sh != 12: sh += 12
                                        elif s_mer == "am" and sh == 12: sh = 0
                                        
                                        if e_mer == "pm" and eh != 12: eh += 12
                                        elif e_mer == "am" and eh == 12: eh = 0
                                        
                                        start_dt = current_date_obj.replace(hour=sh, minute=sm)
                                        end_dt = current_date_obj.replace(hour=eh, minute=em)
                                        
                                    else:
                                        # Single time
                                        single_match = re.search(r"(\d{1,2}):(\d{2})\s*(am|pm)", time_str)
                                        if single_match:
                                            # ... (existing code)
                                            sh, sm, s_mer = single_match.groups()
                                            sh, sm = int(sh), int(sm)
                                            if s_mer == "pm" and sh != 12: sh += 12
                                            elif s_mer == "am" and sh == 12: sh = 0
                                            
                                            start_dt = current_date_obj.replace(hour=sh, minute=sm)
                                            # Default 1 hour duration
                                            end_dt = start_dt + timedelta(hours=1)
                                
                                if start_dt:
                                    event_info["start"] = start_dt.replace(tzinfo=ZoneInfo("America/Chicago")).isoformat()
                                else:
                                    # Fallback
                                    event_info["start"] = current_date_obj.replace(tzinfo=ZoneInfo("America/Chicago")).isoformat()
                                    
                                if end_dt:
                                    event_info["end"] = end_dt.replace(tzinfo=ZoneInfo("America/Chicago")).isoformat()
                                else:
                                    event_info["end"] = ""

                                # Add to events list
                                events[event_count] = event_info
                                event_count += 1
                                
                            except Exception as e:
                                # create print statement for error
                                # print(f"Error parsing event entry: {e}")
                                continue

                # Pagination
                next_link_div = soup.select_one("div.next-link a")
                if next_link_div and next_link_div.get("href"):
                    next_href = next_link_div.get("href")
                    if next_href.startswith("/"):
                        current_url = "https://calendars.illinois.edu" + next_href
                    else:
                         current_url = next_href # Should probably handle relative paths better if needed
                    page_num += 1
                else:
                    current_url = None # No more pages

            except Exception as e:
                print(f"Error scraping {current_url}: {e}")
                break

    return events

def scrape_state_farm():
    global event_count
    events = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
            page.goto(STATE_FARM_CENTER_CALENDAR_LINK, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=10000)
            soup = BeautifulSoup(page.content(), "lxml")
            event_listings = soup.find_all("a", class_="more buttons-hide")
            if not event_listings:
                event_listings = soup.select('a[href*="/events/detail/"]')
            seen_urls = set()
            for i in range(len(event_listings)):
                try:
                    a = event_listings[i]
                    event_link = a.get("href") or a.attrs.get("href")
                    if not event_link or event_link in seen_urls:
                        continue
                    if not event_link.startswith("http"):
                        event_link = "https://www.statefarmcenter.com" + event_link.lstrip("/")
                    seen_urls.add(event_link)
                except Exception:
                    continue

                event_info = {}
                try:
                    page.goto(event_link, wait_until="domcontentloaded", timeout=20000)
                    soup = BeautifulSoup(page.content(), "lxml")
                except Exception:
                    continue

                title_el = soup.find("h1", class_="title") or soup.find("h1")
                event_info["summary"] = title_el.text.strip() if title_el and title_el.text else "State Farm Center Event"
                event_info["description"] = ""
                desc = soup.find("div", class_="description_inner")
                if desc is not None:
                    ps = desc.find_all("p")
                    if ps:
                        event_info["description"] = " ".join(p.text for p in ps if p.text).strip()
                event_info["htmlLink"] = event_link
                event_info["location"] = "State Farm Center 1800 S 1st St, Champaign, IL 61820"
                event_info["tag"] = "Entertainment"

                try:
                    sidebar = soup.find("ul", class_="eventDetailList")
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
                                end_dt = start_dt + timedelta(hours=3)
                                event_info["start"] = start_dt.isoformat()
                                event_info["end"] = end_dt.isoformat()
                            else:
                                start_dt = datetime(year, parse_month_to_number(month), day, 19, 0, tzinfo=ZoneInfo("America/Chicago"))
                                event_info["start"] = start_dt.isoformat()
                                event_info["end"] = (start_dt + timedelta(hours=3)).isoformat()
                        else:
                            event_info["start"] = ""
                            event_info["end"] = ""
                    else:
                        event_info["start"] = ""
                        event_info["end"] = ""
                except Exception:
                    event_info["start"] = ""
                    event_info["end"] = ""

                event_info = {k: (v.strip() if isinstance(v, str) else v) for k, v in event_info.items()}
                events[event_count] = event_info
                event_count += 1

            browser.close()
    except Exception:
        pass
    return events

def scrape_athletics():
    global event_count
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; ProjectHelix/1.0)"})
    events = {}

    for calendar_link in ATHLETIC_TICKET_LINKS:
        try:
            html_text = session.get(calendar_link, timeout=20).text
        except Exception:
            continue
        soup = BeautifulSoup(html_text, "lxml")
        event_listings = soup.find_all("li", class_="sidearm-schedule-home-game")
        if not event_listings:
            continue

        title_div = soup.find("div", class_="sidearm-schedule-title")
        sport = "Sport"
        if title_div:
            h2 = title_div.find("h2")
            if h2 and h2.text:
                m = re.match(r"[\d-]+\s*(.*)\s*Schedule", h2.text)
                if m:
                    sport = m.group(1).strip()

        for i in range(len(event_listings)):
            try:
                event_info = {"description": "", "tag": "Athletics", "htmlLink": calendar_link}
                opp_div = event_listings[i].find("div", class_="sidearm-schedule-game-opponent-name")
                opponent = "Opponent"
                if opp_div:
                    a = opp_div.find("a")
                    if a and a.text:
                        opponent = a.text.strip()
                event_info["summary"] = f"{sport} Game: Illinois VS. {opponent}"

                date_div = event_listings[i].find("div", class_="sidearm-schedule-game-opponent-date")
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
                            current_month = datetime.now().month
                            current_year = datetime.now().year
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
                                    start_dt = datetime(year, parse_month_to_number(month), day, hour, minute, tzinfo=ZoneInfo("America/Chicago"))
                            if start_dt is None:
                                start_dt = datetime(year, parse_month_to_number(month), day, 12, 0, tzinfo=ZoneInfo("America/Chicago"))
                            end_dt = start_dt + timedelta(hours=3)
                            event_info["start"] = start_dt.isoformat()
                            event_info["end"] = end_dt.isoformat()

                loc_div = event_listings[i].find("div", class_="sidearm-schedule-game-location")
                if loc_div:
                    loc_spans = loc_div.find_all("span")
                    if loc_spans:
                        event_info["location"] = f"{loc_spans[1].text}, {loc_spans[0].text}" if len(loc_spans) > 1 else loc_spans[0].text
                    else:
                        event_info["location"] = "Champaign, Ill."
                else:
                    event_info["location"] = "Champaign, Ill."

                event_info = {k: (v.strip() if isinstance(v, str) else v) for k, v in event_info.items()}
                events[event_count] = event_info
                event_count += 1
            except Exception:
                continue
    return events

# Scrape All Function
def scrape():
    global event_count
    event_count = 0
    combined_json_data = {}

    json_data_state_farm = scrape_state_farm()
    combined_json_data = combined_json_data | json_data_state_farm

    json_data_athletics = scrape_athletics()
    combined_json_data = combined_json_data | json_data_athletics

    json_data_general = scrape_general()
    combined_json_data = combined_json_data | json_data_general

    return combined_json_data
#-----------------------AUTO SCRAPE (Modal)-----------------------#
if modal is not None and firebase_admin is not None:
    app = modal.App("daily-scraper")
    image = (
        modal.Image.debian_slim()
        .pip_install("Flask", "beautifulsoup4", "lxml", "playwright", "requests", "firebase_admin")
        .run_commands("playwright install --with-deps chromium")
    )

    @app.function(
        schedule=modal.Cron("0 9 * * *"),
        image=image,
        secrets=[modal.Secret.from_name("firebase-creds")],
    )
    def run_scraper():
        if not firebase_admin._apps:
            cred_dict = json.loads(os.environ["FIREBASE_CREDENTIALS"])
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred, {
                "databaseURL": os.environ.get("FIREBASE_DATABASE_URL", "https://eventflowdatabase-default-rtdb.firebaseio.com"),
            })
        ref = db.reference("scraped_events")
        scraped_data = scrape()
        ref.set(scraped_data)
        print(f"Scraper completed! Saved {len(scraped_data)} events to Firebase.")

    @app.local_entrypoint()
    def test():
        run_scraper.remote()

def main():
    if os.environ.get("SAVE_TO_FIREBASE") == "true":
        # Initialize Firebase from env var
        if firebase_admin and not firebase_admin._apps:
            cred_content = os.environ.get("FIREBASE_CREDENTIALS")
            if cred_content:
                cred_dict = json.loads(cred_content)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred, {
                    "databaseURL": os.environ.get("FIREBASE_DATABASE_URL", "https://eventflowdatabase-default-rtdb.firebaseio.com"),
                })
        
        if firebase_admin:
            ref = db.reference("scraped_events")
            print("Scraping events...")
            scraped_data = scrape()
            ref.set(scraped_data)
            print(f"Scraper completed! Saved {len(scraped_data)} events to Firebase.")
        else:
            print("Firebase Admin SDK not installed or configured.")
    else:
        # Local run
        data = scrape()
        print(f"Scraped {len(data)} events (local run; not saved to Firebase).")
        return data

if __name__ == "__main__":
    main()