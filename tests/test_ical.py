"""docs/verification/caldav.md claims 1-3: iCalendar reading, write/read round trips, RFC 5545 recurrence examples."""
import os
import time
import unittest
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from calendary import cache
from calendary.caldav import ical
from calendary.caldav.recurrence import expand

NEW_YORK = ZoneInfo("America/New_York")
_saved_tz = None


def setUpModule():
    global _saved_tz
    _saved_tz = os.environ.get("TZ")
    os.environ["TZ"] = "Europe/Berlin"
    time.tzset()


def tearDownModule():
    if _saved_tz is None:
        os.environ.pop("TZ", None)
    else:
        os.environ["TZ"] = _saved_tz
    time.tzset()


def calendar(*vevents):
    return "BEGIN:VCALENDAR\r\nVERSION:2.0\r\n" + "".join(
        "BEGIN:VEVENT\r\n" + body.strip().replace("\n", "\r\n") + "\r\nEND:VEVENT\r\n" for body in vevents) + "END:VCALENDAR\r\n"


def window(first, last):
    return (datetime(*first, tzinfo=timezone.utc), datetime(*last, tzinfo=timezone.utc))


def local_starts(items, zone):
    return [datetime.fromisoformat(i["start"]["dateTime"]).astimezone(zone).strftime("%Y-%m-%d %H:%M") for i in items]


class ReadingTest(unittest.TestCase):
    def test_folding_escaping_and_times(self):
        text = calendar("""UID:a
DTSTART;TZID=Europe/Berlin:20261006T085000
DTEND;TZID=Europe/Berlin:20261006T095000
SUMMARY:Gespräch\\, Kunde\\; mit Unterlagen
LOCATION:Bitterfelder Str. 1
DESCRIPTION:Erste Zeile\\nzweite Zeile mit einer sehr langen Beschreibung, die über mehrere g
 efaltete Zeilen läuft""")
        event = ical.events(text)[0]
        self.assertEqual(ical.text(event, "SUMMARY"), "Gespräch, Kunde; mit Unterlagen")
        self.assertEqual(ical.text(event, "DESCRIPTION"), "Erste Zeile\nzweite Zeile mit einer sehr langen Beschreibung, "
                                                          "die über mehrere gefaltete Zeilen läuft")
        start, end = ical.span(event)
        self.assertEqual((start.isoformat(), end - start), ("2026-10-06T08:50:00+02:00", timedelta(hours=1)))

    def test_value_kinds(self):
        self.assertEqual(ical.moment({"VALUE": "DATE"}, "20261003"), date(2026, 10, 3))
        self.assertEqual(ical.moment({}, "20261003T070000Z"), datetime(2026, 10, 3, 7, tzinfo=timezone.utc))
        floating = ical.moment({}, "20261003T090000")
        self.assertEqual((floating.hour, floating.utcoffset()), (9, timedelta(hours=2)))
        self.assertEqual(ical.moment({"TZID": "/mozilla.org/20050126_1/Europe/Berlin"}, "20260101T120000").utcoffset(),
                         timedelta(hours=1))
        with self.assertRaises(ValueError):
            ical.moment({"TZID": "Mars/Olympus"}, "20260101T120000")

    def test_duration_and_defaults(self):
        self.assertEqual(ical.duration("PT1H30M"), timedelta(minutes=90))
        self.assertEqual(ical.duration("-P1W2D"), -timedelta(days=9))
        for bad in ("P", "-PT", "1H", "PT1X"):
            with self.assertRaises(ValueError):
                ical.duration(bad)
        day = ical.events(calendar("UID:d\nDTSTART;VALUE=DATE:20261003"))[0]
        self.assertEqual(ical.span(day), (date(2026, 10, 3), date(2026, 10, 4)))
        timed = ical.events(calendar("UID:t\nDTSTART:20261003T070000Z\nDURATION:PT45M"))[0]
        self.assertEqual(ical.span(timed)[1] - ical.span(timed)[0], timedelta(minutes=45))

    def test_cancelled_and_broken(self):
        text = calendar("UID:c\nDTSTART:20261003T070000Z\nDTEND:20261003T080000Z\nSTATUS:CANCELLED")
        self.assertEqual(expand(ical.events(text), "https://x/c.ics", window((2026, 1, 1), (2027, 1, 1))), [])
        with self.assertRaises(ValueError):
            ical.events("BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nEND:VCALENDAR\r\n")


