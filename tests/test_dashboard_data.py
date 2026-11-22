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


def _samples(start, n, step_minutes, score=80):
    ts = pd.date_range(start, periods=n, freq=f"{step_minutes}min")
    return pd.DataFrame({"timestamp": ts, "posture_score": score})


def test_aggregate_averages_within_bucket_and_drops_empty_buckets():
    from dashboard_data import aggregate_scores

    df = pd.concat([_samples("2026-03-01 10:00", 3, 1, 90), _samples("2026-03-01 14:00", 2, 1, 50)])
    out, start, end = aggregate_scores(df, "Day", "2026-03-01")
    assert list(out["avg_score"]) == [90, 50]
    assert list(out["samples"]) == [3, 2]
    assert (start, end) == (pd.Timestamp("2026-03-01"), pd.Timestamp("2026-03-02"))


def test_aggregate_only_includes_the_selected_period():
    from dashboard_data import aggregate_scores

    df = pd.concat([_samples("2025-01-15", 5, 1, 10), _samples("2026-06-01", 5, 1, 70)])
    assert list(aggregate_scores(df, "Month", "2026-06-20")[0]["avg_score"]) == [70]
    assert list(aggregate_scores(df, "Year", "2025-03-01")[0]["avg_score"]) == [10]
    assert aggregate_scores(df, "Day", "2026-02-02")[0].empty


def test_period_windows_are_calendar_aligned():
    from dashboard_data import period_window

    ts = pd.Timestamp
    assert period_window("Week", "2026-11-22") == (ts("2026-11-16"), ts("2026-11-23"))  # Mon-Sun
    assert period_window("Month", "2026-12-31") == (ts("2026-12-01"), ts("2027-01-01"))
    assert period_window("Year", "2026-07-04") == (ts("2026-01-01"), ts("2027-01-01"))


def test_aggregate_empty():
    from dashboard_data import aggregate_scores

    out, _, _ = aggregate_scores(pd.DataFrame(columns=["timestamp", "posture_score"]), "Day", "2026-01-01")
    assert out.empty
