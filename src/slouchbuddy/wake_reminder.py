"""Wake-from-sleep detection and the reminder text used by the menu bar app."""
import time

TICK_SECONDS = 5
# If the wall clock jumps by more than this between ticks, the machine was asleep.
WAKE_GAP_SECONDS = 30

REMINDER_TITLE = "Slouchbuddy"
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
