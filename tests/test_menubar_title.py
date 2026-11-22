import pytest

pytest.importorskip("rumps", reason="menu bar app is macOS-only")

from slouchbuddy.menubar import title_for  # noqa: E402


def test_nothing_shown_when_not_running():
    assert title_for(None) == ""


def test_score_shown_for_good_and_bad():
    assert title_for({"state": "good", "score": 91}) == " 91"
    assert title_for({"state": "bad", "score": 40}) == " 40"


def test_no_score_for_other_states():
    assert title_for({"state": "paused", "score": None}) == ""
    assert title_for({"state": "uncalibrated", "score": None}) == ""


def test_nudge_sends_notification_then_chime_together(monkeypatch):
    import time
    from types import SimpleNamespace

    from slouchbuddy import menubar
    from slouchbuddy.buddy_brain import BuddyView

    calls = []
    monkeypatch.setattr(menubar, "send_notification", lambda title, msg: calls.append(("notify", msg)))
    monkeypatch.setattr(menubar, "play_alert_sound", lambda: calls.append(("chime",)))
    monkeypatch.setattr(menubar.ipc, "read_status", lambda: {"state": "bad", "score": 40, "reasons": "Head Tilt"})

    views = iter([BuddyView("slouching", "Your head is tilting.", alert=True),
                  BuddyView("happy", "Nice, much better!", alert=False)])
    app = object.__new__(menubar.PostureMenuBar)
    app.monitor = None
    app.brain = SimpleNamespace(update=lambda status: next(views))
    app.status_item = SimpleNamespace(title="")
    app.view_item = SimpleNamespace(title="")
    app.pause_item = SimpleNamespace(title="")
    app.mood, app.comment, app.comment_until = "sleeping", None, 0

    app.refresh(None)
    assert calls == [("notify", "Your head is tilting."), ("chime",)]

    calls.clear()
    app.refresh(None)  # praise: notification only, no chime
    assert calls == [("notify", "Nice, much better!")]
