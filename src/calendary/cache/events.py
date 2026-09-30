"""Google event resources as cache rows and back, and the key that names an event across accounts.

Times are epoch milliseconds. All-day events run from local midnight to the local midnight after their last day,
the exclusive end the Calendar API uses for `end.date`. Not for storage or layout.
"""
import json
from datetime import date, datetime, timedelta

KEY_SEPARATOR = "\n"


def ms(moment):
    return int(moment.timestamp() * 1000)


def local(millis):
    return datetime.fromtimestamp(millis / 1000).astimezone()


def midnight(day):
    """Local midnight of a date, as milliseconds."""
    return ms(datetime(day.year, day.month, day.day).astimezone())


def event_key(account, calendar, event=None):
    """One string for QML: account, calendar and optionally the event id. Google ids never contain a newline."""
    return KEY_SEPARATOR.join(part for part in (account, calendar, event) if part)


def split_key(key):
    return key.split(KEY_SEPARATOR)


def parse_event(item):
    """A Google event resource as a row, or None for a cancelled instance."""
    if item.get("status") == "cancelled":
        return None
    start, end = item.get("start", {}), item.get("end", {})
    all_day = "date" in start
    if all_day:
        first = date.fromisoformat(start["date"])
        after = date.fromisoformat(end["date"]) if "date" in end else first + timedelta(days=1)
        begin, finish = midnight(first), midnight(after)
    elif "dateTime" in start:
        begin = ms(datetime.fromisoformat(start["dateTime"]))
        finish = ms(datetime.fromisoformat(end["dateTime"])) if "dateTime" in end else begin
    else:
        raise ValueError("event %s has neither start.date nor start.dateTime" % item.get("id", "?"))
    return {"id": item["id"], "start": begin, "end": max(finish, begin), "all_day": int(all_day),
            "title": item.get("summary") or "", "location": item.get("location") or "",
            "notes": item.get("description") or "",
            "recurring": int(bool(item.get("recurringEventId") or item.get("recurrence"))),
            "raw": json.dumps(item)}


def to_google(fields):
    """The request body for an event edited in the app: title, location, notes, start, end, allDay, repeat."""
    body = {"summary": fields.get("title", ""), "location": fields.get("location", ""),
            "description": fields.get("notes", "")}
    start, end = int(fields["start"]), int(fields["end"])
    if fields.get("allDay"):
        first = local(start).date()
        last = max(first + timedelta(days=1), local(end).date())
        body["start"], body["end"] = {"date": first.isoformat()}, {"date": last.isoformat()}
    else:
        body["start"] = {"dateTime": local(start).isoformat()}
        body["end"] = {"dateTime": local(max(end, start)).isoformat()}
    if fields.get("repeat"):
        body["recurrence"] = ["RRULE:FREQ=" + fields["repeat"]]
    return body


def event_dict(row):
    """What QML gets for one event."""
    return {"key": event_key(row["account"], row["calendar"], row["id"]),
            "calendarKey": event_key(row["account"], row["calendar"]),
            "title": row["title"], "start": row["start"], "end": row["end"], "allDay": bool(row["all_day"]),
            "location": row["location"], "notes": row["notes"], "recurring": bool(row["recurring"]),
            "color": row["color"], "calendar": row["calendar_name"], "writable": bool(row["writable"])}
