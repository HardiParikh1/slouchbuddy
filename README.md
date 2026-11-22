# Posture Monitor

[![CI](../../actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)

A real-time computer vision application that monitors desk posture using a webcam and alerts you when poor posture is sustained.

## Features

- Real-time pose tracking (MediaPipe) with a live overlay
- **Per-user calibration**: your upright pose is the baseline, so it adapts to your camera angle and body proportions
- Four calibration-relative checks: uneven shoulders, head forward, head tilt, leaning toward the screen
- One **absolute** check (independent of calibration): head level with or below the shoulders
- Weighted 0-100 posture score
- Alerts only after posture stays bad for a sustained period, with a cooldown between alerts (desktop notification + sound)
- 50-minute break reminder
- Session logging to CSV and a Streamlit + Plotly analytics dashboard (score trends, good/bad %, most frequent issues)

## How it works

```
webcam frame -> MediaPipe Pose (33 landmarks) -> PostureDetector (metrics)
             -> analyze_posture(current, baseline) -> status + score
             -> BadPostureTracker (sustained-bad + cooldown) -> notification
             -> SessionLogger (CSV) -> dashboard
```

| Module | Responsibility |
| --- | --- |
| `pose_detection.py` | Turns landmarks into normalized metrics (shoulder imbalance, head offset, tilt, mouth width, head-above-shoulders) |
| `posture_analyzer.py` | Compares metrics to the calibrated baseline; produces the status and weighted score |
| `alert_tracker.py` | Pure state machine for "bad for N seconds" + alert cooldown (injectable clock) |
| `calibration.py` / `session_logger.py` | JSON baseline and CSV session persistence |
| `dashboard*.py` | Streamlit analytics over the logged sessions |
| `app.py` | The camera loop that wires everything together |

Design notes:

- Metrics are compared against *your* baseline rather than fixed angles, because a laptop camera's height and tilt change what "upright" looks like in the frame.
- Each score factor starts losing points only once it crosses its threshold and bottoms out at 2x the threshold, so small natural movement doesn't tank the score.
- Alert timing lives in `BadPostureTracker`, separate from the camera loop, so it's unit-tested without a webcam.
- All thresholds are in `src/config.py`.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# Live monitor: press C to calibrate (sit upright first), B after a break, Q to quit
python src/app.py

# If the wrong camera opens (e.g. an iPhone via Continuity Camera):
CAMERA_INDEX=1 python src/app.py

# Session history dashboard
streamlit run src/dashboard.py
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

The suite covers the analyzer and scoring, the alert tracker (with a fake clock), calibration and session persistence, and the dashboard's data aggregation. CI runs it on every push.

## Limitations

- Designed for a seated desk setup with the head and shoulders in frame, not for lying down or off-axis camera angles.
- Thresholds are hand-tuned defaults and may need adjusting for your camera and desk.

## Tech Stack

Python, OpenCV, MediaPipe, NumPy, pandas, Streamlit, Plotly, pytest, GitHub Actions
