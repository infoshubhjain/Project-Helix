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
# Tests
# ---------------------------------------------------------------------------

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
             patch.object(scrape, "scrape_kam",        return_value={0: {"summary": "KAM"}}):
            data = scrape.scrape()
        self.assertEqual(len(data), 5)
        summaries = {e["summary"] for e in data.values()}
        self.assertEqual(summaries, {"G", "SF", "A", "KC", "KAM"})

    def test_main_raises_when_all_empty(self):
        def fake_scrape():
            scrape.last_scrape_stats = {
                "state_farm": {"events": 0, "status": "empty_or_failed"},
                "athletics":  {"events": 0, "status": "empty_or_failed"},
                "general":    {"events": 0, "status": "empty_or_failed"},
                "kcpa":       {"events": 0, "status": "empty_or_failed"},
                "kam":        {"events": 0, "status": "empty_or_failed"},
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
             patch.object(scrape, "scrape_kam",        return_value={}):
            data = scrape.scrape()

        self.assertEqual(len(data), 1)
        self.assertEqual(scrape.last_scrape_stats["state_farm"]["status"], "empty_or_failed")


if __name__ == "__main__":
    unittest.main()
