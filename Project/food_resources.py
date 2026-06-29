"""Recurring free-food resources around UIUC (Champaign-Urbana).

These are stable, well-known meal programs, pantries, and soup kitchens — not
scraped from a live page, but expanded from a curated recurrence table into
concrete dated occurrences within a forward window. Each emitted event carries a
human-readable ``recurrence`` label so the frontend can group it under a
dedicated "Recurring" section.

Programs that only run while classes are in session ("academic") are gated to
the UIUC term dates below, so they do not show fake occurrences over summer or
winter break. Community resources run year-round.

Sources: publish.illinois.edu/foodresources, scs.illinois.edu/free-food-resources-campus-and-community,
beviercafe.illinois.edu/everybody-eats, housing.illinois.edu/dine/nutrition/everybody-eats,
and The Daily Illini reporting on cultural-house meal programs.
"""
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, List, Any

TZ = ZoneInfo("America/Chicago")
FREE_FOOD_TAG = "Free Food 🍕"

# UIUC academic terms (instruction start through end of finals). Update yearly.
ACADEMIC_TERMS = [
    (date(2026, 8, 24), date(2026, 12, 17)),  # Fall 2026
    (date(2027, 1, 19), date(2027, 5, 13)),   # Spring 2027
]

# Weekday constants (Python date.weekday(): Monday=0 .. Sunday=6)
MON, TUE, WED, THU, FRI, SAT, SUN = range(7)

