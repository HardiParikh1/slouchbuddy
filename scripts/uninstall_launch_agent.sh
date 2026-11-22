#!/bin/sh
PLIST="$HOME/Library/LaunchAgents/com.posturemonitor.reminder.plist"
launchctl unload "$PLIST" 2>/dev/null || true
rm -f "$PLIST"
echo "Uninstalled."
