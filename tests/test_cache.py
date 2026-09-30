"""docs/verification/cache.md: round trips over every day of 2020-2035, exclusive all-day ends, window replacement.

The oracle for times is zoneinfo, for the table a plain list model; neither shares code with calendary.cache.
"""
import os
import random
import time
import unittest
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from calendary import cache

ZONE = "Europe/Berlin"
FIRST, LAST = date(2020, 1, 1), date(2035, 12, 31)
_saved_tz = None


def setUpModule():
    global _saved_tz
    if not hasattr(time, "tzset"):
        raise unittest.SkipTest("pinning the time zone needs time.tzset, which Windows lacks")
    _saved_tz = os.environ.get("TZ")
    os.environ["TZ"] = ZONE
    time.tzset()


def tearDownModule():
    if _saved_tz is None:
        os.environ.pop("TZ", None)
    else:
        os.environ["TZ"] = _saved_tz
    time.tzset()


def oracle_ms(day, hour=0, minute=0):
    return int(datetime(day.year, day.month, day.day, hour, minute, tzinfo=ZoneInfo(ZONE)).timestamp() * 1000)


def every_day():
    day = FIRST
    while day <= LAST:
        yield day
        day += timedelta(days=1)


class RoundTripTest(unittest.TestCase):
    def test_all_day_events_every_day(self):
        checked = 0
        for day in every_day():
            for length in (1, 2, 3):
                fields = {"allDay": True, "start": oracle_ms(day), "end": oracle_ms(day + timedelta(days=length))}
                body = cache.to_google(fields)
                self.assertEqual(body["start"], {"date": day.isoformat()})
                self.assertEqual(body["end"], {"date": (day + timedelta(days=length)).isoformat()})
                row = cache.parse_event(dict(body, id="x"))
                self.assertEqual((row["start"], row["end"], row["all_day"]), (fields["start"], fields["end"], 1))
                checked += 1
        self.assertEqual(checked, 5844 * 3)

    def test_timed_events_every_day(self):
        checked = 0
        for day in every_day():
            for hour, minute in ((0, 0), (2, 30), (23, 45)):
                start = oracle_ms(day, hour, minute)
                for minutes in (15, 60, 1500):
                    fields = {"start": start, "end": start + minutes * 60000}
                    row = cache.parse_event(dict(cache.to_google(fields), id="x"))
                    self.assertEqual((row["start"], row["end"], row["all_day"]), (fields["start"], fields["end"], 0))
                    checked += 1
        self.assertEqual(checked, 5844 * 9)

    def test_one_day_all_day_event_ends_next_day(self):
        body = cache.to_google({"allDay": True, "start": oracle_ms(date(2026, 3, 29)),
                                "end": oracle_ms(date(2026, 3, 29))})
        self.assertEqual(body["end"], {"date": "2026-03-30"})

    def test_cancelled_and_malformed_events(self):
        self.assertIsNone(cache.parse_event({"id": "c", "status": "cancelled"}))
        with self.assertRaises(ValueError):
            cache.parse_event({"id": "d", "start": {}})

    def test_repeat_and_fields(self):
        body = cache.to_google({"title": "T", "location": "L", "notes": "N", "start": 0, "end": 3600000,
                                "repeat": "WEEKLY"})
        self.assertEqual(body["recurrence"], ["RRULE:FREQ=WEEKLY"])
        row = cache.parse_event(dict(body, id="r"))
        self.assertEqual((row["title"], row["location"], row["notes"], row["recurring"]), ("T", "L", "N", 1))


def overlaps(event, window):
    """The oracle's overlap rule, written independently of the SQL."""
    start, end = window
    if event["end"] == event["start"]:
        return start <= event["start"] < end
    return event["start"] < end and event["end"] > start


class WindowTest(unittest.TestCase):
    def test_replace_window_against_list_model(self):
        rng = random.Random(20260930)
        for sequence in range(500):
            db = cache.connect(":memory:")
            db.execute("insert into calendars values ('me', 'cal', 'C', '#888888', 1, 1)")
            db.execute("insert into calendars values ('me', 'other', 'O', '#888888', 1, 0)")
            model = []
            for step in range(6):
                calendar = rng.choice(["cal", "other"])
                window = tuple(sorted(rng.sample(range(0, 100), 2)))
                rows = []
                for n in range(rng.randint(0, 4)):
                    start = rng.randint(window[0], window[1])
                    rows.append({"id": "%d-%d-%d" % (sequence, step, n), "start": start,
                                 "end": start + rng.choice([0, 1, 5, 30]), "all_day": 0, "title": "",
                                 "location": "", "notes": "", "recurring": 0, "raw": "{}"})
                cache.replace_window(db, ("me", calendar), window, rows)
                model = [m for m in model if not (m["calendar"] == calendar and overlaps(m, window))]
                model = [m for m in model if not (m["calendar"] == calendar and m["id"] in {r["id"] for r in rows})]
                model += [dict(r, calendar=calendar) for r in rows]
            stored = {(r["calendar"], r["id"]) for r in db.execute("select calendar, id from events")}
            db.close()
            self.assertEqual(stored, {(m["calendar"], m["id"]) for m in model}, "sequence %d" % sequence)

    def test_hidden_calendars_and_accounts(self):
        db = cache.connect(":memory:")
        cache.add_account(db, "me")
        cache.store_calendars(db, "me", [{"id": "cal", "name": "C", "color": "#888888", "writable": 1, "main": 1}])
        with db:
            cache.put_events(db, "me", "cal", [cache.parse_event({"id": "e", "start": {"date": "2026-10-01"},
                                                                    "end": {"date": "2026-10-02"}})])
        span = (oracle_ms(date(2026, 10, 1)), oracle_ms(date(2026, 10, 2)))
        self.assertEqual(len(cache.between(db, *span)), 1)
        self.assertEqual(cache.between(db, *span, {"me\ncal"}), [])
        cache.store_calendars(db, "me", [])
        self.assertEqual(cache.between(db, *span), [], "events of a removed calendar go with it")
        cache.remove_account(db, "me")
        self.assertEqual(cache.accounts(db), [])
        db.close()


if __name__ == "__main__":
    unittest.main()
