from wake_reminder import WakeDetector


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def test_regular_ticks_are_not_wakes():
    clock = Clock()
    d = WakeDetector(tick_seconds=5, gap_seconds=30, clock=clock)
    for _ in range(50):
        clock.now += 5.2
        assert d.check() is False


def test_long_gap_is_a_wake_then_normal_again():
    clock = Clock()
    d = WakeDetector(tick_seconds=5, gap_seconds=30, clock=clock)
    clock.now += 5
    assert d.check() is False
    clock.now += 3600  # laptop slept for an hour
    assert d.check() is True
    clock.now += 5
    assert d.check() is False
