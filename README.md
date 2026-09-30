<p align="center"><img src="assets/icons/calendary.svg" width="96" alt="Calendary icon"></p>

# Calendary

A calendar for Google accounts and iCloud calendars on Linux, made for Hyprland. Python with Qt Quick (PySide6).

- Sign in with Google in the browser, one button; iCloud with the Apple ID and an app-specific password
  (account.apple.com → Sign-In and Security); several accounts, every calendar can be hidden
- Week and month view; draw an event into the week, drag it to another time or day, drag its edge to resize
- Create, edit and delete events, with repeat for new ones; edits show at once and roll back if Google refuses
- Grey interface in dark and light, following the system; the UI font comes from the Ghostly QShell
- The next events go to `~/.cache/calendary/upcoming.json` for the shell's island

The interface is German. Status: Google works against the real service; iCloud is verified against a fake CalDAV
server and still to be tried against real iCloud, see [docs/roadmap.md](docs/roadmap.md).

## One-time Google setup (for whoever installs it)

Google gives calendar access only to registered apps, so an installation needs its own OAuth client once. Users
never see it; they only press "Mit Google anmelden".

1. In the [Google Cloud Console](https://console.cloud.google.com/) create a project and enable the
   **Google Calendar API**.
2. Under **Google Auth Platform**, create an OAuth client of type **Desktop app** and download its JSON.
3. Set the publishing status to **In production**; in "Testing", Google ends every sign-in after seven days.
4. Save the JSON as `google-client.json` in this folder. It is git-ignored.

Google shows an "unverified app" notice during sign-in until the project is verified. Refresh tokens are stored in
the Secret Service (gnome-keyring) through `secret-tool`, never in a file. Details: ADR
[0001](docs/decisions/0001-google-sign-in.md).

## Install

Needs Python 3 with PySide6, `requests` and `python-dateutil`, `secret-tool` (libsecret), a C compiler and the Wayland headers.

```sh
./install.sh
calendary
```

## Shortcuts

| Key | Action |
| --- | --- |
| ← / →, J / K | previous / next week or month |
| T | today |
| W / M | week / month |
| N | new event |
| Ctrl+R | sync now |
| Ctrl+, | settings |
| Ctrl + wheel | zoom the hours |

## Check

```sh
python3 tools/check.py                            # structure, qmlformat, qmllint, all tests
python3 tools/render.py out.png week dark         # offscreen screenshot with sample events
```

Conventions, decisions and verification plans are in [docs/](docs/README.md).

## License

MIT
