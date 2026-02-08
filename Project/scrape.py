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
    "https://calendars.illinois.edu/list/598"
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
    used = []

    for calendar_link in GENERAL_CALENDAR_LINKS:
        try:
            html_text = session.get(calendar_link, timeout=20).text
        except Exception:
            continue
        soup = BeautifulSoup(html_text, "lxml")
        event_listings = soup.find_all("div", class_="title")

        for i in range(0, len(event_listings)):
            try:
                anchor = event_listings[i].find("a")
                if not anchor or not anchor.get("href"):
                    continue
                raw_href = anchor.attrs["href"].strip()
                if "eventId=" not in raw_href:
                    continue
                base = "https://calendars.illinois.edu"
                event_link = (base + "/" + raw_href.lstrip("/")) if not raw_href.startswith("http") else raw_href
                event_id = event_link.split("eventId=")[-1].split("&")[0]
                if event_id in used:
                    continue
                used.append(event_id)
            except Exception:
                continue

            event_info = {}
            try:
                html_text = session.get(event_link, timeout=20).text
            except Exception:
                continue
            soup = BeautifulSoup(html_text, "lxml")
            event = soup.find("section", class_="detail-content")
            if not event:
                continue

            name_tag = event.find("h2")
            event_name = name_tag.text.strip() if name_tag and name_tag.text else "Unknown Event Name"
            event_info["summary"] = event_name

            try:
                event_info["description"] = ""
                desc = event.find("dd", class_="ws-description")
                if desc is not None and desc.text:
                    event_info["description"] = desc.text.strip()
                event_info["htmlLink"] = event_link

                dts, dds = event.find_all("dt"), event.find_all("dd")
                if len(dts) != len(dds):
                    dts, dds = dts[:len(dds)], dds[:len(dts)]
                details = dict(zip(
                    [d.text.strip().lower().replace(" ", "_") for d in dts],
                    [d.text for d in dds]
                ))

                for key in details:
                    match key:
                        case "date":
                            date_string = details[key]
                            try:
                                month = day = year = None
                                start_hour = start_minute = end_hour = end_minute = None
                                if date_match := re.search(r"(\w+)\s+(\d{1,2}),\s+(\d{4})", date_string):
                                    month = date_match.group(1)
                                    day = int(date_match.group(2))
                                    year = int(date_match.group(3))
                                if time_range_match := re.search(r"(\d{1,2}):(\d{2})\s*(am|pm)?\s*-\s*(\d{1,2}):(\d{2})\s*(am|pm)", date_string, re.IGNORECASE):
                                    start_hour = int(time_range_match.group(1))
                                    start_minute = int(time_range_match.group(2))
                                    start_meridiem = time_range_match.group(3) or time_range_match.group(6)
                                    end_hour = int(time_range_match.group(4))
                                    end_minute = int(time_range_match.group(5))
                                    end_meridiem = time_range_match.group(6).lower()
                                    if start_meridiem:
                                        start_meridiem = start_meridiem.lower()
                                    else:
                                        start_meridiem = end_meridiem
                                    if start_meridiem == "pm" and start_hour != 12:
                                        start_hour += 12
                                    elif start_meridiem == "am" and start_hour == 12:
                                        start_hour = 0
                                    if end_meridiem == "pm" and end_hour != 12:
                                        end_hour += 12
                                    elif end_meridiem == "am" and end_hour == 12:
                                        end_hour = 0
                                elif time_match := re.search(r"(\d{1,2}):(\d{2})\s*(am|pm)", date_string, re.IGNORECASE):
                                    start_hour = int(time_match.group(1))
                                    start_minute = int(time_match.group(2))
                                    start_meridiem = time_match.group(3).lower()
                                    if start_meridiem == "pm" and start_hour != 12:
                                        start_hour += 12
                                    elif start_meridiem == "am" and start_hour == 12:
                                        start_hour = 0
                                    end_hour = (start_hour + 2) % 24
                                    end_minute = start_minute
                                else:
                                    start_hour, start_minute = 0, 0
                                    end_hour, end_minute = 23, 59
                                if None not in (month, day, year, start_hour, start_minute):
                                    start_dt = datetime(year, parse_month_to_number(month), day, start_hour, start_minute, tzinfo=ZoneInfo("America/Chicago"))
                                    event_info["start"] = start_dt.isoformat()
                                else:
                                    event_info["start"] = ""
                                if None not in (month, day, year, end_hour, end_minute):
                                    end_dt = datetime(year, parse_month_to_number(month), day, end_hour, end_minute, tzinfo=ZoneInfo("America/Chicago"))
                                    event_info["end"] = end_dt.isoformat()
                                else:
                                    event_info["end"] = ""
                            except Exception:
                                event_info["start"] = ""
                                event_info["end"] = ""
                        case "location":
                            event_info["location"] = details[key]
                        case "event_type":
                            event_info["tag"] = details[key]

                event_info.setdefault("location", "TBA")
                event_info.setdefault("tag", "General")
                event_info = {
                    key: value.strip() if isinstance(value, str) else value
                    for key, value in event_info.items()
                }
                events[event_count] = event_info
                event_count += 1
            except Exception:
                continue

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
                            year = datetime.now().year + 1 if month in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"] else datetime.now().year
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
    data = scrape()
    print(f"Scraped {len(data)} events (local run; not saved to Firebase).")
    return data

if __name__ == "__main__":
    main()