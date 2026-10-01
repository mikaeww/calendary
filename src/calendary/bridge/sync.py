"""Keeps the cache in step with Google and iCloud: calendar lists and the padded window on screen (ADR 0002).

Every fetched calendar is handed to the arrivals, which decide what to announce. Not for edits (edits.py) or
sign-in (signin.py).
"""
import time

from calendary import cache
from calendary.bridge.signin import display
from calendary.language import tr

# Also the polling period: short enough that events others add show up while the app is open.
STALE_SECONDS = 60
PAD_MS = 31 * 86400000


class Sync:
    def __init__(self, calendar):
        self.calendar = calendar
        self.window = None
        self.fetched = []

    def show(self, start, end):
        """The range on screen; fetched again when no fresh fetch covers it."""
        self.window = (start, end)
        now = time.monotonic()
        if not any(a <= start and end <= b and now - at < STALE_SECONDS for a, b, at in self.fetched):
            self.fetch(start - PAD_MS, end + PAD_MS)

    def everything(self):
        """Calendar lists of every account, then the window on screen."""
        self.fetched = []
        for email in list(self.calendar.remote):
            self.refresh(email)

    def refresh(self, email):
        def stored(items):
            if email not in self.calendar.remote:
                return
            cache.store_calendars(self.calendar.db, email, items)
            self.calendar.arrivals.calendars(email, items)
            self.calendar.accounts_changed()
            if self.window:
                self.fetch(self.window[0] - PAD_MS, self.window[1] + PAD_MS, [email])
        self.calendar.worker.run(self.calendar.remote[email].calendars, stored)

    def fetch(self, start, end, emails=None):
        entry = (start, end, time.monotonic())
        self.fetched.append(entry)
        span = (cache.local(start).isoformat(), cache.local(end).isoformat())
        for email in emails or list(self.calendar.remote):
            for row in cache.calendars(self.calendar.db, email):
                self.fetch_calendar(self.calendar.remote[email], row, ((start, end), span), entry)

    def fetch_calendar(self, account, calendar, windows, entry):
        """calendar = its cache row; windows = ((start_ms, end_ms), (start_rfc3339, end_rfc3339)).

        A failed fetch is not counted as fresh.
        """
        calendar_id = calendar["id"]

        def job():
            rows, skipped = [], 0
            for item in account.events(calendar_id, windows[1]):
                try:
                    row = cache.parse_event(item)
                except (KeyError, ValueError):
                    skipped += 1
                    continue
                if row:
                    rows.append(row)
            return rows, skipped

        def then(result):
            rows, skipped = result
            if account.email not in self.calendar.remote:
                return
            cache.replace_window(self.calendar.db, (account.email, calendar_id), windows[0], rows)
            self.calendar.bump()
            own = {display(key).lower() for key in self.calendar.remote}
            for banner in self.calendar.arrivals.check(account.email, (calendar_id, calendar["name"], calendar["color"]),
                                                        rows, own):
                self.calendar.arrived.emit(banner)
            if skipped:
                self.calendar.say(tr("%d Termine konnten nicht gelesen werden und fehlen") % skipped, True)

        def forget():
            if entry in self.fetched:
                self.fetched.remove(entry)
        self.calendar.worker.run(job, then, forget)
