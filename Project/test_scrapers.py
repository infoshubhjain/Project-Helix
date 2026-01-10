#!/usr/bin/env python3
"""
Test script to verify all scrapers are working properly
"""
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
import re
import requests
import json
import logging
from pathlib import Path
import os

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__) 

# Variables & Constants
event_count = 0

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

def parse_month_to_number(month_str):
    try:
        return datetime.strptime(month_str, "%B").month
    except ValueError:
        return datetime.strptime(month_str, "%b").month

def scrape_general():
    global event_count
    session = requests.Session()
    events = {}
    used = []

    logger.info("\n🔍 Testing scrape_general()...")
    logger.info(f"   Scraping {len(GENERAL_CALENDAR_LINKS)} calendar sources...")

    for idx, calendar_link in enumerate(GENERAL_CALENDAR_LINKS, 1):
        try:
            html_text = session.get(calendar_link, timeout=10).text
            soup = BeautifulSoup(html_text, "lxml")
            event_listings = soup.find_all("div", class_="title")
            logger.info(f"   [{idx}/{len(GENERAL_CALENDAR_LINKS)}] {calendar_link} - Found {len(event_listings)} events")

            for i in range(0, len(event_listings)):
                event_link = "https://calendars.illinois.edu/" + event_listings[i].find("a").attrs["href"]
                event_id = event_link.split("eventId=")[1]

                if event_id in used:
                    continue
                else:
                    used.append(event_id)

                event_info = {}
                html_text = session.get(event_link, timeout=10).text
                soup = BeautifulSoup(html_text, "lxml")
                event = soup.find("section", class_="detail-content")

                # Defensive checks: skip if event content isn't found
                if not event:
                    logger.warning(f"   ⚠️  Skipping event at {event_link} - missing detail-content section")
                    continue

                name_tag_elem = event.find("h2")
                if name_tag_elem and name_tag_elem.text:
                    event_name = name_tag_elem.text.strip()
                else:
                    event_name = "Unknown Event Name"
                event_info["summary"] = event_name
                event_info["description"] = ""
                desc = event.find("dd", class_="ws-description")
                if desc is not None and desc.text:
                    event_info["description"] = desc.text
                event_info["htmlLink"] = event_link

                details = dict(zip(
                            [detail.text.strip().lower().replace(" ", "_") for detail in event.find_all("dt")],
                            [detail.text for detail in event.find_all("dd")]
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
                                    start_meridiem = time_range_match.group(3)
                                    end_hour = int(time_range_match.group(4))
                                    end_minute = int(time_range_match.group(5))
                                    end_meridiem = time_range_match.group(6).lower()

                                    if not start_meridiem:
                                        start_meridiem = end_meridiem
                                    else:
                                        start_meridiem = start_meridiem.lower()

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

                event_info = {
                    key: value.strip() if isinstance(value, str) else value
                    for key, value in event_info.items()
                }

                events[event_count] = event_info
                event_count += 1

        except Exception as e:
            logger.warning(f"   ❌ Error scraping {calendar_link}: {str(e)}")

    logger.info(f"   ✅ scrape_general() completed: {len(events)} unique events")
    return events

def scrape_state_farm():
    global event_count
    events = {}

    logger.info("\n🔍 Testing scrape_state_farm()...")
    logger.info(f"   Scraping {STATE_FARM_CENTER_CALENDAR_LINK}...")

    try:
        html_text = requests.get(STATE_FARM_CENTER_CALENDAR_LINK, timeout=10).text
        soup = BeautifulSoup(html_text, "lxml")
        event_listings = soup.find_all("a", class_="more buttons-hide")
        logger.info(f"   Found {len(event_listings)} event listings")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent="Mozilla/5.0")

            for i in range(0, len(event_listings)):
                try:
                    event_link = event_listings[i].attrs["href"]
                    event_info = {}

                    page.goto(event_link, wait_until="domcontentloaded", timeout=10000)
                    soup = BeautifulSoup(page.content(), "lxml")

                    event_info["summary"] = soup.find("h1", class_="title").text
                    event_info["description"] = ""
                    desc = soup.find("div", class_="description_inner")
                    if desc != None:
                        event_info["description"] = " ".join([text.text for text in desc.find_all("p")])
                    event_info["htmlLink"] = event_link
                    event_info["location"] = "State Farm Center 1800 S 1st St, Champaign, IL 61820"
                    event_info["tag"] = "Entertainment"

                    try:
                        sidebar = soup.find("ul", class_="eventDetailList")
                        month = sidebar.find("span", class_="m-date__month").text.strip()
                        day = int(re.sub(r'\D', '', sidebar.find("span", class_="m-date__day").text.strip()))
                        year = int(re.sub(r'\D', '', sidebar.find("span", class_="m-date__year").text.strip()))
                        start_time_str = sidebar.find("li", class_="item sidebar_event_starts").find("span").text.strip()

                        if time_match := re.search(r"(\d{1,2}):(\d{2})\s*(am|pm)", start_time_str, re.IGNORECASE):
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
                            event_info["start"] = ""
                            event_info["end"] = ""
                    except Exception:
                        event_info["start"] = ""
                        event_info["end"] = ""

                    event_info = {
                        key: value.strip() if isinstance(value, str) else value
                        for key, value in event_info.items()
                    }

                    events[event_count] = event_info
                    event_count += 1

                except Exception as e:
                    logger.warning(f"   ⚠️  Error scraping event {i+1}: {str(e)}")

            browser.close()

        logger.info(f"   ✅ scrape_state_farm() completed: {len(events)} events")

    except Exception as e:
        logger.warning(f"   ❌ Error in scrape_state_farm(): {str(e)}")

    return events

def scrape_athletics():
    global event_count
    session = requests.Session()
    events = {}

    logger.info("\n🔍 Testing scrape_athletics()...")
    logger.info(f"   Scraping {len(ATHLETIC_TICKET_LINKS)} athletic schedules...")

    for idx, calendar_link in enumerate(ATHLETIC_TICKET_LINKS, 1):
        try:
            html_text = session.get(calendar_link, timeout=10).text
            soup = BeautifulSoup(html_text, "lxml")
            event_listings = soup.find_all("li", class_="sidearm-schedule-home-game")
            logger.info(f"   [{idx}/{len(ATHLETIC_TICKET_LINKS)}] {calendar_link} - Found {len(event_listings)} home games")

            if sport := re.match(r"[\d-]+ (.*) Schedule", soup.find("div", class_="sidearm-schedule-title").find("h2").text):
                sport = sport.group(1)
            else:
                sport = "Sport"

            for i in range(0, len(event_listings)):
                event_info = {}

                opponent = event_listings[i].find("div", class_="sidearm-schedule-game-opponent-name").find("a").text
                event_info["summary"] = f"{sport} Game: Illinois VS. {opponent}"
                event_info["description"] = ""
                event_info["tag"] = "Athletics"
                event_info["htmlLink"] = calendar_link

                try:
                    date_info = event_listings[i].find("div", class_="sidearm-schedule-game-opponent-date").find_all("span")

                    if date_match := re.search(r"(\w+)\s+(\d+)", date_info[0].text):
                        month = date_match.group(1)
                        day = int(date_match.group(2))

                        if month in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"]:
                            year = datetime.now().year + 1
                        else:
                            year = datetime.now().year

                        if time_match := re.search(r"(\d{1,2}):?(\d{2})?\s*(am|pm)", date_info[1].text, re.IGNORECASE):
                            hour = int(time_match.group(1))
                            minute = int(time_match.group(2)) if time_match.group(2) else 0
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
                            event_info["start"] = ""
                            event_info["end"] = ""
                    else:
                        event_info["start"] = ""
                        event_info["end"] = ""

                except Exception:
                    event_info["start"] = ""
                    event_info["end"] = ""

                location_info = event_listings[i].find("div", class_="sidearm-schedule-game-location").find_all("span")
                if len(location_info) > 1:
                    event_info["location"] = f"{location_info[1].text}, {location_info[0].text}"
                else:
                    event_info["location"] = f"{location_info[0].text}"

                event_info = {
                    key: value.strip() if isinstance(value, str) else value
                    for key, value in event_info.items()
                }

                events[event_count] = event_info
                event_count += 1

        except Exception as e:
            logger.warning(f"   ❌ Error scraping {calendar_link}: {str(e)}")

    logger.info(f"   ✅ scrape_athletics() completed: {len(events)} events")
    return events

def main():
    print("=" * 60)
    print("🚀 TESTING ALL WEB SCRAPERS")
    print("=" * 60)

    global event_count
    event_count = 0
    all_events = {}

    # Test each scraper
    state_farm_events = scrape_state_farm()
    all_events.update(state_farm_events)

    athletics_events = scrape_athletics()
    all_events.update(athletics_events)

    general_events = scrape_general()
    all_events.update(general_events)

    # Save outputs to JSON files in Project/calander/
    output_dir = Path(__file__).parent / "calander"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "state_farm_events.json").write_text(json.dumps(state_farm_events, indent=2))
    (output_dir / "athletics_events.json").write_text(json.dumps(athletics_events, indent=2))
    (output_dir / "general_events.json").write_text(json.dumps(general_events, indent=2))
    logger.info(f"   🔁 Saved outputs to {output_dir}")

    logger.info("\n" + "=" * 60)
    logger.info("📊 SUMMARY")
    logger.info("=" * 60)
    logger.info(f"State Farm Center Events: {len(state_farm_events)}")
    logger.info(f"Athletics Events: {len(athletics_events)}")
    logger.info(f"General Calendar Events: {len(general_events)}")
    logger.info(f"TOTAL EVENTS SCRAPED: {len(all_events)}")

    # Show sample events
    logger.info("\n" + "=" * 60)
    logger.info("📋 SAMPLE EVENTS (first 3)")
    logger.info("=" * 60)
    for i, (key, event) in enumerate(list(all_events.items())[:3]):
        logger.info(f"\nEvent {key}:")
        logger.info(f"  Title: {event.get('summary', 'N/A')}")
        logger.info(f"  Start: {event.get('start', 'N/A')}")
        logger.info(f"  Location: {event.get('location', 'N/A')}")
        logger.info(f"  Tag: {event.get('tag', 'N/A')}")

    logger.info("\n" + "=" * 60)

    # Fail fast in CI when strict mode is enabled
    if os.environ.get("CI_STRICT", "").lower() == "true":
        zeroed = []
        if len(state_farm_events) == 0:
            zeroed.append("state_farm")
        if len(athletics_events) == 0:
            zeroed.append("athletics")
        if len(general_events) == 0:
            zeroed.append("general")
        if zeroed:
            logger.error(f"❌ CI_STRICT detected zero events for: {', '.join(zeroed)}. Failing job.")
            raise SystemExit(2)

    logger.info("✅ ALL SCRAPERS TESTED")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
