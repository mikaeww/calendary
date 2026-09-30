# Verification plan: iCloud over CalDAV

Component: `src/calendary/caldav/`.

## Claims
1. iCalendar text is read correctly: folded lines, escaped text, `DATE` and `DATE-TIME` values in UTC, with `TZID`
   or floating; `DTEND` or `DURATION`; cancelled instances are dropped.
2. Every event Calendary writes reads back with the same start, end, all-day flag, title, location and notes,
   including days on which daylight saving time changes.
3. Recurring events expand to exactly the instances RFC 5545 lists for its RRULE examples, minus `EXDATE`, with
   `RECURRENCE-ID` overrides replacing their instance, including overrides moved into or out of the window.
4. Discovery finds the calendar home and every event calendar with name, colour and write permission; task-only
   collections are skipped.
5. Creating, changing, moving and deleting a non-recurring event send the right requests with `If-Match` /
   `If-None-Match`, and changing an event keeps properties Calendary does not know (for example `VALARM`).
6. A wrong Apple ID or password is reported as such and nothing is stored.

## Oracle
- Claims 1, 2: RFC 5545 (sections 3.1, 3.3.5, 3.3.11, 3.8.2) and `zoneinfo`.
- Claim 3: the explicit dates in the RRULE examples of RFC 5545 section 3.8.5.3.
- Claims 4 to 6: a fake CalDAV server over real HTTP that answers like iCloud and records every request.
- Real iCloud: manual check with the owner's Apple ID.

## Method
Example tests for claims 1, 4, 5, 6; exhaustive round trip over every day of 2020-2035 in Europe/Berlin for
claim 2; RFC examples for claim 3.

## Thresholds
All pass; 100 % of the round trips agree.

## Known gaps
- Single instances of an iCloud series cannot be edited or deleted from Calendary (refused with a message).
- A `TZID` that zoneinfo does not know is not guessed: the event is skipped and counted in the notice.

## Results (2026-09-30, `tests/test_ical.py`, `tests/test_icloud.py`, `tests/test_bridge.py`)
- Claim 1: passes (folding, escaping, DATE, UTC, TZID including a vendor-prefixed one, floating, DURATION,
  cancelled, malformed).
- Claim 2: 11 688 written events over every day of 2020-2035 in Europe/Berlin read back identical.
- Claim 3: three RFC 5545 examples (daily, bi-weekly across the October DST change, monthly first Friday) match the
  RFC's dates exactly; EXDATE, a moved override, a cancelled override and an override moved into the window pass.
- Claims 4 to 6: pass against the fake server over HTTPS; wrong password, a redirect to a foreign host and plain
  HTTP are refused; the password reaches the keyring only after a successful sign-in, in Apple's dashed form.
- Real iCloud: not yet done.
