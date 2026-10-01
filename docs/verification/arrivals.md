# Verification plan: arrival banners

Component: `src/calendary/bridge/arrivals.py`, `src/calendary/qml/arrivals/Arrivals.qml`.

While Calendary runs it syncs every minute. When someone else adds an event to a calendar shared with the user,
a small banner at the top right says what was added, when it takes place and who added it.

## Claims
1. Only calendars shared with the user count: Google calendars whose `accessRole` is not `owner`, iCloud
   collections marked `CS:shared` or without write access.
2. Only events created after Calendary started count (`created` from Google, `CREATED` from iCalendar). The first
   sync, paging to another month and events from before the start are never announced; an event without a
   creation time is never announced.
3. The user's own events are never announced: Google's `creator.self`, a creator address equal to any signed-in
   account, and, in a calendar the user can write to, an event whose creator is unknown.
4. A series is announced once, not once per instance. An event is announced at most once per run.
5. More than three new events from one calendar in one sync become one summary banner.
6. The banner names the creator when the source does (Google `creator.displayName` or `email`, iCloud
   `CS:created-by`); otherwise it names only the calendar.

## Oracle
- Claims 1 to 6: Google Calendar API v3 reference (`Events` resource: `created`, `creator.self`; `CalendarList`:
  `accessRole`), RFC 5545 3.8.7.1 (`CREATED`), Apple's CalendarServer sharing extension (`CS:shared`,
  `CS:created-by`), read from memory and not re-checked against Apple's servers.

## Method
Example tests of the pure selection (`news`) and the bridge with a fake Google account: start, then an event
created after the start appears in a shared calendar on the next sync. iCloud parsing against the fake CalDAV
server in `tests/test_icloud.py`. The banner is checked with `tools/render.py OUT week dark 1240x800 arrival`.

## Thresholds
All tests pass. Real Google and real iCloud are manual checks, recorded below with date and result.

## Results
- 2026-10-01, `tests/test_arrivals.py`, `tests/test_icloud.py`: claims 1 to 6 pass offline (selection rules with
  example rows, the bridge with a fake shared Google calendar announcing once over two syncs, `CS:shared`,
  `CS:created-by` and `CREATED` read from the fake CalDAV server).
- 2026-10-01, `tools/render.py OUT week dark|light arrival`: one event and one summary banner, both themes, looked
  at: grey surface, calendar colour as a dot, three lines, no borders or shadows.
- Real Google and real iCloud: open. Check: a second person adds an event to a calendar they share with you while
  Calendary runs; within a minute a banner appears.

## Known gaps
- Events added while Calendary was closed are not announced; nothing is remembered across runs.
- Only the synced window (the range on screen ± 31 days) is watched; an event added far in the future shows no
  banner until that range is opened.
- Whether iCloud delivers `CS:created-by` is not verified; without it the banner names the calendar only.
- The banner is inside the window; there is no desktop notification.