# Each resource has one or more rules. Rule kinds:
#   {"freq": "daily",       "start": "HH:MM", "end": "HH:MM"}
#   {"freq": "weekdays",    "start": ..., "end": ...}              # Mon-Fri
#   {"freq": "weekly",      "days": [..], "start": ..., "end": ...}
#   {"freq": "nth_weekday", "weekday": d, "nths": [..], "start": ..., "end": ...}
FOOD_RESOURCES: List[Dict[str, Any]] = [
    # ---------------- Year-round community resources ----------------
    {
        "name": "Daily Bread Soup Kitchen",
        "location": "Daily Bread Soup Kitchen, 116 N First St, Champaign, IL 61820",
        "link": "https://publish.illinois.edu/foodresources/",
        "description": "Free hot meal open to the public, served daily.",
        "recurrence": "Daily, 10:30 AM – 12:30 PM",
        "active": "year_round",
        "rules": [{"freq": "daily", "start": "10:30", "end": "12:30"}],
    },
    {
        "name": "St. Vincent de Paul Food Pantry",
        "location": "708 W Main St, Urbana, IL 61801 (parking-lot distribution)",
        "link": "https://publish.illinois.edu/foodresources/",
        "description": "Free grocery distribution in the church parking lot.",
        "recurrence": "Tuesdays & Thursdays, 4–5 PM",
        "active": "year_round",
        "rules": [{"freq": "weekly", "days": [TUE, THU], "start": "16:00", "end": "17:00"}],
    },
    {
        "name": "Stone Creek Church Food Pantry",
        "location": "Stone Creek Church, 2502 S Race St, Urbana, IL 61801",
        "link": "https://publish.illinois.edu/foodresources/",
        "description": "Free food pantry on the 2nd and 4th Mondays of each month.",
        "recurrence": "2nd & 4th Mondays, 4–6 PM",
        "active": "year_round",
        "rules": [{"freq": "nth_weekday", "weekday": MON, "nths": [2, 4], "start": "16:00", "end": "18:00"}],
    },
    {
        "name": "Jubilee Café Community Dinner",
        "location": "Community United Church of Christ, 805 S 6th St, Champaign, IL 61820",
        "link": "https://community-ucc.org/",
        "description": "Free dinner for students and community members, hosted by CUCC.",
        "recurrence": "Mondays, 5–6:30 PM",
        "active": "year_round",
        "rules": [{"freq": "weekly", "days": [MON], "start": "17:00", "end": "18:30"}],
    },
    {
        "name": "Salvation Army Canteen Run",
        "location": "The Salvation Army, 2212 N Market St, Champaign, IL 61820 (mobile meals)",
        "link": "https://publish.illinois.edu/foodresources/",
        "description": "Mobile free-meal service in the evenings.",
        "recurrence": "Mondays–Wednesdays, 6:30–9 PM",
        "active": "year_round",
        "rules": [{"freq": "weekly", "days": [MON, TUE, WED], "start": "18:30", "end": "21:00"}],
    },
    {
        "name": "Emmanuel Memorial Sack-Lunch Ministry",
        "location": "Emmanuel Memorial Episcopal Church, 208 W University Ave, Champaign, IL 61820",
        "link": "https://publish.illinois.edu/foodresources/",
        "description": "Free sack lunches, weekday mornings while supplies last.",
        "recurrence": "Weekdays, 9–10 AM",
        "active": "year_round",
        "rules": [{"freq": "weekdays", "start": "09:00", "end": "10:00"}],
    },
    {
        "name": "UniPlace Wednesday Community Dinner",
        "location": "University Place Christian Church, 403 S Wright St, Champaign, IL 61820",
        "link": "https://publish.illinois.edu/foodresources/",
        "description": "Free community dinner for campus and community.",
        "recurrence": "Wednesdays, 5–6 PM",
        "active": "year_round",
        "rules": [{"freq": "weekly", "days": [WED], "start": "17:00", "end": "18:00"}],
    },
    {
        "name": "Wesley Evening Food Pantry",
        "location": "Wesley United Methodist Church, 1203 W Green St, Urbana, IL 61801",
        "link": "https://publish.illinois.edu/foodresources/",
        "description": "Evening food pantry; no income requirement or personal information needed.",
        "recurrence": "Thursdays, 5–7:30 PM",
        "active": "year_round",
        "rules": [{"freq": "weekly", "days": [THU], "start": "17:00", "end": "19:30"}],
    },
    {
        "name": "ARC Food Assistance & Nutrition Program",
        "location": "201 E Peabody Dr, Champaign, IL 61820",
        "link": "https://publish.illinois.edu/foodresources/",
        "description": "Free food assistance for U of I students (reduced summer hours — Tuesdays only).",
        "recurrence": "Tuesdays 1–4 PM & Saturdays 2–5 PM",
        "active": "year_round",
        "rules": [
            {"freq": "weekly", "days": [TUE], "start": "13:00", "end": "16:00"},
            {"freq": "weekly", "days": [SAT], "start": "14:00", "end": "17:00"},
        ],
    },
    {
        "name": "The Literary \"Oh SNAP!\" Free Meal",
        "location": "The Literary, downtown Champaign, IL",
        "link": "https://publish.illinois.edu/foodresources/",
        "description": "One free meal per weekday for anyone showing a SNAP card.",
        "recurrence": "Weekdays, 9 AM – 3 PM",
        "active": "year_round",
        "rules": [{"freq": "weekdays", "start": "09:00", "end": "15:00"}],
    },

    # ---------------- Academic-year campus programs ----------------
    {
        "name": "Everybody Eats at ISR",
        "location": "Illinois Street Residence Halls, 1010 W Illinois St, Urbana, IL 61801",
        "link": "https://housing.illinois.edu/dine/nutrition/everybody-eats",
        "description": "Free meals for students experiencing food insecurity; no ID required.",
        "recurrence": "Daily, 10:30 AM – 8 PM",
        "active": "academic",
        "rules": [{"freq": "daily", "start": "10:30", "end": "20:00"}],
    },
    {
        "name": "Everybody Eats at Ike (SDRP)",
        "location": "Student Dining & Residential Programs (SDRP), 57 North seating area, Urbana, IL",
        "link": "https://housing.illinois.edu/dine/nutrition/everybody-eats",
        "description": "Free meals for students experiencing food insecurity; no ID required.",
        "recurrence": "Daily, 10:30 AM – 8 PM",
        "active": "academic",
        "rules": [{"freq": "daily", "start": "10:30", "end": "20:00"}],
    },
    {
        "name": "Bevier Café — Everybody Eats",
        "location": "Bevier Hall, 2nd Floor, 905 S Goodwin Ave, Urbana, IL 61801",
        "link": "https://beviercafe.illinois.edu/everybody-eats/",
        "description": "Student-run café; take a token from the entrance jar for a free hot lunch ('pay what you can / pay it forward').",
        "recurrence": "Weekdays, 11:30 AM – 1 PM (classes in session)",
        "active": "academic",
        "rules": [{"freq": "weekdays", "start": "11:30", "end": "13:00"}],
    },
    {
        "name": "LAS Undercover Food Pantry",
        "location": "LAS Student Academic Affairs Office, 2002 Lincoln Hall, Urbana, IL",
        "link": "https://publish.illinois.edu/foodresources/",
        "description": "Discreet food pantry — ask at the front desk. Open while classes are in session.",
        "recurrence": "Weekdays, mornings & afternoons",
        "active": "academic",
        "rules": [
            {"freq": "weekly", "days": [MON, TUE, THU, FRI], "start": "08:30", "end": "12:00"},
            {"freq": "weekly", "days": [WED], "start": "10:00", "end": "12:00"},
            {"freq": "weekdays", "start": "13:00", "end": "16:40"},
        ],
    },
    {
        "name": "McKinley Community Dinner",
        "location": "McKinley Foundation, Presby Hall, 405 E John St, Champaign, IL 61820",
        "link": "https://publish.illinois.edu/foodresources/",
        "description": "Free lunch for all students; take leftovers home. Hosted by the McKinley Foundation.",
        "recurrence": "Saturdays, 1–2 PM",
        "active": "academic",
        "rules": [{"freq": "weekly", "days": [SAT], "start": "13:00", "end": "14:00"}],
    },
    {
        "name": "Dish It Up (Women's Resources Center)",
        "location": "Women's Resources Center, 616 E Green St, Champaign, IL 61820",
        "link": "https://oiir.illinois.edu/",
        "description": "Free midday meal hosted by the Women's Resources Center. Time approximate — confirm with the center.",
        "recurrence": "2nd & 4th Mondays, around noon",
        "active": "academic",
        "rules": [{"freq": "nth_weekday", "weekday": MON, "nths": [2, 4], "start": "12:00", "end": "13:00"}],
    },
    {
        "name": "Food for Thought (Asian American Cultural Center)",
        "location": "Asian American Cultural Center, 1210 W Nevada St, Urbana, IL 61801",
        "link": "https://oiir.illinois.edu/aacc",
        "description": "Free weekly lunch and conversation. Time approximate — confirm with the center.",
        "recurrence": "Tuesdays, around noon",
        "active": "academic",
        "rules": [{"freq": "weekly", "days": [TUE], "start": "12:00", "end": "13:00"}],
    },
    {
        "name": "Food for the Soul (Bruce D. Nesbitt African American Cultural Center)",
        "location": "Bruce D. Nesbitt African American Cultural Center, 1212 W Nevada St, Urbana, IL 61801",
        "link": "https://oiir.illinois.edu/bnaacc",
        "description": "Free weekly lunch and community gathering. Time approximate — confirm with the center.",
        "recurrence": "Wednesdays, around noon",
        "active": "academic",
        "rules": [{"freq": "weekly", "days": [WED], "start": "12:00", "end": "13:00"}],
    },
    {
        "name": "Lunch on Us (La Casa Cultural Latina)",
        "location": "La Casa Cultural Latina, 1203 W Nevada St, Urbana, IL 61801",
        "link": "https://oiir.illinois.edu/la-casa",
        "description": "Free weekly lunch hosted by La Casa. Time approximate — confirm with the center.",
        "recurrence": "Thursdays, around noon",
        "active": "academic",
        "rules": [{"freq": "weekly", "days": [THU], "start": "12:00", "end": "13:00"}],
    },
    {
        "name": "Dinner on Us (Native American House)",
        "location": "Native American House, 1204 W Nevada St, Urbana, IL 61801",
        "link": "https://oiir.illinois.edu/nah",
        "description": "Free bi-weekly dinner hosted by the Native American House.",
        "recurrence": "Bi-weekly Tuesdays, 5:30 PM",
        "active": "academic",
        "rules": [{"freq": "nth_weekday", "weekday": TUE, "nths": [1, 3], "start": "17:30", "end": "18:30"}],
    },
    {
        "name": "Friday Forum + Conversation Café",
        "location": "University YMCA, 1001 S Wright St, Champaign, IL 61820",
        "link": "https://universityymca.org/",
        "description": "Free meal from the Y-Thai Eatery with a discussion of pressing public issues.",
        "recurrence": "Fridays, 12 PM",
        "active": "academic",
        "rules": [{"freq": "weekly", "days": [FRI], "start": "12:00", "end": "13:00"}],
    },
]


