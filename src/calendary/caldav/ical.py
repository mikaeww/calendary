"""iCalendar (RFC 5545) as far as Calendary needs it: read components and times, write and edit single events.

Reading returns plain structures; writing changes the stored text in place so properties Calendary does not know
(alarms, attendees, anything vendor-specific) survive an edit. Not for recurrence (see recurrence.py).
"""
import re
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

OWN = ("DTSTART", "DTEND", "DURATION", "SUMMARY", "LOCATION", "DESCRIPTION", "DTSTAMP", "LAST-MODIFIED")


def unfold(text):
    """Logical lines: a line break followed by a space or tab continues the previous line (RFC 5545 3.1)."""
    return [line for line in re.sub(r"\r?\n[ \t]", "", text).splitlines() if line]


def fold(line):
    """Content lines of at most 75 octets, broken between UTF-8 characters."""
    parts, current = [], ""
    for char in line:
        limit = 75 if not parts else 74
        if len((current + char).encode()) > limit:
            parts.append(current)
            current = char
        else:
            current += char
    parts.append(current)
    return "\r\n ".join(parts)


def split_line(line):
    """(NAME, {PARAM: value}, value); colons and semicolons inside quoted parameters do not split."""
    inside, cut = False, None
    for i, char in enumerate(line):
        if char == '"':
            inside = not inside
        elif char == ":" and not inside:
            cut = i
            break
    if cut is None:
        raise ValueError("iCalendar line without value: %r" % line[:40])
    parts = re.findall(r'(?:[^;"]|"[^"]*")+', line[:cut])
    params = {}
    for part in parts[1:]:
        key, _, value = part.partition("=")
        params[key.upper()] = value.strip('"')
    return parts[0].upper(), params, line[cut + 1:]


def components(text):
    """The component tree: {"name", "props": [(name, params, value)], "children": [...]}."""
    root = {"name": "", "props": [], "children": []}
    stack = [root]
    for line in unfold(text):
        name, params, value = split_line(line)
        if name == "BEGIN":
            child = {"name": value.upper(), "props": [], "children": []}
            stack[-1]["children"].append(child)
            stack.append(child)
        elif name == "END":
            if len(stack) == 1 or stack[-1]["name"] != value.upper():
                raise ValueError("iCalendar END:%s does not close %s" % (value, stack[-1]["name"] or "anything"))
            stack.pop()
        else:
            stack[-1]["props"].append((name, params, value))
    return root["children"]


def events(text):
    """Every VEVENT in a calendar object."""
    return [child for calendar in components(text) for child in calendar["children"] if child["name"] == "VEVENT"]


def prop(component, name):
    """(params, value) of the first property called `name`, or (None, None)."""
    return next(((params, value) for key, params, value in component["props"] if key == name), (None, None))


def unescape(value):
    return re.sub(r"\\([\\;,nN])", lambda m: "\n" if m.group(1) in "nN" else m.group(1), value)


def escape(value):
    return value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\r\n", "\n").replace("\n", "\\n")


def zone(tzid):
    # A TZID is usually an Olson name; some servers prefix it with a slash or a vendor path, so try every tail.
    parts = tzid.strip().strip("/").split("/")
    for candidate in ("/".join(parts[i:]) for i in range(len(parts))):
        try:
            return ZoneInfo(candidate)
        except (ZoneInfoNotFoundError, ValueError):
            continue
    raise ValueError("unknown TZID %r" % tzid)


def moment(params, value):
    """A `date` for all-day values, an aware `datetime` otherwise; floating times are taken as local time."""
    if (params or {}).get("VALUE") == "DATE" or re.fullmatch(r"\d{8}", value):
        return datetime.strptime(value, "%Y%m%d").date()
    stamp = datetime.strptime(value.rstrip("Z"), "%Y%m%dT%H%M%S")
    if value.endswith("Z"):
        return stamp.replace(tzinfo=timezone.utc)
    if params and "TZID" in params:
        return stamp.replace(tzinfo=zone(params["TZID"]))
    return stamp.astimezone()


def duration(value):
    """RFC 5545 3.3.6 durations such as P1D, PT1H30M, -PT15M, P2W."""
    match = re.fullmatch(r"([+-])?P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?", value)
    if not match or not any(match.groups()[1:]):
        raise ValueError("unknown DURATION %r" % value)
    sign = -1 if match.group(1) == "-" else 1
    weeks, days, hours, minutes, seconds = (int(g or 0) for g in match.groups()[1:])
    return sign * timedelta(weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)


def span(component):
    """(start, end) of a VEVENT; without DTEND or DURATION it lasts one day (dates) or no time (date-times)."""
    params, value = prop(component, "DTSTART")
    if value is None:
        raise ValueError("VEVENT without DTSTART")
    start = moment(params, value)
    end_params, end_value = prop(component, "DTEND")
    if end_value is not None:
        return start, moment(end_params, end_value)
    _, length = prop(component, "DURATION")
    if length is not None:
        return start, start + duration(length)
    return start, start + timedelta(days=1) if isinstance(start, date) and not isinstance(start, datetime) else start


def text(component, name):
    _, value = prop(component, name)
    return unescape(value) if value is not None else ""


def time_value(name, value):
    """A DTSTART/DTEND line from Google's shape ({"date"} or {"dateTime"}); timed values are written in UTC."""
    if "date" in value:
        return "%s;VALUE=DATE:%s" % (name, value["date"].replace("-", ""))
    stamp = datetime.fromisoformat(value["dateTime"]).astimezone(timezone.utc)
    return "%s:%s" % (name, stamp.strftime("%Y%m%dT%H%M%SZ"))


def own_lines(body):
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["DTSTAMP:" + now, "LAST-MODIFIED:" + now, time_value("DTSTART", body["start"]),
             time_value("DTEND", body["end"]), "SUMMARY:" + escape(body.get("summary", ""))]
    lines += ["%s:%s" % (name, escape(body[key])) for name, key in (("LOCATION", "location"),
                                                                    ("DESCRIPTION", "description")) if body.get(key)]
    return lines


def new_event(uid, body):
    """A calendar object with one VEVENT for Google's event shape; recurrence is not written (ADR 0005)."""
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Calendary//Calendary//DE", "BEGIN:VEVENT", "UID:" + uid]
    lines += own_lines(body) + ["END:VEVENT", "END:VCALENDAR"]
    return "\r\n".join(fold(line) for line in lines) + "\r\n"


def edit_event(stored, body):
    """The stored calendar object with Calendary's own properties of its one VEVENT replaced, everything else kept."""
    lines, out, depth, done, sequence = unfold(stored), [], 0, False, 0
    for line in lines:
        name, _, value = split_line(line)
        if name == "BEGIN":
            depth += 1 if value.upper() == "VEVENT" or depth else 0
        in_event = depth == 1 and not done
        if in_event and name == "SEQUENCE":
            sequence = int(value) + 1 if value.isdigit() else 1
            continue
        if in_event and name in OWN:
            continue
        if in_event and name == "END" and value.upper() == "VEVENT":
            out += own_lines(body) + ["SEQUENCE:%d" % sequence]
            done = True
        if name == "END" and depth:
            depth -= 1
        out.append(line)
    if not done:
        raise ValueError("stored calendar object has no VEVENT")
    return "\r\n".join(fold(line) for line in out) + "\r\n"
