"""The interface language: German as written in the code, English from english.json, the system's choice by default.

QML marks its text with qsTr(), Python with tr(); both read the same table. Text without an entry stays German, so
tests/test_language.py keeps the table complete. Not for dates and times, which stay day.month.year and 24 hours.
"""
import json
from pathlib import Path

from PySide6.QtCore import QLocale, QTranslator

ENGLISH = json.loads(Path(__file__).with_name("english.json").read_text(encoding="utf-8"))
_current = ["de"]


def resolve(choice):
    """"de" or "en" for a saved choice; "system" means German on a German system and English everywhere else."""
    if choice in ("de", "en"):
        return choice
    return "de" if QLocale.system().language() == QLocale.Language.German else "en"


def use(choice):
    _current[0] = resolve(choice)


def tr(text):
    """German text in the interface language."""
    return ENGLISH.get(text, text) if _current[0] == "en" else text


class Translator(QTranslator):
    """qsTr() through the same table; None tells Qt to keep the German source."""

    def translate(self, context, source, disambiguation=None, n=-1):
        return ENGLISH.get(source) if _current[0] == "en" else None
