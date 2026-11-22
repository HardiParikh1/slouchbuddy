"""Helpers for starting the background monitor, dashboard and buddy as child processes."""
import os
import subprocess
import sys

DASHBOARD_PORT = 8501
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))


def spawn_monitor():
    """Start the hidden camera monitor (writes status for the menu bar / buddy)."""
    return subprocess.Popen([sys.executable, "-m", "slouchbuddy.app", "--background"])


def spawn_dashboard(port=DASHBOARD_PORT):
    return subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", os.path.join(PACKAGE_DIR, "dashboard.py"),
            "--server.headless", "true", "--server.port", str(port),
            "--client.toolbarMode", "minimal",
            "--theme.primaryColor", "#5b9a76",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def spawn_buddy(with_monitor=False):
    """Start the desktop buddy. By default it only attaches to an already-running monitor."""
    args = [sys.executable, "-m", "slouchbuddy.buddy"]
    if not with_monitor:
        args.append("--no-monitor")
    return subprocess.Popen(args)
