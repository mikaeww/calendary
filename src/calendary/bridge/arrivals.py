"""Events other people just added to calendars shared with the user: what the arrival banners show.

An event counts when it was created after Calendary started, in a calendar the user does not own, by someone who
is not one of the signed-in accounts (docs/verification/arrivals.md). Not for invitations into the user's own
calendars, for anything added before the start, or for storing what was announced across runs.
"""
import json
from datetime import datetime, timezone

from calendary.cache import event_key

# More new events than this from one calendar in one sync become one summary banner.
LIMIT = 3


def created_at(item):
    """When the item was created, or None when the source does not say or gives no time zone."""
    try:
        stamp = datetime.fromisoformat(item["created"])
    except (KeyError, TypeError, ValueError):
        return None
    return stamp if stamp.tzinfo else None


def news(rows, since, own, writable):
    """The rows to announce, earliest first and one per series: created after `since` by someone not in `own`.

    In a calendar the user can write to, an event without a named creator might be the user's own and is skipped.
    """
    found, series = [], set()
    for row in sorted(rows, key=lambda r: r["start"]):
        item = json.loads(row["raw"])
        who = item.get("creator") or {}
        email = (who.get("email") or "").lower()
        created = created_at(item)
        if created is None or created < since or who.get("self") or email in own:
            continue
        if writable and not email and not who.get("displayName"):
            continue
        key = item.get("recurringEventId") or item["id"]
        if key not in series:
            series.add(key)
            found.append(dict(row, who=who.get("displayName") or email, series=key))
    return found


class Arrivals:
    """Remembers which calendars are shared and what was announced; the bridge emits what `check` returns."""

    def __init__(self):
        self.since = datetime.now(timezone.utc)
        self.shared = {}
        self.seen = set()

    def calendars(self, account, items):
        """The account's calendar list: {calendar id: writable} of those shared with the user."""
        self.shared[account] = {c["id"]: bool(c["writable"]) for c in items if c.get("shared")}

    def check(self, account, calendar, rows, own):
        """Banners for the new rows of one fetched calendar = (id, name, color); own = the user's addresses."""
        calendar_id, name, color = calendar
        if calendar_id not in self.shared.get(account, {}):
            return []
        fresh = [row for row in news(rows, self.since, own, self.shared[account][calendar_id])
                 if event_key(account, calendar_id, row["series"]) not in self.seen]
        self.seen.update(event_key(account, calendar_id, row["series"]) for row in fresh)
        banners = [{"title": row["title"], "start": row["start"], "end": row["end"], "allDay": bool(row["all_day"]),
                    "who": row["who"], "calendar": name, "color": color, "count": 1} for row in fresh]
        if len(banners) > LIMIT:
            names = {banner["who"] for banner in banners}
            return [dict(banners[0], title="%d neue Termine" % len(banners), count=len(banners),
                         who=names.pop() if len(names) == 1 else "")]
        return banners
