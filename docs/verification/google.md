# Verification plan: Google sign-in, API and bridge

Components: `src/calendary/google/`, `src/calendary/bridge/`.

## Claims
1. The PKCE challenge is the S256 transform of RFC 7636.
2. The loopback server accepts exactly one redirect carrying the expected `state`, rejects others, and hands the
   code to the token exchange together with the verifier and the redirect URI.
3. A client file is accepted in Google's download format and in the plain `{client_id, client_secret}` form, and
   anything else is reported as missing.
4. The bridge shows an edit before Google answers, replaces the pending id with Google's id, and rolls a refused
   edit back by refetching.
5. Tests never touch the real keyring or network.

## Oracle
- Claim 1: the test vector in RFC 7636, appendix B.
- Claim 2: real HTTP requests against the real loopback server, token exchange replaced by a recorder.
- Claim 4: a fake Google that records calls and can refuse.

## Method
Example and integration tests (claims 1 to 4). The real sign-in against Google is a manual check:
run `calendary`, press "Mit Google anmelden", pick an account, see the calendars in the sidebar.

## Thresholds
All tests pass. The manual sign-in is recorded below with date and result once done.

## Results
- 2026-09-30, `tests/test_google.py`, `tests/test_bridge.py`: claims 1 to 5 pass (RFC 7636 vector also
  recomputed with openssl; loopback tested with real HTTP on 127.0.0.1; bridge with fake Google and keyring).
- 2026-09-30, manual sign-in against Google with the owner's account: passed. Client of type Desktop app, project
  "In production", unverified. Four calendars listed (primary, Familie, two read-only subscriptions). A family
  calendar with 0 events on screen was checked against the API directly: Google also returns 0 instances for the
  fetched window (±31 days); its 8 instances within ±1 year are yearly all-day events in January, March and April.

## Known gaps
Token revocation surfaces as a notice "… neu anmelden"; there is no automatic re-sign-in.