def _in_academic_term(d: date) -> bool:
    return any(start <= d <= end for start, end in ACADEMIC_TERMS)


def _nth_of_month(d: date) -> int:
    """Which occurrence of its weekday within the month (1st, 2nd, ...)."""
    return (d.day - 1) // 7 + 1


def _rule_matches(rule: Dict[str, Any], d: date) -> bool:
    freq = rule["freq"]
    wd = d.weekday()
    if freq == "daily":
        return True
    if freq == "weekdays":
        return wd < SAT
    if freq == "weekly":
        return wd in rule["days"]
    if freq == "nth_weekday":
        return wd == rule["weekday"] and _nth_of_month(d) in rule["nths"]
    return False


def _hm(s: str):
    h, m = s.split(":")
    return int(h), int(m)


def generate_food_events(now: datetime = None, horizon_days: int = 45,
                         max_per_resource: int = 3) -> Dict[int, Dict[str, Any]]:
    """Expand the recurrence table into dated events within the forward window.

    Emits up to ``max_per_resource`` upcoming occurrences per resource (enough to
    show the next date and allow add-to-calendar) so the JSON stays lean. Academic
    programs are skipped on dates outside the UIUC term ranges.
    """
    if now is None:
        now = datetime.now(tz=TZ)
    today = now.date()

    events: Dict[int, Dict[str, Any]] = {}
    idx = 0

    for resource in FOOD_RESOURCES:
        academic = resource["active"] == "academic"
        emitted = 0
        day_offset = 0
        while day_offset <= horizon_days and emitted < max_per_resource:
            d = today + timedelta(days=day_offset)
            day_offset += 1
            if academic and not _in_academic_term(d):
                continue
            for rule in resource["rules"]:
                if emitted >= max_per_resource:
                    break
                if not _rule_matches(rule, d):
                    continue
                sh, sm = _hm(rule["start"])
                eh, em = _hm(rule["end"])
                start_dt = datetime(d.year, d.month, d.day, sh, sm, tzinfo=TZ)
                end_dt = datetime(d.year, d.month, d.day, eh, em, tzinfo=TZ)
                if end_dt < start_dt:  # safety: overnight window
                    end_dt += timedelta(days=1)
                if end_dt < now:       # already over today — skip to keep "next" upcoming
                    continue
                events[idx] = {
                    "summary": resource["name"],
                    "description": resource["description"],
                    "location": resource["location"],
                    "tag": FREE_FOOD_TAG,
                    "htmlLink": resource["link"],
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat(),
                    "recurrence": resource["recurrence"],
                }
                idx += 1
                emitted += 1

    return events
