"""The app's own OAuth client (ADR 0001): read from google-client.json in the repository root.

Not for user input: the interface never asks for a client ID.
"""
import json
from pathlib import Path

CLIENT_FILE = Path(__file__).resolve().parents[3] / "google-client.json"


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
