#!/usr/bin/env python3
"""Smoke + unit tests for scrape.py — no live HTTP."""
import os
import sys
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Project"))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

import scrape  # noqa: E402


class MockResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code


# ---------------------------------------------------------------------------
# Helpers — HTML fixtures
# ---------------------------------------------------------------------------

GENERAL_HTML = """
<div id="ws-calendar-container">
  <h2>Tuesday, February 10, 2026</h2>
  <ul class="event-entries">
    <li class="entry">
      <div class="title"><a href="/detail/123?eventId=123">Mock Event</a></div>
      <div class="event-meta">
        <li class="date">9:00 am - 10:00 am</li>
        <li class="location">Main Hall</li>
      </div>
    </li>
  </ul>
  <h2>Wednesday, February 11, 2026</h2>
  <ul class="event-entries">
    <li class="entry">
      <div class="title"><a href="/detail/456?eventId=456">All Day Event</a></div>
      <div class="event-meta">
        <li class="date">All Day</li>
        <li class="location">Online</li>
      </div>
    </li>
  </ul>
</div>
"""

# Whole-calendar iCal feed (calendars.illinois.edu/icalGmail/<id>.ics) —
# the primary general source; HTML scraping is now only a fallback.
GENERAL_ICS = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
DTSTART;VALUE=DATE-TIME:20990712T130000
DTEND;VALUE=DATE-TIME:20990712T140000
SUMMARY:Science on Tap\\, with Friends
DESCRIPTION:A talk about beer\\nand science.
LOCATION:Riggs Beer Company
CATEGORIES:Exhibition
URL:http://calendars.illinois.edu/detail/7?eventId=1
UID:1-1@illinois.edu
END:VEVENT
BEGIN:VEVENT
DTSTART;VALUE=DATE:20990713
DTEND;VALUE=DATE:20990714
SUMMARY:All Day Exhibit
UID:2-1@illinois.edu
END:VEVENT
BEGIN:VEVENT
DTSTART;VALUE=DATE-TIME:20100101T100000
DTEND;VALUE=DATE-TIME:20100101T110000
SUMMARY:Ancient Past Event
UID:3-1@illinois.edu
END:VEVENT
END:VCALENDAR
"""

# Sidearm athletics ICS feed (fightingillini.com/calendar.ashx) — UTC times,
# "vs" = home / "at" = away, past games prefixed with a result like "[W] ".
ATHLETICS_ICS = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:vcal_1-admin.fightingillini.com
DTSTART:20990904T010000Z
DTEND:20990904T040000Z
LOCATION:Champaign\\, Ill., Gies Memorial Stadium
SUMMARY:Illini Football vs UAB
DESCRIPTION:Illini Football vs UAB\\nTV: BTN
URL:https://admin.fightingillini.com/calendar.aspx?game_id=1
END:VEVENT
BEGIN:VEVENT
UID:vcal_2-admin.fightingillini.com
DTSTART:20990926T170000Z
DTEND:20990926T200000Z
LOCATION:Columbus\\, Ohio
SUMMARY:Illini Football at Ohio State
END:VEVENT
BEGIN:VEVENT
UID:vcal_3-admin.fightingillini.com
DTSTART:20990912T183000Z
DTEND:20990912T213000Z
LOCATION:Champaign\\, Ill., Gies Memorial Stadium
SUMMARY:Illini Football vs Duke - Hall of Fame Weekend | FamILLy Day
END:VEVENT
END:VCALENDAR
"""

# calendars.illinois.edu list-view markup after the July 2026 redesign:
# non-breaking space in the date header, .entry-heading/h3 title,
# dl.entry-meta with .entry-time/.entry-location values in <dd>.
GENERAL_HTML_2026 = """
<div id="ws-calendar-container">
  <h2>Sunday, July\xa012, 2026</h2>
  <ul class="event-entries">
    <li class="entry with-summary">
      <div class="entry-pod list-entry">
        <div class="entry-heading">
          <h3><a href="/detail/7?eventId=555">Science on Tap</a></h3>
        </div>
        <dl class="entry-meta">
          <div class="entry-time">
            <dt class="place-off-screen">Time</dt>
            <dd><svg></svg>1:00 pm - 2:00 pm</dd>
          </div>
          <div class="entry-location" title="Riggs Beer Company">
            <dt class="place-off-screen">Location</dt>
            <dd><svg></svg>Riggs Beer Company</dd>
          </div>
        </dl>
      </div>
    </li>
    <li class="entry">
      <div class="entry-pod list-entry">
        <div class="entry-heading">
          <h3><a href="/detail/7?eventId=556">All Day Exhibit</a></h3>
        </div>
        <dl class="entry-meta">
          <div class="entry-time"><dt>Time</dt><dd>All Day</dd></div>
        </dl>
      </div>
    </li>
  </ul>
</div>
"""

