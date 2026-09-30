"""docs/verification/google.md claims 1-3: PKCE, the loopback sign-in over real HTTP, the client file."""
import base64
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from calendary.google import GoogleError, Login, load_client, pkce
from calendary.google.auth import id_token_email

CLIENT = {"client_id": "id.apps.googleusercontent.com", "client_secret": "secret"}


def fake_id_token(email):
    payload = base64.urlsafe_b64encode(json.dumps({"email": email}).encode()).decode().rstrip("=")
    return "header." + payload + ".signature"


class PkceTest(unittest.TestCase):
    def test_rfc7636_appendix_b(self):
        # Expected value from RFC 7636 appendix B, cross-checked with `openssl dgst -sha256 -binary | base64url`.
        verifier, challenge = pkce("dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk")
        self.assertEqual(challenge, "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM")

    def test_generated_verifier_has_the_allowed_length(self):
        verifier, challenge = pkce()
        self.assertTrue(43 <= len(verifier) <= 128)
        self.assertNotIn("=", challenge)

    def test_id_token(self):
        self.assertEqual(id_token_email(fake_id_token("a@b.de")), "a@b.de")
        with self.assertRaises(GoogleError):
            id_token_email("garbage")


class LoginTest(unittest.TestCase):
    def start(self, tokens=None):
        calls = []

        def exchange(client, fields):
            calls.append(fields)
            return tokens if tokens is not None else {"refresh_token": "r", "id_token": fake_id_token("me@gmail.com")}
        login = Login(CLIENT, exchange)
        result = {}

        def wait():
            try:
                result["value"] = login.wait(timeout=10)
            except GoogleError as error:
                result["error"] = str(error)
        thread = threading.Thread(target=wait)
        thread.start()
        return login, calls, result, thread

    @staticmethod
    def visit(login, query):
        try:
            with urllib.request.urlopen(login.redirect + "/?" + query, timeout=5) as reply:
                return reply.status
        except urllib.error.HTTPError as error:
            error.close()
            return error.code

    def test_url_carries_pkce_state_and_loopback(self):
        login = Login(CLIENT)
        query = {k: v[0] for k, v in parse_qs(urlparse(login.url).query).items()}
        login.server.server_close()
        self.assertEqual(query["redirect_uri"], login.redirect)
        self.assertTrue(login.redirect.startswith("http://127.0.0.1:"))
        self.assertEqual((query["code_challenge"], query["code_challenge_method"]), (pkce(login.verifier)[1], "S256"))
        self.assertEqual((query["state"], query["access_type"]), (login.state, "offline"))

    def test_wrong_state_is_rejected_right_state_signs_in(self):
        login, calls, result, thread = self.start()
        self.assertEqual(self.visit(login, "state=wrong&code=evil"), 400)
        self.assertEqual(self.visit(login, "state=%s&code=good" % login.state), 200)
        thread.join(5)
        self.assertEqual(result["value"], ("me@gmail.com", "r"))
        self.assertEqual(len(calls), 1)
        self.assertEqual((calls[0]["code"], calls[0]["code_verifier"], calls[0]["redirect_uri"]),
                         ("good", login.verifier, login.redirect))

    def test_cancel_and_denial(self):
        login, calls, result, thread = self.start()
        login.cancel()
        thread.join(5)
        self.assertEqual((result["error"], calls), ("Anmeldung abgebrochen", []))
        login, calls, result, thread = self.start()
        self.assertEqual(self.visit(login, "state=%s&error=access_denied" % login.state), 200)
        thread.join(5)
        self.assertEqual(result["error"], "Anmeldung abgebrochen")

    def test_missing_refresh_token_fails_loud(self):
        login, calls, result, thread = self.start(tokens={"id_token": fake_id_token("x@y.de")})
        self.visit(login, "state=%s&code=c" % login.state)
        thread.join(5)
        self.assertEqual(result["error"], "Google hat keine dauerhafte Anmeldung geschickt")


class ClientFileTest(unittest.TestCase):
    def test_accepted_and_rejected_forms(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "google-client.json")
            self.assertIsNone(load_client(path))
            forms = [({"installed": CLIENT}, CLIENT), (CLIENT, CLIENT), ({"installed": {"client_id": "x"}}, None),
                     ([1, 2], None), ({"web": CLIENT}, None)]
            for data, expected in forms:
                path.write_text(json.dumps(data))
                self.assertEqual(load_client(path), expected, data)
            path.write_text("{not json")
            self.assertIsNone(load_client(path))


if __name__ == "__main__":
    unittest.main()
