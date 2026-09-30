#!/usr/bin/env python3
"""Renders the window offscreen with sample events: no real accounts, keyring, network or visible window.

  python3 tools/render.py OUT.png [week|month] [dark|light] [WIDTHxHEIGHT] [editor|settings|icloud]

Everything the app would write goes to a fresh temporary directory. Evidence for layout only, not for motion.
"""
import os
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TMP = Path(tempfile.mkdtemp(prefix="calendary-render-"))
# XDG_DATA_HOME stays: fontconfig finds the user's fonts through it. Every data path is passed explicitly below.
for name in ("XDG_CONFIG_HOME", "XDG_CACHE_HOME"):
    os.environ[name] = str(TMP / name.lower())
os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, str(ROOT / "src"))

import shiboken6  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQuick import QQuickWindow  # noqa: E402

from calendary import cache  # noqa: E402
from calendary.app import build_engine  # noqa: E402
from calendary.bridge import Calendar  # noqa: E402
from calendary.preferences import Preferences  # noqa: E402

EMAIL = "name@gmail.com"


def event(db, calendar, item):
    with db:
        cache.put_events(db, EMAIL, calendar, [cache.parse_event(item)])


def sample(db):
    """A believable week around today: overlaps, a night event, all-day and multi-day bars, a read-only calendar."""
    cache.add_account(db, EMAIL)
    cache.store_calendars(db, EMAIL, [
        {"id": "privat", "name": "Privat", "color": "#7ec8ff", "writable": 1, "main": 1},
        {"id": "arbeit", "name": "Arbeit", "color": "#b5c59d", "writable": 1, "main": 0},
        {"id": "feiertage", "name": "Feiertage", "color": "#ff9ec7", "writable": 0, "main": 0}])
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    monday = today - timedelta(days=today.weekday())
    timed = [("arbeit", 1, (8, 50), (9, 50), "Gespräch Kunde", "Büro"), ("privat", 0, (10, 0), (11, 30), "Zahnarzt", ""),
             ("privat", 0, (11, 0), (12, 0), "Mittagessen", ""), ("arbeit", 2, (14, 0), (15, 0), "Team-Meeting", ""),
             ("privat", 3, (18, 30), (21, 0), "Kino", ""), ("privat", 4, (7, 0), (8, 0), "Gym", ""),
             ("privat", 2, (16, 0), (16, 30), "Paket abholen", ""), ("privat", 5, (20, 0), (23, 30), "Geburtstagsfeier", "Bar")]
    for n, (calendar, day, start, end, title, place) in enumerate(timed):
        base = monday + timedelta(days=day)
        event(db, calendar, {"id": "t%d" % n, "summary": title, "location": place,
                             "start": {"dateTime": base.replace(hour=start[0], minute=start[1]).astimezone().isoformat()},
                             "end": {"dateTime": base.replace(hour=end[0], minute=end[1]).astimezone().isoformat()}})
    for n, (calendar, day, length, title) in enumerate([("feiertage", 4, 1, "Tag der Deutschen Einheit"),
                                                        ("privat", 5, 3, "Kurztrip")]):
        first = (monday + timedelta(days=day)).date()
        event(db, calendar, {"id": "a%d" % n, "summary": title, "start": {"date": first.isoformat()},
                             "end": {"date": (first + timedelta(days=length)).isoformat()}})


def arguments():
    args = sys.argv[1:]
    size = next((a for a in args if "x" in a and a.split("x")[0].isdigit()), "1240x800")
    return {"out": args[0] if args else "calendary.png",
            "view": "month" if "month" in args else "week",
            "theme": "light" if "light" in args else "dark",
            "size": [int(v) for v in size.split("x")],
            "sheet": next((a for a in args if a in ("editor", "settings", "icloud")), "")}


def main():
    options = arguments()
    app = QGuiApplication(sys.argv)
    db = cache.connect(str(TMP / "calendary.db"))
    sample(db)
    preferences = Preferences(str(TMP / "calendary.ini"))
    for key, value in (("view", options["view"]), ("theme", options["theme"]), ("width", options["size"][0]),
                       ("height", options["size"][1])):
        preferences.set(key, value)
    client = TMP / "google-client.json"
    client.write_text('{"client_id": "render.apps.googleusercontent.com", "client_secret": "render"}')
    # No client while the bridge starts, so it never asks the real keyring; afterwards the sheet may show it as set up.
    calendar = Calendar(preferences, db, files={"island": str(TMP / "upcoming.json"), "client": str(TMP / "none.json")})
    calendar.signin.client_file = client
    engine = build_engine(preferences, calendar)
    window = shiboken6.wrapInstance(shiboken6.getCppPointer(engine.rootObjects()[0])[0], QQuickWindow)
    if options["sheet"] in ("settings", "icloud"):
        window.setProperty("settingsOpen", True)
        sheet = next(o for o in window.contentItem().childItems() if o.metaObject().className().startswith("SettingsSheet"))
        sheet.setProperty("addingICloud", options["sheet"] == "icloud")
    elif options["sheet"] == "editor":
        week = calendar.week(float(cache.midnight(datetime.now().date()) - 7 * 86400000), 14)
        ev = next(e for day in week["days"] for e in day if e["title"] == "Gespräch Kunde")
        editor = next(o for o in window.contentItem().childItems() if o.metaObject().className().startswith("EventEditor"))
        editor.setProperty("ev", ev)
    calendar.accountsChanged.emit()
    deadline = time.monotonic() + 1.5
    while time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    window.grabWindow().save(options["out"])
    print(options["out"])


if __name__ == "__main__":
    main()
