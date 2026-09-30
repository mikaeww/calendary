"""Wiring: registers the icon font and the QML singletons and loads the window. The offscreen checks use this too."""
import sys
from pathlib import Path

from PySide6.QtGui import QFontDatabase
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterSingletonInstance

from calendary.bridge import Calendar
from calendary.preferences import Preferences

QML = Path(__file__).resolve().parent / "qml"
ICON_FONT = Path(__file__).resolve().parents[2] / "assets/fonts/calendary-icons.ttf"
_alive = []


def build_engine(preferences=None, calendar=None):
    """Loads Main.qml with the given singletons (fresh real ones by default); Python keeps them alive."""
    if QFontDatabase.addApplicationFont(str(ICON_FONT)) < 0:
        print("calendary: icon font missing at %s, buttons show boxes" % ICON_FONT, file=sys.stderr)
    preferences = preferences or Preferences()
    calendar = calendar or Calendar(preferences)
    _alive[:] = [preferences, calendar]
    qmlRegisterSingletonInstance(Preferences, "Calendary", 1, 0, "Preferences", preferences)
    qmlRegisterSingletonInstance(Calendar, "Calendary", 1, 0, "Calendar", calendar)
    engine = QQmlApplicationEngine()
    engine.load(str(QML / "Main.qml"))
    return engine
