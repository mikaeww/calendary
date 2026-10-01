"""The English table against the source: every marked German text has an entry, no entry is stale, placeholders match."""
import json
import re
import unittest
from pathlib import Path

from calendary import language

SRC = Path(__file__).resolve().parent.parent / "src/calendary"
MARKED = {".qml": re.compile(r'\bqsTr\("((?:[^"\\]|\\.)*)"\)'), ".js": re.compile(r'\bqsTr\("((?:[^"\\]|\\.)*)"\)'),
          ".py": re.compile(r'\btr\("((?:[^"\\]|\\.)*)"\)')}
PLACEHOLDER = re.compile(r"%\d|%[sd]")


def marked_texts():
    found = set()
    for path in SRC.rglob("*"):
        if path.suffix in MARKED:
            found |= {json.loads('"%s"' % raw) for raw in MARKED[path.suffix].findall(path.read_text(encoding="utf-8"))}
    return found


class LanguageTest(unittest.TestCase):
    def test_table_matches_the_source(self):
        marked = marked_texts()
        self.assertGreater(len(marked), 100, "the extraction found the marked texts")
        self.assertEqual(sorted(marked - language.ENGLISH.keys()), [], "German text without English entry")
        self.assertEqual(sorted(language.ENGLISH.keys() - marked), [], "English entry nothing uses")

    def test_placeholders_survive(self):
        for german, english in language.ENGLISH.items():
            self.assertEqual(sorted(PLACEHOLDER.findall(german)), sorted(PLACEHOLDER.findall(english)), german)

    def test_choice(self):
        try:
            language.use("en")
            self.assertEqual(language.tr("Keine Verbindung zu Google"), "No connection to Google")
            self.assertEqual(language.Translator().translate("Main", "Heute"), "Today")
            language.use("de")
            self.assertEqual(language.tr("Keine Verbindung zu Google"), "Keine Verbindung zu Google")
            self.assertIsNone(language.Translator().translate("Main", "Heute"))
            self.assertIn(language.resolve("system"), ("de", "en"))
        finally:
            language.use("de")


if __name__ == "__main__":
    unittest.main()
