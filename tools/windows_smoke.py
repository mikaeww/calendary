"""Smoke test of an installed Windows build, run by its bundled python.exe: imports, keyring, window, fonts.

  <install dir>\\python\\python.exe tools\\windows_smoke.py [SCREENSHOT.png]

Opens the real Main.qml on the Windows platform with the runner's real paths and writes a test credential, so only
for the disposable CI machine.
"""
import sqlite3
import ssl
import sys
import time
import zoneinfo

import shiboken6
from PySide6.QtGui import QFont, QFontInfo, QGuiApplication
from PySide6.QtQuick import QQuickWindow

from calendary import desktop
from calendary.app import build_engine
from calendary.google.client import CLIENT_FILE
from calendary.keyring import Keyring


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
    app = QGuiApplication(sys.argv[:1])
    engine = build_engine()
    checks["window loads"] = bool(engine.rootObjects())
    family = desktop.read()["fontUi"]
    print("platform %s, UI font %r resolves to %s" % (app.platformName(), family, QFontInfo(QFont(family)).family()))
    checks["real Windows platform"] = app.platformName() == "windows"
    if checks["window loads"] and len(sys.argv) > 1:
        window = shiboken6.wrapInstance(shiboken6.getCppPointer(engine.rootObjects()[0])[0], QQuickWindow)
        for _ in range(100):
            app.processEvents()
            time.sleep(0.02)
        window.grabWindow().save(sys.argv[1])
    for name, ok in checks.items():
        print(("ok    " if ok else "FAIL  ") + name)
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
