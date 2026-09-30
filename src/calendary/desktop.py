"""The two things Calendary takes from the Ghostly QShell: its UI font and its reduced-motion switch (ADR 0003).

Read from the shell's preferences.ini; without the shell the system sans and full motion apply. Not for colours.
"""
import os
from pathlib import Path

from PySide6.QtCore import QSettings

SHELL = Path(os.environ.get("CALENDARY_SHELL", Path.home() / ".config/quickshell/ghostly-qshell"))
FALLBACK_FONT = "sans-serif"


def read(shell=SHELL):
    ini = Path(shell) / "preferences.ini"
    if not ini.exists():
        return {"fontUi": FALLBACK_FONT, "reducedMotion": False}
    settings = QSettings(str(ini), QSettings.IniFormat)
    settings.beginGroup("Shell")
    return {"fontUi": str(settings.value("fontUi", FALLBACK_FONT)) or FALLBACK_FONT,
            "reducedMotion": str(settings.value("reducedMotion", "false")).lower() == "true"}
