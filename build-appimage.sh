#!/usr/bin/env bash
set -euo pipefail

APPIMAGE="Universal-Netlimiter-x86_64.AppImage"
APPDIR="/tmp/netlimiter-appdir"

echo "=== Clean up old build ==="
rm -rf "$APPDIR"

echo "=== Extract existing AppImage ==="
SRC="/home/gustl/Netlimiter/$APPIMAGE"
cd /tmp
"$SRC" --appimage-extract
mv squashfs-root "$APPDIR"
rm -f "$SRC"

echo "=== Replace netlimiter.py ==="
cp /home/gustl/Netlimiter/netlimiter.py "$APPDIR/netlimiter.py"

echo "=== Build AppImage ==="
/tmp/appimagetool -n "$APPDIR" /home/gustl/Netlimiter/"$APPIMAGE"

echo "=== Done ==="
ls -lh /home/gustl/Netlimiter/"$APPIMAGE"
