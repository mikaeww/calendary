#!/usr/bin/env python3
"""Builds the Windows installer: embeddable Python, the wheels, src/, the icons and the OAuth client, packed by NSIS.

Runs on Windows with the Python version it bundles and `makensis` on PATH; the release workflow sets up both. The
checkout layout is kept (python/, src/, assets/, google-client.json side by side), so every path the package
derives from `__file__` holds unchanged. Not for Linux, which runs from the checkout (install.sh).

  python tools/build_windows.py VERSION     writes dist/Calendary-VERSION-x64-setup.exe
"""
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
STAGE = DIST / "stage"
PACKAGES = ["PySide6-Essentials==6.11.1", "requests", "python-dateutil", "tzdata"]
IGNORE = shutil.ignore_patterns("__pycache__", "*.c")


def embed_python(target):
    """The official embeddable zip of the running version; its ._pth file is the only search path Python uses."""
    version = "%d.%d.%d" % sys.version_info[:3]
    archive = DIST / "python-embed.zip"
    urllib.request.urlretrieve(f"https://www.python.org/ftp/python/{version}/python-{version}-embed-amd64.zip",
                               archive)
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(target)
    pth = next(target.glob("python*._pth"))
    pth.write_text(pth.read_text() + "Lib\\site-packages\n..\\src\n")
    subprocess.run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "--no-warn-script-location",
                    "--target", str(target / "Lib/site-packages"), *PACKAGES], check=True)


def stage():
    client = ROOT / "google-client.json"
    if not client.exists():
        raise SystemExit("build: google-client.json is missing, the installed app could not sign in to Google")
    shutil.rmtree(STAGE, ignore_errors=True)
    STAGE.mkdir(parents=True)
    embed_python(STAGE / "python")
    shutil.copytree(ROOT / "src/calendary", STAGE / "src/calendary", ignore=IGNORE)
    shutil.copytree(ROOT / "assets/icons", STAGE / "assets/icons")
    for name in ("google-client.json", "LICENSE"):
        shutil.copy2(ROOT / name, STAGE / name)


def main():
    if sys.platform != "win32" or len(sys.argv) != 2 or not re.fullmatch(r"\d+\.\d+\.\d+", sys.argv[1]):
        raise SystemExit(__doc__)
    version = sys.argv[1]
    stage()
    installer = DIST / f"Calendary-{version}-x64-setup.exe"
    subprocess.run(["makensis", "/V2", f"/DVERSION={version}", f"/DSTAGE={STAGE}", f"/DOUTFILE={installer}",
                    str(ROOT / "packaging/windows/calendary.nsi")], check=True)
    print(installer)


if __name__ == "__main__":
    main()