ATHLETICS_HTML = """
<div class="sidearm-schedule-title"><h2>2025-26 Men's Basketball Schedule</h2></div>
<ul>
  <li class="sidearm-schedule-home-game">
    <div class="sidearm-schedule-game-opponent-name"><a>Purdue</a></div>
    <div class="sidearm-schedule-game-opponent-date">
      <span>Feb 14</span>
      <span>7:00 pm</span>
    </div>
    <div class="sidearm-schedule-game-location">
      <span>State Farm Center</span>
      <span>Champaign, IL</span>
    </div>
  </li>
  <li class="sidearm-schedule-home-game">
    <div class="sidearm-schedule-game-opponent-name"><a>Michigan</a></div>
    <div class="sidearm-schedule-game-opponent-date">
      <span>Mar 2</span>
      <span>2:00 pm</span>
    </div>
    <div class="sidearm-schedule-game-location">
      <span>State Farm Center</span>
      <span>Champaign, IL</span>
    </div>
  </li>
</ul>
"""

# fightingillini.com after the July 2026 Sidearm redesign: s-game-card
# components, "vs"/"at" stamp, data-test-id hooks for opponent/venue.
ATHLETICS_HTML_2026 = """
<h1 class="s-common__header-title">2026 Football Schedule</h1>
<div class="s-game-card">
  <span class="s-game-card__header__stamp">vs</span>
  <a data-test-id="s-game-card-standard__header-team-opponent-link" href="#">UAB</a>
  <p>
    <a data-test-id="s-game-card-facility-and-location__game-facility-title-link" href="#">Gies Memorial Stadium</a>
    <span data-test-id="s-game-card-facility-and-location__standard-location-details">Champaign, Ill.</span>
  </p>
  <div class="s-game-card__header__game-score-time">Sep 3 (Thu) 8 PM CT</div>
</div>
<div class="s-game-card">
  <span class="s-game-card__header__stamp">at</span>
  <a data-test-id="s-game-card-standard__header-team-opponent-link" href="#">Ohio State</a>
  <div class="s-game-card__header__game-score-time">Sep 26 (Sat) TBA</div>
</div>
<div class="s-game-card">
  <span class="s-game-card__header__stamp">vs</span>
  <a data-test-id="s-game-card-standard__header-team-opponent-link" href="#">Purdue</a>
  <div class="s-game-card__header__game-score-time">Oct 3 (Sat) TBA</div>
</div>
"""

STATEFARM_LIST_HTML = """
<html>
  <body>
    <a class="more buttons-hide" href="/events/detail/test-event-1">Event 1</a>
  </body>
</html>
"""

STATEFARM_DETAIL_HTML = """
<html>
  <body>
    <h1 class="title">Concert Night</h1>
    <div class="description_inner"><p>Amazing show.</p></div>
    <ul class="eventDetailList">
      <span class="m-date__month">October</span>
      <span class="m-date__day">15</span>
      <span class="m-date__year">2026</span>
      <li class="item sidebar_event_starts"><span>7:30 pm</span></li>
    </ul>
  </body>
</html>
"""


# ---------------------------------------------------------------------------
# Fixtures for new sources
# ---------------------------------------------------------------------------

PARKLAND_JSON = [
    {
        "title": "One World, One Sky: Big Bird&#39;s Adventure",
        "description": "<p>A <b>planetarium</b> show.</p>",
        "location": "M180: Planetarium",
        "permaLinkUrl": "https://www.parkland.edu/event/1",
        "startDateTime": "2026-06-30T13:00:00",
        "endDateTime": "2026-06-30T14:00:00",
        "allDay": False,
        "canceled": False,
    },
    {
        "title": "Cancelled Show",
        "description": "",
        "location": "X",
        "startDateTime": "2026-07-01T10:00:00",
        "endDateTime": "2026-07-01T11:00:00",
        "allDay": False,
        "canceled": True,
    },
    {
        "title": "All Day Expo",
        "description": "",
        "location": "Gallery",
        "permaLinkUrl": "https://www.parkland.edu/event/3",
        "startDateTime": "2026-07-02T00:00:00",
        "endDateTime": "2026-07-02T00:00:00",
        "allDay": True,
        "canceled": False,
    },
]

