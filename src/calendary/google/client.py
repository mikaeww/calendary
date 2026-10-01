"""The OAuth client of the user's own Google Cloud project (ADR 0007): google-client.json in the config folder.

No client ships with Calendary. Each installation picks the JSON that Google offers for download once in the
settings; `import_client` checks it and copies it into place. Not for typing client IDs into the interface.
"""
import json
import os
import shutil
from pathlib import Path

CLIENT_FILE = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "calendary" / "google-client.json"


def load_client(path=CLIENT_FILE):
    """{client_id, client_secret} from Google's download format or the plain form, or None if unusable."""
    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    data = data.get("installed", data)
    if not isinstance(data, dict) or not data.get("client_id") or not data.get("client_secret"):
        return None
    return {"client_id": str(data["client_id"]), "client_secret": str(data["client_secret"])}


def import_client(source, target=CLIENT_FILE):
    """Copies a downloaded client file to `target` when it holds a usable client; False otherwise, target untouched.

    Raises OSError when the copy fails.
    """
    if load_client(source) is None:
        return False
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".partial")
    shutil.copyfile(source, partial)
    # The client secret is not a password, but there is no reason for other users to read it.
    os.chmod(partial, 0o600)
    os.replace(partial, target)
    return True
