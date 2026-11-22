import os
import platform
import subprocess

import numpy as np

try:
    import sounddevice as sd
except (ImportError, OSError):  # package or PortAudio missing (e.g. headless Linux): alerts go silent
    sd = None

from slouchbuddy import config

_SYSTEM = platform.system()


def send_notification(title, message):
    try:
        if _SYSTEM == "Darwin":
            safe_title = title.replace('"', '\\"')
            safe_message = message.replace('"', '\\"')
            script = f'display notification "{safe_message}" with title "{safe_title}"'
            subprocess.run(["osascript", "-e", script], check=False)
        else:
            from plyer import notification
            notification.notify(title=title, message=message, timeout=5)
    except Exception as e:
        print(f"Notification failed: {e}")


SAMPLE_RATE = 44100
MACOS_SOUNDS_DIR = "/System/Library/Sounds"


def _generate_beep(frequency=880, duration=0.25, sample_rate=SAMPLE_RATE):
    """The original plain beep (ALERT_SOUND = "beep")."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    tone = 0.3 * np.sin(2 * np.pi * frequency * t)

    # Fade in/out to avoid a clicking sound at the edges.
    fade_samples = int(sample_rate * 0.02)
    tone[:fade_samples] *= np.linspace(0, 1, fade_samples)
    tone[-fade_samples:] *= np.linspace(1, 0, fade_samples)

    return tone, sample_rate


def _bell(frequency, duration, sample_rate=SAMPLE_RATE):
    """One soft bell strike: a few inharmonic partials with an exponential decay."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    partials = ((1.0, 1.0, 0.30), (2.76, 0.35, 0.18), (5.4, 0.12, 0.08))  # ratio, level, decay (s)
    tone = sum(level * np.sin(2 * np.pi * frequency * ratio * t) * np.exp(-t / decay)
               for ratio, level, decay in partials)
    attack = int(sample_rate * 0.004)
    tone[:attack] *= np.linspace(0, 1, attack)
    return tone


def _generate_chime(sample_rate=SAMPLE_RATE):
    """A gentle two-note chime (E5 then A5): friendly, not alarming."""
    total = int(sample_rate * 1.1)
    out = np.zeros(total)
    for start, freq in ((0.0, 659.25), (0.18, 880.0)):
        strike = _bell(freq, 0.9, sample_rate)
        offset = int(start * sample_rate)
        out[offset:offset + len(strike)] += strike
    out *= 0.28 / max(1e-9, np.abs(out).max())  # normalise to a comfortable, never-clipping level
    fade = int(sample_rate * 0.05)
    out[-fade:] *= np.linspace(1, 0, fade)
    return out, sample_rate


def _macos_sound_path(name):
    path = os.path.join(MACOS_SOUNDS_DIR, f"{name}.aiff")
    return path if _SYSTEM == "Darwin" and os.path.exists(path) else None


def play_alert_sound(name=None):
    """Play the alert sound chosen by config.ALERT_SOUND ("chime", "beep", "off" or the name
    of a macOS system sound such as "Glass", "Pop" or "Ping")."""
    name = name or config.ALERT_SOUND
    if str(name).lower() == "off":
        return
    try:
        system_sound = _macos_sound_path(name)
        if system_sound:
            subprocess.Popen(["afplay", system_sound])
            return
        if sd is None:
            return
        tone, sample_rate = _generate_beep() if str(name).lower() == "beep" else _generate_chime()
        sd.play(tone, sample_rate)
    except Exception as e:
        print(f"Sound alert failed: {e}")


def alert_bad_posture(status, posture_score):
    send_notification("Slouchbuddy", f"{status} (score: {posture_score}/100)")
    play_alert_sound()
