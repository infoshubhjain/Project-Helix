#!/usr/bin/env python3
import os
import sys
import unittest
from unittest.mock import patch


PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Project"))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

import scrape  # noqa: E402


class MockResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code


class TestScrapeSmoke(unittest.TestCase):
    def test_scrape_with_mocked_http_response_and_schema(self):
        html = """
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
        </div>
        """

        with patch.object(scrape, "GENERAL_CALENDAR_LINKS", ["https://example.com/list"]), \
             patch.object(scrape, "scrape_state_farm", return_value={}), \
             patch.object(scrape, "scrape_athletics", return_value={}), \
             patch.object(scrape, "safe_request", return_value=MockResponse(html)):
            data = scrape.scrape()

        self.assertGreater(len(data), 0)
        required_fields = {"summary", "start", "end", "htmlLink", "location", "tag"}
        for event in data.values():
            self.assertTrue(required_fields.issubset(set(event.keys())))
            self.assertTrue(event["summary"])

    def test_main_fails_when_all_sources_empty(self):
        def fake_scrape():
            scrape.last_scrape_stats = {
                "state_farm": {"events": 0, "status": "empty_or_failed"},
                "athletics": {"events": 0, "status": "empty_or_failed"},
                "general": {"events": 0, "status": "empty_or_failed"},
            }
            return {}

        with patch.object(scrape, "scrape", side_effect=fake_scrape):
            with self.assertRaises(RuntimeError):
                scrape.main()


if __name__ == "__main__":
    unittest.main()
