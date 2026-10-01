"""docs/verification/arrivals.md claims 1 to 5: which new events become banners, and the bridge emitting them."""
import json
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from PySide6.QtGui import QGuiApplication

from calendary import cache
from calendary.bridge import Calendar
from calendary.bridge.arrivals import Arrivals, news
from calendary.preferences import Preferences
from tests.test_bridge import FakeGoogle, FakeKeyring

SINCE = datetime(2026, 10, 1, 10, tzinfo=timezone.utc)
LATER, EARLIER = "2026-10-01T10:05:00.000Z", "2026-10-01T09:55:00.000Z"


def row(ident, day, created=LATER, creator=None, series=None):
    item = {"id": ident, "summary": "Termin " + ident, "start": {"dateTime": "2026-10-%02dT12:00:00+02:00" % day},
            "end": {"dateTime": "2026-10-%02dT13:00:00+02:00" % day}, "created": created,
            "creator": creator or {"email": "alex@example.com", "displayName": "Alex"}}
    if series:
        item["recurringEventId"] = series
    return cache.parse_event(item)


def ids(rows):
    return [r["id"] for r in rows]


class NewsTest(unittest.TestCase):
    def test_only_events_created_after_the_start(self):
        rows = [row("old", 6, EARLIER), row("new", 7), row("unknown", 8, None), row("naive", 9, "2026-10-01T11:00:00")]
        self.assertEqual(ids(news(rows, SINCE, set(), False)), ["new"])

    def test_own_events_are_skipped(self):
        rows = [row("self", 6, creator={"email": "me@gmail.com", "self": True}),
                row("other account", 7, creator={"email": "Me@iCloud.com"}), row("alex", 8)]
        self.assertEqual(ids(news(rows, SINCE, {"me@icloud.com"}, True)), ["alex"])

    def test_unknown_creator_counts_only_where_the_user_cannot_write(self):
        rows = [row("anonymous", 6, creator={"email": ""})]
        self.assertEqual(ids(news(rows, SINCE, set(), True)), [])
        found = news(rows, SINCE, set(), False)
        self.assertEqual((ids(found), found[0]["who"]), (["anonymous"], ""))

    def test_a_series_counts_once_with_its_first_instance(self):
        rows = [row("s_2", 13, series="s"), row("s_1", 6, series="s"), row("single", 7)]
        self.assertEqual(ids(news(rows, SINCE, set(), False)), ["s_1", "single"])


class ArrivalsTest(unittest.TestCase):
    def setUp(self):
        self.arrivals = Arrivals()
        self.arrivals.since = SINCE
        self.arrivals.calendars("me", [{"id": "mine", "writable": 1, "shared": 0},
                                       {"id": "alex", "writable": 0, "shared": 1}])

    def test_only_shared_calendars_and_only_once(self):
        self.assertEqual(self.arrivals.check("me", ("mine", "Privat", "#888888"), [row("a", 6)], set()), [])
        banners = self.arrivals.check("me", ("alex", "Alex teilt", "#ff9ec7"), [row("a", 6)], set())
        self.assertEqual([(b["title"], b["who"], b["calendar"], b["count"]) for b in banners],
                         [("Termin a", "Alex", "Alex teilt", 1)])
        self.assertEqual(self.arrivals.check("me", ("alex", "Alex teilt", "#ff9ec7"), [row("a", 6)], set()), [])

    def test_many_at_once_become_one_summary(self):
        rows = [row("e%d" % n, 6 + n) for n in range(5)]
        banners = self.arrivals.check("me", ("alex", "Alex teilt", "#ff9ec7"), rows, set())
        self.assertEqual([(b["title"], b["who"], b["count"]) for b in banners], [("5 neue Termine", "Alex", 5)])


class SharedGoogle(FakeGoogle):
    def calendars(self):
        return [{"id": "cal", "name": "Privat", "color": "#7ec8ff", "writable": 1, "main": 1, "shared": 0},
                {"id": "alex", "name": "Alex teilt", "color": "#ff9ec7", "writable": 0, "main": 0, "shared": 1}]

    def events(self, calendar, window):
        if calendar != "alex":
            return []
        created = (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat()
        return [{"id": "x", "summary": "Kino", "start": {"dateTime": "2026-10-07T20:00:00+02:00"},
                 "end": {"dateTime": "2026-10-07T22:00:00+02:00"}, "created": created,
                 "creator": {"email": "alex@example.com"}}]


class BridgeArrivalTest(unittest.TestCase):
    def test_a_new_event_in_a_shared_calendar_is_announced_once(self):
        app = QGuiApplication.instance() or QGuiApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "client.json").write_text(json.dumps({"client_id": "x", "client_secret": "y"}))
            db = cache.connect(":memory:")
            cache.add_account(db, "me")
            arrived = []
            with mock.patch("calendary.bridge.signin.Account", lambda client, email, token: SharedGoogle()):
                calendar = Calendar(Preferences(str(root / "p.ini"), shell=root), db, FakeKeyring({"me": "t"}),
                                    {"island": str(root / "up.json"), "client": str(root / "client.json")})
                calendar.arrived.connect(arrived.append)
                calendar.show(cache.ms(datetime(2026, 10, 5).astimezone()), cache.ms(datetime(2026, 10, 12).astimezone()))
                for _ in range(2):
                    calendar.refresh()
                    deadline = time.monotonic() + 5
                    while (calendar.busy or not arrived) and time.monotonic() < deadline:
                        app.processEvents()
            db.close()
        self.assertEqual([(a["title"], a["who"], a["calendar"]) for a in arrived],
                         [("Kino", "alex@example.com", "Alex teilt")])


if __name__ == "__main__":
    unittest.main()
