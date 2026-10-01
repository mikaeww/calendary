"""The `Calendar` QML singleton: read slots for week and month, and thin slots onto sync, edits and sign-in.

Owns the database connection (GUI thread only), the worker and the signed-in accounts. The island file is
rewritten after every change. Not for Google specifics or layout rules; those live in their packages.
"""
import time

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

from calendary import cache, layout
from calendary.bridge.edits import Edits
from calendary.bridge.island import ISLAND_FILE, write_island
from calendary.bridge.signin import SignIn, display
from calendary.caldav import is_icloud
from calendary.bridge.sync import STALE_SECONDS, Sync
from calendary.bridge.worker import Worker
from calendary.google import CLIENT_FILE
from calendary.keyring import Keyring

WEEK_MS = 7 * 86400000


class Calendar(QObject):
    changed = Signal()
    accountsChanged = Signal()
    busyChanged = Signal()
    signingChanged = Signal()
    notice = Signal(str, bool)

    def __init__(self, preferences, db=None, keyring=None, files=None):
        """keyring: one keyring for both providers (tests); files: {"island": path, "client": path}."""
        super().__init__()
        files = files or {}
        self.preferences = preferences
        self.db = db or cache.connect()
        self.island = files.get("island", ISLAND_FILE)
        self.remote = {}
        self.revision_ = 0
        self.worker = Worker()
        self.worker.busyChanged.connect(self.busyChanged)
        self.worker.failed.connect(lambda message: self.say(message, True))
        self.sync = Sync(self)
        self.edits = Edits(self)
        keyrings = {"google": keyring, "icloud": keyring} if keyring else {"google": Keyring(),
                                                                           "icloud": Keyring("calendary-icloud")}
        self.signin = SignIn(self, keyrings, files.get("client", CLIENT_FILE))
        self.timer = QTimer(self, interval=STALE_SECONDS * 1000, timeout=self.sync.everything)
        self.timer.start()
        self.export_island()
        self.signin.restore()

    # --- shared by the parts

    def say(self, text, bad):
        self.notice.emit(text, bad)

    def bump(self):
        self.revision_ += 1
        self.changed.emit()
        self.export_island()

    def accounts_changed(self):
        self.accountsChanged.emit()
        self.bump()

    def signing_changed(self):
        self.signingChanged.emit()

    def hidden(self):
        return set(self.preferences.get("hidden", []) or [])

    def export_island(self):
        now = int(time.time() * 1000)
        try:
            write_island(self.island, now, cache.between(self.db, now, now + WEEK_MS, self.hidden()))
        except OSError as error:
            self.say("Island-Datei nicht schreibbar: %s" % error, True)

    # --- properties

    revision = Property(int, lambda self: self.revision_, notify=changed)
    busy = Property(bool, lambda self: self.worker.busy, notify=busyChanged)
    signingIn = Property(bool, lambda self: self.signin.login is not None, notify=signingChanged)
    connecting = Property(bool, lambda self: self.signin.connecting, notify=signingChanged)
    ready = Property(bool, lambda self: self.signin.ready(), notify=accountsChanged)

    def account_list(self):
        """Per account: key (for actions), name (to show), provider, and its calendars."""
        hidden = self.hidden()
        accounts = []
        for key in cache.accounts(self.db):
            provider = "icloud" if is_icloud(key) else "google"
            accounts.append({"key": key, "name": display(key), "provider": provider, "calendars": [
                {"key": cache.event_key(key, row["id"]), "name": row["name"], "color": row["color"],
                 "writable": bool(row["writable"]), "main": bool(row["main"]), "provider": provider,
                 "visible": cache.event_key(key, row["id"]) not in hidden}
                for row in cache.calendars(self.db, key)]})
        return accounts

    accounts = Property("QVariantList", account_list, notify=accountsChanged)

    # --- reading

    @Slot(float, int, result="QVariantMap")
    def week(self, start, days):
        edges = layout.day_edges(int(start), days)
        return layout.week(cache.between(self.db, edges[0], edges[-1], self.hidden()), int(start), days)

    @Slot(float, result="QVariantList")
    def month(self, start):
        edges = layout.day_edges(int(start), 42)
        return layout.month(cache.between(self.db, edges[0], edges[-1], self.hidden()), int(start))

    # --- actions

    @Slot(float, float)
    def show(self, start, end):
        self.sync.show(int(start), int(end))

    @Slot()
    def refresh(self):
        self.sync.everything()

    @Slot()
    def signIn(self):
        self.signin.start()

    @Slot(str)
    def importClient(self, url):
        self.signin.import_client(url)

    @Slot()
    def cancelSignIn(self):
        self.signin.cancel()

    @Slot(str, str, result=bool)
    def connectICloud(self, apple_id, password):
        return self.signin.connect_icloud(apple_id, password)

    @Slot(str)
    def signOut(self, key):
        self.signin.remove(key)

    @Slot(str, bool)
    def setVisible(self, calendar_key, visible):
        hidden = self.hidden() - {calendar_key} if visible else self.hidden() | {calendar_key}
        self.preferences.set("hidden", sorted(hidden))
        self.accounts_changed()

    @Slot("QVariantMap")
    def save(self, fields):
        self.edits.save(dict(fields))

    @Slot(str)
    def remove(self, key):
        self.edits.remove(key)
