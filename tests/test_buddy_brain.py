from slouchbuddy.buddy_brain import (
    COFFEE, CURIOUS, GENERIC_SLOUCH, HAPPY, SLEEPING, SLOUCHING, WORRIED, BuddyBrain,
)


class Clock:
    now = 10_000.0

    def __call__(self):
        return self.now


def make():
    clock = Clock()
    return BuddyBrain(clock=clock), clock


def good(**kw):
    return {"state": "good", "score": 95, **kw}


def bad(reasons="Head Tilt", **kw):
    return {"state": "bad", "score": 40, "reasons": reasons, **kw}


def test_basic_state_to_mood():
    brain, _ = make()
    assert brain.update(None).mood == SLEEPING
    assert brain.update({"state": "paused"}).mood == SLEEPING
    assert brain.update(good()).mood == HAPPY
    assert brain.update({"state": "no_pose"}).mood == CURIOUS
    assert brain.update({"state": "camera_error"}).mood == WORRIED


def test_no_comment_for_a_brief_slouch():
    brain, clock = make()
    brain.update(good())
    clock.now += 1
    view = brain.update(bad())
    assert view.mood == SLOUCHING and view.message is None


def test_comments_on_sustained_slouch_with_issue_specific_hint():
    brain, clock = make()
    brain.update(bad("Shoulders"))
    clock.now += 6
    view = brain.update(bad("Shoulders"))
    assert "shoulders" in view.message.lower()


def test_generic_message_when_reason_unknown():
    brain, clock = make()
    brain.update(bad(reasons=None))
    clock.now += 6
    assert brain.update(bad(reasons=None)).message == GENERIC_SLOUCH


def test_level_head_hint_beats_plain_shoulders_hint():
    brain, clock = make()
    brain.update(bad("Shoulders, Head Level With Shoulders"))
    clock.now += 6
    assert "head up" in brain.update(bad("Shoulders, Head Level With Shoulders")).message.lower()


def test_does_not_nag_repeatedly_during_one_slouch():
    brain, clock = make()
    brain.update(bad())
    clock.now += 6
    assert brain.update(bad()).message
    for _ in range(10):
        clock.now += 5
        assert brain.update(bad()).message is None
    clock.now += 100
    assert brain.update(bad()).message  # eventually reminds again


def test_gets_worried_after_a_long_slouch():
    brain, clock = make()
    brain.update(bad())
    clock.now += 31
    assert brain.update(bad()).mood == WORRIED


def test_praises_recovery_only_after_a_real_slouch():
    brain, clock = make()
    brain.update(bad())
    clock.now += 12
    brain.update(bad())
    clock.now += 1
    assert "better" in brain.update(good()).message.lower()

    brain2, clock2 = make()
    brain2.update(bad())
    clock2.now += 2
    assert brain2.update(good()).message is None


def test_good_streak_milestone_announced_once():
    brain, clock = make()
    brain.update(good())
    clock.now += 15 * 60 + 1
    assert "15 minutes" in brain.update(good()).message
    clock.now += 30
    assert brain.update(good()).message is None


def test_break_reminder_once_then_coffee_mood():
    brain, clock = make()
    first = brain.update(good(break_overdue=True))
    assert first.mood == COFFEE and "break" in first.message.lower()
    clock.now += 60
    again = brain.update(good(break_overdue=True))
    assert again.mood == COFFEE and again.message is None


def test_uncalibrated_explains_calibration_once():
    brain, _ = make()
    first = brain.update({"state": "uncalibrated"})
    assert first.mood == CURIOUS and "Calibrate" in first.message
    assert brain.update({"state": "uncalibrated"}).message is None
