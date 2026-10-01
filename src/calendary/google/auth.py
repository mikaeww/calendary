"""Browser sign-in for installed apps (RFC 8252): loopback redirect on 127.0.0.1, PKCE S256, random state.

Not for token storage (keyring.py) or API calls (api.py).
"""
import base64
import hashlib
import json
import secrets
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import requests

from calendary.google.errors import GoogleError
from calendary.language import tr

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = "openid email https://www.googleapis.com/auth/calendar"
TIMEOUT = 20
DONE_PAGE = ("<!doctype html><meta charset=utf-8><title>Calendary</title>"
             "<p style='font:16px system-ui;margin:3em'>%s</p>")


def pkce(verifier=None):
    """(verifier, S256 challenge) as RFC 7636 defines them."""
    verifier = verifier or secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return verifier, base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def id_token_email(id_token):
    """The email claim. Straight from Google's token endpoint over TLS, so OpenID Connect allows skipping the signature."""
    try:
        payload = id_token.split(".")[1]
        return json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))["email"]
    except (IndexError, ValueError, KeyError) as error:
        raise GoogleError(tr("Google hat keine E-Mail-Adresse geschickt")) from error


def post_token(client, fields):
    """One call to the token endpoint; invalid_grant means revoked, or expired in a project still in "Testing"."""
    try:
        reply = requests.post(TOKEN_URL, data=dict(fields, **client), timeout=TIMEOUT)
    except requests.RequestException as error:
        raise GoogleError(tr("Keine Verbindung zu Google")) from error
    try:
        data = reply.json()
    except ValueError:
        data = {}
    if reply.status_code != 200:
        if data.get("error") == "invalid_grant":
            raise GoogleError(tr("Die Anmeldung ist abgelaufen, bitte neu anmelden"))
        raise GoogleError(tr("Google lehnt die Anmeldung ab (%s)") % data.get("error", reply.status_code))
    return data


class Login:
    """One sign-in: open `url` in the browser, then `wait()` returns (email, refresh_token); `cancel()` ends it."""

    def __init__(self, client, exchange=post_token):
        self.client, self.exchange = client, exchange
        self.verifier, challenge = pkce()
        self.state = secrets.token_urlsafe(16)
        self.result = None
        self.done = threading.Event()
        self.server = HTTPServer(("127.0.0.1", 0), self._handler())
        self.redirect = "http://127.0.0.1:%d" % self.server.server_port
        self.url = AUTH_URL + "?" + urlencode({
            "client_id": client["client_id"], "redirect_uri": self.redirect, "response_type": "code",
            "scope": SCOPE, "code_challenge": challenge, "code_challenge_method": "S256",
            "access_type": "offline", "prompt": "consent select_account", "state": self.state})

    def _handler(self):
        login = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                query = {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}
                if query.get("state") != login.state or login.done.is_set():
                    self.send_error(400)
                    return
                login.result = query
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write((DONE_PAGE % tr("Angemeldet. Du kannst diesen Tab schließen.")).encode())
                login.done.set()

            def log_message(self, *args):
                """Silenced: the default handler prints every request to stderr."""

        return Handler

    def cancel(self):
        if not self.done.is_set():
            self.result = {"error": "cancelled"}
            self.done.set()

    def wait(self, timeout=600):
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        try:
            finished = self.done.wait(timeout)
        finally:
            self.server.shutdown()
            self.server.server_close()
        if not finished:
            raise GoogleError(tr("Anmeldung abgelaufen, bitte erneut versuchen"))
        if "code" not in self.result:
            raise GoogleError(tr("Anmeldung abgebrochen") if self.result.get("error") in ("cancelled", "access_denied")
                              else tr("Anmeldung fehlgeschlagen: %s") % self.result.get("error", "?"))
        tokens = self.exchange(self.client, {"grant_type": "authorization_code", "code": self.result["code"],
                                             "redirect_uri": self.redirect, "code_verifier": self.verifier})
        if "refresh_token" not in tokens:
            raise GoogleError(tr("Google hat keine dauerhafte Anmeldung geschickt"))
        return id_token_email(tokens.get("id_token", "")), tokens["refresh_token"]
