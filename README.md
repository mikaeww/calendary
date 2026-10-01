<p align="center"><img src="assets/icons/calendary.svg" width="96" alt="Calendary icon"></p>

# Calendary

A calendar for Google accounts and iCloud calendars on Linux, made for Hyprland, and on Windows. Python with Qt Quick (PySide6).

- Sign in with Google in the browser, one button; iCloud with the Apple ID and an app-specific password
  (account.apple.com → Sign-In and Security); several accounts, every calendar can be hidden
- Week and month view; draw an event into the week, drag it to another time or day, drag its edge to resize
- Create, edit and delete events, with repeat for new ones; edits show at once and roll back if Google refuses
- Grey interface in dark and light, following the system; the UI font comes from the Ghostly QShell
- When someone adds an event to a calendar shared with you, a small banner says what, when and from whom; your own
  events never show up there
- The next events go to `~/.cache/calendary/upcoming.json` for the shell's island

The interface is German. Status: Google works against the real service; iCloud is verified against a fake CalDAV
server and still to be tried against real iCloud, see [docs/roadmap.md](docs/roadmap.md).

## Google setup

Google gives calendar access only to registered apps, and Calendary ships no client of its own: every installation
uses its own Google Cloud project. This takes about five minutes, once.

1. In the [Google Cloud Console](https://console.cloud.google.com/) create a project and enable the
   **Google Calendar API**.
2. Under **Google Auth Platform → Branding**, fill in the app name and your e-mail address. Under **Audience**,
   choose **External** and set the publishing status to **In production**; in "Testing", Google ends every sign-in
   after seven days.
3. Under **Data Access**, add the scopes `openid`, `.../auth/userinfo.email` and `.../auth/calendar`.
4. Under **Clients**, create an OAuth client of type **Desktop app** and download its JSON file.
5. In Calendary open the settings (Ctrl+,), press "Client-Datei wählen …" and pick that file. It is copied to
   `~/.config/calendary/google-client.json` (`%USERPROFILE%\.config\calendary\` on Windows).

Then "Mit Google anmelden" opens the browser. Google shows an "unverified app" notice because the project is yours
and not verified; continue via "Advanced". Refresh tokens are stored in the Secret Service (gnome-keyring) through
`secret-tool` or in the Windows Credential Manager, never in a file. Details: ADR
[0001](docs/decisions/0001-google-sign-in.md) and [0007](docs/decisions/0007-own-oauth-client.md).

iCloud needs no setup: the Apple ID and an app-specific password are enough.

## Install

Needs Python 3 with PySide6, `requests` and `python-dateutil`, `secret-tool` (libsecret), a C compiler and the Wayland headers.

```sh
./install.sh
calendary
```

## Windows

The installer `Calendary-X.Y.Z-x64-setup.exe` from the releases page installs per user into
`%LOCALAPPDATA%\Programs\Calendary` with a Start menu entry: embedded Python and PySide6, no OAuth client (see
"Google setup"). Secrets go to the Windows Credential Manager.

The release workflow builds it, runs the tests on Windows, installs, smoke-tests and uninstalls, and only then
publishes:

```sh
gh workflow run "Windows release" -f version=0.2.0
```

Details: ADR [0006](docs/decisions/0006-windows-build.md).

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
