"""The Calendar API v3 for one signed-in account: calendar list, events of a window, insert, patch, move, delete.

Access tokens are refreshed on demand. Not for sign-in (auth.py) or for turning resources into rows (cache).
"""
import threading
import time
from urllib.parse import quote

import requests

from calendary.google.auth import post_token
from calendary.google.errors import GoogleError

API = "https://www.googleapis.com/calendar/v3"
TIMEOUT = 20


def path(*parts):
    return "/" + "/".join(quote(part, safe="") for part in parts)


def calendar_entry(item):
    return {"id": item["id"], "name": item.get("summaryOverride") or item.get("summary") or item["id"],
            "color": item.get("backgroundColor", "#888888"),
            "writable": int(item.get("accessRole") in ("owner", "writer")), "main": int(bool(item.get("primary")))}


class Account:
    """One account's API. Safe to call from several worker threads; token refresh is serialised."""

    def __init__(self, client, email, refresh_token):
        self.client, self.email, self.refresh_token = client, email, refresh_token
        self.token, self.expires = None, 0.0
        self.lock = threading.Lock()

    def access_token(self):
        with self.lock:
            if time.monotonic() > self.expires - 60:
                data = post_token(self.client, {"grant_type": "refresh_token", "refresh_token": self.refresh_token})
                self.token = data["access_token"]
                self.expires = time.monotonic() + float(data.get("expires_in", 3600))
            return self.token

    def call(self, method, url, params=None, body=None):
        try:
            reply = requests.request(method, API + url, params=params, json=body, timeout=TIMEOUT,
                                     headers={"Authorization": "Bearer " + self.access_token()})
        except requests.RequestException as error:
            raise GoogleError("Keine Verbindung zu Google") from error
        if reply.status_code >= 400:
            try:
                message = reply.json()["error"]["message"]
            except (ValueError, KeyError, TypeError):
                message = "HTTP %d" % reply.status_code
            raise GoogleError("Google: %s" % message)
        return reply.json() if reply.content else {}

    def pages(self, url, params):
        items, page = [], None
        while True:
            data = self.call("GET", url, dict(params, pageToken=page) if page else params)
            items += data.get("items", [])
            page = data.get("nextPageToken")
            if not page:
                return items

    def calendars(self):
        return [calendar_entry(item) for item in self.pages("/users/me/calendarList", {})]

    def events(self, calendar, window):
        """Instances overlapping window = (start, end) as RFC 3339 strings; series are expanded by Google."""
        return self.pages(path("calendars", calendar, "events"),
                          {"singleEvents": "true", "timeMin": window[0], "timeMax": window[1], "maxResults": 2500})

    def insert(self, calendar, body):
        return self.call("POST", path("calendars", calendar, "events"), body=body)

    def patch(self, calendar, event, body):
        return self.call("PATCH", path("calendars", calendar, "events", event), body=body)

    def move(self, calendar, event, destination):
        return self.call("POST", path("calendars", calendar, "events", event, "move"), {"destination": destination})

    def delete(self, calendar, event):
        return self.call("DELETE", path("calendars", calendar, "events", event))
