import platform
import subprocess

import numpy as np
import sounddevice as sd

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


def _generate_beep(frequency=880, duration=0.25, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    tone = 0.3 * np.sin(2 * np.pi * frequency * t)

    # Fade in/out to avoid a clicking sound at the edges.
    fade_samples = int(sample_rate * 0.02)
    tone[:fade_samples] *= np.linspace(0, 1, fade_samples)
    tone[-fade_samples:] *= np.linspace(1, 0, fade_samples)

    return tone, sample_rate


def play_alert_sound():
    try:
        tone, sample_rate = _generate_beep()
        sd.play(tone, sample_rate)
    except Exception as e:
        print(f"Sound alert failed: {e}")


def alert_bad_posture(status, posture_score):
    send_notification("Posture Monitor", f"{status} (score: {posture_score}/100)")
    play_alert_sound()
