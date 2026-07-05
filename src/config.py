import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BAD_POSTURE_THRESHOLD_SECONDS = 10
ALERT_COOLDOWN_SECONDS = 120

# Remind to take a break every 45-60 min of sitting; default in the middle.
BREAK_REMINDER_SECONDS = 50 * 60

SHOULDER_IMBALANCE_DIFF_THRESHOLD = 0.03
HEAD_FORWARD_DIFF_THRESHOLD = 0.04
HEAD_TILT_DIFF_THRESHOLD = 10
SCREEN_PROXIMITY_DIFF_THRESHOLD = 0.015

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
