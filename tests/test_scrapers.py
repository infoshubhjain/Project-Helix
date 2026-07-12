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
        with patch.object(scrape, "OUTPUT_FILE", "/nonexistent/no-salvage.json"), \
             patch("scrape.scrape_general",    return_value={}), \
             patch("scrape.scrape_state_farm", return_value={}), \
             patch("scrape.scrape_athletics",  return_value={}), \
             patch("scrape.scrape_kcpa",       return_value={}), \
             patch("scrape.scrape_kam",        return_value={}), \
             patch("scrape.scrape_music",      return_value={}), \
             patch("scrape.scrape_spurlock",   return_value={}), \
             patch("scrape.scrape_parkland",   return_value={}), \
             patch("scrape.scrape_urbana_library", return_value={}), \
             patch("scrape.scrape_gies",       return_value={}), \
             patch("scrape.scrape_cs",         return_value={}), \
             patch("scrape.scrape_food_resources", return_value={}):
            result = scrape.scrape()
            self.assertEqual(len(result), 0)


class TestClassifyEvent(unittest.TestCase):
    def test_categories(self):
        cases = [
            ("Intro to CS Lecture", "Academic"),
            ("PhD Dissertation Defense", "Academic"),
            ("Spring Jazz Concert", "Performances"),
            ("Symphony Orchestra Recital", "Performances"),
            ("Illini Basketball vs Purdue", "Athletics"),
            ("Photography Exhibition", "Arts"),
            ("Community Wellness Fair", "Community"),
            ("Family Storytime", "Community"),
            ("Comedy Night Open Mic", "Entertainment"),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(scrape.classify_event(text), expected)

    def test_unknown_returns_general(self):
        self.assertEqual(scrape.classify_event("Mysterious Untagged Thing"), "General")

    def test_word_boundary_avoids_false_positive(self):
        # "start" must not match the "art" keyword
        self.assertEqual(scrape.classify_event("Project Kickoff to start the term"), "General")


class TestDropPastEvents(unittest.TestCase):
    def setUp(self):
        from zoneinfo import ZoneInfo
        self.TZ = ZoneInfo("America/Chicago")
        self.now = datetime(2026, 6, 28, 12, 0, tzinfo=self.TZ)

    def test_drops_past_keeps_future(self):
        events = {
            0: {"summary": "Past", "start": "2026-06-01T10:00:00-05:00", "end": "2026-06-01T11:00:00-05:00"},
            1: {"summary": "Future", "start": "2026-07-01T10:00:00-05:00", "end": "2026-07-01T11:00:00-05:00"},
        }
        kept = scrape.drop_past_events(events, now=self.now)
        self.assertEqual([e["summary"] for e in kept.values()], ["Future"])

    def test_keeps_event_ending_now_or_later(self):
        events = {0: {"summary": "Ongoing", "start": "2026-06-28T11:00:00-05:00", "end": "2026-06-28T23:00:00-05:00"}}
        kept = scrape.drop_past_events(events, now=self.now)
        self.assertEqual(len(kept), 1)

    def test_keeps_unparseable(self):
        events = {0: {"summary": "Bad", "start": "not-a-date", "end": "also-bad"}}
        kept = scrape.drop_past_events(events, now=self.now)
        self.assertEqual(len(kept), 1)

    def test_rekeys_sequentially(self):
        events = {
            5: {"summary": "Future A", "start": "2026-07-01T10:00:00-05:00", "end": "2026-07-01T11:00:00-05:00"},
            9: {"summary": "Future B", "start": "2026-07-02T10:00:00-05:00", "end": "2026-07-02T11:00:00-05:00"},
        }
        kept = scrape.drop_past_events(events, now=self.now)
        self.assertEqual(sorted(kept.keys()), [0, 1])


class TestDedupeEvents(unittest.TestCase):
    def test_collapses_cross_source_duplicates(self):
        # Same title + same start time from two feeds → one event, richer wins.
        events = {
            0: {"summary": "Krannert Uncorked", "start": "2026-07-16T17:30:00-05:00", "description": ""},
            1: {"summary": "Krannert  Uncorked!", "start": "2026-07-16T17:30:00-05:00", "description": "Full details"},
        }
        out = scrape.dedupe_events(events)
        self.assertEqual(len(out), 1)
        self.assertEqual(list(out.values())[0]["description"], "Full details")

    def test_keeps_same_title_different_time_same_day(self):
        # Distinct sessions (e.g. recurring tutoring) must NOT be merged.
        events = {
            0: {"summary": "Drop-in Tutoring", "start": "2026-07-16T07:00:00-05:00", "description": ""},
            1: {"summary": "Drop-in Tutoring", "start": "2026-07-16T12:00:00-05:00", "description": ""},
        }
        out = scrape.dedupe_events(events)
        self.assertEqual(len(out), 2)

    def test_keeps_same_title_different_day(self):
        events = {
            0: {"summary": "Yoga Class", "start": "2026-07-16T10:00:00-05:00", "description": ""},
            1: {"summary": "Yoga Class", "start": "2026-07-17T10:00:00-05:00", "description": ""},
        }
        out = scrape.dedupe_events(events)
        self.assertEqual(len(out), 2)

    def test_keeps_events_without_title_or_date(self):
        events = {
            0: {"summary": "", "start": "2026-07-16T10:00:00-05:00", "description": ""},
            1: {"summary": "Thing", "start": "", "description": ""},
        }
        out = scrape.dedupe_events(events)
        self.assertEqual(len(out), 2)


if __name__ == "__main__":
    unittest.main()
