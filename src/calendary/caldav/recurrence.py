"""The events of one CalDAV resource inside a window, as Google-shaped items: series expanded locally (ADR 0005).

RRULE, RDATE and EXDATE come from the master VEVENT; a VEVENT with RECURRENCE-ID replaces its instance, also when
it was moved into or out of the window. Not for reading iCalendar text (ical.py).
"""
from datetime import date, datetime, timezone

from dateutil.rrule import rruleset, rrulestr

from calendary.caldav.ical import moment, prop, span, text


def is_day(value):
    return isinstance(value, date) and not isinstance(value, datetime)


def google_time(value):
    return {"date": value.isoformat()} if is_day(value) else {"dateTime": value.isoformat()}


def comparable(value):
    """Days as local midnight, so dates and times compare against the same aware window."""
    return datetime(value.year, value.month, value.day).astimezone() if is_day(value) else value


def instance_key(value):
    """How a RECURRENCE-ID names an instance: its date, or its start as UTC."""
    if is_day(value):
        return value.strftime("%Y%m%d")
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def item(component, times, ident, series=None):
    """Google's event shape for one instance; times = (start, end)."""
    result = {"id": ident, "summary": text(component, "SUMMARY"), "location": text(component, "LOCATION"),
              "description": text(component, "DESCRIPTION"), "start": google_time(times[0]),
              "end": google_time(times[1])}
    if series:
        result["recurringEventId"] = series
    params, created = prop(component, "CREATED")
    try:
        if created:
            result["created"] = moment(params, created).isoformat()
    except ValueError:
        # Only the arrival banner reads it; an event with a broken CREATED stays readable, it is just never announced.
        pass
    return result


def cancelled(component):
    return (prop(component, "STATUS")[1] or "").upper() == "CANCELLED"


def overlaps(times, window):
    start, end = comparable(times[0]), comparable(times[1])
    if start == end:
        return window[0] <= start < window[1]
    return start < window[1] and end > window[0]


def dates_of(component, name):
    """Every value of every `name` property; each may hold a comma-separated list."""
    return [moment(params, value) for key, params, value in component["props"] if key == name
            for value in value.split(",")]


def occurrences(master, window):
    """Starts of the master's instances that can overlap the window."""
    start, end = span(master)
    length = end - start
    anchor = datetime(start.year, start.month, start.day) if is_day(start) else start
    rules = rruleset()
    for key, _, value in master["props"]:
        if key == "RRULE":
            rules.rrule(rrulestr(value, dtstart=anchor))
    for extra in dates_of(master, "RDATE"):
        rules.rdate(datetime(extra.year, extra.month, extra.day) if is_day(extra) else extra)
    for skip in dates_of(master, "EXDATE"):
        rules.exdate(datetime(skip.year, skip.month, skip.day) if is_day(skip) else skip)
    low, high = window[0] - length, window[1]
    if is_day(start):
        low, high = low.replace(tzinfo=None), high.replace(tzinfo=None)
    found = rules.between(low, high, inc=True)
    return [(f.date(), f.date() + length) if is_day(start) else (f, f + length) for f in found]


def expand(vevents, href, window):
    """Google-shaped items of one resource overlapping window = (aware start, aware end)."""
    master = next((v for v in vevents if prop(v, "RECURRENCE-ID")[1] is None), None)
    overrides = {instance_key(moment(*prop(v, "RECURRENCE-ID"))): v for v in vevents if v is not master}
    recurring = master is not None and any(key in ("RRULE", "RDATE") for key, _, _ in master["props"])
    items = []
    if master is not None and not cancelled(master):
        if not recurring:
            times = span(master)
            if overlaps(times, window):
                items.append(item(master, times, href))
        else:
            for times in occurrences(master, window):
                key = instance_key(times[0])
                if key not in overrides and overlaps(times, window):
                    items.append(item(master, times, href + "#" + key, href))
    for key, override in overrides.items():
        times = span(override)
        if not cancelled(override) and overlaps(times, window):
            items.append(item(override, times, href + "#" + key, href))
    return items
