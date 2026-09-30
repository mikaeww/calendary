"""Google: the app's OAuth client, browser sign-in and the Calendar API.

Everything here blocks on the network or on `secret-tool`; callers run it on worker threads. No caching.
"""
from calendary.google.api import Account
from calendary.google.auth import Login, pkce
from calendary.google.client import CLIENT_FILE, load_client
from calendary.google.errors import GoogleError

__all__ = ["CLIENT_FILE", "Account", "GoogleError", "Login", "load_client", "pkce"]
