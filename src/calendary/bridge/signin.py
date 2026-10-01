"""Accounts: Google browser sign-in, iCloud with Apple ID and app-specific password, restoring and signing out.

Secrets go to the keyring only after they worked once. Not for syncing.
"""
import re

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices

from calendary import cache
from calendary.caldav import ICloudAccount, apple_id_of, is_icloud
from calendary.google import Account, Login, import_client, load_client
from calendary.language import tr

APP_PASSWORD = re.compile(r"[a-z]{4}-?[a-z]{4}-?[a-z]{4}-?[a-z]{4}")


class SignIn:
    def __init__(self, calendar, keyrings, client_file):
        """keyrings: {"google": Keyring, "icloud": Keyring}."""
        self.calendar, self.keyrings, self.client_file = calendar, keyrings, client_file
        self.login = None
        self.connecting = False

    def ready(self):
        return load_client(self.client_file) is not None

    def restore(self):
        """Accounts in the cache get their secrets back from the keyring, then everything syncs."""
        client = load_client(self.client_file)
        keys = [key for key in cache.accounts(self.calendar.db) if is_icloud(key) or client]
        if not keys:
            return

        def secrets():
            return {key: self.keyrings["icloud"].lookup(apple_id_of(key)) if is_icloud(key)
                    else self.keyrings["google"].lookup(key) for key in keys}

        def ready(found):
            for key, secret in found.items():
                if not secret:
                    self.calendar.say(tr("%s ist abgemeldet, bitte neu anmelden") % display(key), True)
                elif is_icloud(key):
                    self.calendar.remote[key] = ICloudAccount(apple_id_of(key), secret)
                else:
                    self.calendar.remote[key] = Account(client, key, secret)
            self.calendar.sync.everything()
        self.calendar.worker.run(secrets, ready)

    def start(self):
        client = load_client(self.client_file)
        if not client:
            self.calendar.say(tr("Google-Anmeldung ist nicht eingerichtet: zuerst in den Einstellungen die Client-Datei wählen"), True)
            return
        if self.login:
            return
        login = self.login = Login(client)
        self.calendar.signing_changed()
        if not QDesktopServices.openUrl(QUrl(login.url)):
            login.cancel()

        def job():
            email, token = login.wait()
            self.keyrings["google"].store(email, token)
            return Account(client, email, token)
        self.calendar.worker.run(job, self.added, self.finished)

    def import_client(self, url):
        """Takes the client file the user picked (a file URL) as this installation's Google client."""
        try:
            usable = import_client(QUrl(url).toLocalFile(), self.client_file)
        except OSError as error:
            self.calendar.say(tr("Client-Datei nicht übernommen: %s") % (error.strerror or error), True)
            return
        if not usable:
            self.calendar.say(tr("Das ist keine Client-Datei vom Typ Desktop-App aus der Google Cloud Console"), True)
            return
        self.calendar.accounts_changed()
        self.calendar.say(tr("Google-Anmeldung ist eingerichtet"), False)

    def connect_icloud(self, apple_id, password):
        """Checks the input, signs in once, and only then stores the password; False when the input is unusable."""
        apple_id, typed = apple_id.strip(), password.replace(" ", "").strip().lower()
        if "@" not in apple_id or not APP_PASSWORD.fullmatch(typed):
            self.calendar.say(tr("Apple-ID und ein app-spezifisches Passwort (xxxx-xxxx-xxxx-xxxx) eingeben"), True)
            return False
        # Apple shows these passwords as four dashed groups; keep that form whatever was typed.
        letters = typed.replace("-", "")
        password = "-".join(letters[i:i + 4] for i in range(0, 16, 4))
        if self.connecting:
            return False
        self.connecting = True
        self.calendar.signing_changed()

        def job():
            account = ICloudAccount(apple_id, password)
            account.verify()
            self.keyrings["icloud"].store(apple_id.lower(), password)
            return account
        self.calendar.worker.run(job, self.added, self.finished)
        return True

    def added(self, account):
        self.finished()
        cache.add_account(self.calendar.db, account.email)
        self.calendar.remote[account.email] = account
        self.calendar.accounts_changed()
        self.calendar.say(tr("%s ist verbunden") % display(account.email), False)
        self.calendar.sync.refresh(account.email)

    def finished(self):
        self.login = None
        self.connecting = False
        self.calendar.signing_changed()

    def cancel(self):
        if self.login:
            self.login.cancel()

    def remove(self, key):
        self.calendar.remote.pop(key, None)
        cache.remove_account(self.calendar.db, key)
        self.calendar.accounts_changed()
        self.calendar.bump()
        if is_icloud(key):
            self.calendar.worker.run(lambda: self.keyrings["icloud"].clear(apple_id_of(key)), lambda _: None)
        else:
            self.calendar.worker.run(lambda: self.keyrings["google"].clear(key), lambda _: None)


def display(key):
    """The address the interface shows for an account key."""
    return apple_id_of(key) if is_icloud(key) else key
