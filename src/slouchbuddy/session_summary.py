import csv
import glob
import os
from collections import Counter
from datetime import datetime

from slouchbuddy import config


def find_latest_session(sessions_dir=None):
    sessions_dir = sessions_dir or config.SESSIONS_DIR
    resolved_dir = os.path.join(config.DATA_ROOT, sessions_dir)

    csv_files = glob.glob(os.path.join(resolved_dir, "session_*.csv"))
    if not csv_files:
        return None

    return max(csv_files, key=os.path.getmtime)


def load_rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def summarize(rows):
    scores = [int(row["posture_score"]) for row in rows]
    statuses = [row["status"] for row in rows]
    bad_durations = [float(row["bad_duration"]) for row in rows]

    start = datetime.fromisoformat(rows[0]["timestamp"])
    end = datetime.fromisoformat(rows[-1]["timestamp"])

    good_count = sum(1 for status in statuses if status == "GOOD POSTURE")
    bad_count = len(statuses) - good_count

    reason_counts = Counter()
    for status in statuses:
        if status.startswith("BAD POSTURE: "):
            reasons = status.removeprefix("BAD POSTURE: ").split(" + ")
            reason_counts.update(reasons)

    return {
        "duration": end - start,
        "sample_count": len(rows),
        "average_score": sum(scores) / len(scores),
        "min_score": min(scores),
        "good_pct": good_count / len(statuses) * 100,
        "bad_pct": bad_count / len(statuses) * 100,
        "longest_bad_streak": max(bad_durations),
        "reason_counts": reason_counts,
    }


def print_summary(path, summary):
    print(f"Session: {os.path.basename(path)}")
    print(f"Duration: {summary['duration']} ({summary['sample_count']} samples)")
    print(f"Average Posture Score: {summary['average_score']:.1f}/100")
    print(f"Lowest Posture Score: {summary['min_score']}/100")
    print(f"Good posture: {summary['good_pct']:.1f}%  |  Bad posture: {summary['bad_pct']:.1f}%")
    print(f"Longest bad posture streak: {summary['longest_bad_streak']:.1f}s")

    if summary["reason_counts"]:
        print("Bad posture breakdown:")
        for reason, count in summary["reason_counts"].most_common():
            pct = count / summary["sample_count"] * 100
            print(f"  {reason:<16} {pct:.1f}%")


if __name__ == "__main__":
    latest = find_latest_session()

    if latest is None:
        print("No session logs found in", config.SESSIONS_DIR)
    else:
        rows = load_rows(latest)
        if not rows:
            print(f"{latest} is empty.")
        else:
            print_summary(latest, summarize(rows))
