# Slouchbuddy 🐨

[![CI](../../actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)

**Your slouch-fixing desk buddy.** A real-time posture coach for people who work from home: it watches you through your webcam, learns what *your* good posture looks like, and an animated koala in your menu bar nudges you (kindly) when you've been slouching for too long.

## Why I built this

After about six months of working from home, my posture was wrecked. No office chair, no colleagues walking past, just me, a laptop and hours of slowly sinking into the desk. I knew I should sit up straight, but nothing was reminding me, and by the time I noticed, I'd been hunched over for an hour.

Posture apps I looked at either wanted a wearable or only gave a generic "sit up" timer. I figured the better fix was to build the thing I actually wanted: a live monitor that sees how I'm sitting right now, compares it to my own upright baseline, and taps me on the shoulder only when it matters.

It started as a webcam experiment and grew into a small menu bar app, an analytics dashboard so I can see whether I'm actually improving, and a koala that hangs out in my menu bar so that working alone is a little less lonely (and the nagging is a lot friendlier).

## Features

- **Real-time pose tracking** (MediaPipe) with a live camera view you can open when you want it
- **Per-user calibration:** your upright pose is the baseline, so it adapts to your camera angle and body proportions
- **Five posture checks:** uneven shoulders, head forward, head tilt and leaning toward the screen (all relative to your baseline), plus an **absolute** check for head level with or below the shoulders that ignores calibration
- **A 0-100 posture score,** weighted across those checks
- **A koala buddy** that reacts to how you sit (happy, lazy-slouching, oops, curious, sleepy, coffee break). On macOS it lives in the menu bar; anything it has to say arrives as a notification: specific tips ("shoulders are uneven", "chin back"), cheers when you recover, good-streak milestones and break reminders
- **Gentle alerts:** only after posture stays bad for a sustained period, with a cooldown, a soft chime (configurable) and no nagging
- **Break reminders** and a friendly "sit up" notification whenever your laptop wakes from sleep
- **A cosy analytics dashboard** (Streamlit + Plotly) with day / week / month / year views, good-vs-bad percentages and your most frequent issues
- **Starts at login** on macOS, Windows and Linux
- **Private by design:** everything runs locally; no video or data leaves your machine, and pausing releases the camera entirely

## Install

Requires Python 3.9-3.12 and a webcam.

```bash
pip install git+https://github.com/HardiParikh1/posture-monitor.git
```

From a clone: `pip install .`, or `pip install -e ".[dev]"` for development.

## Usage

```bash
slouchbuddy              # macOS: koala in the menu bar. Windows/Linux: the koala card
slouchbuddy dashboard    # analytics dashboard in your browser
slouchbuddy run          # plain camera window (C = calibrate, B = break taken, Q = quit)
slouchbuddy buddy        # the on-screen koala card (Windows/Linux)
slouchbuddy menubar      # the menu bar koala (macOS)
slouchbuddy test-sound   # hear the alert sound
slouchbuddy install-login / uninstall-login
```

**First run:** sit up straight as you would at your desk, then choose **Calibrate** from the koala's menu. If the wrong camera opens (e.g. an iPhone through Continuity Camera), set `CAMERA_INDEX=1` (or 2, ...), or use `slouchbuddy install-login --camera 1` for the login item.

### The koala buddy

On macOS the koala lives **only in the menu bar**, animated next to your live score and changing mood with your posture. Nothing is drawn over your screen. Click it to calibrate, take a break, pause (which turns the camera off), open the camera view or open the dashboard.

On Windows and Linux there's no menu bar koala, so `slouchbuddy` opens a small koala card in the top-right corner of your screen instead (drag it anywhere, right-click for the same menu).

The koala is drawn entirely in code ([`koala.py`](src/slouchbuddy/koala.py)), so there are no image assets, and its personality is a small, tested state machine ([`buddy_brain.py`](src/slouchbuddy/buddy_brain.py)): it waits before commenting, doesn't repeat itself, and only praises a recovery that was worth praising.

### The dashboard

`slouchbuddy dashboard` opens a cosy eucalyptus-grove page (light and dark themes) with a koala whose mood follows your average score, soft cards, drifting leaves, and:

- the score over time by **day, week, month or year**, with a picker for the exact period
- good-posture percentage, longest bad streak and sessions tracked
- your most frequent issues and a session-by-session trend

### Alert sound

Alerts play a soft two-note chime. Hear the options with `slouchbuddy test-sound chime` (or `beep`, `Glass`, `Pop`, `Ping`, ...) and choose one with `ALERT_SOUND` in [`config.py`](src/slouchbuddy/config.py): `"chime"`, `"beep"`, `"off"`, or the name of a macOS system sound.

### Windows and Linux

Everything works on all three platforms except the menu bar koala (macOS only): the monitor, the on-screen koala card, notifications and the dashboard. `install-login` registers startup via the registry (Windows) or an autostart entry (Linux). macOS is where it's developed and used daily; CI runs the tests on all three systems, but the Windows and Linux camera and window behaviour is untested on real machines, so bug reports are very welcome.

### Where data is stored

Calibration and session logs live in `~/.slouchbuddy/data/` (override with `SLOUCHBUDDY_HOME`). When running from a source checkout they stay in the repo's `data/` folder.

## How it works

```
webcam frame -> MediaPipe Pose (33 landmarks) -> PostureDetector (metrics)
             -> analyze_posture(current, baseline) -> status + score
             -> BadPostureTracker (sustained-bad + cooldown) -> chime
             -> status file -> koala (menu bar / card) -> BuddyBrain -> mood + notification
             -> SessionLogger (CSV) -> dashboard
```

The camera runs in a background process; the menu bar app and the koala card are thin front ends that read its status and send it commands (calibrate, pause, ...) through small files ([`ipc.py`](src/slouchbuddy/ipc.py)).

| Module | Responsibility |
| --- | --- |
| `pose_detection.py` | Turns landmarks into normalized metrics (shoulder imbalance, head offset, tilt, mouth width, head-above-shoulders) |
| `posture_analyzer.py` | Compares metrics to the calibrated baseline; produces the status and weighted score |
| `alert_tracker.py` | Pure state machine for "bad for N seconds" plus alert cooldown (injectable clock) |
| `app.py` | The camera loop; runs in the foreground or hidden in the background |
| `koala.py` | Draws the animated koala (Pillow): six moods shared by the menu bar, the card and the dashboard |
| `buddy_brain.py` | The koala's personality: monitor status in, mood and comment out |
| `menubar.py` / `buddy.py` | The macOS menu bar app and the tkinter koala card |
| `ipc.py` / `launcher.py` | File-based status and commands; helpers that start the monitor and dashboard |
| `notifications.py` | Desktop notifications and the alert chime |
| `calibration.py` / `session_logger.py` | JSON baseline and CSV session persistence |
| `dashboard*.py` | Streamlit analytics, theme and artwork |
| `launch_agent.py` / `cli.py` | Start-at-login on each OS and the `slouchbuddy` command |

Design notes:

- Metrics are compared against *your* baseline rather than fixed angles, because a laptop camera's height and tilt change what "upright" looks like in the frame.
- Each score factor starts losing points only once it crosses its threshold and bottoms out at 2x the threshold, so small natural movement doesn't tank the score.
- Anything with timing or decisions (alerts, the koala's mood, wake detection, dashboard aggregation) is a pure function or state machine with an injectable clock, so it's unit-tested without a camera or a display.
- All thresholds live in [`config.py`](src/slouchbuddy/config.py).

## Tests

```bash
pip install -r requirements-dev.txt   # lightweight: no camera or MediaPipe needed
pytest
```

The suite (80+ tests) covers the analyzer and scoring, the alert tracker, the koala's behaviour and rendering, the IPC channel, calibration and session persistence, the alert sound, the CLI and login items, and the dashboard's aggregation and artwork. CI runs it on Linux, Windows and macOS, and builds the package.

## Limitations

- Designed for a seated desk setup with your head and shoulders in frame; it isn't for lying down or for off-axis camera angles.
- Thresholds are hand-tuned defaults and may need adjusting for your camera and desk.
- The dashboard loads its fonts from Google Fonts and falls back to system fonts offline.

## Tech stack

Python, OpenCV, MediaPipe, NumPy, pandas, Pillow, Streamlit, Plotly, tkinter, rumps (macOS menu bar), pytest, GitHub Actions
