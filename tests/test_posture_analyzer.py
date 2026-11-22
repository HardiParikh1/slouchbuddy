import pytest

from slouchbuddy import config
from slouchbuddy.posture_analyzer import analyze_posture, calculate_posture_score, get_shoulder_status

BASELINE = {
    "shoulder_imbalance": 0.01,
    "nose_to_shoulder_x": 0.02,
    "head_tilt_angle": 0.0,
    "mouth_width": 0.05,
    "head_above_shoulders": 0.2,
}


def metrics(**overrides):
    return {**BASELINE, **overrides}


def test_identical_to_baseline_is_good_and_perfect_score():
    result = analyze_posture(metrics(), BASELINE)
    assert result.status == "GOOD POSTURE"
    assert not result.is_bad_posture
    assert result.posture_score == 100


@pytest.mark.parametrize(
    "override, reason",
    [
        ({"shoulder_imbalance": 0.01 + 0.05}, "SHOULDERS"),
        ({"nose_to_shoulder_x": 0.02 + 0.1}, "HEAD FORWARD"),
        ({"head_tilt_angle": 25.0}, "HEAD TILT"),
        ({"mouth_width": 0.05 + 0.05}, "SCREEN DISTANCE"),
        ({"head_above_shoulders": 0.0}, "HEAD LEVEL WITH SHOULDERS"),
    ],
)
def test_each_factor_is_flagged(override, reason):
    result = analyze_posture(metrics(**override), BASELINE)
    assert result.is_bad_posture
    assert reason in result.status


def test_multiple_reasons_are_joined():
    result = analyze_posture(metrics(head_tilt_angle=30, shoulder_imbalance=0.1), BASELINE)
    assert result.status.startswith("BAD POSTURE: ")
    assert "SHOULDERS" in result.status and "HEAD TILT" in result.status
    assert " + " in result.status


def test_values_within_threshold_are_not_flagged():
    just_under = config.HEAD_TILT_DIFF_THRESHOLD - 0.5
    assert analyze_posture(metrics(head_tilt_angle=just_under), BASELINE).status == "GOOD POSTURE"


def test_moving_away_from_screen_is_not_flagged():
    # Smaller mouth width = further from camera; only getting closer is penalised.
    result = analyze_posture(metrics(mouth_width=0.01), BASELINE)
    assert "SCREEN DISTANCE" not in result.status


def test_head_level_check_ignores_calibration():
    # Calibrated while slumped: the relative checks see no drift, the absolute one still fires.
    slumped = metrics(head_above_shoulders=0.01)
    result = analyze_posture(slumped, slumped)
    assert "HEAD LEVEL WITH SHOULDERS" in result.status
    assert result.posture_score <= config.HEAD_LEVEL_SCORE_CAP


def test_head_level_boundary():
    ok = analyze_posture(metrics(head_above_shoulders=config.HEAD_LEVEL_MIN_GAP), BASELINE)
    assert "HEAD LEVEL" not in ok.status


def test_score_is_zero_to_hundred_and_monotonic():
    scores = [calculate_posture_score(d, 0, 0, 0) for d in (0, 0.03, 0.045, 0.06, 1.0)]
    assert scores == sorted(scores, reverse=True)
    assert all(0 <= s <= 100 for s in scores)


def test_score_bottoms_out_when_everything_is_terrible():
    assert calculate_posture_score(10, 10, 1000, 10) == 0


def test_score_penalty_only_starts_past_threshold():
    assert calculate_posture_score(config.SHOULDER_IMBALANCE_DIFF_THRESHOLD, 0, 0, 0) == 100


def test_score_caps_each_factor_at_its_weight():
    only_shoulders = calculate_posture_score(10, 0, 0, 0)
    assert only_shoulders == 100 - config.POSTURE_SCORE_WEIGHTS["shoulder"]


@pytest.mark.parametrize(
    "value, expected",
    [(0.0, "GOOD"), (0.03, "WARNING"), (0.2, "BAD")],
)
def test_shoulder_status_buckets(value, expected):
    assert get_shoulder_status(value) == expected
