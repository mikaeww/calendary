"""Platform code: the Hyprland suspend workaround here, Windows' keyring and taskbar entry in `windows`.

`windows` is imported only on Windows, by keyring.py and __main__.py; nothing portable lives here.
"""
from calendary.platform.preload import preload_nosuspend

__all__ = ["preload_nosuspend"]
