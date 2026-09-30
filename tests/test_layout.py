"""docs/verification/layout.md: columns, lanes and month cells against brute-force oracles."""
import itertools
import os
import random
import time
import unittest
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from calendary import layout

ZONE = "Europe/Berlin"
SEED = 20260930
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


def at(day, minutes=0):
    moment = datetime(day.year, day.month, day.day, tzinfo=ZoneInfo(ZONE)) + timedelta(minutes=minutes)
    return int(moment.timestamp() * 1000)


def depth(intervals):
    """Largest number of half-open intervals covering one instant, by checking every start."""
    return max((sum(1 for a, b in intervals if a <= s < b) for s, _ in intervals), default=0)


class ColumnsTest(unittest.TestCase):
    def test_columns_on_random_days(self):
        rng = random.Random(SEED)
        monday = date(2026, 9, 28)
        for case in range(2000):
            events = []
            for n in range(rng.randint(1, 12)):
                start = rng.randrange(0, 24 * 60 - 15, 15)
                length = rng.choice([15, 20, 30, 45, 60, 90, 120, 240])
                events.append({"title": str(n), "allDay": False, "start": at(monday, start),
                               "end": at(monday, min(24 * 60, start + length))})
            placed = layout.week(events, at(monday), 1)["days"][0]
            self.assertEqual(len(placed), len(events), "case %d" % case)
            for a, b in itertools.combinations(placed, 2):
                if a["top"] < b["bottom"] and b["top"] < a["bottom"]:
                    self.assertNotEqual(a["col"], b["col"], "case %d: %s and %s overlap" % (case, a, b))
            for ev in placed:
                self.assertLess(ev["col"], ev["cols"])
                cluster = [p for p in placed if p["cols"] == ev["cols"] and self.connected(placed, ev, p)]
                self.assertEqual(ev["cols"], depth([(p["top"], p["bottom"]) for p in cluster]), "case %d" % case)

    @staticmethod
    def connected(placed, a, b):
        """Whether a and b are in one cluster: a chain of overlapping events links them."""
        seen, todo = {id(a)}, [a]
        while todo:
            current = todo.pop()
            if current is b:
                return True
            for other in placed:
                if id(other) not in seen and other["top"] < current["bottom"] and current["top"] < other["bottom"]:
                    seen.add(id(other))
                    todo.append(other)
        return False

    def test_event_across_midnight_is_split(self):
        monday = date(2026, 9, 28)
        night = {"title": "n", "allDay": False, "start": at(monday, 23 * 60), "end": at(monday, 25 * 60)}
        days = layout.week([night], at(monday), 2)["days"]
        self.assertEqual((days[0][0]["top"], days[0][0]["bottom"]), (1380, 1440))
        self.assertEqual((days[1][0]["top"], days[1][0]["bottom"]), (0, 60))


class LanesTest(unittest.TestCase):
    def test_every_set_of_up_to_three_bars(self):
        monday = date(2026, 9, 28)
        spans = [(a, b) for a in range(7) for b in range(a, 7)]
        self.assertEqual(len(spans), 28)
        checked = 0
        for count in (1, 2, 3):
            for chosen in itertools.product(spans, repeat=count):
                events = [{"title": str(i), "allDay": True, "start": at(monday + timedelta(days=a)),
                           "end": at(monday + timedelta(days=b + 1))} for i, (a, b) in enumerate(chosen)]
                result = layout.week(events, at(monday), 7)
                bars = result["bars"]
                self.assertEqual([(bar["first"], bar["first"] + bar["span"] - 1) for bar in
                                  sorted(bars, key=lambda bar: int(bar["title"]))], list(chosen))
                for x, y in itertools.combinations(bars, 2):
                    if x["lane"] == y["lane"]:
                        self.assertTrue(x["first"] + x["span"] <= y["first"] or y["first"] + y["span"] <= x["first"])
                self.assertEqual(result["lanes"], depth([(a, b + 1) for a, b in chosen]))
                checked += 1
        self.assertEqual(checked, 28 + 28 ** 2 + 28 ** 3)

    def test_bars_clip_to_the_week(self):
        monday = date(2026, 9, 28)
        long = {"title": "l", "allDay": True, "start": at(monday - timedelta(days=3)), "end": at(monday + timedelta(days=2))}
        bar = layout.week([long], at(monday), 7)["bars"][0]
        self.assertEqual((bar["first"], bar["span"]), (0, 2))


class MonthTest(unittest.TestCase):
    def test_cells_on_random_months(self):
        rng = random.Random(SEED)
        for case in range(500):
            first = date(2020, 1, 1) + timedelta(days=rng.randrange(0, 5800))
            events = []
            for n in range(rng.randint(0, 10)):
                start = rng.randrange(-3 * 1440, 45 * 1440, 15)
                length = rng.choice([0, 15, 60, 1440, 1500, 3 * 1440])
                events.append({"title": str(n), "allDay": False, "start": at(first, start),
                               "end": at(first, start + length)})
            cells = layout.month(events, at(first))
            for i in range(42):
                begin, end = at(first + timedelta(days=i)), at(first + timedelta(days=i + 1))
                expected = [e["title"] for e in events if (begin <= e["start"] < end if e["start"] == e["end"]
                                                           else e["start"] < end and e["end"] > begin)]
                self.assertEqual([e["title"] for e in cells[i]], expected, "case %d cell %d" % (case, i))


if __name__ == "__main__":
    unittest.main()
