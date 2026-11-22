import pytest

pytest.importorskip("rumps", reason="menu bar app is macOS-only")

from menubar import title_for  # noqa: E402


def test_not_running():
    assert title_for(None) == "⏳"


def test_score_shown_for_good_and_bad():
    assert title_for({"state": "good", "score": 91}) == "🟢 91"
    assert title_for({"state": "bad", "score": 40}) == "🔴 40"


def test_other_states_show_icon_only():
    assert title_for({"state": "paused", "score": None}) == "⏸"
    assert title_for({"state": "uncalibrated", "score": None}) == "🎯"
