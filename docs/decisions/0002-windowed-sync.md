# 0002: Windowed sync instead of sync tokens

**Status:** accepted
**Date:** 2026-09-30

## Context
Recurring events have to appear as instances. Google's incremental sync (`syncToken`) cannot be combined with
`timeMin`/`timeMax`, and `singleEvents=true` without a time window expands open-ended series without bound.

## Options
- `syncToken` with `singleEvents=false` and expanding RRULEs locally: needs an RRULE engine and exception handling.
- Fetch the visible range plus padding with `singleEvents=true`, replace that window in the cache.

## Decision
The bridge fetches the range on screen padded by 31 days on each side, for every calendar, with
`singleEvents=true`, and replaces exactly that window in the cache. A fetch counts as fresh for five minutes; the
calendar list and the window are refetched every five minutes, on window activation and on demand.

## Consequences
- More API calls than incremental sync; fine for one person's calendars.
- Edits to a recurring event change one instance only.
- Events outside every fetched window are not in the cache; the island export covers seven days, which the
  padding always includes.
