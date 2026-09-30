# Architecture overview

```text
QML (src/calendary/qml)                     Python (src/calendary)
  Main.qml ── calendar/ sidebar/ sheets/  ──▶  bridge.Calendar  (QML singleton "Calendar")
        │                                        │  worker threads ──▶ google.Account / google.Login
        └── theme/ motion/ controls/             │  GUI thread     ──▶ cache (SQLite)
                                                 │                 ──▶ layout.week / layout.month
  Preferences (QML singleton) ◀── preferences    └── island export ──▶ ~/.cache/calendary/upcoming.json
```

| Component | Module | For | Not for |
|---|---|---|---|
| google | `google/` | Sign-in (loopback + PKCE), token refresh, Calendar API calls, keyring | Caching, threads |
| cache | `cache/` | Google resources to rows and back; SQLite windows | Network, layout |
| layout | `layout/` | Where events sit in a week (columns, lanes) and in month cells | Drawing, time zones beyond local |
| bridge | `bridge/` | The QML-facing calendar: threads, optimistic edits, periodic sync, island file | Business rules of Google |
| preferences | `preferences.py`, `desktop.py` | Saved view settings; font and reduced motion from the shell | Colours (those are QML tokens) |
| platform | `platform/` | The Hyprland suspend workaround (`nosuspend.c`, preload) | Anything portable |
| qml | `qml/` | Everything visible; tokens in `theme/`, motion maths in `motion/` | Network or database access |

## Data flow

1. QML asks `Calendar.show(start, end)` for the range on screen. The bridge fetches the padded window on worker
   threads if no fresh fetch covers it (ADR 0002) and replaces it in the cache on the GUI thread.
2. QML reads `Calendar.week(start, days)` / `Calendar.month(start)`; both are recomputed when `revision` changes.
3. `Calendar.save(fields)` writes the row at once with a pending id, sends it to Google, then swaps in Google's
   answer; a refusal shows a notice and refetches, which rolls the row back.
4. After every change the next seven days go to the island file, written atomically.

## Files on disk

| Path | Content |
|---|---|
| `<repo>/google-client.json` | The app's OAuth client (git-ignored, ADR 0001) |
| `$XDG_CONFIG_HOME/calendary/calendary.ini` | Preferences as JSON values |
| `$XDG_DATA_HOME/calendary/calendary.db` | The cache and the list of accounts |
| `$XDG_CACHE_HOME/calendary/upcoming.json` | Island export |
| Secret Service `service=calendary account=<email>` | Refresh token per account |
