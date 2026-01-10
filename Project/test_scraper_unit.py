import pytest
from bs4 import BeautifulSoup
from datetime import datetime
import json

from test_scrapers import parse_month_to_number, scrape_general

class DummyResponse:
    def __init__(self, text):
        self.text = text


def test_parse_month_to_number():
    assert parse_month_to_number("January") == 1
    assert parse_month_to_number("Jan") == 1
    assert parse_month_to_number("Dec") == 12


def test_scrape_general_skips_missing_event(monkeypatch):
    # Listing page contains one event link; the event page lacks the detail-content section
    listing_html = '<div class="title"><a href="/events/?eventId=123">Event</a></div>'
    event_html_missing = '<html><body><p>No details here</p></body></html>'

    def fake_get(self, url, timeout=10):
        if "list" in url:
            return DummyResponse(listing_html)
        else:
            return DummyResponse(event_html_missing)

    # Patch requests.Session.get
    monkeypatch.setattr("requests.Session.get", fake_get)

    events = scrape_general()
    assert isinstance(events, dict)
    # The event should be skipped because detail-content is missing
    assert len(events) == 0
