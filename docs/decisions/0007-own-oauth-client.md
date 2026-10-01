# 0007: Every installation brings its own OAuth client

**Status:** accepted
**Date:** 2026-10-01

## Context
The repository becomes public so that anyone can install Calendary. Until now the owner's OAuth client sat next to
the source (ADR 0001) and was baked into the Windows installer (ADR 0006). A public installer would let everyone
sign in through the owner's Google Cloud project: its quota, its consent screen, its responsibility. The owner wants
each user to set up their own client instead.

## Options
- Keep shipping the owner's client: easiest for users, but exactly what the owner does not want.
- Client ID and secret as text fields in the settings: works, but copying two long strings is error-prone.
- The user picks the JSON file Google offers for download; the app checks it and copies it into its config folder.

## Decision
No client ships with the app or the installer. `google-client.json` lives in `$XDG_CONFIG_HOME/calendary/` (the
`.config` folder in the user's home on Windows), next to the preferences. Without it the settings explain the
setup and offer "Client-Datei wählen …"; the picked file is accepted only when it holds a Desktop-app client
(`installed` or the plain form), then copied with mode 0600. Sign-in itself stays as in ADR 0001: one button,
loopback redirect, PKCE, refresh tokens in the keyring.

## Consequences
- Every user does the Google Cloud setup once (README, "Google setup"); without it only iCloud works.
- The Windows workflow needs no secret; `GOOGLE_CLIENT_JSON` is unused.
- Releases built before this decision contain the owner's client and were deleted.
