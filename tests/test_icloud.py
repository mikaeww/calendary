"""docs/verification/caldav.md claims 4-6: discovery, edits and sign-in against a fake CalDAV server over real HTTPS.

The server answers like iCloud and records every request. It uses a throw-away certificate for localhost that only
this test trusts, so the production rule "HTTPS on the account's domain only" stays in force.
"""
import base64
import os
import re
import ssl
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from calendary.caldav import ICloudAccount, account_key
from calendary.caldav import ical
from calendary.errors import ServiceError

USER, PASSWORD = "alex@icloud.com", "abcd-efgh-ijkl-mnop"
SERIES = ("BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nUID:s\r\nDTSTART;TZID=Europe/Berlin:20261005T100000\r\n"
          "DURATION:PT1H\r\nSUMMARY:Serie\r\nRRULE:FREQ=WEEKLY;COUNT=3\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n")
SINGLE = ("BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nUID:e\r\nDTSTART:20261007T100000Z\r\nDTEND:20261007T110000Z\r\n"
          "SUMMARY:Termin von Alex\r\nBEGIN:VALARM\r\nTRIGGER:-PT10M\r\nACTION:DISPLAY\r\nEND:VALARM\r\nEND:VEVENT\r\n"
          "END:VCALENDAR\r\n")


def multistatus(*responses):
    return ('<?xml version="1.0"?><d:multistatus xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav" '
            'xmlns:a="http://apple.com/ns/ical/">%s</d:multistatus>' % "".join(
                "<d:response><d:href>%s</d:href><d:propstat><d:prop>%s</d:prop><d:status>HTTP/1.1 200 OK</d:status>"
                "</d:propstat></d:response>" % response for response in responses))


def collection(href, name, color, privilege, components="VEVENT"):
    comps = "".join('<c:comp name="%s"/>' % c for c in components.split(","))
    return (href, "<d:resourcetype><d:collection/><c:calendar/></d:resourcetype><d:displayname>%s</d:displayname>"
                  "<a:calendar-color>%s</a:calendar-color><c:supported-calendar-component-set>%s"
                  "</c:supported-calendar-component-set><d:current-user-privilege-set><d:privilege><d:%s/>"
                  "</d:privilege></d:current-user-privilege-set>" % (name, color, comps, privilege))


class Server(BaseHTTPRequestHandler):
    """iCloud as far as Calendary uses it; `store` maps resource paths to (text, etag)."""

    def reply(self, status, body="", headers=None):
        data = body.encode()
        self.send_response(status)
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def handle_one(self):
        state = self.server.state
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length).decode() if length else ""
        state["requests"].append((self.command, self.path, dict(self.headers), body))
        expected = "Basic " + base64.b64encode(("%s:%s" % (USER, PASSWORD)).encode()).decode()
        if self.headers.get("Authorization") != expected:
            return self.reply(401)
        if self.command == "PROPFIND" and self.path == "/" and state.get("evil"):
            return self.reply(301, headers={"Location": "https://evil.example/"})
        if self.command == "PROPFIND" and self.path == "/":
            return self.reply(207, multistatus(("/", "<d:current-user-principal><d:href>/42/principal/</d:href>"
                                                     "</d:current-user-principal>")))
        if self.command == "PROPFIND" and self.path == "/42/principal/":
            return self.reply(207, multistatus(("/42/principal/", "<c:calendar-home-set><d:href>%s/42/calendars/"
                                                "</d:href></c:calendar-home-set>" % state["base"])))
        if self.command == "PROPFIND" and self.path == "/42/calendars/":
            return self.reply(207, multistatus(
                ("/42/calendars/", "<d:resourcetype><d:collection/></d:resourcetype>"),
                collection("/42/calendars/home/", "Privat", "#7EC8FFFF", "write"),
                collection("/42/calendars/alex/", "Alex teilt", "#FF9EC7FF", "read"),
                collection("/42/calendars/tasks/", "Erinnerungen", "#888888FF", "write", "VTODO")))
        if self.command == "REPORT":
            found = [(path, text) for path, (text, _) in state["store"].items() if path.startswith(self.path)]
            return self.reply(207, multistatus(*[(path, "<c:calendar-data>%s</c:calendar-data>" % text.replace("&", "&amp;"))
                                                 for path, text in found]))
        return self.resource(state, body)

    def resource(self, state, body):
        current = state["store"].get(self.path)
        if self.command == "GET":
            return self.reply(200, current[0], {"ETag": current[1]}) if current else self.reply(404)
        if self.command == "PUT":
            if self.headers.get("If-None-Match") == "*" and current:
                return self.reply(412)
            if self.headers.get("If-Match") and (not current or current[1] != self.headers["If-Match"]):
                return self.reply(412)
            state["store"][self.path] = (body, '"%d"' % len(state["requests"]))
            return self.reply(201)
        if self.command == "DELETE":
            if self.headers.get("If-Match") and current and current[1] != self.headers["If-Match"]:
                return self.reply(412)
            state["store"].pop(self.path, None)
            return self.reply(204)
        return self.reply(405)

    do_GET = do_PUT = do_DELETE = do_PROPFIND = do_REPORT = handle_one

    def log_message(self, *args):
        """Silenced: the default handler prints every request."""


class ICloudTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cert, key = Path(cls.tmp.name, "cert.pem"), Path(cls.tmp.name, "key.pem")
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", str(key), "-out",
                        str(cert), "-days", "1", "-subj", "/CN=localhost", "-addext", "subjectAltName=DNS:localhost"],
                       check=True, capture_output=True)
        cls.server = ThreadingHTTPServer(("localhost", 0), Server)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert, key)
        cls.server.socket = context.wrap_socket(cls.server.socket, server_side=True)
        cls.base = "https://localhost:%d" % cls.server.server_port
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.saved_bundle = os.environ.get("REQUESTS_CA_BUNDLE")
        os.environ["REQUESTS_CA_BUNDLE"] = str(cert)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        if cls.saved_bundle is None:
            os.environ.pop("REQUESTS_CA_BUNDLE", None)
        else:
            os.environ["REQUESTS_CA_BUNDLE"] = cls.saved_bundle
        cls.tmp.cleanup()

    def setUp(self):
        self.server.state = {"base": self.base, "requests": [], "store": {
            "/42/calendars/home/s.ics": (SERIES, '"s1"'), "/42/calendars/alex/e.ics": (SINGLE, '"e1"')}}
        self.account = ICloudAccount(USER, PASSWORD, root=self.base + "/", domain="localhost")

    def requests(self, method):
        return [r for r in self.server.state["requests"] if r[0] == method]

    def test_discovery_lists_event_calendars_with_permissions(self):
        calendars = self.account.calendars()
        self.assertEqual([(c["name"], c["color"], c["writable"]) for c in calendars],
                         [("Privat", "#7EC8FF", 1), ("Alex teilt", "#FF9EC7", 0)])
        self.assertEqual(calendars[1]["id"], self.base + "/42/calendars/alex/")
        self.assertEqual(self.account.email, account_key(USER))

    def test_events_expand_series_and_keep_single_ones(self):
        home = self.base + "/42/calendars/home/"
        items = self.account.events(home, ("2026-10-01T00:00:00+02:00", "2026-11-01T00:00:00+01:00"))
        self.assertEqual([i["start"]["dateTime"] for i in items], ["2026-10-05T10:00:00+02:00",
                                                                   "2026-10-12T10:00:00+02:00",
                                                                   "2026-10-19T10:00:00+02:00"])
        report = self.requests("REPORT")[-1]
        self.assertIn('<c:time-range start="20260930T220000Z" end="20261031T230000Z"/>', report[3])
        self.assertEqual(report[2]["Depth"], "1")

    def test_insert_patch_move_delete(self):
        home, shared = self.base + "/42/calendars/home/", self.base + "/42/calendars/alex/"
        body = {"summary": "Neu", "start": {"dateTime": "2026-10-08T09:00:00+02:00"},
                "end": {"dateTime": "2026-10-08T10:00:00+02:00"}}
        created = self.account.insert(home, body)
        self.assertEqual(self.requests("PUT")[-1][2].get("If-None-Match"), "*")
        path = created["id"][len(self.base):]
        self.assertIn(path, self.server.state["store"])

        existing = self.base + "/42/calendars/alex/e.ics"
        self.account.patch(shared, existing, dict(body, summary="Geändert"))
        self.assertEqual(self.requests("PUT")[-1][2].get("If-Match"), '"e1"')
        stored = ical.events(self.server.state["store"]["/42/calendars/alex/e.ics"][0])[0]
        self.assertEqual((ical.text(stored, "SUMMARY"), stored["children"][0]["name"]), ("Geändert", "VALARM"))

        moved = self.account.move(shared, existing, home)
        self.assertEqual(moved["id"], home + "e.ics")
        self.assertNotIn("/42/calendars/alex/e.ics", self.server.state["store"])
        self.assertIn("/42/calendars/home/e.ics", self.server.state["store"])

        self.account.delete(home, moved["id"])
        self.assertNotIn("/42/calendars/home/e.ics", self.server.state["store"])

    def test_series_and_new_series_are_refused(self):
        home = self.base + "/42/calendars/home/"
        for call in (lambda: self.account.patch(home, home + "s.ics", {}),
                     lambda: self.account.delete(home, home + "s.ics#20261012T080000Z"),
                     lambda: self.account.insert(home, {"recurrence": ["RRULE:FREQ=DAILY"]})):
            with self.assertRaises(ServiceError):
                call()
        self.assertIn("/42/calendars/home/s.ics", self.server.state["store"])

    def test_wrong_password_and_foreign_redirect(self):
        with self.assertRaisesRegex(ServiceError, "app-spezifisches Passwort"):
            ICloudAccount(USER, "wxyz-wxyz-wxyz-wxyz", root=self.base + "/", domain="localhost").verify()
        self.server.state["evil"] = True
        with self.assertRaisesRegex(ServiceError, "fremde Adresse"):
            self.account.verify()
        with self.assertRaisesRegex(ServiceError, "fremde Adresse"):
            ICloudAccount(USER, PASSWORD, root="http://localhost/", domain="localhost").verify()


class ConnectTest(unittest.TestCase):
    def test_bad_input_is_refused_before_any_request(self):
        from calendary.bridge.signin import APP_PASSWORD
        for good in ("abcd-efgh-ijkl-mnop", "abcdefghijklmnop"):
            self.assertTrue(APP_PASSWORD.fullmatch(good))
        for bad in ("mein-passwort", "abcd-efgh-ijkl", "ABCD-EFGH-IJKL-MNO1"):
            self.assertIsNone(APP_PASSWORD.fullmatch(bad))
        self.assertTrue(re.fullmatch(r"icloud:.+", account_key(" Alex@iCloud.com ")))
        self.assertEqual(account_key(" Alex@iCloud.com "), "icloud:alex@icloud.com")


if __name__ == "__main__":
    unittest.main()
