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
        self.assertIn("Daily Bread Soup Kitchen", names)  # year-round
        self.assertNotIn("Bevier Café — Everybody Eats", names)  # academic
        self.assertNotIn("Everybody Eats at ISR", names)  # academic

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
        required = {
            "summary",
            "description",
            "location",
            "tag",
            "htmlLink",
            "start",
            "end",
            "recurrence",
        }
        for e in events.values():
            self.assertTrue(required.issubset(e.keys()), f"missing fields: {e}")
            self.assertEqual(e["tag"], fr.FREE_FOOD_TAG)
            # ISO timestamps are tz-aware and ordered
            s = datetime.fromisoformat(e["start"])
            en = datetime.fromisoformat(e["end"])
            self.assertIsNotNone(s.tzinfo)
            self.assertLess(s, en)

    def test_caps_occurrences_per_resource(self):
        events = fr.generate_food_events(
            now=datetime(2026, 9, 1, 8, 0, tzinfo=TZ), max_per_resource=2
        )
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
        self.assertTrue(fr._rule_matches(rule, date(2026, 9, 4)))  # Friday
        self.assertFalse(fr._rule_matches(rule, date(2026, 9, 5)))  # Saturday

    def test_weekly_specific_days(self):
        rule = {"freq": "weekly", "days": [fr.TUE, fr.THU]}
        self.assertTrue(fr._rule_matches(rule, date(2026, 9, 1)))  # Tuesday
        self.assertFalse(fr._rule_matches(rule, date(2026, 9, 2)))  # Wednesday


class TestCalendarEntries(unittest.TestCase):
    """RRULE export feeding the "add all to Google Calendar" button."""

    TZ = ZoneInfo("America/Chicago")

    def test_rrule_shapes(self):
        self.assertEqual(fr._rrule({"freq": "daily"}), "FREQ=DAILY")
        self.assertEqual(
            fr._rrule({"freq": "weekdays"}), "FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR"
        )
        self.assertEqual(
            fr._rrule({"freq": "weekly", "days": [fr.TUE, fr.THU]}),
            "FREQ=WEEKLY;BYDAY=TU,TH",
        )
        self.assertEqual(
            fr._rrule({"freq": "nth_weekday", "weekday": fr.MON, "nths": [2, 4]}),
            "FREQ=MONTHLY;BYDAY=2MO,4MO",
        )

    def test_directory_only_contributes_nothing(self):
        """Appointment-only listings must never reach a calendar."""
        for r in fr.FOOD_RESOURCES:
            if r["active"] == "directory_only":
                self.assertEqual(fr._calendar_entries(r), [])

    def test_academic_entry_is_bounded_by_its_term(self):
        resource = next(
            r for r in fr.FOOD_RESOURCES if r["name"] == "Everybody Eats at ISR"
        )
        now = datetime(2026, 9, 1, 9, 0, tzinfo=self.TZ)  # mid Fall 2026
        entry = fr._calendar_entries(resource, now=now)[0]
        term_end = fr.ACADEMIC_TERMS[0][1].strftime("%Y%m%d")
        self.assertIn("UNTIL=" + term_end, entry["rrule"])

    def test_year_round_entry_has_no_until(self):
        resource = next(
            r for r in fr.FOOD_RESOURCES if r["name"] == "Daily Bread Soup Kitchen"
        )
        entry = fr._calendar_entries(resource)[0]
        self.assertNotIn("UNTIL", entry["rrule"])

    def test_first_occurrence_is_never_in_the_past(self):
        now = datetime.now(tz=self.TZ)
        for r in fr.FOOD_RESOURCES:
            for entry in fr._calendar_entries(r, now=now):
                self.assertGreaterEqual(
                    datetime.fromisoformat(entry["end"]), now, r["name"]
                )

    def test_academic_program_skips_to_next_term_over_break(self):
        """Asked during summer, an academic program starts when classes resume."""
        resource = next(
            r for r in fr.FOOD_RESOURCES if r["name"] == "Everybody Eats at ISR"
        )
        now = datetime(2026, 7, 1, 9, 0, tzinfo=self.TZ)  # summer break
        entry = fr._calendar_entries(resource, now=now)[0]
        start = datetime.fromisoformat(entry["start"]).date()
        self.assertTrue(fr._in_academic_term(start))

    def test_directory_exposes_calendar_for_every_dated_resource(self):
        for r in fr.food_directory():
            self.assertIn("calendar", r)
            for entry in r["calendar"]:
                self.assertTrue(entry["rrule"].startswith("RRULE:FREQ="))
                self.assertTrue(entry["start"] and entry["end"])


class TestDeriveAcademicTerms(unittest.TestCase):
    """Term dates read from the Academic Dates calendar (ID 557)."""

    # Shape and wording taken verbatim from the live feed.
    FEED = [
        {"SUMMARY": "First Day of Instruction\\, Fall Semester", "DTSTART": "20260824"},
        {"SUMMARY": "Instruction resumes", "DTSTART": "20261130"},
        {"SUMMARY": "Last Day of Instruction\\, Fall Semester", "DTSTART": "20261209"},
        {"SUMMARY": "Final Exams Begin", "DTSTART": "20261211"},
        {
            "SUMMARY": "First Day of Instruction\\, Winter Session",
            "DTSTART": "20261218",
        },
        {"SUMMARY": "Winter Session Final Exams Begin", "DTSTART": "20270115"},
        {
            "SUMMARY": "First Day of Instruction\\, Spring Semester",
            "DTSTART": "20270119",
        },
        {"SUMMARY": "Final Exams Begin", "DTSTART": "20270507"},
        {"SUMMARY": "First Day of Instruction\\, Summer Term 1", "DTSTART": "20270517"},
    ]

    def test_reproduces_the_hardcoded_terms(self):
        """The derived dates must match the hand-maintained fallback exactly."""
        self.assertEqual(
            fr.derive_academic_terms(self.FEED),
            [
                (date(2026, 8, 24), date(2026, 12, 17)),
                (date(2027, 1, 19), date(2027, 5, 13)),
            ],
        )

    def test_summer_and_winter_sessions_are_ignored(self):
        for start, _ in fr.derive_academic_terms(self.FEED):
            self.assertNotIn(start, (date(2026, 12, 18), date(2027, 5, 17)))

    def test_empty_or_garbage_feed_yields_nothing(self):
        """Caller keeps its fallback on [] — wrong dates beat stale ones."""
        self.assertEqual(fr.derive_academic_terms([]), [])
        self.assertEqual(
            fr.derive_academic_terms(
                [{"SUMMARY": "Some Lecture", "DTSTART": "20260901"}]
            ),
            [],
        )
        self.assertEqual(
            fr.derive_academic_terms(
                [
                    {
                        "SUMMARY": "First Day of Instruction, Fall Semester",
                        "DTSTART": "notadate",
                    }
                ]
            ),
            [],
        )

    def test_start_without_a_following_finals_date_is_dropped(self):
        self.assertEqual(
            fr.derive_academic_terms(
                [
                    {
                        "SUMMARY": "First Day of Instruction, Fall Semester",
                        "DTSTART": "20260824",
                    }
                ]
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
