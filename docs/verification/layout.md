# Verification plan: layout

Component: `src/calendary/layout/` (`week.py`, `month.py`).

## Claims
1. Timed events of one day that overlap in time never share a column, and `col < cols` for every event.
2. The number of columns of a cluster equals the largest number of its events that overlap at one instant
   (no wasted width).
3. All-day bars in the same lane never share a day, and the number of lanes equals the largest number of bars
   covering one day.
4. Every event appears in exactly the month cells whose day it overlaps; a zero-length event appears on its start
   day only.

## Oracle
Brute force written in the test: overlap depth by sweeping every start instant (claims 2, 3), direct day-by-day
overlap check with `datetime` (claim 4).

## Method
- Claims 1, 2: property test over 2000 seeded random days with 1 to 12 events.
- Claim 3: exhaustive over every set of up to three bars inside a seven-day week (all 28 spans per bar).
- Claim 4: property test over 500 seeded random months.

## Corpus
Seed 20260930; spans cover the week edges, multi-day events and zero-length events.

## Thresholds
100 % of cases agree with the oracle.

## Known gaps
Timed events shorter than 20 minutes are drawn 20 minutes tall; the layout treats them as that tall, so two short
back-to-back events can share a cluster.

## Results (2026-09-30, `tests/test_layout.py`)
- Claims 1, 2: 2000 random days (seed 20260930), no shared column among overlapping events, column count equal to
  the overlap depth of every cluster.
- Claim 3: all 22 764 sets of one to three bars in a week, lanes never share a day, lane count equals the busiest
  day.
- Claim 4: 500 random months, 21 000 cells, 100 % agreement with the day-by-day oracle.
