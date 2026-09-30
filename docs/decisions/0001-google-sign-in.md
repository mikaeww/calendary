# 0001: Google sign-in with an app-owned OAuth client

**Status:** accepted
**Date:** 2026-09-30

## Context
Google gives calendar access only to registered OAuth clients. The owner wants sign-in to be one button: no client
ID, secret or URL typed into the app. Embedded web views are blocked by Google for sign-in, and borrowing another
application's client (GNOME Online Accounts, Thunderbird) breaks Google's terms.

## Options
- Client fields in the settings (previous prototype): works, but every user does developer setup in the UI.
- GNOME Online Accounts: its client is GNOME's; adding an account needs gnome-control-center.
- Device flow: as far as known, the calendar scope is not on the list Google allows for limited-input clients
  (from memory of the docs, not re-checked for this decision).
- App-owned client of type "Desktop app", shipped with the app, loopback redirect with PKCE (RFC 8252).

## Decision
The app reads its client from `google-client.json` next to the source (Google's download format), which is
git-ignored. The interface has one action, "Mit Google anmelden": the system browser opens, the loopback server on
127.0.0.1 receives the code, PKCE (S256) and a random `state` protect the exchange. Refresh tokens go to the Secret
Service through `secret-tool` (attributes `service=calendary account=<email>`), never into a file.

## Consequences
- The owner creates the client once in the Google Cloud Console and sets the project to "In production"; in
  "Testing" Google expires refresh tokens after seven days.
- Google shows an "unverified app" warning on sign-in until the project is verified.
- Publishing the repository means either shipping the client file separately or letting others bring their own.
