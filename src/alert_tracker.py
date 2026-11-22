import time

import config


class BadPostureTracker:
    """Tracks how long posture has been continuously bad and decides when to alert.

    Pure logic with an injectable clock, so it can be unit-tested without a camera.
    """

    def __init__(self, threshold_seconds=None, cooldown_seconds=None, clock=time.time):
        self.threshold_seconds = (
            config.BAD_POSTURE_THRESHOLD_SECONDS if threshold_seconds is None else threshold_seconds
        )
        self.cooldown_seconds = (
            config.ALERT_COOLDOWN_SECONDS if cooldown_seconds is None else cooldown_seconds
        )
        self._clock = clock
        self._bad_since = None
        self._last_alert = None

    def update(self, is_bad):
        """Record the latest frame. Returns (bad_duration_seconds, should_alert)."""
        now = self._clock()

        if not is_bad:
            self._bad_since = None
            return 0, False

        if self._bad_since is None:
            self._bad_since = now
        duration = now - self._bad_since

        if duration < self.threshold_seconds:
            return duration, False

        cooled_down = (
            self._last_alert is None or now - self._last_alert >= self.cooldown_seconds
        )
        if cooled_down:
            self._last_alert = now
        return duration, cooled_down

    def reset(self):
        self._bad_since = None
