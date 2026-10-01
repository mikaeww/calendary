<p align="center"><img src="assets/icons/calendary.svg" width="96" alt="Calendary icon"></p>

# Calendary

A desktop calendar for Google Calendar and Apple's iCloud calendars, on Linux (made for Hyprland) and Windows.
Python with Qt Quick (PySide6). The interface is English or German: it follows the system language and can be
switched in the settings.

- Several Google accounts and Apple IDs side by side; every calendar can be hidden
- Week and month view; draw an event into the week, drag it to another time or day, drag its edge to resize
- Create, edit and delete events, with repeat for new ones; edits show at once and roll back if the server refuses
- Grey interface in dark and light, following the system
- English and German; Settings → Language switches at once
- When someone adds an event to a calendar shared with you, a small banner says what, when and from whom; your own
  events never show up there
- The next events go to `~/.cache/calendary/upcoming.json` for a desktop shell to show

Status: Google is tested against the real service. iCloud is tested against a fake CalDAV server and still has to
be tried against real iCloud; see [docs/roadmap.md](docs/roadmap.md).

Contents: [Install on Windows](#install-on-windows) · [Install on Linux](#install-on-linux) ·
[Connect Google Calendar](#google-setup) · [Connect Apple Calendar (iCloud)](#connect-apple-calendar-icloud) ·
[Shared calendars](#shared-calendars)

## Install on Windows

1. Open the [latest release](https://github.com/mikaeww/calendary/releases/latest) and download
   `Calendary-X.Y.Z-x64-setup.exe`.
2. Run it. The installer is not signed, so Windows may show "Windows protected your PC": click **More info**, then
   **Run anyway**. It installs for your user only into `%LOCALAPPDATA%\Programs\Calendary`; no administrator rights.
3. Start Calendary from the Start menu.

Python and everything else come with the installer. Passwords and sign-in tokens go to the Windows Credential
Manager. To remove it: Settings → Apps → Calendary → Uninstall.

## Install on Linux

You need Python 3 with PySide6, `requests` and `python-dateutil`, `secret-tool` (libsecret) with a running Secret
Service such as gnome-keyring, a C compiler and the Wayland client headers. On Arch Linux:

```sh
sudo pacman -S --needed git python pyside6 python-requests python-dateutil libsecret gnome-keyring gcc wayland
```

Other distributions have the same packages under similar names. Then:

```sh
git clone https://github.com/mikaeww/calendary.git
cd calendary
./install.sh
calendary
```

`install.sh` links the `calendary` command, the menu entry and the icons into `~/.local`; the app runs from the
cloned folder, so `git pull` updates it. Passwords and sign-in tokens go to the Secret Service, never into a file.

## Google setup

Google lets only registered apps read calendars, and Calendary ships no registration of its own: everyone connects
it to their own free Google Cloud project. This takes about ten minutes and is done once per computer.

**In the Google Cloud Console**

1. Open the [Google Cloud Console](https://console.cloud.google.com/) with your Google account. Open the project
   menu at the top, choose **New project**, name it e.g. `Calendary` and press **Create**. Make sure the new
   project is selected at the top.
2. Go to **APIs & Services → Library**, search for **Google Calendar API**, open it and press **Enable**.
3. Go to **Google Auth Platform** (search for it at the top) and press **Get started**. Enter `Calendary` as app
   name and your address as support e-mail, choose **External** as audience, enter your address as contact, accept
   the policy and press **Create**.
4. Under **Audience**, press **Publish app** so the status becomes **In production**. In "Testing" Google signs you
   out every seven days.
5. Under **Data Access**, press **Add or remove scopes** and add `openid`, `.../auth/userinfo.email` and
   `.../auth/calendar`, then **Save**.
6. Under **Clients**, press **Create client**, choose **Desktop app** as application type, keep any name and press
   **Create**. Download the JSON file in the dialog that follows (the name starts with `client_secret_`).

**In Calendary**

7. Open the settings: the gear at the bottom left or Ctrl+,.
8. Press **Choose client file …** and pick the downloaded JSON file. Calendary checks it and keeps a copy in
   `~/.config/calendary/google-client.json` (`%USERPROFILE%\.config\calendary\` on Windows); the download can be
   deleted afterwards.
9. Press **Sign in with Google**. Your browser opens; pick your account. Google warns "Google hasn't verified this
   app", because the project is yours and not reviewed by Google: press **Advanced**, then **Go to Calendary**, and
   allow access to your calendars. Return to Calendary; the calendars appear in the sidebar.

More Google accounts: press **Sign in with Google** again. The same client works for all of them. Details: ADR
[0001](docs/decisions/0001-google-sign-in.md) and [0007](docs/decisions/0007-own-oauth-client.md).

## Connect Apple Calendar (iCloud)

iCloud needs no Cloud project, only an app-specific password. Your Apple ID must have two-factor authentication
turned on, which is the default for current Apple IDs.

1. Sign in at [account.apple.com](https://account.apple.com/account/manage), open **Sign-In and Security → App-Specific
   Passwords** and create one named `Calendary`. Apple shows it once, in the form `xxxx-xxxx-xxxx-xxxx`.
2. In Calendary open the settings and press **Connect iCloud**.
3. Enter your Apple ID (its e-mail address) and the app-specific password, not your normal password, and press
   **Connect**. Calendary tries the sign-in first and stores the password only if it worked.

Your iCloud calendars appear in the sidebar, including calendars others share with you; read-only ones carry a
lock. To revoke access later, delete the app-specific password on account.apple.com or press **Sign out** in the
settings. iCloud series can be viewed but not yet edited in Calendary.

## Shared calendars

A calendar someone shares with you shows up once you have accepted the invitation: for Google in Google Calendar
on the web or the phone, for iCloud in the Calendar app on an Apple device or on icloud.com.

While Calendary is open it syncs every minute. When someone else adds an event to such a calendar, a banner at the
top right names the calendar, the event, its time and, where Google or iCloud tell, who added it. Clicking it shows
that day. Events added while Calendary was closed do not get a banner.

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
