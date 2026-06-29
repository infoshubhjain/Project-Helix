"""Tests for the recurring free-food resource generator."""
import os
import sys
import unittest
from datetime import datetime, date
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Project"))
import food_resources as fr

TZ = ZoneInfo("America/Chicago")


class TestSeasonGating(unittest.TestCase):
    def test_summer_excludes_academic_programs(self):
        # Late June is summer break — no academic-only programs should appear.
        now = datetime(2026, 6, 29, 8, 0, tzinfo=TZ)
        events = fr.generate_food_events(now=now)
        names = {e["summary"] for e in events.values()}
        self.assertIn("Daily Bread Soup Kitchen", names)        # year-round
        self.assertNotIn("Bevier Café — Everybody Eats", names)  # academic
        self.assertNotIn("Everybody Eats at ISR", names)         # academic

    def test_fall_term_includes_academic_programs(self):
        now = datetime(2026, 9, 1, 8, 0, tzinfo=TZ)
        events = fr.generate_food_events(now=now)
        names = {e["summary"] for e in events.values()}
        self.assertIn("Bevier Café — Everybody Eats", names)
        self.assertIn("Everybody Eats at ISR", names)
        self.assertIn("Daily Bread Soup Kitchen", names)

    def test_in_academic_term_helper(self):
        self.assertTrue(fr._in_academic_term(date(2026, 9, 1)))
        self.assertFalse(fr._in_academic_term(date(2026, 7, 1)))
        self.assertTrue(fr._in_academic_term(date(2027, 2, 1)))


class TestEventSchema(unittest.TestCase):
    def test_events_have_required_fields_and_tag(self):
        events = fr.generate_food_events(now=datetime(2026, 9, 1, 8, 0, tzinfo=TZ))
        self.assertGreater(len(events), 0)
        required = {"summary", "description", "location", "tag", "htmlLink", "start", "end", "recurrence"}
        for e in events.values():
            self.assertTrue(required.issubset(e.keys()), f"missing fields: {e}")
            self.assertEqual(e["tag"], fr.FREE_FOOD_TAG)
            # ISO timestamps are tz-aware and ordered
            s = datetime.fromisoformat(e["start"])
            en = datetime.fromisoformat(e["end"])
            self.assertIsNotNone(s.tzinfo)
            self.assertLess(s, en)

    def test_caps_occurrences_per_resource(self):
        events = fr.generate_food_events(now=datetime(2026, 9, 1, 8, 0, tzinfo=TZ), max_per_resource=2)
        from collections import Counter
        counts = Counter(e["summary"] for e in events.values())
        self.assertTrue(all(c <= 2 for c in counts.values()))

    def test_only_future_events(self):
        now = datetime(2026, 9, 1, 12, 0, tzinfo=TZ)
        events = fr.generate_food_events(now=now)
        for e in events.values():
            self.assertGreaterEqual(datetime.fromisoformat(e["end"]), now)


class TestRecurrenceRules(unittest.TestCase):
    def test_nth_weekday_matches_second_and_fourth_monday(self):
        rule = {"freq": "nth_weekday", "weekday": fr.MON, "nths": [2, 4]}
        # September 2026 Mondays: 7th(1st), 14th(2nd), 21st(3rd), 28th(4th)
        self.assertFalse(fr._rule_matches(rule, date(2026, 9, 7)))
        self.assertTrue(fr._rule_matches(rule, date(2026, 9, 14)))
        self.assertFalse(fr._rule_matches(rule, date(2026, 9, 21)))
        self.assertTrue(fr._rule_matches(rule, date(2026, 9, 28)))

    def test_weekdays_excludes_weekend(self):
        rule = {"freq": "weekdays"}
        self.assertTrue(fr._rule_matches(rule, date(2026, 9, 4)))   # Friday
        self.assertFalse(fr._rule_matches(rule, date(2026, 9, 5)))  # Saturday

    def test_weekly_specific_days(self):
        rule = {"freq": "weekly", "days": [fr.TUE, fr.THU]}
        self.assertTrue(fr._rule_matches(rule, date(2026, 9, 1)))   # Tuesday
        self.assertFalse(fr._rule_matches(rule, date(2026, 9, 2)))  # Wednesday


if __name__ == "__main__":
    unittest.main()
