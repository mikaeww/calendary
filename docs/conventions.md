# Conventions

Binding rules for Calendary, derived from the `clean-project` skill. Deviations need an ADR in `decisions/`.

## Layout

- `src/calendary/` holds the Python package: one concept per module, one directory per concept with several files.
- `src/calendary/qml/` holds the interface. `Main.qml` is the window; everything else lives in a named directory
  (`theme`, `motion`, `controls`, `calendar`, `sidebar`, `sheets`, `arrivals`).
- `tests/` checks the public operations of the package and the pure QML logic (`*.test.js`).
- `tools/` holds dev commands: `check.py`, `structure.py`, `qmltypes.py` (describes the Python singletons to
  qmllint), `render.py` (offscreen screenshots with sample data), `build_windows.py` and `windows_smoke.py`
  (Windows installer, ADR 0006).

## Hard limits

Enforced by `tools/structure.py`, which runs in `tools/check.py`.

| Limit | Value |
|---|---|
| Lines per handwritten file (code, docs, scripts) | 500 |
| Code files per directory (entry files and tests excluded) | 8 |
| Markdown files per docs directory, index included | 8 |
| Lines per Python function | 60 |
| Parameters per Python function (`self`/`cls` excluded) | 5 |
| Directory depth below `src/` | 4 |

Forbidden module names: `utils`, `util`, `helpers`, `helper`, `misc`, `common`, `stuff`, `shared`.

## Code

- Entry files (`__init__.py`, `__main__.py`) document and wire; logic lives in named modules.
- No bare `except:`, no `assert` in library code unless its message starts with `invariant:`.
- Every module starts with a docstring saying what it is for and what not.
- Errors are never swallowed silently; a deliberate ignore carries a comment saying why.
- Network and keyring calls run on worker threads; only the GUI thread touches the database.
- Tests touch only files, processes and keyring entries they created. The real keyring is never used in tests.
- Dependencies: Python 3 stdlib, PySide6, `requests`, `python-dateutil` (ADR 0005), `secret-tool` on Linux,
  `tzdata` on Windows (ADR 0006). Nothing else without an ADR.

## Interface

- Colours, radii, spacing, font sizes and motion durations come only from `qml/theme/Theme.qml`.
- Neutral grey only (R = G = B). The one exception is the calendar colour of Google calendars, shown as a small
  dot (ADR 0003).
- No borders, lines or shadows as structure; depth is a brightness step. Radii come in two steps: surfaces and
  controls. No pill shapes.
- Dark and light palettes both exist; the default follows the system, the choice is saved.
- Motion follows `qml/motion/`: everything that can be interrupted (paging, view switch, sheets, the segmented
  control) runs on one analytic, critically damped spring driven by the render loop, which keeps position and
  velocity on retarget and lands exactly on its target. Hover and colour changes use a short native transition.
  Reduced motion removes travel and keeps fades.
- Every QML file declares `pragma ComponentBehavior: Bound`; delegates reach model data only through required
  properties.
- UI text is German, code and docs are English.

## Workflow

1. Plan in the commit message, or in `docs/` for larger changes.
2. Implement in steps that keep the tree working.
3. `python3 tools/check.py` must pass.
4. Real check: `python3 tools/render.py` for the interface, the real program for anything else.
5. Commit one logical step at a time with the docs it changes, naming how it was checked.
