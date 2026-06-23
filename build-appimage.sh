#!/usr/bin/env bash
set -euo pipefail

APPIMAGE="Universal-Netlimiter-x86_64.AppImage"
APPDIR="/tmp/netlimiter-appdir"

echo "=== Clean up old build ==="
rm -rf "$APPDIR"
rm -f "$APPIMAGE"

echo "=== Extract existing AppImage ==="
cd /tmp
/home/gustl/Netlimiter/Universal-Netlimiter-x86_64.AppImage --appimage-extract
mv squashfs-root "$APPDIR"

echo "=== Replace netlimiter.py ==="
cp /home/gustl/Netlimiter/netlimiter.py "$APPDIR/netlimiter.py"

echo "=== Build AppImage ==="
/tmp/appimagetool "$APPDIR" /home/gustl/Netlimiter/"$APPIMAGE"

echo "=== Done ==="
ls -lh /home/gustl/Netlimiter/"$APPIMAGE"
