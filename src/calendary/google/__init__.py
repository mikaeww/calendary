"""Google: the user's own OAuth client, browser sign-in and the Calendar API.

Everything here blocks on the network or on `secret-tool`; callers run it on worker threads. No caching.
"""
from calendary.google.api import Account
from calendary.google.auth import Login, pkce
from calendary.google.client import CLIENT_FILE, import_client, load_client
from calendary.google.errors import GoogleError

__all__ = ["CLIENT_FILE", "Account", "GoogleError", "Login", "import_client", "load_client", "pkce"]
