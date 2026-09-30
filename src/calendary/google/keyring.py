"""Refresh tokens in the Secret Service through `secret-tool`, one item per account. Never in a file."""
import subprocess

from calendary.google.errors import GoogleError

TIMEOUT = 20


class Keyring:
    """`service` separates the app's items from everything else in the keyring; tests pass their own."""

    def __init__(self, service="calendary"):
        self.service = service

    def _run(self, args, secret=None):
        try:
            return subprocess.run(["secret-tool", *args], input=secret, capture_output=True, timeout=TIMEOUT)
        except (OSError, subprocess.SubprocessError) as error:
            raise GoogleError("Schlüsselbund nicht erreichbar (secret-tool): %s" % error) from error

    def store(self, email, token):
        done = self._run(["store", "--label", "Calendary: " + email, "service", self.service, "account", email],
                         token.encode())
        if done.returncode != 0:
            raise GoogleError("Anmeldung konnte nicht im Schlüsselbund gespeichert werden")

    def lookup(self, email):
        """The refresh token, or None when the keyring has none for this account."""
        done = self._run(["lookup", "service", self.service, "account", email])
        return done.stdout.decode().strip() or None

    def clear(self, email):
        self._run(["clear", "service", self.service, "account", email])
