"""macOS menu bar app: an animated koala in the menu bar that reacts to your posture.

The koala lives only in the menu bar (no window on screen); anything it has to say arrives
as a notification. Click it to calibrate, pause, open the camera view or the dashboard.

    slouchbuddy menubar
"""
import os
import subprocess
import time
import webbrowser

import rumps

from slouchbuddy import buddy_brain, config, ipc, koala, launcher
from slouchbuddy.buddy_brain import BuddyBrain
from slouchbuddy.notifications import play_alert_sound, send_notification
from slouchbuddy.wake_reminder import REMINDER_MESSAGE, TICK_SECONDS, WakeDetector

NOTIFICATION_TITLE = "Slouchbuddy 🐨"

STATE_TEXT = {
    "good": "Good posture",
    "bad": "Bad posture",
    "no_pose": "Can't see you",
    "uncalibrated": "Not calibrated: sit upright, then Calibrate",
    "paused": "Paused (camera off)",
    "camera_error": "Camera unavailable (check permissions)",
}


def title_for(status):
    """Text shown next to the koala in the menu bar: the live score, when there is one."""
    if status and status.get("state") in ("good", "bad") and status.get("score") is not None:
        return f' {status["score"]}'
    return ""


class PostureMenuBar(rumps.App):
    def __init__(self):
        icon_dir = os.path.join(config.DATA_ROOT, "data", "icons")
        self.frames = {mood: koala.icon_frame_paths(mood, icon_dir) for mood in koala.MOODS}
        super().__init__(
            "Slouchbuddy", title="", icon=self.frames[buddy_brain.SLEEPING][0], quit_button=None
        )
        self.brain = BuddyBrain()
        self.mood = buddy_brain.SLEEPING
        self.comment = None
        self.comment_until = 0
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
            rumps.MenuItem("Quit Slouchbuddy", callback=self.quit),
        ]

        self.monitor = None
        self.dashboard = None
        self.wake = WakeDetector()
        self.start_monitor()

        self.refresh_timer = rumps.Timer(self.refresh, 1)
        self.refresh_timer.start()
        self.animation_timer = rumps.Timer(self.animate, koala.FRAME_SECONDS)
        self.animation_timer.start()
        self.wake_timer = rumps.Timer(self.check_wake, TICK_SECONDS)
        self.wake_timer.start()

    def start_monitor(self):
        self.monitor = launcher.spawn_monitor()

    def refresh(self, _):
        if self.monitor is not None and self.monitor.poll() is not None:
            self.start_monitor()  # monitor crashed: restart it

        status = ipc.read_status()
        self.title = title_for(status)

        view = self.brain.update(status)
        self.mood = view.mood
        if view.message:
            self.comment, self.comment_until = view.message, time.time() + 45
            send_notification(NOTIFICATION_TITLE, view.message)
            if view.alert:
                play_alert_sound()  # right after the notification, so they land together

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
        if self.comment and time.time() < self.comment_until:
            text = f"🐨 {self.comment}"
        self.status_item.title = text

        self.view_item.title = "Hide live view" if status.get("window_visible") else "Show live view"
        self.pause_item.title = "Resume monitoring" if status["state"] == "paused" else "Pause monitoring"

    def animate(self, _):
        frames = self.frames[self.mood]
        self.icon = frames[int(time.time() / koala.FRAME_SECONDS) % len(frames)]

    def check_wake(self, _):
        if self.wake.check():
            send_notification(NOTIFICATION_TITLE, REMINDER_MESSAGE)

    def toggle_view(self, _):
        ipc.send_command("toggle")

    def toggle_pause(self, _):
        status = ipc.read_status()
        ipc.send_command("resume" if status and status["state"] == "paused" else "pause")

    def open_dashboard(self, _):
        if self.dashboard is None or self.dashboard.poll() is not None:
            self.dashboard = launcher.spawn_dashboard()
        webbrowser.open(f"http://localhost:{launcher.DASHBOARD_PORT}")

    def quit(self, _):
        ipc.send_command("quit")
        for proc in (self.dashboard,):
            if proc is not None and proc.poll() is None:
                proc.terminate()
        if self.monitor is not None and self.monitor.poll() is None:
            try:
                self.monitor.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.monitor.terminate()
        rumps.quit_application()


def main():
    # Menu bar only: no Dock icon.
    from AppKit import NSApplication, NSApplicationActivationPolicyAccessory

    NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    PostureMenuBar().run()


if __name__ == "__main__":
    main()
