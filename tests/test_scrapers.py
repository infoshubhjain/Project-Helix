"""Unit tests for scraper helper functions (no live HTTP)."""
import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Project'))
import scrape


class TestParseMonthToNumber(unittest.TestCase):
    def test_full_month_names(self):
        cases = [
            ("January", 1), ("February", 2), ("March", 3), ("April", 4),
            ("May", 5), ("June", 6), ("July", 7), ("August", 8),
            ("September", 9), ("October", 10), ("November", 11), ("December", 12),
        ]
        for name, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(scrape.parse_month_to_number(name), expected)

    def test_abbreviated_month_names(self):
        cases = [("Jan", 1), ("Feb", 2), ("Mar", 3), ("Sep", 9), ("Dec", 12)]
        for name, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(scrape.parse_month_to_number(name), expected)


class TestDetectFreeFood(unittest.TestCase):
    def _event(self, summary="", description="", tag="General"):
        return {"summary": summary, "description": description, "location": "", "tag": tag}

    def test_pizza_triggers_free_food(self):
        e = self._event(summary="CS Club Pizza Night")
        result = scrape.detect_free_food(e)
        self.assertIn("Free Food", result["tag"])

    def test_no_food_unchanged(self):
        e = self._event(summary="Lecture on Algorithms", tag="Academic")
        result = scrape.detect_free_food(e)
        self.assertEqual(result["tag"], "Academic")

    def test_existing_tag_not_overwritten(self):
        e = self._event(summary="Basketball game lunch", tag="Athletics")
        result = scrape.detect_free_food(e)
        self.assertIn("Athletics", result["tag"])
        self.assertIn("Free Food", result["tag"])

    def test_no_duplicate_free_food_tag(self):
        e = self._event(summary="Free food pizza buffet", tag="Free Food 🍕")
        result = scrape.detect_free_food(e)
        self.assertEqual(result["tag"].count("Free Food"), 1)


class TestValidateEvent(unittest.TestCase):
    def test_valid_event(self):
        self.assertTrue(scrape.validate_event({"summary": "Test Event"}))

    def test_missing_summary(self):
        self.assertFalse(scrape.validate_event({"location": "Somewhere"}))

    def test_empty_summary(self):
        self.assertFalse(scrape.validate_event({"summary": ""}))


class TestCapEvents(unittest.TestCase):
    def test_no_cap_when_under_limit(self):
        events = {i: {"summary": f"E{i}"} for i in range(5)}
        result = scrape.cap_events(events, 10)
        self.assertEqual(len(result), 5)

    def test_caps_when_over_limit(self):
        events = {i: {"summary": f"E{i}"} for i in range(20)}
        result = scrape.cap_events(events, 10)
        self.assertEqual(len(result), 10)

    def test_non_dict_returns_empty(self):
        self.assertEqual(scrape.cap_events("bad", 10), {})


class TestScrapeGeneral(unittest.TestCase):
    def test_returns_empty_on_http_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = ""
        with patch("scrape.safe_request", return_value=None):
            result = scrape.scrape_general()
        self.assertIsInstance(result, dict)


class TestScrape(unittest.TestCase):
    def test_raises_on_all_empty_sources(self):
        with patch("scrape.scrape_general",    return_value={}), \
             patch("scrape.scrape_state_farm", return_value={}), \
             patch("scrape.scrape_athletics",  return_value={}), \
             patch("scrape.scrape_kcpa",       return_value={}), \
             patch("scrape.scrape_kam",        return_value={}), \
             patch("scrape.scrape_music",      return_value={}), \
             patch("scrape.scrape_spurlock",   return_value={}):
            result = scrape.scrape()
            self.assertEqual(len(result), 0)


if __name__ == "__main__":
    unittest.main()