class RoundTripTest(unittest.TestCase):
    def test_written_events_read_back_every_day(self):
        span, checked = window((2019, 12, 1), (2036, 2, 1)), 0
        day = date(2020, 1, 1)
        while day <= date(2035, 12, 31):
            midnight = int(datetime(day.year, day.month, day.day).astimezone().timestamp() * 1000)
            for fields in ({"allDay": True, "start": midnight, "end": midnight + 86400000 * 2},
                           {"start": midnight + 150 * 60000, "end": midnight + 225 * 60000}):
                body = cache.to_google(dict(fields, title="Termin, mit; Zeichen", location="Ort", notes="a\nb"))
                items = expand(ical.events(ical.new_event("u", body)), "https://x/u.ics", span)
                row = cache.parse_event(items[0])
                expected = cache.parse_event(dict(body, id="https://x/u.ics"))
                self.assertEqual({k: row[k] for k in ("start", "end", "all_day", "title", "location", "notes")},
                                 {k: expected[k] for k in ("start", "end", "all_day", "title", "location", "notes")})
                checked += 1
            day += timedelta(days=1)
        self.assertEqual(checked, 5844 * 2)

    def test_edit_keeps_unknown_properties(self):
        stored = calendar("""UID:keep
DTSTART:20261003T070000Z
DTEND:20261003T080000Z
SUMMARY:Alt
SEQUENCE:2
ATTENDEE;CN="Alex, A.":mailto:alex@example.com
BEGIN:VALARM
ACTION:DISPLAY
DESCRIPTION:Erinnerung
TRIGGER:-PT15M
END:VALARM""")
        body = cache.to_google({"title": "Neu", "start": 1790830800000, "end": 1790834400000})
        edited = ical.edit_event(stored, body)
        event = ical.events(edited)[0]
        self.assertEqual((ical.text(event, "SUMMARY"), ical.prop(event, "SEQUENCE")[1]), ("Neu", "3"))
        self.assertEqual(ical.prop(event, "ATTENDEE")[0]["CN"], "Alex, A.")
        alarm = event["children"][0]
        self.assertEqual((alarm["name"], ical.text(alarm, "DESCRIPTION")), ("VALARM", "Erinnerung"))
        self.assertTrue(all(len(line.encode()) <= 75 for line in edited.split("\r\n")))


class RecurrenceTest(unittest.TestCase):
    """Expected dates are the ones printed in RFC 5545 section 3.8.5.3."""

    def series(self, rule, start="19970902T090000", extra=""):
        text = calendar("UID:s\nDTSTART;TZID=America/New_York:%s\nDURATION:PT1H\nRRULE:%s\n%s" % (start, rule, extra))
        return expand(ical.events(text), "https://x/s.ics", window((1997, 1, 1), (1999, 1, 1)))

    def test_daily_for_ten_occurrences(self):
        starts = local_starts(self.series("FREQ=DAILY;COUNT=10"), NEW_YORK)
        self.assertEqual(starts, ["1997-09-%02d 09:00" % d for d in range(2, 12)])

    def test_every_other_week_across_the_dst_change(self):
        items = self.series("FREQ=WEEKLY;INTERVAL=2;UNTIL=19971224T000000Z;WKST=SU;BYDAY=MO,WE,FR", "19970901T090000")
        days = {"09": [1, 3, 5, 15, 17, 19, 29], "10": [1, 3, 13, 15, 17, 27, 29, 31], "11": [10, 12, 14, 24, 26, 28],
                "12": [8, 10, 12, 22]}
        expected = ["1997-%s-%02d 09:00" % (month, d) for month, ds in days.items() for d in ds]
        self.assertEqual(sorted(local_starts(items, NEW_YORK)), expected)

    def test_monthly_first_friday(self):
        items = self.series("FREQ=MONTHLY;COUNT=10;BYDAY=1FR", "19970905T090000")
        expected = ["1997-09-05", "1997-10-03", "1997-11-07", "1997-12-05", "1998-01-02", "1998-02-06", "1998-03-06",
                    "1998-04-03", "1998-05-01", "1998-06-05"]
        self.assertEqual(local_starts(items, NEW_YORK), [d + " 09:00" for d in expected])

    def test_exdate_and_overrides(self):
        text = calendar(
            "UID:w\nDTSTART;TZID=Europe/Berlin:20261005T100000\nDTEND;TZID=Europe/Berlin:20261005T110000\n"
            "SUMMARY:Serie\nRRULE:FREQ=WEEKLY;COUNT=4\nEXDATE;TZID=Europe/Berlin:20261012T100000",
            "UID:w\nRECURRENCE-ID;TZID=Europe/Berlin:20261019T100000\nDTSTART;TZID=Europe/Berlin:20261020T150000\n"
            "DTEND;TZID=Europe/Berlin:20261020T160000\nSUMMARY:Verschoben",
            "UID:w\nRECURRENCE-ID;TZID=Europe/Berlin:20261026T100000\nDTSTART;TZID=Europe/Berlin:20261026T100000\n"
            "DTEND;TZID=Europe/Berlin:20261026T110000\nSTATUS:CANCELLED")
        items = expand(ical.events(text), "https://x/w.ics", window((2026, 10, 1), (2026, 11, 1)))
        berlin = ZoneInfo("Europe/Berlin")
        self.assertEqual([(s, i["summary"]) for s, i in zip(local_starts(items, berlin), items)],
                         [("2026-10-05 10:00", "Serie"), ("2026-10-20 15:00", "Verschoben")])
        self.assertTrue(all(i["recurringEventId"] == "https://x/w.ics" for i in items))
        self.assertEqual(items[1]["id"], "https://x/w.ics#20261019T080000Z")

    def test_override_moved_into_the_window(self):
        text = calendar(
            "UID:m\nDTSTART;VALUE=DATE:20260105\nRRULE:FREQ=YEARLY\nSUMMARY:Geburtstag",
            "UID:m\nRECURRENCE-ID;VALUE=DATE:20270105\nDTSTART;VALUE=DATE:20261230\nSUMMARY:Vorgezogen")
        items = expand(ical.events(text), "https://x/m.ics", window((2026, 12, 20), (2027, 1, 3)))
        self.assertEqual([(i["start"], i["summary"]) for i in items], [({"date": "2026-12-30"}, "Vorgezogen")])


if __name__ == "__main__":
    unittest.main()
