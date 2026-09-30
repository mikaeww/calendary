"""Calendary: a Google and iCloud calendar for Hyprland, also built for Windows, in Python with Qt Quick.

Run it with `python3 -m calendary` (the `calendary` launcher does that). The package is split into `google`
(sign-in and API), `cache` (SQLite copy of the events), `layout` (where events sit), `bridge` (what QML talks to),
`preferences`/`desktop` (settings) and `platform` (Hyprland workaround, Windows keyring). See docs/architecture/overview.md.
"""
