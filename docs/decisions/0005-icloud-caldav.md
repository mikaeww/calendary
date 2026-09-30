# 0005: iCloud calendars over CalDAV

**Status:** accepted
**Date:** 2026-09-30

## Context
The owner's phone shows a calendar shared through iCloud by a friend. Google cannot see it, and the vision
excluded other providers. The owner decided to add iCloud with live, editable access.

## Options
- Ask the owner of the calendar to publish it and subscribe to the public link in Google: read-only, hours of
  delay, and the calendar becomes readable by anyone with the link.
- CalDAV against iCloud with the Apple ID and an app-specific password: live, editable where the share allows it.

## Decision
CalDAV, with iCloud as the only CalDAV server for now. Sign-in takes the Apple ID and an app-specific password,
checked against the server before anything is stored; the password goes to the Secret Service
(`service=calendary-icloud account=<apple id>`). iCloud accounts are keyed `icloud:<apple id>` so the same address
can also be a Google account.

The CalDAV account speaks the same event shape as the Google one (Google's event resource), so the cache, layout,
bridge and interface stay provider-neutral. Recurring events are expanded locally with `python-dateutil` (already
installed, BSD/Apache licensed): calendar-query with a time range returns whole series, and server-side expansion
is not relied on.

## Consequences
- New dependency `python-dateutil`, only for RRULE, RDATE and EXDATE expansion.
- Edits of single instances of an iCloud series are refused with a message; the whole event is edited through
  the series owner. Non-recurring iCloud events can be created, changed, moved between calendars and deleted.
- Edits keep every property Calendary does not know (alarms, attendees) by changing the stored iCalendar text in
  place instead of rewriting it.
