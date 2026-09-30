"""What Calendary remembers: view, week start, theme, hidden calendars, hour height and window size.

Values are JSON in $XDG_CONFIG_HOME/calendary/calendary.ini, written the moment they change. The shell's font and
reduced-motion setting are exposed here too, read once at start (see desktop.py). Not for colours.
"""
import json
import os

from PySide6.QtCore import Property, QObject, QSettings, Slot
from PySide6.QtQml import QJSValue

from calendary import desktop

PREFERENCES_FILE = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"),
                                "calendary", "calendary.ini")


class Preferences(QObject):
    def __init__(self, path=PREFERENCES_FILE, shell=None):
        super().__init__()
        self._settings = QSettings(path, QSettings.IniFormat)
        self._desktop = desktop.read(shell or desktop.SHELL)

    fontUi = Property(str, lambda self: self._desktop["fontUi"], constant=True)
    reducedMotion = Property(bool, lambda self: self._desktop["reducedMotion"], constant=True)

    @Slot(str, "QVariant", result="QVariant")
    def get(self, key, default=None):
        raw = self._settings.value(key)
        if raw is None:
            return default
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return default

    @Slot(str, "QVariant")
    def set(self, key, value):
        # Nested JS objects arrive as QJSValue; json needs plain Python values.
        if isinstance(value, QJSValue):
            value = value.toVariant()
        encoded = json.dumps(value)
        if self._settings.value(key) != encoded:
            self._settings.setValue(key, encoded)
            self._settings.sync()
