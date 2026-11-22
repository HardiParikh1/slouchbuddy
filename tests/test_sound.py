import numpy as np

from slouchbuddy import notifications


def test_chime_is_audible_but_never_clips_and_fades_out():
    tone, rate = notifications._generate_chime()
    assert rate == notifications.SAMPLE_RATE
    assert 0.9 < len(tone) / rate < 1.3
    assert 0.1 < np.abs(tone).max() <= 0.3
    assert abs(tone[-1]) < 1e-3  # ends silently, no click


def test_chime_has_two_strikes():
    tone, rate = notifications._generate_chime()
    envelope = np.abs(tone)
    first = envelope[: int(0.18 * rate)].max()
    second = envelope[int(0.18 * rate): int(0.30 * rate)].max()
    assert second > 0.5 * first  # the second note really is a new strike


def test_off_plays_nothing(monkeypatch):
    called = []
    monkeypatch.setattr(notifications.sd, "play", lambda *a, **k: called.append(a))
    notifications.play_alert_sound("off")
    assert called == []


def test_chime_and_beep_go_to_the_sound_device(monkeypatch):
    called = []
    monkeypatch.setattr(notifications.sd, "play", lambda *a, **k: called.append(a))
    monkeypatch.setattr(notifications, "_macos_sound_path", lambda name: None)
    notifications.play_alert_sound("chime")
    notifications.play_alert_sound("beep")
    assert len(called) == 2 and len(called[0][0]) != len(called[1][0])


def test_macos_system_sound_uses_afplay(monkeypatch):
    popen = []
    monkeypatch.setattr(notifications, "_macos_sound_path", lambda name: f"/x/{name}.aiff")
    monkeypatch.setattr(notifications.subprocess, "Popen", lambda args: popen.append(args))
    notifications.play_alert_sound("Glass")
    assert popen == [["afplay", "/x/Glass.aiff"]]
