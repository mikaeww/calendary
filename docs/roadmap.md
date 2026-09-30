# Roadmap

## Phase 1: usable calendar (current)

Goal: sign in with Google, see week and month, create, move, resize, edit and delete events.

| Item | State |
|---|---|
| Check tooling (structure, qmllint, qmlformat, tests) | done |
| Cache, week/month layout, Google API, sign-in | done, verified offline, see `verification/` |
| Interface: sidebar, week, month, editor, settings, dark and light | done, offscreen-tested |
| Island export for the Ghostly QShell | done; the shell's `CalendarView.qml` reads it |
| Sign-in against real Google | done 2026-09-30, see `verification/google.md` |

## Phase 1b: iCloud (ADR 0005)

| Item | State |
|---|---|
| CalDAV discovery, events, edits of single events, sign-in with app password | done, verified against a fake server |
| Sign-in against real iCloud | open |

## Phase 2: comfort

- Multi-day events as spanning bars in the month view.
- Drag in the month view.
- Editing a whole series instead of a single instance.
- iCloud: new series and edits of single instances of a series.

## Not planned

Offline edit queue, other providers, invitations.
