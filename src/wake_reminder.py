"""Tiny background reminder: nudges you to sit properly at login and every time the
laptop wakes from sleep. It never touches the camera.

Run directly (`python src/wake_reminder.py`) or install it as a login item with
`scripts/install_launch_agent.sh`.
"""
import time

from notifications import send_notification

TICK_SECONDS = 5
# If the wall clock jumps by more than this between ticks, the machine was asleep.
WAKE_GAP_SECONDS = 30

REMINDER_TITLE = "Posture Monitor"
REMINDER_MESSAGE = "Welcome back! Sit up, relax your shoulders and bring your screen to eye level."


class WakeDetector:
    """Detects sleep/wake by noticing that a fixed-interval tick arrived very late."""

    def __init__(self, tick_seconds=TICK_SECONDS, gap_seconds=WAKE_GAP_SECONDS, clock=time.time):
        self._tick = tick_seconds
        self._gap = gap_seconds
        self._clock = clock
        self._last = clock()

    def check(self):
        """Call once per tick. Returns True if the machine just woke up."""
        now = self._clock()
        woke = now - self._last > self._tick + self._gap
        self._last = now
        return woke


def main():
    send_notification(REMINDER_TITLE, REMINDER_MESSAGE)  # login / start
    detector = WakeDetector()
    while True:
        time.sleep(TICK_SECONDS)
        if detector.check():
            send_notification(REMINDER_TITLE, REMINDER_MESSAGE)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
