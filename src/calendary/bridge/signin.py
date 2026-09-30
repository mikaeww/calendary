"""Accounts: browser sign-in, restoring signed-in accounts at start, signing out. Not for syncing."""
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices

from calendary import cache
from calendary.google import Account, Login, load_client

MISSING_CLIENT = "Google-Anmeldung ist nicht eingerichtet: google-client.json fehlt im App-Ordner (siehe README)"


class SignIn:
    def __init__(self, calendar, keyring, client_file):
        self.calendar, self.keyring, self.client_file = calendar, keyring, client_file
        self.login = None

    def ready(self):
        return load_client(self.client_file) is not None

    def restore(self):
        """Accounts in the cache get their refresh tokens back from the keyring, then everything syncs."""
        client = load_client(self.client_file)
        emails = cache.accounts(self.calendar.db)
        if not client or not emails:
            return

        def ready(tokens):
            for email, token in tokens.items():
                if token:
                    self.calendar.remote[email] = Account(client, email, token)
                else:
                    self.calendar.say("%s ist abgemeldet, bitte neu anmelden" % email, True)
            self.calendar.sync.everything()
        self.calendar.worker.run(lambda: {email: self.keyring.lookup(email) for email in emails}, ready)

    def start(self):
        client = load_client(self.client_file)
        if not client:
            self.calendar.say(MISSING_CLIENT, True)
            return
        if self.login:
            return
        login = self.login = Login(client)
        self.calendar.signing_changed()
        if not QDesktopServices.openUrl(QUrl(login.url)):
            login.cancel()

        def job():
            email, token = login.wait()
            self.keyring.store(email, token)
            return email, token

        def done(result):
            email, token = result
            self.finished()
            cache.add_account(self.calendar.db, email)
            self.calendar.remote[email] = Account(client, email, token)
            self.calendar.accounts_changed()
            self.calendar.say("%s ist verbunden" % email, False)
            self.calendar.sync.refresh(email)
        self.calendar.worker.run(job, done, self.finished)

    def finished(self):
        self.login = None
        self.calendar.signing_changed()

    def cancel(self):
        if self.login:
            self.login.cancel()

    def remove(self, email):
        self.calendar.remote.pop(email, None)
        cache.remove_account(self.calendar.db, email)
        self.calendar.accounts_changed()
        self.calendar.bump()
        self.calendar.worker.run(lambda: self.keyring.clear(email), lambda _: None)
