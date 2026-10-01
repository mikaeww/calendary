#!/bin/sh
# Builds the Hyprland preload and links Calendary, its launcher entry and icons into ~/.local.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$here/build"
cc -shared -fPIC -O2 -Wall -o "$here/build/libnosuspend.so" "$here/src/calendary/platform/nosuspend.c" -lwayland-client -ldl
icons=~/.local/share/icons/hicolor
mkdir -p ~/.local/bin ~/.local/share/applications "$icons/scalable/apps"
ln -sf "$here/calendary" ~/.local/bin/calendary
ln -sf "$here/calendary.desktop" ~/.local/share/applications/calendary.desktop
ln -sf "$here/assets/icons/calendary.svg" "$icons/scalable/apps/calendary.svg"
for size in 16 24 32 48; do
    mkdir -p "$icons/${size}x${size}/apps"
    ln -sf "$here/assets/icons/calendary-mini-$size.png" "$icons/${size}x${size}/apps/calendary.png"
done
for size in 64 128 256 512; do
    mkdir -p "$icons/${size}x${size}/apps"
    ln -sf "$here/assets/icons/calendary-$size.png" "$icons/${size}x${size}/apps/calendary.png"
done
update-desktop-database ~/.local/share/applications 2>/dev/null || true
gtk-update-icon-cache -q -t "$icons" 2>/dev/null || true
if [ ! -f "${XDG_CONFIG_HOME:-$HOME/.config}/calendary/google-client.json" ]; then
    echo "Hinweis: Für Google fehlt noch der eigene OAuth-Client, siehe README (Google setup)."
fi
echo "calendary installiert"
