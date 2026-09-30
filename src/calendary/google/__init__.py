"""Google: the app's OAuth client, browser sign-in, refresh tokens in the keyring and the Calendar API.

Everything here blocks on the network or on `secret-tool`; callers run it on worker threads. No caching.
"""
from calendary.google.api import Account
from calendary.google.auth import Login, pkce
from calendary.google.client import CLIENT_FILE, load_client
from calendary.google.errors import GoogleError
from calendary.google.keyring import Keyring

__all__ = ["CLIENT_FILE", "Account", "GoogleError", "Keyring", "Login", "load_client", "pkce"]
