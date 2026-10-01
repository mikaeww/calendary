"""An iCloud account over CalDAV with the methods and event shape of google.Account (ADR 0005).

Events are Google-shaped dicts; ids are resource URLs, instances of a series `<url>#<recurrence id>`. Single
instances of a series and new recurring events are refused with a message. Not for sign-in UI or storage.
"""
import threading
import uuid
from datetime import datetime, timezone
from urllib.parse import urljoin

from calendary.caldav import ical
from calendary.caldav.dav import NS, Dav, tag
from calendary.caldav.recurrence import expand
from calendary.errors import ServiceError
from calendary.language import tr

ROOT = "https://caldav.icloud.com/"
DOMAIN = "icloud.com"
PREFIX = "icloud:"
CALENDAR_PROPS = ["d:resourcetype", "d:displayname", "a:calendar-color", "c:supported-calendar-component-set",
                  "d:current-user-privilege-set"]
QUERY = ('<?xml version="1.0" encoding="utf-8"?><c:calendar-query xmlns:d="DAV:" xmlns:c="%s" xmlns:cs="%s">'
         '<d:prop><d:getetag/><c:calendar-data/><cs:created-by/></d:prop><c:filter><c:comp-filter name="VCALENDAR">'
         '<c:comp-filter name="VEVENT"><c:time-range start="%%s" end="%%s"/></c:comp-filter></c:comp-filter>'
         "</c:filter></c:calendar-query>" % (NS["c"], NS["cs"]))


def account_key(apple_id):
    """How the cache names an iCloud account; the prefix keeps it apart from a Google account with the same address."""
    return PREFIX + apple_id.strip().lower()


def is_icloud(key):
    return key.startswith(PREFIX)


def apple_id_of(key):
    return key[len(PREFIX):]


def series_refused():
    return ServiceError(tr("Serien aus iCloud lassen sich in Calendary noch nicht bearbeiten, bitte am Handy ändern"))


def first_href(results, name):
    for base, props in results:
        element = props.get(tag(name))
        found = element.findtext("d:href", None, NS) if element is not None else None
        if found:
            return urljoin(base, found.strip())
    raise ServiceError(tr("iCloud hat kein %s geliefert") % name.split(":")[1])


def calendar_entry(href, props):
    """The calendar list entry of one collection, or None when it holds no events."""
    kind = props.get(tag("d:resourcetype"))
    if kind is None or kind.find("c:calendar", NS) is None:
        return None
    components = props.get(tag("c:supported-calendar-component-set"))
    if components is not None and not any(c.get("name") == "VEVENT" for c in components.findall("c:comp", NS)):
        return None
    privileges = props.get(tag("d:current-user-privilege-set"))
    writable = privileges is None or any(privileges.find(".//d:" + p, NS) is not None
                                         for p in ("write", "write-content", "all"))
    color = props.get(tag("a:calendar-color"))
    name = props.get(tag("d:displayname"))
    # A collection someone else shares carries CS:shared; a read-only one in the user's home is shared as well.
    shared = kind.find("cs:shared", NS) is not None or not writable
    return {"id": href, "name": (name.text if name is not None and name.text else href.rstrip("/").rsplit("/", 1)[-1]),
            "color": (color.text or "#888888")[:7] if color is not None else "#888888",
            "writable": int(writable), "main": 0, "shared": int(shared)}


def created_by(element):
    """Google's `creator` shape from CalendarServer's created-by property, or None when the server does not say."""
    if element is None:
        return None
    name = " ".join(part for part in (element.findtext("cs:first-name", "", NS).strip(),
                                      element.findtext("cs:last-name", "", NS).strip()) if part)
    address = element.findtext("d:href", "", NS).strip()
    email = address[len("mailto:"):] if address.lower().startswith("mailto:") else ""
    return {"displayName": name, "email": email} if name or email else None


def utc(stamp):
    return datetime.fromisoformat(stamp).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


class ICloudAccount:
    """Same surface as google.Account: calendars, events, insert, patch, move, delete, plus verify for sign-in."""

    def __init__(self, apple_id, password, root=ROOT, domain=DOMAIN):
        self.email = account_key(apple_id)
        self.dav = Dav(apple_id.strip(), password, domain)
        self.root = root
        self.home = None
        self.lock = threading.Lock()

    def calendar_home(self):
        with self.lock:
            if not self.home:
                principal = first_href(self.dav.propfind(self.root, ["d:current-user-principal"]),
                                       "d:current-user-principal")
                self.home = first_href(self.dav.propfind(principal, ["c:calendar-home-set"]), "c:calendar-home-set")
            return self.home

    def verify(self):
        """Signs in once against the server; raises ServiceError with the reason when it does not work."""
        self.calendar_home()

    def calendars(self):
        results = self.dav.propfind(self.calendar_home(), CALENDAR_PROPS, depth=1)
        return [entry for entry in (calendar_entry(href, props) for href, props in results) if entry]

    def events(self, calendar, window):
        """Instances overlapping window = (start, end) as RFC 3339; an unreadable resource comes back without a
        start, so the sync counts it as skipped instead of losing the whole calendar."""
        span = (datetime.fromisoformat(window[0]), datetime.fromisoformat(window[1]))
        items = []
        for href, props in self.dav.report(calendar, QUERY % (utc(window[0]), utc(window[1]))):
            data = props.get(tag("c:calendar-data"))
            if data is None or not data.text:
                continue
            try:
                found = expand(ical.events(data.text), href, span)
            except (ValueError, KeyError):
                items.append({"id": href})
                continue
            creator = created_by(props.get(tag("cs:created-by")))
            items += [dict(item, creator=creator) if creator else item for item in found]
        return items

    def insert(self, calendar, body):
        if body.get("recurrence"):
            raise ServiceError(tr("Wiederholungen lassen sich in iCloud-Kalendern noch nicht anlegen"))
        uid = "%s@calendary" % uuid.uuid4()
        url = calendar.rstrip("/") + "/" + uid + ".ics"
        self.dav.put(url, ical.new_event(uid, body), {"If-None-Match": "*"})
        return dict(body, id=url)

    def stored(self, event):
        """(text, etag) of a single event; series and their instances are refused."""
        if "#" in event:
            raise series_refused()
        text, etag = self.dav.get(event)
        vevents = ical.events(text)
        if len(vevents) != 1 or any(key in ("RRULE", "RDATE") for key, _, _ in vevents[0]["props"]):
            raise series_refused()
        return text, etag

    def patch(self, calendar, event, body):
        text, etag = self.stored(event)
        self.dav.put(event, ical.edit_event(text, body), {"If-Match": etag} if etag else {})
        return dict(body, id=event)

    def move(self, calendar, event, destination):
        """Copies the resource into the other calendar, then deletes the original; returns the new id."""
        text, etag = self.stored(event)
        url = destination.rstrip("/") + "/" + event.rstrip("/").rsplit("/", 1)[-1]
        self.dav.put(url, text, {"If-None-Match": "*"})
        self.dav.delete(event, etag)
        return {"id": url}

    def delete(self, calendar, event):
        self.stored(event)
        self.dav.delete(event)
