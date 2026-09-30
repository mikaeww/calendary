# Verification plan: cache

Component: `src/calendary/cache/` (`events.py`, `database.py`).

## Claims
1. `parse_event(to_google(fields))` returns the same start, end and all-day flag as `fields` for every timed event
   and every all-day event, including days on which daylight saving time changes.
2. An all-day event's `end.date` is exclusive, as the Calendar API defines it: a one-day event on D ends on D+1.
3. Cancelled instances parse to nothing; they never reach the cache.
4. After `replace_window(w, rows)` the cache holds exactly `rows` for that calendar inside `w` and is unchanged for
   events that do not overlap `w`.

## Oracle
- Claims 1, 2: the Calendar API reference (event resource: `start.date`, `end.date` exclusive, `dateTime` RFC 3339)
  and Python's `datetime`/`zoneinfo` for local midnights, which share no code with the component.
- Claim 4: a plain Python list model of the table (filter by overlap, then append), written in the test.

## Method
- Claims 1, 2: exhaustive over every day of 2020-01-01 to 2035-12-31 in Europe/Berlin (5844 days) for all-day
  events of length 1 to 3, plus timed events at 00:00, 02:30 and 23:45 of each day with 15-minute to 25-hour
  durations.
- Claim 3: example test.
- Claim 4: differential against the list model on 500 seeded random operation sequences.

## Corpus
Generated from the date range above; seed 20260930 for the random sequences.

## Thresholds
100 % agreement on every generated case.

## Known gaps
Events whose `start.timeZone` differs from the local zone are shown at their absolute instant in local time; the
original zone is not kept for editing.

## Results (2026-09-30, `tests/test_cache.py`)
- Claims 1, 2: 17 532 all-day and 52 596 timed round trips over 2020-01-01 to 2035-12-31 in Europe/Berlin,
  100 % agreement with zoneinfo.
- Claim 3: passes.
- Claim 4: 500 sequences of 6 random replacements (seed 20260930), 100 % agreement with the list model.
