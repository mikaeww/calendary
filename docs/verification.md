# Verification

## Policy

- Every component with non-trivial logic has a plan in `verification/` before its code: claims, oracle, method,
  corpus, thresholds, known gaps.
- A check that did not run is not passed. Results are written into the plan with the date they were measured.
- Offscreen renders (`tools/render.py`) are evidence for layout only, not for motion smoothness or real input.
- Nothing here talks to real Google or the real keyring; those paths are verified by hand and noted as such.

## Plans

| Plan | Component |
|---|---|
| [verification/cache.md](verification/cache.md) | Google event resources to rows and back, window replacement |
| [verification/layout.md](verification/layout.md) | Week columns, all-day lanes, month cells |
| [verification/dates.md](verification/dates.md) | Date arithmetic and parsing in `qml/calendar/dates.js` |
| [verification/google.md](verification/google.md) | Sign-in, token refresh, API calls, bridge behaviour |
