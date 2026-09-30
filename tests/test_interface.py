"""The real window, offscreen, against the fake Google: drag, resize, draw, the editor, paging and the view switch.

Mouse events go to the offscreen window only, never to a desktop session.
"""
import json
import tempfile
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

import shiboken6
from PySide6.QtCore import Q_ARG, QEvent, QMetaObject, QPointF, Qt
from PySide6.QtGui import QGuiApplication, QMouseEvent
from PySide6.QtQuick import QQuickWindow

from calendary import cache
from calendary.app import build_engine
from calendary.bridge import Calendar
from calendary.preferences import Preferences
from tests.test_bridge import FakeGoogle, FakeKeyring

MOUSE = {"press": QEvent.MouseButtonPress, "move": QEvent.MouseMove, "release": QEvent.MouseButtonRelease}


class InterfaceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        (root / "client.json").write_text(json.dumps({"client_id": "x.apps.googleusercontent.com", "client_secret": "y"}))
        monday = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        monday -= timedelta(days=monday.weekday())
        cls.monday = monday
        cls.fake = FakeGoogle()
        cls.fake.items = [{"id": "kino", "summary": "Kino", "start": {"dateTime": (monday + timedelta(days=3, hours=18)).astimezone().isoformat()},
                           "end": {"dateTime": (monday + timedelta(days=3, hours=20)).astimezone().isoformat()}}]
        cls.db = cache.connect(":memory:")
        cache.add_account(cls.db, "me")
        preferences = Preferences(str(root / "p.ini"), shell=root)
        preferences.set("view", "week")
        with mock.patch("calendary.bridge.signin.Account", lambda client, email, token: cls.fake):
            cls.calendar = Calendar(preferences, cls.db, FakeKeyring({"me": "t"}),
                                    {"island": str(root / "up.json"), "client": str(root / "client.json")})
            cls.engine = build_engine(preferences, cls.calendar)
            # Inside the patch: the accounts are created when the keyring answer arrives on the GUI thread.
            cls.spin(1.5)
        cls.window = shiboken6.wrapInstance(shiboken6.getCppPointer(cls.engine.rootObjects()[0])[0], QQuickWindow)

    @classmethod
    def tearDownClass(cls):
        cls.window.close()
        del cls.engine
        cls.db.close()
        cls.tmp.cleanup()

    @classmethod
    def spin(cls, seconds=0.6):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline or cls.calendar.busy:
            cls.app.processEvents()
            time.sleep(0.005)
            if time.monotonic() > deadline + 5:
                raise AssertionError("worker still busy")

    def mouse(self, kind, x, y):
        button = Qt.NoButton if kind == "move" else Qt.LeftButton
        buttons = Qt.NoButton if kind == "release" else Qt.LeftButton
        event = QMouseEvent(MOUSE[kind], QPointF(x, y), QPointF(x, y), button, buttons, Qt.NoModifier)
        QGuiApplication.sendEvent(self.window, event)
        self.app.processEvents()

    def drag(self, start, end):
        self.mouse("press", *start)
        for step in range(1, 11):
            self.mouse("move", start[0] + (end[0] - start[0]) * step / 10, start[1] + (end[1] - start[1]) * step / 10)
        self.mouse("release", *end)
        self.spin()

    def items(self, prefix, root=None):
        found = []

        def walk(item):
            for child in item.childItems():
                if child.metaObject().className().startswith(prefix):
                    found.append(child)
                walk(child)
        walk(root or self.window.contentItem())
        return found

    def block(self, title):
        return next(b for b in self.items("EventBlock") if b.property("ev")["title"] == title)

    def test_1_move_resize_draw_and_edit(self):
        week = self.items("WeekView")[0]
        column, hour = week.property("column"), week.property("hourHeight")
        kino = self.block("Kino")
        grab = kino.mapToScene(QPointF(kino.width() / 2, 12))
        self.drag((grab.x(), grab.y()), (grab.x() + column, grab.y() + hour))
        name, item = self.fake.calls[-1]
        self.assertEqual(name, "patch")
        moved = cache.parse_event(dict(item, id="x"))
        self.assertEqual(datetime.fromtimestamp(moved["start"] / 1000), self.monday + timedelta(days=4, hours=19))

        kino = self.block("Kino")
        edge = kino.mapToScene(QPointF(kino.width() / 2, kino.height() - 3))
        self.drag((edge.x(), edge.y()), (edge.x(), edge.y() + hour))
        resized = cache.parse_event(dict(self.fake.calls[-1][1], id="x"))
        self.assertEqual((resized["end"] - resized["start"]) / 60000, 180)

        kino = self.block("Kino")
        top = kino.mapToScene(QPointF(0, 0)).y() - kino.property("y")
        first_day = week.mapToScene(QPointF(week.property("gutter") + column / 2, 0)).x()
        # At the height of Kino, which is on screen whatever the grid is scrolled to.
        self.drag((first_day, top + 19 * hour), (first_day, top + 20.5 * hour))
        editor = self.items("EventEditor")[0]
        self.assertTrue(editor.property("open"), "drawing a slot opens the editor")
        self.items("QQuickTextInput", editor)[0].setProperty("text", "Probe")
        QMetaObject.invokeMethod(editor, "save")
        self.spin()
        name, item = self.fake.calls[-1]
        self.assertEqual((name, item["summary"]), ("insert", "Probe"))
        created = cache.parse_event(dict(item, id="x"))
        self.assertEqual(datetime.fromtimestamp(created["start"] / 1000), self.monday + timedelta(hours=19))
        self.assertEqual((created["end"] - created["start"]) / 60000, 90)

    def test_2_paging_and_view_switch(self):
        start = self.window.property("rangeStart")
        QMetaObject.invokeMethod(self.window, "go", Q_ARG("QVariant", 1))
        self.spin(0.8)
        self.assertEqual(datetime.fromtimestamp(self.window.property("rangeStart") / 1000),
                         datetime.fromtimestamp(start / 1000) + timedelta(days=7))
        self.window.setProperty("view", "month")
        self.spin(0.8)
        month = self.items("MonthView")[0]
        week = self.items("WeekView")[0]
        self.assertEqual((round(month.property("opacity"), 3), week.property("visible")), (1.0, False))


if __name__ == "__main__":
    unittest.main()