URBANA_HTML = """
<div class="amev-event-list">
  <div class="amev-event">
    <div class="amev-event-data">
      <div class="amev-event-title"><a href="https://urbanafreelibrary.libnet.info/event/1">Gardening for Butterflies</a></div>
      <div class="amev-event-time headingtext">Sun, Jun 28, 1:00pm - 2:00pm</div>
      <div class="amev-event-location headingtext"><i class="am-locations"></i>The Urbana Free Library - <i>The Lewis Auditorium</i></div>
    </div>
  </div>
  <div class="amev-event">
    <div class="amev-event-data">
      <div class="amev-event-title"><a href="https://urbanafreelibrary.libnet.info/event/2">Books and Bounces</a></div>
      <div class="amev-event-time headingtext">Tue, Jun 30, 10:15am</div>
      <div class="amev-event-location headingtext">The Urbana Free Library</div>
    </div>
  </div>
</div>
"""

GIES_HTML = """
<div class="events">
  <div class="event-item">
    <a href="https://giesbusiness.illinois.edu/event/2026/07/07/business-calendar/webinar">Gies Online MSBAi Webinar</a>
    <time class="event-time">6:00 PM - 7:00 PM</time>
  </div>
  <div class="event-item">
    <a href="https://giesbusiness.illinois.edu/event/2026/07/08/business-calendar/coffee">Global Learner Coffee Chat</a>
    <time class="event-time">9:00 AM - 10:00 AM</time>
  </div>
</div>
"""

