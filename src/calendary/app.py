"""Wiring: registers the QML singletons and loads the window. The offscreen checks use this too."""
from pathlib import Path

from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterSingletonInstance

from calendary.bridge import Calendar
from calendary.preferences import Preferences

QML = Path(__file__).resolve().parent / "qml"
_alive = []


def build_engine(preferences=None, calendar=None):
    """Loads Main.qml with the given singletons (fresh real ones by default); Python keeps them alive."""
    preferences = preferences or Preferences()
    calendar = calendar or Calendar(preferences)
    _alive[:] = [preferences, calendar]
    qmlRegisterSingletonInstance(Preferences, "Calendary", 1, 0, "Preferences", preferences)
    qmlRegisterSingletonInstance(Calendar, "Calendary", 1, 0, "Calendar", calendar)
    engine = QQmlApplicationEngine()
    engine.load(str(QML / "Main.qml"))
    return engine
