"""Secrets in the Secret Service through `secret-tool`, one item per account and service. Never in a file.

On Windows `Keyring` is the Credential Manager from platform/windows.py, with the same calls.

Google refresh tokens use the service `calendary`, iCloud app-specific passwords `calendary-icloud`.
"""
import subprocess
import sys

from calendary.errors import ServiceError

TIMEOUT = 20


class Keyring:
    """`service` separates the app's items from everything else in the keyring; tests pass their own."""

    def __init__(self, service="calendary"):
        self.service = service

    def _run(self, args, secret=None):
        try:
            return subprocess.run(["secret-tool", *args], input=secret, capture_output=True, timeout=TIMEOUT)
        except (OSError, subprocess.SubprocessError) as error:
            raise ServiceError("Schlüsselbund nicht erreichbar (secret-tool): %s" % error) from error

    def store(self, email, token):
        done = self._run(["store", "--label", "Calendary (%s): %s" % (self.service, email), "service", self.service, "account", email],
                         token.encode())
        if done.returncode != 0:
            raise ServiceError("Anmeldung konnte nicht im Schlüsselbund gespeichert werden")

    def lookup(self, email):
        """The refresh token, or None when the keyring has none for this account."""
        done = self._run(["lookup", "service", self.service, "account", email])
        return done.stdout.decode().strip() or None

    def clear(self, email):
        self._run(["clear", "service", self.service, "account", email])


if sys.platform == "win32":
    from calendary.platform.windows import CredentialManager as Keyring  # noqa: F811
