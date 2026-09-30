"""The file the Ghostly QShell's island reads: the next events of the coming week, written atomically."""
import json
import os

ISLAND_FILE = os.path.join(os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache"),
                           "calendary", "upcoming.json")
LIMIT = 8


def upcoming(events, now):
    """Events that have not ended, soonest first, all-day before timed on the same start."""
    ahead = sorted((e for e in events if e["end"] > now), key=lambda e: (e["start"], not e["allDay"]))
    return [{key: e[key] for key in ("title", "start", "end", "allDay", "color", "calendar", "location")}
            for e in ahead[:LIMIT]]


def write_island(path, now, events):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temporary = path + ".tmp"
    with open(temporary, "w") as f:
        json.dump({"updated": now, "events": upcoming(events, now)}, f)
    os.replace(temporary, path)
