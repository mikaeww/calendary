"""WebDAV and CalDAV over HTTPS with basic authentication: PROPFIND, REPORT, GET, PUT, DELETE.

Redirects are followed here, keeping the method; requests would turn a redirected PROPFIND into a GET. Not for
iCalendar content or for iCloud specifics.
"""
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse

import requests

from calendary.errors import ServiceError

TIMEOUT = 20
NS = {"d": "DAV:", "c": "urn:ietf:params:xml:ns:caldav", "a": "http://apple.com/ns/ical/",
      "cs": "http://calendarserver.org/ns/"}
REDIRECTS = (301, 302, 303, 307, 308)


class Dav:
    """`domain` bounds where the credentials may go: HTTPS on that domain or its subdomains, nothing else."""

    def __init__(self, user, password, domain):
        self.auth = (user, password)
        self.domain = domain

    def trusted(self, url):
        parsed = urlparse(url)
        host = parsed.hostname or ""
        # Security: basic auth is sent with every request, so a redirect or href elsewhere must never be followed.
        if parsed.scheme != "https" or not (host == self.domain or host.endswith("." + self.domain)):
            raise ServiceError("iCloud verweist auf eine fremde Adresse (%s), abgebrochen" % (host or url))
        return url

    def request(self, method, url, body=None, headers=None):
        """One call; follows up to five redirects with the same method and maps failures to ServiceError."""
        for _ in range(5):
            self.trusted(url)
            try:
                reply = requests.request(method, url, data=body.encode() if isinstance(body, str) else body,
                                         headers=headers or {}, auth=self.auth, timeout=TIMEOUT, allow_redirects=False)
            except requests.RequestException as error:
                raise ServiceError("Keine Verbindung zu iCloud") from error
            if reply.status_code in REDIRECTS and "location" in reply.headers:
                url = urljoin(url, reply.headers["location"])
                continue
            if reply.status_code == 401:
                raise ServiceError("iCloud lehnt die Anmeldung ab: Apple-ID oder app-spezifisches Passwort stimmt nicht")
            if reply.status_code == 412:
                raise ServiceError("Der Termin wurde inzwischen woanders geändert, bitte neu laden")
            if reply.status_code >= 400:
                raise ServiceError("iCloud: HTTP %d bei %s %s" % (reply.status_code, method, url))
            reply.final_url = url
            return reply
        raise ServiceError("iCloud leitet zu oft weiter")

    def multistatus(self, method, url, body, depth):
        """[(absolute href, {"{ns}name": element})] of every response, with the properties that came back 200."""
        reply = self.request(method, url, body, {"Depth": str(depth), "Content-Type": "application/xml; charset=utf-8"})
        try:
            root = ET.fromstring(reply.content)
        except ET.ParseError as error:
            raise ServiceError("iCloud hat unlesbares XML geschickt") from error
        results = []
        for response in root.findall("d:response", NS):
            href = urljoin(reply.final_url, response.findtext("d:href", "", NS))
            props = {}
            for propstat in response.findall("d:propstat", NS):
                found = propstat.find("d:prop", NS)
                if found is not None and " 200 " in propstat.findtext("d:status", "", NS) + " ":
                    for element in found:
                        props[element.tag] = element
            results.append((href, props))
        return results

    def propfind(self, url, names, depth=0):
        """names like "d:displayname"; returns multistatus()."""
        props = "".join("<%s/>" % name for name in names)
        body = ('<?xml version="1.0" encoding="utf-8"?><d:propfind xmlns:d="DAV:" xmlns:c="%s" xmlns:a="%s"'
                ' xmlns:cs="%s"><d:prop>%s</d:prop></d:propfind>' % (NS["c"], NS["a"], NS["cs"], props))
        return self.multistatus("PROPFIND", url, body, depth)

    def report(self, url, body):
        return self.multistatus("REPORT", url, body, 1)

    def get(self, url):
        """(text, etag) of one resource."""
        reply = self.request("GET", url)
        return reply.content.decode("utf-8"), reply.headers.get("etag")

    def put(self, url, text, condition):
        """condition: {"If-Match": etag} to replace, {"If-None-Match": "*"} to create only."""
        headers = dict(condition, **{"Content-Type": "text/calendar; charset=utf-8"})
        return self.request("PUT", url, text, headers).headers.get("etag")

    def delete(self, url, etag=None):
        self.request("DELETE", url, headers={"If-Match": etag} if etag else {})


def tag(name):
    """"c:calendar" -> "{urn:ietf:params:xml:ns:caldav}calendar"."""
    prefix, local = name.split(":")
    return "{%s}%s" % (NS[prefix], local)
