# Verification plan: dates

Component: `src/calendary/qml/calendar/dates.js`.

## Claims
1. `addDays(t, n)` keeps the wall-clock time and moves exactly `n` calendar days, across daylight saving changes.
2. `addMonths(t, n)` lands on the same day of the month or on the last day of a shorter month.
3. `startOfWeek(t, s)` is the local midnight of the latest weekday `s` on or before `t`; `monthGrid` is the
   `startOfWeek` of the first of the month.
4. `parseDate` accepts exactly the real dates written `D.M.`, `D.M.YY` or `D.M.YYYY`; `parseTime` accepts exactly
   `H`, `HH`, `H:MM`, `HHMM`, `H.MM` with hours 0-23 and minutes 0-59.

## Oracle
Arithmetic on UTC day numbers (`Date.UTC`), which does not use local time and shares no code with `dates.js`.

## Method
Exhaustive: every day of 2020-01-01 to 2035-12-31 for claims 1 to 3 (with `n` in -40..40 for `addDays` and
-25..25 for `addMonths`), every string `D.M.YYYY` for D 0-32, M 0-13 in 2024 and 2026, every time 0-25:0-61.
Run under `TZ=Europe/Berlin` and `TZ=America/New_York`.

## Thresholds
100 % agreement.

## Known gaps
Two-digit years map to 2000-2099.
