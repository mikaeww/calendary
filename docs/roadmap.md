# Roadmap

## Phase 1: usable calendar (current)

Goal: sign in with Google, see week and month, create, move, resize, edit and delete events.

| Item | State |
|---|---|
| Check tooling (structure, qmllint, qmlformat, tests) | done |
| Cache, week/month layout, Google API, sign-in | done, verified offline, see `verification/` |
| Interface: sidebar, week, month, editor, settings, dark and light | planned |
| Island export for the Ghostly QShell | planned |
| Sign-in against real Google | open: needs the owner's OAuth client (`google-client.json`) |

## Phase 2: comfort

- Multi-day events as spanning bars in the month view.
- Drag in the month view.
- Editing a whole series instead of a single instance.

## Not planned

Offline edit queue, other providers, invitations.
