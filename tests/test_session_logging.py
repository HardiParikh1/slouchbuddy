import csv

import pytest

from session_logger import SessionLogger
from session_summary import load_rows, summarize


def write_session(tmp_path, entries):
    logger = SessionLogger(sessions_dir=str(tmp_path), interval_seconds=0.001)
    import time
    for score, status, bad in entries:
        logger.log(score, status, bad)
        time.sleep(0.002)
    logger.close()
    return logger.path


def test_logger_writes_header_and_rows(tmp_path):
    path = write_session(tmp_path, [(90, "GOOD POSTURE", 0), (40, "BAD POSTURE: HEAD TILT", 3.2)])
    with open(path, newline="") as f:
        rows = list(csv.reader(f))
    assert rows[0] == ["timestamp", "posture_score", "status", "bad_duration"]
    assert len(rows) == 3
    assert rows[2][1:] == ["40", "BAD POSTURE: HEAD TILT", "3.2"]


def test_logger_throttles_to_interval(tmp_path):
    logger = SessionLogger(sessions_dir=str(tmp_path), interval_seconds=60)
    for _ in range(50):
        logger.log(100, "GOOD POSTURE", 0)
    logger.close()
    assert len(load_rows(logger.path)) == 1


def test_summarize(tmp_path):
    path = write_session(
        tmp_path,
        [
            (100, "GOOD POSTURE", 0),
            (60, "BAD POSTURE: SHOULDERS + HEAD TILT", 5.0),
            (40, "BAD POSTURE: HEAD TILT", 12.5),
            (100, "GOOD POSTURE", 0),
        ],
    )
    s = summarize(load_rows(path))
    assert s["sample_count"] == 4
    assert s["average_score"] == pytest.approx(75)
    assert s["min_score"] == 40
    assert s["good_pct"] == pytest.approx(50)
    assert s["bad_pct"] == pytest.approx(50)
    assert s["longest_bad_streak"] == 12.5
    assert s["reason_counts"]["HEAD TILT"] == 2
    assert s["reason_counts"]["SHOULDERS"] == 1
