"""`python3 -m calendary`: the Hyprland workaround, the application object and the window."""
import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication, QIcon

from calendary.app import build_engine
from calendary.platform import preload_nosuspend

ICON = Path(__file__).resolve().parents[2] / "assets/icons/calendary.svg"


def main():
    preload_nosuspend()
    QGuiApplication.setApplicationName("Calendary")
    QGuiApplication.setDesktopFileName("calendary")
    app = QGuiApplication(sys.argv)
    app.setWindowIcon(QIcon(str(ICON)))
    engine = build_engine()
    if not engine.rootObjects():
        return 1
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
