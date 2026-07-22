import glob
import os
from collections import Counter

import pandas as pd

import config


def list_session_files():
    resolved_dir = os.path.join(config.PROJECT_ROOT, config.SESSIONS_DIR)
    files = glob.glob(os.path.join(resolved_dir, "session_*.csv"))
    return sorted(files, key=os.path.getmtime, reverse=True)


def _session_label(path):
    stem = os.path.basename(path).removeprefix("session_").removesuffix(".csv")
    try:
        return pd.to_datetime(stem, format="%Y%m%d_%H%M%S").strftime("%b %d, %Y – %I:%M %p")
    except ValueError:
        return stem


def load_session(path):
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df["session_file"] = os.path.basename(path)
    df["session_label"] = _session_label(path)
    return df


def load_all_sessions(files):
    columns = ["timestamp", "posture_score", "status", "bad_duration", "session_file", "session_label"]
    if not files:
        return pd.DataFrame(columns=columns)

    frames = [load_session(f) for f in files]
    return pd.concat(frames, ignore_index=True)


def extract_reason_counts(status_series):
    counts = Counter()
    for status in status_series:
        if isinstance(status, str) and status.startswith("BAD POSTURE: "):
            reasons = status.removeprefix("BAD POSTURE: ").split(" + ")
            counts.update(reasons)
    return counts


def session_level_summary(df_all):
    columns = ["session_file", "session_label", "session_start", "avg_score", "good_pct", "sample_count"]
    if df_all.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    for session_file, group in df_all.groupby("session_file"):
        good_count = (group["status"] == "GOOD POSTURE").sum()
        rows.append(
            {
                "session_file": session_file,
                "session_label": group["session_label"].iloc[0],
                "session_start": group["timestamp"].min(),
                "avg_score": group["posture_score"].mean(),
                "good_pct": good_count / len(group) * 100,
                "sample_count": len(group),
            }
        )

    return pd.DataFrame(rows).sort_values("session_start").reset_index(drop=True)
