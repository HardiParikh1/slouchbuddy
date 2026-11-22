"""macOS menu bar app: runs the posture monitor in the background and shows the live
score in the menu bar. Click it to open the live camera view, calibrate, pause, etc.

    python src/menubar.py
"""
import os
import subprocess
import sys
import webbrowser

import rumps

import ipc
from wake_reminder import REMINDER_MESSAGE, REMINDER_TITLE, TICK_SECONDS, WakeDetector

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_PORT = 8501

ICONS = {
    "good": "🟢",
    "bad": "🔴",
    "no_pose": "👀",
    "uncalibrated": "🎯",
    "paused": "⏸",
    "camera_error": "📷",
}
STATE_TEXT = {
    "good": "Good posture",
    "bad": "Bad posture",
    "no_pose": "Can't see you",
    "uncalibrated": "Not calibrated: sit upright, then Calibrate",
    "paused": "Paused (camera off)",
    "camera_error": "Camera unavailable (check permissions)",
}


def title_for(status):
    """Menu bar text for a status dict (None means the monitor isn't running yet)."""
    if status is None:
        return "⏳"
    icon = ICONS.get(status["state"], "❔")
    if status["state"] in ("good", "bad") and status.get("score") is not None:
        return f'{icon} {status["score"]}'
    return icon


class PostureMenuBar(rumps.App):
    def __init__(self):
        super().__init__("Posture Monitor", title="⏳", quit_button=None)
        self.status_item = rumps.MenuItem("Starting…")
        self.view_item = rumps.MenuItem("Show live view", callback=self.toggle_view)
        self.pause_item = rumps.MenuItem("Pause monitoring", callback=self.toggle_pause)
        self.menu = [
            self.status_item,
            None,
            self.view_item,
            rumps.MenuItem("Calibrate (sit upright first)", callback=lambda _: ipc.send_command("calibrate")),
            rumps.MenuItem("I took a break", callback=lambda _: ipc.send_command("break")),
            self.pause_item,
            None,
            rumps.MenuItem("Open dashboard", callback=self.open_dashboard),
            rumps.MenuItem("Quit Posture Monitor", callback=self.quit),
        ]

        self.monitor = None
        self.dashboard = None
        self.wake = WakeDetector()
        self.start_monitor()

        self.refresh_timer = rumps.Timer(self.refresh, 1)
        self.refresh_timer.start()
        self.wake_timer = rumps.Timer(self.check_wake, TICK_SECONDS)
        self.wake_timer.start()

    def start_monitor(self):
        self.monitor = subprocess.Popen(
            [sys.executable, os.path.join(SRC_DIR, "app.py"), "--background"], cwd=SRC_DIR
        )

    def refresh(self, _):
        if self.monitor is not None and self.monitor.poll() is not None:
            self.start_monitor()  # monitor crashed: restart it

        status = ipc.read_status()
        self.title = title_for(status)
        if status is None:
            self.status_item.title = "Starting…"
            return

        text = STATE_TEXT.get(status["state"], status["state"])
        if status["state"] == "bad" and status.get("reasons"):
            text = f'Bad posture: {status["reasons"]}'
        elif status["state"] == "good":
            text = f'Good posture ({status["score"]}/100)'
        if status.get("break_overdue"):
            text += " · take a break!"
        self.status_item.title = text

        self.view_item.title = "Hide live view" if status.get("window_visible") else "Show live view"
        self.pause_item.title = "Resume monitoring" if status["state"] == "paused" else "Pause monitoring"

    def check_wake(self, _):
        if self.wake.check():
            rumps.notification(REMINDER_TITLE, "", REMINDER_MESSAGE)

    def toggle_view(self, _):
        ipc.send_command("toggle")

    def toggle_pause(self, _):
        status = ipc.read_status()
        ipc.send_command("resume" if status and status["state"] == "paused" else "pause")

    def open_dashboard(self, _):
        if self.dashboard is None or self.dashboard.poll() is not None:
            self.dashboard = subprocess.Popen(
                [
                    sys.executable, "-m", "streamlit", "run", os.path.join(SRC_DIR, "dashboard.py"),
                    "--server.headless", "true", "--server.port", str(DASHBOARD_PORT),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        webbrowser.open(f"http://localhost:{DASHBOARD_PORT}")

    def quit(self, _):
        ipc.send_command("quit")
        for proc in (self.monitor, self.dashboard):
            if proc is not None and proc.poll() is None:
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.terminate()
        rumps.quit_application()


if __name__ == "__main__":
    # Menu bar only: no Dock icon.
    from AppKit import NSApplication, NSApplicationActivationPolicyAccessory

    NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    PostureMenuBar().run()
