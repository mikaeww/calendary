"""Smoke test of an installed Windows build, run by its bundled python.exe: imports, keyring, window.

  <install dir>\\python\\python.exe tools\\windows_smoke.py

Loads the real Main.qml offscreen with the runner's real paths and writes a test credential, so only for the
disposable CI machine.
"""
import os
import sqlite3
import ssl
import sys
import zoneinfo

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtGui import QGuiApplication  # noqa: E402

from calendary.app import build_engine  # noqa: E402
from calendary.google.client import CLIENT_FILE  # noqa: E402
from calendary.keyring import Keyring  # noqa: E402


def credential_round_trip():
    keyring = Keyring("calendary-smoke")
    keyring.store("smoke@example.com", "token")
    found = keyring.lookup("smoke@example.com")
    keyring.clear("smoke@example.com")
    return found == "token" and keyring.lookup("smoke@example.com") is None


def main():
    checks = {"keyring is the Credential Manager": Keyring.__name__ == "CredentialManager",
              "OAuth client installed": CLIENT_FILE.exists(),
              "time zones": zoneinfo.ZoneInfo("Europe/Berlin").key == "Europe/Berlin",
              "ssl and sqlite": bool(ssl.OPENSSL_VERSION and sqlite3.sqlite_version),
              "credential round trip": credential_round_trip()}
    app = QGuiApplication(sys.argv)
    engine = build_engine()
    checks["window loads"] = bool(engine.rootObjects())
    app.processEvents()
    for name, ok in checks.items():
        print(("ok    " if ok else "FAIL  ") + name)
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
