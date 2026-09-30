"""Creating, changing and deleting events: shown at once, sent to Google, rolled back by a refetch on refusal.

Not for fetching (sync.py).
"""
import secrets

from calendary import cache


class Edits:
    def __init__(self, calendar):
        self.calendar = calendar

    def save(self, fields):
        """fields: key (empty for new), calendarKey, title, location, notes, start, end, allDay, repeat."""
        account, calendar = cache.split_key(fields["calendarKey"])
        old = cache.split_key(fields["key"]) if fields.get("key") else None
        remote = self.calendar.remote.get(account)
        previous = self.calendar.remote.get(old[0]) if old else None
        if not remote or (old and not previous):
            self.calendar.say("%s ist nicht angemeldet" % (account if not remote else old[0]), True)
            return
        body = cache.to_google(fields)
        shown = old[2] if old else "pending-" + secrets.token_hex(6)
        with self.calendar.db:
            if old:
                cache.delete_event(self.calendar.db, *old)
            cache.put_events(self.calendar.db, account, calendar, [cache.parse_event(dict(body, id=shown))])
        self.calendar.bump()

        def send():
            if not old:
                return remote.insert(calendar, body)
            if old[0] != account:
                created = remote.insert(calendar, body)
                previous.delete(old[1], old[2])
                return created
            if old[1] != calendar:
                remote.move(old[1], old[2], calendar)
            return remote.patch(calendar, old[2], body)

        def settle(item):
            with self.calendar.db:
                cache.delete_event(self.calendar.db, account, calendar, shown)
                cache.put_events(self.calendar.db, account, calendar, [cache.parse_event(item)])
            self.calendar.bump()
            # A new series has instances beyond the one item Google returns.
            if body.get("recurrence"):
                self.calendar.sync.everything()
        self.calendar.worker.run(send, settle, self.calendar.sync.everything)

    def remove(self, key):
        account, calendar, event = cache.split_key(key)
        remote = self.calendar.remote.get(account)
        if not remote:
            self.calendar.say("%s ist nicht angemeldet" % account, True)
            return
        with self.calendar.db:
            cache.delete_event(self.calendar.db, account, calendar, event)
        self.calendar.bump()
        self.calendar.worker.run(lambda: remote.delete(calendar, event), lambda _: None,
                                 self.calendar.sync.everything)