CS_HTML = """
<div class="calendar">
  <div class="event col">
    <p class="title h5"><a href="https://calendars.illinois.edu/detail/2654?eventId=1">Final Defense of Shaowei Liu</a></p>
    <ul class="fa-ul">
      <li><span class="fa-li"></span>June 29, 2026</li>
      <li class="time"><span class="fa-li"></span>Monday<span class="hide-empty" data-value="7">, 9:30 AM</span></li>
      <li class="location hide-empty" data-value="23"><span class="fa-li"></span>Siebel Center Room 3102</li>
    </ul>
  </div>
  <div class="event col">
    <p class="title h5"><a href="https://calendars.illinois.edu/detail/2654?eventId=2">Seminar Without Location</a></p>
    <ul class="fa-ul">
      <li><span class="fa-li"></span>June 30, 2026</li>
      <li class="time"><span class="fa-li"></span>Tuesday<span class="hide-empty" data-value="7">, 12:00 PM</span></li>
      <li class="location hide-empty"><span class="fa-li"></span></li>
    </ul>
  </div>
</div>
"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestScrapeParkland(unittest.TestCase):

    def _run(self):
        resp = MagicMock()
        resp.json.return_value = PARKLAND_JSON
        resp.status_code = 200
        with patch.object(scrape, "safe_request", return_value=resp):
            return scrape.scrape_parkland()

    def test_skips_cancelled(self):
        data = self._run()
        titles = {e["summary"] for e in data.values()}
        self.assertIn("One World, One Sky: Big Bird's Adventure", titles)  # entity unescaped
        self.assertNotIn("Cancelled Show", titles)

    def test_strips_html_description(self):
        data = self._run()
        ev = [e for e in data.values() if e["summary"].startswith("One World")][0]
        self.assertEqual(ev["description"], "A planetarium show.")

    def test_iso_datetimes_have_tz(self):
        data = self._run()
        ev = [e for e in data.values() if e["summary"].startswith("One World")][0]
        self.assertIn("2026-06-30T13:00", ev["start"])
        self.assertIn("-05:00", ev["start"])

    def test_all_day_event(self):
        data = self._run()
        ev = [e for e in data.values() if e["summary"] == "All Day Expo"][0]
        self.assertIn("T00:00", ev["start"])
        self.assertIn("T23:59", ev["end"])


class TestScrapeUrbanaLibrary(unittest.TestCase):

    def _run(self):
        with patch.object(scrape, "safe_request", return_value=MockResponse(URBANA_HTML)):
            return scrape.scrape_urbana_library()

    def test_parses_events(self):
        data = self._run()
        self.assertEqual(len(data), 2)

    def test_time_range(self):
        data = self._run()
        ev = [e for e in data.values() if e["summary"] == "Gardening for Butterflies"][0]
        self.assertIn("T13:00", ev["start"])
        self.assertIn("T14:00", ev["end"])

    def test_single_time_gets_1h(self):
        data = self._run()
        ev = [e for e in data.values() if e["summary"] == "Books and Bounces"][0]
        self.assertIn("T10:15", ev["start"])
        self.assertIn("T11:15", ev["end"])


class TestScrapeGies(unittest.TestCase):

    def _run(self):
        with patch.object(scrape, "safe_request", return_value=MockResponse(GIES_HTML)):
            return scrape.scrape_gies()

    def test_date_from_url(self):
        data = self._run()
        ev = [e for e in data.values() if "MSBAi" in e["summary"]][0]
        self.assertIn("2026-07-07T18:00", ev["start"])
        self.assertIn("2026-07-07T19:00", ev["end"])

    def test_coffee_chat_gets_free_food(self):
        data = self._run()
        ev = [e for e in data.values() if "Coffee" in e["summary"]][0]
        self.assertIn("Free Food", ev["tag"])


class TestScrapeCS(unittest.TestCase):

    def _run(self):
        with patch.object(scrape, "safe_request", return_value=MockResponse(CS_HTML)):
            return scrape.scrape_cs()

    def test_parses_date_time_location(self):
        data = self._run()
        ev = [e for e in data.values() if "Shaowei" in e["summary"]][0]
        self.assertIn("2026-06-29T09:30", ev["start"])
        self.assertEqual(ev["location"], "Siebel Center Room 3102")

    def test_empty_location_falls_back(self):
        data = self._run()
        ev = [e for e in data.values() if "Without Location" in e["summary"]][0]
        self.assertTrue(ev["location"])  # non-empty default
        self.assertNotEqual(ev["location"], "")


class TestScrapeGeneralFeed(unittest.TestCase):
    """Primary path: whole-calendar ICS feed."""

    def _run(self):
        with patch.object(scrape, "GENERAL_CALENDAR_LINKS", ["https://calendars.illinois.edu/list/7"]), \
             patch.object(scrape, "safe_request", return_value=MockResponse(GENERAL_ICS)):
            return scrape.scrape_general()

    def test_timed_event_with_escapes(self):
        data = self._run()
        ev = [e for e in data.values() if "Science on Tap" in e["summary"]][0]
        self.assertEqual(ev["summary"], "Science on Tap, with Friends")  # \\, unescaped
        self.assertIn("2099-07-12T13:00", ev["start"])
        self.assertIn("T14:00", ev["end"])
        self.assertEqual(ev["location"], "Riggs Beer Company")
        self.assertIn("beer and science", ev["description"])            # \\n → space
        self.assertTrue(ev["htmlLink"].startswith("https://"))          # http upgraded
        self.assertEqual(ev["tag"], "Arts")                             # CATEGORIES feeds classify

    def test_all_day_event(self):
        data = self._run()
        ev = [e for e in data.values() if e["summary"] == "All Day Exhibit"][0]
        self.assertIn("T00:00", ev["start"])
        self.assertIn("T23:59", ev["end"])

    def test_ancient_past_events_skipped(self):
        data = self._run()
        self.assertFalse(any("Ancient" in e["summary"] for e in data.values()))

    def test_uid_dedupes_across_calendars(self):
        with patch.object(scrape, "GENERAL_CALENDAR_LINKS",
                          ["https://calendars.illinois.edu/list/7",
                           "https://calendars.illinois.edu/list/557"]), \
             patch.object(scrape, "safe_request", return_value=MockResponse(GENERAL_ICS)):
            data = scrape.scrape_general()
        # Same feed served for both calendars — UIDs collapse the duplicates.
        self.assertEqual(len(data), 2)

    def test_falls_back_to_html_when_feed_dead(self):
        def fake(url, session, **kw):
            if url.endswith(".ics"):
                return None  # feed outage
            return MockResponse(GENERAL_HTML)
        with patch.object(scrape, "GENERAL_CALENDAR_LINKS", ["https://calendars.illinois.edu/list/7"]), \
             patch.object(scrape, "safe_request", side_effect=fake):
            data = scrape.scrape_general()
        self.assertEqual(len(data), 2)  # HTML fallback parsed the list page

    def test_dead_feed_falls_back_per_calendar(self):
        # Feed OK for calendar 7, dead for 557 — 557 alone gets HTML-scraped.
        def fake(url, session, **kw):
            if url.endswith("/7.ics"):
                return MockResponse(GENERAL_ICS)
            if url.endswith(".ics"):
                return None
            return MockResponse(GENERAL_HTML)
        with patch.object(scrape, "GENERAL_CALENDAR_LINKS",
                          ["https://calendars.illinois.edu/list/7",
                           "https://calendars.illinois.edu/list/557"]), \
             patch.object(scrape, "safe_request", side_effect=fake):
            data = scrape.scrape_general()
        summaries = {e["summary"] for e in data.values()}
        self.assertIn("All Day Exhibit", summaries)  # from the working feed
        self.assertIn("Mock Event", summaries)       # from the HTML fallback


class TestScrapeAthleticsFeed(unittest.TestCase):
    """Primary path: Sidearm per-sport ICS feed."""

    def _run(self):
        with patch.object(scrape, "ATHLETICS_ICS_FEEDS",
                          [("Football", "https://fightingillini.com/calendar.ashx/calendar.ics?sport_id=2",
                            "https://fightingillini.com/sports/football/schedule")]), \
             patch.object(scrape, "safe_request", return_value=MockResponse(ATHLETICS_ICS)):
            return scrape.scrape_athletics()

    def test_home_games_only(self):
        data = self._run()
        summaries = [e["summary"] for e in data.values()]
        self.assertEqual(len(data), 2)
        self.assertFalse(any("Ohio State" in s for s in summaries))  # away skipped

    def test_utc_converted_and_suffix_stripped(self):
        data = self._run()
        uab = [e for e in data.values() if "UAB" in e["summary"]][0]
        self.assertIn("2099-09-03T20:00", uab["start"])  # 0100Z → 8 PM Chicago (CDT)
        duke = [e for e in data.values() if "Duke" in e["summary"]][0]
        self.assertEqual(duke["summary"], "Football Game: Illinois VS. Duke")  # promo suffix stripped
        self.assertEqual(uab["htmlLink"], "https://fightingillini.com/sports/football/schedule")


class TestScrapeGeneral(unittest.TestCase):

    def _run_general(self, html):
        with patch.object(scrape, "GENERAL_CALENDAR_LINKS", ["https://example.com/list"]), \
             patch.object(scrape, "safe_request", return_value=MockResponse(html)):
            return scrape.scrape_general()

    def test_schema_fields_present(self):
        data = self._run_general(GENERAL_HTML)
        self.assertGreater(len(data), 0)
        required = {"summary", "start", "end", "htmlLink", "location", "tag"}
        for ev in data.values():
            self.assertTrue(required.issubset(ev.keys()), f"Missing fields in {ev}")
            self.assertTrue(ev["summary"])

    def test_timed_event_parsed(self):
        data = self._run_general(GENERAL_HTML)
        timed = [e for e in data.values() if e["summary"] == "Mock Event"]
        self.assertEqual(len(timed), 1)
        ev = timed[0]
        self.assertIn("T09:00", ev["start"])
        self.assertIn("T10:00", ev["end"])

    def test_all_day_event_parsed(self):
        data = self._run_general(GENERAL_HTML)
        all_day = [e for e in data.values() if e["summary"] == "All Day Event"]
        self.assertEqual(len(all_day), 1)
        ev = all_day[0]
        self.assertIn("T00:00", ev["start"])
        self.assertIn("T23:59", ev["end"])

    def test_deduplication(self):
        """Same URL on two calendar pages should only appear once."""
        dup_html = GENERAL_HTML  # pretend this is returned for both pages
        calls = [0]
        def fake_safe_request(url, session, **kw):
            calls[0] += 1
            if calls[0] == 1:
                # First page — return events + a fake next-link
                return MockResponse(
                    GENERAL_HTML +
                    '<div class="next-link"><a href="/list/7?page=2">Next</a></div>'
                )
            # Second page — same events (duplicates)
            return MockResponse(GENERAL_HTML)

        with patch.object(scrape, "GENERAL_CALENDAR_LINKS", ["https://calendars.illinois.edu/list/7"]), \
             patch.object(scrape, "safe_request", side_effect=fake_safe_request):
            data = scrape.scrape_general()

        # Should not have duplicates — only 2 unique events
        self.assertEqual(len(data), 2)

    def test_empty_on_failed_request(self):
        with patch.object(scrape, "GENERAL_CALENDAR_LINKS", ["https://example.com/list"]), \
             patch.object(scrape, "safe_request", return_value=None):
            data = scrape.scrape_general()
        self.assertEqual(data, {})


class TestRecurringEventKeepsAllDates(unittest.TestCase):
    """A recurring event shares one detail URL across date headers — every
    occurrence must survive dedup (keyed by date+link, not link alone)."""

    RECURRING_HTML = """
    <div id="ws-calendar-container">
      <h2>Monday, March 02, 2026</h2>
      <ul class="event-entries">
        <li class="entry">
          <div class="title"><a href="/detail/7?eventId=42">Weekly Tutoring</a></div>
          <div class="event-meta"><li class="date">5:00 pm</li><li class="location">Grainger</li></div>
        </li>
      </ul>
      <h2>Monday, March 09, 2026</h2>
      <ul class="event-entries">
        <li class="entry">
          <div class="title"><a href="/detail/7?eventId=42">Weekly Tutoring</a></div>
          <div class="event-meta"><li class="date">5:00 pm</li><li class="location">Grainger</li></div>
        </li>
      </ul>
    </div>
    """

    def test_both_occurrences_kept(self):
        with patch.object(scrape, "GENERAL_CALENDAR_LINKS", ["https://example.com/list"]), \
             patch.object(scrape, "safe_request", return_value=MockResponse(self.RECURRING_HTML)):
            data = scrape.scrape_general()
        starts = sorted(e["start"][:10] for e in data.values())
        self.assertEqual(starts, ["2026-03-02", "2026-03-09"])


class TestScrapeGeneral2026Markup(unittest.TestCase):
    """The July 2026 site redesign: \xa0 in date headers, entry-heading/entry-meta."""

    def _run(self):
        with patch.object(scrape, "GENERAL_CALENDAR_LINKS", ["https://example.com/list"]), \
             patch.object(scrape, "safe_request", return_value=MockResponse(GENERAL_HTML_2026)):
            return scrape.scrape_general()

    def test_parses_new_markup(self):
        data = self._run()
        self.assertEqual(len(data), 2)

    def test_timed_event(self):
        data = self._run()
        ev = [e for e in data.values() if e["summary"] == "Science on Tap"][0]
        self.assertIn("2026-07-12T13:00", ev["start"])
        self.assertIn("T14:00", ev["end"])
        self.assertEqual(ev["location"], "Riggs Beer Company")

    def test_all_day_event(self):
        data = self._run()
        ev = [e for e in data.values() if e["summary"] == "All Day Exhibit"][0]
        self.assertIn("T00:00", ev["start"])
        self.assertIn("T23:59", ev["end"])


class TestScrapeAthletics(unittest.TestCase):

    def _run_athletics(self, html):
        with patch.object(scrape, "ATHLETIC_TICKET_LINKS", ["https://fightingillini.com/sports/mens-basketball/schedule"]), \
             patch.object(scrape, "safe_request", return_value=MockResponse(html)):
            return scrape.scrape_athletics()

    def test_games_parsed(self):
        data = self._run_athletics(ATHLETICS_HTML)
        self.assertEqual(len(data), 2)

    def test_game_schema(self):
        data = self._run_athletics(ATHLETICS_HTML)
        required = {"summary", "start", "end", "location", "tag", "description", "htmlLink"}
        for ev in data.values():
            self.assertTrue(required.issubset(ev.keys()))
            self.assertEqual(ev["tag"], "Athletics")
            self.assertIn("Illinois VS.", ev["summary"])

    def test_game_time_parsed(self):
        data = self._run_athletics(ATHLETICS_HTML)
        purdue = [e for e in data.values() if "Purdue" in e["summary"]][0]
        self.assertIn("T19:00", purdue["start"])

    def test_empty_on_failed_request(self):
        with patch.object(scrape, "ATHLETIC_TICKET_LINKS", ["https://fightingillini.com/sports/football/schedule"]), \
             patch.object(scrape, "safe_request", return_value=None):
            data = scrape.scrape_athletics()
        self.assertEqual(data, {})


class TestScrapeAthletics2026Markup(unittest.TestCase):
    """The July 2026 Sidearm redesign: s-game-card layout, home games say 'vs'."""

    def _run(self):
        with patch.object(scrape, "ATHLETIC_TICKET_LINKS", ["https://fightingillini.com/sports/football/schedule"]), \
             patch.object(scrape, "safe_request", return_value=MockResponse(ATHLETICS_HTML_2026)):
            return scrape.scrape_athletics()

    def test_home_games_only(self):
        data = self._run()
        summaries = [e["summary"] for e in data.values()]
        self.assertEqual(len(data), 2)
        self.assertTrue(any("UAB" in s for s in summaries))
        self.assertFalse(any("Ohio State" in s for s in summaries))  # away game skipped

    def test_time_and_venue(self):
        data = self._run()
        uab = [e for e in data.values() if "UAB" in e["summary"]][0]
        self.assertIn("T20:00", uab["start"])
        self.assertEqual(uab["location"], "Gies Memorial Stadium, Champaign, Ill.")
        self.assertIn("Football Game:", uab["summary"])

    def test_tba_time_defaults_to_noon(self):
        data = self._run()
        purdue = [e for e in data.values() if "Purdue" in e["summary"]][0]
        self.assertIn("T12:00", purdue["start"])


class TestScrapeYearWrapAround(unittest.TestCase):
    """Athletics year-assignment logic."""

    def test_august_month_gets_next_year_when_current_month_is_august(self):
        # If today is August and event month is February → next year
        with patch("scrape.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 8, 1)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            with patch.object(scrape, "ATHLETIC_TICKET_LINKS", ["https://example.com"]), \
                 patch.object(scrape, "safe_request", return_value=MockResponse(ATHLETICS_HTML)):
                data = scrape.scrape_athletics()

        # Both Feb and Mar events should be assigned year 2027
        for ev in data.values():
            self.assertIn("2027", ev["start"])

    def test_january_month_stays_current_year_when_current_month_is_january(self):
        with patch("scrape.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 1)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            with patch.object(scrape, "ATHLETIC_TICKET_LINKS", ["https://example.com"]), \
                 patch.object(scrape, "safe_request", return_value=MockResponse(ATHLETICS_HTML)):
                data = scrape.scrape_athletics()

        for ev in data.values():
            self.assertIn("2026", ev["start"])


class TestParseMonthToNumber(unittest.TestCase):
    def test_full_names(self):
        self.assertEqual(scrape.parse_month_to_number("January"), 1)
        self.assertEqual(scrape.parse_month_to_number("December"), 12)

    def test_abbreviations(self):
        self.assertEqual(scrape.parse_month_to_number("Jan"), 1)
        self.assertEqual(scrape.parse_month_to_number("Feb"), 2)
        self.assertEqual(scrape.parse_month_to_number("Sep"), 9)

    def test_unknown_returns_1(self):
        self.assertEqual(scrape.parse_month_to_number("Blarg"), 1)

    def test_case_insensitive(self):
        self.assertEqual(scrape.parse_month_to_number("MARCH"), 3)
        self.assertEqual(scrape.parse_month_to_number("oct"), 10)


class TestTimeParsing(unittest.TestCase):
    """Test time parsing edge cases in scrape_general HTML."""

    def _parse_time_event(self, time_text):
        html = f"""
        <div id="ws-calendar-container">
          <h2>Monday, March 01, 2026</h2>
          <ul class="event-entries">
            <li class="entry">
              <div class="title"><a href="/detail/1?eventId=1">Event</a></div>
              <div class="event-meta">
                <li class="date">{time_text}</li>
                <li class="location">Hall</li>
              </div>
            </li>
          </ul>
        </div>
        """
        with patch.object(scrape, "GENERAL_CALENDAR_LINKS", ["https://example.com"]), \
             patch.object(scrape, "safe_request", return_value=MockResponse(html)):
            data = scrape.scrape_general()
        return list(data.values())[0] if data else None

    def test_12pm_noon(self):
        ev = self._parse_time_event("12:00 pm - 1:00 pm")
        self.assertIsNotNone(ev)
        self.assertIn("T12:00", ev["start"])
        self.assertIn("T13:00", ev["end"])

    def test_12am_midnight(self):
        ev = self._parse_time_event("12:00 am - 1:00 am")
        self.assertIsNotNone(ev)
        self.assertIn("T00:00", ev["start"])
        self.assertIn("T01:00", ev["end"])

    def test_single_time_gets_1h_duration(self):
        ev = self._parse_time_event("3:30 pm")
        self.assertIsNotNone(ev)
        self.assertIn("T15:30", ev["start"])
        self.assertIn("T16:30", ev["end"])

    def test_range_without_start_meridiem(self):
        # "9:00 - 10:00 pm" — start inherits pm
        ev = self._parse_time_event("9:00 - 10:00 pm")
        self.assertIsNotNone(ev)
        self.assertIn("T21:00", ev["start"])
        self.assertIn("T22:00", ev["end"])


class TestScrapeIntegration(unittest.TestCase):

    def _all_empty(self):
        """Return a dict of patches that make every scraper return {}."""
        return {
            "scrape_general":    {},
            "scrape_state_farm": {},
            "scrape_athletics":  {},
            "scrape_kcpa":       {},
            "scrape_kam":        {},
        }

    def test_scrape_merges_all_sources(self):
        with patch.object(scrape, "scrape_general",    return_value={0: {"summary": "G"}}), \
             patch.object(scrape, "scrape_state_farm", return_value={0: {"summary": "SF"}}), \
             patch.object(scrape, "scrape_athletics",  return_value={0: {"summary": "A"}}), \
             patch.object(scrape, "scrape_kcpa",       return_value={0: {"summary": "KC"}}), \
             patch.object(scrape, "scrape_kam",        return_value={0: {"summary": "KAM"}}), \
             patch.object(scrape, "scrape_music",      return_value={0: {"summary": "MUS"}}), \
             patch.object(scrape, "scrape_spurlock",   return_value={0: {"summary": "SPU"}}), \
             patch.object(scrape, "scrape_parkland",   return_value={0: {"summary": "PK"}}), \
             patch.object(scrape, "scrape_urbana_library", return_value={0: {"summary": "UFL"}}), \
             patch.object(scrape, "scrape_gies",       return_value={0: {"summary": "GIES"}}), \
             patch.object(scrape, "scrape_cs",         return_value={0: {"summary": "CS"}}), \
             patch.object(scrape, "scrape_food_resources", return_value={0: {"summary": "FOOD"}}):
            data = scrape.scrape()
        self.assertEqual(len(data), 12)
        summaries = {e["summary"] for e in data.values()}
        self.assertEqual(summaries, {"G", "SF", "A", "KC", "KAM", "MUS", "SPU", "PK", "UFL", "GIES", "CS", "FOOD"})

    def test_main_raises_when_all_empty(self):
        def fake_scrape():
            scrape.last_scrape_stats = {
                "state_farm": {"events": 0, "status": "empty_or_failed"},
                "athletics":  {"events": 0, "status": "empty_or_failed"},
                "general":    {"events": 0, "status": "empty_or_failed"},
                "kcpa":       {"events": 0, "status": "empty_or_failed"},
                "kam":        {"events": 0, "status": "empty_or_failed"},
                "music":      {"events": 0, "status": "empty_or_failed"},
                "spurlock":   {"events": 0, "status": "empty_or_failed"},
                "parkland":   {"events": 0, "status": "empty_or_failed"},
                "urbana_library": {"events": 0, "status": "empty_or_failed"},
                "gies":       {"events": 0, "status": "empty_or_failed"},
                "cs":         {"events": 0, "status": "empty_or_failed"},
                "food_resources": {"events": 0, "status": "empty_or_failed"},
            }
            return {}

        with patch.object(scrape, "scrape", side_effect=fake_scrape):
            with self.assertRaises(RuntimeError):
                scrape.main()

    def test_one_failing_source_does_not_abort_others(self):
        def boom():
            raise RuntimeError("source down")

        with patch.object(scrape, "scrape_state_farm", side_effect=boom), \
             patch.object(scrape, "scrape_athletics",  return_value={}), \
             patch.object(scrape, "scrape_general",    return_value={0: {"summary": "G"}}), \
             patch.object(scrape, "scrape_kcpa",       return_value={}), \
             patch.object(scrape, "scrape_kam",        return_value={}), \
             patch.object(scrape, "scrape_music",      return_value={}), \
             patch.object(scrape, "scrape_spurlock",   return_value={}), \
             patch.object(scrape, "scrape_parkland",   return_value={}), \
             patch.object(scrape, "scrape_urbana_library", return_value={}), \
             patch.object(scrape, "scrape_gies",       return_value={}), \
             patch.object(scrape, "scrape_cs",         return_value={}), \
             patch.object(scrape, "scrape_food_resources", return_value={}):
            data = scrape.scrape()

        self.assertEqual(len(data), 1)
        self.assertEqual(scrape.last_scrape_stats["state_farm"]["status"], "empty_or_failed")


if __name__ == "__main__":
    unittest.main()
