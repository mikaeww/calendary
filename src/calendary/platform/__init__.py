"""Platform workarounds that only make sense on Hyprland; nothing portable lives here."""
from calendary.platform.preload import preload_nosuspend

__all__ = ["preload_nosuspend"]
