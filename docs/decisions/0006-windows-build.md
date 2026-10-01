# 0006: Windows build with embedded Python and NSIS

**Status:** accepted; shipping the OAuth client in the installer is superseded by 0007
**Date:** 2026-09-30

## Context
The owner asked for a Windows version with an NSIS installer and a GitHub release. On Windows there is no
`secret-tool`, `zoneinfo` has no time zone data, and the launcher and install script are shell scripts.

## Options
- PyInstaller: one `calendary.exe`, but the package lives in an archive, so every path derived from `__file__`
  (QML, icons, OAuth client) would need a frozen-app branch.
- The official embeddable Python with the wheels next to `src/`, the checkout layout kept: no path changes, the
  process is `pythonw.exe`.
- For secrets, the `keyring` package (plus pywin32-ctypes and the jaraco packages) or three advapi32 calls
  through `ctypes`.

## Decision
Embeddable Python, the checkout layout under `%LOCALAPPDATA%\Programs\Calendary`, built by
`tools/build_windows.py` on a GitHub Windows runner and packed by NSIS (`packaging/windows/calendary.nsi`).
Secrets go to the Windows Credential Manager through `ctypes` (`platform/windows.py`), generic credentials named
`<service>/<account>`. `tzdata` is bundled as the one Windows-only dependency. The OAuth client comes from the
repository secret `GOOGLE_CLIENT_JSON` and is part of the installer.

## Consequences
- The installer is about the size of PySide6-Essentials; Task Manager shows `pythonw.exe`, the taskbar shows
  Calendary through its own app id.
- The installer contains the OAuth client, so releases stay in the private repository.
- The icon glyphs came from the owner's installed Monofur Nerd Font and were boxes on Windows; the seven used
  Material Design Icons now ship as `assets/fonts/calendary-icons.ttf` ("Calendary Icons"), on both platforms.
- Settings, cache and island file use the XDG fallbacks in the user folder (`.config`, `.local`, `.cache`).
- The release workflow runs the unit tests on Windows, renders the interface, installs silently, runs
  `tools/windows_smoke.py` and uninstalls before it publishes.
