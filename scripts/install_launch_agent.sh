#!/bin/sh
# Installs a macOS LaunchAgent so the Posture Monitor menu bar app starts at login
# (monitoring in the background and nudging you on every wake). Use
# CAMERA_INDEX=1 sh scripts/install_launch_agent.sh to pick a different camera. Undo with scripts/uninstall_launch_agent.sh
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"
LABEL="com.posturemonitor.reminder"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

[ -x "$PYTHON" ] || { echo "Python not found at $PYTHON (set PYTHON=...)"; exit 1; }
mkdir -p "$HOME/Library/LaunchAgents"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PYTHON</string>
    <string>$ROOT/src/menubar.py</string>
  </array>
  <key>WorkingDirectory</key><string>$ROOT/src</string>
  <key>EnvironmentVariables</key>
  <dict><key>CAMERA_INDEX</key><string>${CAMERA_INDEX:-0}</string></dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
</dict>
</plist>
EOF

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
echo "Installed. Posture Monitor now starts at login and lives in your menu bar."
