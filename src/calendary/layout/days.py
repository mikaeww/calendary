"""Local day boundaries and the overlap rule every layout shares. Not for formatting dates."""
from datetime import timedelta

from calendary.cache.events import local, midnight

DAY_MS = 86400000


def day_edges(start, days):
    """Local midnights from the day of `start` on, days + 1 of them; days are not assumed to be 24 hours."""
    first = local(start).date()
    return [midnight(first + timedelta(days=i)) for i in range(days + 1)]


def on_day(event, begin, end):
    """Whether the event touches [begin, end); a zero-length event only on the day it starts."""
    if event["end"] == event["start"]:
        return begin <= event["start"] < end
    return event["start"] < end and event["end"] > begin


def is_long(event):
    """All-day events and events of a day or more go in the all-day strip."""
    return event["allDay"] or event["end"] - event["start"] >= DAY_MS
