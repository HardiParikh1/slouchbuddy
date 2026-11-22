import pandas as pd

from dashboard_data import extract_reason_counts, load_all_sessions, session_level_summary


def make_df():
    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                ["2026-01-02 10:00:00", "2026-01-02 10:00:01", "2026-01-01 09:00:00"]
            ),
            "posture_score": [100, 50, 80],
            "status": ["GOOD POSTURE", "BAD POSTURE: SHOULDERS", "GOOD POSTURE"],
            "bad_duration": [0, 4, 0],
            "session_file": ["b.csv", "b.csv", "a.csv"],
            "session_label": ["B", "B", "A"],
        }
    )


def test_extract_reason_counts_splits_combined_reasons():
    counts = extract_reason_counts(
        pd.Series(["GOOD POSTURE", "BAD POSTURE: A + B", "BAD POSTURE: A", None])
    )
    assert counts == {"A": 2, "B": 1}


def test_session_summary_sorted_by_start_with_metrics():
    summary = session_level_summary(make_df())
    assert list(summary["session_file"]) == ["a.csv", "b.csv"]
    b = summary[summary["session_file"] == "b.csv"].iloc[0]
    assert b["avg_score"] == 75
    assert b["good_pct"] == 50
    assert b["sample_count"] == 2


def test_empty_inputs_are_handled():
    assert load_all_sessions([]).empty
    assert session_level_summary(load_all_sessions([])).empty
