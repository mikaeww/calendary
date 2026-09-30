"""docs/verification/google.md claims 4-5: the bridge against a fake Google and a fake keyring, no network."""
import json
import tempfile
import time
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

from PySide6.QtGui import QGuiApplication

from calendary import cache
from calendary.bridge import Calendar
from calendary.bridge.island import LIMIT, upcoming
from calendary.google import GoogleError
from calendary.preferences import Preferences


def at(*parts):
    return cache.ms(datetime(*parts).astimezone())


class FakeKeyring:
    def __init__(self, tokens):
        self.tokens = dict(tokens)

    def store(self, email, token):
        self.tokens[email] = token

    def lookup(self, email):
        return self.tokens.get(email)

    def clear(self, email):
        self.tokens.pop(email, None)


class FakeGoogle:
    """Records calls; `refuse` makes the next write fail like Google would."""

    def __init__(self, email="me"):
        self.email = email
        self.items = [{"id": "e1", "summary": "Gespräch Kunde", "start": {"dateTime": "2026-10-06T08:50:00+02:00"},
                       "end": {"dateTime": "2026-10-06T09:50:00+02:00"}},
                      {"id": "broken", "start": {}}]
        self.calls, self.refuse = [], False

    def calendars(self):
        return [{"id": "cal", "name": "Privat", "color": "#7ec8ff", "writable": 1, "main": 1}]

    def events(self, calendar, window):
        return list(self.items)

    def write(self, name, item):
        self.calls.append((name, item))
        if self.refuse:
            raise GoogleError("Google: nein")
        return item

    def insert(self, calendar, body):
        item = self.write("insert", dict(body, id="new%d" % len(self.items)))
        self.items.append(item)
        return item

    def patch(self, calendar, event, body):
        return self.write("patch", dict(body, id=event))

    def move(self, calendar, event, destination):
        return self.write("move", {"id": event, "to": destination})

    def delete(self, calendar, event):
        self.items = [i for i in self.items if i["id"] != event]
        return self.write("delete", {"id": event})


class BridgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        (root / "client.json").write_text(json.dumps({"client_id": "x.apps.googleusercontent.com",
                                                      "client_secret": "y"}))
        self.island = root / "upcoming.json"
        self.db = cache.connect(":memory:")
        cache.add_account(self.db, "me")
        cache.add_account(self.db, "gone")
        self.fake = FakeGoogle()
        self.notices = []
        with mock.patch("calendary.bridge.signin.Account", lambda client, email, token: self.fake):
            self.calendar = Calendar(Preferences(str(root / "p.ini"), shell=root), self.db, FakeKeyring({"me": "t"}),
                                     {"island": str(self.island), "client": str(root / "client.json")})
            self.calendar.notice.connect(lambda text, bad: self.notices.append(text))
            self.calendar.show(at(2026, 10, 5), at(2026, 10, 12))
            self.settle()

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def settle(self):
        deadline = time.monotonic() + 5
        self.app.processEvents()
        while self.calendar.busy and time.monotonic() < deadline:
            self.app.processEvents()
        self.app.processEvents()
        self.assertFalse(self.calendar.busy, "worker still busy after 5 s")

    def titles(self, day):
        return [e["title"] for e in self.calendar.week(at(2026, 10, 5), 7)["days"][day]]

    def test_restore_fetches_and_reports(self):
        self.assertEqual(list(self.calendar.remote), ["me"])
        self.assertIn("gone ist abgemeldet, bitte neu anmelden", self.notices)
        self.assertIn("1 Termine konnten nicht gelesen werden und fehlen", self.notices)
        self.assertEqual(self.titles(1), ["Gespräch Kunde"])
        self.assertEqual(self.calendar.accounts[0]["calendars"][0]["name"], "Privat")

    def test_edit_shows_at_once_then_takes_googles_id(self):
        fields = {"calendarKey": "me\ncal", "title": "Neu", "start": at(2026, 10, 7, 12), "end": at(2026, 10, 7, 13)}
        self.calendar.save(fields)
        shown = self.calendar.week(at(2026, 10, 5), 7)["days"][2][0]
        self.assertTrue(shown["key"].startswith("me\ncal\npending-"))
        self.settle()
        saved = self.calendar.week(at(2026, 10, 5), 7)["days"][2][0]
        self.assertEqual((saved["key"], saved["title"]), ("me\ncal\nnew2", "Neu"))
        self.calendar.save(dict(fields, key=saved["key"], title="Umbenannt"))
        self.settle()
        self.assertEqual(self.fake.calls[-1][0], "patch")
        self.assertEqual(self.titles(2), ["Umbenannt"])

    def test_refused_edit_rolls_back(self):
        self.fake.refuse = True
        self.calendar.save({"calendarKey": "me\ncal", "title": "Kaputt", "start": at(2026, 10, 7, 12),
                            "end": at(2026, 10, 7, 13)})
        self.assertEqual(self.titles(2), ["Kaputt"])
        self.settle()
        self.settle()
        self.assertEqual(self.titles(2), [])
        self.assertIn("Google: nein", self.notices)

    def test_remove_hide_island_and_sign_out(self):
        with open(self.island) as f:
            self.assertEqual(set(json.load(f)), {"updated", "events"})
        self.calendar.setVisible("me\ncal", False)
        self.assertEqual(self.titles(1), [])
        self.calendar.setVisible("me\ncal", True)
        self.calendar.remove("me\ncal\ne1")
        self.assertEqual(self.titles(1), [])
        self.settle()
        self.assertEqual(self.fake.calls[-1], ("delete", {"id": "e1"}))
        self.calendar.signOut("me")
        self.settle()
        self.assertEqual((self.calendar.accounts[0]["email"], len(self.calendar.accounts)), ("gone", 1))
        self.assertIsNone(self.calendar.signin.keyring.lookup("me"))

    def test_sign_in_without_client_says_so(self):
        self.calendar.signin.client_file = Path(self.tmp.name, "missing.json")
        self.calendar.signIn()
        self.assertTrue(self.notices[-1].startswith("Google-Anmeldung ist nicht eingerichtet"))
        self.assertFalse(self.calendar.signingIn)


class IslandTest(unittest.TestCase):
    def test_upcoming_order_filter_and_limit(self):
        event = lambda title, start, end, all_day=False: {"title": title, "start": start, "end": end, "allDay": all_day,
                                                          "color": "#888888", "calendar": "C", "location": ""}
        events = [event("later", 50, 60), event("over", 0, 10), event("day", 20, 120, True), event("timed", 20, 30),
                  event("running", 5, 40)] + [event("n%d" % i, 100 + i, 200) for i in range(10)]
        titles = [e["title"] for e in upcoming(events, now=10)]
        self.assertEqual(titles[:4], ["running", "day", "timed", "later"])
        self.assertEqual(len(titles), LIMIT)
        self.assertNotIn("over", titles)


if __name__ == "__main__":
    unittest.main()
