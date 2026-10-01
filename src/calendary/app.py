"""Wiring: icon font, interface language, the QML singletons and the window. The offscreen checks use this too."""
import sys
from pathlib import Path

from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QFontDatabase
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterSingletonInstance

from calendary import language
from calendary.bridge import Calendar
from calendary.preferences import Preferences

QML = Path(__file__).resolve().parent / "qml"
ICON_FONT = Path(__file__).resolve().parents[2] / "assets/fonts/calendary-icons.ttf"
_alive = []
# One translator for the process: installing it again is a no-op, a second one would answer first.
_translator = language.Translator()


def build_engine(preferences=None, calendar=None):
    """Loads Main.qml with the given singletons (fresh real ones by default); Python keeps them alive."""
    if QFontDatabase.addApplicationFont(str(ICON_FONT)) < 0:
        print("calendary: icon font missing at %s, buttons show boxes" % ICON_FONT, file=sys.stderr)
    preferences = preferences or Preferences()
    calendar = calendar or Calendar(preferences)
    QCoreApplication.installTranslator(_translator)
    _alive[:] = [preferences, calendar]
    qmlRegisterSingletonInstance(Preferences, "Calendary", 1, 0, "Preferences", preferences)
    qmlRegisterSingletonInstance(Calendar, "Calendary", 1, 0, "Calendar", calendar)
    engine = QQmlApplicationEngine()
    # Qt.uiLanguage holds the saved choice ("system", "de" or "en"); the settings sheet changes it.
    engine.uiLanguageChanged.connect(lambda: (language.use(engine.uiLanguage()), engine.retranslate()))
    # Applied directly as well: Qt starts uiLanguage at the system's language, which may equal the choice and not emit.
    language.use(preferences.get("language", "system"))
    engine.setUiLanguage(preferences.get("language", "system"))
    engine.load(str(QML / "Main.qml"))
    return engine
