from alert_tracker import BadPostureTracker


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def make(threshold=10, cooldown=120):
    clock = FakeClock()
    return BadPostureTracker(threshold, cooldown, clock=clock), clock


def test_good_posture_never_alerts():
    tracker, clock = make()
    for _ in range(100):
        clock.advance(1)
        assert tracker.update(False) == (0, False)


def test_no_alert_before_threshold():
    tracker, clock = make(threshold=10)
    tracker.update(True)
    clock.advance(9)
    duration, alert = tracker.update(True)
    assert duration == 9 and not alert


def test_alerts_once_threshold_reached():
    tracker, clock = make(threshold=10)
    tracker.update(True)
    clock.advance(10)
    assert tracker.update(True) == (10, True)


def test_cooldown_suppresses_repeat_alerts_then_allows_again():
    tracker, clock = make(threshold=10, cooldown=120)
    tracker.update(True)
    clock.advance(10)
    assert tracker.update(True)[1] is True

    clock.advance(60)
    assert tracker.update(True)[1] is False

    clock.advance(60)
    assert tracker.update(True)[1] is True


def test_good_frame_resets_the_streak():
    tracker, clock = make(threshold=10)
    tracker.update(True)
    clock.advance(8)
    tracker.update(False)
    clock.advance(5)
    duration, alert = tracker.update(True)
    assert duration == 0 and not alert


def test_reset_clears_streak():
    tracker, clock = make(threshold=10)
    tracker.update(True)
    clock.advance(20)
    tracker.reset()
    assert tracker.update(True) == (0, False)
