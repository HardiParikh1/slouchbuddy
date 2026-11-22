import glob
import os
from collections import Counter

import pandas as pd

from slouchbuddy import config


def list_session_files():
    resolved_dir = os.path.join(config.DATA_ROOT, config.SESSIONS_DIR)
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


SCORE_VIEWS = ["Day", "Week", "Month", "Year"]

# view -> resample frequency (bucket size)
_FREQ = {"Day": "5min", "Week": "h", "Month": "D", "Year": "W"}


def period_window(view, anchor):
    """Calendar period [start, end) containing `anchor`: that day, week (Mon-Sun),
    month or year."""
    anchor = pd.Timestamp(anchor).normalize()
    if view == "Day":
        start, end = anchor, anchor + pd.Timedelta(days=1)
    elif view == "Week":
        start = anchor - pd.Timedelta(days=anchor.weekday())
        end = start + pd.Timedelta(days=7)
    elif view == "Month":
        start = anchor.replace(day=1)
        end = start + pd.offsets.MonthBegin(1)
    elif view == "Year":
        start = anchor.replace(month=1, day=1)
        end = start + pd.offsets.YearBegin(1)
    else:
        raise ValueError(f"unknown view: {view}")
    return start, end


def aggregate_scores(df, view, anchor):
    """Average posture score per time bucket within the calendar period around `anchor`.

    Returns (agg, start, end). `agg` has `timestamp`, `avg_score`, `samples`; empty
    buckets are dropped (never interpolated) so gaps in tracking stay visible.
    """
    start, end = period_window(view, anchor)
    empty = pd.DataFrame(columns=["timestamp", "avg_score", "samples"])
    if df.empty:
        return empty, start, end

    # Concatenating sessions can leave an object-dtype column; resample needs real datetimes.
    stamps = pd.to_datetime(df["timestamp"])
    in_window = df.assign(timestamp=stamps)[(stamps >= start) & (stamps < end)]
    if in_window.empty:
        return empty, start, end

    grouped = (
        in_window.set_index("timestamp")["posture_score"]
        .resample(_FREQ[view])
        .agg(["mean", "count"])
    )
    grouped = grouped[grouped["count"] > 0].reset_index()
    grouped.columns = ["timestamp", "avg_score", "samples"]
    return grouped, start, end
