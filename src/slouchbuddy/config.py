import os



def _find_data_root():
    """Where calibration, session logs and IPC files live.

    1. $SLOUCHBUDDY_HOME if set.
    2. The repo root when running from a source checkout (keeps existing ./data).
    3. ~/.slouchbuddy for a normal pip install.
    """
    override = os.environ.get("SLOUCHBUDDY_HOME")
    if override:
        return os.path.abspath(os.path.expanduser(override))

    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if os.path.exists(os.path.join(repo_root, "pyproject.toml")):
        return repo_root

    return os.path.join(os.path.expanduser("~"), ".slouchbuddy")


DATA_ROOT = _find_data_root()

BAD_POSTURE_THRESHOLD_SECONDS = 10
ALERT_COOLDOWN_SECONDS = 120

# Sound played with a posture alert: "chime" (soft two-note bell), "beep", "off", or the name of a
# macOS system sound ("Glass", "Pop", "Ping", "Tink", "Hero", "Purr", "Bottle"...).
ALERT_SOUND = "chime"

# Remind to take a break every 45-60 min of sitting; default in the middle.
BREAK_REMINDER_SECONDS = 50 * 60

SHOULDER_IMBALANCE_DIFF_THRESHOLD = 0.03
HEAD_FORWARD_DIFF_THRESHOLD = 0.04
HEAD_TILT_DIFF_THRESHOLD = 10
SCREEN_PROXIMITY_DIFF_THRESHOLD = 0.015

# Absolute check (independent of calibration): the nose must sit at least this far
# above the shoulder line, as a fraction of frame height. Upright is ~0.15-0.30;
# a head level with or below the shoulders (lying down, slumped) is ~0 or negative.
HEAD_LEVEL_MIN_GAP = 0.08
HEAD_LEVEL_SCORE_CAP = 40

SHOULDER_GOOD_THRESHOLD = 0.02
SHOULDER_WARNING_THRESHOLD = 0.05

CALIBRATION_FILE = "data/calibration.json"

SESSIONS_DIR = "data/sessions"
SESSION_LOG_INTERVAL_SECONDS = 1.0

# Posture Score: each factor starts losing points once its diff crosses the
# "bad" threshold above, and bottoms out at 0 once it reaches
# POSTURE_SCORE_SEVERITY_CAP times the threshold.
POSTURE_SCORE_WEIGHTS = {
    "shoulder": 25,
    "head_forward": 25,
    "head_tilt": 25,
    "screen_distance": 25,
}
POSTURE_SCORE_SEVERITY_CAP = 2.0
